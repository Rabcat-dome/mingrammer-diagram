"""M4-01, M4-02, M4-05: T-001..006 and T-017, with the S01 inspect, reject and edit checks."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from render_helpers import (
    FIXTURES,
    bundle_files,
    codes,
    encode,
    graph_of,
    manifest_of,
    render,
    svg_root,
)

from cloud_architecture_diagrams.catalog import catalog
from cloud_architecture_diagrams.render import RenderResult
from cloud_architecture_diagrams.render.checks import SVG
from cloud_architecture_diagrams.render.draw import EDGE_STYLES
from cloud_architecture_diagrams.validation import validate_json

REFERENCES = FIXTURES / "references"
ALL = sorted(path.stem for path in REFERENCES.glob("*.json"))
KUBERNETES = [
    ("aws-three-tier", "eks-namespaces", "eks-nodes"),
    ("azure-hub-spoke", "aks-namespaces", "aks-nodes"),
    ("gcp-shared-vpc", "gke-namespaces", "gke-nodes"),
    ("huawei-web", "cce-namespaces", "cce-nodes"),
    ("onprem-physical-logical", "k8s-namespaces", "k8s-nodes"),
    ("hybrid-five", "k8s-detail", None),
]
EXPECTED_WARNINGS = {"VIEW_EXCLUSIONS", "ASSET_PRIVATE_USE_ONLY"}


def model_of(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((REFERENCES / f"{name}.json").read_text())
    return value


def validated(model: dict[str, Any]) -> Any:
    return validate_json(encode(model))


def errors(model: dict[str, Any]) -> list[str]:
    return [item.code for item in validated(model).diagnostics if item.severity == "error"]


def view_of(model: dict[str, Any], identifier: str) -> dict[str, Any]:
    found: dict[str, Any] = next(item for item in model["views"] if item["id"] == identifier)
    return found


def resource(model: dict[str, Any], identifier: str) -> dict[str, Any]:
    found: dict[str, Any] = next(item for item in model["resources"] if item["id"] == identifier)
    return found


def graph(
    name: str, view: str, output: Path, model: dict[str, Any] | None = None
) -> dict[str, Any]:
    result = render(model or model_of(name), output, view=view)
    assert result.rendered, codes(result)
    return graph_of(result)


def node_of(found: dict[str, Any], identifier: str) -> dict[str, Any]:
    item: dict[str, Any] = next(item for item in found["nodes"] if item["id"] == identifier)
    return item


def chain_of(found: dict[str, Any], identifier: str) -> list[str]:
    """Every group an entity sits in, innermost first."""
    groups = {item["id"]: item for item in found["groups"]}
    parent = node_of(found, identifier)["group"]
    chain: list[str] = []
    while parent is not None:
        chain.append(parent)
        parent = groups[parent]["parent"]
    return chain


def all_ids(model: dict[str, Any]) -> set[str]:
    return {item["id"] for key in ("scopes", "boundaries", "resources") for item in model[key]}


# Every reference, whatever its scenario.


@pytest.mark.parametrize("name", ALL)
def test_a_reference_validates_strictly_and_warns_only_about_what_it_must(name: str) -> None:
    result = validated(model_of(name))
    assert result.valid and result.mode == "strict" and not result.draft
    assert {item.code for item in result.diagnostics} <= EXPECTED_WARNINGS


@pytest.mark.parametrize("name", ALL)
def test_a_reference_states_that_it_is_synthetic(name: str) -> None:
    metadata = model_of(name)["metadata"]
    assert metadata["environment"] == "reference" and metadata["assumptions"]


@pytest.mark.parametrize("name", ALL)
def test_every_entity_and_relationship_reaches_a_view(name: str) -> None:
    model = model_of(name)
    assert all_ids(model) <= {item for view in model["views"] for item in view["entity_refs"]}
    assert {item["id"] for item in model["relationships"]} <= {
        item for view in model["views"] for item in view["relationship_refs"]
    }


@pytest.mark.parametrize("name", ALL)
def test_every_view_draws_exactly_what_it_selects(name: str, tmp_path: Path) -> None:
    model = model_of(name)
    for view in model["views"]:
        result = render(model, tmp_path, view=view["id"])
        assert result.rendered, (view["id"], codes(result))
        found = graph_of(result)
        assert not found["fallbacks"] and not found["draft"]
        assert {item["id"] for item in found["edges"]} == set(view["relationship_refs"])
        drawn = {item["id"] for key in ("nodes", "groups") for item in found[key]}
        assert set(view["entity_refs"]) <= drawn
        # Provider boxes are the only thing added, and their IDs cannot equal a model ID.
        assert not {item for item in drawn - set(view["entity_refs"]) if item in all_ids(model)}
        elements = {item.get("id", "") for item in svg_root(result).iter(f"{{{SVG}}}g")}
        assert {f"edge:{item}" for item in view["relationship_refs"]} <= elements


@pytest.mark.parametrize("name", ALL)
def test_a_left_out_id_is_disclosed_for_every_view(name: str) -> None:
    model = model_of(name)
    result = validated(model)
    relationships = {item["id"] for item in model["relationships"]}
    for view in model["views"]:
        omitted = all_ids(model) - set(view["entity_refs"])
        omitted |= relationships - set(view["relationship_refs"])
        assert set(result.view_exclusions[view["id"]]) == omitted, view["id"]


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("direction", ["TB", "LR"])
def test_the_first_view_draws_in_both_directions(name: str, direction: str, tmp_path: Path) -> None:
    model = model_of(name)
    model["views"][0]["direction"] = direction
    result = render(model, tmp_path)
    assert result.rendered, codes(result)
    assert manifest_of(result)["png"]["scale"] == 1.0
    found = graph_of(result)
    assert found["direction"] == direction
    assert set(found["legend"]) == {item["kind"] for item in found["edges"]}
    assert set(found["legend"]) <= set(EDGE_STYLES)


@pytest.mark.parametrize("name", ALL)
def test_every_view_keeps_the_png_at_full_size(name: str, tmp_path: Path) -> None:
    model = model_of(name)
    for view in model["views"]:
        result = render(model, tmp_path, view=view["id"])
        assert manifest_of(result)["png"]["scale"] == 1.0, view["id"]


# T-001 AWS three-tier.


def test_t001_one_logical_alb_keeps_both_subnets(tmp_path: Path) -> None:
    found = graph("aws-three-tier", "overview", tmp_path)
    balancers = [
        item
        for item in found["nodes"]
        if item["type_id"] == "aws.network.application_load_balancer"
    ]
    assert [item["id"] for item in balancers] == ["alb"]
    assert balancers[0]["memberships"]["subnet"] == ["subnet-public-a", "subnet-public-b"]


def test_t001_requested_services_and_security_groups_stay_visible(tmp_path: Path) -> None:
    found = graph("aws-three-tier", "overview", tmp_path)
    drawn = {item["id"] for key in ("nodes", "groups") for item in found[key]}
    assert {
        "alb",
        "app-instance-a",
        "app-instance-b",
        "database",
        "s3-bucket",
        "cloudwatch",
    } <= drawn
    assert {"sg-alb", "sg-app", "sg-db", "nat-gateway", "internet-gateway"} <= drawn
    # The boxes for AZs are left out here, so each subnet and instance must still say its zone.
    assert "az-a" not in drawn and "location:" in " ".join(node_of(found, "database")["lines"])


def test_t001_edges_keep_direction_and_the_named_labels(tmp_path: Path) -> None:
    found = graph("aws-three-tier", "overview", tmp_path)
    edges = {item["id"]: item for item in found["edges"]}
    assert all(item["directed"] for item in edges.values())
    assert "HTTPS" in edges["t-igw-alb"]["lines"]
    assert "Application to database" in edges["t-app-a-db"]["lines"]
    assert (edges["t-app-a-nat"]["source"], edges["t-app-a-nat"]["target"]) == (
        "app-instance-a",
        "nat-gateway",
    )


def test_t001_rejects_an_instance_whose_subnet_is_in_another_zone() -> None:
    model = model_of("aws-three-tier")
    resource(model, "app-instance-a")["placement"]["location"]["zone_ref"] = "az-b"
    assert errors(model) == ["PLACEMENT_SUBNET_ZONE_MISMATCH"]


def test_t001_edit_renames_a_tier_and_adds_an_instance_keeping_ids(tmp_path: Path) -> None:
    model = model_of("aws-three-tier")
    before = all_ids(model)
    subnet = next(item for item in model["boundaries"] if item["id"] == "subnet-app-a")
    subnet["name"] = "Service subnet A"
    added = copy.deepcopy(resource(model, "app-instance-a")) | {"id": "app-instance-c", "name": "C"}
    model["resources"].append(added)
    view_of(model, "overview")["entity_refs"].append("app-instance-c")
    assert validated(model).valid
    assert all_ids(model) == before | {"app-instance-c"}
    found = graph("aws-three-tier", "overview", tmp_path, model)
    original = graph("aws-three-tier", "overview", tmp_path)
    assert {item["id"] for item in found["edges"]} == {item["id"] for item in original["edges"]}
    assert (
        "Service subnet A"
        in next(item for item in found["groups"] if item["id"] == "subnet-app-a")["lines"]
    )


# T-002 Azure hub and spoke.


def test_t002_ownership_stays_apart_from_network_attachment(tmp_path: Path) -> None:
    network = graph("azure-hub-spoke", "overview", tmp_path)
    assert "subnet-spoke-workload" in chain_of(network, "spoke-vm")
    assert not {item["id"] for item in network["groups"]} & {"subscription", "rg-hub", "rg-spoke"}
    ownership = graph("azure-hub-spoke", "ownership", tmp_path)
    chain = chain_of(ownership, "spoke-vm")
    assert chain[:3] == ["rg-spoke", "subscription", "tenant"]
    assert "subnet-spoke-workload" not in chain and "vnet-spoke" not in chain
    assert "vnet-spoke" in node_of(ownership, "spoke-vm")["memberships"]["network"]


def test_t002_only_the_stated_links_join_hub_and_spoke(tmp_path: Path) -> None:
    found = graph("azure-hub-spoke", "overview", tmp_path)
    edges = {item["id"]: item for item in found["edges"]}
    peering = edges["peering-hub-spoke"]
    assert peering["kind"] == "peering" and not peering["directed"]
    assert (peering["source"], peering["target"]) == ("vnet-hub", "vnet-spoke")
    hub = {
        "vnet-hub",
        "subnet-hub-firewall",
        "subnet-hub-gateway",
        "hub-firewall",
        "hub-vpn-gateway",
    }
    spoke = {"vnet-spoke", "subnet-spoke-workload", "subnet-spoke-aks", "spoke-vm", "spoke-vm-nic"}
    crossing = [
        item["id"]
        for item in found["edges"]
        if {item["source"], item["target"]} & hub and {item["source"], item["target"]} & spoke
    ]
    assert crossing == ["peering-hub-spoke"]


def test_t002_nic_and_security_are_explicit(tmp_path: Path) -> None:
    found = graph("azure-hub-spoke", "overview", tmp_path)
    edge = next(item for item in found["edges"] if item["id"] == "attach-nic-vm")
    assert edge["kind"] == "attachment"
    assert node_of(found, "spoke-vm-nic")["memberships"]["security"] == ["nsg-spoke"]
    assert {"hub-firewall", "hub-vpn-gateway"} <= {item["id"] for item in found["nodes"]}


def test_t002_rejects_an_attachment_to_a_subnet_of_another_vnet() -> None:
    model = model_of("azure-hub-spoke")
    attachment = resource(model, "spoke-vm")["placement"]["network_attachments"][0]
    attachment["subnet_refs"] = ["subnet-hub-firewall"]
    assert errors(model) == ["PLACEMENT_SUBNET_NETWORK_MISMATCH"]


def test_t002_edit_adds_a_second_spoke_with_only_its_own_connections(tmp_path: Path) -> None:
    model = model_of("azure-hub-spoke")
    original = copy.deepcopy(model["relationships"])
    vnet = copy.deepcopy(next(item for item in model["boundaries"] if item["id"] == "vnet-spoke"))
    vnet |= {"id": "vnet-spoke-2", "name": "Spoke 2 VNet"}
    model["boundaries"].append(vnet)
    model["relationships"].append(
        {
            "id": "peering-hub-spoke-2",
            "source_ref": "vnet-hub",
            "target_ref": "vnet-spoke-2",
            "kind": "peering",
            "direction": "undirected",
            "label": "VNet peering",
        }
    )
    view = view_of(model, "overview")
    view["entity_refs"].append("vnet-spoke-2")
    view["relationship_refs"].append("peering-hub-spoke-2")
    assert validated(model).valid
    assert model["relationships"][: len(original)] == original
    found = graph("azure-hub-spoke", "overview", tmp_path, model)
    assert [item["id"] for item in found["edges"] if "vnet-spoke-2" in item.values()] == [
        "peering-hub-spoke-2"
    ]


# T-003 GCP Shared VPC.


def test_t003_the_vpc_is_global_and_its_subnets_regional() -> None:
    model = model_of("gcp-shared-vpc")
    boundaries = {item["id"]: item for item in model["boundaries"]}
    vpc = boundaries["vpc-shared"]
    assert vpc["kind"] == "network" and vpc.get("parent_ref") is None
    regions = {
        relation["target_ref"]
        for item in boundaries.values()
        if item["kind"] == "subnet"
        for relation in item["relations"]
        if relation["kind"] == "located_in"
    }
    assert regions == {"region-asia-southeast1", "region-asia-southeast2"}


def test_t003_ownership_is_not_flattened_into_the_network(tmp_path: Path) -> None:
    found = graph("gcp-shared-vpc", "projects", tmp_path)
    assert "project-app-service" in chain_of(found, "vm-web-a")
    assert "project-network-host" not in chain_of(found, "vm-web-a")
    assert node_of(found, "vpc-shared")["group"] == "project-network-host"
    assert "vpc-shared" in node_of(found, "vm-web-a")["memberships"]["network"]
    edge = next(item for item in found["edges"] if item["id"] == "shared-vpc-attachment")
    assert (edge["source"], edge["target"]) == ("project-app-service", "project-network-host")


def test_t003_rejects_a_workload_zone_outside_its_subnet_region() -> None:
    model = model_of("gcp-shared-vpc")
    attachment = resource(model, "vm-web-a")["placement"]["network_attachments"][0]
    attachment["subnet_refs"] = ["subnet-gke"]
    assert errors(model) == ["PLACEMENT_REGION_MISMATCH"]


def test_t003_edit_moves_a_workload_to_another_zone_keeping_its_id(tmp_path: Path) -> None:
    model = model_of("gcp-shared-vpc")
    resource(model, "vm-web-a")["placement"]["location"]["zone_ref"] = "zone-asia-southeast1-b"
    assert validated(model).valid
    before = graph("gcp-shared-vpc", "overview", tmp_path)
    after = graph("gcp-shared-vpc", "overview", tmp_path, model)
    assert {item["id"] for item in after["nodes"]} == {item["id"] for item in before["nodes"]}
    assert node_of(after, "vm-web-a")["memberships"]["subnet"] == ["subnet-web"]


# T-004 Huawei web application.

HUAWEI_NATIVE = {
    "elb-web",
    "ecs-web",
    "rds-web",
    "obs-web",
    "eip-egress",
    "nat-egress",
    "cloud-eye",
    "lts",
    "api-gateway",
    "functiongraph",
    "iam",
    "vpn",
}


def test_t004_each_required_service_uses_its_approved_huawei_icon(tmp_path: Path) -> None:
    seen: set[str] = set()
    for view in ("overview", "services"):
        for node in graph("huawei-web", view, tmp_path)["nodes"]:
            if node["id"] in HUAWEI_NATIVE:
                assert node["icon"]["source"] == "custom_asset" and not node["fallback"]
                asset = catalog().records[node["type_id"]].representation.asset
                assert asset and node["icon"]["reference"] == asset
                assert catalog().packs[node["icon"]["pack"]].status == "private_use_only"
                seen.add(node["id"])
    assert seen == HUAWEI_NATIVE


def test_t004_a_bundle_carries_the_private_use_limit(tmp_path: Path) -> None:
    result = render(model_of("huawei-web"), tmp_path, view="overview")
    assert "ASSET_PRIVATE_USE_ONLY" in {item.code for item in result.diagnostics}
    rights = json.dumps(manifest_of(result)["rights"])
    assert "private" in rights.lower()
    assert b"private personal use only" in bundle_files(result)["diagram.svg"]


def test_t004_a_box_does_not_imply_a_scope_the_service_lacks(tmp_path: Path) -> None:
    # OBS is scoped to the account, and its region sits inside the IAM project's box.
    found = graph("huawei-web", "overview", tmp_path)
    assert "project-ap-southeast-2" in chain_of(found, "ecs-web")
    chain = chain_of(found, "obs-web")
    assert "project-ap-southeast-2" not in chain and "huawei-account" in chain
    assert "location:" in " ".join(node_of(found, "obs-web")["lines"])


def test_t004_the_egress_path_is_only_what_the_model_states(tmp_path: Path) -> None:
    found = graph("huawei-web", "overview", tmp_path)
    assert {(item["source"], item["target"]) for item in found["edges"]} == {
        ("elb-web", "ecs-web"),
        ("ecs-web", "rds-web"),
        ("ecs-web", "nat-egress"),
        ("nat-egress", "eip-egress"),
    }


def test_t004_edit_adds_cce_with_its_detail_view_keeping_the_web_ids(tmp_path: Path) -> None:
    full = model_of("huawei-web")
    detail = {
        identifier
        for view in ("cce-namespaces", "cce-nodes")
        for identifier in view_of(full, view)["entity_refs"]
    }
    web = copy.deepcopy(full)
    web["resources"] = [item for item in web["resources"] if item["id"] not in detail]
    links = [
        item
        for item in web["relationships"]
        if item["source_ref"] not in detail and item["target_ref"] not in detail
    ]
    web["relationships"] = links
    kept = {item["id"] for item in links}
    web["views"] = [item for item in web["views"] if not item["id"].startswith("cce-")]
    for view in web["views"]:
        view["entity_refs"] = [item for item in view["entity_refs"] if item not in detail]
        view["relationship_refs"] = [item for item in view["relationship_refs"] if item in kept]
    assert validated(web).valid and validated(full).valid
    before = graph("huawei-web", "overview", tmp_path, web)
    after = graph("huawei-web", "overview", tmp_path, full)
    # The edit adds the compact cluster to the web view, and changes nothing that was there.
    assert after["edges"] == before["edges"]
    shared = {item["id"]: item for item in before["nodes"]}
    added = {item["id"] for item in after["nodes"]} - set(shared)
    assert added == {"cce-cluster"}
    for node in after["nodes"]:
        if node["id"] in shared:
            assert node == shared[node["id"]], node["id"]
    groups = {item["id"]: item for item in before["groups"]}
    assert {item["id"] for item in after["groups"]} - set(groups) == {"cce-cluster"}
    assert [item for item in after["groups"] if item["id"] in groups] == before["groups"]
    # The detail view it brings draws from the same model, with its own IDs.
    detail_view = graph("huawei-web", "cce-namespaces", tmp_path)
    assert {"cce-cluster", "ns-web"} <= {item["id"] for item in detail_view["groups"]}


# T-005 On-premises physical and logical views.


def test_t005_physical_and_logical_nest_differently_for_one_identity(tmp_path: Path) -> None:
    physical = graph("onprem-physical-logical", "physical", tmp_path)
    logical = graph("onprem-physical-logical", "logical", tmp_path)
    assert chain_of(physical, "physical-server-1")[:4] == ["rack-b", "room-a", "dc-1", "site-main"]
    chain = chain_of(logical, "physical-server-1")
    assert "subnet-app" in chain and "rack-b" not in chain
    assert (
        node_of(physical, "physical-server-1")["type_id"]
        == node_of(logical, "physical-server-1")["type_id"]
    )
    assert "location:" in " ".join(node_of(logical, "physical-server-1")["lines"])


def test_t005_memberships_that_overlap_all_stay_on_the_node(tmp_path: Path) -> None:
    found = graph("onprem-physical-logical", "logical", tmp_path)
    firewall = node_of(found, "firewall-1")["memberships"]
    assert set(firewall["network"]) == {"net-prod", "net-mgmt"}
    assert set(firewall["subnet"]) == {"subnet-app", "subnet-data", "subnet-mgmt"}
    assert set(firewall["security"]) == {"zone-app", "zone-data", "zone-mgmt"}
    vm = node_of(found, "vm-1")["memberships"]
    assert set(vm["network"]) == {"net-prod", "net-mgmt"} and vm["deployment"] == ["hypervisor-1"]


def test_t005_every_requested_kind_of_device_is_in_the_model() -> None:
    types = {item["service_type"] for item in model_of("onprem-physical-logical")["resources"]}
    assert {
        "onprem.network.router",
        "onprem.network.l2_switch",
        "onprem.network.l3_switch",
        "onprem.security.firewall",
        "onprem.compute.hypervisor",
        "onprem.compute.physical_server",
        "onprem.compute.virtual_machine",
        "onprem.containers.kubernetes_cluster",
        "onprem.database.database",
        "onprem.storage.nas",
        "onprem.storage.san",
        "onprem.identity.identity_service",
        "onprem.operations.backup_system",
        "onprem.operations.monitoring",
    } <= types


def test_t005_rejects_a_subnet_paired_with_a_network_it_reaches_only_elsewhere() -> None:
    # This subnet reaches its network only through a VLAN and a VRF, so one hop would not see it.
    model = model_of("onprem-physical-logical")
    resource(model, "nas-1")["placement"]["network_attachments"] = [
        {"network_ref": "net-mgmt", "subnet_refs": ["subnet-data"]}
    ]
    assert errors(model) == ["PLACEMENT_SUBNET_NETWORK_MISMATCH"]


def test_t005_edit_moves_a_server_between_racks_keeping_its_logical_memberships(
    tmp_path: Path,
) -> None:
    model = model_of("onprem-physical-logical")
    resource(model, "physical-server-1")["placement"]["location"]["rack_ref"] = "rack-c"
    assert validated(model).valid
    before = node_of(graph("onprem-physical-logical", "logical", tmp_path), "physical-server-1")
    after_graph = graph("onprem-physical-logical", "logical", tmp_path, model)
    after = node_of(after_graph, "physical-server-1")
    assert after["group"] == before["group"]
    for dimension in ("network", "subnet", "security"):
        assert after["memberships"][dimension] == before["memberships"][dimension]
    moved = graph("onprem-physical-logical", "physical", tmp_path, model)
    assert chain_of(moved, "physical-server-1")[0] == "rack-c"


# T-006 Five-environment hybrid.

ENVIRONMENTS = {"aws", "azure", "gcp", "huawei", "onprem"}
LINKS = {
    "link-aws-direct-connect": "peering",
    "link-azure-vpn": "vpn",
    "link-gcp-interconnect": "peering",
    "link-huawei-direct-connect": "peering",
}


def test_t006_the_overview_shows_all_five_environments(tmp_path: Path) -> None:
    found = graph("hybrid-five", "overview", tmp_path)
    assert {item["provider"] for item in found["nodes"]} == ENVIRONMENTS
    boxes = {item["provider"] for item in found["groups"] if item["entity"] == "provider"}
    assert boxes == ENVIRONMENTS


def test_t006_links_are_the_stated_ones_and_never_a_mesh(tmp_path: Path) -> None:
    found = graph("hybrid-five", "connectivity", tmp_path)
    assert {item["id"]: item["kind"] for item in found["edges"]} == LINKS
    providers = {item["id"]: item["provider"] for item in found["nodes"]}
    for edge in found["edges"]:
        # Every stated link joins on-premises to one cloud, so no cloud pair appears connected.
        assert "onprem" in {providers[edge["source"]], providers[edge["target"]]}
        assert not edge["directed"] and edge["lines"]


def test_t006_the_legend_tells_connectivity_from_data_flow(tmp_path: Path) -> None:
    found = graph("hybrid-five", "overview", tmp_path)
    assert {"peering", "vpn", "traffic", "replication"} == set(found["legend"])
    for edge in found["edges"]:
        if edge["id"] in LINKS:
            assert edge["kind"] == LINKS[edge["id"]]
        else:
            assert edge["kind"] in {"traffic", "replication"} and edge["directed"] and edge["lines"]


def test_t006_each_trust_boundary_is_labeled_and_holds_its_workloads(tmp_path: Path) -> None:
    found = graph("hybrid-five", "overview", tmp_path)
    zones = {
        item["id"]: item for item in found["groups"] if item["boundary_kind"] == "security_zone"
    }
    assert {item["provider"] for item in zones.values()} == ENVIRONMENTS
    assert all("Security zone" in " ".join(item["lines"]) for item in zones.values())
    assert "aws-trust-zone" in chain_of(found, "aws-web")
    cluster = next(item for item in found["groups"] if item["id"] == "k8s-cluster")
    assert cluster["parent"] == "onprem-trust-zone"


def test_t006_the_cluster_stays_compact_in_the_overview(tmp_path: Path) -> None:
    found = graph("hybrid-five", "overview", tmp_path)
    assert "k8s-cluster" in {item["id"] for item in found["groups"]}
    assert not any(item["type_id"].startswith("k8s.") for item in found["nodes"])
    excluded = validated(model_of("hybrid-five")).view_exclusions["overview"]
    assert {"k8s-pod-orders-1", "k8s-namespace-orders"} <= set(excluded)


def test_t006_edit_adds_a_stated_link_without_changing_the_others(tmp_path: Path) -> None:
    full = model_of("hybrid-five")
    link = next(
        item for item in full["relationships"] if item["id"] == "link-huawei-direct-connect"
    )
    without = copy.deepcopy(full)
    without["relationships"].remove(link)
    for view in without["views"]:
        view["relationship_refs"] = [
            item for item in view["relationship_refs"] if item != link["id"]
        ]
    assert validated(without).valid
    edges = graph("hybrid-five", "connectivity", tmp_path, without)["edges"]
    assert link["id"] not in {item["id"] for item in edges}
    # Adding it back is the stated edit, and only that one edge may appear.
    after = graph("hybrid-five", "connectivity", tmp_path, full)["edges"]
    assert [item for item in after if item["id"] != link["id"]] == edges


# T-017 Kubernetes detail across the five hosting environments.


@pytest.mark.parametrize(("name", "logical", "_nodes"), KUBERNETES)
def test_t017_namespace_view_draws_the_service_and_storage_paths(
    name: str, logical: str, _nodes: str | None, tmp_path: Path
) -> None:
    found = graph(name, logical, tmp_path)
    kinds = {item["id"]: item["type_id"] for item in found["nodes"]}
    pairs = {
        (kinds.get(item["source"]), kinds.get(item["target"])): item["kind"]
        for item in found["edges"]
    }
    assert pairs[("k8s.ingress", "k8s.service")] == "traffic"
    assert pairs[("k8s.service", "k8s.pod")] == "traffic"
    assert ("k8s.deployment", "k8s.replicaset") in pairs
    assert ("k8s.replicaset", "k8s.pod") in pairs
    if name != "hybrid-five":
        assert pairs[("k8s.persistentvolumeclaim", "k8s.persistentvolume")] == "storage"


@pytest.mark.parametrize(("name", "logical", "nodes"), [item for item in KUBERNETES if item[2]])
def test_t017_namespace_and_placement_stay_separate_for_one_pod(
    name: str, logical: str, nodes: str, tmp_path: Path
) -> None:
    model = model_of(name)
    pods = [item for item in model["resources"] if item["service_type"] == "k8s.pod"]
    assert len(pods) >= 2
    namespace_view = graph(name, logical, tmp_path)
    node_view = graph(name, nodes, tmp_path)
    for pod in pods:
        context = pod["kubernetes"]
        assert context["namespace_ref"] in chain_of(namespace_view, pod["id"])
        assert context["node_ref"] not in chain_of(namespace_view, pod["id"])
        assert "node:" in " ".join(node_of(namespace_view, pod["id"])["lines"])
        assert context["node_ref"] in chain_of(node_view, pod["id"])
        assert "namespace:" in " ".join(node_of(node_view, pod["id"])["lines"])
        assert (
            node_of(namespace_view, pod["id"])["type_id"]
            == node_of(node_view, pod["id"])["type_id"]
        )


@pytest.mark.parametrize(("name", "logical", "_nodes"), KUBERNETES)
def test_t017_a_view_invents_no_placement(
    name: str, logical: str, _nodes: str | None, tmp_path: Path
) -> None:
    model = model_of(name)
    for pod in model["resources"]:
        if pod["service_type"] == "k8s.pod":
            pod["kubernetes"].pop("node_ref", None)
    found = graph(name, logical, tmp_path, model)
    for pod in model["resources"]:
        if pod["service_type"] == "k8s.pod" and pod["id"] in view_of(model, logical)["entity_refs"]:
            assert "node: unspecified" in node_of(found, pod["id"])["lines"]


@pytest.mark.parametrize(("name", "logical", "_nodes"), KUBERNETES)
def test_t017_an_edit_keeps_every_id_and_link_it_does_not_touch(
    name: str, logical: str, _nodes: str | None, tmp_path: Path
) -> None:
    model = model_of(name)
    before = graph(name, logical, tmp_path)
    pod = next(item for item in model["resources"] if item["service_type"] == "k8s.pod")
    added = copy.deepcopy(pod) | {"id": "edit-added-pod", "name": "edit-added-pod"}
    model["resources"].append(added)
    deployment = next(
        item for item in model["resources"] if item["service_type"] == "k8s.deployment"
    )
    deployment["name"] = "renamed-deployment"
    view_of(model, logical)["entity_refs"].append("edit-added-pod")
    assert validated(model).valid
    after = graph(name, logical, tmp_path, model)
    assert after["edges"] == before["edges"]
    earlier = {item["id"]: item for item in before["nodes"]}
    assert {item["id"] for item in after["nodes"]} == set(earlier) | {"edit-added-pod"}
    for node in after["nodes"]:
        if node["id"] not in {"edit-added-pod", deployment["id"]}:
            assert node == earlier[node["id"]], node["id"]
    assert "renamed-deployment" in node_of(after, deployment["id"])["lines"]
    assert node_of(after, deployment["id"])["type_id"] == earlier[deployment["id"]]["type_id"]


def other_cluster(model: dict[str, Any], cluster: str, namespace: str) -> None:
    """A second cluster and namespace, so that a reference can wrongly cross between them."""
    twin = copy.deepcopy(resource(model, cluster)) | {"id": "other-cluster", "name": "Other"}
    space = copy.deepcopy(resource(model, namespace)) | {"id": "other-namespace", "name": "other"}
    space["kubernetes"]["cluster_ref"] = "other-cluster"
    model["resources"] += [twin, space]


@pytest.mark.parametrize(("name", "_logical", "_nodes"), KUBERNETES)
def test_t017_rejects_a_namespace_from_another_cluster(
    name: str, _logical: str, _nodes: str | None
) -> None:
    model = model_of(name)
    pod = next(item for item in model["resources"] if item["service_type"] == "k8s.pod")
    cluster = pod["kubernetes"]["cluster_ref"]
    other_cluster(model, cluster, pod["kubernetes"]["namespace_ref"])
    assert validated(model).valid
    pod["kubernetes"]["namespace_ref"] = "other-namespace"
    assert "K8S_NAMESPACE_MISMATCH" in errors(model)


@pytest.mark.parametrize(("name", "_logical", "_nodes"), KUBERNETES)
def test_t017_a_secret_cannot_carry_a_value(name: str, _logical: str, _nodes: str | None) -> None:
    model = model_of(name)
    secrets = [item for item in model["resources"] if item["service_type"] == "k8s.secret"]
    if name != "hybrid-five":
        assert secrets
    for secret in secrets:
        changed = copy.deepcopy(model)
        resource(changed, secret["id"])["kubernetes"]["data"] = {"password": "not-a-real-value"}
        assert errors(changed) == ["SCHEMA_FIELD_INVALID"]
        resource(changed, secret["id"])["kubernetes"].pop("data")
        resource(changed, secret["id"])["value"] = "not-a-real-value"
        assert errors(changed) == ["SCHEMA_FIELD_INVALID"]


@pytest.mark.parametrize(("name", "_logical", "_nodes"), KUBERNETES)
def test_t017_the_cluster_keeps_its_id_and_provider_across_views(
    name: str, _logical: str, _nodes: str | None, tmp_path: Path
) -> None:
    model = model_of(name)
    clusters = [
        item
        for item in model["resources"]
        if (item.get("kubernetes") or {}).get("kind") == "Cluster"
    ]
    assert len(clusters) == 1
    cluster = clusters[0]
    views = [item["id"] for item in model["views"] if cluster["id"] in item["entity_refs"]]
    assert len(views) >= 2
    for view in views:
        found = graph(name, view, tmp_path)
        same = [
            item
            for key in ("nodes", "groups")
            for item in found[key]
            if item["id"] == cluster["id"]
        ]
        assert same and all(item["provider"] == cluster["provider"] for item in same)


# M4-03 English and Thai labels.

THAI = {
    "app-instance-a": "เซิร์ฟเวอร์แอปพลิเคชัน เอ",
    "app-instance-b": "เซิร์ฟเวอร์แอปพลิเคชัน บี",
    "database": "ฐานข้อมูลหลัก",
    "alb": "ตัวกระจายโหลดแอปพลิเคชัน",
    "s3-bucket": "ที่เก็บไฟล์",
    "cloudwatch": "ระบบเฝ้าระวัง",
}


def thai_model() -> dict[str, Any]:
    model = model_of("aws-three-tier")
    model["metadata"]["title"] = "เว็บแอปพลิเคชันสามชั้นบน AWS"
    for identifier, name in THAI.items():
        resource(model, identifier)["name"] = name
    return model


def test_thai_labels_render_strictly_with_the_same_ids(tmp_path: Path) -> None:
    result: RenderResult = render(thai_model(), tmp_path, view="overview")
    assert result.rendered and not result.draft, codes(result)
    english = graph("aws-three-tier", "overview", tmp_path)
    found = graph_of(result)
    assert [item["id"] for item in found["nodes"]] == [item["id"] for item in english["nodes"]]
    text = " ".join(item.text or "" for item in svg_root(result).iter(f"{{{SVG}}}text"))
    assert "ฐานข้อมูลหลัก" in text and "ระบบเฝ้าระวัง" in text
    assert "Noto Sans Thai" in json.dumps(manifest_of(result)["fonts"])


def foreign_zone_model() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "metadata": {"id": "zone", "title": "Zone", "environment": "test", "assumptions": ["x"]},
        "scopes": [],
        "boundaries": [
            {
                "id": "trust",
                "name": "Shared trust zone",
                "provider": "external",
                "kind": "security_zone",
            }
        ],
        "resources": [
            {
                "id": "app",
                "name": "Application",
                "provider": "gcp",
                "service_type": "gcp.compute.compute_engine",
                "taxonomy": "compute.vm",
                "placement": {"security_boundaries": ["trust"]},
            }
        ],
        "relationships": [],
        "views": [{"id": "overview", "title": "Overview", "entity_refs": ["trust", "app"]}],
    }


def test_a_foreign_security_zone_keeps_a_resource_in_its_own_provider(tmp_path: Path) -> None:
    model = foreign_zone_model()
    assert errors(model) == []
    found = graph("", "overview", tmp_path, model)
    assert chain_of(found, "app") == ["_provider.gcp"]
    # The membership is a declared fact, so leaving the box must not lose it.
    assert "security: Shared trust zone" in " ".join(node_of(found, "app")["lines"])
    assert next(item for item in found["groups"] if item["id"] == "trust")["parent"] == (
        "_provider.external"
    )


def test_a_foreign_security_zone_keeps_a_boundary_in_its_own_provider(tmp_path: Path) -> None:
    model = foreign_zone_model()
    model["boundaries"].append(
        {
            "id": "vpc",
            "name": "Network",
            "provider": "gcp",
            "kind": "network",
            "relations": [{"kind": "security_member_of", "target_ref": "trust"}],
        }
    )
    model["views"][0]["entity_refs"].append("vpc")
    found = graph("", "overview", tmp_path, model)
    assert (
        next(item for item in found["groups"] if item["id"] == "vpc")["parent"] == "_provider.gcp"
    )


@pytest.mark.parametrize("name", ALL)
def test_every_provider_box_holds_only_that_provider(name: str, tmp_path: Path) -> None:
    model = model_of(name)
    views = [view for view in model["views"] if view.get("grouping", "provider") == "provider"]
    assert views or name == "onprem-physical-logical"
    for view in views:
        found = graph(name, view["id"], tmp_path / view["id"], model)
        groups = {item["id"]: item for item in found["groups"]}
        for item in [*found["nodes"], *found["groups"]]:
            at = item["group"] if "group" in item else item["parent"]
            while at is not None:
                assert groups[at]["provider"] == item["provider"], (item["id"], at)
                at = groups[at]["parent"]


def scheduled_pod(target: str = "aks-node-1") -> dict[str, Any]:
    model = model_of("azure-hub-spoke")
    del resource(model, "web-pod-1")["kubernetes"]["node_ref"]
    model["relationships"].append(
        {"id": "pod-to-node", "source_ref": "web-pod-1", "target_ref": target, "kind": "scheduling"}
    )
    view_of(model, "aks-nodes")["relationship_refs"].append("pod-to-node")
    return model


def test_a_scheduling_edge_alone_places_a_pod_on_its_node(tmp_path: Path) -> None:
    model = scheduled_pod()
    assert errors(model) == []
    found = graph("", "aks-nodes", tmp_path / "nodes", model)
    assert chain_of(found, "web-pod-1")[0] == "aks-node-1"
    assert "node: unspecified" not in node_of(found, "web-pod-1")["lines"]
    assert "pod-to-node" in {edge["id"] for edge in found["edges"]}
    # The namespace view does not nest by Node, so it states the same fact in a note.
    other = graph("", "aks-namespaces", tmp_path / "namespaces", model)
    assert "node: node-1" in node_of(other, "web-pod-1")["lines"]


def test_a_scheduling_edge_to_a_node_pool_leaves_the_node_unspecified(tmp_path: Path) -> None:
    model = scheduled_pod("aks-node-pool")
    assert errors(model) == []
    found = graph("", "aks-nodes", tmp_path, model)
    assert "node: unspecified" in node_of(found, "web-pod-1")["lines"]


def test_a_pod_with_no_node_and_no_edge_stays_unspecified(tmp_path: Path) -> None:
    model = model_of("azure-hub-spoke")
    del resource(model, "web-pod-1")["kubernetes"]["node_ref"]
    found = graph("", "aks-nodes", tmp_path, model)
    assert "node: unspecified" in node_of(found, "web-pod-1")["lines"]
    assert "aks-node-1" not in chain_of(found, "web-pod-1")
