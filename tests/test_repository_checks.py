"""Gate helpers must agree with what the build ships and what Git records."""

import hashlib
import importlib.util
import subprocess
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def checks() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "repository_checks", ROOT / "scripts/repository_checks.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(".DS_Store\n")
    package = tmp_path / "src/demo"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / ".DS_Store").write_text("ignored by the build")
    module = checks()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    return module


def build_wheel(root: Path, *names: str) -> None:
    dist = root / "reports/dist"
    dist.mkdir(parents=True)
    with zipfile.ZipFile(dist / "demo-1-py3-none-any.whl", "w") as wheel:
        wheel.writestr("demo-1.dist-info/RECORD", "")
        for name in names:
            wheel.writestr(name, "")


def test_wheel_check_ignores_files_the_build_excludes(repository: ModuleType) -> None:
    build_wheel(repository.ROOT, "demo/__init__.py")
    assert repository.package() == []


def test_wheel_check_compares_contents_not_only_names(repository: ModuleType) -> None:
    (repository.ROOT / "src/demo/__init__.py").write_text("VALUE = 1\n")
    build_wheel(repository.ROOT, "demo/__init__.py")
    assert len(repository.package()) == 1


def test_wheel_check_rejects_a_wheel_without_code(repository: ModuleType) -> None:
    build_wheel(repository.ROOT)
    assert len(repository.package()) == 1


def test_digests_match_what_git_records(repository: ModuleType) -> None:
    # The docs check recomputes proof digests with `git show`, which returns a link's text.
    root = repository.ROOT
    tool = root / "plugins/demo/bin/tool"
    tool.parent.mkdir(parents=True)
    tool.write_text("#!/bin/sh\n")
    (root / "plugins/demo/linked.py").symlink_to("../../src/demo/__init__.py")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "t"],
        cwd=root,
        check=True,
    )
    digests = repository.source_digests()
    assert set(digests) == {"plugins/demo/bin/tool", "src/demo/__init__.py"}
    for name, digest in digests.items():
        content = subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=root)
        assert hashlib.sha256(content).hexdigest() == digest


def test_digests_cover_the_code_the_plugin_runs() -> None:
    digests = checks().source_digests()
    assert "plugins/cloud-architecture-diagrams/bin/cloud-diagrams" in digests
    assert "plugins/cloud-architecture-diagrams/skills/architecture-model/SKILL.md" in digests
    for link in (ROOT / "plugins/cloud-architecture-diagrams").rglob("*"):
        if link.is_symlink():
            target = str(link.resolve().relative_to(ROOT))
            assert target in digests or any(name.startswith(f"{target}/") for name in digests)
