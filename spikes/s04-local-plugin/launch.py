"""Start only the installed, source-matched local MCP image; no startup installs."""
import json
import os
import secrets
import subprocess
import sys
from common import ROOT, VERSION, STATE, OUTPUT, docker_path, fingerprint, require_local_docker


def main():
    docker = docker_path()
    require_local_docker(docker)
    if not STATE.is_file():
        raise RuntimeError("Local runtime is not installed. Run: python3 " + str(ROOT / "scripts/setup.py"))
    state = json.loads(STATE.read_text())
    source = fingerprint()
    if state.get("version") != VERSION or state.get("source_sha256") != source:
        raise RuntimeError("Runtime/package versions differ; rerun this plugin's scripts/setup.py")
    image = state["image_id"]
    label = subprocess.check_output([docker, "image", "inspect", image, "--format",
                                    '{{index .Config.Labels "cloud.architecture.source"}}'], text=True).strip()
    if label != source:
        raise RuntimeError("Installed image provenance does not match the plugin")
    OUTPUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    if "," in str(OUTPUT) or "\n" in str(OUTPUT):
        raise RuntimeError("This pilot requires an output-root path without commas/newlines")
    name = "cloud-diagrams-mcp-" + secrets.token_hex(8)
    args = [docker, "run", "--init", "--rm", "--pull", "never", "-i", "--name", name,
            "--network", "none", "--memory", "1g", "--memory-swap", "1g", "--cpus", "1",
            "--pids-limit", "64", "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m,mode=1777",
            "--mount", "type=bind,src=" + str(OUTPUT) + ",dst=/output",
            "--env", "CLOUD_DIAGRAM_HOST_OUTPUT_ROOT", "--env", "CLOUD_DIAGRAM_PLUGIN_VERSION"]
    if hasattr(os, "getuid") and os.getuid() > 0:
        args += ["--user", str(os.getuid()) + ":" + str(os.getgid())]
    args += [image]
    environment = os.environ.copy()
    environment["CLOUD_DIAGRAM_HOST_OUTPUT_ROOT"] = str(OUTPUT)
    environment["CLOUD_DIAGRAM_PLUGIN_VERSION"] = VERSION
    os.execvpe(docker, args, environment)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
