"""Versioned taxonomy, provider and Kubernetes catalogs, rule text and bounded discovery."""

import json
from functools import cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .models import KubernetesKind, Provider

DATA = Path(__file__).resolve().parent / "catalog_data"
PROVIDER_FILES = ("aws", "azure", "gcp", "huawei", "onprem", "common", "kubernetes")
MAX_RESULTS = 200
TypeId = Annotated[
    str,
    StringConstraints(
        pattern=r"^(aws|azure|gcp|huawei|onprem|external|k8s|common)\.[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?$",
        max_length=64,
    ),
]
Location = Literal["none", "global", "regional", "zonal", "site", "physical", "any"]
Capability = Literal[
    "api_management",
    "backup",
    "block_storage",
    "container_cluster",
    "database",
    "external_party",
    "file_storage",
    "firewall",
    "gateway",
    "hypervisor",
    "identity",
    "kubernetes_config",
    "kubernetes_identity",
    "kubernetes_policy",
    "kubernetes_storage",
    "kubernetes_traffic",
    "kubernetes_workload",
    "load_balancing",
    "location",
    "logging",
    "monitoring",
    "nat",
    "network",
    "node_group",
    "object_storage",
    "physical_compute",
    "policy",
    "private_connectivity",
    "public_ip",
    "routing",
    "scope",
    "security_boundary",
    "serverless",
    "subnet",
    "switching",
    "virtual_compute",
    "vpn",
]


def _read(name: str) -> str:
    return (DATA / (name + ".json")).read_text(encoding="utf-8")


class CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class PlacementRule(CatalogModel):
    """Absence means unspecified, so these constrain only what a model actually declares."""

    location: Location = "any"
    network: Literal["none", "network", "subnet"] = "none"
    scope_kinds: tuple[str, ...] | None = None
    parent_kinds: tuple[str, ...] = ()
    network_member_kinds: tuple[str, ...] = ()
    security_group_scope: Literal["network", "region"] | None = None
    min_subnets: int = 0
    max_subnets: int | None = None
    max_networks: int | None = None
    max_subnets_per_network: int | None = None
    min_subnet_zones: int = 0
    single_subnet_zone: bool = False
    unique_networks: bool = False
    dedicated_subnet: bool = False
    same_resource_group_as_network: bool = False
    host_types: tuple[str, ...] = ()
    iam_authorization: Literal["project", "global"] | None = None
    enterprise_project_authorization: bool | None = None


class Representation(CatalogModel):
    kind: Literal["native_class", "custom_asset", "labeled_boundary", "labeled_node", "blocked"]
    label: str | None = None
    class_path: str | None = None
    pack: str | None = None
    asset: str | None = None
    blocker: str | None = None
    source_candidate: str | None = None


class CatalogRecord(CatalogModel):
    id: TypeId
    providers: tuple[Provider, ...] = Field(min_length=1)
    entity: Literal["resource", "boundary", "scope"]
    kind: str | None = None
    display_name: str = Field(min_length=1, max_length=128)
    taxonomy: str
    capabilities: tuple[Capability, ...] = Field(min_length=1)
    placement: PlacementRule = PlacementRule()
    representation: Representation
    status: Literal["supported", "semantics_only", "private_use_only"]
    sources: tuple[str, ...] = Field(min_length=1)
    native_id: str | None = None
    native_aliases: tuple[str, ...] = ()
    kubernetes_kinds: tuple[KubernetesKind, ...] = ()
    api_version: str | None = None
    namespaced: bool | None = None


class TaxonomyEntry(CatalogModel):
    id: str
    meaning: str


class TaxonomyFile(CatalogModel):
    catalog_version: str
    taxonomy: tuple[TaxonomyEntry, ...]
    lenient_fallback: Representation


class ClusterMode(CatalogModel):
    control_plane: Literal["provider_managed", "user_managed"]
    node_pool_types: tuple[str, ...]
    abstracted_nodes: bool


class ProviderFile(CatalogModel):
    catalog_version: str
    provider: Provider | None = None
    platform: Literal["common", "kubernetes"] | None = None
    single_scope_kinds: tuple[str, ...] = ()
    label_syntax: Literal["aws", "azure", "gcp"] | None = None
    label_source: str | None = None
    verified_release: str | None = None
    verified_release_source: str | None = None
    cluster_modes: dict[str, ClusterMode] = Field(default_factory=dict)
    records: tuple[CatalogRecord, ...]


class Rule(CatalogModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]+$")
    severity: Literal["error", "warning"]
    message: str
    remedy: str
    sources: tuple[str, ...] = Field(min_length=1)


class RulesFile(CatalogModel):
    catalog_version: str
    rules: tuple[Rule, ...]


class Terms(CatalogModel):
    url: str
    summary: str
    sha256: str | None = None


class Candidate(CatalogModel):
    url: str
    note: str
    sha256: str | None = None


class Pack(CatalogModel):
    id: str
    status: Literal["approved", "blocked", "private_use_only"]
    distribution: Literal["bundled", "dependency", "none"]
    publisher: str
    license: str | None
    rights_basis: Literal[
        "license", "publisher_permission", "publisher_invitation", "owner_risk_acceptance", "none"
    ]
    owner_decision: str | None = None
    source_url: str
    source_version: str
    retrieved: str
    terms: tuple[Terms, ...] = Field(min_length=1)
    conditions: tuple[str, ...] = Field(min_length=1)
    attribution: str | None
    redistribution_evidence: str | None
    source_commit: str | None = None
    source_tag_object: str | None = None
    source_git_blob: str | None = None
    source_sha256: str | None = None
    blocker: str | None = None
    blocker_reason: str | None = None
    blocker_scope: Literal["public_distribution", "icon_coverage"] | None = None
    candidates: tuple[Candidate, ...] = ()


class AssetOriginal(CatalogModel):
    name: str
    sha256: str
    digest_of: Literal["canonical_stencil_xml", "decoded_png"]
    entry_index: int | None = None


class DerivedFile(CatalogModel):
    path: str
    sha256: str
    width: int | None = None
    height: int | None = None


class AssetDerived(CatalogModel):
    svg: DerivedFile | None
    png: DerivedFile


class Asset(CatalogModel):
    id: str
    pack: str
    concept: str
    required_label: str
    composition: str
    symbols: tuple[str, ...] = Field(min_length=1)
    title_token: str | None = None
    original: tuple[AssetOriginal, ...] = Field(min_length=1)
    derived: AssetDerived
    changes: str


class AssetManifest(CatalogModel):
    catalog_version: str
    packs: tuple[Pack, ...]
    assets: tuple[Asset, ...]


class Catalog:
    def __init__(self) -> None:
        taxonomy = TaxonomyFile.model_validate_json(_read("taxonomy"))
        self.version = taxonomy.catalog_version
        self.taxonomy = taxonomy.taxonomy
        self.taxonomy_ids = frozenset(entry.id for entry in self.taxonomy)
        self.fallback = taxonomy.lenient_fallback
        self.files = {
            name: ProviderFile.model_validate_json(_read(name)) for name in PROVIDER_FILES
        }
        self.records: dict[str, CatalogRecord] = {
            record.id: record for file in self.files.values() for record in file.records
        }
        self.rules = {
            rule.code: rule for rule in RulesFile.model_validate_json(_read("rules")).rules
        }
        self.cluster_modes = self.files["kubernetes"].cluster_modes
        inventory: dict[str, dict[str, list[str]]] = json.loads(_read("inventory"))["required"]
        self.inventory = inventory
        self.manifest = AssetManifest.model_validate_json(_read("assets"))
        self.packs = {pack.id: pack for pack in self.manifest.packs}
        self.assets = {asset.id: asset for asset in self.manifest.assets}
        self._groups: dict[tuple[str, str, str], CatalogRecord] = {
            (provider, record.entity, record.kind): record
            for record in self.records.values()
            if record.kind is not None
            for provider in record.providers
        }

    def group_type(
        self, provider: str, entity: Literal["scope", "boundary"], kind: str
    ) -> CatalogRecord | None:
        return self._groups.get((provider, entity, kind))

    def provider_file(self, provider: str) -> ProviderFile | None:
        return self.files.get(provider)

    def release_blockers(self) -> list[dict[str, object]]:
        return [
            {
                "id": pack.blocker,
                "pack": pack.id,
                "scope": pack.blocker_scope,
                "reason": pack.blocker_reason,
                "affected_types": sorted(
                    record.id
                    for record in self.records.values()
                    if self._uses_pack(record, pack.id)
                ),
            }
            for pack in self.manifest.packs
            if pack.blocker
        ]

    def _uses_pack(self, record: CatalogRecord, pack: str) -> bool:
        item = record.representation
        return item.pack == pack or (
            item.asset in self.assets and self.assets[item.asset].pack == pack
        )

    def search(
        self,
        *,
        provider: str | None = None,
        taxonomy: str | None = None,
        entity: str | None = None,
        query: str | None = None,
        type_id: str | None = None,
        kubernetes: bool = False,
        limit: int = 50,
    ) -> dict[str, object]:
        needle = (query or "").casefold()
        found = [
            record
            for record in self.records.values()
            if (provider is None or provider in record.providers)
            and (taxonomy is None or record.taxonomy == taxonomy)
            and (entity is None or record.entity == entity)
            and (type_id is None or record.id == type_id)
            and (not kubernetes or bool(record.kubernetes_kinds))
            and (
                not needle
                or needle in record.id.casefold()
                or needle in record.display_name.casefold()
                or needle in (record.native_id or "").casefold()
            )
        ]
        found.sort(key=lambda record: record.id)
        bounded = max(1, min(limit, MAX_RESULTS))
        return {
            "catalog_version": self.version,
            "total": len(found),
            "returned": min(len(found), bounded),
            "truncated": len(found) > bounded,
            "records": [
                record.model_dump(mode="json", exclude_none=True, exclude_defaults=True)
                for record in found[:bounded]
            ],
        }


@cache
def catalog() -> Catalog:
    return Catalog()
