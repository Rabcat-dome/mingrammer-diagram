"""What the host starts. It needs only the standard library, so it answers before setup has run."""

from __future__ import annotations

import os
import sys

# -I keeps the script's own folder out of the import path, along with anything in the environment.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from work_adapter.protocol import serve  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(serve())
