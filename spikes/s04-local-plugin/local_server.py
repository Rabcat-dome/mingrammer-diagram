"""Native stdio MCP and direct-script backend; no HTTP listener or cloud service."""
import base64
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import threading
from typing import Literal
from mcp.server import MCPServer
from mcp_types import BlobResourceContents, CallToolResult, EmbeddedResource, ImageContent, TextContent, ToolAnnotations
from pydantic import BaseModel, ConfigDict
from artifact_store import ArtifactStore, FILES
from execution import POLICY, execute
from render_fixture import runtime_info, validate

STORE = ArtifactStore(os.environ['CLOUD_DIAGRAM_HOST_OUTPUT_ROOT'])
RUNTIME = Path(os.environ['CLOUD_DIAGRAM_RUNTIME_DIR'])
VERSION = os.environ['CLOUD_DIAGRAM_PLUGIN_VERSION']
INFO = {**runtime_info(), 'plugin_version': VERSION, 'execution': 'native Python local stdio/direct script; no Docker', 'limits': POLICY}
GATE = threading.Lock()
mcp = MCPServer('Cloud Architecture Diagrams S04', version=VERSION,
                instructions='S04 native pilot: synthetic three-node fixtures only. Call get_runtime_info first. No provider catalog is implemented.')


class FixtureRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    labels: list[str]


def failure(code):
    return CallToolResult(is_error=True, content=[TextContent(type='text', text=code)])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
def get_runtime_info() -> CallToolResult:
    """Verify this machine's native Python/Graphviz/fonts and renderer limits; no Docker required."""
    return CallToolResult(structured_content=INFO, content=[TextContent(type='text', text=json.dumps(INFO))])


@mcp.tool(annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False))
def render_fixture(request: FixtureRequest) -> CallToolResult:
    """Render exactly three literal labels using native local scripts and return a complete artifact bundle."""
    payload = {'node_count': 3, **request.model_dump()}
    try:
        validate(payload)
        STORE.check_root()
    except ValueError as error:
        return failure(str(error) if str(error).startswith('S04_') else 'S04_INVALID_REQUEST')
    except OSError:
        return failure('S04_OUTPUT_ROOT_UNAVAILABLE')
    if not GATE.acquire(blocking=False):
        return failure('S04_BUSY')
    try:
        with tempfile.TemporaryDirectory(prefix='request-', dir=RUNTIME / 'tmp') as scratch:
            destination = Path(scratch) / 'result'
            environment = os.environ.copy()
            environment['CLOUD_DIAGRAM_SCRATCH_ROOT'] = scratch
            command = ['/usr/bin/sandbox-exec', '-f', str(Path(__file__).with_name('network.sb')),
                       sys.executable, str(Path(__file__).with_name('native_worker.py')), str(destination)]
            output = execute(command, json.dumps(payload).encode(), environment, scratch)
            report = json.loads(output)
            report['files'] = {name: value for name, value in report['files'].items() if name in FILES}
            identifier = secrets.token_hex(16)
            report.update({'runtime': INFO, 'bundle_id': identifier,
                           'host_paths': {name: str(STORE.root / identifier / name) for name in sorted(FILES)}})
            STORE.publish(identifier, destination, report)
        png = STORE.read(identifier, 'diagram.png')
        return CallToolResult(structured_content=report, content=[TextContent(type='text', text=json.dumps(report)),
            ImageContent(type='image', data=base64.b64encode(png).decode(), mime_type='image/png')])
    except ValueError as error:
        code = str(error)
        return failure(code if code.startswith('S04_') and code.isidentifier() else 'S04_RENDER_FAILURE')
    except (OSError, KeyError):
        return failure('S04_RENDER_OR_ARTIFACT_FAILURE')
    finally:
        GATE.release()


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
def read_fixture_artifact(bundle_id: str, filename: Literal['diagram.png', 'diagram.svg', 'source.dot', 'source.json', 'manifest.json']) -> CallToolResult:
    """Read only a regular, non-symlink file anchored inside this plugin's private artifact root."""
    try:
        data = STORE.read(bundle_id, filename)
    except (OSError, ValueError):
        return failure('S04_ARTIFACT_UNAVAILABLE')
    mime = {'png': 'image/png', 'svg': 'image/svg+xml', 'json': 'application/json', 'dot': 'text/plain'}[filename.rsplit('.', 1)[1]]
    return CallToolResult(content=[EmbeddedResource(type='resource', resource=BlobResourceContents(
        uri='artifact://' + bundle_id + '/' + filename, mime_type=mime, blob=base64.b64encode(data).decode()))])


if __name__ == '__main__':
    mcp.run(transport='stdio')
