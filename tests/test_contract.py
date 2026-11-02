"""FR-001..006/018/020/029, NFR-005/009; T-008 and the core part of T-017."""

import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from cloud_architecture_diagrams.models import MAX_INPUT_BYTES, Architecture
from cloud_architecture_diagrams.validation import Mode, validate_json

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str = "core-valid") -> dict[str, Any]:
    value: dict[str, Any] = json.loads((FIXTURES / (name + ".json")).read_text())
    return value


def codes(model: dict[str, Any], mode: Mode = "strict") -> set[str]:
    result = validate_json(json.dumps(model).encode(), mode=mode)
    assert not result.valid
    assert result.pending_checks == ["catalog", "provider_rules", "render"]
    assert all(item.remedy and item.field and item.code for item in result.diagnostics)
    return {item.code for item in result.diagnostics}


@pytest.mark.parametrize("name", ["core-valid", "kubernetes-valid"])
def test_schema_and_core_agree_on_valid_fixtures(name: str) -> None:
    data = fixture(name)
    schema = Architecture.model_json_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    result = validate_json(json.dumps(data).encode())
    assert result.valid and not result.draft
    assert result.validation_scope == "core_only" and result.pending_checks


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


@pytest.mark.parametrize("target_port", [0, 65536, True, "bad name"])
def test_port_bounds_match_schema(target_port: object) -> None:
    data = fixture()
    data["resources"][0]["properties"] = {"ports": [{"port": 443, "target_port": target_port}]}
    assert list(Draft202012Validator(Architecture.model_json_schema()).iter_errors(data))
    assert "SCHEMA_FIELD_INVALID" in codes(data)


def test_label_keys_can_preserve_native_metadata_without_inference() -> None:
    data = fixture()
    data["resources"][0]["properties"] = {"labels": {"app.kubernetes.io/name": "api", "Empty": ""}}
    assert validate_json(json.dumps(data).encode()).valid


def test_foreign_provider_ownership_is_invalid() -> None:
    data = fixture()
    data["resources"][0]["provider"] = "aws"
    assert "SCOPE_PROVIDER_MISMATCH" in codes(data)


def test_explicit_empty_view_is_not_a_silent_default() -> None:
    result = validate_json(json.dumps(fixture()).encode(), view_id="")
    assert not result.valid and result.diagnostics[-1].code == "VIEW_NOT_FOUND"
