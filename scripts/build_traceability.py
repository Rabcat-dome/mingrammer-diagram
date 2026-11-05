"""M6-02: write the human page of the P0 report from its JSON, so that the two cannot differ."""

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "doc/project-management/evidence/S10-p0-traceability.json"
PAGE = ROOT / "doc/project-management/evidence/S10-p0-traceability.md"
LABELS = {
    "met": "Met",
    "met_with_owner": "Met, with the owner's acceptance",
    "partly": "Partly",
    "blocked_on_work": "Blocked on Work",
    "blocked_on_second_machine": "Blocked on a second machine",
    "not_met": "Not met",
}
INTRO = """# S10 — P0 Traceability

M6-02's requirement-to-check report. It covers every P0 requirement and every acceptance scenario in the [requirements](../../requirements/requirements.md). `scripts/build_traceability.py` writes this page from [its JSON](S10-p0-traceability.json), and the `release-audit` lane fails if an ID is missing or extra, a named test no longer exists, an evidence link is broken, or a claim has no check behind it. That guard proves a check exists. Whether it checks enough was judged by reading it, and the [S10 evidence](S10-release-checks.md#the-p0-audit) says how.

No release SHA exists: M6-03 and M6-04 have not run, and this report describes the head it was last checked at, not a release.
"""


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render(records: list[dict[str, Any]]) -> str:
    counts = Counter(record["state"] for record in records)
    lines = [INTRO, "## Summary\n", "| State | P0 requirements and scenarios |", "|---|---|"]
    lines += [f"| {LABELS[state]} | {counts[state]} |" for state in LABELS]
    lines += [f"| Total | {len(records)} |", "", "## Report\n"]
    lines += ["| ID | Requires | State | Checks | Evidence | Open |", "|---|---|---|---|---|---|"]
    for record in records:
        checks = "<br>".join(f"`{item['lane']}`: `{item['test']}`" for item in record["checks"])
        evidence = "<br>".join(
            f"[{Path(item).name.split('#')[0]}]({Path(item).name})"
            if "/evidence/" in item
            else f"[{Path(item).name.split('#')[0]}](../../../{item})"
            for item in record["evidence"]
        )
        state = LABELS[record["state"]]
        if record["owner"]:
            state += f" ({record['owner']})"
        lines.append(
            f"| {record['id']} | {cell(record['summary'])} | {state} | {checks} | {evidence} "
            f"| {cell(record['open'] or record.get('note', ''))} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    PAGE.write_text(render(json.loads(TRACE.read_text())))
    print(f"wrote {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
