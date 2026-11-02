# Core Contract v1.0.0

S05 / M1 and S06 / M2 implementation guide, subordinate to the single [requirements](../requirements/requirements.md). Package `0.3.0a1` is a core development version; installed Work plugin `0.1.0-alpha.3` remains the independent S04 fixture. This change does not replace that plugin or claim full architecture rendering.

## Setup and discovery

Use Python 3.13.7 and uv 0.13.0. The runtime dependency is Pydantic; `uv.lock` freezes dependency versions and hashes. Build backend hatchling 1.27.0 is also pinned. No Graphviz, Docker, Work SDK or model API is needed by this stage. `diagrams` 0.25.1 is a development dependency, used only to verify catalog icon mappings until M3.

```sh
uv sync --locked --python 3.13.7
uv run --locked cloud-diagrams capabilities
uv run --locked cloud-diagrams schema
uv run --locked cloud-diagrams validate < tests/fixtures/core-valid.json
uv run --locked cloud-diagrams validate --view detail < tests/fixtures/kubernetes-valid.json
uv run --locked cloud-diagrams catalog --provider aws --query "load balancer"
uv run --locked python scripts/quality_gate.py
```

Exit 0 means the core, catalog and provider checks passed; exit 2 means invalid input; exit 64 means the command was used incorrectly. A result with a core error stops there, reporting `validation_scope: core_only` and `catalog`, `provider_rules` and `render` as pending. A sound model also runs the semantic layer and reports `core_catalog_provider`, with `catalog_version` and only `render` pending. No render command is exposed; M3 adds final strict/lenient render behavior. Lenient mode marks a draft and turns one thing into a warning, an unknown `service_type`, keeping its provider, type and label. Every other error stays fatal.

Discovery emits the [executable schema](../../schemas/architecture-v1.schema.json). The gate compares it with the Python model and checks valid fixtures with an independent JSON Schema validator. JSON Schema expresses structural checks; cross-field/reference semantics require the core validator too. [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) supplies strict types and [schema generation](https://docs.pydantic.dev/latest/concepts/json_schema/) derives the machine contract from the same definitions.

## Data contract

| Collection | Meaning |
|---|---|
| `metadata` | Diagram ID/title/environment, explicit assumptions and optional description |
| `scopes` | Provider-specific administrative identity and optional administrative parent |
| `boundaries` | Geography/network/security/physical group, separate scope refs, optional containment parent and typed membership relations |
| `resources` | Stable ID, hosting provider, literal display name, service type/taxonomy, bounded properties and independent placement/context dimensions |
| `relationships` | Stable ID, explicit endpoint refs, typed kind/direction, literal label/protocol/purpose/security text |
| `views` | Stable ID/title, explicit entity/relationship selection, allowlisted grouping/direction/style/legend |

Entity, relationship and view IDs share a global namespace. Diagram metadata ID is separate. IDs use lowercase ASCII letters followed by letters/digits/dot/underscore/hyphen, at most 64 characters. Text labels preserve English/Thai; control characters and unpaired surrogates fail. Properties are closed typed data, not a bag of executable options. Native metadata label keys and empty values are preserved. The semantic layer checks Kubernetes, AWS, Azure and GCP label syntax; Huawei Cloud and on-premises labels are not syntax-checked. Unknown fields, arbitrary Graphviz/style keys, code and Secret data payload fields fail schema checks. String content is data and is never interpreted as code/HTML by this stage; safe graph/SVG conversion remains M3.

Ownership, location, network attachment, security membership and deployment context remain separate. Shared VPC/multiple network attachments can reference distinct scopes without inventing a single nesting tree. Scope ownership must keep provider identity. Reference existence/kind checks precede per-service placement rules. Containment/ownership and each typed boundary-membership dimension reject cycles; ordinary traffic/replication cycles are allowed.

## Kubernetes context

Kubernetes is represented by optional resource context, retaining the hosting provider. It is not a provider enum value. Cluster markers carry their own identity; other represented kinds reference a Cluster. Namespace references are required for namespaced kinds and forbidden for cluster-scoped kinds. An abstract `IngressController` may omit namespace; if supplied, the namespace must be in the same cluster.

Typed references check cluster/provider and, where applicable, namespace consistency. Resource-to-Kubernetes `ownership` edges use the same supported workload-owner kind/context rules as `kubernetes.owner_ref`; administrative Scope ownership remains separate and provider-consistent. Use membership/context for logical cluster/namespace grouping. They distinguish node pools, declared Pod-to-Node placement, workload ownership, Ingress-to-Service, Service-to-Pod targets, PVC/PV/StorageClass, ConfigMap/Secret and ServiceAccount. Namespace grouping does not assign Pods to Nodes. Missing Pod node placement remains unspecified. Secret markers are reference-only and cannot carry properties; actual secret data is outside the contract.

The context rules use the concepts in [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) and [owners/dependents](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/). The core fixture is not live discovery, Kubernetes API validation or proof of runtime reachability/enforcement. Provider mappings and kind-specific rules are in the next section. Label selectors are not modeled; Service targets remain explicit `target_refs`.

## Catalogs and provider semantics

`catalog_data` holds versioned JSON: the taxonomy, one file per provider plus common and Kubernetes records, the rule table, the required-item inventory, the rights manifest and the native-icon lock. `schemas/catalog-v1.schema.json` publishes the record format. Each record has a stable type ID, its providers, entity, display name, optional native ID, one taxonomy ID, capabilities, placement rule, representation, status and sources. The file header carries the catalog version. `cloud-diagrams catalog` returns bounded, filterable results, and `capabilities` lists `release_blockers`.

A resource resolves by `service_type`. A scope or boundary resolves by provider and kind, so it needs no type field. A resource's type must belong to its provider, so no provider is substituted, and its taxonomy must be the type's one primary ID.

Placement rules apply to what a model declares, so an unspecified zone or subnet stays valid while a contradictory one fails. Scope kind, location scope, network form, subnet counts and zones, security-group scope and host type are data on each record, with a few provider-specific checks for Azure subscriptions, GCP Shared VPC and Huawei projects. `catalog_data/rules.json` gives every diagnostic code its message, remedy and sources. A test requires each code to have a negative case, and each type to appear in a passing fixture.

Subnet network membership resolves both `parent_ref` and `network_member_of`; cloud subnets permit one network, while on-premises logical overlaps remain supported. ALB subnet attachments stay in one VPC. Singleton ownership kinds are checked across scope ancestry, independent of reference order; repeating a compatible ancestor does not create a second owner. IAM and enterprise-project dimensions remain separate.

A Pod's concrete Node scheduling edges must agree with `node_ref` and each other. Repeated agreeing declarations, unspecified placement, workload scheduling across Nodes and NodePool targets remain allowed, and NodePool edges are not reconciled with `node_ref`. An EKS managed or self-managed node group must use its cluster's declared VPC when both are supplied; different subnet lists are allowed. This rule does not constrain generic or hybrid Kubernetes nodes or Fargate profiles.

Kubernetes adds cluster modes that map each cluster type to its control-plane ownership and its allowed node-pool types, an owner matrix, per-kind reference and property rules, and rules that keep scheduling, membership, policy, storage, configuration and traffic relationships distinct. Nothing infers reachability, controller availability or a Pod's node. API versions were verified against Kubernetes 1.37.

A record's `representation` says how M3 must draw it: a controlled `diagrams` class, a bundled asset with its required label, a labeled boundary or node, or `blocked`. A blocked type is `semantics_only`: it validates, warns with `ICON_UNAVAILABLE`, and takes no substitute. No type is blocked at this catalog version. A `private_use_only` type uses an icon accepted under D-018 for private personal use only, and any model using one warns once with `ASSET_PRIVATE_USE_ONLY`. The package carries `Private :: Do Not Upload`, and the gate fails on a public repository. See the [S06 evidence](../project-management/evidence/S06-provider-catalogs.md).

## Views and diagnostics

Every view reference must resolve; a selected edge requires both endpoints selected. Every result lists each view's excluded entity/relationship IDs in `view_exclusions`, with a `VIEW_EXCLUSIONS` warning for each partial view; `selected_view` and `excluded_ids` describe the first or explicitly selected view. It never changes the canonical input or infers omitted security/traffic/placement. An explicit missing/empty view ID fails.

Diagnostics contain severity, stable code, JSON-pointer-like field, optional entity ID, message and remedy. Rejected values and raw parser exceptions are excluded. Schema version mismatches, repeated JSON keys, invalid UTF-8, nonstandard constants, duplicate IDs, bad references, cycles and wrong Kubernetes scope are fatal in both modes. Up to 100 error diagnostics are emitted; this truncation does not convert failure into success.

## Core parsing bounds

| Bound | Value |
|---|---|
| UTF-8 JSON bytes | 1 MiB |
| Nesting depth before parsing | 64 |
| Combined scopes/boundaries/resources | 1000 |
| Relationships / views | 4000 / 32 |
| Label / description length | 256 / 2048 codepoints |
| Error diagnostics | 100 |

These bound core parsing/validation; they are not renderer size/performance promises. Existing S04 render limits remain separate. Final renderer/security acceptance is M3/M4.

## Quality gate and trust

[Workflow](../../.github/workflows/quality-gate.yml) runs only explicit owner actions on this repository's main/codex branches, plus owner-created same-repository PRs. Fork/external PR actions are not scheduled on the personal runner. Checkout/upload actions are pinned to verified upstream commits, repository permissions are read-only and checkout credentials are not persisted. Dependencies use the locked native environment; see [uv's CI guide](https://docs.astral.sh/uv/guides/integration/github/), [checkout](https://github.com/actions/checkout) and [upload-artifact](https://github.com/actions/upload-artifact).

Portable documentation links must resolve inside the repository; historical host paths are provenance text, with repository-relative evidence copies for actual links. Every implemented lane runs: docs/traceability and frozen proof hashes, narrow credential patterns, Ruff lint/format, strict mypy, actionlint, schema/core tests, catalog and license checks, provider semantics, Claude plugin package contract, core package build and wheel contents. Missing tools, timeout or any failed lane fails the aggregate. Reports identify exact checkout SHA, dirty state, lock/source hashes and future checks as deferred, never passed. Report retention is 14 days. The per-run Python environment is removed after the job. This is a core package build, not M5 plugin-package acceptance. Read-only GitHub API verification found only the owner as collaborator and fork-PR workflows disabled at the S05 snapshot; these server-side access settings complement the actor guards. An editable workflow alone is not a tamper-resistant trust boundary.

Credential patterns are a narrow working-tree check, not an entropy/history scan or security audit. Static typing/lint cover implemented core/scripts/tests; historical S04 spike source remains frozen and separately reviewed. Tests/CI contain synthetic architectures. Current private-plan limitations still require manual review/merge discipline. Separate Astra review is recorded outside the pipeline without paid model API calls.
