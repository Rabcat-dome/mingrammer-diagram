"""M5 package contract: manifests, the built package, the tool contract and the private runtime.

Everything runs the built package as the host runs it: outside the checkout, over real pipes, from
a path with a space and a plus sign. Host-specific behavior comes from a measured probe recorded in
the S09 evidence, because CI has no account and no model. Actual Work acceptance stays manual.
"""

import ast
import base64
import hashlib
import importlib.util
import json
import os
import queue
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import zipfile
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import yaml

from cloud_architecture_diagrams.models import Architecture

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/cloud-architecture-work"
FIXTURES = ROOT / "tests/fixtures"
PLUGIN = "cloud-architecture-work"
TOOLS = {
    "get_capabilities",
    "setup_runtime",
    "get_schema",
    "search_catalog",
    "validate_model",
    "render_model",
    "read_artifact",
    "list_bundles",
}
BUNDLE_FILES = {
    "diagram.png",
    "diagram.svg",
    "model.json",
    "view.json",
    "diagnostics.json",
    "manifest.json",
}
STATUSES = {
    "ok",
    "validation_failed",
    "runtime_failure",
    "timeout",
    "artifact_unavailable",
    "runtime_unavailable",
    "invalid_arguments",
    "busy",
}
# S04 alpha.3 stays a separate frozen fixture, so a change here has to be a deliberate decision.
S04_TREE_SHA256 = "8cacd3df60940216ea12f0d562f0d903636cb58268b87686c2922a673a3f4e2d"
BUNDLE_NAME = re.compile(r"[a-z][a-z0-9._-]*--[a-z][a-z0-9._-]*--[0-9a-f]{16}")
# The host starts whatever `python3` it finds, which on a new Mac is this one. Everything runs on it,
# because a parse check says nothing about the standard library: `rmtree(dir_fd=)` got past one.
APPLE_PYTHON = "/usr/bin/python3"


def builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_work_plugin", ROOT / "scripts/build_work_plugin.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    output = tmp_path_factory.mktemp("work-build").resolve() / "release"
    return dict(builder().build(output)) | {"output": output}


@pytest.fixture(scope="module")
def package(built: dict[str, Any]) -> Path:
    return Path(built["marketplace_root"]) / "plugins" / PLUGIN


def load(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return value


def fixture(name: str) -> dict[str, Any]:
    return load(FIXTURES / name)


class Client:
    """The host's side of the stdio transport, reduced to what these tests need."""

    def __init__(self, root: Path, environment: dict[str, str], python: str = APPLE_PYTHON) -> None:
        self.process = subprocess.Popen(
            [python, "-I", "-B", str(root / "server/main.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=root,
            env=environment,
        )
        self.frames: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self.stderr: list[bytes] = []
        self.sequence = 100
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._read_errors, daemon=True).start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.frames.put(json.loads(line))
        self.frames.put(None)

    def _read_errors(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr.append(line)

    def write(self, data: bytes) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def send(self, message: dict[str, Any]) -> None:
        self.write(json.dumps(message).encode() + b"\n")

    def next_frame(self, seconds: float = 60) -> dict[str, Any]:
        frame = self.frames.get(timeout=seconds)
        assert frame is not None, "the server closed its output"
        return frame

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.sequence += 1
        self.send({"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params or {}})
        frame = self.next_frame()
        assert frame["id"] == self.sequence
        return frame

    def call(self, name: str, **arguments: Any) -> dict[str, Any]:
        frame = self.request("tools/call", {"name": name, "arguments": arguments})
        result: dict[str, Any] = frame["result"]
        return result

    def body(self, name: str, **arguments: Any) -> dict[str, Any]:
        return text_of(self.call(name, **arguments))

    def close(self) -> int:
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        return self.process.wait(timeout=30)


def text_of(result: dict[str, Any]) -> dict[str, Any]:
    assert result["content"][0]["type"] == "text"
    value: dict[str, Any] = json.loads(result["content"][0]["text"])
    assert value["status"] in STATUSES
    # A failure must carry what the caller needs, and isError must agree with the status.
    assert result["isError"] is (value["status"] != "ok")
    if value["status"] != "ok":
        assert value["code"] and value["message"] and value["remedy"]
    return value


@pytest.fixture(scope="module")
def environment(tmp_path_factory: pytest.TempPathFactory) -> dict[str, str]:
    """What the host passes a server, with a shared runtime so only one test has to build it."""
    data = tmp_path_factory.mktemp("work-data").resolve()
    cache = subprocess.check_output(["uv", "cache", "dir"], text=True).strip()
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(data / "home-unused"),
        "CLOUD_ARCHITECTURE_WORK_DATA": str(data / "work-plugin"),
        "UV_CACHE_DIR": cache,
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "LC_CTYPE": "C.UTF-8",
        **(
            {"UV_SYSTEM_CERTS": os.environ["UV_SYSTEM_CERTS"]}
            if "UV_SYSTEM_CERTS" in os.environ
            else {}
        ),
    }


@pytest.fixture(scope="module")
def installed(
    package: Path, tmp_path_factory: pytest.TempPathFactory, environment: dict[str, str]
) -> Path:
    """A relocated copy with a built runtime, reached through the setup tool."""
    copy = tmp_path_factory.mktemp("work cache+plugin").resolve() / PLUGIN
    shutil.copytree(package, copy)
    client = Client(copy, environment)
    client.request("initialize", {"protocolVersion": "2025-06-18"})
    assert client.body("setup_runtime")["result"]["started"] is True
    deadline = time.monotonic() + 150
    state = "installing"
    while time.monotonic() < deadline:
        state = client.body("get_capabilities")["result"]["runtime"]["state"]
        if state in ("ready", "failed"):
            break
        time.sleep(0.2)
    client.close()
    assert state == "ready"
    return copy


@pytest.fixture
def home(tmp_path: Path, environment: dict[str, str]) -> dict[str, str]:
    root = tmp_path.resolve() / "home"
    root.mkdir()
    return environment | {"HOME": str(root)}


@pytest.fixture
def client(installed: Path, home: dict[str, str]) -> Iterator[Client]:
    server = Client(installed, home)
    server.request("initialize", {"protocolVersion": "2025-06-18"})
    yield server
    server.close()


def output_root(environment: dict[str, str]) -> Path:
    return Path(environment["HOME"]) / "Documents/CloudArchitectureDiagrams/work"


# The package.
def test_build_holds_exactly_the_allowlisted_tree(package: Path) -> None:
    # Everything else, including research records and uncleared source packs, stays out (NFR-004).
    core = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "src").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.name != ".DS_Store"
    }
    expected = core | {
        "README.md",
        "plugin.json",
        "mcp.json",
        "pyproject.toml",
        "uv.lock",
        "scripts/runtime.py",
        "server/main.py",
        "server/work_adapter/__init__.py",
        "server/work_adapter/artifacts.py",
        "server/work_adapter/protocol.py",
        "server/work_adapter/runtime.py",
        "server/work_adapter/tools.py",
        "skills/architecture-model/SKILL.md",
        "skills/architecture-model/references/model-guide.md",
        "skills/architecture-model/examples/core-valid.json",
        "skills/architecture-model/examples/kubernetes-valid.json",
    }
    found = {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}
    assert found == expected


def test_build_has_no_symbolic_links_because_the_host_drops_them(built: dict[str, Any]) -> None:
    # Measured on the host: `plugin add` silently leaves every symbolic link out of its cache.
    root = Path(built["marketplace_root"])
    assert not [path for path in root.rglob("*") if path.is_symlink()]


def test_core_in_the_package_is_the_repository_copy(package: Path) -> None:
    for source in (ROOT / "src").rglob("*"):
        if source.is_file() and "__pycache__" not in source.parts and source.name != ".DS_Store":
            assert (package / source.relative_to(ROOT)).read_bytes() == source.read_bytes()
    assert (package / "uv.lock").read_bytes() == (ROOT / "uv.lock").read_bytes()
    assert (package / "pyproject.toml").read_bytes() == (ROOT / "pyproject.toml").read_bytes()


def test_source_links_into_one_copy_of_the_core() -> None:
    for link, target in {
        "src": "src",
        "uv.lock": "uv.lock",
        "skills/architecture-model/examples/core-valid.json": "tests/fixtures/core-valid.json",
        "skills/architecture-model/examples/kubernetes-valid.json": (
            "tests/fixtures/kubernetes-valid.json"
        ),
        "skills/architecture-model/references/model-guide.md": (
            "plugins/cloud-architecture-diagrams/skills/architecture-model/references/model-guide.md"
        ),
    }.items():
        assert (SOURCE / link).is_symlink()
        assert (SOURCE / link).resolve() == ROOT / target


def test_manifest_meets_the_host_format(package: Path) -> None:
    manifest = load(package / "plugin.json")
    assert manifest["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    assert manifest["name"] == PLUGIN == package.name
    assert re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,62}[a-z0-9]", manifest["name"])
    assert manifest["description"].strip()
    assert manifest["author"]["name"]
    # Portable clients find these at fixed locations, and top-level copies are not allowed.
    assert not {"skills", "mcpServers", "apps", "interface"} & set(manifest)
    openai = manifest["extensions"]["com.openai"]
    assert openai["requires_local_executor"] is True
    interface = openai["interface"]
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        assert isinstance(interface[key], str) and interface[key].strip()
    assert len(interface["shortDescription"]) <= 30
    assert interface["category"] == "Productivity"
    assert isinstance(interface["capabilities"], list)
    assert 1 <= len(interface["defaultPrompt"]) <= 3
    # The long description goes wherever the listing goes, so it has to carry the limit too.
    assert "private personal use only" in interface["longDescription"]


def test_version_is_strict_semver_stamped_with_the_content(built: dict[str, Any]) -> None:
    source = load(SOURCE / "plugin.json")["version"]
    assert re.fullmatch(r"\d+\.\d+\.\d+-alpha\.\d+", source), "keep the source version unstamped"
    assert built["version"] == f"{source}+{built['content_sha256'][:12]}"
    package = Path(built["marketplace_root"]) / "plugins" / PLUGIN
    assert load(package / "plugin.json")["version"] == built["version"]


def test_changing_any_file_changes_the_version(tmp_path: Path) -> None:
    module = builder()
    original = module.collect()
    changed = dict(original)
    name = "server/work_adapter/tools.py"
    changed[name] = original[name] + b"# one more line\n"
    assert module.content_digest(original) != module.content_digest(changed)
    renamed = dict(original)
    renamed["server/other.py"] = renamed.pop("server/main.py")
    assert module.content_digest(original) != module.content_digest(renamed)


def test_the_build_runs_on_the_oldest_python_and_gives_the_same_package(
    tmp_path: Path, built: dict[str, Any]
) -> None:
    # The README's install command runs on whatever `python3` the machine has.
    output = tmp_path.resolve() / "apple"
    done = subprocess.run(
        [
            APPLE_PYTHON,
            "-I",
            "-B",
            str(ROOT / "scripts/build_work_plugin.py"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)["archive_sha256"] == built["archive_sha256"]


def test_the_same_source_builds_the_same_archive(tmp_path: Path, built: dict[str, Any]) -> None:
    again = builder().build(tmp_path.resolve() / "again")
    assert again["archive_sha256"] == built["archive_sha256"]
    assert again["version"] == built["version"]


def test_archive_holds_the_marketplace_and_its_checksum_is_recorded(built: dict[str, Any]) -> None:
    output = built["output"]
    archive = output / built["archive"]
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest == built["archive_sha256"]
    assert (output / f"{built['archive']}.sha256").read_text() == f"{digest}  {built['archive']}\n"
    tree = Path(built["marketplace_root"])
    expected = {path.relative_to(tree).as_posix() for path in tree.rglob("*") if path.is_file()}
    with zipfile.ZipFile(archive) as stored:
        names = stored.namelist()
        assert stored.testzip() is None
        for name in names:
            assert name.startswith(f"{PLUGIN}-marketplace/")
            assert ".." not in Path(name).parts
    assert {name.split("/", 1)[1] for name in names} == expected


def test_build_will_not_replace_a_folder_it_did_not_make(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("the owner's file")
    with pytest.raises(SystemExit):
        builder().build(tmp_path.resolve())
    assert (tmp_path / "keep.txt").read_text() == "the owner's file"


def test_marketplace_entry_has_the_fields_the_host_requires(built: dict[str, Any]) -> None:
    root = Path(built["marketplace_root"])
    market = load(root / ".agents/plugins/marketplace.json")
    assert market["name"] == built["marketplace"]
    [entry] = market["plugins"]
    assert entry["name"] == PLUGIN
    assert (root / entry["source"]["path"]).resolve() == (root / "plugins" / PLUGIN).resolve()
    assert entry["source"]["source"] == "local"
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"
    assert entry["category"] == "Productivity"


def test_server_config_starts_the_packaged_server_in_isolation(package: Path) -> None:
    config = load(package / "mcp.json")
    assert config["$schema"] == "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
    [server] = config["mcpServers"].values()
    assert server["type"] == "stdio"
    assert server["command"] == "python3"
    assert server["args"] == ["-I", "-B", "${PLUGIN_ROOT}/server/main.py"]
    assert server["cwd"] == "${PLUGIN_ROOT}"
    assert set(server) == {"type", "command", "args", "cwd"}
    assert (package / "server/main.py").is_file()


def test_s04_fixture_stays_frozen_and_separate(built: dict[str, Any]) -> None:
    market = load(ROOT / ".agents/plugins/marketplace.json")
    assert market["name"] == "mingrammer-local" != built["marketplace"]
    [entry] = market["plugins"]
    assert entry["source"]["path"] == "./spikes/s04-local-plugin/output/cloud-architecture-diagrams"
    assert entry["name"] != PLUGIN
    listing = subprocess.check_output(
        ["git", "ls-files", "-z", "--", "spikes/s04-local-plugin"], cwd=ROOT
    )
    digests = [
        [name.decode(), hashlib.sha256((ROOT / name.decode()).read_bytes()).hexdigest()]
        for name in sorted(listing.split(b"\0"))
        if name
    ]
    assert hashlib.sha256(json.dumps(digests).encode()).hexdigest() == S04_TREE_SHA256


def test_core_stays_free_of_the_host_adapter() -> None:
    # FR-065: a later adapter reuses the core, so nothing in it may know about this host.
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text)):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not {item.split(".")[0] for item in names} & {"mcp", "work_adapter"}, path
        for host in ("work_adapter", "CODEX_HOME", "CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT"):
            assert host not in text, (path, host)


# The server's own interpreter.
def adapter_sources(root: Path) -> list[Path]:
    return [*sorted((root / "server").rglob("*.py")), root / "scripts/runtime.py"]


def test_the_lint_lane_really_covers_the_adapter() -> None:
    # A pyproject.toml in the plugin folder once made Ruff treat it as its own project, so the lane
    # passed while skipping every file here.
    assert not (SOURCE / "pyproject.toml").exists()
    listed = subprocess.check_output(
        [sys.executable, "-m", "ruff", "check", "--show-files", str(SOURCE)], cwd=ROOT, text=True
    )
    found = {Path(line).relative_to(SOURCE).as_posix() for line in listed.splitlines()}
    assert found == {path.relative_to(SOURCE).as_posix() for path in adapter_sources(SOURCE)}


def test_the_lint_lane_holds_the_adapter_to_the_oldest_python(tmp_path: Path) -> None:
    # Python 3.10 syntax in the adapter would pass on the developer's Python and fail on a new Mac.
    probe = SOURCE / "server/work_adapter/_lint_probe.py"
    probe.write_text("match 1:\n    case _:\n        pass\n")
    try:
        done = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(probe)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        probe.unlink()
    assert done.returncode != 0
    assert "3.9" in done.stdout


def test_adapter_parses_on_the_oldest_python_a_mac_ships(package: Path) -> None:
    # It runs on whatever `python3` the host finds, which on a new Mac is Apple's 3.9.
    for path in adapter_sources(package):
        ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 9))


def test_adapter_uses_only_the_standard_library(package: Path) -> None:
    allowed = set(sys.stdlib_module_names) | {"work_adapter"}
    for path in adapter_sources(package):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                assert {alias.name.split(".")[0] for alias in node.names} <= allowed, path
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert str(node.module).split(".")[0] in allowed, path


def test_the_oldest_python_is_what_these_tests_really_run() -> None:
    version = subprocess.check_output([APPLE_PYTHON, "--version"], text=True).split()[1]
    assert version.startswith("3.9."), "the suite must exercise the oldest supported interpreter"


def test_server_also_answers_on_a_current_python(package: Path, home: dict[str, str]) -> None:
    server = Client(package, home, python=sys.executable)
    version = server.request("initialize", {"protocolVersion": "2025-06-18"})
    assert version["result"]["serverInfo"]["name"] == PLUGIN
    assert server.body("get_capabilities")["status"] == "ok"
    assert server.close() == 0


# The protocol.
def test_initialize_negotiates_the_protocol_version(client: Client) -> None:
    assert client.request("initialize", {"protocolVersion": "2025-03-26"})["result"][
        "protocolVersion"
    ] == ("2025-03-26")
    newest = client.request("initialize", {"protocolVersion": "1999-01-01"})["result"]
    assert newest["protocolVersion"] == "2025-11-25"
    assert newest["capabilities"] == {"tools": {}}
    assert newest["serverInfo"]["version"].startswith("0.1.0-alpha.1+")


def test_tools_list_is_the_closed_contract(client: Client) -> None:
    tools = client.request("tools/list")["result"]["tools"]
    assert {tool["name"] for tool in tools} == TOOLS
    for tool in tools:
        assert tool["description"]
        assert tool["inputSchema"]["type"] == "object"
        # An unknown argument must fail rather than be ignored.
        assert tool["inputSchema"]["additionalProperties"] is False
        assert tool["annotations"]["destructiveHint"] is False
    writers = {tool["name"] for tool in tools if not tool["annotations"]["readOnlyHint"]}
    assert writers == {"setup_runtime", "render_model"}
    # A model may never delete anything, and retention stays the owner's call.
    assert not [name for name in TOOLS if re.search("delete|remove|prune", name)]


def test_protocol_errors_do_not_stop_the_server(client: Client) -> None:
    assert client.request("no/such/method")["error"]["code"] == -32601
    # Some clients send null rather than an empty object for a tool with no arguments.
    empty = client.request("tools/call", {"name": "list_bundles", "arguments": None})["result"]
    assert text_of(empty)["status"] == "ok"
    client.write(b"{not json\n")
    assert client.next_frame()["error"]["code"] == -32700
    client.send({"jsonrpc": "2.0", "id": 7, "params": {}})
    assert client.next_frame()["error"]["code"] == -32600
    client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert client.request("ping")["result"] == {}


@pytest.mark.parametrize(
    "request_id",
    [b"[1]", b'{"a":1}', b"true", b"null", b"1e400", b"-1e400"],
    ids=["array", "object", "boolean", "null", "overflow", "negative-overflow"],
)
def test_an_id_that_is_not_a_string_or_number_is_refused(client: Client, request_id: bytes) -> None:
    client.write(
        b'{"jsonrpc":"2.0","id":' + request_id + b',"method":"tools/call",'
        b'"params":{"name":"list_bundles","arguments":{}}}\n'
    )
    reply = client.next_frame()
    assert reply["error"]["code"] == -32600 and reply["id"] is None
    assert client.request("ping")["result"] == {}


@pytest.mark.parametrize(
    "frame",
    [
        b'{"jsonrpc":"2.0","id":1e400,"method":false}',
        b'{"jsonrpc":"2.0","id":-1e400}',
        b'{"jsonrpc":"2.0","id":[1],"method":false}',
        b'{"jsonrpc":"2.0","id":{"a":1}}',
        b'{"jsonrpc":"2.0","id":true}',
    ],
    ids=["overflow-bad-method", "overflow-no-method", "array", "object", "boolean"],
)
def test_an_invalid_request_never_sends_a_bad_id_back(client: Client, frame: bytes) -> None:
    client.write(frame + b"\n")
    reply = client.next_frame()
    assert reply["error"]["code"] == -32600 and reply["id"] is None
    assert client.request("ping")["result"] == {}


@pytest.mark.parametrize("request_id", [7, "seven", 1.5])
def test_an_invalid_request_with_a_good_id_still_names_it(client: Client, request_id: Any) -> None:
    client.send({"jsonrpc": "2.0", "id": request_id})
    reply = client.next_frame()
    assert reply["error"]["code"] == -32600 and reply["id"] == request_id


def test_an_ordinary_fractional_id_still_works(client: Client) -> None:
    client.write(b'{"jsonrpc":"2.0","id":1.5,"method":"ping"}\n')
    reply = client.next_frame()
    assert reply["id"] == 1.5 and reply["result"] == {}


def test_a_control_character_in_an_unparsable_frame_id_does_not_stop_the_server(
    client: Client,
) -> None:
    client.write(b'{"jsonrpc":"2.0","id":"a\x01b",oops\n')
    reply = client.next_frame()
    assert reply["error"]["code"] == -32700 and reply["id"] is None
    assert client.request("ping")["result"] == {}


def test_a_cancel_naming_an_unusable_id_does_not_stop_the_server(client: Client) -> None:
    for request_id in ([1], {"a": 1}, None, True):
        client.send(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": request_id},
            }
        )
    assert client.request("ping")["result"] == {}


PREAMBLE = """
import io, json, subprocess, sys, threading, time
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "server"))
from work_adapter import protocol, runtime, tools
box = runtime.Runtime(root)
box.data.mkdir(parents=True, exist_ok=True)
"""


def inside_the_adapter(
    package: Path, home: dict[str, str], tmp_path: Path, script: str
) -> dict[str, Any]:
    """Hold the adapter at an exact moment, on the Python the host really starts it with."""
    environment = home | {"CLOUD_ARCHITECTURE_WORK_DATA": str(tmp_path.resolve() / "data")}
    done = subprocess.run(
        [APPLE_PYTHON, "-I", "-B", "-c", PREAMBLE + script, str(package)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    value: dict[str, Any] = json.loads(done.stdout)
    return value


HELD_START = """
real = subprocess.Popen
entered = threading.Event()
children = []
def held(*args, **options):
    # The moment after the system has made the child and before anything can know about it.
    child = real(["/bin/sleep", "60"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                 stderr=subprocess.DEVNULL, start_new_session=True)
    children.append(child)
    entered.set()
    time.sleep(0.5)
    return child
subprocess.Popen = held
results = []
worker = threading.Thread(target=lambda: results.append(CALL), daemon=True)
worker.start()
assert entered.wait(20), "the call never started a child"
box.stop_all()
alive = children[0].poll() is None
children[0].kill()
worker.join(20)
started = len(children)
after = CALL
print(json.dumps({"alive": alive, "result": SHOW(results[0]), "after": SHOW(after),
                  "children": len(children), "started": started}))
"""


def held_start(call: str, show: str) -> str:
    return HELD_START.replace("CALL", call).replace("SHOW", show)


def test_shutdown_stops_a_core_caught_between_its_start_and_its_registration(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        held_start('box.run_core(["capabilities"], None, 30, 1)', "(lambda item: item.cancelled)"),
    )
    assert report["alive"] is False and report["result"] is True
    # Once stopping, a call starts nothing at all.
    assert report["after"] is True and report["children"] == report["started"] == 1


def test_shutdown_stops_setup_caught_between_its_start_and_its_registration(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package, home, tmp_path, held_start("box.setup()", '(lambda item: item.get("code"))')
    )
    assert report["alive"] is False
    assert report["result"] == report["after"] == "RUNTIME_SETUP_INTERRUPTED"
    assert report["children"] == report["started"] == 1


def test_a_readiness_check_reads_only_a_setup_as_a_setup(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
import fcntl
lock = box.data / "setup.lock"
with open(lock, "a") as other:
    # Another call's readiness check, caught in its instant.
    fcntl.flock(other, fcntl.LOCK_SH)
    check = box._setup_locked_elsewhere()
    state_during_check = box.state()["state"]
    fcntl.flock(other, fcntl.LOCK_UN)
    # A setup, here or in another chat's process.
    fcntl.flock(other, fcntl.LOCK_EX)
    setup = box._setup_locked_elsewhere()
    state_during_setup = box.state()["state"]
print(json.dumps({"check": check, "state_during_check": state_during_check, "setup": setup,
                  "state_during_setup": state_during_setup}))
""",
    )
    assert report == {
        "check": False,
        "state_during_check": "not_installed",
        "setup": True,
        "state_during_setup": "installing",
    }


def test_setup_waits_out_a_readiness_check_but_not_a_setup(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
import fcntl
lock = box.data / "setup.lock"
other = open(lock, "a")
fcntl.flock(other, fcntl.LOCK_SH)
threading.Timer(0.2, lambda: fcntl.flock(other, fcntl.LOCK_UN)).start()
with open(lock, "a") as mine:
    waited = runtime._take_setup_lock(mine)
    fcntl.flock(mine, fcntl.LOCK_UN)
fcntl.flock(other, fcntl.LOCK_EX)
started = time.monotonic()
outcome = box.setup()
took = time.monotonic() - started
print(json.dumps({"waited": waited, "code": outcome.get("code"), "ready": outcome.get("ready"),
                  "gave_up_in_time": 0.9 <= took < 5}))
""",
    )
    assert report == {
        "waited": True,
        "code": "RUNTIME_SETUP_BUSY",
        "ready": False,
        "gave_up_in_time": True,
    }


def test_parallel_calls_on_a_ready_runtime_never_read_as_installing(client: Client) -> None:
    # The real server answered 21 of 100 of these with RUNTIME_INSTALLING.
    assert client.body("get_capabilities")["result"]["runtime"]["state"] == "ready"
    for _ in range(20):
        for number in range(5):
            client.send(
                {
                    "jsonrpc": "2.0",
                    "id": 1000 + number,
                    "method": "tools/call",
                    "params": {
                        "name": "search_catalog",
                        "arguments": {"provider": "gcp", "query": "gke", "limit": 1},
                    },
                }
            )
        bodies = [text_of(client.next_frame()["result"]) for _ in range(5)]
        assert [body.get("code") for body in bodies] == [None] * 5
        assert {body["status"] for body in bodies} == {"ok"}


def test_a_cancel_arriving_before_the_child_starts_still_stops_it(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
real = subprocess.Popen
children = []
def started(*args, **options):
    child = real(["/bin/sleep", "60"], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                 stderr=subprocess.DEVNULL, start_new_session=True)
    children.append(child)
    return child
subprocess.Popen = started
box.cancel(5)
done = box.run_core(["capabilities"], None, 30, 5)
print(json.dumps({"cancelled": done.cancelled, "alive": children[0].poll() is None}))
""",
    )
    assert report == {"cancelled": True, "alive": False}


def test_a_cancel_arriving_as_a_call_ends_leaves_no_token(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
output = io.BytesIO()
server = protocol.Server(tools.Toolbox(box), output)
finish = box.finished
def late(token):
    finish(token)
    server.cancel({"requestId": token})
box.finished = late
server.calls[7] = threading.current_thread()
server._run_call(7, "list_bundles", {}, False)
print(json.dumps({"tokens": len(box.cancelled_early), "answered": bool(output.getvalue())}))
""",
    )
    assert report == {"tokens": 0, "answered": True}


def test_an_unexpected_failure_on_a_frame_is_answered_and_the_server_goes_on(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
output = io.BytesIO()
server = protocol.Server(tools.Toolbox(box), output)
def broken(frame):
    raise RuntimeError("secret from the frame")
server.handle = broken
server.read_frames(io.BytesIO(b"one\\ntwo\\n"))
text = output.getvalue().decode()
print(json.dumps({"replies": len(text.splitlines()), "leaked": "secret" in text}))
""",
    )
    assert report == {"replies": 2, "leaked": False}


def test_the_stop_signal_still_gets_through_the_frame_guard(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
server = protocol.Server(tools.Toolbox(box), io.BytesIO())
def stopping(frame):
    raise protocol.Stop
server.handle = stopping
try:
    server.read_frames(io.BytesIO(b"one\\n"))
    stopped = False
except protocol.Stop:
    stopped = True
print(json.dumps({"stopped": stopped}))
""",
    )
    assert report == {"stopped": True}


def test_oversize_frame_is_refused_by_id_and_the_server_goes_on(client: Client) -> None:
    padding = "x" * (5 * 1024 * 1024)
    client.write(
        json.dumps(
            {"jsonrpc": "2.0", "id": 55, "method": "tools/call", "params": {"pad": padding}}
        ).encode()
        + b"\n"
    )
    frame = client.next_frame()
    assert frame["id"] == 55
    assert frame["error"]["code"] == -32600
    assert client.request("ping")["result"] == {}


def test_repeated_key_is_refused_rather_than_silently_lost(client: Client) -> None:
    client.write(
        b'{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"name":"validate_model",'
        b'"arguments":{"model":{"metadata":{"id":"a","id":"b"}}}}}\n'
    )
    assert text_of(client.next_frame()["result"])["code"] == "MODEL_REPEATED_KEY"


def test_end_of_input_ends_the_server_cleanly(installed: Path, home: dict[str, str]) -> None:
    server = Client(installed, home)
    assert server.close() == 0


def test_terminate_signal_ends_the_server_cleanly(installed: Path, home: dict[str, str]) -> None:
    server = Client(installed, home)
    server.request("ping")
    server.process.send_signal(signal.SIGTERM)
    assert server.process.wait(timeout=20) == 0


def test_hostile_environment_and_working_directory_change_nothing(
    installed: Path, home: dict[str, str], tmp_path: Path
) -> None:
    planted = tmp_path / "planted"
    planted.mkdir()
    marker = planted / "ran"
    (planted / "json.py").write_text(f"open({str(marker)!r}, 'w').close()\n")
    hostile = home | {"PYTHONPATH": str(planted), "PYTHONHOME": str(planted)}
    process = subprocess.run(
        [APPLE_PYTHON, "-I", "-B", str(installed / "server/main.py")],
        input=b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n',
        capture_output=True,
        cwd=planted,
        env=hostile,
        timeout=30,
        check=False,
    )
    assert json.loads(process.stdout)["result"] == {}
    assert not marker.exists()


# The private runtime.
def test_fresh_machine_reports_setup_rather_than_failing(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    fresh = home | {"CLOUD_ARCHITECTURE_WORK_DATA": str(tmp_path.resolve() / "empty-data")}
    server = Client(package, fresh)
    server.request("initialize", {"protocolVersion": "2025-06-18"})
    report = server.body("get_capabilities")["result"]
    assert report["runtime"]["state"] == "not_installed"
    assert report["render_available"] is False
    assert report["core"] is None
    assert [item["code"] for item in report["blockers"]] == ["RUNTIME_NOT_READY"]
    assert report["plugin"]["version"] == load(package / "plugin.json")["version"]
    for name, arguments in (
        ("get_schema", {}),
        ("search_catalog", {"provider": "aws"}),
        ("validate_model", {"model": fixture("core-valid.json")}),
        ("render_model", {"model": fixture("core-valid.json")}),
    ):
        body = server.body(name, **arguments)
        assert body["status"] == "runtime_unavailable"
        assert body["code"] == "RUNTIME_NOT_READY"
    assert server.close() == 0


def test_setup_builds_the_locked_runtime_and_leaves_the_plugin_unchanged(
    installed: Path, environment: dict[str, str], package: Path
) -> None:
    before = {
        path.relative_to(installed).as_posix(): path.read_bytes()
        for path in installed.rglob("*")
        if path.is_file()
    }
    assert before == {
        path.relative_to(package).as_posix(): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }
    data = Path(environment["CLOUD_ARCHITECTURE_WORK_DATA"])
    digest = hashlib.sha256((installed / "uv.lock").read_bytes()).hexdigest()
    environment_path = data / f"env-{digest[:16]}"
    assert (environment_path / "bin/python").exists()
    marker = load(data / f"env-{digest[:16]}.ready.json")
    assert marker["lock_sha256"] == digest
    assert marker["render_probe"] == {"passed": True}
    assert marker["probed_with"] == load(installed / "plugin.json")["version"]
    # Only dependencies go in, so no build backend runs and the wheel is not installed there.
    site = next(environment_path.glob("lib/python*/site-packages"))
    assert not (site / "cloud_architecture_diagrams").exists()
    assert (site / "pydantic").is_dir() and (site / "diagrams").is_dir()
    # Development tools stay out of what ships to every machine.
    assert not {"pytest", "ruff", "mypy", "build"} & {path.name for path in site.iterdir()}
    version = subprocess.check_output(
        [
            environment_path / "bin/python",
            "-I",
            "-c",
            "import platform;print(platform.python_version())",
        ],
        text=True,
    )
    assert version.strip() == "3.13.7"
    # The probe renders where bundles go, then takes its bundle away again.
    assert not list(
        (Path(environment["HOME"]) / "Documents/CloudArchitectureDiagrams/work").iterdir()
    )


def test_a_changed_lock_needs_a_new_runtime_rather_than_using_the_old_one(
    installed: Path, home: dict[str, str], tmp_path: Path
) -> None:
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(installed, copy)
    with (copy / "uv.lock").open("a") as stream:
        stream.write("# changed\n")
    server = Client(copy, home)
    assert server.body("get_capabilities")["result"]["runtime"]["state"] != "ready"
    assert server.body("validate_model", model={})["code"] == "RUNTIME_NOT_READY"
    server.close()


def wait_for_setup(server: Client, seconds: float = 120) -> dict[str, Any]:
    server.body("setup_runtime")
    deadline = time.monotonic() + seconds
    report: dict[str, Any] = {}
    while time.monotonic() < deadline:
        report = server.body("get_capabilities")["result"]
        if report["runtime"]["state"] in ("ready", "failed"):
            return report
        time.sleep(0.1)
    raise AssertionError(report)


def test_a_stale_lock_is_a_reported_setup_failure(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    # A lock that no longer matches the project must stop setup, and never be rewritten in place.
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(package, copy)
    project = copy / "pyproject.toml"
    project.write_text(project.read_text().replace('"pydantic>=2.12,<3"', '"pydantic>=2.13,<3"'))
    lock = (copy / "uv.lock").read_bytes()
    fresh = home | {"CLOUD_ARCHITECTURE_WORK_DATA": str(tmp_path.resolve() / "data")}
    server = Client(copy, fresh)
    report = wait_for_setup(server)
    assert report["runtime"]["state"] == "failed"
    assert report["runtime"]["failure"]["code"] == "RUNTIME_SETUP_FAILED"
    assert report["runtime"]["failure"]["detail"]
    assert server.body("validate_model", model={})["status"] == "runtime_unavailable"
    assert (copy / "uv.lock").read_bytes() == lock
    server.close()


def test_missing_tools_are_named_with_their_fix(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(package, copy)
    source = copy / "server/work_adapter/runtime.py"
    source.write_text(
        source.read_text().replace(
            'TOOL_DIRECTORIES = ("/opt/homebrew/bin", "/usr/local/bin")', "TOOL_DIRECTORIES = ()"
        )
    )
    fresh = home | {
        "CLOUD_ARCHITECTURE_WORK_DATA": str(tmp_path.resolve() / "data"),
        "PATH": "/usr/bin:/bin",
    }
    server = Client(copy, fresh, python="/usr/bin/python3")
    report = server.body("get_capabilities")["result"]
    codes = {item["code"] for item in report["blockers"]}
    assert {"RUNTIME_UV_MISSING", "RENDER_ENGINE_UNAVAILABLE"} <= codes
    assert all(item["remedy"] for item in report["blockers"])
    report = wait_for_setup(server)
    assert report["runtime"]["failure"]["code"] == "RUNTIME_UV_MISSING"
    assert "brew install uv" in report["runtime"]["failure"]["remedy"]
    server.close()


def test_a_process_whose_version_was_replaced_says_so(
    installed: Path, home: dict[str, str], tmp_path: Path
) -> None:
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(installed, copy)
    server = Client(copy, home)
    assert server.body("get_capabilities")["status"] == "ok"
    # The host removes the whole folder of the version it replaces.
    shutil.rmtree(copy)
    calls: tuple[tuple[str, dict[str, Any]], ...] = (
        ("validate_model", {"model": {}}),
        ("get_capabilities", {}),
        ("setup_runtime", {}),
        ("get_schema", {}),
    )
    for name, arguments in calls:
        body = server.body(name, **arguments)
        assert body["status"] == "runtime_unavailable", name
        assert body["code"] == "PLUGIN_UPDATED", name
        assert "new chat" in body["remedy"]
    server.close()


def test_runtime_script_covers_preflight_and_removal(
    package: Path, home: dict[str, str], environment: dict[str, str]
) -> None:
    # This one uses the real location under a throwaway home, which removal must clean exactly.
    fresh = {key: value for key, value in home.items() if key != "CLOUD_ARCHITECTURE_WORK_DATA"}
    script = [APPLE_PYTHON, "-I", "-B", str(package / "scripts/runtime.py")]
    parent = Path(fresh["HOME"]) / ".local/share/cloud-architecture-diagrams"
    sibling = parent / "claude-plugin"
    sibling.mkdir(parents=True)
    unready = subprocess.run([*script, "preflight"], env=fresh, capture_output=True, check=False)
    assert unready.returncode == 1
    assert json.loads(unready.stdout)["runtime"]["state"] == "not_installed"
    done = subprocess.run([*script, "setup"], env=fresh, capture_output=True, check=False)
    assert done.returncode == 0, done.stdout
    assert json.loads(done.stdout)["ready"] is True
    ready = subprocess.run([*script, "preflight"], env=fresh, capture_output=True, check=False)
    assert ready.returncode == 0, ready.stdout
    assert (parent / "work-plugin").is_dir()
    removed = subprocess.run([*script, "remove"], env=fresh, capture_output=True, check=False)
    assert removed.returncode == 0
    assert not (parent / "work-plugin").exists()
    assert sibling.is_dir(), "the Claude plugin's runtime is not this adapter's to remove"


def test_setup_clears_the_runtime_of_an_earlier_lock_and_removal_only_what_it_made(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    data = tmp_path.resolve() / "data"
    old = data / "env-0000000000000000"
    (old / "bin").mkdir(parents=True)
    (data / "env-0000000000000000.ready.json").write_text("{}")
    (data / "notes.txt").write_text("not the plugin's")
    fresh = home | {"CLOUD_ARCHITECTURE_WORK_DATA": str(data)}
    script = [APPLE_PYTHON, "-I", "-B", str(package / "scripts/runtime.py")]
    done = subprocess.run([*script, "setup"], env=fresh, capture_output=True, check=False)
    assert json.loads(done.stdout)["ready"] is True, done.stdout
    assert not old.exists()
    assert not (data / "env-0000000000000000.ready.json").exists()
    removed = subprocess.run([*script, "remove"], env=fresh, capture_output=True, check=False)
    report = json.loads(removed.stdout)
    assert report["kept"] is True
    assert [path.name for path in data.iterdir()] == ["notes.txt"]


def fake_uv(package: Path, home: dict[str, str], tmp_path: Path) -> tuple[Path, dict[str, str]]:
    """A copy whose setup hangs in a stand-in for uv, to see what stopping it leaves behind."""
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(package, copy)
    source = copy / "server/work_adapter/runtime.py"
    source.write_text(
        source.read_text().replace(
            'TOOL_DIRECTORIES = ("/opt/homebrew/bin", "/usr/local/bin")', "TOOL_DIRECTORIES = ()"
        )
    )
    tools = tmp_path.resolve() / "bin"
    tools.mkdir()
    uv = tools / "uv"
    uv.write_text('#!/bin/sh\necho $$ > "$HOME/uv.pid"\nexec sleep 300\n')
    uv.chmod(0o755)
    return copy, home | {
        "CLOUD_ARCHITECTURE_WORK_DATA": str(tmp_path.resolve() / "data"),
        "PATH": f"{tools}:/usr/bin:/bin",
    }


def wait_for_file(path: Path) -> int:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if path.exists() and path.read_text().strip():
            return int(path.read_text())
        time.sleep(0.02)
    raise AssertionError(f"{path} never appeared")


def test_stopping_during_setup_records_no_false_cause(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    copy, environment = fake_uv(package, home, tmp_path)
    server = Client(copy, environment)
    assert server.body("setup_runtime")["result"]["started"] is True
    pid = wait_for_file(Path(home["HOME"]) / "uv.pid")
    report = server.body("get_capabilities")["result"]
    assert report["runtime"]["state"] == "installing"
    # While setup runs, the answer is to wait, never to start it again.
    assert "RUNTIME_INSTALLING" in {item["code"] for item in report["blockers"]}
    assert "RUNTIME_NOT_READY" not in {item["code"] for item in report["blockers"]}
    assert server.body("validate_model", model={})["code"] == "RUNTIME_INSTALLING"
    assert server.close() == 0
    wait_until_stopped(pid)
    assert not (tmp_path / "data/setup-failure.json").exists()
    next_chat = Client(copy, environment)
    state = next_chat.body("get_capabilities")["result"]["runtime"]
    assert state == {"state": "not_installed"}
    assert next_chat.body("validate_model", model={})["code"] == "RUNTIME_NOT_READY"
    next_chat.close()


def test_setup_refuses_a_source_build(package: Path, home: dict[str, str], tmp_path: Path) -> None:
    # The lock pins each wheel, and not what a build would pull in. The real setup runs with this.
    copy, environment = fake_uv(package, home, tmp_path)
    (tmp_path.resolve() / "bin/uv").write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/uv.arguments"\n'
        'echo $$ > "$HOME/uv.pid"\nexec sleep 300\n'
    )
    server = Client(copy, environment)
    assert server.body("setup_runtime")["result"]["started"] is True
    pid = wait_for_file(Path(home["HOME"]) / "uv.pid")
    arguments = (Path(home["HOME"]) / "uv.arguments").read_text().split()
    assert {"sync", "--locked", "--no-dev", "--no-install-project", "--no-build"} <= set(arguments)
    assert server.close() == 0
    wait_until_stopped(pid)


def test_a_client_request_id_cannot_cancel_setup(
    installed: Path, home: dict[str, str], tmp_path: Path
) -> None:
    # A call in flight under the ID "setup", cancelled while real setup runs, stops only that call.
    copy, environment = fake_uv(installed, home, tmp_path)
    write_stand_in(copy)
    environment["CLOUD_ARCHITECTURE_WORK_DATA"] = home["CLOUD_ARCHITECTURE_WORK_DATA"]
    server = Client(copy, environment)
    server.send(
        {
            "jsonrpc": "2.0",
            "id": "setup",
            "method": "tools/call",
            "params": {"name": "render_model", "arguments": {"model": behaving("sleep")}},
        }
    )
    render = wait_for_file(Path(home["HOME"]) / "stand-in.pid")
    assert server.body("setup_runtime")["result"]["started"] is True
    setup = wait_for_file(Path(home["HOME"]) / "uv.pid")
    server.send(
        {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": "setup"}}
    )
    wait_until_stopped(render)
    assert server.request("ping")["result"] == {}
    assert not pid_stopped(setup)
    assert server.close() == 0
    wait_until_stopped(setup)


def test_stopping_during_the_setup_probe_writes_no_marker(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(package, copy)
    write_stand_in(copy)
    (copy / "skills/architecture-model/examples/core-valid.json").write_text(
        json.dumps(behaving("sleep"))
    )
    data = tmp_path.resolve() / "data"
    fresh = home | {"CLOUD_ARCHITECTURE_WORK_DATA": str(data)}
    server = Client(copy, fresh)
    server.body("setup_runtime")
    pid = wait_for_file(Path(home["HOME"]) / "stand-in.pid")
    assert server.close() == 0
    wait_until_stopped(pid)
    assert not list(data.glob("*.ready.json"))
    assert not (data / "setup-failure.json").exists()


# Discovery.
def test_capabilities_state_the_runtime_limits_and_host_modes(client: Client) -> None:
    report = client.body("get_capabilities")["result"]
    assert report["runtime"]["state"] == "ready"
    assert report["render_available"] is True
    assert report["blockers"] == []
    assert report["setup_command"].endswith("/scripts/runtime.py' setup")
    assert report["core_version"] == report["core"]["package_version"]
    assert report["core"]["render"]["limits"]["view_entities"] == 200
    assert {check["name"] for check in report["checks"]} == {
        "host",
        "uv",
        "graphviz",
        "sandbox",
        "output_root",
    }
    modes = report["host_modes"]
    assert "Work mode" in modes["selected"]
    assert any("web" in item for item in modes["not_supported"])
    assert any("cloud" in item for item in modes["not_supported"])
    assert report["artifacts"]["root"].endswith("Documents/CloudArchitectureDiagrams/work")
    assert "until you remove them" in report["artifacts"]["retention"]
    # The Huawei limit must stay visible at the point of discovery.
    assert [item["id"] for item in report["core"]["release_blockers"]] == ["O-002"]


def test_schema_tool_returns_the_core_schema(client: Client) -> None:
    assert client.body("get_schema")["result"] == Architecture.model_json_schema()


def test_catalog_search_is_filterable_and_bounded(client: Client) -> None:
    found = client.body("search_catalog", provider="aws", query="load balancer", limit=2)["result"]
    assert 0 < found["returned"] <= 2
    assert all("aws" in record["providers"] for record in found["records"])
    assert client.body("search_catalog", type_id="aws.storage.s3")["result"]["returned"] == 1
    assert client.body("search_catalog", kubernetes=True, limit=1)["result"]["truncated"] is True
    taxonomy = client.body("search_catalog", list_taxonomy=True)["result"]["taxonomy"]
    assert taxonomy
    # The joined option form keeps a value from reading as another option.
    dash = client.body("search_catalog", query="--provider=aws")
    assert dash["status"] == "ok" and dash["result"]["returned"] == 0


@pytest.mark.parametrize(
    ("tool", "arguments"),
    [
        ("search_catalog", {"provider": "ibm"}),
        ("search_catalog", {"entity": "thing"}),
        ("search_catalog", {"limit": 0}),
        ("search_catalog", {"limit": 201}),
        ("search_catalog", {"limit": True}),
        ("search_catalog", {"query": 7}),
        ("search_catalog", {"query": "x" * 257}),
        ("search_catalog", {"query": "nul\x00byte"}),
        ("search_catalog", {"query": "line\nbreak"}),
        ("search_catalog", {"query": "\ud800"}),
        ("search_catalog", {"kubernetes": "yes"}),
        ("search_catalog", {"unexpected": 1}),
        ("get_capabilities", {"unexpected": 1}),
        ("validate_model", {}),
        ("validate_model", {"model": "{}"}),
        ("validate_model", {"model": []}),
        ("validate_model", {"model": {}, "mode": "loose"}),
        ("validate_model", {"model": {}, "view": "--output=/etc"}),
        ("validate_model", {"model": {}, "view": 3}),
        ("render_model", {}),
        ("render_model", {"model": {}, "bundle_id": "a--b--0123456789abcdef"}),
        ("render_model", {"bundle_id": 3}),
        ("render_model", {"model": {}, "output": "/etc"}),
        ("read_artifact", {"bundle_id": "a--b--0123456789abcdef"}),
        ("read_artifact", {"file": "model.json"}),
        ("read_artifact", {"bundle_id": 1, "file": 2}),
        ("list_bundles", {"limit": 0}),
        ("list_bundles", {"limit": 101}),
        ("list_bundles", {"limit": "5"}),
        ("no_such_tool", {}),
    ],
)
def test_bad_arguments_are_refused_before_anything_runs(
    client: Client, tool: str, arguments: dict[str, Any]
) -> None:
    body = client.body(tool, **arguments)
    assert body["status"] == "invalid_arguments"
    assert body["code"] == "INVALID_ARGUMENTS"
    assert "/etc" not in json.dumps(body), "a rejected value is never echoed"


# Validation.
def test_valid_model_passes_through_the_core_result(client: Client) -> None:
    body = client.body("validate_model", model=fixture("kubernetes-valid.json"), view="compact")
    assert body["status"] == "ok"
    result = body["result"]
    assert result["valid"] is True
    assert result["validation_scope"] == "core_catalog_provider"
    assert result["selected_view"] == "compact"
    assert result["pending_checks"] == ["render"]
    assert set(result["view_exclusions"]) == {"detail", "compact"}


def test_invalid_model_is_a_validation_failure_with_its_diagnostics(client: Client) -> None:
    model = fixture("core-valid.json")
    model["views"][0]["entity_refs"] = ["does-not-exist"]
    body = client.body("validate_model", model=model)
    assert body["status"] == "validation_failed"
    assert body["code"] == body["result"]["diagnostics"][0]["code"] == "REFERENCE_MISSING"
    assert body["result"]["valid"] is False


def test_lenient_turns_only_an_unknown_type_into_a_draft(client: Client) -> None:
    model = fixture("core-valid.json")
    model["resources"][0]["service_type"] = "aws.made.up"
    assert client.body("validate_model", model=model)["status"] == "validation_failed"
    lenient = client.body("validate_model", model=model, mode="lenient")
    assert lenient["status"] == "ok"
    assert lenient["result"]["draft"] is True
    assert client.body("render_model", model=model)["status"] == "validation_failed"
    drawn = client.body("render_model", model=model, mode="lenient")
    assert drawn["status"] == "ok"
    assert drawn["result"]["draft"] is True


def test_oversize_and_unencodable_models_get_a_core_diagnostic(client: Client) -> None:
    model = fixture("core-valid.json")
    model["metadata"]["description"] = "x" * (1024 * 1024 + 8)
    assert client.body("validate_model", model=model)["status"] == "validation_failed"
    model = fixture("core-valid.json")
    model["metadata"]["title"] = "\ud800"
    body = client.body("validate_model", model=model)
    assert body["status"] == "validation_failed"
    assert body["code"]


def test_too_deep_model_is_refused_without_crashing(client: Client) -> None:
    deep: dict[str, Any] = {}
    for _ in range(70):
        deep = {"a": deep}
    assert client.body("validate_model", model=deep)["status"] == "validation_failed"
    assert client.request("ping")["result"] == {}


# Rendering and retrieval.
def published(body: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assert body["status"] == "ok", body
    assert body["result"]["rendered"] is True
    return {item["name"]: item for item in body["result"]["artifacts"]}


def test_render_publishes_a_verified_bundle_with_a_preview(
    client: Client, home: dict[str, str]
) -> None:
    result = client.call("render_model", model=fixture("core-valid.json"))
    body = text_of(result)
    files = published(body)
    assert set(files) == BUNDLE_FILES
    root = output_root(home)
    assert body["result"]["bundle_path"] == str(root / body["result"]["bundle_id"])
    for item in files.values():
        data = Path(item["path"]).read_bytes()
        assert len(data) == item["bytes"]
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert Path(item["path"]).parent.parent == root
    image = result["content"][1]
    assert image["type"] == "image" and image["mimeType"] == "image/png"
    assert base64.b64decode(image["data"]) == Path(files["diagram.png"]["path"]).read_bytes()
    # A host may send only structuredContent to its model, which would lose the image.
    assert "structuredContent" not in result
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert BUNDLE_NAME.fullmatch(body["result"]["bundle_id"])


def test_thai_labels_survive_from_call_to_source(client: Client) -> None:
    model = fixture("core-valid.json")
    model["metadata"]["title"] = "สถาปัตยกรรมระบบ"
    model["resources"][0]["name"] = "แอปพลิเคชันหลัก"
    body = client.body("render_model", model=model)
    files = published(body)
    assert json.loads(Path(files["model.json"]["path"]).read_text(encoding="utf-8")) == model
    assert "แอปพลิเคชันหลัก" in Path(files["diagram.svg"]["path"]).read_text(encoding="utf-8")


def test_each_file_reads_back_through_the_tool(client: Client) -> None:
    body = client.body("render_model", model=fixture("core-valid.json"))
    bundle_id = body["result"]["bundle_id"]
    for name, item in published(body).items():
        answer = client.call("read_artifact", bundle_id=bundle_id, file=name)
        header = text_of(answer)
        assert header["result"]["path"] == item["path"]
        assert header["result"]["bytes"] == item["bytes"]
        content = answer["content"][1]
        if name == "diagram.png":
            assert content["type"] == "image"
            data = base64.b64decode(content["data"])
        elif name == "diagram.svg":
            assert content["resource"]["mimeType"] == "image/svg+xml"
            data = base64.b64decode(content["resource"]["blob"])
        else:
            # The model needs to read these, so they cannot be opaque.
            assert content["resource"]["mimeType"] == "application/json"
            data = content["resource"]["text"].encode()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]


def test_another_view_renders_from_the_bundle_and_ids_stay_stable(
    client: Client, home: dict[str, str]
) -> None:
    model = fixture("kubernetes-valid.json")
    first = client.body("render_model", model=model, view="detail")
    files = published(first)
    second = client.body("render_model", bundle_id=first["result"]["bundle_id"], view="compact")
    assert second["result"]["selected_view"] == "compact"
    assert second["result"]["bundle_id"] != first["result"]["bundle_id"]
    source = published(second)["model.json"]
    assert source["sha256"] == files["model.json"]["sha256"]
    # Overview and detail views of one model share every ID (T-017).
    one = json.loads(Path(files["view.json"]["path"]).read_text())
    two = json.loads(Path(published(second)["view.json"]["path"]).read_text())
    drawn = [
        {entry["id"] for key in ("nodes", "groups") for entry in view["graph"][key]}
        for view in (one, two)
    ]
    assert "cluster" in drawn[0] & drawn[1]
    assert {"pod-a", "service", "ingress", "pvc"} <= drawn[0]


def test_edit_keeps_ids_and_the_earlier_bundle(client: Client) -> None:
    model = fixture("core-valid.json")
    first = client.body("render_model", model=model)
    earlier = published(first)
    answer = client.call("read_artifact", bundle_id=first["result"]["bundle_id"], file="model.json")
    source = json.loads(answer["content"][1]["resource"]["text"])
    assert source == model
    source["resources"][0]["name"] = "Renamed application"
    second = client.body("render_model", model=source)
    updated = published(second)
    stored = json.loads(Path(updated["model.json"]["path"]).read_text())
    assert [item["id"] for item in stored["resources"]] == [
        item["id"] for item in model["resources"]
    ]
    assert stored["resources"][0]["name"] == "Renamed application"
    assert (
        hashlib.sha256(Path(earlier["model.json"]["path"]).read_bytes()).hexdigest()
        == earlier["model.json"]["sha256"]
    )
    assert updated["model.json"]["sha256"] != earlier["model.json"]["sha256"]


def test_every_reference_family_renders_through_the_tool(client: Client) -> None:
    for path in sorted((FIXTURES / "references").glob("*.json")):
        files = published(client.body("render_model", model=load(path)))
        assert set(files) == BUNDLE_FILES


def test_private_use_limit_reaches_the_tool_result(client: Client) -> None:
    body = client.body("render_model", model=load(FIXTURES / "references/huawei-web.json"))
    published(body)
    assert body["result"]["rights"]["private_use_only"] is True
    assert "D-018" in body["result"]["rights"]["distribution_limit"]
    assert any(d["code"] == "ASSET_PRIVATE_USE_ONLY" for d in body["result"]["diagnostics"])


def test_a_label_no_font_holds_is_a_validation_failure(client: Client) -> None:
    model = fixture("core-valid.json")
    model["metadata"]["title"] = "a → b"
    body = client.body("render_model", model=model)
    assert body["status"] == "validation_failed"
    assert body["code"] == "RENDER_TEXT_UNDRAWABLE"
    assert "U+2192" in body["message"]


def test_view_that_cannot_be_drawn_is_a_validation_failure(client: Client) -> None:
    model: dict[str, Any] = {
        "schema_version": "1.0.0",
        "metadata": {"id": "big", "title": "Big", "environment": "test", "assumptions": []},
        "resources": [
            {
                "id": f"r{index}",
                "name": f"Item {index}",
                "provider": "external",
                "service_type": "external.network.internet",
                "taxonomy": "external.entity",
            }
            for index in range(201)
        ],
        "views": [{"id": "all", "title": "All", "entity_refs": [f"r{i}" for i in range(201)]}],
    }
    body = client.body("render_model", model=model)
    assert body["status"] == "validation_failed"
    assert body["code"] == "RENDER_VIEW_TOO_LARGE"
    assert "Split" in body["remedy"]


def test_unsafe_output_root_is_a_runtime_failure_and_nothing_publishes(
    client: Client, home: dict[str, str]
) -> None:
    root = output_root(home)
    root.mkdir(parents=True)
    root.chmod(0o777)
    body = client.body("render_model", model=fixture("core-valid.json"))
    assert body["status"] == "runtime_failure"
    assert body["code"] == "RENDER_OUTPUT_PATH_UNSAFE"
    root.chmod(0o700)
    assert not list(root.iterdir())
    blockers = client.body("get_capabilities")["result"]["blockers"]
    assert blockers == []


def test_capabilities_name_an_unusable_output_root(client: Client, home: dict[str, str]) -> None:
    root = output_root(home)
    root.parent.mkdir(parents=True)
    root.symlink_to(root.parent)
    report = client.body("get_capabilities")["result"]
    assert report["render_available"] is False
    assert [item["code"] for item in report["blockers"]] == ["OUTPUT_ROOT_UNAVAILABLE"]
    assert client.body("render_model", model=fixture("core-valid.json"))["status"] != "ok"
    # An unusable root must not read as an empty one, which would look like nothing to do.
    assert client.body("list_bundles")["code"] == "ARTIFACT_UNSAFE"
    root.unlink()


@pytest.mark.parametrize("command", [["list"], ["prune", "--older-than-days", "1"]])
def test_runtime_script_reports_an_unusable_root_rather_than_nothing(
    installed: Path, home: dict[str, str], command: list[str]
) -> None:
    root = output_root(home)
    root.parent.mkdir(parents=True)
    root.symlink_to(root.parent)
    done = subprocess.run(
        [APPLE_PYTHON, "-I", "-B", str(installed / "scripts/runtime.py"), *command],
        env=home,
        capture_output=True,
        check=False,
    )
    assert done.returncode == 1
    assert json.loads(done.stdout)["code"] == "OUTPUT_ROOT_UNAVAILABLE"


# Artifact scope.
def rendered_bundle(client: Client, home: dict[str, str]) -> tuple[str, Path]:
    body = client.body("render_model", model=fixture("core-valid.json"))
    return body["result"]["bundle_id"], output_root(home) / body["result"]["bundle_id"]


@pytest.mark.parametrize(
    ("bundle_id", "file", "code"),
    [
        ("../../etc--passwd--0123456789abcdef", "model.json", "ARTIFACT_NAME_REFUSED"),
        ("..", "model.json", "ARTIFACT_NAME_REFUSED"),
        (".request-0123456789abcdef0123456789abcdef", "model.json", "ARTIFACT_NAME_REFUSED"),
        ("/etc/passwd", "model.json", "ARTIFACT_NAME_REFUSED"),
        ("a--b--NOTHEX", "model.json", "ARTIFACT_NAME_REFUSED"),
        ("a--b--0123456789abcdef", "../manifest.json", "ARTIFACT_NAME_REFUSED"),
        ("a--b--0123456789abcdef", "secret.txt", "ARTIFACT_NAME_REFUSED"),
        ("a--b--0123456789abcdef", "model.json", "ARTIFACT_NOT_FOUND"),
    ],
)
def test_artifact_names_outside_the_contract_are_refused(
    client: Client, bundle_id: str, file: str, code: str
) -> None:
    body = client.body("read_artifact", bundle_id=bundle_id, file=file)
    assert body["status"] == "artifact_unavailable"
    assert body["code"] == code


def test_symbolic_links_in_a_bundle_are_not_followed(
    client: Client, home: dict[str, str], tmp_path: Path
) -> None:
    bundle_id, folder = rendered_bundle(client, home)
    secret = tmp_path / "secret.json"
    secret.write_text('{"secret": true}')
    (folder / "model.json").unlink()
    (folder / "model.json").symlink_to(secret)
    body = client.body("read_artifact", bundle_id=bundle_id, file="model.json")
    assert body["code"] == "ARTIFACT_UNSAFE"
    assert "secret" not in json.dumps(body)
    assert client.body("render_model", bundle_id=bundle_id)["code"] == "ARTIFACT_UNSAFE"


def test_a_hard_link_in_a_bundle_is_not_read(
    client: Client, home: dict[str, str], tmp_path: Path
) -> None:
    bundle_id, folder = rendered_bundle(client, home)
    secret = tmp_path / "secret.json"
    secret.write_text('{"secret": true}')
    (folder / "model.json").unlink()
    os.link(secret, folder / "model.json")
    body = client.body("read_artifact", bundle_id=bundle_id, file="model.json")
    assert body["code"] == "ARTIFACT_UNSAFE"
    assert "secret" not in json.dumps(body)
    assert client.body("render_model", bundle_id=bundle_id)["code"] == "ARTIFACT_UNSAFE"


def test_a_linked_bundle_and_a_linked_root_are_not_followed(
    client: Client, home: dict[str, str], tmp_path: Path
) -> None:
    bundle_id, folder = rendered_bundle(client, home)
    moved = tmp_path / "moved"
    folder.rename(moved)
    folder.symlink_to(moved)
    assert client.body("read_artifact", bundle_id=bundle_id, file="model.json")["code"] == (
        "ARTIFACT_UNSAFE"
    )
    folder.unlink()
    root = output_root(home)
    away = tmp_path / "away"
    root.rename(away)
    root.symlink_to(away)
    assert client.body("read_artifact", bundle_id="a--b--0123456789abcdef", file="model.json")[
        "code"
    ] == ("ARTIFACT_UNSAFE")


def test_a_damaged_source_file_is_refused_rather_than_crashing(
    client: Client, home: dict[str, str]
) -> None:
    bundle_id, folder = rendered_bundle(client, home)
    (folder / "model.json").write_bytes(b"\xff\xfe not text")
    assert client.body("read_artifact", bundle_id=bundle_id, file="model.json")["code"] == (
        "ARTIFACT_INTEGRITY"
    )


def test_preflight_runs_nothing_that_path_chose(client: Client) -> None:
    # A read-only check must not execute whatever binary PATH offers; the core sandboxes its query.
    report = client.body("get_capabilities")["result"]
    details = {check["name"]: check["detail"] for check in report["checks"]}
    assert details["graphviz"].endswith("/dot")
    assert details["uv"].endswith("/uv")


def test_a_special_file_in_a_bundle_cannot_hang_a_read(
    client: Client, home: dict[str, str]
) -> None:
    bundle_id, folder = rendered_bundle(client, home)
    (folder / "view.json").unlink()
    os.mkfifo(folder / "view.json")
    body = client.body("read_artifact", bundle_id=bundle_id, file="view.json")
    assert body["code"] == "ARTIFACT_UNSAFE"


def test_a_file_over_the_transport_limit_stays_on_disk_by_path(
    client: Client, home: dict[str, str]
) -> None:
    # Measured on the host: a 16 MiB result leaves the call hanging, so this must fail first.
    bundle_id, folder = rendered_bundle(client, home)
    with (folder / "diagram.svg").open("wb") as stream:
        stream.truncate(8 * 1024 * 1024 + 1)
    body = client.body("read_artifact", bundle_id=bundle_id, file="diagram.svg")
    assert body["status"] == "artifact_unavailable"
    assert body["code"] == "ARTIFACT_TOO_LARGE"
    assert body["path"] == str(folder / "diagram.svg")


# Retention.
def test_bundles_list_newest_first_and_are_bounded(client: Client, home: dict[str, str]) -> None:
    names = []
    for _ in range(3):
        names.append(
            client.body("render_model", model=fixture("core-valid.json"))["result"]["bundle_id"]
        )
        time.sleep(0.02)
    (output_root(home) / "not-a-bundle").mkdir()
    listing = client.body("list_bundles", limit=2)["result"]
    assert [item["bundle_id"] for item in listing["bundles"]] == list(reversed(names))[:2]
    assert listing["bundles"][0]["view_id"]
    assert listing["bundles"][0]["private_use_only"] is False
    assert listing["bundles"][0]["draft"] is False
    assert "until you remove them" in listing["retention"]
    capabilities = client.body("get_capabilities")["result"]["artifacts"]
    assert capabilities["bundles"] == 3


def test_prune_reports_first_and_removes_only_old_bundles(
    client: Client, home: dict[str, str], installed: Path, tmp_path: Path
) -> None:
    old, old_folder = rendered_bundle(client, home)
    new, new_folder = rendered_bundle(client, home)
    os.utime(old_folder, (time.time() - 30 * 86400, time.time() - 30 * 86400))
    root = output_root(home)
    keep = root / "owner-notes"
    keep.mkdir()
    os.utime(keep, (time.time() - 30 * 86400, time.time() - 30 * 86400))
    outside = tmp_path / "outside--view--0123456789abcdef"
    outside.mkdir()
    (root / "link--view--0123456789abcdef").symlink_to(outside)
    script = [APPLE_PYTHON, "-I", "-B", str(installed / "scripts/runtime.py"), "prune"]
    arguments = ["--older-than-days", "7"]
    report = subprocess.run([*script, *arguments], env=home, capture_output=True, check=True)
    assert json.loads(report.stdout) == {"removed": [old], "applied": False}
    assert old_folder.is_dir()
    applied = subprocess.run(
        [*script, *arguments, "--apply"], env=home, capture_output=True, check=True
    )
    assert json.loads(applied.stdout) == {"removed": [old], "applied": True}
    assert not old_folder.exists()
    assert new_folder.is_dir() and keep.is_dir() and outside.is_dir()


def test_prune_that_cannot_finish_reports_it_rather_than_a_traceback(
    client: Client, home: dict[str, str], installed: Path
) -> None:
    _, folder = rendered_bundle(client, home)
    os.utime(folder, (time.time() - 30 * 86400, time.time() - 30 * 86400))
    folder.chmod(0o500)
    try:
        done = subprocess.run(
            [
                APPLE_PYTHON,
                "-I",
                "-B",
                str(installed / "scripts/runtime.py"),
                "prune",
                "--older-than-days",
                "7",
                "--apply",
            ],
            env=home,
            capture_output=True,
            check=False,
        )
    finally:
        folder.chmod(0o700)
    assert done.returncode == 1
    assert json.loads(done.stdout)["code"] == "OUTPUT_ROOT_UNAVAILABLE"
    assert b"Traceback" not in done.stderr


# Failure mapping, against a stand-in core that misbehaves on request.
STAND_IN = """
import hashlib, json, os, sys, time

def main():
    arguments = sys.argv[1:]
    if arguments[0] == "capabilities":
        print(json.dumps({"package_version": "VERSION", "render_available": True}))
        return 0
    if arguments[0] == "schema":
        return 1
    behavior = json.loads(sys.stdin.buffer.read())["metadata"]["id"]
    diagnostic = lambda code: {"severity": "error", "code": code, "field": "/", "message": "m", "remedy": "r"}
    if behavior == "crash":
        raise RuntimeError("SECRET-FROM-MODEL")
    if behavior == "garbage":
        print("not json")
        return 0
    if behavior == "list":
        print("[]")
        return 0
    if behavior == "exit3":
        print(json.dumps({"rendered": True}))
        return 3
    if behavior == "engine-timeout":
        print(json.dumps({"diagnostics": [diagnostic("RENDER_TIMEOUT")]}))
        return 4
    if behavior == "engine-failed":
        print(json.dumps({"diagnostics": [diagnostic("RENDER_ENGINE_FAILED")]}))
        return 4
    if behavior == "sleep":
        with open(os.path.join(os.environ["HOME"], "stand-in.pid"), "w") as stream:
            stream.write(str(os.getpid()))
        time.sleep(600)
        return 0
    output = next(a.split("=", 1)[1] for a in arguments if a.startswith("--output="))
    bundle = "stand--in--0123456789abcdef"
    folder = os.path.join(output, bundle)
    os.makedirs(folder, mode=0o700, exist_ok=True)
    names = ["diagram.png", "diagram.svg", "model.json", "view.json", "diagnostics.json", "manifest.json"]
    artifacts = []
    for name in names:
        size = 6 * 1024 * 1024 if behavior == "big-png" and name == "diagram.png" else 3
        data = b"x" * size
        with open(os.path.join(folder, name), "wb") as stream:
            stream.write(data)
        artifacts.append({"name": name, "path": os.path.join(folder, name), "bytes": size, "sha256": hashlib.sha256(data).hexdigest(), "media_type": "x"})
    if behavior == "tampered":
        artifacts[0]["sha256"] = "0" * 64
    if behavior == "missing-file":
        os.unlink(artifacts[1]["path"])
    if behavior == "short-list":
        artifacts.pop()
    print(json.dumps({"rendered": True, "bundle_id": bundle, "artifacts": artifacts, "diagnostics": []}))
    return 0
"""


def write_stand_in(copy: Path) -> None:
    found = re.search(r'^version = "([^"]+)"', (copy / "pyproject.toml").read_text(), re.MULTILINE)
    assert found
    (copy / "src/cloud_architecture_diagrams/cli.py").write_text(
        STAND_IN.replace("VERSION", found.group(1))
    )


@pytest.fixture
def stand_in(installed: Path, home: dict[str, str], tmp_path: Path) -> Iterator[Client]:
    copy = tmp_path.resolve() / "copy"
    shutil.copytree(installed, copy)
    write_stand_in(copy)
    tools = copy / "server/work_adapter/tools.py"
    tools.write_text(tools.read_text().replace("CALL_SECONDS = 58", "CALL_SECONDS = 3"))
    runtime = copy / "server/work_adapter/runtime.py"
    runtime.write_text(
        runtime.read_text().replace("STOP_GRACE_SECONDS = 10", "STOP_GRACE_SECONDS = 1")
    )
    server = Client(copy, home)
    yield server
    server.close()


def behaving(name: str) -> dict[str, Any]:
    return {"metadata": {"id": name}}


@pytest.mark.parametrize(
    ("behavior", "status", "code"),
    [
        ("crash", "runtime_failure", "CORE_CRASHED"),
        ("garbage", "runtime_failure", "CORE_CRASHED"),
        ("list", "runtime_failure", "CORE_CRASHED"),
        ("exit3", "runtime_failure", "CORE_CRASHED"),
        ("engine-timeout", "timeout", "RENDER_TIMEOUT"),
        ("engine-failed", "runtime_failure", "RENDER_ENGINE_FAILED"),
        ("tampered", "artifact_unavailable", "ARTIFACT_INTEGRITY"),
        ("missing-file", "artifact_unavailable", "ARTIFACT_NOT_FOUND"),
        ("short-list", "artifact_unavailable", "ARTIFACT_INCOMPLETE"),
    ],
)
def test_core_outcomes_map_onto_stable_statuses(
    stand_in: Client, behavior: str, status: str, code: str
) -> None:
    # FR-043, FR-063: a partial bundle is not a success, and a crash is not a result about the model.
    body = stand_in.body("render_model", model=behaving(behavior))
    assert (body["status"], body["code"]) == (status, code)
    assert "SECRET-FROM-MODEL" not in json.dumps(body)
    assert "SECRET-FROM-MODEL" not in b"".join(stand_in.stderr).decode()


def test_a_png_too_large_to_preview_stays_a_success_without_an_image(stand_in: Client) -> None:
    result = stand_in.call("render_model", model=behaving("big-png"))
    body = text_of(result)
    assert body["status"] == "ok"
    assert body["preview"].startswith("omitted")
    assert len(result["content"]) == 1


def pid_stopped(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def wait_for_pid(home: dict[str, str]) -> int:
    path = Path(home["HOME"]) / "stand-in.pid"
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if path.exists() and path.read_text():
            return int(path.read_text())
        time.sleep(0.02)
    raise AssertionError("the stand-in never started")


def wait_until_stopped(pid: int) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if pid_stopped(pid):
            return
        time.sleep(0.02)
    raise AssertionError(f"process {pid} kept running")


def test_a_call_over_its_time_limit_is_stopped_and_reported(
    stand_in: Client, home: dict[str, str]
) -> None:
    body = stand_in.body("render_model", model=behaving("sleep"))
    assert (body["status"], body["code"]) == ("timeout", "CALL_TIMEOUT")
    wait_until_stopped(int((Path(home["HOME"]) / "stand-in.pid").read_text()))


def test_a_second_render_while_one_runs_is_busy(stand_in: Client, home: dict[str, str]) -> None:
    stand_in.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "render_model", "arguments": {"model": behaving("sleep")}},
        }
    )
    wait_for_pid(home)
    body = stand_in.body("render_model", model=behaving("garbage"))
    assert (body["status"], body["code"]) == ("busy", "RENDER_BUSY")
    assert stand_in.next_frame()["id"] == 1


def test_too_many_calls_at_once_get_a_stable_busy_answer(
    package: Path, home: dict[str, str], tmp_path: Path
) -> None:
    report = inside_the_adapter(
        package,
        home,
        tmp_path,
        """
output = io.BytesIO()
toolbox = tools.Toolbox(box)
release = threading.Event()
call = toolbox.call
def held(name, arguments, token):
    release.wait(20)
    return call(name, arguments, token)
toolbox.call = held
server = protocol.Server(toolbox, output)
def frame(number):
    return json.dumps({"jsonrpc": "2.0", "id": number, "method": "tools/call",
                       "params": {"name": "list_bundles", "arguments": {}}}).encode() + b"\\n"
def answers():
    return [json.loads(line) for line in output.getvalue().decode().splitlines()]
def status(answer):
    return json.loads(answer["result"]["content"][0]["text"])
server.read_frames(io.BytesIO(b"".join(frame(number) for number in range(1, 10))))
refused = answers()
release.set()
for thread in list(server.calls.values()):
    thread.join(20)
server.read_frames(io.BytesIO(frame(10)))
later = answers()[1:]
print(json.dumps({
    "refused": [[item["id"], status(item)["status"], status(item)["code"]] for item in refused],
    "later": sorted(item["id"] for item in later),
    "statuses": sorted({status(item)["status"] for item in later}),
}))
""",
    )
    # Eight are running, so only the ninth is refused, and the first eight still get answers.
    assert report["refused"] == [[9, "busy", "TOO_MANY_CALLS"]]
    assert report["statuses"] == ["ok"] and report["later"][:8] == list(range(1, 9))


def test_the_skill_names_both_reasons_for_busy(package: Path) -> None:
    skill = (package / "skills/architecture-model/SKILL.md").read_text()
    row = next(line for line in skill.splitlines() if line.startswith("| `busy` |"))
    assert "TOO_MANY_CALLS" in row and "RENDER_BUSY" in row


def test_the_readme_says_what_reaches_the_host(package: Path) -> None:
    text = (package / "README.md").read_text()
    assert "the PNG preview" in text and "those icons reach the host" in text


def test_a_cancelled_call_stops_its_process_and_gets_no_answer(
    stand_in: Client, home: dict[str, str]
) -> None:
    stand_in.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "render_model", "arguments": {"model": behaving("sleep")}},
        }
    )
    pid = wait_for_pid(home)
    stand_in.send(
        {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 1}}
    )
    wait_until_stopped(pid)
    assert stand_in.request("ping")["result"] == {}
    with pytest.raises(queue.Empty):
        stand_in.frames.get(timeout=0.3)
    # A cancelled call must release the render it was holding.
    assert stand_in.body("render_model", model=behaving("garbage"))["code"] == "CORE_CRASHED"


def test_shutdown_stops_a_running_core(stand_in: Client, home: dict[str, str]) -> None:
    stand_in.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "render_model", "arguments": {"model": behaving("sleep")}},
        }
    )
    pid = wait_for_pid(home)
    assert stand_in.close() == 0
    wait_until_stopped(pid)


def test_a_signal_stops_a_running_core(stand_in: Client, home: dict[str, str]) -> None:
    stand_in.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "render_model", "arguments": {"model": behaving("sleep")}},
        }
    )
    pid = wait_for_pid(home)
    stand_in.process.send_signal(signal.SIGTERM)
    assert stand_in.process.wait(timeout=20) == 0
    wait_until_stopped(pid)


def test_real_core_leaves_no_scratch_when_the_server_stops_mid_render(
    client: Client, home: dict[str, str]
) -> None:
    # The core's own tests cover its cleanup; this proves the signal reaches it through the adapter.
    client.send(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "render_model",
                "arguments": {"model": load(FIXTURES / "references/hybrid-five.json")},
            },
        }
    )
    root = output_root(home)
    deadline = time.monotonic() + 30
    scratch: list[Path] = []
    while not scratch and time.monotonic() < deadline:
        scratch = list(root.glob(".request-*")) if root.exists() else []
    assert scratch, "the render never reached Graphviz, so this would prove nothing"
    assert client.close() == 0
    assert not [item.name for item in root.iterdir() if item.name.startswith(".")]


# T-014 privacy.
def test_model_content_reaches_no_log_and_no_runtime_file(
    client: Client, home: dict[str, str], environment: dict[str, str]
) -> None:
    secret = "ZZ-PRIVATE-MARKER-สถาปัตยกรรม"
    model = fixture("core-valid.json")
    model["metadata"]["title"] = secret
    model["resources"][0]["name"] = secret
    assert client.body("validate_model", model=model)["status"] == "ok"
    assert client.body("render_model", model=model)["status"] == "ok"
    invalid = json.loads(json.dumps(model))
    invalid["resources"][0]["id"] = "UPPER-" + "ZZ-PRIVATE-MARKER"
    refused = client.body("validate_model", model=invalid)
    assert refused["status"] == "validation_failed"
    assert "ZZ-PRIVATE-MARKER" not in json.dumps(refused["result"]["diagnostics"])
    client.close()
    log = b"".join(client.stderr).decode()
    assert "tool=render_model status=ok" in log
    assert "ZZ-PRIVATE-MARKER" not in log
    data = Path(environment["CLOUD_ARCHITECTURE_WORK_DATA"])
    for path in data.iterdir():
        if path.is_file():
            assert b"ZZ-PRIVATE-MARKER" not in path.read_bytes(), path


def test_the_adapter_opens_no_network_connection(package: Path) -> None:
    for path in adapter_sources(package):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import | ast.ImportFrom):
                names = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [str(node.module)]
                )
                for name in names:
                    assert name.split(".")[0] not in {"socket", "http", "urllib", "ssl"}, path


# The skill. A sentence here decides what a live session does, as the Claude plugin found out.
@pytest.fixture(scope="module")
def skill(package: Path) -> str:
    return (package / "skills/architecture-model/SKILL.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "phrase",
    [
        "Understand the request",
        "Look up exact types",
        "metadata.assumptions",
        "Call `validate_model`",
        "Fix by diagnostic",
    ],
)
def test_skill_guides_each_step_of_the_workflow(package: Path, phrase: str) -> None:
    # FR-061: requirement gathering, lookup, assumptions, validation and repair are the skill's job.
    assert phrase in (package / "skills/architecture-model/SKILL.md").read_text()


def test_skill_metadata_is_what_the_host_reads(package: Path, skill: str) -> None:
    front = yaml.safe_load(skill.split("---", 2)[1])
    assert set(front) == {"name", "description"}
    assert front["name"] == "architecture-model"
    assert len(front["description"]) <= 1024
    assert "Thai" in front["description"]
    assert "flowcharts" in front["description"]


def test_skill_names_every_tool_and_no_other(skill: str) -> None:
    assert {name for name in TOOLS if f"`{name}`" in skill} == TOOLS
    assert not {"Bash", "CLAUDE_PLUGIN_ROOT", "bin/cloud-diagrams", "mkdir", "$TMPDIR"} & {
        word
        for word in ("Bash", "CLAUDE_PLUGIN_ROOT", "bin/cloud-diagrams", "mkdir", "$TMPDIR")
        if word in skill
    }


def test_skill_explains_every_result_status(skill: str) -> None:
    for status in STATUSES:
        assert f"`{status}`" in skill


def test_skill_links_resolve_in_the_package(package: Path, skill: str) -> None:
    folder = package / "skills/architecture-model"
    links = re.findall(r"\]\(((?:references|examples)/[^)]+)\)", skill)
    assert len(links) == 3
    for link in links:
        assert (folder / link).is_file()


def test_skill_keeps_the_rules_a_live_session_depends_on(skill: str) -> None:
    for sentence in (
        # Setup is a background step, and a session must not improvise around it.
        "call `setup_runtime` once",
        "Do not install anything yourself",
        # Rendering stays inside the controlled renderer.
        "Do not fill the gap by writing `diagrams` Python, Graphviz DOT",
        # Partial views and validation limits stay disclosed.
        "must never silently drop a component",
        "does not prove that anything is deployed",
        # Edits keep identity, and old bundles stay.
        "Keep existing IDs",
        "`read_artifact`",
        # The rights limit reaches the user.
        "private personal use only",
        "never propose a generic symbol",
        # Lenient mode is not an escape.
        "It bypasses no other error",
        # Retrieval: all six files, by path.
        "link all six files",
        "`RENDER_PNG_SCALED`",
        "`PLUGIN_UPDATED`",
        # Measured on the host: tools are reached through `exec`, under these exact names, and an
        # image reaches the model only when it is forwarded.
        "`tools.mcp__cloud_architecture__render_model({model})`",
        "`ALL_TOOLS`",
        "`image(...)`",
        "`JSON.parse`",
        "`result.setup_command`",
        "as a Markdown image",
        # Measured on both hosts' sessions: without this, regions and zones draw as loose boxes.
        "the guide's section on choosing what a view selects",
        "On any other status there is no `content[1]`",
        "Only setup reaches the network",
        "`result.runtime.render_probe.passed`",
        # Measured in a live session: a missing service must stop the model guessing.
        "such as Amazon CloudFront",
    ):
        assert sentence in skill, sentence


def test_guide_describes_this_host_too(package: Path) -> None:
    guide = (package / "skills/architecture-model/references/model-guide.md").read_text()
    assert "`get_schema`" in guide and "`search_catalog`" in guide


def test_readme_states_the_modes_rights_and_the_whole_lifecycle(package: Path) -> None:
    text = (package / "README.md").read_text(encoding="utf-8")
    for needle in (
        "private personal use only",
        "Work mode",
        "web",
        "cloud",
        "macOS",
        "brew install uv graphviz",
        "codex plugin marketplace add",
        "codex plugin add cloud-architecture-work@mingrammer-work",
        "codex plugin remove cloud-architecture-work@mingrammer-work",
        "codex plugin marketplace remove mingrammer-work",
        "scripts/runtime.py",
        "prune",
        "iCloud",
        "~/.codex/sessions",
        "approve",
        "Docker",
    ):
        assert needle in text, needle
    for status in STATUSES:
        assert f"`{status}`" in text, status
