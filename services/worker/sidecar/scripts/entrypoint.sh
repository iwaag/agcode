#!/bin/bash
set -e

# Git HTTPS credential setup
if [ -n "$GITHUB_TOKEN" ]; then
    GIT_HOST="${GIT_HOST:-github.com}"
    git config --global credential.helper store
    echo "https://x-token-auth:${GITHUB_TOKEN}@${GIT_HOST}" > ~/.git-credentials
    chmod 600 ~/.git-credentials
    echo "[entrypoint] git HTTPS credential configured (host=$GIT_HOST)"
else
    echo "[entrypoint] WARNING: GITHUB_TOKEN not set, git auth skipped"
fi

# VS Code tunnel login
if [ -n "$VSCODE_TOKEN" ]; then
    code tunnel user login --provider github --access-token "$VSCODE_TOKEN"
    echo "[entrypoint] VS Code tunnel login done"
else
    echo "[entrypoint] WARNING: VSCODE_TOKEN not set, tunnel login skipped"
fi

# Start FastAPI server
exec uvicorn main:app --app-dir /app --host 0.0.0.0 --port 8000
