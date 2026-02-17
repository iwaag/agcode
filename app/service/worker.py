from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os
WORKER_IMAGE_NAME = os.getenv("WORKER_IMAGE_NAME")

def launch_worker_with_pvc(task_id: str, user_id: str):
    config.load_kube_config()
    v1 = client.CoreV1Api()
    namespace = "default"
    pvc_name = f"pvc-task-{task_id}"
    pod_name = f"worker-task-{task_id}"
    try:
        v1.read_namespaced_persistent_volume_claim(name=pvc_name, namespace=namespace)
        print(f"PVC {pvc_name} already exists. Reusing...")
    except ApiException as e:
        if e.status == 404:
            print(f"PVC {pvc_name} not found. Creating new one...")
            pvc_body = client.V1PersistentVolumeClaim(
                metadata=client.V1ObjectMeta(name=pvc_name),
                spec=client.V1PersistentVolumeClaimSpec(
                    access_modes=["ReadWriteOnce"],
                    resources=client.V1ResourceRequirements(requests={"storage": "1Gi"}),
                    storage_class_name="microk8s-hostpath" 
                )
            )
            v1.create_namespaced_persistent_volume_claim(namespace=namespace, body=pvc_body)
        else:
            raise e
    pod_spec = client.V1Pod(
        metadata=client.V1ObjectMeta(
            name=pod_name,
            labels={"task-id": task_id, "user-id": user_id, "type": "session-worker"}
        ),
        spec=client.V1PodSpec(
            restart_policy="Never",
            containers=[
                client.V1Container(
                    name="worker-container",
                    image="WORKER_IMAGE_NAME:latest",
                    volume_mounts=[
                        client.V1VolumeMount(
                            name="task-data",
                            mount_path="/mnt/data"
                        )
                    ],
                    env=[client.V1EnvVar(name="TASK_ID", value=task_id)]
                )
            ],
            volumes=[
                client.V1Volume(
                    name="task-data",
                    persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pvc_name)
                )
            ]
        )
    )
    try:
        v1.create_namespaced_pod(namespace=namespace, body=pod_spec)
        print(f"Pod {pod_name} created successfully.")
    except ApiException as e:
        print(f"Exception when creating Pod: {e}")