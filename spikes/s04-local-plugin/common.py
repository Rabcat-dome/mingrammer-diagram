"""Host-side standard-library helpers for the S04 local runtime pilot."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / "plugin.json").read_text())["version"]
STATE = Path.home() / ".local/share/cloud-architecture-diagrams" / (VERSION + ".json")
OUTPUT = Path.home() / "Documents/CloudArchitectureDiagrams"


def docker_path():
    candidates = [shutil.which("docker"), "/usr/local/bin/docker", "/opt/homebrew/bin/docker"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("A running Linux Docker engine is required. Install/start it, then run scripts/setup.py.")


def require_local_docker(docker):
    context = os.environ.get("DOCKER_CONTEXT")
    endpoint = os.environ.get("DOCKER_HOST") if not context else None
    if not endpoint:
        context = context or subprocess.check_output([docker, "context", "show"], text=True).strip()
        endpoint = subprocess.check_output([docker, "context", "inspect", context, "--format",
                                            "{{.Endpoints.docker.Host}}"], text=True).strip()
    if not endpoint.startswith(("unix://", "npipe://")):
        raise RuntimeError("Local runtime requires a local Docker socket; remote/TCP Docker endpoints are not supported")
    return endpoint


def fingerprint():
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((ROOT / "runtime").iterdir()) if p.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()
