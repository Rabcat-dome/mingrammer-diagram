"""Bounded JSON parsing, identity/reference checks and Kubernetes context rules."""

import json
from collections import Counter, deque
from typing import Literal

from pydantic import ValidationError

from .diagnostics import Diagnostic, ValidationResult
from .models import (
    CLUSTER_SCOPED,
    MAX_DEPTH,
    MAX_ENTITIES,
    MAX_INPUT_BYTES,
    SCHEMA_VERSION,
    Architecture,
    Boundary,
    Entity,
    Resource,
    Scope,
)

Mode = Literal["strict", "lenient"]
WORKLOAD_OWNERS = {"Deployment", "ReplicaSet", "StatefulSet", "DaemonSet", "Job", "CronJob", "Pod"}


class InputFailure(ValueError):
    pass


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise InputFailure("INPUT_DUPLICATE_KEY")
        result[key] = value
    return result


def _constant(_: str) -> object:
    raise InputFailure("INPUT_JSON_INVALID")


def _depth(text: str) -> None:
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise InputFailure("INPUT_DEPTH_LIMIT")
        elif char in "]}":
            depth -= 1


def _unicode(value: object) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise InputFailure("INPUT_UNICODE_INVALID")
    elif isinstance(value, list):
        for child in value:
            _unicode(child)
    elif isinstance(value, dict):
        for key, child in value.items():
            _unicode(key)
            _unicode(child)


def _error(code: str, field: str, entity_id: str | None = None) -> Diagnostic:
    messages = {
        "INPUT_SIZE_LIMIT": ("JSON exceeds 1 MiB.", "Reduce the model before submitting it."),
        "INPUT_DEPTH_LIMIT": ("JSON exceeds 64 nesting levels.", "Remove excessive nesting."),
        "INPUT_JSON_INVALID": (
            "Input is not strict UTF-8 JSON.",
            "Use valid UTF-8 JSON without NaN or Infinity.",
        ),
        "INPUT_UNICODE_INVALID": (
            "Input contains unpaired Unicode surrogates.",
            "Supply valid Unicode text.",
        ),
        "INPUT_DUPLICATE_KEY": (
            "A JSON object repeats a key.",
            "Remove the duplicate; last-value-wins parsing is forbidden.",
        ),
        "SCHEMA_VERSION_UNSUPPORTED": (
            "Schema version is missing or unsupported.",
            "Set schema_version to 1.0.0; migrate other versions explicitly.",
        ),
        "SCHEMA_FIELD_INVALID": (
            "Field violates the closed, strict schema.",
            "Use schema discovery; remove unknown fields and correct field types/bounds.",
        ),
        "ID_DUPLICATE": (
            "An ID is reused across entities, relationships or views.",
            "Assign unique stable IDs across these collections.",
        ),
        "MODEL_ENTITY_LIMIT": (
            "Combined scopes/boundaries/resources exceed 1000.",
            "Reduce the submitted model; selecting a smaller view does not reduce input size.",
        ),
        "REFERENCE_MISSING": (
            "Reference does not identify a declared entity.",
            "Declare its target or use the correct existing ID.",
        ),
        "REFERENCE_KIND_INVALID": (
            "Reference points to the wrong entity/boundary kind.",
            "Use the entity kind specified for this field in the contract guide.",
        ),
        "REFERENCE_DUPLICATE": (
            "A reference list repeats an ID.",
            "Keep each target ID once in this list.",
        ),
        "CONTAINMENT_CYCLE": (
            "An ownership/containment dimension contains a cycle.",
            "Remove the cyclic parent, owner or same-dimension membership relation.",
        ),
        "SCOPE_PROVIDER_MISMATCH": (
            "Administrative scope belongs to another provider.",
            "Keep ownership references in the entity's provider; use relationships for cross-provider connectivity.",
        ),
        "K8S_CLUSTER_REQUIRED": (
            "Kubernetes entity lacks cluster context.",
            "Set cluster_ref to a declared Cluster resource.",
        ),
        "K8S_CLUSTER_CONTEXT_INVALID": (
            "Cluster identity cannot reference another cluster.",
            "Remove cluster_ref from the Cluster marker itself.",
        ),
        "K8S_NAMESPACE_REQUIRED": (
            "Namespaced Kubernetes entity lacks namespace context.",
            "Set namespace_ref to a Namespace in the same cluster.",
        ),
        "K8S_NAMESPACE_FORBIDDEN": (
            "Cluster-scoped kind has a namespace.",
            "Remove namespace_ref from this cluster-scoped entity.",
        ),
        "K8S_CLUSTER_MISMATCH": (
            "Kubernetes reference crosses cluster or hosting-provider context.",
            "Use a target in the same cluster/provider; represent external traffic separately.",
        ),
        "K8S_NAMESPACE_MISMATCH": (
            "Kubernetes reference crosses namespace context.",
            "Use a target in the same namespace for this reference role.",
        ),
        "K8S_REFERENCE_KIND_INVALID": (
            "Kubernetes reference targets an incompatible kind.",
            "Use the kind required by this role, such as Node for node_ref or Secret for secret_refs.",
        ),
        "K8S_REFERENCE_ROLE_INVALID": (
            "Reference role is not supported on this source kind.",
            "Use the documented source kind, such as Pod for node_ref and Ingress for service_refs.",
        ),
        "K8S_SECRET_REFERENCE_ONLY": (
            "Secret markers permit references, not property values.",
            "Remove Secret properties; retain only its identity, name, provider and context.",
        ),
        "VIEW_NOT_FOUND": ("Requested view ID is not declared.", "Select an existing view ID."),
        "VIEW_RELATIONSHIP_MISSING": (
            "View selects an undeclared relationship.",
            "Declare the relationship or remove its selection.",
        ),
        "VIEW_ENDPOINT_EXCLUDED": (
            "A selected relationship has an excluded endpoint.",
            "Select both endpoints or remove the relationship from this view.",
        ),
    }
    message, remedy = messages[code]
    return Diagnostic(
        severity="error",
        code=code,
        field=field,
        entity_id=entity_id,
        message=message,
        remedy=remedy,
    )


def _cycles(graph: dict[str, set[str]]) -> bool:
    """Kahn traversal avoids recursion on long, otherwise valid containment chains."""
    indegree = dict.fromkeys(graph, 0)
    for targets in graph.values():
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1
    ready = deque(node for node, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        node = ready.popleft()
        visited += 1
        for target in graph.get(node, set()):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return visited != len(indegree)


class Checker:
    def __init__(self, model: Architecture) -> None:
        self.model = model
        self.entities: dict[str, Entity] = {
            entity.id: entity for entity in [*model.scopes, *model.boundaries, *model.resources]
        }
        self.diagnostics: list[Diagnostic] = []

    def error(self, code: str, field: str, source: str | None = None) -> None:
        if len(self.diagnostics) < 100:
            self.diagnostics.append(_error(code, field, source))

    def ref(
        self,
        identifier: str,
        field: str,
        source: str,
        expected: type[Scope] | type[Boundary] | type[Resource] | None = None,
        kind: str | None = None,
    ) -> Entity | None:
        target = self.entities.get(identifier)
        if target is None:
            self.error("REFERENCE_MISSING", field, source)
        elif expected is not None and not isinstance(target, expected):
            self.error("REFERENCE_KIND_INVALID", field, source)
        elif kind is not None and (not isinstance(target, Boundary) or target.kind != kind):
            self.error("REFERENCE_KIND_INVALID", field, source)
        else:
            source_entity = self.entities.get(source)
            if (
                isinstance(target, Scope)
                and source_entity
                and source_entity.provider != target.provider
            ):
                self.error("SCOPE_PROVIDER_MISMATCH", field, source)
                return None
            return target
        return None

    def refs(
        self,
        ids: list[str],
        field: str,
        source: str,
        expected: type[Scope] | type[Boundary] | type[Resource] | None = None,
        kind: str | None = None,
    ) -> None:
        if len(ids) != len(set(ids)):
            self.error("REFERENCE_DUPLICATE", field, source)
        for i, identifier in enumerate(ids):
            self.ref(identifier, f"{field}/{i}", source, expected, kind)

    def general(self) -> None:
        graphs: dict[str, dict[str, set[str]]] = {"scope": {}, "boundary": {}, "owner": {}}
        for i, scope in enumerate(self.model.scopes):
            graphs["scope"][scope.id] = set()
            if scope.parent_ref:
                target = self.ref(scope.parent_ref, f"/scopes/{i}/parent_ref", scope.id, Scope)
                if target:
                    graphs["scope"][scope.id].add(target.id)
                    if target.provider != scope.provider:
                        self.error("SCOPE_PROVIDER_MISMATCH", f"/scopes/{i}/parent_ref", scope.id)
        for i, boundary in enumerate(self.model.boundaries):
            path = f"/boundaries/{i}"
            graphs["boundary"][boundary.id] = set()
            self.refs(boundary.scope_refs, path + "/scope_refs", boundary.id, Scope)
            if boundary.parent_ref:
                if target := self.ref(
                    boundary.parent_ref, path + "/parent_ref", boundary.id, Boundary
                ):
                    graphs["boundary"][boundary.id].add(target.id)
            for n, relation in enumerate(boundary.relations):
                self.ref(
                    relation.target_ref, f"{path}/relations/{n}/target_ref", boundary.id, Boundary
                )
                graphs.setdefault(relation.kind, {}).setdefault(boundary.id, set()).add(
                    relation.target_ref
                )
        for i, resource in enumerate(self.model.resources):
            path = f"/resources/{i}/placement"
            placement = resource.placement
            self.refs(placement.scope_refs, path + "/scope_refs", resource.id, Scope)
            for field, kind in [
                ("region_ref", "region"),
                ("zone_ref", "zone"),
                ("site_ref", "site"),
                ("rack_ref", "rack"),
            ]:
                if identifier := getattr(placement.location, field):
                    self.ref(identifier, path + "/location/" + field, resource.id, Boundary, kind)
            for n, attachment in enumerate(placement.network_attachments):
                prefix = f"{path}/network_attachments/{n}"
                self.ref(
                    attachment.network_ref,
                    prefix + "/network_ref",
                    resource.id,
                    Boundary,
                    "network",
                )
                self.refs(
                    attachment.subnet_refs, prefix + "/subnet_refs", resource.id, Boundary, "subnet"
                )
            self.refs(
                placement.security_boundaries,
                path + "/security_boundaries",
                resource.id,
                Boundary,
                "security_zone",
            )
            self.refs(placement.deployment_context, path + "/deployment_context", resource.id)
            for n, identifier in enumerate(placement.deployment_context):
                target = self.entities.get(identifier)
                if target and not isinstance(target, (Boundary, Resource)):
                    self.error(
                        "REFERENCE_KIND_INVALID", f"{path}/deployment_context/{n}", resource.id
                    )
            if resource.kubernetes and resource.kubernetes.owner_ref:
                graphs["owner"].setdefault(resource.id, set()).add(resource.kubernetes.owner_ref)
        for i, relationship in enumerate(self.model.relationships):
            self.ref(relationship.source_ref, f"/relationships/{i}/source_ref", relationship.id)
            self.ref(relationship.target_ref, f"/relationships/{i}/target_ref", relationship.id)
            if relationship.kind == "ownership":
                graphs["owner"].setdefault(relationship.target_ref, set()).add(
                    relationship.source_ref
                )
                dependent = self.entities.get(relationship.target_ref)
                owner = self.entities.get(relationship.source_ref)
                if isinstance(dependent, Resource) and dependent.kubernetes and owner is not None:
                    path = f"/relationships/{i}/source_ref"
                    if isinstance(owner, Scope):
                        # Administrative scope is distinct from a Kubernetes controller owner.
                        self.ref(owner.id, path, dependent.id, Scope)
                    else:
                        # Alternate controller-ownership encodings must use identical context rules.
                        self.k8_ref(dependent, path, owner.id, WORKLOAD_OWNERS, True)
        for name, graph in graphs.items():
            if _cycles(graph):
                self.error("CONTAINMENT_CYCLE", "/" + name)

    def k8_ref(
        self,
        resource: Resource,
        path: str,
        identifier: str,
        kinds: set[str],
        namespaced: bool = False,
    ) -> None:
        context = resource.kubernetes
        assert context is not None
        found = self.ref(identifier, path, resource.id, Resource)
        if not isinstance(found, Resource):
            return
        other = found.kubernetes
        if other is None or other.kind not in kinds:
            self.error("K8S_REFERENCE_KIND_INVALID", path, resource.id)
            return
        cluster = resource.id if context.kind == "Cluster" else context.cluster_ref
        other_cluster = found.id if other.kind == "Cluster" else other.cluster_ref
        if cluster != other_cluster or resource.provider != found.provider:
            self.error("K8S_CLUSTER_MISMATCH", path, resource.id)
        if namespaced and context.namespace_ref != other.namespace_ref:
            self.error("K8S_NAMESPACE_MISMATCH", path, resource.id)

    def kubernetes(self) -> None:
        for i, resource in enumerate(self.model.resources):
            context = resource.kubernetes
            if context is None:
                continue
            path = f"/resources/{i}/kubernetes"
            if context.kind == "Cluster":
                if context.cluster_ref is not None:
                    self.error("K8S_CLUSTER_CONTEXT_INVALID", path + "/cluster_ref", resource.id)
            elif context.cluster_ref is None:
                self.error("K8S_CLUSTER_REQUIRED", path + "/cluster_ref", resource.id)
            if context.kind in CLUSTER_SCOPED:
                if context.namespace_ref is not None:
                    self.error("K8S_NAMESPACE_FORBIDDEN", path + "/namespace_ref", resource.id)
            elif context.kind != "IngressController" and context.namespace_ref is None:
                self.error("K8S_NAMESPACE_REQUIRED", path + "/namespace_ref", resource.id)
            if context.cluster_ref:
                self.k8_ref(resource, path + "/cluster_ref", context.cluster_ref, {"Cluster"})
            if context.namespace_ref:
                self.k8_ref(resource, path + "/namespace_ref", context.namespace_ref, {"Namespace"})
            roles: list[tuple[str, set[str], bool]] = [
                ("node_pool_ref", {"NodePool"}, False),
                ("node_ref", {"Node"}, False),
                (
                    "owner_ref",
                    WORKLOAD_OWNERS,
                    True,
                ),
                ("volume_ref", {"PersistentVolume"}, False),
                ("storage_class_ref", {"StorageClass"}, False),
                ("service_account_ref", {"ServiceAccount"}, True),
            ]
            allowed_sources = {
                "node_pool_ref": {"Node"},
                "node_ref": {"Pod"},
                "volume_ref": {"PersistentVolumeClaim"},
                "storage_class_ref": {"PersistentVolumeClaim", "PersistentVolume"},
            }
            for field, kinds, namespaced in roles:
                if identifier := getattr(context, field):
                    if field in allowed_sources and context.kind not in allowed_sources[field]:
                        self.error("K8S_REFERENCE_ROLE_INVALID", path + "/" + field, resource.id)
                    self.k8_ref(resource, path + "/" + field, identifier, kinds, namespaced)
            collections = [
                ("service_refs", {"Service"}),
                ("target_refs", {"Pod"}),
                ("volume_claim_refs", {"PersistentVolumeClaim"}),
                ("config_refs", {"ConfigMap"}),
                ("secret_refs", {"Secret"}),
            ]
            for field, kinds in collections:
                identifiers: list[str] = getattr(context, field)
                if len(identifiers) != len(set(identifiers)):
                    self.error("REFERENCE_DUPLICATE", path + "/" + field, resource.id)
                if identifiers and (
                    (field == "service_refs" and context.kind != "Ingress")
                    or (field == "target_refs" and context.kind != "Service")
                ):
                    self.error("K8S_REFERENCE_ROLE_INVALID", path + "/" + field, resource.id)
                for n, identifier in enumerate(identifiers):
                    self.k8_ref(resource, f"{path}/{field}/{n}", identifier, kinds, True)
            if context.kind == "Secret" and resource.properties.model_dump(exclude_defaults=True):
                self.error("K8S_SECRET_REFERENCE_ONLY", f"/resources/{i}/properties", resource.id)

    def views(self) -> None:
        edges = {edge.id: edge for edge in self.model.relationships}
        for i, view in enumerate(self.model.views):
            self.refs(view.entity_refs, f"/views/{i}/entity_refs", view.id)
            if len(view.relationship_refs) != len(set(view.relationship_refs)):
                self.error("REFERENCE_DUPLICATE", f"/views/{i}/relationship_refs", view.id)
            for n, identifier in enumerate(view.relationship_refs):
                edge = edges.get(identifier)
                path = f"/views/{i}/relationship_refs/{n}"
                if edge is None:
                    self.error("VIEW_RELATIONSHIP_MISSING", path, view.id)
                elif not {edge.source_ref, edge.target_ref} <= set(view.entity_refs):
                    self.error("VIEW_ENDPOINT_EXCLUDED", path, view.id)


def validate_json(
    payload: bytes, *, mode: Mode = "strict", view_id: str | None = None
) -> ValidationResult:
    result = ValidationResult(valid=False, mode=mode, draft=mode == "lenient")
    try:
        if len(payload) > MAX_INPUT_BYTES:
            raise InputFailure("INPUT_SIZE_LIMIT")
        text = payload.decode("utf-8", errors="strict")
        _depth(text)
        value: object = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
        _unicode(value)
        if isinstance(value, dict) and value.get("schema_version") != SCHEMA_VERSION:
            raise InputFailure("SCHEMA_VERSION_UNSUPPORTED")
        model = Architecture.model_validate(value)
    except InputFailure as error:
        result.diagnostics = [
            _error(
                str(error), "/schema_version" if str(error) == "SCHEMA_VERSION_UNSUPPORTED" else "/"
            )
        ]
        return result
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ValidationError):
            result.diagnostics = [
                _error(
                    "SCHEMA_FIELD_INVALID",
                    "/"
                    + "/".join(
                        str(part).replace("~", "~0").replace("/", "~1")[:128]
                        for part in item["loc"]
                    ),
                )
                for item in error.errors(
                    include_input=False, include_context=False, include_url=False
                )[:100]
            ]
        else:
            result.diagnostics = [_error("INPUT_JSON_INVALID", "/")]
        return result
    identifiers = (
        [item.id for item in model.scopes]
        + [item.id for item in model.boundaries]
        + [item.id for item in model.resources]
        + [item.id for item in model.relationships]
        + [item.id for item in model.views]
    )
    counts = Counter(identifiers)
    if any(count > 1 for count in counts.values()):
        result.diagnostics = [_error("ID_DUPLICATE", "/")]
        return result
    if len(model.scopes) + len(model.boundaries) + len(model.resources) > MAX_ENTITIES:
        result.diagnostics = [_error("MODEL_ENTITY_LIMIT", "/")]
        return result
    checker = Checker(model)
    checker.general()
    checker.kubernetes()
    checker.views()
    selected = (
        next((view for view in model.views if view.id == view_id), None)
        if view_id is not None
        else model.views[0]
    )
    relationships = {edge.id for edge in model.relationships}
    result.view_exclusions = {
        view.id: sorted(
            (set(checker.entities) - set(view.entity_refs))
            | (relationships - set(view.relationship_refs))
        )
        for view in model.views
    }
    if selected is None:
        checker.error("VIEW_NOT_FOUND", "/views")
    else:
        result.selected_view = selected.id
        result.excluded_ids = result.view_exclusions[selected.id]
    result.diagnostics = checker.diagnostics
    result.valid = not checker.diagnostics
    if result.valid:
        result.diagnostics.extend(
            Diagnostic(
                severity="warning",
                code="VIEW_EXCLUSIONS",
                field=f"/views/{index}",
                entity_id=view.id,
                message="This view excludes declared IDs; see view_exclusions.",
                remedy="Include needed IDs explicitly or retain this disclosed partial view.",
            )
            for index, view in enumerate(model.views)
            if result.view_exclusions[view.id]
        )
    return result
