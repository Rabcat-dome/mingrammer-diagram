"""M2 provider and Kubernetes semantics: FR-010..015/018/020..022/029/053 and T-001..008/017."""

import copy
import json
import re
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from cloud_architecture_diagrams import semantics
from cloud_architecture_diagrams.catalog import Catalog, Representation, catalog
from cloud_architecture_diagrams.models import Architecture, KubernetesKind
from cloud_architecture_diagrams.semantics import OWNERS
from cloud_architecture_diagrams.validation import Mode, validate_json

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"
HOSTS = ["eks", "aks", "gke", "cce", "onprem"]
PROVIDERS = ["aws", "azure", "gcp", "huawei", "onprem", "hybrid"]
POSITIVE = (
    [f"providers/{name}" for name in PROVIDERS]
    + [f"kubernetes/{name}" for name in HOSTS]
    + ["core-valid", "kubernetes-valid"]
)
CASES: dict[str, list[dict[str, Any]]] = json.loads((FIXTURES / "semantics/cases.json").read_text())


def expand(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A base of kubernetes/* means the case must hold on every hosting environment (M2-06)."""
    return [
        {**case, "base": base, "id": f"{case['id']}[{base}]"}
        for case in cases
        for base in (
            [f"kubernetes/{host}" for host in HOSTS]
            if case["base"] == "kubernetes/*"
            else [case["base"]]
        )
    ]


def load(base: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((FIXTURES / (base + ".json")).read_text())
    return value


def walk(document: Any, segment: str) -> Any:
    if segment.startswith("id:"):
        identifier = segment.removeprefix("id:")
        return next(item for item in document if item["id"] == identifier)
    return document[segment]


def apply(document: dict[str, Any], operations: list[dict[str, Any]], provider: str) -> None:
    for operation in operations:
        path = operation.get("set") or operation.get("add") or operation["del"]
        *parents, leaf = path.split("/")
        target: Any = document
        for segment in parents:
            if segment not in target and isinstance(target, dict):
                target[segment] = {}
            target = walk(target, segment)
        if "del" in operation:
            if leaf.startswith("id:"):
                target.remove(walk(target, leaf))
            else:
                del target[leaf]
            continue
        value = copy.deepcopy(operation["value"])
        if isinstance(value, dict) and value.get("provider") == "@host":
            value["provider"] = provider
        if "set" in operation:
            if leaf.startswith("id:"):
                target[target.index(walk(target, leaf))] = value
            else:
                target[leaf] = value
        else:
            target.setdefault(leaf, []).append(value)
    # Added entities stay out of views, so a case tests its rule and not view disclosure.


def mutated(case: dict[str, Any]) -> dict[str, Any]:
    document = load(case["base"])
    provider = document["resources"][0]["provider"]
    apply(document, case["ops"], provider)
    return document


def codes(document: dict[str, Any], mode: Mode = "strict") -> dict[str, set[str]]:
    result = validate_json(json.dumps(document).encode(), mode=mode)
    found: dict[str, set[str]] = {"error": set(), "warning": set()}
    for item in result.diagnostics:
        found[item.severity].add(item.code)
        assert item.field.startswith("/") and item.message and item.remedy
    return found


@pytest.mark.parametrize("base", POSITIVE)
def test_positive_fixture_is_fully_valid(base: str) -> None:
    document = load(base)
    Draft202012Validator(Architecture.model_json_schema()).validate(document)
    result = validate_json(json.dumps(document).encode())
    assert result.valid, [item.code for item in result.diagnostics if item.severity == "error"]
    assert result.validation_scope == "core_catalog_provider"
    assert result.pending_checks == ["render"]
    assert result.catalog_version == catalog().version


@pytest.mark.parametrize(
    "case", expand(CASES["errors"]), ids=lambda case: case["id"] if isinstance(case, dict) else ""
)
def test_negative_case_fails_with_its_code(case: dict[str, Any]) -> None:
    document = mutated(case)
    strict = codes(document)
    assert case["expect"] in strict["error"], strict
    # A case must fail for its own reason, or a broken mutation would pass as coverage.
    if case["expect"] != "CATALOG_TYPE_UNKNOWN":
        # FR-006: known semantic errors stay fatal in lenient mode as well.
        assert case["expect"] in codes(document, "lenient")["error"]


@pytest.mark.parametrize("case", CASES["warnings"], ids=lambda case: case["id"])
def test_warning_case_is_disclosed_without_failing(case: dict[str, Any]) -> None:
    document = mutated(case)
    found = codes(document)
    assert case["expect"] in found["warning"], found
    assert not found["error"], found


def test_every_rule_has_a_negative_case_and_every_emitted_code_is_declared() -> None:
    rules = catalog().rules
    # No catalog type is blocked today, so a direct test below exercises this warning instead.
    expected = {case["expect"] for group in CASES.values() for case in group} | {"ICON_UNAVAILABLE"}
    assert set(rules) <= expected, set(rules) - expected
    source = (ROOT / "src/cloud_architecture_diagrams/semantics.py").read_text()
    emitted = set(re.findall(r'"([A-Z][A-Z0-9_]{3,})"', source))
    assert emitted == set(rules), emitted ^ set(rules)
    for rule in rules.values():
        assert rule.sources and all(rule.sources)


def test_every_catalog_type_appears_in_a_passing_fixture() -> None:
    resources: set[str] = set()
    groups: set[tuple[str, str, str]] = set()
    for base in POSITIVE:
        document = load(base)
        resources |= {item["service_type"] for item in document["resources"]}
        groups |= {(item["provider"], "scope", item["kind"]) for item in document["scopes"]}
        groups |= {(item["provider"], "boundary", item["kind"]) for item in document["boundaries"]}
    records = catalog().records.values()
    missing = {r.id for r in records if r.entity == "resource" and r.id not in resources}
    assert not missing, missing
    for record in records:
        if record.entity != "resource":
            assert any(
                (provider, record.entity, record.kind) in groups for provider in record.providers
            ), record.id


def test_a_blocked_type_warns_and_validates_without_a_substitute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    view = Catalog()
    record = view.records["huawei.storage.obs"]
    item = Representation(kind="blocked", pack="huawei-cloud-icons", blocker="O-002")
    view.records[record.id] = record.model_copy(
        update={"representation": item, "status": "semantics_only"}
    )
    monkeypatch.setattr(semantics, "catalog", lambda: view)
    found = codes(load("providers/huawei"))
    assert "ICON_UNAVAILABLE" in found["warning"] and not found["error"]


def test_core_and_guide_examples_stay_valid() -> None:
    for name in ["core-valid", "kubernetes-valid"]:
        assert validate_json((FIXTURES / (name + ".json")).read_bytes()).valid


@pytest.mark.parametrize("host", HOSTS)
def test_kubernetes_overview_and_detail_share_stable_ids(host: str) -> None:
    document = load(f"kubernetes/{host}")
    result = validate_json(json.dumps(document).encode())
    assert result.valid and result.view_exclusions["detail"] == []
    excluded = set(result.view_exclusions["overview"])
    identifiers = {item["id"] for item in document["resources"]}
    assert {"pod-a", "secret", "netpol", "pvc"} <= excluded
    assert {"cluster", "edge-lb"} <= identifiers - excluded
    assert document["resources"][0]["provider"] != "kubernetes"


@pytest.mark.parametrize("host", HOSTS)
def test_missing_pod_placement_stays_unspecified(host: str) -> None:
    document = load(f"kubernetes/{host}")
    pods = [item for item in document["resources"] if item["service_type"] == "k8s.pod"]
    assert any("node_ref" not in pod["kubernetes"] for pod in pods)
    assert validate_json(json.dumps(document).encode()).valid


def test_lenient_mode_discloses_unknown_type_without_substitution() -> None:
    document = load("providers/aws")
    web = next(item for item in document["resources"] if item["id"] == "web")
    web["service_type"] = "aws.compute.not_a_service"
    strict = validate_json(json.dumps(document).encode())
    assert not strict.valid and not strict.draft
    lenient = validate_json(json.dumps(document).encode(), mode="lenient")
    assert lenient.valid and lenient.draft
    warning = next(item for item in lenient.diagnostics if item.code == "CATALOG_TYPE_UNKNOWN")
    assert warning.severity == "warning" and warning.entity_id == "web"
    assert catalog().fallback.pack in catalog().packs
    assert catalog().packs[str(catalog().fallback.pack)].status == "approved"


def test_lenient_mode_cannot_excuse_a_bad_provider_or_a_core_error() -> None:
    document = load("providers/hybrid")
    document["resources"][0]["provider"] = "kubernetes"
    assert not validate_json(json.dumps(document).encode(), mode="lenient").valid


def test_scope_and_network_dimensions_stay_independent() -> None:
    # One resource keeps its own scope, zone, network, security and deployment answers, and a
    # Shared VPC workload's project differs from the project that owns its network.
    document = load("providers/gcp")
    vm = next(item for item in document["resources"] if item["id"] == "vm")
    network = next(item for item in document["boundaries"] if item["id"] == "vpc")
    assert vm["placement"]["scope_refs"] == ["service"] and network["scope_refs"] == ["host"]
    assert len(vm["placement"]["network_attachments"]) == 2
    assert validate_json(json.dumps(document).encode()).valid


def test_kubernetes_catalog_covers_every_kind_with_its_namespace_scope() -> None:
    from typing import get_args

    from cloud_architecture_diagrams.models import CLUSTER_SCOPED

    records = {
        record.kubernetes_kinds[0]: record for record in catalog().files["kubernetes"].records
    }
    assert set(records) == set(get_args(KubernetesKind))
    for kind, record in records.items():
        assert record.id == "k8s." + kind.lower()
        if kind != "IngressController":
            assert bool(record.namespaced) == (kind not in CLUSTER_SCOPED), kind
    assert set(OWNERS) <= set(records)
