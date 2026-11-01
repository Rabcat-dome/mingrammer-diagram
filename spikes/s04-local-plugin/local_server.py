"""Local stdio-only S04 pilot. No public MCP, listener port or auth service."""
import base64
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import tempfile
import threading
from typing import Literal

from mcp.server import MCPServer
from mcp_types import BlobResourceContents, CallToolResult, EmbeddedResource, ImageContent, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict
from render_fixture import runtime_info, validate

ROOT = Path("/output")
HOST_ROOT = Path(os.environ["CLOUD_DIAGRAM_HOST_OUTPUT_ROOT"])
VERSION = os.environ["CLOUD_DIAGRAM_PLUGIN_VERSION"]
FILES = {"diagram.png", "diagram.svg", "source.dot", "source.json", "manifest.json"}
INFO = {**runtime_info(), "plugin_version": VERSION, "execution": "local stdio; network-none container"}
GATE = threading.Lock()
mcp = MCPServer("Cloud Architecture Diagrams S04", version=VERSION,
                instructions="Experimental S04 runtime: only synthetic three-node fixtures. Call get_runtime_info first. No cloud service catalog is implemented.")


class FixtureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    labels: list[str]


def failure(code):
    return CallToolResult(is_error=True, content=[TextContent(type="text", text=code)])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
def get_runtime_info() -> CallToolResult:
    """Verify this machine's local renderer versions/fonts, non-root UID and isolation configuration."""
    return CallToolResult(structured_content=INFO, content=[TextContent(type="text", text=json.dumps(INFO))])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False))
def render_fixture(request: FixtureRequest) -> CallToolResult:
    """Render exactly three literal labels locally for S04; return preview and a complete local artifact bundle."""
    request = {"node_count": 3, **request.model_dump()}
    try:
        validate(request)
    except ValueError as error:
        return failure(str(error))
    if not GATE.acquire(blocking=False):
        return failure("S04_BUSY")
    identifier = secrets.token_hex(16)
    staging = ROOT / ("." + identifier + ".part")
    try:
        with tempfile.TemporaryDirectory(prefix="s04-local-") as scratch:
            destination = Path(scratch) / "result"
            process = subprocess.Popen(
                ["python", "/app/render_fixture.py", "render", str(destination)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8",
                     "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"},
            )
            try:
                output, _ = process.communicate(json.dumps(request).encode(), timeout=55)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate(timeout=5)
                raise ValueError("S04_RENDER_TIMEOUT")
            if process.returncode:
                raise ValueError("S04_RENDER_FAILURE")
            report = json.loads(output)
            report["files"] = {name: value for name, value in report["files"].items() if name in FILES}
            report["runtime"] = INFO
            report["bundle_id"] = identifier
            report["host_paths"] = {filename: str(HOST_ROOT / identifier / filename) for filename in sorted(FILES)}
            (destination / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
            staging.mkdir()
            for filename in sorted(FILES):
                shutil.copyfile(destination / filename, staging / filename)
            os.replace(staging, ROOT / identifier)
        png = (ROOT / identifier / "diagram.png").read_bytes()
        return CallToolResult(structured_content=report,
                              content=[TextContent(type="text", text=json.dumps(report)),
                                       ImageContent(type="image", data=base64.b64encode(png).decode(), mime_type="image/png")])
    except ValueError as error:
        shutil.rmtree(staging, ignore_errors=True)
        return failure(str(error))
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    finally:
        GATE.release()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
def read_fixture_artifact(bundle_id: str, filename: Literal["diagram.png", "diagram.svg", "source.dot", "source.json", "manifest.json"]) -> CallToolResult:
    """Read a file from this pilot's local output root; never read an arbitrary path."""
    if not re.fullmatch(r"[a-f0-9]{32}", bundle_id):
        return failure("S04_INVALID_BUNDLE")
    directory = ROOT / bundle_id
    path = directory / filename
    if directory.is_symlink() or path.is_symlink() or not path.is_file():
        return failure("S04_ARTIFACT_UNAVAILABLE")
    if path.stat().st_size > 16 * 1024 * 1024:
        return failure("S04_ARTIFACT_LIMIT")
    mime = {"png": "image/png", "svg": "image/svg+xml", "json": "application/json", "dot": "text/plain"}[filename.rsplit(".", 1)[1]]
    content = EmbeddedResource(type="resource", resource=BlobResourceContents(
        uri="artifact://" + bundle_id + "/" + filename, mime_type=mime,
        blob=base64.b64encode(path.read_bytes()).decode()))
    return CallToolResult(content=[content])


if __name__ == "__main__":
    mcp.run(transport="stdio")
