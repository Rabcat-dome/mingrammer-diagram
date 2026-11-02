"""Run Graphviz alone, sandboxed and bounded (NFR-002, NFR-009). Input only reaches it as DOT text."""

import os
import pwd
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from dataclasses import dataclass

from .errors import RenderFailure
from .limits import Limits
from .paths import signals_deferred

SANDBOX = "/usr/bin/sandbox-exec"
ENGINE_LOG = "engine.log"
RESOLVED_FONT = re.compile(rb"^fontname: .* resolved to: .*$", re.MULTILINE)
FALLBACK_DIRECTORIES = ("/opt/homebrew/bin", "/usr/local/bin")
# Parameters, not string building: a path in a profile cannot alter its rules.
PROFILE = """(version 1)
(allow default)
(deny network*)
(deny process-fork)
(deny process-exec*)
(allow process-exec* (literal (param "ENGINE")))
(deny file-write*)
(allow file-write* (subpath (param "REQUEST")))
(allow file-write-data (literal "/dev/null"))
(deny file-read-data (subpath (param "HOME")))
(allow file-read-data (subpath (param "REQUEST")))
"""
# Applied by a child rather than preexec_fn, which is unsafe once a host adds threads.
LIMITER = """
import os, resource, sys
cpu, size = int(sys.argv[1]), int(sys.argv[2])
resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
resource.setrlimit(resource.RLIMIT_FSIZE, (size, size))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.execv(sys.argv[3], sys.argv[3:])
"""
ISOLATION = {
    "kind": "macos-sandbox-exec",
    "network": "denied",
    "process_creation": "denied",
    "file_writes": "request directory only",
    "home_directory_reads": "denied",
    "memory": "sampled process-group RSS, not a kernel hard cap",
    "temporary_storage": "sampled request-directory bytes, not a quota",
}


@dataclass(frozen=True)
class Engine:
    path: str
    version: str


def _dot_path() -> str | None:
    # A relative PATH entry would resolve inside the user's project, under a pre-approved command.
    entries = [
        entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry.startswith("/")
    ]
    return shutil.which("dot", path=os.pathsep.join([*entries, *FALLBACK_DIRECTORIES]))


def host_blockers() -> list[str]:
    blockers = []
    if _dot_path() is None:
        blockers.append("graphviz_missing")
    if sys.platform != "darwin" or not os.access(SANDBOX, os.X_OK):
        blockers.append("sandbox_unavailable")
    return blockers


def find_engine() -> Engine:
    if sys.platform != "darwin" or not os.access(SANDBOX, os.X_OK):
        raise RenderFailure("RENDER_ISOLATION_UNAVAILABLE", "/engine")
    found = _dot_path()
    if found is None:
        raise RenderFailure("RENDER_ENGINE_UNAVAILABLE", "/engine")
    path = os.path.realpath(found)
    try:
        # Even this query runs sandboxed, because the binary is whatever PATH offered.
        output = subprocess.run(
            sandboxed([path, "-V"], "/nonexistent", real_home()),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env={"PATH": "/usr/bin:/bin"},
            timeout=10,
            check=True,
        ).stderr
    except (OSError, subprocess.SubprocessError) as error:
        raise RenderFailure("RENDER_ENGINE_UNAVAILABLE", "/engine") from error
    version = re.search(rb"graphviz version ([0-9][0-9.]*)", output)
    if version is None:
        raise RenderFailure("RENDER_ENGINE_UNAVAILABLE", "/engine")
    return Engine(path, version.group(1).decode())


def real_home() -> str:
    # The account's record, because $HOME is whatever the environment says.
    return os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir)


def limited(command: list[str], limits: Limits) -> list[str]:
    return [
        sys.executable,
        "-I",
        "-S",
        "-c",
        LIMITER,
        str(limits.cpu_seconds),
        str(limits.file_bytes),
        *command,
    ]


def sandboxed(engine: list[str], request: str, home: str) -> list[str]:
    return [
        SANDBOX,
        "-D",
        f"ENGINE={engine[0]}",
        "-D",
        f"REQUEST={request}",
        "-D",
        f"HOME={home}",
        "-p",
        PROFILE,
        *engine,
    ]


def engine_environment(request: str) -> dict[str, str]:
    # Nothing is inherited, so FONTCONFIG_PATH, GVBINDIR, DYLD_* and the like cannot steer it.
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": request,
        "TMPDIR": f"{request}/tmp",
        "LANG": "en_US.UTF-8",
        "FONTCONFIG_FILE": f"{request}/fonts.conf",
        # On macOS Pango defaults to CoreText, which ignores fontconfig and picks a system font.
        "PANGOCAIRO_BACKEND": "fc",
    }


def group_rss(group: int) -> int:
    listing = subprocess.check_output(["/bin/ps", "-axo", "pgid=,rss="], text=True, timeout=2)
    return sum(
        int(fields[1]) * 1024
        for line in listing.splitlines()
        if len(fields := line.split()) == 2 and int(fields[0]) == group
    )


def directory_bytes(root: str) -> int:
    total = 0
    for folder, directories, files in os.walk(root, followlinks=False):
        for name in [*directories, *files]:
            try:
                info = os.lstat(os.path.join(folder, name))
            except FileNotFoundError:
                continue
            if not stat.S_ISLNK(info.st_mode):
                total += info.st_size
    return total


def _stop(process: subprocess.Popen[bytes], finished: bool) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    if not finished:
        process.wait()


def run_bounded(
    command: list[str],
    cwd: str,
    environment: dict[str, str],
    limits: Limits,
    scratch: str,
    stderr: int = subprocess.DEVNULL,
) -> None:
    """A failure, a limit or an interrupt leaves no process of this group running."""
    process: subprocess.Popen[bytes] | None = None
    finished = False
    try:
        # An interrupt here could otherwise lose track of a child that had already started.
        with signals_deferred():
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=stderr,
                start_new_session=True,
            )
        started = time.monotonic()
        while True:
            try:
                status = process.wait(timeout=limits.sampling_seconds)
                finished = True
                if status != 0:
                    raise RenderFailure("RENDER_ENGINE_FAILED", "/engine")
                return
            except subprocess.TimeoutExpired:
                pass
            if time.monotonic() - started >= limits.wall_seconds:
                raise RenderFailure("RENDER_TIMEOUT", "/engine")
            if group_rss(process.pid) > limits.memory_bytes:
                raise RenderFailure("RENDER_MEMORY_LIMIT", "/engine")
            if directory_bytes(scratch) > limits.temporary_bytes:
                raise RenderFailure("RENDER_TEMPORARY_LIMIT", "/engine")
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise RenderFailure("RENDER_ENGINE_FAILED", "/engine") from error
    finally:
        # An exited leader can still leave group members behind, so this runs on success too.
        if process is not None:
            with signals_deferred():
                _stop(process, finished)


def run_engine(engine: Engine, request: str, limits: Limits) -> None:
    # One layout for both files, and -v reports which font files that layout really used.
    arguments = [engine.path, "-v", "-Tsvg", "-o", "diagram.svg", "-Tpng", "-o", "diagram.png"]
    command = limited(sandboxed([*arguments, "graph.dot"], request, real_home()), limits)
    log = os.open(
        f"{request}/{ENGINE_LOG}", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    try:
        run_bounded(command, request, engine_environment(request), limits, request, log)
    finally:
        os.close(log)


def check_fonts_used(log: bytes, request: str) -> None:
    """A manifest must not claim fonts the engine skipped, as a host's Pango build could do."""
    resolved = RESOLVED_FONT.findall(log)
    allowed = os.fsencode(f"{request}/fonts/")
    if not resolved or not all(allowed in line for line in resolved):
        raise RenderFailure("RENDER_FONT_UNAVAILABLE", "/engine")
