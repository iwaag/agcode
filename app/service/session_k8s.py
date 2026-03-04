import os
import re
import time

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from schema.schema import SessionConfig, SessionInfo
import db.database as db

IMAGE_NAME_CODER_PRO = os.getenv("IMAGE_NAME_CODER_PRO")
IMAGE_NAME_CODER_NOOB = os.getenv("IMAGE_NAME_CODER_NOOB")
NAMESPACE = "default"
STORAGE_CLASS_NAME = "microk8s-hostpath"
PVC_SIZE = "1Gi"
SCHEDULING_TIMEOUT_SECONDS = 30


def _to_k8s_name_fragment(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("Kubernetes resource name fragment cannot be empty")
    return normalized


def _resolve_image(image_name: str | None, env_name: str) -> str:
    if not image_name:
        raise ValueError(f"{env_name} is not set")
    if "@" in image_name:
        return image_name

    last_segment = image_name.rsplit("/", 1)[-1]
    if ":" in last_segment:
        return image_name

    return f"{image_name}:latest"


def _ensure_pvc(v1: client.CoreV1Api, pvc_name: str) -> None:
    try:
        v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=NAMESPACE)
        print(f"PVC {pvc_name} already exists. Reusing...")
        return
    except ApiException as e:
        if e.status != 404:
            raise

    print(f"PVC {pvc_name} not found. Creating new one...")
    pvc_body = client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(name=pvc_name),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(requests={"storage": PVC_SIZE}),
            storage_class_name=STORAGE_CLASS_NAME,
        ),
    )
    v1.create_namespaced_persistent_volume_claim(namespace=NAMESPACE, body=pvc_body)


def _build_pod(
    *,
    pod_name: str,
    session_id: str,
    user_id: str,
    role: str,
    image: str,
    own_pvc_name: str,
    peer_pvc_name: str,
    node_name: str | None = None,
) -> client.V1Pod:
    labels = {
        "task-id": session_id,
        "user-id": user_id,
        "type": "session-worker",
        "role": role,
    }
    return client.V1Pod(
        metadata=client.V1ObjectMeta(name=pod_name, labels=labels),
        spec=client.V1PodSpec(
            restart_policy="Never",
            node_name=node_name,
            containers=[
                client.V1Container(
                    name=f"{role}-container",
                    image=image,
                    volume_mounts=[
                        client.V1VolumeMount(
                            name="own-task-data",
                            mount_path="/mnt/data",
                            read_only=False,
                        ),
                        client.V1VolumeMount(
                            name="peer-task-data",
                            mount_path="/mnt/peer-data",
                            read_only=True,
                        ),
                    ],
                    env=[
                        client.V1EnvVar(name="TASK_ID", value=session_id),
                        client.V1EnvVar(name="SESSION_ROLE", value=role),
                    ],
                )
            ],
            volumes=[
                client.V1Volume(
                    name="own-task-data",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=own_pvc_name,
                        read_only=False,
                    ),
                ),
                client.V1Volume(
                    name="peer-task-data",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                        claim_name=peer_pvc_name,
                        read_only=True,
                    ),
                ),
            ],
        ),
    )


def _create_or_reuse_pod(v1: client.CoreV1Api, pod_spec: client.V1Pod) -> client.V1Pod:
    pod_name = pod_spec.metadata.name
    try:
        pod = v1.create_namespaced_pod(namespace=NAMESPACE, body=pod_spec)
        print(f"Pod {pod_name} created successfully.")
        return pod
    except ApiException as e:
        if e.status == 409:
            print(f"Pod {pod_name} already exists. Reusing...")
            return v1.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
        raise


def _wait_for_node_assignment(v1: client.CoreV1Api, pod_name: str) -> str:
    deadline = time.time() + SCHEDULING_TIMEOUT_SECONDS
    while time.time() < deadline:
        pod = v1.read_namespaced_pod(name=pod_name, namespace=NAMESPACE)
        node_name = pod.spec.node_name
        if node_name:
            return node_name
        time.sleep(1)

    raise TimeoutError(f"Pod {pod_name} was not scheduled within {SCHEDULING_TIMEOUT_SECONDS} seconds")


async def run_session(session_id: str, project_id: str, user_id: str) -> SessionInfo:
    session_info = db.get_session(session_id)
    if not session_info:
        raise ValueError(f"Session {session_id} not found")

    config.load_kube_config(config_file="./remote-config.yaml")
    v1 = client.CoreV1Api()
    task_name = _to_k8s_name_fragment(session_id)
    pro_pvc_name = f"pvc-session-{task_name}-pro"
    noob_pvc_name = f"pvc-session-{task_name}-noob"
    pro_pod_name = f"worker-session-{task_name}-pro"
    noob_pod_name = f"worker-session-{task_name}-noob"

    _ensure_pvc(v1, pro_pvc_name)
    _ensure_pvc(v1, noob_pvc_name)

    pro_pod_spec = _build_pod(
        pod_name=pro_pod_name,
        session_id=session_id,
        user_id=user_id,
        role="pro",
        image=_resolve_image(IMAGE_NAME_CODER_PRO, "IMAGE_NAME_CODER_PRO"),
        own_pvc_name=pro_pvc_name,
        peer_pvc_name=noob_pvc_name,
    )
    _create_or_reuse_pod(v1, pro_pod_spec)
    assigned_node_name = _wait_for_node_assignment(v1, pro_pod_name)

    noob_pod_spec = _build_pod(
        pod_name=noob_pod_name,
        session_id=session_id,
        user_id=user_id,
        role="noob",
        image=_resolve_image(IMAGE_NAME_CODER_NOOB, "IMAGE_NAME_CODER_NOOB"),
        own_pvc_name=noob_pvc_name,
        peer_pvc_name=pro_pvc_name,
        node_name=assigned_node_name,
    )
    _create_or_reuse_pod(v1, noob_pod_spec)

    return SessionInfo(id=session_id)
