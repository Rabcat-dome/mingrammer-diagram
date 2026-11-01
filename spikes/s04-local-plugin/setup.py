"""Install this version's renderer image on the current machine."""
import json
import os
import subprocess
import sys
import tempfile
from common import ROOT, VERSION, STATE, OUTPUT, docker_path, fingerprint, require_local_docker


def main():
    docker = docker_path()
    endpoint = require_local_docker(docker)
    system = subprocess.check_output([docker, "info", "--format", "{{.OSType}}"], text=True).strip()
    if system != "linux":
        raise RuntimeError("The local runtime needs a Linux Docker engine")
    source = fingerprint()
    tag = "cloud-architecture-diagrams-runtime:" + VERSION
    subprocess.run([docker, "build", "--tag", tag, "--label", "cloud.architecture.source=" + source,
                    str(ROOT / "runtime")], stdout=sys.stderr, check=True)
    image = subprocess.check_output([docker, "image", "inspect", tag, "--format", "{{.Id}}"], text=True).strip()
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    OUTPUT.mkdir(parents=True, exist_ok=True, mode=0o700)
    state = {"version": VERSION, "source_sha256": source, "image_id": image, "output_root": str(OUTPUT), "docker_endpoint": endpoint}
    with tempfile.NamedTemporaryFile("w", dir=STATE.parent, delete=False) as temporary:
        json.dump(state, temporary, indent=2)
        temporary.write("\n")
        path = temporary.name
    os.replace(path, STATE)
    print(json.dumps({"installed": True, **state, "state_file": str(STATE)}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
