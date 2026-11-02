"""M7 Claude Code package contract: manifests, package boundary and clean-copy runtime."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, get_args

import pytest
import yaml

from cloud_architecture_diagrams.cli import capabilities
from cloud_architecture_diagrams.models import (
    Boundary,
    KubernetesKind,
    Provider,
    Relationship,
    Scope,
)
from cloud_architecture_diagrams.validation import validate_json

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/cloud-architecture-diagrams"
SKILL = PLUGIN / "skills/architecture-model"
FIXTURES = ROOT / "tests/fixtures"
COMMAND = '"${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams"'
FILES = {
    ".claude-plugin/plugin.json",
    "README.md",
    "bin/cloud-diagrams",
    "skills/architecture-model/SKILL.md",
    "skills/architecture-model/references/model-guide.md",
}
LINKS = {
    "pyproject.toml": "pyproject.toml",
    "uv.lock": "uv.lock",
    "src": "src",
    "skills/architecture-model/examples/core-valid.json": "tests/fixtures/core-valid.json",
    "skills/architecture-model/examples/kubernetes-valid.json": (
        "tests/fixtures/kubernetes-valid.json"
    ),
}


def load(path: Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_text())
    return value


def test_marketplace_resolves_the_plugin() -> None:
    marketplace = load(ROOT / ".claude-plugin/marketplace.json")
    assert marketplace["owner"]["name"]
    [entry] = marketplace["plugins"]
    assert entry["source"].startswith("./")
    assert (ROOT / entry["source"]).resolve() == PLUGIN
    assert entry["name"] == load(PLUGIN / ".claude-plugin/plugin.json")["name"] == PLUGIN.name


def test_plugin_is_versioned_by_commit() -> None:
    # A fixed version keeps installed copies on their cached content until someone bumps it.
    assert "version" not in load(PLUGIN / ".claude-plugin/plugin.json")
    assert "version" not in load(ROOT / ".claude-plugin/marketplace.json")["plugins"][0]


def test_package_contains_only_the_allowlisted_tree() -> None:
    # Everything else, including research records and uncleared assets, stays out (NFR-004).
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", str(PLUGIN)],
        cwd=ROOT,
    )
    prefix = PLUGIN.relative_to(ROOT)
    packaged = {
        str(Path(name.decode()).relative_to(prefix)) for name in output.split(b"\0") if name
    }
    assert packaged == FILES | set(LINKS)
    assert not any((PLUGIN / name).is_symlink() for name in FILES)


@pytest.mark.parametrize(("link", "target"), LINKS.items())
def test_core_is_linked_not_copied(link: str, target: str) -> None:
    path = PLUGIN / link
    assert path.is_symlink() and not Path(os.readlink(path)).is_absolute()
    assert path.resolve() == ROOT / target


def test_skill_discloses_the_missing_renderer() -> None:
    _, frontmatter, body = (SKILL / "SKILL.md").read_text().split("---\n", 2)
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == SKILL.name
    assert metadata["allowed-tools"] == f"Bash({COMMAND} *)"
    # Quoted, so the pre-approved command also survives a plugin path containing a space.
    mentions = re.findall(r"`[^`]*bin/cloud-diagrams[^`]*`", body)
    assert mentions and all(mention.startswith(f"`{COMMAND}") for mention in mentions)
    # When rendering arrives this fails, so the skill cannot keep describing an old capability.
    assert capabilities()["render_available"] is False
    assert "cannot render" in metadata["description"]


def test_model_guide_names_every_enumerated_kind() -> None:
    guide = (SKILL / "references/model-guide.md").read_text()
    kinds = [
        *get_args(KubernetesKind),
        *get_args(Provider),
        *(
            value
            for model in (Scope, Boundary, Relationship)
            for value in get_args(model.model_fields["kind"].annotation)
        ),
    ]
    assert [kind for kind in kinds if f"`{kind}`" not in guide] == []


def test_model_guide_examples_validate() -> None:
    blocks = re.findall(
        r"```json\n(.*?)\n```", (SKILL / "references/model-guide.md").read_text(), re.S
    )
    assert blocks
    for block in blocks:
        result = validate_json(block.encode())
        assert result.valid, result.diagnostics


@pytest.fixture(scope="module")
def installed(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    """Mirror a Claude Code install: outside the checkout, with symlinks made real."""
    base = tmp_path_factory.mktemp("claude-plugin")
    copy = base / "cache" / PLUGIN.name
    shutil.copytree(PLUGIN, copy, ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "src/cloud_architecture_diagrams/__init__.py").write_text('__version__ = "copy"\n')
    ambient = {"VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"}
    environment = {key: value for key, value in os.environ.items() if key not in ambient}
    return copy, environment | {"XDG_DATA_HOME": str(base / "data")}


def run(
    installed: tuple[Path, dict[str, str]],
    *arguments: str,
    payload: bytes = b"",
    path: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    copy, environment = installed
    return subprocess.run(
        [copy / "bin/cloud-diagrams", *arguments],
        input=payload,
        capture_output=True,
        cwd=cwd or copy.parent,
        env=environment | ({"PATH": path} if path else {}),
        timeout=150,
        check=False,
    )


def test_copy_runs_its_own_core(installed: tuple[Path, dict[str, str]]) -> None:
    result = run(installed, "capabilities")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["package_version"] == "copy"


def test_copy_validates_models_from_stdin(installed: tuple[Path, dict[str, str]]) -> None:
    model = load(FIXTURES / "core-valid.json")
    model["metadata"]["title"] = "สถาปัตยกรรม"
    valid = run(installed, "validate", payload=json.dumps(model, ensure_ascii=False).encode())
    assert valid.returncode == 0, valid.stderr
    assert json.loads(valid.stdout)["validation_scope"] == "core_only"

    invalid = run(installed, "validate", payload=b'{"schema_version":"1.0.0"}')
    assert invalid.returncode == 2
    assert json.loads(invalid.stdout)["valid"] is False


def test_working_directory_cannot_shadow_modules(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # The skill pre-approves this command, so a project's files must never run through it.
    marker = tmp_path / "executed"
    (tmp_path / "pydantic.py").write_text(f"open({str(marker)!r}, 'w').close()\n")
    result = run(installed, "capabilities", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_usage_error_is_not_reported_as_an_invalid_model(
    installed: tuple[Path, dict[str, str]],
) -> None:
    result = run(installed, "validate", "--mode", "nope")
    assert result.returncode == 64 and not result.stdout


def test_missing_uv_is_a_setup_failure(installed: tuple[Path, dict[str, str]]) -> None:
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in the base system path")
    result = run(installed, "capabilities", path="/usr/bin:/bin")
    assert result.returncode == 3 and not result.stdout
    assert b"uv is required" in result.stderr


def test_setup_failure_is_not_reported_as_an_invalid_model(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # uv can exit 2, which must not read as this command's invalid-model result.
    fake = tmp_path / "uv"
    fake.write_text("#!/bin/sh\necho stray output\nexit 2\n")
    fake.chmod(0o755)
    result = run(installed, "validate", payload=b"{}", path=f"{tmp_path}:/usr/bin:/bin")
    assert result.returncode == 3 and not result.stdout
    assert b"could not prepare" in result.stderr
