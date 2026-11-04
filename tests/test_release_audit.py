"""M6-02 release-audit lane: T-015's package contents and the P0 report's guard."""

import copy
import json
import re
import subprocess
import sys
import tarfile
import zipfile
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
    assert release_audit.missing_names(["assets/NOTICE.md"], ("assets/NOTICE.md",)) == []
    assert release_audit.missing_names(["a/b.md"], ("assets/NOTICE.md",)) == ["assets/NOTICE.md"]


@pytest.mark.parametrize("required", release_audit.WHEEL_REQUIRED)
def test_a_package_without_a_required_notice_is_found(required: str) -> None:
    names = [name for name in release_audit.wheel_names(ROOT / "reports/dist") if name != required]
    assert release_audit.missing_names(names, release_audit.WHEEL_REQUIRED) == [required]


def test_the_reproduction_proof_passes_and_still_describes_this_source() -> None:
    # A proof is committed after the commit it reproduced, so it is bound to the source instead.
    from reproduce_core import source_digest

    proof = json.loads(
        (ROOT / "doc/project-management/evidence/S10-core-reproduction-proof.json").read_text()
    )
    assert proof["locked_route_all_match"] and proof["wheel_route_all_match"]
    assert proof["routes_agree"] and proof["mismatches"] == [] and proof["views"] >= 26
    assert proof["wheel_matches_expected"] is True
    assert proof["source_digest"] == source_digest(ROOT)


@pytest.mark.parametrize("name", [".agents/plugins/x.json", "doc/x.md", ".git", "plugins/a/b.md"])
def test_the_source_archive_keeps_out_the_rest_of_the_repository(name: str) -> None:
    assert release_audit.SDIST_FORBIDDEN.search(name)


def test_the_source_archive_keeps_what_a_build_needs() -> None:
    names = ["pyproject.toml", "src/a.py", "tests/test_a.py", "scripts/b.py", "docs.txt"]
    assert not [name for name in names if release_audit.SDIST_FORBIDDEN.search(name)]


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
        ({"state": "met_with_owner", "owner": "D-999 says so"}, "no decision D-999"),
        ({"state": "met_with_owner", "owner": "D-023", "checks": []}, "met with no check"),
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


def test_ci_uploads_only_text_reports() -> None:
    # The wheel and the rendered bundles hold Huawei icons for private personal use (D-018).
    workflow = (ROOT / ".github/workflows/quality-gate.yml").read_text()
    assert workflow.count("actions/upload-artifact@") == 1
    found = re.search(r"path: \|\n((?: {12}\S+\n)+)", workflow)
    assert found, "the upload must name its paths one by one"
    assert found.group(1).split() == ["reports/*.log", "reports/*.xml", "reports/*.json"]


def test_what_a_source_archive_must_hold_stays_required() -> None:
    assert set(release_audit.SDIST_REQUIRED) == {
        "README.md",
        "pyproject.toml",
        "uv.lock",
        "src/cloud_architecture_diagrams/cli.py",
        "src/cloud_architecture_diagrams/assets/NOTICE.md",
        "src/cloud_architecture_diagrams/assets/THIRD-PARTY-PYTHON.md",
        "src/cloud_architecture_diagrams/catalog_data/assets.json",
    }
    assert set(release_audit.WHEEL_REQUIRED) == {
        "cloud_architecture_diagrams/cli.py",
        *(f"cloud_architecture_diagrams/{item}" for item in release_audit.PACKAGE_REQUIRED),
    }
    assert set(release_audit.PLUGIN_REQUIRED) == {
        f"src/cloud_architecture_diagrams/{item}" for item in release_audit.PACKAGE_REQUIRED
    }


def archives(folder: Path, sdist: dict[str, bytes], wheel: dict[str, bytes]) -> Path:
    with tarfile.open(folder / "x-1.tar.gz", "w:gz") as archive:
        for name, data in sdist.items():
            path = folder / "entry"
            path.write_bytes(data)
            archive.add(path, f"x-1/{name}")
            path.unlink()
    with zipfile.ZipFile(folder / "x-1-py3-none-any.whl", "w") as archive:
        for name, data in wheel.items():
            archive.writestr(name, data)
    return folder


def full_wheel(data: bytes = b"x") -> dict[str, bytes]:
    return dict.fromkeys(release_audit.WHEEL_REQUIRED, data)


def full_sdist(data: bytes = b"x") -> dict[str, bytes]:
    names = [*release_audit.SDIST_REQUIRED, *(f"src/{n}" for n in release_audit.WHEEL_REQUIRED)]
    return dict.fromkeys(names, data)


def audit_errors(folder: Path) -> list[str]:
    errors: list[str] = release_audit.audit(folder)["errors"]
    return errors


def test_an_empty_source_archive_fails_the_audit(tmp_path: Path) -> None:
    errors = audit_errors(archives(tmp_path, {}, full_wheel()))
    assert {f"sdist: lacks {name}" for name in release_audit.SDIST_REQUIRED} <= set(errors)
    assert all(error.startswith("sdist: lacks ") for error in errors)


def test_a_source_archive_with_one_harmless_file_fails_the_audit(tmp_path: Path) -> None:
    errors = audit_errors(archives(tmp_path, {"README.md": b"x"}, full_wheel()))
    assert "sdist: lacks pyproject.toml" in errors


def test_a_wheel_of_empty_files_fails_the_audit(tmp_path: Path) -> None:
    errors = audit_errors(archives(tmp_path, full_sdist(), full_wheel(b"")))
    assert {f"wheel: {name} is empty" for name in release_audit.WHEEL_REQUIRED} <= set(errors)


def test_a_source_archive_of_empty_files_fails_the_audit(tmp_path: Path) -> None:
    errors = audit_errors(archives(tmp_path, full_sdist(b""), full_wheel()))
    assert {f"sdist: {name} is empty" for name in release_audit.SDIST_REQUIRED} <= set(errors)


@pytest.mark.parametrize("name", ["xREADME.md", "tests/README.md", "extra/README.md"])
def test_a_file_somewhere_else_does_not_count(name: str) -> None:
    assert release_audit.missing_names([name], ("README.md",)) == ["README.md"]


def test_an_empty_file_is_not_hidden_by_a_full_one_of_the_same_name_elsewhere() -> None:
    sizes = {"README.md": 0, "tests/README.md": 5}
    assert release_audit.empty_required(sizes, ("README.md",)) == ["README.md"]


def test_a_source_archive_with_only_a_misplaced_file_fails_the_audit(tmp_path: Path) -> None:
    sdist = full_sdist()
    del sdist["README.md"]
    sdist["tests/README.md"] = b"x"
    assert audit_errors(archives(tmp_path, sdist, full_wheel())) == ["sdist: lacks README.md"]


def test_a_wheel_with_its_package_in_another_folder_fails_the_audit(tmp_path: Path) -> None:
    wheel = {f"extra/{name}": b"x" for name in release_audit.WHEEL_REQUIRED}
    errors = audit_errors(archives(tmp_path, full_sdist(), wheel))
    assert {f"wheel: lacks {name}" for name in release_audit.WHEEL_REQUIRED} <= set(errors)


def test_the_audit_passes_when_each_archive_is_whole(tmp_path: Path) -> None:
    assert audit_errors(archives(tmp_path, full_sdist(), full_wheel())) == []


GOOD_PROOF = {"views": 26, "routes_agree": True, "mismatches": [], "wheel_matches_expected": True}


@pytest.mark.parametrize(
    ("change", "passes"),
    [
        ({}, True),
        ({"wheel_matches_expected": None}, True),
        ({"views": 0}, False),
        ({"routes_agree": False}, False),
        ({"mismatches": ["a--b"]}, False),
        ({"wheel_matches_expected": False}, False),
    ],
)
def test_a_reproduction_proof_fails_unless_it_proved_something(
    change: dict[str, Any], passes: bool
) -> None:
    from reproduce_core import proof_passed

    assert proof_passed(GOOD_PROOF | change) is passes


@pytest.mark.parametrize("module", ["models.py", "render/graph.py"])
def test_a_source_archive_without_a_module_the_wheel_has_fails_the_audit(
    tmp_path: Path, module: str
) -> None:
    name = f"cloud_architecture_diagrams/{module}"
    sdist, wheel = full_sdist(), full_wheel() | {name: b"x"}
    sdist[f"src/{name}"] = b"x"
    assert audit_errors(archives(tmp_path, sdist, wheel)) == []
    del sdist[f"src/{name}"]
    (tmp_path / "x-1.tar.gz").unlink()
    (tmp_path / "x-1-py3-none-any.whl").unlink()
    assert audit_errors(archives(tmp_path, sdist, wheel)) == [f"sdist: lacks src/{name}"]


def test_a_wheel_without_a_module_the_source_archive_has_fails_the_audit(tmp_path: Path) -> None:
    name = "cloud_architecture_diagrams/models.py"
    sdist = full_sdist() | {f"src/{name}": b"x"}
    assert audit_errors(archives(tmp_path, sdist, full_wheel())) == [f"wheel: lacks {name}"]


def test_a_source_file_that_differs_from_the_wheel_fails_the_audit(tmp_path: Path) -> None:
    name = "cloud_architecture_diagrams/cli.py"
    sdist = full_sdist() | {f"src/{name}": b"x"}
    wheel = full_wheel() | {name: b"two"}
    assert audit_errors(archives(tmp_path, sdist, wheel)) == [
        f"sdist: src/{name} differs from the wheel"
    ]


def test_a_source_archive_with_a_second_top_folder_fails_the_audit(tmp_path: Path) -> None:
    folder = archives(tmp_path, full_sdist(), full_wheel())
    source = folder / "x-1.tar.gz"
    moved = tmp_path / "moved.tar.gz"
    with tarfile.open(source) as old, tarfile.open(moved, "w:gz") as new:
        for item in old.getmembers():
            if item.name == "x-1/pyproject.toml":
                item.name = "other/pyproject.toml"
            new.addfile(item, old.extractfile(item))
    moved.replace(source)
    assert audit_errors(folder) == ["sdist: has 2 top-level entries where one folder is expected"]


def test_the_real_packages_have_one_top_folder_and_the_same_files() -> None:
    dist = ROOT / "reports/dist"
    assert len(release_audit.sdist_roots(dist)) == 1
    assert (
        release_audit.package_differences(
            release_audit.wheel_sizes(dist), release_audit.sdist_sizes(dist)
        )
        == []
    )
