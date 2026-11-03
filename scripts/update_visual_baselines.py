"""Accept the current reference renders as the reviewed baseline. Look at them first.

A failing `visual-regression` lane leaves before, after and diff images in
reports/visual-regression. Run this only after reviewing those, and give the reason, which stays in
the record. The evidence for each acceptance belongs in doc/project-management/evidence.
"""

import argparse
import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
sys.path.insert(0, str(ROOT / "tests"))

from visual_helpers import (  # noqa: E402
    BASELINES,
    RECORD,
    digest,
    engine_version,
    graph_text,
    reference_views,
    render_view,
    view_key,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reason", required=True, help="Why the output changed")
    arguments = parser.parse_args()
    views = {}
    outputs: dict[str, bytes] = {}
    # The renderer refuses a root with a symbolic link in its path, as $TMPDIR has on macOS, and
    # reports/ is where private-use bundles already live, so a killed run leaves nothing elsewhere.
    REPORTS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=REPORTS) as scratch:
        for scenario, view in reference_views():
            rendered = render_view(scenario, view, Path(scratch))
            key = view_key(scenario, view)
            outputs[f"{key}.graph.json"] = graph_text(rendered["graph"]).encode()
            outputs[f"{key}.png"] = rendered["png"]
            views[key] = {"svg": digest(rendered["svg"]), "png": digest(rendered["png"])}
    # Nothing is removed until every view has rendered, so a failed run keeps the old baselines.
    shutil.rmtree(BASELINES, ignore_errors=True)
    BASELINES.mkdir(parents=True)
    for name, data in outputs.items():
        (BASELINES / name).write_bytes(data)
    RECORD.write_text(
        json.dumps(
            {
                "reason": arguments.reason,
                "accepted_on": date.today().isoformat(),
                "engine": engine_version(),
                "views": views,
            },
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    print(f"Accepted {len(views)} views into {BASELINES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
