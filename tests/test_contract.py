"""FR-001..006/018/020/029, NFR-005/009; T-008 and the core part of T-017."""

import copy
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from cloud_architecture_diagrams import __version__
from cloud_architecture_diagrams.models import MAX_INPUT_BYTES, Architecture
from cloud_architecture_diagrams.validation import Levels, Mode, validate_json

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str = "core-valid") -> dict[str, Any]:
    value: dict[str, Any] = json.loads((FIXTURES / (name + ".json")).read_text())
    return value


def codes(
    model: dict[str, Any], mode: Mode = "strict", pending: list[str] | None = None
) -> set[str]:
    result = validate_json(json.dumps(model).encode(), mode=mode)
    assert not result.valid
    # A core failure stops before the semantic layer, and the result must say so.
    assert result.pending_checks == (pending or ["catalog", "provider_rules", "render"])
    assert all(item.remedy and item.field and item.code for item in result.diagnostics)
    return {item.code for item in result.diagnostics}


@pytest.mark.parametrize("name", ["core-valid", "kubernetes-valid", "compass-valid"])
def test_schema_and_core_agree_on_valid_fixtures(name: str) -> None:
    data = fixture(name)
    schema = Architecture.model_json_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    result = validate_json(json.dumps(data).encode())
    assert result.valid and not result.draft
    assert result.validation_scope == "core_catalog_provider"
    assert result.pending_checks == ["render"]


def test_published_schema_matches_discovery() -> None:
    published = json.loads(Path("schemas/architecture-v1.schema.json").read_text())
    assert published == Architecture.model_json_schema()


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize(
    "case",
    [
        "id",
        "reference",
        "scope-cycle",
        "boundary-cycle",
        "view",
        "endpoint",
        "provider",
        "code",
        "type",
        "style",
    ],
)
def test_core_errors_remain_fatal_in_both_modes(case: str, mode: Mode) -> None:
    data = fixture()
    if case == "id":
        data["resources"][0]["id"] = "project"
        expected = "ID_DUPLICATE"
    elif case == "reference":
        data["resources"][0]["placement"]["scope_refs"] = ["missing"]
        expected = "REFERENCE_MISSING"
    elif case == "scope-cycle":
        data["scopes"][0]["parent_ref"] = "project"
        expected = "CONTAINMENT_CYCLE"
    elif case == "boundary-cycle":
        data["boundaries"][0]["parent_ref"] = "subnet"
        expected = "CONTAINMENT_CYCLE"
    elif case == "view":
        data["views"][0]["entity_refs"] = ["missing"]
        expected = "REFERENCE_MISSING"
    elif case == "endpoint":
        data["relationships"] = [
            {"id": "edge", "source_ref": "app", "target_ref": "vpc", "kind": "traffic"}
        ]
        data["views"][0]["relationship_refs"] = ["edge"]
        data["views"][0]["entity_refs"] = ["app"]
        expected = "VIEW_ENDPOINT_EXCLUDED"
    elif case == "provider":
        data["resources"][0]["provider"] = "kubernetes"
        expected = "SCHEMA_FIELD_INVALID"
    elif case == "code":
        data["resources"][0]["code"] = "import os"
        expected = "SCHEMA_FIELD_INVALID"
    elif case == "type":
        data["resources"][0]["properties"] = {"replicas": True}
        expected = "SCHEMA_FIELD_INVALID"
    else:
        data["views"][0]["graphviz"] = {"imagepath": "/tmp"}
        expected = "SCHEMA_FIELD_INVALID"
    assert expected in codes(data, mode)


@pytest.mark.parametrize(
    "payload,expected",
    [
        (b"\xff", "INPUT_JSON_INVALID"),
        (b'{"x":1,"x":2}', "INPUT_DUPLICATE_KEY"),
        (b"[" * 65 + b"]" * 65, "INPUT_DEPTH_LIMIT"),
        (b"x" * (MAX_INPUT_BYTES + 1), "INPUT_SIZE_LIMIT"),
        (b'{"schema_version":"9.0.0"}', "SCHEMA_VERSION_UNSUPPORTED"),
        (b'{"schema_version":"1.0.0","x":NaN}', "INPUT_JSON_INVALID"),
        (b'{"schema_version":"1.0.0","x":"\\ud800"}', "INPUT_UNICODE_INVALID"),
    ],
)
def test_bounded_parser(payload: bytes, expected: str) -> None:
    result = validate_json(payload)
    assert not result.valid and result.diagnostics[0].code == expected


def test_a_missing_field_has_its_own_code_and_remedy() -> None:
    # Work chats left metadata.environment out of their first model, and the remedy for an
    # unknown field sent each one to read the whole schema to find what was missing.
    data = fixture()
    del data["metadata"]["environment"]
    result = validate_json(json.dumps(data).encode())
    assert not result.valid
    [missing] = result.diagnostics
    assert (missing.code, missing.field) == ("SCHEMA_FIELD_MISSING", "/metadata/environment")
    assert missing.remedy.startswith("Add the field")
    data = fixture()
    data["metadata"]["extra"] = "unknown"
    assert codes(data) == {"SCHEMA_FIELD_INVALID"}


def test_labels_are_literal_utf8_and_json_depth_ignores_braces_in_strings() -> None:
    data = fixture()
    data["resources"][0]["name"] = "Application \u0e23\u0e30\u0e1a\u0e1a " + "{" * 70
    assert validate_json(json.dumps(data).encode()).valid
    data["resources"][0]["name"] = "unsafe\nlabel"
    assert "SCHEMA_FIELD_INVALID" in codes(data)


def test_partial_view_discloses_every_excluded_id_without_mutation() -> None:
    data = fixture("kubernetes-valid")
    before = copy.deepcopy(data)
    result = validate_json(json.dumps(data).encode(), view_id="compact", mode="lenient")
    assert result.valid and result.draft
    assert set(result.excluded_ids) == {
        r["id"] for r in data["resources"] if r["id"] != "cluster"
    } | {"traffic"}
    assert [d.code for d in result.diagnostics] == ["VIEW_EXCLUSIONS"]
    assert data == before
    assert not validate_json(json.dumps(data).encode(), view_id="absent").valid


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize(
    "case",
    [
        "namespace-required",
        "namespace-forbidden",
        "cluster-required",
        "cross-cluster",
        "wrong-node",
        "wrong-kind",
        "wrong-namespace",
        "owner-cycle",
        "secret-data",
        "secret-properties",
        "role",
    ],
)
def test_kubernetes_scope_and_typed_references(case: str, mode: Mode) -> None:
    data = fixture("kubernetes-valid")
    resources = {r["id"]: r for r in data["resources"]}
    pod = resources["pod-a"]["kubernetes"]
    if case == "namespace-required":
        pod.pop("namespace_ref")
        expected = "K8S_NAMESPACE_REQUIRED"
    elif case == "namespace-forbidden":
        resources["node-a"]["kubernetes"]["namespace_ref"] = "namespace"
        expected = "K8S_NAMESPACE_FORBIDDEN"
    elif case == "cluster-required":
        pod.pop("cluster_ref")
        expected = "K8S_CLUSTER_REQUIRED"
    elif case == "cross-cluster":
        cluster = copy.deepcopy(resources["cluster"])
        cluster["id"] = "other-cluster"
        data["resources"].append(cluster)
        resources["node-a"]["kubernetes"]["cluster_ref"] = "other-cluster"
        expected = "K8S_CLUSTER_MISMATCH"
    elif case == "wrong-node":
        pod["node_ref"] = "deployment"
        expected = "K8S_REFERENCE_KIND_INVALID"
    elif case == "wrong-kind":
        pod["config_refs"] = ["secret"]
        expected = "K8S_REFERENCE_KIND_INVALID"
    elif case == "wrong-namespace":
        ns = copy.deepcopy(resources["namespace"])
        ns["id"] = "other-namespace"
        data["resources"].append(ns)
        resources["secret"]["kubernetes"]["namespace_ref"] = "other-namespace"
        expected = "K8S_NAMESPACE_MISMATCH"
    elif case == "owner-cycle":
        resources["deployment"]["kubernetes"]["owner_ref"] = "replicaset"
        expected = "CONTAINMENT_CYCLE"
    elif case == "secret-data":
        resources["secret"]["properties"] = {"data": {"password": "sensitive-test-value"}}
        expected = "SCHEMA_FIELD_INVALID"
    elif case == "secret-properties":
        resources["secret"]["properties"] = {"labels": {"password": "sensitive-test-value"}}
        expected = "K8S_SECRET_REFERENCE_ONLY"
    else:
        resources["deployment"]["kubernetes"]["node_ref"] = "node-a"
        expected = "K8S_REFERENCE_ROLE_INVALID"
    result_codes = codes(data, mode)
    assert expected in result_codes
    assert "sensitive-test-value" not in validate_json(json.dumps(data).encode()).model_dump_json()


def test_namespace_and_node_are_independent_dimensions() -> None:
    data = fixture("kubernetes-valid")
    for grouping in ["namespace", "node"]:
        data["views"][0]["grouping"] = grouping
        assert validate_json(json.dumps(data).encode()).valid
    model = Architecture.model_validate(data)
    pods = [r.kubernetes for r in model.resources if r.kubernetes and r.kubernetes.kind == "Pod"]
    assert {p.node_ref for p in pods} == {"node-a", "node-b"}
    assert {p.namespace_ref for p in pods} == {"namespace"}


def test_ownership_cycles_fail_but_traffic_cycles_are_valid() -> None:
    data = fixture()
    data["relationships"] = [
        {"id": "forward", "source_ref": "app", "target_ref": "vpc", "kind": "traffic"},
        {"id": "back", "source_ref": "vpc", "target_ref": "app", "kind": "traffic"},
    ]
    assert validate_json(json.dumps(data).encode()).valid
    for edge in data["relationships"]:
        edge["kind"] = "ownership"
    assert "CONTAINMENT_CYCLE" in codes(data)


def test_long_chain_and_combined_entity_bound() -> None:
    data = fixture()
    data["scopes"] = [
        {
            "id": f"s-{i}",
            "name": "Scope",
            "provider": "gcp",
            "kind": "folder",
            **({"parent_ref": f"s-{i - 1}"} if i else {}),
        }
        for i in range(1000)
    ]
    data["resources"] = []
    data["boundaries"] = []
    data["views"][0]["entity_refs"] = ["s-999"]
    assert validate_json(json.dumps(data).encode()).valid
    data["boundaries"] = [
        {"id": "one-too-many", "name": "Site", "provider": "onprem", "kind": "site"}
    ]
    assert "MODEL_ENTITY_LIMIT" in codes(data)


def test_every_partial_view_is_disclosed_whichever_view_is_selected() -> None:
    # FR-025: a complete first view must not hide a later partial view.
    result = validate_json((FIXTURES / "kubernetes-valid.json").read_bytes())
    assert result.valid and result.selected_view == "detail" and result.excluded_ids == []
    assert result.view_exclusions["detail"] == []
    assert result.view_exclusions["compact"]
    assert [(d.code, d.entity_id) for d in result.diagnostics] == [("VIEW_EXCLUSIONS", "compact")]
    selected = validate_json((FIXTURES / "kubernetes-valid.json").read_bytes(), view_id="compact")
    assert selected.excluded_ids == result.view_exclusions["compact"]
    assert selected.view_exclusions == result.view_exclusions


def test_package_versions_agree() -> None:
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    assert project["version"] == __version__


def test_results_are_utf8_whatever_the_output_encoding() -> None:
    # A rejected key is echoed in `field`, so results can carry non-ASCII text.
    payload = '{"schema_version":"1.0.0","สถาปัตยกรรม":1}'.encode()
    result = subprocess.run(
        ["cloud-diagrams", "validate"],
        input=payload,
        capture_output=True,
        env=os.environ | {"PYTHONIOENCODING": "ascii"},
    )
    assert result.returncode == 2 and not result.stderr
    fields = [item["field"] for item in json.loads(result.stdout)["diagnostics"]]
    assert any("สถาปัตยกรรม" in field for field in fields)


def test_cli_exit_codes_and_discovery() -> None:
    for command in ["schema", "capabilities"]:
        result = subprocess.run(["cloud-diagrams", command], capture_output=True, check=True)
        assert isinstance(json.loads(result.stdout), dict) and not result.stderr
    result = subprocess.run(
        ["cloud-diagrams", "validate"],
        input=(FIXTURES / "core-valid.json").read_bytes(),
        capture_output=True,
    )
    assert result.returncode == 0 and json.loads(result.stdout)["valid"]
    bad = subprocess.run(
        ["cloud-diagrams", "validate", "--mode", "lenient"], input=b"{}", capture_output=True
    )
    assert bad.returncode == 2 and not json.loads(bad.stdout)["valid"] and not bad.stderr
    # Exit 2 means an invalid model, so a command-usage error must not share it.
    usage = subprocess.run(["cloud-diagrams", "validate", "--mode", "nope"], capture_output=True)
    assert usage.returncode == 64 and not usage.stdout and usage.stderr


@pytest.mark.parametrize("target_port", [0, 65536, True, "bad name"])
def test_port_bounds_match_schema(target_port: object) -> None:
    data = fixture()
    data["resources"][0]["properties"] = {"ports": [{"port": 443, "target_port": target_port}]}
    assert list(Draft202012Validator(Architecture.model_json_schema()).iter_errors(data))
    assert "SCHEMA_FIELD_INVALID" in codes(data)


def test_label_keys_can_preserve_native_metadata_without_inference() -> None:
    labels = {"app.kubernetes.io/name": "api", "Empty": ""}
    data = fixture("kubernetes-valid")
    data["resources"][0]["properties"] = {"labels": labels}
    assert validate_json(json.dumps(data).encode()).valid
    # The same keys break GCP's own label syntax, which M2 enforces on a non-Kubernetes resource.
    data = fixture()
    data["resources"][0]["properties"] = {"labels": labels}
    assert "LABEL_SYNTAX_INVALID" in codes(data, pending=["render"])


def test_foreign_provider_ownership_is_invalid() -> None:
    data = fixture()
    data["resources"][0]["provider"] = "aws"
    assert "SCOPE_PROVIDER_MISMATCH" in codes(data)


def test_explicit_empty_view_is_not_a_silent_default() -> None:
    result = validate_json(json.dumps(fixture()).encode(), view_id="")
    assert not result.valid and result.diagnostics[-1].code == "VIEW_NOT_FOUND"


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("case", ["namespace", "cluster", "kind", "plain-resource", "valid"])
def test_ownership_edges_use_the_same_context_rules_as_owner_ref(case: str, mode: Mode) -> None:
    data = fixture("kubernetes-valid")
    resources = {resource["id"]: resource for resource in data["resources"]}
    resources["pod-a"]["kubernetes"].pop("owner_ref")
    owner_id = "replicaset"
    if case in {"namespace", "cluster"}:
        namespace = copy.deepcopy(resources["namespace"])
        namespace["id"] = "other-namespace"
        data["resources"].append(namespace)
        owner = resources["replicaset"]["kubernetes"]
        owner.pop("owner_ref")
        owner["namespace_ref"] = namespace["id"]
        if case == "cluster":
            cluster = copy.deepcopy(resources["cluster"])
            cluster["id"] = "other-cluster"
            data["resources"].append(cluster)
            namespace["kubernetes"]["cluster_ref"] = "other-cluster"
            owner["cluster_ref"] = "other-cluster"
    elif case == "kind":
        owner_id = "node-a"
    elif case == "plain-resource":
        owner_id = "plain-resource"
        data["resources"].append(
            {
                "id": owner_id,
                "name": "VM",
                "provider": "gcp",
                "service_type": "gcp.compute.vm",
                "taxonomy": "compute.vm",
            }
        )
    data["relationships"].append(
        {
            "id": "controller-owner",
            "source_ref": owner_id,
            "target_ref": "pod-a",
            "kind": "ownership",
        }
    )
    edge_result = validate_json(json.dumps(data).encode(), mode=mode)
    data["relationships"].pop()
    resources["pod-a"]["kubernetes"]["owner_ref"] = owner_id
    ref_result = validate_json(json.dumps(data).encode(), mode=mode)
    assert edge_result.valid == ref_result.valid == (case == "valid")
    if case != "valid":
        expected = {
            "namespace": "K8S_NAMESPACE_MISMATCH",
            "cluster": "K8S_CLUSTER_MISMATCH",
            "kind": "K8S_REFERENCE_KIND_INVALID",
            "plain-resource": "K8S_REFERENCE_KIND_INVALID",
        }[case]
        assert expected in {item.code for item in edge_result.diagnostics}
        assert expected in {item.code for item in ref_result.diagnostics}


@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_mixed_controller_ownership_cycle_is_fatal(mode: Mode) -> None:
    data = fixture("kubernetes-valid")
    data["relationships"].append(
        {"id": "cycle-edge", "source_ref": "pod-a", "target_ref": "replicaset", "kind": "ownership"}
    )
    assert "CONTAINMENT_CYCLE" in codes(data, mode)


def test_docs_gate_requires_portable_links_not_existing_external_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "scripts/repository_checks.py").write_bytes(
        Path("scripts/repository_checks.py").read_bytes()
    )
    documents = {
        "doc/requirements/requirements.md": "| FR-001 | Rule |\n| T-001 Case |\n",
        "doc/project-management/milestones.md": "| M1-01 | Task |\n",
        "doc/project-management/decisions.md": "| D-001 | Decision |\n",
        "README.md": "[Requirements](doc/requirements/requirements.md)\n",
    }
    for name, text in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    command = [sys.executable, str(root / "scripts/repository_checks.py"), "docs"]
    assert subprocess.run(command, cwd=root, capture_output=True).returncode == 0
    artifact = tmp_path / "historical.png"
    artifact.write_bytes(b"historical sentinel")
    (root / "README.md").write_text(f"[Historical artifact]({artifact})\n")
    rejected = subprocess.run(command, cwd=root, capture_output=True)
    assert rejected.returncode == 1 and b"must stay inside the repository" in rejected.stdout
    (root / "README.md").write_text(f"Historical provenance: `{artifact}`.\n")
    artifact.unlink()
    assert subprocess.run(command, cwd=root, capture_output=True).returncode == 0


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("provider", ["gcp", "aws"])
def test_administrative_cluster_owner_remains_separate(mode: Mode, provider: str) -> None:
    data = fixture("kubernetes-valid")
    data["scopes"] = [
        {
            "id": "admin",
            "name": "Administrative owner",
            "provider": provider,
            "kind": "project" if provider == "gcp" else "account",
        }
    ]
    data["relationships"].append(
        {"id": "admin-owner", "source_ref": "admin", "target_ref": "cluster", "kind": "ownership"}
    )
    result = validate_json(json.dumps(data).encode(), mode=mode)
    assert result.valid == (provider == "gcp")
    if provider == "aws":
        assert "SCOPE_PROVIDER_MISMATCH" in {item.code for item in result.diagnostics}


@pytest.mark.parametrize("field", ["source_ref", "target_ref"])
@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_a_relationship_endpoint_must_exist(field: str, mode: Mode) -> None:
    # FR-004: a dangling edge would otherwise draw from nothing, and no mode may excuse it.
    model = fixture("core-valid")
    model["relationships"] = [
        {
            "id": "edge",
            "source_ref": model["resources"][0]["id"],
            "target_ref": model["resources"][0]["id"],
            "kind": "traffic",
        }
    ]
    assert validate_json(json.dumps(model).encode(), mode=mode).valid
    model["relationships"][0][field] = "nothing-here"
    result = validate_json(json.dumps(model).encode(), mode=mode)
    assert not result.valid
    assert "REFERENCE_MISSING" in {item.code for item in result.diagnostics}


@pytest.mark.parametrize("arguments", [["validate"], ["render", "--output", "out"]])
def test_the_command_line_is_strict_unless_told_otherwise(
    arguments: list[str], tmp_path: Path
) -> None:
    # FR-006: the plugins reach the core through this command, so its own default must hold too.
    model = fixture("core-valid")
    model["resources"][0]["service_type"] = "external.system.madeup"
    result = subprocess.run(
        ["cloud-diagrams", *arguments],
        input=json.dumps(model).encode(),
        cwd=tmp_path,
        capture_output=True,
        timeout=120,
        check=False,
    )
    report = json.loads(result.stdout)
    assert result.returncode == 2 and report["mode"] == "strict" and not report["draft"]
    assert "CATALOG_TYPE_UNKNOWN" in {item["code"] for item in report["diagnostics"]}


def _compass_errors(model: dict[str, Any], mode: Mode = "strict") -> list[tuple[str, str]]:
    result = validate_json(json.dumps(model).encode(), mode=mode)
    return [(item.code, item.field) for item in result.diagnostics if item.severity == "error"]


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("direction", ("VIEW_BAND_DIRECTION", "/views/0/direction")),
        ("east-west-direction", ("VIEW_BAND_DIRECTION", "/views/0/direction")),
        ("band-id", ("VIEW_BAND_ID_DUPLICATE", "/views/0/bands/1/id")),
        ("band-missing", ("REFERENCE_MISSING", "/views/0/bands/0/entity_refs/1")),
        ("band-unselected", ("VIEW_BAND_ENTITY_EXCLUDED", "/views/0/bands/0/entity_refs/1")),
        ("band-repeat", ("REFERENCE_DUPLICATE", "/views/0/bands/2/entity_refs")),
        ("two-bands", ("VIEW_BAND_CONFLICT", "/views/0/bands/3/entity_refs/2")),
        ("line-missing", ("VIEW_RELATIONSHIP_MISSING", "/views/0/east_west_refs/2")),
        ("line-unselected", ("VIEW_EAST_WEST_UNSELECTED", "/views/0/east_west_refs/0")),
        ("line-repeat", ("REFERENCE_DUPLICATE", "/views/0/east_west_refs")),
        ("line-across", ("VIEW_EAST_WEST_CONFLICT", "/views/0/east_west_refs/2")),
        ("chain-across", ("VIEW_EAST_WEST_CONFLICT", "/views/0/east_west_refs/3")),
    ],
)
def test_bands_and_east_west_lines_cannot_contradict_themselves(
    case: str, expected: tuple[str, str], mode: Mode
) -> None:
    # D-055: a band is one row and an east-west line stays level, so no mode may draw a row twice.
    model = fixture("compass-valid")
    view = model["views"][0]
    if case == "direction":
        view["direction"] = "LR"
    elif case == "east-west-direction":
        view["bands"] = []
        view["direction"] = "LR"
    elif case == "band-id":
        view["bands"][1]["id"] = view["bands"][0]["id"]
    elif case == "band-missing":
        view["bands"][0]["entity_refs"].append("nothing-here")
    elif case == "band-unselected":
        view["bands"][0]["entity_refs"].append("az-a1")
    elif case == "band-repeat":
        view["bands"][2]["entity_refs"].append("app-a")
    elif case == "two-bands":
        view["bands"][3]["entity_refs"].append("app-a")
    elif case == "line-missing":
        view["east_west_refs"].append("nothing-here")
    elif case == "line-unselected":
        view["relationship_refs"].remove("peering-ab")
    elif case == "line-repeat":
        view["east_west_refs"].append("peering-ab")
    elif case == "line-across":
        # Traffic from App A to its database runs between two bands, so it cannot run level.
        view["east_west_refs"].append("app-a-db-a")
    else:
        # Each line alone is fine; together they put the app row and the data row on one level.
        model["relationships"].append(
            {
                "id": "app-b-vpc-b",
                "source_ref": "app-b",
                "target_ref": "vpc-b",
                "kind": "dependency",
            }
        )
        model["relationships"].append(
            {"id": "vpc-a-db-a", "source_ref": "vpc-a", "target_ref": "db-a", "kind": "dependency"}
        )
        view["relationship_refs"] += ["app-b-vpc-b", "vpc-a-db-a"]
        view["east_west_refs"] += ["app-b-vpc-b", "vpc-a-db-a"]
    assert expected in _compass_errors(model, mode)


@pytest.mark.parametrize(
    "change",
    [
        {"bands": [{"id": "north", "entity_refs": []}]},
        {"bands": [{"id": "north", "entity_refs": ["users"], "rank": "min"}]},
        {"bands": [{"id": f"band-{n}", "entity_refs": ["users"]} for n in range(33)]},
        {"bands": [{"id": "North", "entity_refs": ["users"]}]},
        {"east_west_refs": "peering-ab"},
    ],
)
def test_bands_take_only_bounded_values(change: dict[str, Any]) -> None:
    # FR-045: a band names rows, never Graphviz rank attributes or unbounded lists.
    model = fixture("compass-valid")
    model["views"][0].update(change)
    assert {code for code, _ in _compass_errors(model)} == {"SCHEMA_FIELD_INVALID"}


def test_a_view_without_bands_or_east_west_lines_keeps_its_direction() -> None:
    model = fixture("compass-valid")
    view = model["views"][1]
    assert "bands" not in view and "east_west_refs" not in view
    view["direction"] = "LR"
    assert _compass_errors(model) == []


def test_levels_join_east_west_lines_to_their_band_or_keep_them_apart() -> None:
    model = Architecture.model_validate(fixture("compass-valid"))
    view = model.views[0]
    ends = {edge.id: (edge.source_ref, edge.target_ref) for edge in model.relationships}
    bands, levels = Levels.of(view, ends).rows(view)
    assert bands == (
        ("users",),
        ("alb-a",),
        ("app-a", "app-b"),
        ("db-a", "db-b"),
        ("vpn-a",),
        ("onprem-router",),
    )
    # The peering runs between two VPC boxes that no band names, so it is a level of its own.
    assert levels == (("vpc-a", "vpc-b"),)
    # An end that joins a band takes that band's row, after the members the band names.
    joined = view.model_copy(update={"east_west_refs": ["app-b-db-b"]})
    joined = joined.model_copy(
        update={
            "bands": [view.bands[2], view.bands[0].model_copy(update={"entity_refs": ["app-a"]})]
        }
    )
    assert Levels.of(joined, ends).rows(joined)[0][0] == ("app-a", "app-b", "db-b")
