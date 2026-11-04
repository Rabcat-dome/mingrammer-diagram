"""M6-02 and T-015: what each distribution holds, and whether the P0 report still matches the baseline.

The other lanes check how each package behaves. This one reads what would actually leave the machine:
the wheel, the sdist and both plugins. It writes `reports/release-audit.json`, and then runs its tests.
"""

import ast
import json
import os
import re
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

CLAUDE_PLUGIN = ROOT / "plugins/cloud-architecture-diagrams"
FORBIDDEN = re.compile(
    r"(^|/)(__pycache__|\.claude|\.git|\.venv|\.env|reports|spikes|baselines|assets-source)(/|$)"
    r"|\.pyc$|\.DS_Store$|settings\.local\.json$"
)
# A source archive may hold tests and scripts, and not these parts of the repository.
SDIST_FORBIDDEN = re.compile(r"^(\.agents|\.claude-plugin|\.git|doc|plugins)(/|$)")
PACKAGE_REQUIRED = (
    "assets/NOTICE.md",
    "assets/THIRD-PARTY-PYTHON.md",
    "assets/fonts/NotoSans-OFL.txt",
    "assets/fonts/NotoSansThai-OFL.txt",
    "catalog_data/assets.json",
)
PRIVATE_USE = "private personal use"
REQUIREMENTS = ROOT / "doc/requirements/requirements.md"
TRACE = ROOT / "doc/project-management/evidence/S10-p0-traceability.json"
STATES = {
    "met",
    "met_with_owner",
    "partly",
    "blocked_on_work",
    "blocked_on_second_machine",
    "not_met",
}


def forbidden_names(names: list[str]) -> list[str]:
    return sorted(name for name in names if FORBIDDEN.search(name))


def missing_names(names: list[str], required: tuple[str, ...]) -> list[str]:
    return [item for item in required if not any(name.endswith(item) for name in names)]


def wheel_names(dist: Path) -> list[str]:
    wheels = sorted(dist.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"{dist}: expected one wheel, found {len(wheels)}")
    with zipfile.ZipFile(wheels[0]) as wheel:
        return wheel.namelist()


def sdist_names(dist: Path) -> list[str]:
    archives = sorted(dist.glob("*.tar.gz"))
    if len(archives) != 1:
        raise SystemExit(f"{dist}: expected one sdist, found {len(archives)}")
    with tarfile.open(archives[0]) as archive:
        # The top folder is only the package's name, and a path check must not read it.
        return [name.split("/", 1)[1] for name in archive.getnames() if "/" in name]


def claude_plugin_names(root: Path = CLAUDE_PLUGIN) -> list[str]:
    """The tree as an install copies it: links resolved, and compiled files left behind."""
    names = []
    for folder, children, files in os.walk(root, followlinks=True):
        children[:] = [item for item in children if item != "__pycache__"]
        names += [str((Path(folder) / item).relative_to(root)) for item in files]
    return names


def work_plugin_names() -> list[str]:
    from build_work_plugin import collect

    return list(collect())


def audit(dist: Path) -> dict[str, Any]:
    packages = {
        "wheel": (wheel_names(dist), PACKAGE_REQUIRED),
        "sdist": (sdist_names(dist), ()),
        "claude-plugin": (claude_plugin_names(), PACKAGE_REQUIRED),
        "work-plugin": (work_plugin_names(), PACKAGE_REQUIRED),
    }
    errors: list[str] = []
    counts = {}
    for label, (names, required) in packages.items():
        counts[label] = len(names)
        errors += [f"{label}: must not ship {name}" for name in forbidden_names(names)]
        if label == "sdist":
            errors += [
                f"sdist: must not ship {name}" for name in names if SDIST_FORBIDDEN.search(name)
            ]
        errors += [f"{label}: lacks {name}" for name in missing_names(names, required)]
    for path in (
        CLAUDE_PLUGIN / "README.md",
        CLAUDE_PLUGIN / "skills/architecture-model/SKILL.md",
        ROOT / "plugins/cloud-architecture-work/README.md",
        ROOT / "src/cloud_architecture_diagrams/assets/NOTICE.md",
    ):
        if PRIVATE_USE not in path.read_text().lower():
            errors.append(f"{path.relative_to(ROOT)}: must state the private-use limit")
    return {"passed": not errors, "errors": errors, "files": counts}


def requirement_ids(text: str) -> tuple[list[str], list[str]]:
    """The P0 requirements and every acceptance scenario the baseline defines."""
    p0 = re.findall(r"^\| ((?:FR|NFR)-\d+) \| P0\b", text, re.M)
    scenarios = re.findall(r"^\| (T-\d+)\b", text, re.M)
    return p0, scenarios


def test_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
    }


def trace_errors(records: list[dict[str, Any]], root: Path = ROOT) -> list[str]:
    """The report may not drift from the baseline, name a test that is gone, or claim with no check."""
    from repository_checks import anchors

    expected = sum(requirement_ids((root / REQUIREMENTS.relative_to(ROOT)).read_text()), [])
    decisions = set(
        re.findall(
            r"^\| (D-\d+) \|",
            (root / "doc/project-management/decisions.md").read_text(),
            re.M,
        )
    )
    found = [record["id"] for record in records]
    errors = [f"{item}: not in the report" for item in expected if item not in found]
    errors += [
        f"{item}: not a P0 requirement or scenario" for item in found if item not in expected
    ]
    errors += [f"{item}: listed twice" for item in sorted(set(found)) if found.count(item) > 1]
    for record in records:
        name = record["id"]
        if record["state"] not in STATES:
            errors.append(f"{name}: unknown state {record['state']}")
        if record["state"].startswith("met") and not record["checks"]:
            errors.append(f"{name}: met with no check")
        if record["state"].startswith("met") and record["open"]:
            errors.append(f"{name}: met, yet something is open")
        if not record["state"].startswith("met") and not record["open"]:
            errors.append(f"{name}: not met, and nothing says what is open")
        named = set(re.findall(r"\bD-\d+\b", record["owner"]))
        if record["state"] == "met_with_owner" and not named:
            errors.append(f"{name}: an owner's acceptance must name its decision")
        errors += [f"{name}: no decision {item}" for item in sorted(named - decisions)]
        for check in record["checks"]:
            path = root / check["file"]
            if not path.is_file() or check["test"] not in test_names(path):
                errors.append(f"{name}: no test {check['test']} in {check['file']}")
        for evidence in record["evidence"]:
            target, _, anchor = evidence.partition("#")
            path = root / target
            if not path.is_file():
                errors.append(f"{name}: no evidence file {target}")
            elif anchor and anchor not in anchors(path.read_text()):
                errors.append(f"{name}: no anchor {evidence}")
    return errors


def main() -> int:
    report = audit(ROOT / "reports/dist")
    reports = ROOT / "reports"
    (reports / "release-audit.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    for error in report["errors"]:
        print(error)
    print(json.dumps(report["files"]))
    errors = trace_errors(json.loads(TRACE.read_text()))
    for error in errors:
        print(error)
    if report["errors"] or errors:
        return 1
    import pytest

    return int(
        pytest.main(
            ["tests/test_release_audit.py", "--junitxml=reports/release-audit-tests.xml", "-q"]
        )
    )


if __name__ == "__main__":
    sys.exit(main())
