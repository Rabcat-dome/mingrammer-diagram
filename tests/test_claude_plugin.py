"""M7 Claude Code package contract: manifests, package boundary and clean-copy runtime."""

import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any, get_args

import pytest
import yaml

from cloud_architecture_diagrams.catalog import catalog
from cloud_architecture_diagrams.cli import capabilities
from cloud_architecture_diagrams.models import (
    CLUSTER_SCOPED,
    Boundary,
    BoundaryRelation,
    KubernetesKind,
    Port,
    Properties,
    Provider,
    Relationship,
    Scope,
    View,
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


def literals(annotation: Any) -> set[str]:
    """Literal values, looking through `Literal[...] | None`."""
    found: set[str] = set()
    for item in get_args(annotation):
        found |= literals(item) if get_args(item) else {item} if isinstance(item, str) else set()
    return found


GUIDE_LISTS = {
    "provider": (r"\*\*Provider:\*\* (.*?)\. Use", literals(Provider)),
    "scope": (
        r"## Scopes.*?Kinds: (.*?)\. A parent",
        literals(Scope.model_fields["kind"].annotation),
    ),
    "boundary": (
        r"## Boundaries.*?Kinds: (.*?)\.\n",
        literals(Boundary.model_fields["kind"].annotation),
    ),
    "boundary-relation": (
        r"with kind (.*?)\. Containment",
        literals(BoundaryRelation.model_fields["kind"].annotation),
    ),
    "service-type": (
        r"Kubernetes Service type: (.*?)\)",
        literals(Properties.model_fields["service_type"].annotation),
    ),
    "port-protocol": (
        r"`protocol` one of (.*?)\)",
        literals(Port.model_fields["protocol"].annotation),
    ),
    "relationship": (
        r"## Relationships.*?Kinds: (.*?)\. `direction`",
        literals(Relationship.model_fields["kind"].annotation),
    ),
    "relationship-direction": (
        r"`direction` is (.*?)\.\n",
        literals(Relationship.model_fields["direction"].annotation),
    ),
    "view-grouping": (
        r"`grouping`: (.*?)\. `direction`",
        literals(View.model_fields["grouping"].annotation),
    ),
    "view-direction": (
        r"`direction`: (.*?)\. `style`",
        literals(View.model_fields["direction"].annotation),
    ),
    "view-style": (r"`style`: (.*?)\.\n", literals(View.model_fields["style"].annotation)),
    "kubernetes-kind": (r"\nKinds: (`Cluster`.*?)\.\n", literals(KubernetesKind)),
    "cluster-scoped": (r"forbid `namespace_ref`: (.*?)\.\n", set(CLUSTER_SCOPED)),
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


def test_skill_states_what_the_renderer_does() -> None:
    _, frontmatter, body = (SKILL / "SKILL.md").read_text().split("---\n", 2)
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == SKILL.name
    assert metadata["allowed-tools"] == f"Bash({COMMAND} *)"
    # Quoted, so the pre-approved command also survives a plugin path containing a space.
    mentions = re.findall(r"`[^`]*bin/cloud-diagrams[^`]*`", body)
    assert mentions and all(mention.startswith(f"`{COMMAND}") for mention in mentions)
    # When capabilities move this fails, so the skill cannot keep describing old ones.
    assert capabilities()["commands"] == ["schema", "capabilities", "validate", "catalog", "render"]
    assert capabilities()["pending_checks"] == []
    assert capabilities()["render"]["formats"] == ["svg", "png"]  # type: ignore[index]
    assert "cannot render" not in metadata["description"]
    assert "SVG" in metadata["description"] and "PNG" in metadata["description"]
    # The discovery command the skill relies on must stay in its workflow.
    assert f"{COMMAND} catalog" in body
    assert f"{COMMAND} render --output" in body
    # A bundle's limits and fallbacks must reach the user, so the skill must keep saying so.
    for term in ("`rendered`", "`artifacts`", "`rights`", "DRAFT", "Graphviz", "exit 4"):
        assert term.lower() in body.lower(), term


def test_skill_still_forbids_drawing_outside_the_controlled_renderer() -> None:
    body = (SKILL / "SKILL.md").read_text()
    assert "Do not fill the gap" in body
    for term in ("`diagrams` Python", "Graphviz DOT"):
        assert term in body, term


def test_plugin_manifests_stop_saying_rendering_is_unavailable() -> None:
    for path in (PLUGIN / ".claude-plugin/plugin.json", ROOT / ".claude-plugin/marketplace.json"):
        assert "Rendering is not available" not in path.read_text()
    readme = (PLUGIN / "README.md").read_text()
    assert "cannot render" not in readme.lower()
    assert "Graphviz" in readme and "render --output" in readme


@pytest.mark.parametrize(("pattern", "expected"), GUIDE_LISTS.values(), ids=GUIDE_LISTS.keys())
def test_model_guide_lists_match_the_contract(pattern: str, expected: set[str]) -> None:
    guide = (SKILL / "references/model-guide.md").read_text()
    match = re.search(pattern, guide, re.S)
    assert match, pattern
    assert set(re.findall(r"`([^`]+)`", match.group(1))) == expected


def test_model_guide_taxonomy_matches_requirements() -> None:
    requirements = (ROOT / "doc/requirements/requirements.md").read_text()
    baseline = requirements.split("Initial taxonomy IDs", 1)[1].split("```")[1]
    guide = (SKILL / "references/model-guide.md").read_text()
    line = next(line for line in guide.splitlines() if line.startswith("- `taxonomy`"))
    listed = set(re.findall(r"`([a-z_]+\.[a-z_]+)`", line))
    assert listed == set(re.findall(r"[a-z_]+\.[a-z_]+", baseline))


def test_skill_discloses_what_validation_leaves_unchecked() -> None:
    # M2 enforces these, so the caveat must stop calling them unchecked and name what is left.
    model = load(FIXTURES / "core-valid.json")
    model["resources"][0]["taxonomy"] = "made.up"
    model["resources"][0]["service_type"] = "not.a.real.service"
    result = validate_json(json.dumps(model).encode())
    assert {"CATALOG_TAXONOMY_UNKNOWN", "CATALOG_TYPE_UNKNOWN"} <= {
        item.code for item in result.diagnostics
    }
    assert not result.valid
    skill = (SKILL / "SKILL.md").read_text()
    caveat = next(line for line in skill.splitlines() if line.startswith('A `"valid": true`'))
    assert "`service_type`" not in caveat and "`taxonomy`" not in caveat
    for limit in ("reachab", "deployed", "render"):
        assert limit in caveat, limit


def test_skill_discloses_the_huawei_icon_blocker() -> None:
    # A Huawei model validates, so the skill must still state both limits on its icons.
    blockers = capabilities()["release_blockers"]
    assert isinstance(blockers, list)
    assert [item["id"] for item in blockers] == ["O-002"]
    skill = (SKILL / "SKILL.md").read_text()
    for term in ("ICON_UNAVAILABLE", "ASSET_PRIVATE_USE_ONLY", "generic", "private personal use"):
        assert term in skill, term


def test_model_guide_types_exist_in_the_catalog() -> None:
    guide = (SKILL / "references/model-guide.md").read_text()
    pattern = r"`((?:aws|azure|gcp|huawei|onprem|external|k8s|common)\.[a-z_.]+)`"
    named = set(re.findall(pattern, guide)) - set(catalog().taxonomy_ids)
    assert len(named) > 10
    assert named <= set(catalog().records), named - set(catalog().records)


def test_model_guide_lists_every_kubernetes_mapping_rule() -> None:
    guide = (SKILL / "references/model-guide.md").read_text()
    for cluster, mode in catalog().cluster_modes.items():
        assert f"`{cluster}`" in guide, cluster
        for pool in mode.node_pool_types:
            assert f"`{pool}`" in guide, pool


def test_skill_reports_exclusions_for_every_view() -> None:
    skill = (SKILL / "SKILL.md").read_text()
    assert "`view_exclusions`" in skill and "every view" in skill


def test_copy_serves_catalog_data_and_assets_from_its_own_tree(
    installed: tuple[Path, dict[str, str]],
) -> None:
    # Data files must survive the same copy that real installs use, not only the checkout.
    result = run(installed, "catalog", "--type", "onprem.storage.nas")
    assert result.returncode == 0, result.stderr
    [record] = json.loads(result.stdout)["records"]
    assert record["representation"]["asset"] == "onprem-nas"
    copied = installed[0] / "src/cloud_architecture_diagrams"
    assert (copied / "assets/onprem/nas.svg").is_file()
    assert (copied / "assets/NOTICE.md").is_file()


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
    # CI sets the bytecode variables itself, which would hide a wrapper that stopped passing -B.
    ambient = {
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "UV_PROJECT_ENVIRONMENT",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONPYCACHEPREFIX",
    }
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


def locked_runtime_packages() -> dict[str, str]:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    packages = {package["name"]: package for package in lock["package"]}
    pending = [item["name"] for item in packages[PLUGIN.name]["dependencies"]]
    found: dict[str, str] = {}
    while pending:
        name = pending.pop()
        if name not in found:
            found[name] = packages[name]["version"]
            pending += [item["name"] for item in packages[name].get("dependencies", [])]
    return found


def test_environment_holds_exactly_the_locked_runtime_packages(
    installed: tuple[Path, dict[str, str]],
) -> None:
    # No development tools, and no build of the project: its code runs from the plugin copy.
    result = run(installed, "capabilities")
    assert result.returncode == 0, result.stderr
    environment = Path(installed[1]["XDG_DATA_HOME"]) / (
        "cloud-architecture-diagrams/claude-plugin/venv/lib/python3.13/site-packages"
    )
    found = {}
    for info in environment.glob("*.dist-info"):
        name, version = info.name.removesuffix(".dist-info").rsplit("-", 1)
        found[name.lower().replace("_", "-")] = version
    assert found == locked_runtime_packages()


def test_runs_leave_the_plugin_unchanged(installed: tuple[Path, dict[str, str]]) -> None:
    def contents() -> dict[Path, bytes]:
        return {path: path.read_bytes() for path in installed[0].rglob("*") if path.is_file()}

    before = contents()
    payload = (FIXTURES / "core-valid.json").read_bytes()
    assert run(installed, "capabilities").returncode == 0
    assert run(installed, "validate", payload=payload).returncode == 0
    assert contents() == before
    # Earlier tests may already have run, so a snapshot alone would miss bytecode they wrote.
    assert not list(installed[0].rglob("__pycache__"))


def test_stale_lock_is_a_setup_failure(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # The command must refuse a stale lock, not rewrite the plugin's lock and carry on.
    stale = tmp_path / PLUGIN.name
    shutil.copytree(installed[0], stale)
    project = stale / "pyproject.toml"
    project.write_text(project.read_text().replace('version = "', 'version = "9', 1))
    lock = (stale / "uv.lock").read_bytes()
    result = run((stale, installed[1]), "capabilities")
    assert result.returncode == 3 and not result.stdout
    assert (stale / "uv.lock").read_bytes() == lock


def test_setup_cannot_consume_the_model_or_write_to_stdout(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # stdin carries the model and stdout carries the result, so setup is cut off from both.
    assert run(installed, "capabilities").returncode == 0
    fake = tmp_path / "uv"
    fake.write_text("#!/bin/sh\ncat >/dev/null\necho stray output\n")
    fake.chmod(0o755)
    payload = (FIXTURES / "core-valid.json").read_bytes()
    result = run(installed, "validate", payload=payload, path=f"{tmp_path}:/usr/bin:/bin")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"] is True


def test_copy_runs_its_own_core(installed: tuple[Path, dict[str, str]]) -> None:
    result = run(installed, "capabilities")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["package_version"] == "copy"


def test_copy_renders_a_complete_bundle(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # A clean copy with its own locked environment, the way a real install renders.
    output = tmp_path / "bundles"
    payload = (FIXTURES / "core-valid.json").read_bytes()
    result = run(installed, "render", "--output", str(output), payload=payload, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["rendered"] is True and report["bundle_path"].startswith(str(output))
    names = {item["name"] for item in report["artifacts"]}
    assert {"diagram.svg", "diagram.png", "manifest.json"} <= names
    for item in report["artifacts"]:
        assert Path(item["path"]).stat().st_size == item["bytes"]
    manifest = next(item for item in report["artifacts"] if item["name"] == "manifest.json")
    assert json.loads(Path(manifest["path"]).read_text())["status"] == "complete"


def test_copy_serves_fonts_and_private_use_terms_from_its_own_tree(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    payload = (FIXTURES / "providers/huawei.json").read_bytes()
    result = run(installed, "render", "--output", str(tmp_path / "out"), payload=payload)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["rights"]["private_use_only"] is True
    assert report["rights"]["blockers"] == ["O-002"]
    assert (installed[0] / "src/cloud_architecture_diagrams/assets/fonts").is_dir()


def test_failed_render_keeps_its_exit_status_and_report(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # Exit 4 carries JSON diagnostics, so the wrapper must not rewrite it into a runtime failure.
    target = tmp_path / "a-file"
    target.write_text("")
    payload = (FIXTURES / "core-valid.json").read_bytes()
    result = run(installed, "render", "--output", str(target), payload=payload)
    assert result.returncode == 4 and not result.stderr
    assert json.loads(result.stdout)["rendered"] is False
    invalid = run(installed, "render", "--output", str(tmp_path / "out"), payload=b"{}")
    assert invalid.returncode == 2 and json.loads(invalid.stdout)["rendered"] is False


def test_copy_validates_models_from_stdin(installed: tuple[Path, dict[str, str]]) -> None:
    model = load(FIXTURES / "core-valid.json")
    model["metadata"]["title"] = "สถาปัตยกรรม"
    valid = run(installed, "validate", payload=json.dumps(model, ensure_ascii=False).encode())
    assert valid.returncode == 0, valid.stderr
    assert json.loads(valid.stdout)["validation_scope"] == "core_catalog_provider"

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


def test_unusual_install_paths_work(installed: tuple[Path, dict[str, str]], tmp_path: Path) -> None:
    odd = tmp_path / "my plugins:v1" / PLUGIN.name
    shutil.copytree(installed[0], odd)
    (odd / "src/cloud_architecture_diagrams/__init__.py").write_text('__version__ = "odd"\n')
    result = run((odd, installed[1]), "capabilities")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["package_version"] == "odd"


def test_hostile_python_environment_is_ignored(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    marker = tmp_path / "executed"
    planted = tmp_path / "planted"
    planted.mkdir()
    (planted / "pydantic.py").write_text(f"open({str(marker)!r}, 'w').close()\n")
    hostile = {
        "PYTHONPATH": str(planted),
        "PYTHONHOME": str(planted),
        "VIRTUAL_ENV": str(planted),
        "UV_PROJECT_ENVIRONMENT": str(tmp_path / "other"),
    }
    result = run((installed[0], installed[1] | hostile), "capabilities")
    assert result.returncode == 0, result.stderr
    assert not marker.exists() and not (tmp_path / "other").exists()


def test_project_files_do_not_affect_setup(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    for name in ["uv.toml", "pyproject.toml", "uv.lock"]:
        (tmp_path / name).write_text("not [valid toml\n")
    (tmp_path / ".python-version").write_text("2.7\n")
    result = run(installed, "capabilities", cwd=tmp_path)
    assert result.returncode == 0, result.stderr


def test_relative_data_home_cannot_run_project_files(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    # A relative location resolves inside the project, under the pre-approved command.
    copy, environment = installed
    assert run(installed, "capabilities").returncode == 0
    share = tmp_path / "home/.local/share"
    share.mkdir(parents=True)
    (share / "cloud-architecture-diagrams").symlink_to(
        Path(environment["XDG_DATA_HOME"]) / "cloud-architecture-diagrams"
    )
    marker = tmp_path / "executed"
    project = tmp_path / "project"
    python = project / "relative/cloud-architecture-diagrams/claude-plugin/venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\ntouch {marker}\n")
    python.chmod(0o755)
    hostile = environment | {"XDG_DATA_HOME": "relative", "HOME": str(tmp_path / "home")}
    result = run((copy, hostile), "capabilities", cwd=project)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


@pytest.mark.parametrize("shell", ["/bin/sh", "/bin/dash"])
def test_missing_home_is_a_setup_failure(
    installed: tuple[Path, dict[str, str]], shell: str
) -> None:
    # dash exits 2 on an unset variable under set -u, which would read as an invalid model.
    if not Path(shell).exists():
        pytest.skip(f"{shell} is not available")
    copy, environment = installed
    bare = {k: v for k, v in environment.items() if k not in {"HOME", "XDG_DATA_HOME"}}
    result = subprocess.run(
        [shell, copy / "bin/cloud-diagrams", "capabilities"],
        capture_output=True,
        env=bare,
        check=False,
    )
    assert result.returncode == 3 and not result.stdout
    assert b"absolute path" in result.stderr


def test_unexpected_runtime_failure_is_not_a_model_result(
    installed: tuple[Path, dict[str, str]], tmp_path: Path
) -> None:
    broken = tmp_path / PLUGIN.name
    shutil.copytree(installed[0], broken)
    (broken / "src/cloud_architecture_diagrams/cli.py").unlink()
    result = run((broken, installed[1]), "capabilities")
    assert result.returncode == 3 and not result.stdout
    assert b"failed unexpectedly" in result.stderr


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
