"""The private per-machine runtime: where it lives, how it is built and how it is checked."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import platform
import pwd
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from .artifacts import BUNDLE

PYTHON = "3.13.7"
SANDBOX = "/usr/bin/sandbox-exec"
# A host started from the desktop can have a short PATH, and uv and Graphviz usually live here.
TOOL_DIRECTORIES = ("/opt/homebrew/bin", "/usr/local/bin")
SETUP_SECONDS = 600
PROBE_SECONDS = 30
STOP_GRACE_SECONDS = 10
SETUP_LOCK_WAIT_SECONDS = 1.0
DETAIL_CHARACTERS = 2000
# Same entry as the Claude plugin's wrapper: -I keeps the working directory and Python's environment
# variables out of the import path, and the explicit insert accepts any plugin path.
BOOT = (
    "import sys; sys.path.insert(0, sys.argv.pop(1)); "
    "from cloud_architecture_diagrams.cli import main; raise SystemExit(main())"
)
HOST_MODES = {
    "selected": "The ChatGPT desktop app in Work mode, with this plugin's tools running on this Mac",
    "tested_system": "macOS on Apple silicon",
    "not_supported": [
        "ChatGPT on the web or on mobile",
        "Threads that run in the cloud, because they cannot reach a local process",
    ],
    "not_verified": [
        "Intel Macs",
        "Windows and Linux, where rendering refuses to run without the macOS sandbox",
        "Codex in the ChatGPT desktop app, which shares the engine but is not the acceptance target",
    ],
}


# Internal calls get their own keys, so no client's request ID can name one and cancel it.
SETUP_TOKEN = object()
SETUP_CHECK_TOKEN = object()
SETUP_PROBE_TOKEN = object()
ENVIRONMENT_FILE = re.compile(r"env-[0-9a-f]{16}(\.ready\.json)?")


class SetupInterrupted(Exception):
    """The tool process is stopping, which says nothing about whether setup would have worked."""


@dataclass
class Completed:
    status: int
    stdout: bytes
    timed_out: bool = False
    cancelled: bool = False


@dataclass
class Process:
    """A running child, so a cancel or a shutdown can stop it."""

    popen: subprocess.Popen[bytes]
    cancelled: bool = False


@dataclass
class SetupState:
    running: bool = False
    thread: threading.Thread | None = None


def _home() -> Path:
    # Only an absolute location counts, because a relative one would resolve inside a project.
    value = os.environ.get("HOME", "")
    return Path(value if value.startswith("/") else pwd.getpwuid(os.getuid()).pw_dir)


def _tail(data: bytes) -> str:
    return data.decode("utf-8", "replace")[-DETAIL_CHARACTERS:].strip()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _take_setup_lock(handle: TextIO) -> bool:
    """A readiness check holds this lock for an instant, so only a lasting refusal is a setup."""
    deadline = time.monotonic() + SETUP_LOCK_WAIT_SECONDS
    while True:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.02)


def stop_group(popen: subprocess.Popen[bytes]) -> None:
    """The core cleans up on SIGTERM; a process that does not stop in time is killed."""
    try:
        os.killpg(popen.pid, signal.SIGTERM)
        popen.wait(timeout=STOP_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(popen.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass


@dataclass
class Runtime:
    root: Path
    running: dict[Any, Process] = field(default_factory=dict)
    # A cancel can arrive before its call has started a process.
    cancelled_early: set[Any] = field(default_factory=set)
    guard: threading.Lock = field(default_factory=threading.Lock)
    stopping: bool = False
    setup_state: SetupState = field(default_factory=SetupState)

    def __post_init__(self) -> None:
        self.manifest = json.loads((self.root / "plugin.json").read_text(encoding="utf-8"))
        self.version = str(self.manifest["version"])
        self.home = _home()
        # A fixed location, because the host passes a server few variables, so one set only in a
        # shell would leave Terminal and the host looking in different places. Tests share a runtime.
        shared = os.environ.get("CLOUD_ARCHITECTURE_WORK_DATA", "")
        self.data = (
            Path(shared)
            if shared.startswith("/")
            else self.home / ".local/share/cloud-architecture-diagrams/work-plugin"
        )
        self.output = self.home / "Documents/CloudArchitectureDiagrams/work"

    # Where the runtime lives. The lock's digest names it, so a release with the same dependencies
    # reuses it and one with new dependencies cannot run on the old ones.
    def lock_digest(self) -> str:
        return _digest(self.root / "uv.lock")

    @property
    def environment_path(self) -> Path:
        return self.data / ("env-" + self.lock_digest()[:16])

    @property
    def marker_path(self) -> Path:
        return self.data / ("env-" + self.lock_digest()[:16] + ".ready.json")

    @property
    def failure_path(self) -> Path:
        return self.data / "setup-failure.json"

    @property
    def python(self) -> Path:
        return self.environment_path / "bin/python"

    def setup_command(self) -> str:
        return shlex.join(["python3", "-I", "-B", str(self.root / "scripts/runtime.py"), "setup"])

    def core_version(self) -> str:
        match = re.search(
            r'^version = "([^"]+)"',
            (self.root / "pyproject.toml").read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        return match.group(1) if match else "unknown"

    def installed_files_present(self) -> bool:
        # An upgrade removes the old cached copy while an older chat's process can still be running.
        return (self.root / "src/cloud_architecture_diagrams/cli.py").is_file() and (
            self.root / "uv.lock"
        ).is_file()

    def _search_path(self) -> str:
        entries = [e for e in os.environ.get("PATH", "").split(os.pathsep) if e.startswith("/")]
        return os.pathsep.join(
            dict.fromkeys(
                [*entries, *TOOL_DIRECTORIES, str(self.home / ".local/bin"), "/usr/bin", "/bin"]
            )
        )

    def find_tool(self, name: str) -> str | None:
        return shutil.which(name, path=self._search_path())

    def core_environment(self) -> dict[str, str]:
        # Nothing else is inherited, so neither the host's variables nor a project's can steer it.
        environment = {
            "PATH": self._search_path(),
            "HOME": str(self.home),
            "LANG": "C.UTF-8",
            "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        }
        return environment

    # Running children.
    def _start(self, token: Any, start: Callable[[], subprocess.Popen[bytes]]) -> Process | None:
        """Start and register as one step, so that shutdown cannot miss a child being started.

        None means this process is shutting down and nothing was started.
        """
        with self.guard:
            if self.stopping:
                return None
            process = Process(start())
            self.running[token] = process
            stop = token in self.cancelled_early
        if stop:
            process.cancelled = True
            stop_group(process.popen)
        return process

    def cancel(self, token: Any) -> None:
        with self.guard:
            process = self.running.get(token)
            if process is None:
                self.cancelled_early.add(token)
        if process is not None:
            process.cancelled = True
            threading.Thread(target=stop_group, args=(process.popen,), daemon=True).start()

    def finished(self, token: Any) -> None:
        with self.guard:
            self.cancelled_early.discard(token)

    def stop_all(self) -> None:
        with self.guard:
            self.stopping = True
            processes = list(self.running.values())
        for process in processes:
            process.cancelled = True
        threads = [
            threading.Thread(target=stop_group, args=(process.popen,), daemon=True)
            for process in processes
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(STOP_GRACE_SECONDS + 2)

    def run_core(
        self, arguments: list[str], payload: bytes | None, seconds: float, token: Any
    ) -> Completed:
        """Run the core once in its own process group, and always leave it stopped."""
        command = [
            str(self.python),
            "-I",
            "-B",
            "-c",
            BOOT,
            str(self.root / "src"),
            *arguments,
        ]
        process = self._start(
            token,
            lambda: subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL if payload is None else subprocess.PIPE,
                stdout=subprocess.PIPE,
                # A traceback can quote a value from the model, so it reaches neither the log nor
                # the host.
                stderr=subprocess.DEVNULL,
                env=self.core_environment(),
                cwd=str(self.data),
                start_new_session=True,
            ),
        )
        if process is None:
            return Completed(-1, b"", cancelled=True)
        popen = process.popen
        try:
            stdout, _ = popen.communicate(payload, timeout=seconds)
            return Completed(popen.returncode, stdout, cancelled=process.cancelled)
        except subprocess.TimeoutExpired:
            stop_group(popen)
            stdout, _ = popen.communicate()
            return Completed(popen.returncode, stdout, timed_out=True)
        finally:
            with self.guard:
                self.running.pop(token, None)

    # Setup.
    def state(self) -> dict[str, Any]:
        if self.setup_state.running or self._setup_locked_elsewhere():
            return {"state": "installing"}
        try:
            marker = json.loads(self.marker_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            marker = None
        if (
            isinstance(marker, dict)
            and marker.get("lock_sha256") == self.lock_digest()
            and self.python.is_file()
        ):
            return {"state": "ready", "environment": str(self.environment_path), **marker}
        try:
            failure = json.loads(self.failure_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            failure = None
        if isinstance(failure, dict):
            return {"state": "failed", "failure": failure}
        return {"state": "not_installed"}

    def _setup_locked_elsewhere(self) -> bool:
        try:
            with open(self.data / "setup.lock", "a") as handle:
                # Shared, because only a setup holds this lock exclusively. Two exclusive checks at
                # once would each read the other as a setup and report a ready runtime as installing.
                try:
                    fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
                except OSError:
                    return True
                fcntl.flock(handle, fcntl.LOCK_UN)
                return False
        except OSError:
            return False

    def start_setup(self) -> bool:
        """Setup can outlast a tool call, so it runs behind the call. False if one is running."""
        with self.guard:
            if self.setup_state.running:
                return False
            self.setup_state.running = True
        thread = threading.Thread(target=self._setup_in_background, daemon=True)
        self.setup_state.thread = thread
        thread.start()
        return True

    def _setup_in_background(self) -> None:
        try:
            self.setup()
        finally:
            self.setup_state.running = False

    def _record_failure(
        self, code: str, message: str, remedy: str, detail: str = ""
    ) -> dict[str, Any]:
        failure = {"code": code, "message": message, "remedy": remedy, "detail": detail}
        self.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._write_json(self.failure_path, failure)
        return {"ready": False, **failure}

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False, encoding="utf-8"
        ) as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            temporary = stream.name
        os.replace(temporary, path)

    def setup(self) -> dict[str, Any]:
        """Build or repair the private environment, then prove it can validate and render."""
        self.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(self.data / "setup.lock", "a") as handle:
            if not _take_setup_lock(handle):
                return {"ready": False, "code": "RUNTIME_SETUP_BUSY"}
            return self._setup_locked()

    def _setup_locked(self) -> dict[str, Any]:
        self.failure_path.unlink(missing_ok=True)
        try:
            return self._build()
        except SetupInterrupted:
            # Finished downloads are kept, so the next attempt resumes. Recording a failure here
            # would send the next chat looking for a cause that does not exist.
            return {"ready": False, "code": "RUNTIME_SETUP_INTERRUPTED"}

    def _build(self) -> dict[str, Any]:
        uv = self.find_tool("uv")
        if uv is None:
            return self._record_failure(
                "RUNTIME_UV_MISSING",
                "uv was not found, so the private Python environment cannot be built.",
                "Install uv, for example with: brew install uv. Then call setup_runtime again.",
            )
        # Only what could point uv at another project or interpreter goes; a proxy or cache stays.
        steering = {"VIRTUAL_ENV", "UV_PROJECT", "UV_PYTHON", "PYTHONHOME", "PYTHONPATH"}
        environment = {key: value for key, value in os.environ.items() if key not in steering}
        environment["UV_PROJECT_ENVIRONMENT"] = str(self.environment_path)
        environment["PATH"] = self._search_path()
        try:
            process = self._start(
                SETUP_TOKEN,
                lambda: subprocess.Popen(
                    [
                        uv,
                        "sync",
                        "--quiet",
                        "--system-certs",
                        "--locked",
                        "--no-dev",
                        "--no-install-project",
                        # The lock pins each wheel, but not what a source build would pull in.
                        "--no-build",
                        "--python",
                        PYTHON,
                        "--project",
                        str(self.root),
                    ],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=environment,
                    cwd=str(self.data),
                    start_new_session=True,
                ),
            )
        except OSError as error:
            return self._record_failure(
                "RUNTIME_SETUP_FAILED",
                "uv could not be started.",
                "Check that uv runs from a terminal, then call setup_runtime again.",
                type(error).__name__,
            )
        if process is None:
            raise SetupInterrupted
        sync = process.popen
        try:
            output, _ = sync.communicate(timeout=SETUP_SECONDS)
        except subprocess.TimeoutExpired:
            stop_group(sync)
            return self._record_failure(
                "RUNTIME_SETUP_TIMEOUT",
                "Building the private environment took too long and was stopped.",
                "Check the network, then call setup_runtime again; finished downloads are kept.",
            )
        finally:
            with self.guard:
                self.running.pop(SETUP_TOKEN, None)
        if process.cancelled:
            raise SetupInterrupted
        if sync.returncode != 0:
            return self._record_failure(
                "RUNTIME_SETUP_FAILED",
                "uv could not build the private environment from the locked dependencies.",
                "Read the detail, fix the cause, then call setup_runtime again.",
                _tail(output),
            )
        # The environment holds dependencies only, so this is the first real run of the core.
        checked = self.run_core(["capabilities"], None, PROBE_SECONDS, SETUP_CHECK_TOKEN)
        if checked.cancelled:
            raise SetupInterrupted
        try:
            version = json.loads(checked.stdout)["package_version"]
        except (ValueError, KeyError, TypeError):
            version = None
        if checked.status != 0 or version != self.core_version():
            return self._record_failure(
                "RUNTIME_SETUP_FAILED",
                "The private environment was built, but the core did not run from it.",
                "Run the runtime script's remove command, then call setup_runtime again.",
            )
        marker = {
            "lock_sha256": self.lock_digest(),
            "python": PYTHON,
            # A later release with the same lock reuses this runtime, so name what this describes.
            "probed_with": self.version,
            "render_probe": self.render_probe(),
        }
        self._write_json(self.marker_path, marker)
        self.failure_path.unlink(missing_ok=True)
        self._remove_old_environments()
        return {"ready": True, **marker}

    def _remove_old_environments(self) -> None:
        # Only one version of the plugin is ever installed, so only one lock's runtime is in use.
        current = {self.environment_path.name, self.marker_path.name}
        for path in self.data.iterdir():
            if ENVIRONMENT_FILE.fullmatch(path.name) and path.name not in current:
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)

    def render_probe(self) -> dict[str, Any]:
        """One real render of a bundled example where bundles really go, then remove that bundle.

        Only this proves the sandbox, fonts and folder all work from this host process. It also
        brings up the system's question about Documents during setup, not during a drawing.
        """
        example = self.root / "skills/architecture-model/examples/core-valid.json"
        try:
            ran = self.run_core(
                ["render", "--output=" + str(self.output)],
                example.read_bytes(),
                PROBE_SECONDS,
                SETUP_PROBE_TOKEN,
            )
            if ran.cancelled:
                raise SetupInterrupted
            report = json.loads(ran.stdout)
            if report.get("rendered") is True:
                bundle = str(report["bundle_id"])
                if BUNDLE.fullmatch(bundle):
                    shutil.rmtree(self.output / bundle, ignore_errors=True)
                return {"passed": True}
            codes = [
                d["code"] for d in report.get("diagnostics", []) if d.get("severity") == "error"
            ]
            return {"passed": False, "codes": codes}
        except (OSError, ValueError, KeyError, TypeError):
            return {"passed": False, "codes": ["RENDER_PROBE_FAILED"]}

    def remove(self) -> dict[str, Any]:
        """Delete only what setup made, by name. Bundles and the Claude plugin's runtime stay."""
        removed = []
        if self.data.is_dir():
            for path in sorted(self.data.iterdir()):
                if ENVIRONMENT_FILE.fullmatch(path.name) or path.name in (
                    "setup.lock",
                    "setup-failure.json",
                ):
                    if path.is_dir() and not path.is_symlink():
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        path.unlink(missing_ok=True)
                    removed.append(path.name)
            # A folder holding anything this code did not make stays, and says so by still existing.
            try:
                self.data.rmdir()
            except OSError:
                pass
        return {"runtime": str(self.data), "removed": removed, "kept": self.data.exists()}

    # Preflight.
    def _sandbox_works(self) -> bool:
        # A host can itself be sandboxed, where presence alone says nothing about permission to run.
        try:
            return (
                subprocess.run(
                    [SANDBOX, "-p", "(version 1)(allow default)(deny network*)", "/usr/bin/true"],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=PROBE_SECONDS,
                    check=False,
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            return False

    def output_blocker(self) -> dict[str, str] | None:
        """The core makes the same checks and more; this reports them before anyone draws."""
        blocked = {
            "code": "OUTPUT_ROOT_UNAVAILABLE",
            "message": "The output folder cannot be used.",
            "remedy": (
                "Make ~/Documents reachable: allow the ChatGPT app under System Settings > "
                "Privacy & Security > Files and Folders, and keep symbolic links out of the "
                "folder's path. Its own folder must not be writable by others."
            ),
        }
        existing = Path(self.output.anchor)
        try:
            for part in self.output.parts[1:]:
                try:
                    info = os.lstat(existing / part)
                except FileNotFoundError:
                    break
                if stat.S_ISLNK(info.st_mode):
                    return blocked
                existing = existing / part
            if existing == self.output:
                info = os.stat(existing)
                if info.st_uid != os.getuid() or info.st_mode & 0o022:
                    return blocked
            # Listing is what makes macOS ask, so the question comes up now and not mid-render.
            os.listdir(existing)
        except OSError:
            return blocked
        return None if os.access(existing, os.W_OK) else blocked

    def preflight(self) -> dict[str, Any]:
        """Facts about this machine, checked live, because any of them can change after setup."""
        checks: list[dict[str, Any]] = []
        blockers: list[dict[str, str]] = []

        def check(name: str, detail: str | None, code: str, message: str, remedy: str) -> None:
            checks.append({"name": name, "ok": detail is not None, "detail": detail})
            if detail is None:
                blockers.append({"code": code, "message": message, "remedy": remedy})

        system = f"{platform.system()} {platform.machine()}"
        check(
            "host",
            system if sys.platform == "darwin" else None,
            "HOST_UNSUPPORTED",
            "Rendering needs the macOS sandbox, and this system does not have it.",
            "Use a Mac. Only macOS on Apple silicon has been tested.",
        )
        # Found, not run: PATH chooses these binaries, and this check is read-only. The core reads
        # Graphviz's version under its sandbox when it renders, and records it in the manifest.
        check(
            "uv",
            self.find_tool("uv"),
            "RUNTIME_UV_MISSING",
            "uv was not found, so the private Python environment cannot be built.",
            "Install uv, for example with: brew install uv.",
        )
        check(
            "graphviz",
            self.find_tool("dot"),
            "RENDER_ENGINE_UNAVAILABLE",
            "Graphviz dot was not found, so nothing can be drawn.",
            "Install Graphviz, for example with: brew install graphviz.",
        )
        check(
            "sandbox",
            SANDBOX if self._sandbox_works() else None,
            "RENDER_ISOLATION_UNAVAILABLE",
            "The sandbox that isolates the renderer cannot run from this host process.",
            "Run this from the ChatGPT desktop app on a Mac, not from a sandboxed shell.",
        )
        blocker = self.output_blocker()
        checks.append(
            {"name": "output_root", "ok": blocker is None, "detail": str(self.output)},
        )
        if blocker:
            blockers.append(blocker)
        return {"checks": checks, "blockers": blockers, "server_python": platform.python_version()}


def wait_for_setup(runtime: Runtime, seconds: float) -> None:
    """For tests and the CLI: waits for a background setup without touching its state."""
    thread = runtime.setup_state.thread
    deadline = time.monotonic() + seconds
    while thread is not None and thread.is_alive() and time.monotonic() < deadline:
        thread.join(0.1)
