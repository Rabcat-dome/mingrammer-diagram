"""Direct JSON-to-diagram command, sharing the same controlled renderer as MCP."""
import json
import sys
from local_server import FixtureRequest, render_fixture
from render_fixture import MAX_INPUT

try:
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError("S04_INPUT_LIMIT")
    result = render_fixture(FixtureRequest.model_validate(json.loads(raw)))
    if result.is_error:
        raise ValueError(result.content[0].text)
    print(json.dumps(result.structured_content))
except (ValueError, json.JSONDecodeError) as error:
    print(str(error), file=sys.stderr)
    sys.exit(2)
