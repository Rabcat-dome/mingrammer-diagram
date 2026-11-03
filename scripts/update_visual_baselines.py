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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

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
    shutil.rmtree(BASELINES, ignore_errors=True)
    BASELINES.mkdir(parents=True)
    views = {}
    # The renderer refuses a root with a symbolic link in its path, as $TMPDIR has on macOS.
    with tempfile.TemporaryDirectory(dir=BASELINES.parent) as scratch:
        for scenario, view in reference_views():
            rendered = render_view(scenario, view, Path(scratch))
            key = view_key(scenario, view)
            (BASELINES / f"{key}.graph.json").write_text(graph_text(rendered["graph"]))
            (BASELINES / f"{key}.png").write_bytes(rendered["png"])
            views[key] = {"svg": digest(rendered["svg"]), "png": digest(rendered["png"])}
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
