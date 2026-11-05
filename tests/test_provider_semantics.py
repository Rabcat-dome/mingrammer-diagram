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
PROVIDERS = ["aws", "aws-ecs-lambda-waf", "azure", "gcp", "huawei", "onprem", "hybrid"]
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


def entity(document: dict[str, Any], collection: str, identifier: str) -> dict[str, Any]:
    return next(item for item in document[collection] if item["id"] == identifier)


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("provider", ["aws", "azure", "gcp", "huawei"])
@pytest.mark.parametrize("encoding", ["relation", "agreeing", "conflicting"])
def test_subnet_membership_encodings(mode: Mode, provider: str, encoding: str) -> None:
    document = load(f"providers/{provider}")
    subnet = next(item for item in document["boundaries"] if item["kind"] == "subnet")
    network = subnet["parent_ref"]
    if encoding == "relation":
        del subnet["parent_ref"]
    if encoding == "conflicting":
        other = copy.deepcopy(entity(document, "boundaries", network))
        other["id"] = "network-other"
        document["boundaries"].append(other)
        network = other["id"]
    subnet.setdefault("relations", []).append({"kind": "network_member_of", "target_ref": network})
    errors = codes(document, mode)["error"]
    if encoding == "conflicting":
        assert "BOUNDARY_NETWORK_COUNT_INVALID" in errors
    else:
        assert not errors, errors


@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_relation_only_subnet_still_checks_network_region(mode: Mode) -> None:
    document = load("providers/aws")
    subnet = entity(document, "boundaries", "app-a")
    del subnet["parent_ref"]
    subnet["relations"].append({"kind": "network_member_of", "target_ref": "vpc"})
    region = copy.deepcopy(entity(document, "boundaries", "region"))
    region["id"] = "region-other"
    document["boundaries"].append(region)
    entity(document, "boundaries", "az-a")["parent_ref"] = "region-other"
    result = validate_json(json.dumps(document).encode(), mode=mode)
    mismatched = {
        item.entity_id for item in result.diagnostics if item.code == "BOUNDARY_REGION_MISMATCH"
    }
    assert "app-a" in mismatched


@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_multi_vpc_ec2_remains_valid(mode: Mode) -> None:
    document = load("providers/aws")
    network = copy.deepcopy(entity(document, "boundaries", "vpc"))
    network["id"] = "network-other"
    subnet = copy.deepcopy(entity(document, "boundaries", "app-a"))
    subnet.update(id="subnet-other", parent_ref="network-other")
    document["boundaries"].extend([network, subnet])
    entity(document, "resources", "web")["placement"]["network_attachments"].append(
        {"network_ref": "network-other", "subnet_refs": ["subnet-other"]}
    )
    assert not codes(document, mode)["error"]


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("conflict", [False, True])
@pytest.mark.parametrize("collection,identifier", [("resources", "vm"), ("boundaries", "vnet")])
def test_azure_scope_lineage_is_order_independent(
    mode: Mode, reverse: bool, conflict: bool, collection: str, identifier: str
) -> None:
    document = load("providers/azure")
    other = copy.deepcopy(entity(document, "scopes", "sub"))
    other["id"] = "sub-other"
    document["scopes"].append(other)
    target = entity(document, collection, identifier)
    placement = target["placement"] if collection == "resources" else target
    refs = [placement["scope_refs"][0], "sub-other" if conflict else "sub"]
    placement["scope_refs"] = list(reversed(refs)) if reverse else refs
    errors = codes(document, mode)["error"]
    assert ("PLACEMENT_SCOPE_CARDINALITY" in errors) is conflict
    if not conflict:
        assert not errors, errors


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize(
    "scenario", ["conflicting_edges", "matching", "unspecified", "workload", "pool"]
)
def test_concrete_pod_assignments_and_broader_scheduling(
    mode: Mode, host: str, scenario: str
) -> None:
    document = load(f"kubernetes/{host}")
    pod = entity(document, "resources", "pod-a")
    document["relationships"] = [
        edge
        for edge in document["relationships"]
        if not (edge["source_ref"] == "pod-a" and edge["kind"] == "scheduling")
    ]
    if scenario in {"conflicting_edges", "unspecified"}:
        pod["kubernetes"].pop("node_ref")
    targets = {
        "conflicting_edges": ["node-a", "node-b"],
        "matching": ["node-a", "node-a"],
        "unspecified": [],
        "workload": ["node-a", "node-b"],
        "pool": ["pool"],
    }[scenario]
    for number, target in enumerate(targets):
        document["relationships"].append(
            {
                "id": f"schedule-extra-{number}",
                "kind": "scheduling",
                "source_ref": "deploy" if scenario == "workload" else "pod-a",
                "target_ref": target,
            }
        )
    # Edge-only models need updated view selections after removing their original edge.
    ids = {edge["id"] for edge in document["relationships"]}
    for view in document["views"]:
        view["relationship_refs"] = [ref for ref in view["relationship_refs"] if ref in ids]
    errors = codes(document, mode)["error"]
    if scenario == "conflicting_edges":
        assert "K8S_NODE_ASSIGNMENT_CONFLICT" in errors
    else:
        assert not errors, errors


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("pool_id", ["mng", "self-managed"])
@pytest.mark.parametrize(
    "scenario", ["different_subnet", "pool_unspecified", "cluster_unspecified"]
)
def test_eks_nodegroup_compatible_or_unspecified_networks(
    mode: Mode, pool_id: str, scenario: str
) -> None:
    document = load("providers/aws")
    pool = entity(document, "resources", pool_id)
    if scenario == "different_subnet":
        pool["placement"]["network_attachments"] = [
            {"network_ref": "vpc", "subnet_refs": ["data-a"]}
        ]
    elif scenario == "pool_unspecified":
        pool["placement"].pop("network_attachments")
    else:
        entity(document, "resources", "eks")["placement"].pop("network_attachments")
    assert not codes(document, mode)["error"]


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("service_type", ["aws.containers.eks_fargate_profile", "k8s.nodepool"])
def test_eks_vpc_rule_leaves_fargate_and_generic_pools_unchecked(
    mode: Mode, service_type: str
) -> None:
    document = load("providers/aws")
    network = copy.deepcopy(entity(document, "boundaries", "vpc"))
    network["id"] = "vpc-other"
    subnet = copy.deepcopy(entity(document, "boundaries", "app-a"))
    subnet["id"] = "app-other"
    subnet["parent_ref"] = "vpc-other"
    document["boundaries"] += [network, subnet]
    pool = entity(document, "resources", "self-managed")
    pool["service_type"] = service_type
    pool["placement"]["network_attachments"] = [
        {"network_ref": "vpc-other", "subnet_refs": ["app-other"]}
    ]
    assert not codes(document, mode)["error"]


@pytest.mark.parametrize("mode", ["strict", "lenient"])
@pytest.mark.parametrize("refs", [["sub", "proj", "ep"], ["ep", "proj", "sub"]])
def test_huawei_iam_lineage_and_enterprise_scope_stay_separate(mode: Mode, refs: list[str]) -> None:
    document = load("providers/huawei")
    entity(document, "resources", "ecs")["placement"]["scope_refs"] = refs
    assert not codes(document, mode)["error"]


@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_onprem_overlapping_logical_memberships_remain_valid(mode: Mode) -> None:
    document = load("providers/onprem")
    network = copy.deepcopy(entity(document, "boundaries", "net"))
    network["id"] = "network-other"
    document["boundaries"].append(network)
    entity(document, "boundaries", "subnet")["relations"].append(
        {"kind": "network_member_of", "target_ref": "network-other"}
    )
    assert not codes(document, mode)["error"]


def spoke_in_two_regions() -> dict[str, Any]:
    model: dict[str, Any] = json.loads(
        (Path(__file__).parent / "fixtures/references/azure-hub-spoke.json").read_text()
    )
    spoke = next(item for item in model["boundaries"] if item["id"] == "vnet-spoke")
    home = next(item for item in model["boundaries"] if item["id"] == spoke["parent_ref"])
    model["boundaries"].append({**home, "id": "region-other", "name": "other"})
    del spoke["parent_ref"]
    spoke["relations"] = [
        {"kind": "located_in", "target_ref": "region-other"},
        {"kind": "located_in", "target_ref": home["id"]},
    ]
    return model


@pytest.mark.parametrize("reverse", [False, True])
def test_a_boundary_in_two_regions_fails_in_either_order(reverse: bool) -> None:
    model = spoke_in_two_regions()
    spoke = next(item for item in model["boundaries"] if item["id"] == "vnet-spoke")
    if reverse:
        spoke["relations"].reverse()
    assert "BOUNDARY_LOCATION_MULTIPLE" in codes(model)["error"]


def test_a_parent_and_a_location_in_different_regions_fail() -> None:
    model = spoke_in_two_regions()
    spoke = next(item for item in model["boundaries"] if item["id"] == "vnet-spoke")
    spoke["parent_ref"] = spoke["relations"].pop()["target_ref"]
    assert "BOUNDARY_LOCATION_MULTIPLE" in codes(model)["error"]


def test_a_parent_and_a_location_in_one_region_stay_valid() -> None:
    model = spoke_in_two_regions()
    spoke = next(item for item in model["boundaries"] if item["id"] == "vnet-spoke")
    spoke["parent_ref"] = spoke["relations"][1]["target_ref"]
    spoke["relations"].pop(0)
    assert "BOUNDARY_LOCATION_MULTIPLE" not in codes(model)["error"]
    assert codes(model)["error"] == set()


def spanning_boundary(kind: str, reverse: bool) -> dict[str, Any]:
    """A boundary of this kind in the Azure reference's region and in a second one."""
    model: dict[str, Any] = json.loads(
        (Path(__file__).parent / "fixtures/references/azure-hub-spoke.json").read_text()
    )
    home = next(item for item in model["boundaries"] if item["kind"] == "region")
    relations = [
        {"kind": "located_in", "target_ref": home["id"]},
        {"kind": "located_in", "target_ref": "region-other"},
    ]
    model["boundaries"] += [
        {**home, "id": "region-other", "name": "other"},
        {
            "id": "probe",
            "name": "Probe",
            "provider": "azure",
            "kind": kind,
            "relations": relations[::-1] if reverse else relations,
        },
    ]
    return model


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("kind", ["environment", "security_zone", "cluster"])
def test_a_kind_whose_region_nothing_reads_may_span_regions(kind: str, reverse: bool) -> None:
    assert codes(spanning_boundary(kind, reverse))["error"] == set()


@pytest.mark.parametrize("reverse", [False, True])
def test_a_production_environment_across_regions_keeps_its_members(reverse: bool) -> None:
    model = spanning_boundary("environment", reverse)
    member = next(item for item in model["resources"] if item["id"] == "aks-cluster")
    member["placement"]["deployment_context"] = ["probe"]
    assert codes(model)["error"] == set()


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("kind", ["network", "security_group", "zone"])
def test_a_kind_whose_region_is_read_may_not_span_regions(kind: str, reverse: bool) -> None:
    assert "BOUNDARY_LOCATION_MULTIPLE" in codes(spanning_boundary(kind, reverse))["error"]


ECS_LAMBDA_WAF = "providers/aws-ecs-lambda-waf"


def subnets(document: dict[str, Any], count: int) -> list[str]:
    """Add subnets to the fixture's VPC and return their IDs."""
    identifiers = [f"extra-{number}" for number in range(count)]
    for identifier in identifiers:
        document["boundaries"].append(
            {
                "id": identifier,
                "name": identifier,
                "provider": "aws",
                "kind": "subnet",
                "parent_ref": "vpc",
                "relations": [{"kind": "located_in", "target_ref": "az-a"}],
            }
        )
    return identifiers


@pytest.mark.parametrize("target", ["web", "worker", "receipts"])
@pytest.mark.parametrize(("count", "valid"), [(1, True), (16, True), (17, False)])
def test_ecs_and_lambda_list_up_to_sixteen_subnets(target: str, count: int, valid: bool) -> None:
    # AWS states 16 for awsVpcConfiguration and for a function's VpcConfig, and states no minimum.
    document = load(ECS_LAMBDA_WAF)
    attachment = {"network_ref": "vpc", "subnet_refs": subnets(document, count)}
    entity(document, "resources", target)["placement"]["network_attachments"] = [attachment]
    errors = codes(document)["error"]
    assert ("PLACEMENT_SUBNET_COUNT_INVALID" in errors) is not valid, errors
    if valid:
        assert not errors, errors


@pytest.mark.parametrize("target", ["web", "worker", "receipts"])
def test_a_network_attachment_stays_optional_on_ecs_and_lambda(target: str) -> None:
    # A function runs in Lambda's own VPC unless attached, and an unspecified network stays valid.
    document = load(ECS_LAMBDA_WAF)
    placement = entity(document, "resources", target)["placement"]
    del placement["network_attachments"], placement["security_boundaries"]
    assert not codes(document)["error"]


def test_a_workload_may_leave_its_cluster_unspecified() -> None:
    document = load(ECS_LAMBDA_WAF)
    del entity(document, "resources", "web")["placement"]["deployment_context"]
    assert not codes(document)["error"]


def hosted_on(document: dict[str, Any], service_type: str, taxonomy: str) -> None:
    """Add a host of the given type, with no location of its own."""
    provider = service_type.split(".")[0]
    document["resources"].append(
        {
            "id": "probe-host",
            "name": "Host",
            "provider": provider,
            "service_type": service_type,
            "taxonomy": taxonomy,
        }
    )


@pytest.mark.parametrize(
    "service_type", ["onprem.compute.physical_server", "onprem.compute.virtual_machine"]
)
def test_ecs_anywhere_hosts_are_valid_on_a_service_and_not_on_fargate(service_type: str) -> None:
    # ECS Anywhere registers an on-premises server or VM to a cluster, with the EXTERNAL launch type.
    document = load(ECS_LAMBDA_WAF)
    taxonomy = catalog().records[service_type].taxonomy
    hosted_on(document, service_type, taxonomy)
    context = ["cluster", "probe-host"]
    entity(document, "resources", "worker")["placement"]["deployment_context"] = context
    assert not codes(document)["error"]
    entity(document, "resources", "web")["placement"]["deployment_context"] = context
    assert codes(document)["error"] == {"PLACEMENT_HOST_TYPE_INVALID"}


@pytest.mark.parametrize(
    ("base", "target"),
    [(ECS_LAMBDA_WAF, "worker"), (ECS_LAMBDA_WAF, "web"), ("providers/onprem", "vm")],
)
def test_a_draft_host_gets_no_host_rule(base: str, target: str) -> None:
    # An unknown type has no record to judge: strict refuses it once, and lenient keeps a draft.
    document = load(base)
    hosted_on(document, "aws.compute.not_a_service", "compute.vm")
    entity(document, "resources", target)["placement"]["deployment_context"] = ["probe-host"]
    assert codes(document)["error"] == {"CATALOG_TYPE_UNKNOWN"}
    lenient = validate_json(json.dumps(document).encode(), mode="lenient")
    assert lenient.valid and lenient.draft


def test_only_an_ecs_service_may_name_an_ec2_host() -> None:
    document = load(ECS_LAMBDA_WAF)
    worker = entity(document, "resources", "worker")["placement"]["deployment_context"]
    assert worker == ["cluster", "worker-host"] and not codes(document)["error"]
    entity(document, "resources", "web")["placement"]["deployment_context"] = worker
    assert "PLACEMENT_HOST_TYPE_INVALID" in codes(document)["error"]


def test_several_ec2_hosts_are_not_several_clusters() -> None:
    document = load(ECS_LAMBDA_WAF)
    second = copy.deepcopy(entity(document, "resources", "worker-host"))
    second["id"] = "worker-host-2"
    document["resources"].append(second)
    context = entity(document, "resources", "worker")["placement"]["deployment_context"]
    context.append("worker-host-2")
    assert not codes(document)["error"]


@pytest.mark.parametrize(
    "relationship",
    [
        {"source_ref": "waf", "target_ref": "alb", "kind": "attachment"},
        {"source_ref": "alb", "target_ref": "waf", "kind": "attachment"},
        # Repeating one association is still one web ACL.
        {"source_ref": "waf", "target_ref": "alb", "kind": "attachment", "label": "Again"},
    ],
)
def test_a_web_acl_may_attach_to_an_alb_either_way(relationship: dict[str, str]) -> None:
    document = load(ECS_LAMBDA_WAF)
    document["relationships"].append({"id": "probe", **relationship})
    assert not codes(document)["error"]


@pytest.mark.parametrize(
    "relationship",
    [
        # Authors often draw users -> WAF -> service. That claims nothing about what it protects.
        {"source_ref": "waf", "target_ref": "worker-host", "kind": "traffic"},
        {"source_ref": "waf", "target_ref": "worker-host", "kind": "policy"},
        {"source_ref": "bucket", "target_ref": "waf", "kind": "observability"},
    ],
)
def test_only_an_attachment_claims_what_a_web_acl_protects(relationship: dict[str, str]) -> None:
    document = load(ECS_LAMBDA_WAF)
    document["relationships"].append({"id": "probe", **relationship})
    assert not codes(document)["error"]


def test_an_iam_policy_on_a_web_acl_is_not_refused() -> None:
    document = load(ECS_LAMBDA_WAF)
    document["resources"].append(
        {
            "id": "iam",
            "name": "AWS IAM",
            "provider": "aws",
            "service_type": "aws.identity.iam",
            "taxonomy": "identity.access",
        }
    )
    document["relationships"].append(
        {"id": "probe", "source_ref": "iam", "target_ref": "waf", "kind": "policy"}
    )
    assert not codes(document)["error"]


@pytest.mark.parametrize("position", [0, -1])
def test_two_web_acls_are_reported_on_the_resource_in_either_edge_order(position: int) -> None:
    document = load(ECS_LAMBDA_WAF)
    second = copy.deepcopy(entity(document, "resources", "waf"))
    second["id"] = "waf-2"
    document["resources"].append(second)
    edge = {"id": "probe", "source_ref": "waf-2", "target_ref": "alb", "kind": "attachment"}
    edges = document["relationships"]
    edges.insert(0 if position == 0 else len(edges), edge)
    found = validate_json(json.dumps(document).encode()).diagnostics
    [item] = [item for item in found if item.code == "AWS_WAF_ACL_MULTIPLE"]
    index = next(n for n, resource in enumerate(document["resources"]) if resource["id"] == "alb")
    assert item.entity_id == "alb" and item.field == f"/resources/{index}"


def test_one_web_acl_may_protect_several_albs() -> None:
    document = load(ECS_LAMBDA_WAF)
    second = copy.deepcopy(entity(document, "resources", "alb"))
    second["id"] = "alb-2"
    document["resources"].append(second)
    document["relationships"].append(
        {"id": "probe", "source_ref": "waf", "target_ref": "alb-2", "kind": "attachment"}
    )
    assert not codes(document)["error"]


def test_a_web_acl_may_go_undeclared_in_any_region() -> None:
    # A web ACL for CloudFront has no regional home to state, so no region is required of it.
    document = load(ECS_LAMBDA_WAF)
    entity(document, "resources", "waf")["placement"]["location"] = {}
    assert not codes(document)["error"]


def test_a_draft_target_gets_no_web_acl_rule() -> None:
    # An unknown type has no record to judge, and lenient mode keeps it as a disclosed draft.
    document = load(ECS_LAMBDA_WAF)
    document["resources"].append(
        {
            "id": "edge",
            "name": "Amazon CloudFront",
            "provider": "aws",
            "service_type": "aws.edge.cloudfront",
            "taxonomy": "edge.delivery",
        }
    )
    document["relationships"].append(
        {"id": "probe", "source_ref": "waf", "target_ref": "edge", "kind": "attachment"}
    )
    assert codes(document)["error"] == {"CATALOG_TYPE_UNKNOWN"}
    lenient = validate_json(json.dumps(document).encode(), mode="lenient")
    assert lenient.valid and lenient.draft


def test_unrelated_attachment_edges_stay_free() -> None:
    # Only a type that lists its targets is limited, so existing models keep their meaning.
    document = load("providers/aws")
    document["relationships"].append(
        {"id": "probe", "source_ref": "web", "target_ref": "bucket", "kind": "attachment"}
    )
    assert not codes(document)["error"]


def test_a_region_comes_from_the_network_when_no_location_is_declared() -> None:
    def mismatched(document: dict[str, Any]) -> set[str | None]:
        result = validate_json(json.dumps(document).encode())
        return {
            item.entity_id
            for item in result.diagnostics
            if item.code == "PLACEMENT_HOST_REGION_MISMATCH"
        }

    document = load(ECS_LAMBDA_WAF)
    other = {"id": "region-other", "name": "Other", "provider": "aws", "kind": "region"}
    document["boundaries"].append(other)
    entity(document, "resources", "cluster")["placement"]["location"] = {
        "region_ref": "region-other"
    }
    entity(document, "resources", "web")["placement"]["location"] = {}
    assert mismatched(document) == {"web", "worker"}
    # With nothing declared there is nothing to compare, so the region stays unspecified.
    entity(document, "resources", "web")["placement"]["network_attachments"] = []
    assert mismatched(document) == {"worker"}
