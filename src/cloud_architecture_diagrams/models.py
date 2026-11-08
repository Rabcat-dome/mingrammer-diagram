"""Closed, strict data contract. Catalog and provider rules live in catalog.py and semantics.py."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

SCHEMA_VERSION = "1.0.0"
MAX_INPUT_BYTES = 1024 * 1024
MAX_DEPTH = 64
MAX_ENTITIES = 1000
Identifier = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9._-]{0,63}$")]
Provider = Literal["aws", "azure", "gcp", "huawei", "onprem", "external"]
Text = Annotated[
    str, StringConstraints(min_length=1, max_length=256, pattern=r"^[^\x00-\x1f\x7f-\x9f]*$")
]
Refs = Annotated[list[Identifier], Field(max_length=1000)]
KubernetesKind = Literal[
    "Cluster",
    "ControlPlane",
    "NodePool",
    "Node",
    "Namespace",
    "Deployment",
    "ReplicaSet",
    "StatefulSet",
    "DaemonSet",
    "Job",
    "CronJob",
    "Pod",
    "Service",
    "Ingress",
    "IngressController",
    "PersistentVolumeClaim",
    "PersistentVolume",
    "StorageClass",
    "ConfigMap",
    "Secret",
    "ServiceAccount",
    "NetworkPolicy",
]
CLUSTER_SCOPED = frozenset(
    {
        "Cluster",
        "ControlPlane",
        "NodePool",
        "Node",
        "Namespace",
        "PersistentVolume",
        "StorageClass",
    }
)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


class Metadata(Contract):
    id: Identifier
    title: Text
    environment: Text
    assumptions: list[Text] = Field(default_factory=list, max_length=64)
    description: Annotated[
        str, StringConstraints(max_length=2048, pattern=r"^[^\x00-\x1f\x7f-\x9f]*$")
    ] = ""


class Entity(Contract):
    id: Identifier
    name: Text
    provider: Provider


class Scope(Entity):
    kind: Literal[
        "account",
        "tenant",
        "subscription",
        "resource_group",
        "organization",
        "folder",
        "project",
        "iam_project",
        "enterprise_project",
        "environment",
    ]
    parent_ref: Identifier | None = None


class BoundaryRelation(Contract):
    kind: Literal["located_in", "network_member_of", "security_member_of", "deployment_member_of"]
    target_ref: Identifier


class Boundary(Entity):
    kind: Literal[
        "region",
        "zone",
        "network",
        "subnet",
        "security_zone",
        "security_group",
        "site",
        "data_center",
        "room",
        "rack",
        "vlan",
        "vrf",
        "cluster",
        "environment",
    ]
    scope_refs: Refs = Field(default_factory=list)
    parent_ref: Identifier | None = None
    relations: list[BoundaryRelation] = Field(default_factory=list, max_length=64)


class Location(Contract):
    region_ref: Identifier | None = None
    zone_ref: Identifier | None = None
    site_ref: Identifier | None = None
    rack_ref: Identifier | None = None


class NetworkAttachment(Contract):
    network_ref: Identifier
    subnet_refs: Refs = Field(default_factory=list)


class Placement(Contract):
    scope_refs: Refs = Field(default_factory=list)
    location: Location = Field(default_factory=Location)
    network_attachments: list[NetworkAttachment] = Field(default_factory=list, max_length=32)
    security_boundaries: Refs = Field(default_factory=list)
    deployment_context: Refs = Field(default_factory=list)


class Port(Contract):
    port: int = Field(ge=1, le=65535)
    target_port: Annotated[int, Field(ge=1, le=65535)] | Identifier | None = None
    protocol: Literal["TCP", "UDP", "SCTP"] = "TCP"


class Properties(Contract):
    replicas: int | None = Field(default=None, ge=0, le=10000)
    labels: dict[
        Text, Annotated[str, StringConstraints(max_length=256, pattern=r"^[^\x00-\x1f\x7f-\x9f]*$")]
    ] = Field(default_factory=dict, max_length=64)
    service_type: Literal["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"] | None = None
    ports: list[Port] = Field(default_factory=list, max_length=32)


class KubernetesContext(Contract):
    kind: KubernetesKind
    cluster_ref: Identifier | None = None
    namespace_ref: Identifier | None = None
    node_pool_ref: Identifier | None = None
    owner_ref: Identifier | None = None
    node_ref: Identifier | None = None
    service_refs: Refs = Field(default_factory=list)
    target_refs: Refs = Field(default_factory=list)
    volume_claim_refs: Refs = Field(default_factory=list)
    volume_ref: Identifier | None = None
    storage_class_ref: Identifier | None = None
    config_refs: Refs = Field(default_factory=list)
    secret_refs: Refs = Field(default_factory=list)
    service_account_ref: Identifier | None = None


class Resource(Entity):
    service_type: Identifier
    taxonomy: Annotated[
        str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$", max_length=64)
    ]
    placement: Placement = Field(default_factory=Placement)
    properties: Properties = Field(default_factory=Properties)
    kubernetes: KubernetesContext | None = None


class Relationship(Contract):
    id: Identifier
    source_ref: Identifier
    target_ref: Identifier
    kind: Literal[
        "traffic",
        "vpn",
        "peering",
        "replication",
        "management",
        "membership",
        "scheduling",
        "policy",
        "storage",
        "configuration",
        "attachment",
        "ownership",
        "dependency",
        "observability",
    ]
    direction: Literal["directed", "undirected"] = "directed"
    label: Text | None = None
    protocol: Text | None = None
    purpose: Text | None = None
    security: Text | None = None


class Band(Contract):
    """One row of a north-to-south view. Its ID is the view's own, not a model entity."""

    id: Identifier
    entity_refs: Annotated[list[Identifier], Field(min_length=1, max_length=1000)]


class View(Contract):
    id: Identifier
    title: Text
    entity_refs: Annotated[list[Identifier], Field(min_length=1, max_length=1000)]
    relationship_refs: Annotated[list[Identifier], Field(max_length=4000)] = Field(
        default_factory=list
    )
    grouping: Literal["none", "provider", "scope", "network", "namespace", "node", "physical"] = (
        "provider"
    )
    direction: Literal["TB", "LR"] = "LR"
    style: Literal["provider", "neutral"] = "provider"
    legend: bool = True
    # D-055: rows from north to south, and the lines drawn level across them. Layout only.
    bands: list[Band] = Field(default_factory=list, max_length=32)
    east_west_refs: Annotated[list[Identifier], Field(max_length=4000)] = Field(
        default_factory=list
    )


class Architecture(Contract):
    schema_version: Literal["1.0.0"]
    metadata: Metadata
    scopes: list[Scope] = Field(default_factory=list, max_length=1000)
    boundaries: list[Boundary] = Field(default_factory=list, max_length=1000)
    resources: list[Resource] = Field(default_factory=list, max_length=1000)
    relationships: list[Relationship] = Field(default_factory=list, max_length=4000)
    views: list[View] = Field(min_length=1, max_length=32)
