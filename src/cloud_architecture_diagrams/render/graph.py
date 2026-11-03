"""View-to-graph mapping (M3-01). Selection is explicit and every drawing choice is catalog data.

Graphviz clusters form a tree, but ownership, location, network, security and deployment do not.
Each entity nests under the first selected container its view's grouping allows, and every other
selected membership stays visible as a text note, so nesting never hides or invents a dimension.
"""

import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict

from ..catalog import CatalogRecord, catalog
from ..models import Architecture, Boundary, Entity, Resource, Scope, View
from ..validation import Mode
from .errors import RenderFailure
from .limits import Limits

LABEL_WIDTH = 20
WORD_OVERRUN = 3
EDGE_WIDTH = 28
TITLE_WIDTH = 110
ZERO_WIDTH = {"Mn", "Me", "Cf"}
PROVIDER_LABELS = {
    "aws": "AWS",
    "azure": "Microsoft Azure",
    "gcp": "Google Cloud",
    "huawei": "Huawei Cloud",
    "onprem": "On-premises",
    "external": "External",
}
NETWORK_KINDS = {"network", "subnet", "vlan", "vrf"}
PHYSICAL_KINDS = {"region", "zone", "site", "data_center", "room", "rack"}
# Which membership dimensions may become nesting in each grouping. The rest stay notes.
NESTING: dict[str, frozenset[str]] = {
    "none": frozenset(),
    "provider": frozenset(
        {
            "namespace",
            "node pool",
            "cluster",
            "parent",
            "subnet",
            "network",
            "location",
            "deployment",
            "scope",
            "security",
        }
    ),
    "scope": frozenset({"parent", "scope"}),
    "network": frozenset({"parent", "subnet", "network"}),
    "namespace": frozenset({"namespace", "node pool", "cluster"}),
    "node": frozenset({"node", "node pool", "cluster"}),
    "physical": frozenset({"parent", "location"}),
}
# Namespace and worker placement are separate facts, so each stays visible in every grouping. So do
# a declared subnet and location, which lets a view leave out their boxes and keep the fact. A region
# is the exception: it applies to nearly everything, so it is noted only when the view selects it.
ALWAYS_NOTED = {"namespace", "node", "subnet", "location"}


class GraphModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GraphIcon(GraphModel):
    source: Literal["native_class", "custom_asset"]
    reference: str
    pack: str


class GraphNode(GraphModel):
    id: str
    entity: Literal["scope", "boundary", "resource"]
    provider: str
    type_id: str
    drawing: Literal["icon", "labeled_node", "labeled_box"]
    lines: tuple[str, ...]
    icon: GraphIcon | None = None
    group: str | None = None
    fallback: bool = False
    memberships: dict[str, tuple[str, ...]] = {}


class GraphGroup(GraphModel):
    id: str
    entity: Literal["scope", "boundary", "resource", "provider"]
    provider: str
    type_id: str | None
    boundary_kind: str | None = None
    scope_kind: str | None = None
    lines: tuple[str, ...]
    parent: str | None = None
    memberships: dict[str, tuple[str, ...]] = {}


class GraphEdge(GraphModel):
    id: str
    source: str
    target: str
    kind: str
    directed: bool
    lines: tuple[str, ...]


class Fallback(GraphModel):
    entity_id: str
    provider: str
    service_type: str
    label: str


class RenderGraph(GraphModel):
    """Normalized and host-independent, so M4 can compare it across machines and edits."""

    view_id: str
    grouping: str
    direction: Literal["TB", "LR"]
    style: Literal["provider", "neutral"]
    legend: tuple[str, ...]
    draft: bool
    title_lines: tuple[str, ...]
    notice_lines: tuple[str, ...]
    groups: tuple[GraphGroup, ...]
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    fallbacks: tuple[Fallback, ...]

    def packs(self) -> list[str]:
        return sorted({node.icon.pack for node in self.nodes if node.icon})


def visible_width(text: str) -> int:
    return sum(unicodedata.category(char) not in ZERO_WIDTH for char in text)


def _split_word(word: str, width: int) -> list[str]:
    # A combining mark takes no width, so it can never start a line apart from its base.
    pieces: list[str] = []
    current = ""
    used = 0
    for char in word:
        visible = unicodedata.category(char) not in ZERO_WIDTH
        if visible and used >= width:
            pieces.append(current)
            current, used = "", 0
        current += char
        used += visible
    return [*pieces, current]


def wrap(text: str, width: int) -> list[str]:
    """Thai has no spaces between words, so a long word breaks by width rather than overflowing.

    A word just past the width stays whole, as Kubernetes kind names do, and only that one line runs
    wider. The node spacing in `draw` leaves room for it.
    """
    lines: list[str] = []
    current = ""
    for word in text.split(" "):
        whole = visible_width(word) <= width + WORD_OVERRUN
        for piece in [word] if whole else _split_word(word, width):
            candidate = f"{current} {piece}" if current else piece
            if visible_width(candidate) <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = piece
    return [*lines, current]


def _memberships(entity: Entity) -> list[tuple[str, list[str]]]:
    """Every declared dimension, most specific first; the order decides which one nests."""
    if isinstance(entity, Scope):
        return [("parent", [entity.parent_ref] if entity.parent_ref else [])]
    if isinstance(entity, Boundary):

        def related(kind: str) -> list[str]:
            return [item.target_ref for item in entity.relations if item.kind == kind]

        return [
            ("parent", [entity.parent_ref] if entity.parent_ref else []),
            ("network", related("network_member_of")),
            ("location", related("located_in")),
            ("deployment", related("deployment_member_of")),
            ("scope", list(entity.scope_refs)),
            ("security", related("security_member_of")),
        ]
    assert isinstance(entity, Resource)
    placement = entity.placement
    location = placement.location
    found: list[tuple[str, list[str]]] = []
    if context := entity.kubernetes:
        for dimension, target in [
            ("namespace", context.namespace_ref),
            ("node", context.node_ref),
            ("node pool", context.node_pool_ref),
            ("cluster", context.cluster_ref),
        ]:
            found.append((dimension, [target] if target else []))
    return [
        *found,
        (
            "subnet",
            [ref for item in placement.network_attachments for ref in item.subnet_refs],
        ),
        ("network", [item.network_ref for item in placement.network_attachments]),
        *[
            ("location", [ref])
            for ref in (
                location.rack_ref,
                location.zone_ref,
                location.site_ref,
                location.region_ref,
            )
            if ref
        ],
        ("deployment", list(placement.deployment_context)),
        ("scope", list(placement.scope_refs)),
        ("security", list(placement.security_boundaries)),
    ]


class Mapper:
    def __init__(self, model: Architecture, view: View, mode: Mode, limits: Limits) -> None:
        self.model = model
        self.view = view
        self.mode = mode
        self.limits = limits
        self.entities: dict[str, Entity] = {
            entity.id: entity for entity in [*model.scopes, *model.boundaries, *model.resources]
        }
        self.selected = [self.entities[identifier] for identifier in view.entity_refs]
        self.selected_ids = set(view.entity_refs)
        # An unknown type draws as a fallback node, so it can never hold other entities.
        self.group_ids = {
            entity.id
            for entity in self.selected
            if self._is_group(entity) and self._record(entity) is not None
        }
        self.parents: dict[str, str | None] = {}

    def _kubernetes_kind(self, entity: Entity) -> str | None:
        if isinstance(entity, Resource) and entity.kubernetes:
            return entity.kubernetes.kind
        return None

    def _is_group(self, entity: Entity) -> bool:
        grouping = self.view.grouping
        kind = self._kubernetes_kind(entity)
        if grouping == "provider":
            return isinstance(entity, (Scope, Boundary)) or kind in {
                "Cluster",
                "NodePool",
                "Namespace",
            }
        if grouping == "scope":
            return isinstance(entity, Scope)
        if grouping == "network":
            return isinstance(entity, Boundary) and entity.kind in NETWORK_KINDS
        if grouping == "physical":
            return isinstance(entity, Boundary) and entity.kind in PHYSICAL_KINDS
        if grouping == "namespace":
            return kind in {"Cluster", "NodePool", "Namespace"}
        if grouping == "node":
            return kind in {"Cluster", "NodePool", "Node"}
        return False

    def _record(self, entity: Entity) -> CatalogRecord | None:
        data = catalog()
        if isinstance(entity, Resource):
            return data.records.get(entity.service_type)
        if isinstance(entity, Scope):
            return data.group_type(entity.provider, "scope", entity.kind)
        assert isinstance(entity, Boundary)
        return data.group_type(entity.provider, "boundary", entity.kind)

    def _chain(self, identifier: str | None) -> list[str]:
        found: list[str] = []
        while identifier is not None:
            found.append(identifier)
            identifier = self.parents.get(identifier)
        return found

    def _common_ancestor(self, identifiers: list[str]) -> str | None:
        chains = [self._chain(identifier) for identifier in identifiers]
        return next((item for item in chains[0] if all(item in c for c in chains[1:])), None)

    def _container(self, entity: Entity) -> str | None:
        allowed = NESTING[self.view.grouping]
        for dimension, targets in _memberships(entity):
            if dimension not in allowed:
                continue
            # Dimensions are acyclic one at a time, not together, so a chain must not loop back.
            found = [
                target
                for target in targets
                if target in self.group_ids
                and target != entity.id
                and entity.id not in self._chain(target)
                and not self._implies_another_scope(entity, target)
            ]
            if len(found) == 1:
                return found[0]
            if len(found) > 1 and entity.id not in self.group_ids:
                if common := self._common_ancestor(found):
                    return common
        return None

    def _implies_another_scope(self, entity: Entity, target: str) -> bool:
        """A box reads as ownership, so an entity must not sit inside a scope it does not declare.

        A regional service scoped to an account can have its region inside a project's box. It then
        nests by its account, and the region stays a note.
        """
        if isinstance(entity, Resource):
            scope_refs = entity.placement.scope_refs
        elif isinstance(entity, Boundary):
            scope_refs = entity.scope_refs
        else:
            return False
        if not scope_refs:
            return False
        allowed: set[str] = set()
        for declared in scope_refs:
            current: str | None = declared
            while current is not None and current not in allowed:
                allowed.add(current)
                scope = self.entities[current]
                current = scope.parent_ref if isinstance(scope, Scope) else None
        return any(
            isinstance(self.entities[group], Scope) and group not in allowed
            for group in self._chain(target)
            if group in self.entities
        )

    def _nest_groups(self) -> None:
        """A group's place depends on where its candidates sit, so repeat until none moves.

        Working in ID order means the order a view lists its entities cannot choose the tree. Every
        move keeps the tree free of loops, so stopping at the bound still leaves a valid one.
        """
        groups = sorted(
            (entity for entity in self.selected if entity.id in self.group_ids),
            key=lambda entity: entity.id,
        )
        for _ in range(len(groups) + 1):
            moved = False
            for entity in groups:
                parent = self._container(entity)
                if parent != self.parents.get(entity.id):
                    self.parents[entity.id] = parent
                    moved = True
            if not moved:
                return

    def _notes(self, entity: Entity, parent: str | None) -> list[str]:
        chain = self._chain(parent)
        lines: list[str] = []
        for dimension, targets in _memberships(entity):
            shown = [
                target
                for target in targets
                if target not in chain
                and target != entity.id
                and (
                    target in self.selected_ids
                    or (dimension in ALWAYS_NOTED and not self._is_region(target))
                )
            ]
            if shown:
                names = ", ".join(self.entities[target].name for target in shown)
                lines += wrap(f"{dimension}: {names}", LABEL_WIDTH)
        kind = self._kubernetes_kind(entity)
        if kind == "Pod" and isinstance(entity, Resource) and entity.kubernetes:
            # A Pod with no declared Node is unspecified, whatever group it sits beside.
            if entity.kubernetes.node_ref is None:
                lines.append("node: unspecified")
        return lines

    def _is_region(self, identifier: str) -> bool:
        entity = self.entities[identifier]
        return isinstance(entity, Boundary) and entity.kind == "region"

    def _declared(self, entity: Entity) -> dict[str, tuple[str, ...]]:
        return {name: tuple(targets) for name, targets in _memberships(entity) if targets}

    def _icon(self, record: CatalogRecord) -> GraphIcon | None:
        item = record.representation
        if item.kind == "native_class" and item.class_path and item.pack:
            return GraphIcon(source="native_class", reference=item.class_path, pack=item.pack)
        if item.asset:
            asset = catalog().assets.get(item.asset)
            if asset is None:
                raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/representation", record.id)
            return GraphIcon(source="custom_asset", reference=asset.id, pack=asset.pack)
        return None

    def _service_label(self, entity: Entity, record: CatalogRecord) -> list[str]:
        label = record.representation.label or record.display_name
        # The catalog's label is required on assets, so a similar name does not replace it.
        return [] if label == entity.name else wrap(label, LABEL_WIDTH)

    def _fallback(self, entity: Resource) -> tuple[GraphNode, Fallback]:
        data = catalog().fallback
        assert data.class_path and data.pack and data.label
        parent = self.parents.get(entity.id)
        lines = [
            *wrap(entity.name, LABEL_WIDTH),
            *wrap(data.label, LABEL_WIDTH),
            *wrap(f"{entity.provider}: {entity.service_type}", LABEL_WIDTH),
            *self._notes(entity, parent),
        ]
        node = GraphNode(
            id=entity.id,
            entity="resource",
            provider=entity.provider,
            type_id=entity.service_type,
            drawing="icon",
            lines=tuple(lines),
            icon=GraphIcon(source="native_class", reference=data.class_path, pack=data.pack),
            group=parent,
            fallback=True,
            memberships=self._declared(entity),
        )
        return node, Fallback(
            entity_id=entity.id,
            provider=entity.provider,
            service_type=entity.service_type,
            label=entity.name,
        )

    def build(self) -> RenderGraph:
        view = self.view
        limits = self.limits
        if (
            len(view.entity_refs) > limits.view_entities
            or len(view.relationship_refs) > limits.view_relationships
        ):
            raise RenderFailure("RENDER_VIEW_TOO_LARGE", "/views", view.id)
        records: dict[str, CatalogRecord] = {}
        for entity in self.selected:
            record = self._record(entity)
            if record is None:
                # Validation admits an unknown type only for a lenient resource.
                if not (isinstance(entity, Resource) and self.mode == "lenient"):
                    raise RenderFailure("RENDER_TYPE_UNRESOLVED", "/views", entity.id)
                continue
            if record.representation.kind == "blocked":
                raise RenderFailure("RENDER_TYPE_BLOCKED", "/views", entity.id)
            records[entity.id] = record
        self._nest_groups()
        self._check_depth()
        for entity in self.selected:
            if entity.id not in self.group_ids:
                self.parents[entity.id] = self._container(entity)
        groups: list[GraphGroup] = []
        nodes: list[GraphNode] = []
        fallbacks: list[Fallback] = []
        for entity in self.selected:
            record = records.get(entity.id)
            if record is None:
                assert isinstance(entity, Resource)
                node, fallback = self._fallback(entity)
                nodes.append(node)
                fallbacks.append(fallback)
            elif entity.id in self.group_ids:
                self._add_group(entity, record, groups, nodes)
            else:
                nodes.append(self._node(entity, record))
        if view.grouping == "provider":
            groups, nodes = self._under_providers(groups, nodes)
        relationships = {edge.id: edge for edge in self.model.relationships}
        edges = []
        for identifier in view.relationship_refs:
            edge = relationships[identifier]
            lines = [
                line
                for text in (edge.label, edge.protocol, edge.purpose, edge.security)
                if text
                for line in wrap(text, EDGE_WIDTH)
            ]
            edges.append(
                GraphEdge(
                    id=edge.id,
                    source=edge.source_ref,
                    target=edge.target_ref,
                    kind=edge.kind,
                    directed=edge.direction == "directed",
                    lines=tuple(lines),
                )
            )
        return RenderGraph(
            view_id=view.id,
            grouping=view.grouping,
            direction=view.direction,
            style=view.style,
            legend=tuple(sorted({edge.kind for edge in edges})) if view.legend else (),
            draft=self.mode == "lenient",
            title_lines=tuple(self._title(fallbacks)),
            notice_lines=tuple(self._notices(nodes)),
            groups=tuple(groups),
            nodes=tuple(nodes),
            edges=tuple(edges),
            fallbacks=tuple(fallbacks),
        )

    def _title(self, fallbacks: list[Fallback]) -> list[str]:
        metadata = self.model.metadata
        lines = [
            *wrap(metadata.title, TITLE_WIDTH),
            *wrap(f"{self.view.title} ({metadata.environment})", TITLE_WIDTH),
        ]
        if self.mode == "lenient":
            lines.append("DRAFT: lenient validation, not a final diagram")
        if fallbacks:
            lines.append(f"DRAFT: {len(fallbacks)} unknown type(s) drawn with a generic symbol")
        return lines

    def _notices(self, nodes: list[GraphNode]) -> list[str]:
        """An image can leave its bundle, so it carries the terms of the icons bundled here."""
        data = catalog()
        lines: list[str] = []
        for identifier in sorted({node.icon.pack for node in nodes if node.icon}):
            pack = data.packs[identifier]
            if pack.distribution != "bundled" or not pack.attribution:
                continue
            if pack.status == "private_use_only":
                lines += wrap(
                    "Contains icons for private personal use only; rights not cleared "
                    "(D-018, O-002). Do not share outside private use.",
                    TITLE_WIDTH,
                )
            lines += wrap(pack.attribution, TITLE_WIDTH)
        return lines

    def _node(self, entity: Entity, record: CatalogRecord) -> GraphNode:
        parent = self.parents.get(entity.id)
        icon = self._icon(record)
        item = record.representation
        drawing: Literal["icon", "labeled_node", "labeled_box"] = (
            "icon" if icon else "labeled_node" if item.kind == "labeled_node" else "labeled_box"
        )
        return GraphNode(
            id=entity.id,
            entity=_entity_kind(entity),
            provider=entity.provider,
            type_id=record.id,
            drawing=drawing,
            lines=(
                *wrap(entity.name, LABEL_WIDTH),
                *self._service_label(entity, record),
                *self._notes(entity, parent),
            ),
            icon=icon,
            group=parent,
            memberships=self._declared(entity),
        )

    def _add_group(
        self,
        entity: Entity,
        record: CatalogRecord,
        groups: list[GraphGroup],
        nodes: list[GraphNode],
    ) -> None:
        parent = self.parents.get(entity.id)
        groups.append(
            GraphGroup(
                id=entity.id,
                entity=_entity_kind(entity),
                provider=entity.provider,
                type_id=record.id,
                boundary_kind=entity.kind if isinstance(entity, Boundary) else None,
                scope_kind=entity.kind if isinstance(entity, Scope) else None,
                lines=(
                    *wrap(entity.name, LABEL_WIDTH * 2),
                    *self._service_label(entity, record),
                    *self._notes(entity, parent),
                ),
                parent=parent,
                memberships=self._declared(entity),
            )
        )
        # A group whose type has an icon keeps it, as a marker that edges can also reach.
        if icon := self._icon(record):
            label = record.representation.label or record.display_name
            nodes.append(
                GraphNode(
                    id=entity.id,
                    entity=_entity_kind(entity),
                    provider=entity.provider,
                    type_id=record.id,
                    drawing="icon",
                    lines=tuple(wrap(label, LABEL_WIDTH)),
                    icon=icon,
                    group=entity.id,
                )
            )

    def _under_providers(
        self, groups: list[GraphGroup], nodes: list[GraphNode]
    ) -> tuple[list[GraphGroup], list[GraphNode]]:
        """Only this grouping adds provider boxes, and their IDs cannot equal a model ID."""
        providers: list[str] = []
        placed_groups = []
        placed_nodes = []
        for group in groups:
            if group.parent is None:
                providers.append(group.provider)
                group = group.model_copy(update={"parent": _provider_group(group.provider)})
            placed_groups.append(group)
        for node in nodes:
            if node.group is None:
                providers.append(node.provider)
                node = node.model_copy(update={"group": _provider_group(node.provider)})
            placed_nodes.append(node)
        synthetic = [
            GraphGroup(
                id=_provider_group(provider),
                entity="provider",
                provider=provider,
                type_id=None,
                lines=(PROVIDER_LABELS[provider],),
            )
            for provider in dict.fromkeys(providers)
        ]
        return [*synthetic, *placed_groups], placed_nodes

    def _check_depth(self) -> None:
        for identifier in self.group_ids:
            if len(self._chain(identifier)) > self.limits.group_depth:
                raise RenderFailure("RENDER_GROUP_DEPTH_LIMIT", "/views", identifier)


def _entity_kind(entity: Entity) -> Literal["scope", "boundary", "resource"]:
    if isinstance(entity, Scope):
        return "scope"
    return "boundary" if isinstance(entity, Boundary) else "resource"


def _provider_group(provider: str) -> str:
    return f"_provider.{provider}"


def map_view(model: Architecture, view: View, mode: Mode, limits: Limits) -> RenderGraph:
    return Mapper(model, view, mode, limits).build()
