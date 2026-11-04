"""M6-02 release-audit lane: T-015's package contents and the P0 report's guard."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_audit  # noqa: E402

RECORD: dict[str, Any] = {
    "id": "FR-001",
    "state": "met",
    "summary": "x",
    "checks": [
        {
            "lane": "release-audit",
            "file": "tests/test_release_audit.py",
            "test": "test_a_forbidden_path_is_found",
        }
    ],
    "evidence": ["doc/project-management/evidence/S08-reference-diagrams.md#validation"],
    "open": "",
    "owner": "",
}


def full_report() -> list[dict[str, Any]]:
    text = release_audit.REQUIREMENTS.read_text()
    ids = sum(release_audit.requirement_ids(text), [])
    return [RECORD | {"id": item} for item in ids]


@pytest.mark.parametrize(
    "name",
    [
        ".claude/settings.local.json",
        ".claude/worktrees/agent-1/pyproject.toml",
        "src/x/__pycache__/a.cpython-313.pyc",
        "tests/baselines/huawei-web--overview.png",
        "reports/render-smoke/a.png",
        "spikes/s04-local-plugin/x.py",
        "a/.DS_Store",
    ],
)
def test_a_forbidden_path_is_found(name: str) -> None:
    assert release_audit.forbidden_names(["src/keep.py", name]) == [name]


def test_an_ordinary_path_is_not_forbidden() -> None:
    names = ["cloud_architecture_diagrams/assets/NOTICE.md", "src/reporting.py", "tests/gitfoo.py"]
    assert release_audit.forbidden_names(names) == []


def test_a_missing_notice_is_found() -> None:
    assert release_audit.missing_names(["a/assets/NOTICE.md"], ("assets/NOTICE.md",)) == []
    assert release_audit.missing_names(["a/b.md"], ("assets/NOTICE.md",)) == ["assets/NOTICE.md"]


@pytest.mark.parametrize("required", release_audit.PACKAGE_REQUIRED)
def test_a_package_without_a_required_notice_is_found(required: str) -> None:
    names = [
        name
        for name in release_audit.wheel_names(ROOT / "reports/dist")
        if not name.endswith(required)
    ]
    assert release_audit.missing_names(names, release_audit.PACKAGE_REQUIRED) == [required]


def test_the_notices_stay_required() -> None:
    # A shorter list would pass every check above, so the list itself is pinned.
    assert set(release_audit.PACKAGE_REQUIRED) == {
        "assets/NOTICE.md",
        "assets/THIRD-PARTY-PYTHON.md",
        "assets/fonts/NotoSans-OFL.txt",
        "assets/fonts/NotoSansThai-OFL.txt",
        "catalog_data/assets.json",
    }


def test_the_built_packages_hold_only_what_they_should() -> None:
    report = release_audit.audit(ROOT / "reports/dist")
    assert report["errors"] == [] and report["passed"]
    assert all(count > 0 for count in report["files"].values())


def test_the_wheel_installs_alone_and_renders_from_outside_the_repository(tmp_path: Path) -> None:
    # A clean install is T-015: the built wheel and the hash-locked packages, and nothing else.
    wheels = sorted((ROOT / "reports/dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    requirements = tmp_path / "requirements.txt"
    export = ["uv", "export", "--frozen", "--no-dev", "--no-emit-project"]
    exported = subprocess.run(
        [*export, "--format", "requirements-txt"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    requirements.write_text(exported.stdout)
    environment = tmp_path / "environment"
    python = environment / "bin/python"
    for command in (
        ["uv", "venv", "--quiet", "--python", sys.executable, str(environment)],
        [
            "uv",
            "pip",
            "install",
            "--quiet",
            "--python",
            str(python),
            "--require-hashes",
            "-r",
            str(requirements),
        ],
        ["uv", "pip", "install", "--quiet", "--python", str(python), "--no-deps", str(wheels[0])],
    ):
        subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=240, check=True)
    cli = environment / "bin/cloud-diagrams"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    model = (ROOT / "tests/fixtures/references/huawei-web.json").read_bytes()
    result = subprocess.run(
        [str(cli), "render", "--output", "out", "--view", "services"],
        cwd=elsewhere,
        input=model,
        capture_output=True,
        timeout=120,
        check=True,
    )
    report = json.loads(result.stdout)
    assert report["rendered"] and Path(report["bundle_path"]).is_relative_to(elsewhere.resolve())
    names = {item["name"] for item in report["artifacts"]}
    assert {"diagram.png", "diagram.svg", "manifest.json"} <= names
    # The private-use limit travels with the wheel's own files, not this checkout's.
    manifest = json.loads((Path(report["bundle_path"]) / "manifest.json").read_text())
    assert "private" in json.dumps(manifest["rights"]).lower()


def test_the_sdist_reader_drops_only_the_package_folder(tmp_path: Path) -> None:
    import tarfile

    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude/settings.local.json").write_text("{}")
    with tarfile.open(tmp_path / "x-1.tar.gz", "w:gz") as archive:
        archive.add(tmp_path / ".claude/settings.local.json", "x-1/.claude/settings.local.json")
    names = release_audit.sdist_names(tmp_path)
    assert names == [".claude/settings.local.json"]
    assert release_audit.forbidden_names(names) == names


def test_the_committed_report_covers_the_baseline() -> None:
    records = json.loads(release_audit.TRACE.read_text())
    assert release_audit.trace_errors(records) == []
    assert len(records) == sum(
        len(group)
        for group in release_audit.requirement_ids(release_audit.REQUIREMENTS.read_text())
    )


def test_the_page_is_what_the_json_says() -> None:
    import build_traceability

    records = json.loads(build_traceability.TRACE.read_text())
    assert build_traceability.PAGE.read_text() == build_traceability.render(records)


def test_a_clean_report_passes_the_guard() -> None:
    assert release_audit.trace_errors(full_report()) == []


def test_a_requirement_left_out_is_found() -> None:
    records = full_report()
    missing = records.pop(0)["id"]
    assert release_audit.trace_errors(records) == [f"{missing}: not in the report"]


def test_an_unknown_id_is_found() -> None:
    records = full_report() + [RECORD | {"id": "FR-999"}]
    assert release_audit.trace_errors(records) == ["FR-999: not a P0 requirement or scenario"]


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"state": "done"}, "unknown state done"),
        ({"checks": []}, "met with no check"),
        ({"open": "something"}, "met, yet something is open"),
        ({"state": "partly"}, "not met, and nothing says what is open"),
        ({"state": "met_with_owner", "owner": "the owner said so"}, "must name its decision"),
        (
            {"checks": [{"lane": "x", "file": "tests/test_release_audit.py", "test": "test_gone"}]},
            "no test test_gone",
        ),
        ({"evidence": ["doc/nothing.md"]}, "no evidence file doc/nothing.md"),
        (
            {"evidence": ["doc/project-management/evidence/S08-reference-diagrams.md#gone"]},
            "no anchor",
        ),
    ],
)
def test_a_false_or_empty_claim_is_found(change: dict[str, Any], message: str) -> None:
    records = copy.deepcopy(full_report())
    records[0] |= change
    errors = release_audit.trace_errors(records)
    assert any(message in error and records[0]["id"] in error for error in errors), errors
