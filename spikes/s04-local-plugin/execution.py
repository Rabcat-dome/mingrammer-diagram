"""Bounded native subprocess execution; macOS RSS/disk checks are sampled."""
import os
from pathlib import Path
import signal
import subprocess
import time

POLICY = {"wall_seconds": 55, "memory_bytes": 1024 ** 3, "temporary_bytes": 256 * 1024 ** 2,
          "sampling_seconds": 0.1, "cpu_seconds_soft_hard": [45, 50],
          "memory_enforcement": "sampled process-group RSS; not a kernel hard cap",
          "temporary_enforcement": "sampled request-directory bytes; not a tmpfs quota",
          "network": "renderer and descendants denied by macOS sandbox-exec"}


def group_rss(group):
    listing = subprocess.check_output(["/bin/ps", "-axo", "pgid=,rss="], text=True, timeout=2)
    return sum(int(fields[1]) * 1024 for line in listing.splitlines()
               if len(fields := line.split()) == 2 and int(fields[0]) == group)


def directory_bytes(root):
    return sum(p.lstat().st_size for p in Path(root).rglob("*") if not p.is_symlink())


def terminate(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.communicate(timeout=5)


def execute(command, payload, environment, scratch, policy=None):
    policy = policy or POLICY
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True, env=environment)
    started = time.monotonic()
    completed = False
    try:
        while True:
            try:
                output, _ = process.communicate(payload, timeout=policy["sampling_seconds"])
                if process.returncode:
                    raise ValueError("S04_RENDER_FAILURE")
                completed = True
                return output
            except subprocess.TimeoutExpired:
                payload = None
                if time.monotonic() - started >= policy["wall_seconds"]:
                    raise ValueError("S04_RENDER_TIMEOUT")
                if group_rss(process.pid) > policy["memory_bytes"]:
                    raise ValueError("S04_MEMORY_LIMIT")
                if directory_bytes(scratch) > policy["temporary_bytes"]:
                    raise ValueError("S04_TEMPORARY_LIMIT")
    finally:
        # A dead parent can leave descendants holding stdout/stderr open.
        if not completed:
            terminate(process)
