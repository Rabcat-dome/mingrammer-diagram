"""Execute only the controlled fixture renderer in a caller-created scratch directory."""
import json
import os
from pathlib import Path
import resource
import sys
from render_fixture import MAX_FILE, MAX_INPUT, render, validate

resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))
raw = sys.stdin.buffer.read(MAX_INPUT + 1)
if len(raw) > MAX_INPUT:
    raise ValueError("S04_INPUT_LIMIT")
request = json.loads(raw)
validate(request)
root = Path(os.environ["CLOUD_DIAGRAM_SCRATCH_ROOT"]).resolve(strict=True)
destination = Path(sys.argv[1])
if destination.name != "result" or destination.parent.resolve(strict=True) != root:
    raise ValueError("S04_OUTPUT_ROOT")
print(json.dumps(render(request, destination)))
