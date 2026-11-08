"""Catalog resolution and documented provider/Kubernetes semantics, applied after core checks.

Each dimension stays separate, and a rule fires only on what a model declares: a missing zone,
subnet or Pod placement stays unspecified, while a contradictory one fails. Nothing here infers
reachability, controller availability or a deployed resource.
"""

import re
from collections import defaultdict
from typing import Literal

from .catalog import Catalog, CatalogRecord, catalog
from .diagnostics import Diagnostic
from .models import Architecture, Boundary, Entity, Resource, Scope

Mode = Literal["strict", "lenient"]
LOCATION_FIELDS: dict[str, set[str]] = {
    "none": set(),
    "global": set(),
    "regional": {"region_ref"},
    "zonal": {"region_ref", "zone_ref"},
    "site": {"site_ref"},
    "physical": {"site_ref", "rack_ref"},
    "any": {"region_ref", "zone_ref", "site_ref", "rack_ref"},
}
# The location forms whose region other rules compare. An environment, trust zone or cluster may span
# regions, because nothing reads a region from those.
REGION_READ = {"regional", "zonal"}
# AWS allows one web ACL for each resource. No other type that lists targets states such a rule.
WEB_ACL_TYPES = {"aws.security.waf", "aws.security.waf_cloudfront"}
LOCATED_IN: dict[str, set[str]] = {
    "none": set(),
    "global": set(),
    "regional": {"region"},
    "zonal": {"zone"},
    "site": {"site", "data_center"},
    "physical": {"site", "data_center", "room", "rack"},
    "any": {"region", "zone", "site", "data_center", "room", "rack"},
}
WORKLOADS = {"Deployment", "ReplicaSet", "StatefulSet", "DaemonSet", "Job", "CronJob"}
POD_HOLDERS = WORKLOADS | {"Pod"}
OWNERS: dict[str, set[str]] = {
    "ReplicaSet": {"Deployment"},
    "Job": {"CronJob"},
    "Pod": {"ReplicaSet", "StatefulSet", "DaemonSet", "Job"},
}
REFERENCE_SOURCES: dict[str, set[str]] = {
    "volume_claim_refs": POD_HOLDERS,
    "config_refs": POD_HOLDERS | {"IngressController"},
    "secret_refs": POD_HOLDERS | {"ServiceAccount", "Ingress", "IngressController"},
    "service_account_ref": POD_HOLDERS,
}
NO_TRAFFIC = {
    "Namespace",
    "ConfigMap",
    "Secret",
    "ServiceAccount",
    "StorageClass",
    "NetworkPolicy",
    "PersistentVolumeClaim",
    "PersistentVolume",
    "NodePool",
}
REPLICATED = {"Deployment", "ReplicaSet", "StatefulSet"}
PORTED = POD_HOLDERS | {"Service", "Ingress", "IngressController"}
# AWS exempts only hybrid nodes, which stay generic here. Its Fargate pages imply the cluster VPC
# without stating it, so a Fargate profile stays out.
EKS_CLUSTER_VPC_POOLS = {
    "aws.containers.eks_managed_node_group",
    "aws.containers.eks_self_managed_nodes",
}
ECS_CLUSTER = "aws.containers.ecs_cluster"
QUALIFIED = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9_.-]{0,61}[A-Za-z0-9])?$")
SUBDOMAIN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$")
AZURE_FORBIDDEN = set("<>%&\\?/")


def _kubernetes_label(key: str, value: str) -> bool:
    prefix, separator, name = key.rpartition("/")
    if separator and (len(prefix) > 253 or not SUBDOMAIN.match(prefix)):
        return False
    return bool(QUALIFIED.match(name)) and (not value or bool(QUALIFIED.match(value)))


def _label_valid(syntax: str | None, key: str, value: str) -> bool:
    if syntax == "aws":
        return len(key) <= 128 and len(value) <= 256 and not key.casefold().startswith("aws:")
    if syntax == "azure":
        return not AZURE_FORBIDDEN & set(key) and len(value) <= 256
    if syntax == "gcp":
        return (
            len(key) <= 63
            and len(value) <= 63
            and key[0].isalpha()
            and key == key.lower()
            and value == value.lower()
            and all(char.isalnum() or char in "_-" for char in key + value)
        )
    return True


class Semantics:
    def __init__(self, model: Architecture, mode: Mode) -> None:
        self.model = model
        self.mode = mode
        self.catalog: Catalog = catalog()
        self.diagnostics: list[Diagnostic] = []
        self.entities: dict[str, Entity] = {
            entity.id: entity for entity in [*model.scopes, *model.boundaries, *model.resources]
        }
        self.types: dict[str, CatalogRecord] = {}
        self.unavailable_reported: set[str] = set()
        self.private_use_reported = False
        self.dedicated: dict[str, set[str]] = defaultdict(set)
        self.subnet_types: dict[str, set[str]] = defaultdict(set)
        self.attached: dict[str, set[str]] = defaultdict(set)
        self.web_acls: dict[str, set[str]] = defaultdict(set)
        self.target_regions: dict[str, set[str]] = defaultdict(set)

    def emit(self, code: str, field: str, entity_id: str | None = None) -> None:
        if sum(item.severity == "error" for item in self.diagnostics) >= 100:
            return
        rule = self.catalog.rules[code]
        severity = rule.severity
        if code == "CATALOG_TYPE_UNKNOWN" and self.mode == "lenient":
            severity = "warning"
        self.diagnostics.append(
            Diagnostic(
                severity=severity,
                code=code,
                field=field,
                entity_id=entity_id,
                message=rule.message,
                remedy=rule.remedy,
            )
        )

    def private_use(self, record: CatalogRecord, field: str, entity_id: str) -> None:
        # Once per model, because the limit applies to the whole output rather than to each icon.
        if record.status == "private_use_only" and not self.private_use_reported:
            self.private_use_reported = True
            self.emit("ASSET_PRIVATE_USE_ONLY", field, entity_id)

    def boundary(self, identifier: str | None) -> Boundary | None:
        found = self.entities.get(identifier) if identifier else None
        return found if isinstance(found, Boundary) else None

    def resource(self, identifier: str | None) -> Resource | None:
        found = self.entities.get(identifier) if identifier else None
        return found if isinstance(found, Resource) else None

    def _ancestor(self, boundary: Boundary | None, kinds: set[str]) -> Boundary | None:
        """Follow containment and located_in without treating either as ownership."""
        seen: set[str] = set()
        pending = [boundary] if boundary else []
        while pending:
            current = pending.pop()
            if current.id in seen:
                continue
            seen.add(current.id)
            if current.kind in kinds:
                return current
            targets = [current.parent_ref] + [
                relation.target_ref
                for relation in current.relations
                if relation.kind == "located_in"
            ]
            pending.extend(found for found in map(self.boundary, targets) if found)
        return None

    def region_of(self, boundary: Boundary | None) -> Boundary | None:
        return self._ancestor(boundary, {"region"})

    def spans_regions(self, boundary: Boundary) -> bool:
        """Two regions leave region_of's answer to declaration order, so neither can stand."""
        declared = [
            boundary.parent_ref,
            *(item.target_ref for item in boundary.relations if item.kind == "located_in"),
        ]
        regions = {found.id for ref in declared if (found := self.region_of(self.boundary(ref)))}
        return len(regions) > 1

    def zone_of(self, boundary: Boundary | None) -> Boundary | None:
        return self._ancestor(boundary, {"zone"})

    def declared_region(self, resource: Resource) -> Boundary | None:
        """A resource's region from its location, or else from the network it attaches to."""
        location = resource.placement.location
        found = self.region_of(self.boundary(location.region_ref)) or self.region_of(
            self.boundary(location.zone_ref)
        )
        if found:
            return found
        networks = (item.network_ref for item in resource.placement.network_attachments)
        return next(filter(None, (self.region_of(self.boundary(ref)) for ref in networks)), None)

    def scope_ancestors(self, refs: list[str], kind: str) -> dict[str, Scope]:
        """Resolve each lineage, retaining its most specific scope of the requested kind."""
        found: dict[str, Scope] = {}
        superseded: set[str] = set()
        for identifier in refs:
            current = self.entities.get(identifier)
            seen: set[str] = set()
            matched = False
            while isinstance(current, Scope) and current.id not in seen:
                if current.kind == kind:
                    found[current.id] = current
                    if matched:
                        superseded.add(current.id)
                    matched = True
                seen.add(current.id)
                current = self.entities.get(current.parent_ref) if current.parent_ref else None
        return {
            identifier: scope for identifier, scope in found.items() if identifier not in superseded
        }

    def scope_ancestor(self, refs: list[str], kind: str) -> Scope | None:
        candidates = self.scope_ancestors(refs, kind)
        return next(iter(candidates.values())) if len(candidates) == 1 else None

    def subnet_networks(self, subnet: Boundary) -> set[str]:
        """The networks a subnet belongs to, directly or through its VLAN and VRF."""
        found: set[str] = set()
        seen = {subnet.id}
        pending = [subnet]
        while pending:
            current = pending.pop()
            targets = [current.parent_ref] + [
                relation.target_ref
                for relation in current.relations
                if relation.kind == "network_member_of"
            ]
            for identifier in targets:
                target = self.boundary(identifier)
                if target is None or target.id in seen:
                    continue
                seen.add(target.id)
                if target.kind == "network":
                    found.add(target.id)
                elif target.kind in {"vlan", "vrf"}:
                    pending.append(target)
        return found

    def run(self) -> list[Diagnostic]:
        self.scopes()
        self.boundaries()
        for index, resource in enumerate(self.model.resources):
            self.resource_type(index, resource)
        for index, resource in enumerate(self.model.resources):
            record = self.types.get(resource.id)
            if record:
                self.placement(index, resource, record)
                self.provider_rules(index, resource, record)
            self.labels(index, resource)
        self.dedicated_subnets()
        self.kubernetes()
        self.relationships()
        self.shared_vpc()
        self.huawei_project_regions()
        return self.diagnostics

    def scopes(self) -> None:
        for index, scope in enumerate(self.model.scopes):
            path = f"/scopes/{index}"
            record = self.catalog.group_type(scope.provider, "scope", scope.kind)
            if record is None:
                self.emit("PROVIDER_SCOPE_KIND_INVALID", path + "/kind", scope.id)
                continue
            self.types[scope.id] = record
            parent = self.entities.get(scope.parent_ref) if scope.parent_ref else None
            if isinstance(parent, Scope) and parent.kind not in record.placement.parent_kinds:
                self.emit("SCOPE_PARENT_KIND_INVALID", path + "/parent_ref", scope.id)

    def boundaries(self) -> None:
        for index, boundary in enumerate(self.model.boundaries):
            path = f"/boundaries/{index}"
            record = self.catalog.group_type(boundary.provider, "boundary", boundary.kind)
            if record is None:
                self.emit("PROVIDER_BOUNDARY_KIND_INVALID", path + "/kind", boundary.id)
                continue
            self.types[boundary.id] = record
            self.private_use(record, path + "/kind", boundary.id)
            self.scope_kinds(boundary.scope_refs, record, path + "/scope_refs", boundary.id)
            parent = self.boundary(boundary.parent_ref)
            if parent is not None:
                if parent.kind not in record.placement.parent_kinds:
                    self.emit("BOUNDARY_PARENT_KIND_INVALID", path + "/parent_ref", boundary.id)
                if parent.provider != boundary.provider:
                    self.emit("BOUNDARY_PROVIDER_MISMATCH", path + "/parent_ref", boundary.id)
            located = [item for item in boundary.relations if item.kind == "located_in"]
            for number, relation in enumerate(boundary.relations):
                field = f"{path}/relations/{number}/target_ref"
                target = self.boundary(relation.target_ref)
                if target is None:
                    continue
                if relation.kind == "located_in":
                    if target.kind not in LOCATED_IN[record.placement.location]:
                        self.emit("BOUNDARY_LOCATION_SCOPE_INVALID", field, boundary.id)
                    if target.provider != boundary.provider:
                        self.emit("BOUNDARY_PROVIDER_MISMATCH", field, boundary.id)
                elif relation.kind == "network_member_of":
                    if target.kind not in record.placement.network_member_kinds:
                        self.emit("BOUNDARY_RELATION_KIND_INVALID", field, boundary.id)
                    if target.provider != boundary.provider:
                        self.emit("BOUNDARY_PROVIDER_MISMATCH", field, boundary.id)
                elif relation.kind == "security_member_of" and target.kind not in {
                    "security_zone",
                    "security_group",
                }:
                    self.emit("BOUNDARY_RELATION_KIND_INVALID", field, boundary.id)
            if (record.placement.location == "zonal" and len(located) > 1) or (
                record.placement.location in REGION_READ and self.spans_regions(boundary)
            ):
                self.emit("BOUNDARY_LOCATION_MULTIPLE", path + "/relations", boundary.id)
            if boundary.kind == "subnet":
                limit = record.placement.max_networks
                if limit is not None and len(self.subnet_networks(boundary)) > limit:
                    self.emit("BOUNDARY_NETWORK_COUNT_INVALID", path, boundary.id)
                self.subnet_region(path, boundary)

    def subnet_region(self, path: str, subnet: Boundary) -> None:
        own = self.region_of(subnet)
        for identifier in sorted(self.subnet_networks(subnet)):
            expected = self.region_of(self.boundary(identifier))
            for relation in subnet.relations:
                if relation.kind == "located_in":
                    located = self.region_of(self.boundary(relation.target_ref))
                    if located and expected and located.id != expected.id:
                        self.emit("BOUNDARY_REGION_MISMATCH", path + "/relations", subnet.id)
            if own and expected and own.id != expected.id:
                self.emit("BOUNDARY_REGION_MISMATCH", path, subnet.id)

    def scope_kinds(
        self, refs: list[str], record: CatalogRecord, field: str, entity_id: str
    ) -> None:
        allowed = record.placement.scope_kinds
        for identifier in refs:
            scope = self.entities.get(identifier)
            if isinstance(scope, Scope):
                if allowed is not None and scope.kind not in allowed:
                    self.emit("PLACEMENT_SCOPE_KIND_INVALID", field, entity_id)
        provider = self.catalog.provider_file(self.entities[entity_id].provider)
        for kind in provider.single_scope_kinds if provider else ():
            if len(self.scope_ancestors(refs, kind)) > 1:
                self.emit("PLACEMENT_SCOPE_CARDINALITY", field, entity_id)

    def resource_type(self, index: int, resource: Resource) -> None:
        path = f"/resources/{index}"
        if resource.taxonomy not in self.catalog.taxonomy_ids:
            self.emit("CATALOG_TAXONOMY_UNKNOWN", path + "/taxonomy", resource.id)
        record = self.catalog.records.get(resource.service_type)
        if record is None:
            self.emit("CATALOG_TYPE_UNKNOWN", path + "/service_type", resource.id)
            return
        if record.entity != "resource":
            self.emit("CATALOG_TYPE_ENTITY_INVALID", path + "/service_type", resource.id)
            return
        if resource.provider not in record.providers:
            self.emit("CATALOG_PROVIDER_MISMATCH", path + "/provider", resource.id)
            return
        if resource.taxonomy in self.catalog.taxonomy_ids and resource.taxonomy != record.taxonomy:
            self.emit("CATALOG_TAXONOMY_MISMATCH", path + "/taxonomy", resource.id)
        context = resource.kubernetes
        requires_context = record.id.startswith("k8s.") or "node_group" in record.capabilities
        if (context is None and requires_context) or (
            context is not None and context.kind not in record.kubernetes_kinds
        ):
            self.emit("CATALOG_KUBERNETES_KIND_MISMATCH", path + "/service_type", resource.id)
            return
        self.types[resource.id] = record
        if record.representation.kind == "blocked" and record.id not in self.unavailable_reported:
            self.unavailable_reported.add(record.id)
            self.emit("ICON_UNAVAILABLE", path + "/service_type", resource.id)
        self.private_use(record, path + "/service_type", resource.id)

    def placement(self, index: int, resource: Resource, record: CatalogRecord) -> None:
        path = f"/resources/{index}/placement"
        placement = resource.placement
        rule = record.placement
        location = placement.location
        self.scope_kinds(placement.scope_refs, record, path + "/scope_refs", resource.id)
        for field, identifier in location.model_dump().items():
            if not identifier:
                continue
            if field not in LOCATION_FIELDS[rule.location]:
                self.emit(
                    "PLACEMENT_LOCATION_SCOPE_INVALID", f"{path}/location/{field}", resource.id
                )
            target = self.boundary(identifier)
            if target and target.provider != resource.provider:
                self.emit("BOUNDARY_PROVIDER_MISMATCH", f"{path}/location/{field}", resource.id)
        zone = self.boundary(location.zone_ref)
        region = self.boundary(location.region_ref)
        zone_region = self.region_of(zone)
        if region and zone_region and region.id != zone_region.id:
            self.emit("PLACEMENT_ZONE_REGION_MISMATCH", path + "/location/zone_ref", resource.id)
        own_region = region or zone_region
        rack = self.boundary(location.rack_ref)
        site = self.boundary(location.site_ref)
        if rack and site and self._ancestor(rack, {"site"}) not in (None, site):
            self.emit("PLACEMENT_RACK_SITE_MISMATCH", path + "/location/rack_ref", resource.id)
        self.network(path, resource, record, own_region, zone)
        self.security(path, resource, record, own_region)
        clusters: set[str] = set()
        for number, identifier in enumerate(placement.deployment_context):
            host = self.resource(identifier)
            # An unknown draft type has no record to judge, and lenient mode keeps it as a draft.
            if host is None or host.id not in self.types or not rule.host_types:
                continue
            field = f"{path}/deployment_context/{number}"
            if host.service_type not in rule.host_types:
                self.emit("PLACEMENT_HOST_TYPE_INVALID", field, resource.id)
                continue
            if host.service_type == ECS_CLUSTER:
                clusters.add(host.id)
            own, other = self.declared_region(resource), self.declared_region(host)
            if own and other and own.id != other.id:
                self.emit("PLACEMENT_HOST_REGION_MISMATCH", field, resource.id)
        if len(clusters) > 1:
            self.emit("AWS_ECS_CLUSTER_MULTIPLE", path + "/deployment_context", resource.id)

    def network(
        self,
        path: str,
        resource: Resource,
        record: CatalogRecord,
        own_region: Boundary | None,
        zone: Boundary | None,
    ) -> None:
        rule = record.placement
        attachments = resource.placement.network_attachments
        field = path + "/network_attachments"
        if attachments and rule.network == "none":
            self.emit("PLACEMENT_NETWORK_FORBIDDEN", field, resource.id)
            return
        subnets: list[Boundary] = []
        networks = [attachment.network_ref for attachment in attachments]
        for number, attachment in enumerate(attachments):
            network = self.boundary(attachment.network_ref)
            if network is None:
                continue
            self.attached[resource.id].add(network.id)
            if network.provider != resource.provider:
                self.emit("BOUNDARY_PROVIDER_MISMATCH", f"{field}/{number}", resource.id)
            region = self.region_of(network)
            if own_region and region and own_region.id != region.id:
                self.emit("PLACEMENT_REGION_MISMATCH", f"{field}/{number}/network_ref", resource.id)
            limit = rule.max_subnets_per_network
            if limit is not None and len(attachment.subnet_refs) > limit:
                self.emit("PLACEMENT_SUBNET_COUNT_INVALID", f"{field}/{number}", resource.id)
            if attachment.subnet_refs and rule.network == "network":
                self.emit("PLACEMENT_SUBNET_FORBIDDEN", f"{field}/{number}", resource.id)
                continue
            for count, identifier in enumerate(attachment.subnet_refs):
                subnet = self.boundary(identifier)
                if subnet is None:
                    continue
                subnets.append(subnet)
                self.subnet_types[subnet.id].add(record.id)
                if rule.dedicated_subnet:
                    self.dedicated[subnet.id].add(record.id)
                sub_field = f"{field}/{number}/subnet_refs/{count}"
                homes = self.subnet_networks(subnet)
                if homes and network.id not in homes:
                    self.emit("PLACEMENT_SUBNET_NETWORK_MISMATCH", sub_field, resource.id)
                if subnet.provider != resource.provider:
                    self.emit("BOUNDARY_PROVIDER_MISMATCH", sub_field, resource.id)
                sub_zone = self.zone_of(subnet)
                if zone and sub_zone and zone.id != sub_zone.id:
                    self.emit("PLACEMENT_SUBNET_ZONE_MISMATCH", sub_field, resource.id)
                sub_region = self.region_of(subnet)
                if own_region and sub_region and own_region.id != sub_region.id:
                    self.emit("PLACEMENT_REGION_MISMATCH", sub_field, resource.id)
        if rule.max_networks is not None and len(set(networks)) > rule.max_networks:
            self.emit("PLACEMENT_NETWORK_COUNT_INVALID", field, resource.id)
        if rule.unique_networks and len(networks) != len(set(networks)):
            self.emit("PLACEMENT_NETWORK_COUNT_INVALID", field, resource.id)
        if subnets and (
            len(subnets) < rule.min_subnets
            or (rule.max_subnets is not None and len(subnets) > rule.max_subnets)
        ):
            self.emit("PLACEMENT_SUBNET_COUNT_INVALID", field, resource.id)
        zones = [self.zone_of(subnet) for subnet in subnets]
        known = {item.id for item in zones if item}
        if subnets and all(zones):
            if rule.min_subnet_zones and len(known) < rule.min_subnet_zones:
                self.emit("PLACEMENT_SUBNET_ZONES_INVALID", field, resource.id)
        if rule.single_subnet_zone and len(known) > 1:
            self.emit("PLACEMENT_SUBNET_ZONES_INVALID", field, resource.id)
        # A subnet with no declared zone stays unspecified, and repeating one is still one subnet.
        placed = {
            subnet.id: found.id for subnet, found in zip(subnets, zones, strict=True) if found
        }
        if rule.one_subnet_per_zone and len(set(placed.values())) < len(placed):
            self.emit("PLACEMENT_SUBNET_ZONES_INVALID", field, resource.id)

    def security(
        self, path: str, resource: Resource, record: CatalogRecord, own_region: Boundary | None
    ) -> None:
        for number, identifier in enumerate(resource.placement.security_boundaries):
            group = self.boundary(identifier)
            if group is None or group.kind != "security_group":
                continue
            field = f"{path}/security_boundaries/{number}"
            if group.provider != resource.provider:
                self.emit("BOUNDARY_PROVIDER_MISMATCH", field, resource.id)
                continue
            if record.placement.network == "none":
                self.emit("PLACEMENT_SECURITY_GROUP_FORBIDDEN", field, resource.id)
                continue
            scope = (
                self.types[group.id].placement.security_group_scope
                if group.id in self.types
                else None
            )
            if scope == "network":
                homes = {
                    relation.target_ref
                    for relation in group.relations
                    if relation.kind == "network_member_of"
                }
                if group.parent_ref:
                    homes.add(group.parent_ref)
                networks = {
                    attachment.network_ref for attachment in resource.placement.network_attachments
                }
                if homes and networks and not homes & networks:
                    self.emit("PLACEMENT_SECURITY_GROUP_NETWORK_MISMATCH", field, resource.id)
            elif scope == "region":
                region = self.region_of(group)
                if region and own_region and region.id != own_region.id:
                    self.emit("PLACEMENT_SECURITY_GROUP_REGION_MISMATCH", field, resource.id)

    def dedicated_subnets(self) -> None:
        # A subnet delegated to one service holds only that service. Types that share a native
        # resource type, such as an App Service web app and a function app, share a delegation.
        for index, boundary in enumerate(self.model.boundaries):
            owners = self.dedicated.get(boundary.id)
            services = {self.catalog.records[owner].native_id or owner for owner in owners or ()}
            if owners and (self.subnet_types[boundary.id] - owners or len(services) > 1):
                self.emit(
                    "PLACEMENT_DEDICATED_SUBNET_CONFLICT", f"/boundaries/{index}", boundary.id
                )

    def provider_rules(self, index: int, resource: Resource, record: CatalogRecord) -> None:
        path = f"/resources/{index}/placement"
        refs = resource.placement.scope_refs
        if resource.provider == "azure":
            own_subscription = self.scope_ancestor(refs, "subscription")
            own_group = self.scope_ancestor(refs, "resource_group")
            for number, attachment in enumerate(resource.placement.network_attachments):
                network = self.boundary(attachment.network_ref)
                if network is None:
                    continue
                subscription = self.scope_ancestor(network.scope_refs, "subscription")
                if own_subscription and subscription and own_subscription.id != subscription.id:
                    self.emit(
                        "AZURE_NETWORK_SUBSCRIPTION_MISMATCH",
                        f"{path}/network_attachments/{number}",
                        resource.id,
                    )
                group = self.scope_ancestor(network.scope_refs, "resource_group")
                if (
                    record.placement.same_resource_group_as_network
                    and own_group
                    and group
                    and own_group.id != group.id
                ):
                    self.emit(
                        "AZURE_FIREWALL_RESOURCE_GROUP_MISMATCH",
                        f"{path}/network_attachments/{number}",
                        resource.id,
                    )
        elif resource.provider == "huawei":
            self.huawei(path, resource, record)

    def huawei(self, path: str, resource: Resource, record: CatalogRecord) -> None:
        field = path + "/scope_refs"
        refs = resource.placement.scope_refs
        project = self.scope_ancestor(refs, "iam_project")
        if project and record.placement.iam_authorization == "global":
            self.emit("HUAWEI_GLOBAL_AUTHORIZATION_PROJECT_INVALID", field, resource.id)
        enterprise = self.scope_ancestor(refs, "enterprise_project")
        if enterprise and record.placement.enterprise_project_authorization is False:
            self.emit("HUAWEI_ENTERPRISE_PROJECT_UNSUPPORTED", field, resource.id)
        if project:
            regions = self.project_regions(project)
            own = self.region_of(self.boundary(resource.placement.location.region_ref)) or (
                self.region_of(self.boundary(resource.placement.location.zone_ref))
            )
            if own and regions and own.id not in regions:
                self.emit("HUAWEI_IAM_PROJECT_REGION_MISMATCH", field, resource.id)

    def project_regions(self, project: Scope) -> set[str]:
        lineage: set[str] = set()
        current: Entity | None = project
        while isinstance(current, Scope) and current.id not in lineage:
            lineage.add(current.id)
            current = self.entities.get(current.parent_ref) if current.parent_ref else None
        return {
            boundary.id
            for boundary in self.model.boundaries
            if boundary.kind == "region" and lineage & set(boundary.scope_refs)
        }

    def labels(self, index: int, resource: Resource) -> None:
        field = f"/resources/{index}/properties/labels"
        provider = self.catalog.provider_file(resource.provider)
        for key, value in resource.properties.labels.items():
            valid = (
                _kubernetes_label(key, value)
                if resource.kubernetes
                else _label_valid(provider.label_syntax if provider else None, key, value)
            )
            if not valid:
                self.emit("LABEL_SYNTAX_INVALID", field, resource.id)

    def huawei_project_regions(self) -> None:
        projects: dict[str, set[str]] = defaultdict(set)
        for boundary in self.model.boundaries:
            if boundary.provider == "huawei" and boundary.kind == "region":
                for identifier in boundary.scope_refs:
                    projects[identifier].add(boundary.id)
        for index, scope in enumerate(self.model.scopes):
            if scope.kind == "iam_project" and len(projects[scope.id]) > 1:
                self.emit("HUAWEI_IAM_PROJECT_REGION_MISMATCH", f"/scopes/{index}", scope.id)

    def kubernetes(self) -> None:
        for index, resource in enumerate(self.model.resources):
            context = resource.kubernetes
            if context is None:
                continue
            path = f"/resources/{index}"
            field = path + "/kubernetes"
            kind = context.kind
            cluster = self.resource(context.cluster_ref) if kind != "Cluster" else resource
            mode = (
                self.catalog.cluster_modes.get(cluster.service_type)
                if cluster is not None
                else None
            )
            if kind == "NodePool" and mode and resource.service_type not in mode.node_pool_types:
                self.emit("K8S_NODE_POOL_TYPE_INVALID", path + "/service_type", resource.id)
            if (
                resource.service_type in EKS_CLUSTER_VPC_POOLS
                and cluster is not None
                and cluster.service_type in {"aws.containers.eks", "aws.containers.eks_auto_mode"}
                and self.attached[resource.id]
                and self.attached[cluster.id]
                and self.attached[resource.id] != self.attached[cluster.id]
            ):
                self.emit(
                    "AWS_EKS_NODE_GROUP_NETWORK_MISMATCH",
                    path + "/placement/network_attachments",
                    resource.id,
                )
            if kind == "Node" and mode and mode.abstracted_nodes:
                self.emit("K8S_ABSTRACTED_NODE_DECLARED", field, resource.id)
            if (
                kind == "ControlPlane"
                and mode
                and mode.control_plane == "provider_managed"
                and (
                    resource.placement.network_attachments
                    or any(resource.placement.location.model_dump().values())
                )
            ):
                self.emit("K8S_MANAGED_CONTROL_PLANE_PLACEMENT", path + "/placement", resource.id)
            owner = self.resource(context.owner_ref)
            if owner and owner.kubernetes and owner.kubernetes.kind not in OWNERS.get(kind, set()):
                self.emit("K8S_OWNER_KIND_INVALID", field + "/owner_ref", resource.id)
            for name, kinds in REFERENCE_SOURCES.items():
                if getattr(context, name) and kind not in kinds:
                    self.emit("K8S_REFERENCE_SOURCE_INVALID", f"{field}/{name}", resource.id)
            properties = resource.properties
            if (
                (properties.service_type is not None and kind != "Service")
                or (properties.replicas is not None and kind not in REPLICATED)
                or (properties.ports and kind not in PORTED)
            ):
                self.emit("K8S_PROPERTY_INVALID", path + "/properties", resource.id)
            if properties.service_type == "ExternalName" and context.target_refs:
                self.emit("K8S_SERVICE_TARGET_INVALID", field + "/target_refs", resource.id)
            for number, identifier in enumerate(resource.placement.deployment_context):
                target = self.resource(identifier)
                if (
                    target
                    and target.kubernetes
                    and target.kubernetes.kind in {"Node", "NodePool"}
                    and kind != "Node"
                ):
                    self.emit(
                        "K8S_SCHEDULING_CONTEXT_INVALID",
                        f"{path}/placement/deployment_context/{number}",
                        resource.id,
                    )

    def relationships(self) -> None:
        assignments: dict[str, set[str]] = defaultdict(set)
        for resource in self.model.resources:
            context = resource.kubernetes
            if context and context.kind == "Pod" and context.node_ref:
                assignments[resource.id].add(context.node_ref)
        # Collect before checking so edge order cannot choose a winning assignment.
        for edge in self.model.relationships:
            source, target = self.resource(edge.source_ref), self.resource(edge.target_ref)
            if (
                edge.kind == "scheduling"
                and source
                and source.kubernetes
                and source.kubernetes.kind == "Pod"
                and target
                and target.kubernetes
                and target.kubernetes.kind == "Node"
            ):
                assignments[source.id].add(target.id)
        for index, resource in enumerate(self.model.resources):
            if len(assignments[resource.id]) > 1:
                self.emit(
                    "K8S_NODE_ASSIGNMENT_CONFLICT", f"/resources/{index}/kubernetes", resource.id
                )
        for index, edge in enumerate(self.model.relationships):
            field = f"/relationships/{index}"
            source = self.resource(edge.source_ref)
            target = self.resource(edge.target_ref)
            self.provider_edge(field, edge.kind, edge.id, source, target)
            if source is None or target is None:
                if edge.kind == "traffic":
                    for endpoint in (source, target):
                        if (
                            endpoint
                            and endpoint.kubernetes
                            and endpoint.kubernetes.kind in NO_TRAFFIC
                        ):
                            self.emit("K8S_RELATIONSHIP_INVALID", field, edge.id)
                continue
            self.kubernetes_edge(field, edge.kind, edge.id, source, target)
        # Collected first, so the report names the resource whichever edge came first.
        for index, resource in enumerate(self.model.resources):
            if len(self.web_acls[resource.id]) > 1:
                self.emit("AWS_WAF_ACL_MULTIPLE", f"/resources/{index}", resource.id)
            if len(self.target_regions[resource.id]) > 1:
                code = (
                    "AWS_WAF_RESOURCE_REGION_MISMATCH"
                    if resource.service_type in WEB_ACL_TYPES
                    else "PLACEMENT_ATTACHMENT_REGION_MISMATCH"
                )
                self.emit(code, f"/resources/{index}", resource.id)

    def provider_edge(
        self,
        field: str,
        kind: str,
        identifier: str,
        source: Resource | None,
        target: Resource | None,
    ) -> None:
        if kind != "attachment" or source is None or target is None:
            return
        self.attachment(field, identifier, source, target)
        pair = {source.service_type, target.service_type}
        if pair == {"azure.compute.virtual_machine", "azure.network.network_interface"}:
            first = self.scope_ancestor(source.placement.scope_refs, "subscription")
            second = self.scope_ancestor(target.placement.scope_refs, "subscription")
            if (first and second and first.id != second.id) or self.regions_differ(source, target):
                self.emit("AZURE_NIC_VM_SCOPE_MISMATCH", field, identifier)
        if "huawei.network.eip" in pair and self.regions_differ(source, target):
            self.emit("HUAWEI_EIP_REGION_MISMATCH", field, identifier)

    def attachment(self, field: str, identifier: str, source: Resource, target: Resource) -> None:
        """A type that lists targets attaches only to those. An unknown draft type has no rule yet.

        Either end may list the other, so an edge drawn either way is read once: as owned by the end
        whose record lists the other end's type. It is refused only when neither does and at least
        one end lists targets. The one-owner rule is AWS WAF's alone, and the region rule applies to
        an owner whose record sets `same_region_as_targets`. A global owner, such as a CloudFront
        web ACL, has no region of its own, so only its targets' regions are compared.
        """
        first, second = self.types.get(source.id), self.types.get(target.id)
        if first is None or second is None:
            return
        if target.service_type in first.placement.attachment_targets:
            owner, owned, record = source, target, first
        elif source.service_type in second.placement.attachment_targets:
            owner, owned, record = target, source, second
        else:
            if first.placement.attachment_targets or second.placement.attachment_targets:
                self.emit("PLACEMENT_ATTACHMENT_TARGET_INVALID", field, identifier)
            return
        if record.id in WEB_ACL_TYPES:
            self.web_acls[owned.id].add(owner.id)
        if record.placement.same_region_as_targets:
            declared = (self.declared_region(owner), self.declared_region(owned))
            self.target_regions[owner.id] |= {region.id for region in declared if region}

    def regions_differ(self, first: Resource, second: Resource) -> bool:
        def region(resource: Resource) -> Boundary | None:
            location = resource.placement.location
            return self.region_of(self.boundary(location.region_ref)) or self.region_of(
                self.boundary(location.zone_ref)
            )

        one, other = region(first), region(second)
        return bool(one and other and one.id != other.id)

    def kubernetes_edge(
        self, field: str, kind: str, identifier: str, source: Resource, target: Resource
    ) -> None:
        one, other = source.kubernetes, target.kubernetes
        if one is None and other is None:
            return
        if kind == "traffic":
            if any(side and side.kind in NO_TRAFFIC for side in (one, other)):
                self.emit("K8S_RELATIONSHIP_INVALID", field, identifier)
            return
        if one is None or other is None:
            # A workload may state storage or policy links to a provider service, or to anything
            # else the author supplied, but scheduling and membership are Kubernetes concepts.
            if kind in {"scheduling", "membership"}:
                self.emit("K8S_RELATIONSHIP_INVALID", field, identifier)
            return
        allowed = {
            "scheduling": (POD_HOLDERS, {"Node", "NodePool"}),
            "policy": ({"NetworkPolicy"}, POD_HOLDERS | {"Namespace"}),
            "storage": (
                POD_HOLDERS | {"PersistentVolumeClaim", "PersistentVolume"},
                {"PersistentVolumeClaim", "PersistentVolume", "StorageClass"},
            ),
            "configuration": (
                POD_HOLDERS | {"ServiceAccount", "Ingress", "IngressController"},
                {"ConfigMap", "Secret", "ServiceAccount"},
            ),
        }
        if kind == "ownership":
            if other.kind in OWNERS and one.kind not in OWNERS[other.kind]:
                self.emit("K8S_OWNER_KIND_INVALID", field, identifier)
            elif other.kind not in OWNERS:
                self.emit("K8S_OWNER_KIND_INVALID", field, identifier)
            return
        if kind == "membership":
            valid = (
                other.kind == "Cluster"
                or (other.kind == "Namespace" and one.namespace_ref == target.id)
                or (other.kind == "NodePool" and one.kind == "Node")
            )
            if not valid:
                self.emit("K8S_RELATIONSHIP_INVALID", field, identifier)
        elif kind in allowed:
            sources, targets = allowed[kind]
            if one.kind not in sources or other.kind not in targets:
                self.emit("K8S_RELATIONSHIP_INVALID", field, identifier)
        else:
            return
        first = source.id if one.kind == "Cluster" else one.cluster_ref
        second = target.id if other.kind == "Cluster" else other.cluster_ref
        if first != second or source.provider != target.provider:
            self.emit("K8S_RELATIONSHIP_CROSS_SCOPE", field, identifier)
        namespaced = (
            kind == "configuration" and one.kind != "IngressController" or kind == "policy"
        ) or (kind == "storage" and other.kind == "PersistentVolumeClaim")
        if namespaced and other.namespace_ref and one.namespace_ref != other.namespace_ref:
            self.emit("K8S_RELATIONSHIP_CROSS_SCOPE", field, identifier)
        if kind == "policy" and other.kind == "Namespace" and one.namespace_ref != target.id:
            self.emit("K8S_RELATIONSHIP_CROSS_SCOPE", field, identifier)

    def shared_vpc(self) -> None:
        hosts: dict[str, set[str]] = defaultdict(set)
        for edge in self.model.relationships:
            source = self.entities.get(edge.source_ref)
            target = self.entities.get(edge.target_ref)
            if (
                edge.kind == "attachment"
                and isinstance(source, Scope)
                and isinstance(target, Scope)
                and source.provider == target.provider == "gcp"
                and source.kind == target.kind == "project"
            ):
                hosts[source.id].add(target.id)
        all_hosts = {host for targets in hosts.values() for host in targets}
        for index, scope in enumerate(self.model.scopes):
            if scope.id in hosts and scope.id in all_hosts:
                self.emit("GCP_SHARED_VPC_PROJECT_ROLE_CONFLICT", f"/scopes/{index}", scope.id)
            if len(hosts.get(scope.id, ())) > 1:
                self.emit("GCP_SHARED_VPC_MULTIPLE_HOSTS", f"/scopes/{index}", scope.id)
        for index, resource in enumerate(self.model.resources):
            if resource.provider != "gcp":
                continue
            project = self.scope_ancestor(resource.placement.scope_refs, "project")
            if project is None:
                continue
            for number, attachment in enumerate(resource.placement.network_attachments):
                network = self.boundary(attachment.network_ref)
                owner = self.scope_ancestor(network.scope_refs, "project") if network else None
                if owner and owner.id != project.id and owner.id not in hosts.get(project.id, ()):
                    self.emit(
                        "GCP_SHARED_VPC_ATTACHMENT_REQUIRED",
                        f"/resources/{index}/placement/network_attachments/{number}",
                        resource.id,
                    )


def check(model: Architecture, mode: Mode) -> list[Diagnostic]:
    return Semantics(model, mode).run()
