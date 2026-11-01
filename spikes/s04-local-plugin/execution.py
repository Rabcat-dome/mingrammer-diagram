"""Bounded native execution with catchable-signal shutdown and scratch cleanup."""
from contextlib import contextmanager
import os
from pathlib import Path
import signal
import stat
import subprocess
import tempfile
import threading
import time

POLICY = {"wall_seconds": 55, "memory_bytes": 1024 ** 3, "temporary_bytes": 256 * 1024 ** 2,
          "sampling_seconds": 0.1, "cpu_seconds_soft_hard": [45, 50],
          "memory_enforcement": "sampled process-group RSS; not a kernel hard cap",
          "temporary_enforcement": "sampled request-directory bytes; not a tmpfs quota",
          "shutdown": "SIGTERM/SIGINT/stdio EOF stop renderer groups and drain request cleanup; SIGKILL cannot run cleanup",
          "network": "renderer and descendants denied by macOS sandbox-exec"}
_LOCK = threading.RLock()
_PROCESSES = set()
_JOBS = {}
_EXIT_STATUS = None
_MAIN_REGISTRATION = 0
_CANCEL_CALLBACK = None


def set_cancel_callback(callback):
    global _CANCEL_CALLBACK
    _CANCEL_CALLBACK = callback


def check_running():
    if _EXIT_STATUS is not None:
        if threading.current_thread() is threading.main_thread():
            raise SystemExit(_EXIT_STATUS)
        raise ValueError('S04_HELPER_SHUTDOWN')


@contextmanager
def registration():
    # Defer a main-thread signal exit until a newly allocated resource is registered.
    global _MAIN_REGISTRATION
    main = threading.current_thread() is threading.main_thread()
    if main:
        _MAIN_REGISTRATION += 1
    try:
        with _LOCK:
            yield
    finally:
        if main:
            _MAIN_REGISTRATION -= 1


def kill_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def stop_requests(exit_status):
    global _EXIT_STATUS
    if _EXIT_STATUS is not None:
        return
    _EXIT_STATUS = exit_status
    with _LOCK:
        processes = tuple(_PROCESSES)
        jobs = tuple(_JOBS.values())
    for process in processes:
        kill_group(process)
    if _MAIN_REGISTRATION:
        return
    # Worker-thread finally blocks reap processes and remove owned scratch first.
    deadline = time.monotonic() + 5
    for owner, done in jobs:
        if owner != threading.get_ident():
            done.wait(max(0, deadline - time.monotonic()))
    if _CANCEL_CALLBACK is not None:
        # Let the async transport unwind normally instead of throwing
        # SystemExit through the event loop's selector/task-group internals.
        _CANCEL_CALLBACK()
        return
    raise SystemExit(exit_status)


def shutdown(signum, _frame):
    stop_requests(128 + signum)


def install_shutdown_handlers():
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, shutdown)


@contextmanager
def request_directory(parent):
    temporary = None
    token = object()
    done = threading.Event()
    try:
        with registration():
            check_running()
            temporary = tempfile.TemporaryDirectory(prefix='request-', dir=parent)
            _JOBS[token] = (threading.get_ident(), done)
        check_running()
        yield temporary.name
    finally:
        try:
            if temporary is not None:
                temporary.cleanup()
        finally:
            with _LOCK:
                _JOBS.pop(token, None)
            done.set()


def group_rss(group):
    listing = subprocess.check_output(["/bin/ps", "-axo", "pgid=,rss="], text=True, timeout=2)
    return sum(int(fields[1]) * 1024 for line in listing.splitlines()
               if len(fields := line.split()) == 2 and int(fields[0]) == group)


def directory_bytes(root):
    total = 0
    for path in Path(root).rglob('*'):
        try:
            info = path.lstat()
        except FileNotFoundError:
            # Graphviz/diagrams normally delete intermediate files during render.
            continue
        if not stat.S_ISLNK(info.st_mode):
            total += info.st_size
    return total


def terminate(process):
    kill_group(process)
    try:
        process.communicate(timeout=5)
    except (OSError, ValueError):
        # A main-thread signal can interrupt communicate while its pipe selector
        # is closing. Preserve the original shutdown/error and still reap.
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass
        process.wait(timeout=5)


def execute(command, payload, environment, scratch, policy=None):
    policy = policy or POLICY
    process = None
    completed = False
    try:
        with registration():
            check_running()
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True, env=environment)
            _PROCESSES.add(process)
        check_running()
        started = time.monotonic()
        while True:
            check_running()
            try:
                output, _ = process.communicate(payload, timeout=policy["sampling_seconds"])
                check_running()
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
        try:
            if process is not None and not completed:
                terminate(process)
        finally:
            with _LOCK:
                _PROCESSES.discard(process)
