"""Loopback S04 MCP/HTTP proof. Development bearer auth is not Work OAuth."""

import base64
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import subprocess
import threading
import time

from mcp.server import MCPServer
from mcp_types import CallToolResult, ImageContent, TextContent, ToolAnnotations
from starlette.responses import FileResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn

from render_fixture import MAX_INPUT, runtime_info, validate

TOKEN = os.environ.get("S04_TOKEN", "")
if len(TOKEN) < 32:
    raise RuntimeError("S04_TOKEN must be set for the loopback development proof")
ORIGIN = os.environ["S04_ARTIFACT_ORIGIN"].rstrip("/")
ROOT = Path("/tmp/s04-artifacts")
ROOT.mkdir(exist_ok=True)
GATE = threading.Lock()
ARTIFACTS = {"diagram.svg", "diagram.png", "source.dot", "source.json", "manifest.json"}
TTL = 600
mcp = MCPServer("S04 runtime proof", version="0.0.1",
                instructions="Synthetic runtime fixture only. It does not implement cloud semantics or a release plugin.")


def expire():
    for directory in ROOT.iterdir():
        if directory.is_dir() and time.time() - directory.stat().st_mtime > TTL:
            shutil.rmtree(directory)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
def runtime_info_tool() -> dict:
    """Inspect S04 Python/Graphviz/font versions and container limits."""
    return runtime_info()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False))
def render_fixture(labels: list[str]) -> CallToolResult:
    """Render exactly three synthetic nodes with supplied literal labels; not a cloud architecture renderer."""
    request = {"node_count": 3, "labels": labels}
    validate(request)
    if not GATE.acquire(blocking=False):
        raise ValueError("S04_BUSY")
    request_id = secrets.token_hex(16)
    destination = ROOT / request_id
    try:
        expire()
        process = subprocess.Popen(
            ["python", "/app/render_fixture.py", "render", str(destination)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True,
            env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp",
                 "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"},
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
        report["request_id"] = request_id
        report["artifact_urls"] = {name: f"{ORIGIN}/artifacts/{request_id}/{name}" for name in sorted(ARTIFACTS)}
        report["artifact_access"] = "Same development bearer token required; Work download untested"
        report["expires_after_seconds"] = TTL
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(report)),
                     ImageContent(type="image", data=base64.b64encode((destination / "diagram.png").read_bytes()).decode(),
                                  mime_type="image/png")],
            structured_content=report,
        )
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    finally:
        GATE.release()


class DevelopmentBoundary:
    """Protect every local route. This is deliberately not an OAuth server."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        expected = ("Bearer " + TOKEN).encode()
        if not hmac.compare_digest(headers.get(b"authorization", b""), expected):
            await send({"type": "http.response.start", "status": 401,
                        "headers": [(b"www-authenticate", b"Bearer"), (b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"Unauthorized"})
            return
        if scope["path"].startswith("/artifacts/"):
            expire()
            match = re.fullmatch(r"/artifacts/([a-f0-9]{32})/([a-z.]+)", scope["path"])
            if scope["method"] == "GET" and match and match[2] in ARTIFACTS:
                path = ROOT / match[1] / match[2]
                if path.is_file():
                    return await FileResponse(path, filename=match[2])(scope, receive, send)
            await send({"type": "http.response.start", "status": 404, "headers": []})
            await send({"type": "http.response.body", "body": b"Not found"})
            return
        return await self.app(scope, receive, send)


if __name__ == "__main__":
    app = mcp.streamable_http_app(stateless_http=True, json_response=True,
                                 max_request_body_size=MAX_INPUT, host="0.0.0.0")
    uvicorn.run(DevelopmentBoundary(app), host="0.0.0.0", port=8000, access_log=False, log_level="warning")
