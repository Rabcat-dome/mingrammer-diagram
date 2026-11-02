# Core Contract v1.0.0

S05 / M1 implementation guide, subordinate to the single [requirements](../requirements/requirements.md). Package `0.2.0a1` is a core development version; installed Work plugin `0.1.0-alpha.3` remains the independent S04 fixture. This change does not replace that plugin or claim full architecture rendering.

## Setup and discovery

Use Python 3.13.7 and uv 0.13.0. The runtime dependency is Pydantic; `uv.lock` freezes dependency versions and hashes. Build backend hatchling 1.27.0 is also pinned. No Graphviz, Docker, Work SDK or model API is needed by this core stage.

```sh
uv sync --locked --python 3.13.7
uv run --locked cloud-diagrams capabilities
uv run --locked cloud-diagrams schema
uv run --locked cloud-diagrams validate < tests/fixtures/core-valid.json
uv run --locked cloud-diagrams validate --view detail < tests/fixtures/kubernetes-valid.json
uv run --locked python scripts/quality_gate.py
```

Exit 0 means the implemented **core** checks passed; exit 2 means invalid input. Results always identify `validation_scope: core_only` and pending catalog/provider/render layers. No render command is exposed. A structurally acceptable service type is not an approved/resolved catalog type. M2 adds catalog/provider validation; M3 adds final strict/lenient render behavior. Lenient mode already marks a draft but cannot bypass any core error; no recoverable fallback is implemented here.

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

Entity, relationship and view IDs share a global namespace. Diagram metadata ID is separate. IDs use lowercase ASCII letters followed by letters/digits/dot/underscore/hyphen, at most 64 characters. Text labels preserve English/Thai; control characters and unpaired surrogates fail. Properties are closed typed data, not a bag of executable options. Native metadata label keys/empty values are preserved; exact provider label syntax is M2 work. Unknown fields, arbitrary Graphviz/style keys, code and Secret data payload fields fail schema checks. String content is data and is never interpreted as code/HTML by this stage; safe graph/SVG conversion remains M3.

Ownership, location, network attachment, security membership and deployment context remain separate. Shared VPC/multiple network attachments can reference distinct scopes without inventing a single nesting tree. Scope ownership must keep provider identity. Reference existence/kind checks precede later per-service placement rules. Containment/ownership and each typed boundary-membership dimension reject cycles; ordinary traffic/replication cycles are allowed.

## Kubernetes context

Kubernetes is represented by optional resource context, retaining the hosting provider. It is not a provider enum value. Cluster markers carry their own identity; other represented kinds reference a Cluster. Namespace references are required for namespaced kinds and forbidden for cluster-scoped kinds. An abstract `IngressController` may omit namespace; if supplied, the namespace must be in the same cluster. Exact managed-mode/provider mappings and API versions are M2 decisions.

Typed references check cluster/provider and, where applicable, namespace consistency. Resource-to-Kubernetes `ownership` edges use the same supported workload-owner kind/context rules as `kubernetes.owner_ref`; administrative Scope ownership remains separate and provider-consistent. Use membership/context for logical cluster/namespace grouping. They distinguish node pools, declared Pod-to-Node placement, workload ownership, Ingress-to-Service, Service-to-Pod targets, PVC/PV/StorageClass, ConfigMap/Secret and ServiceAccount. Namespace grouping does not assign Pods to Nodes. Missing Pod node placement remains unspecified. Secret markers are reference-only and cannot carry properties; actual secret data is outside the contract.

The context rules use the concepts in [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) and [owners/dependents](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/). The core fixture is not live discovery, Kubernetes API validation or proof of runtime reachability/enforcement. Full kind/provider-specific rules and selector/controller behavior remain M2.

## Views and diagnostics

Every view reference must resolve; a selected edge requires both endpoints selected. A selected partial view returns every excluded entity/relationship ID and a `VIEW_EXCLUSIONS` warning. It never changes the canonical input or infers omitted security/traffic/placement. An explicit missing/empty view ID fails.

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

Portable documentation links must resolve inside the repository; historical host paths are provenance text, with repository-relative evidence copies for actual links. Every implemented lane runs: docs/traceability and frozen proof hashes, narrow credential patterns, Ruff lint/format, strict mypy, actionlint, schema/core tests and core package build. Missing tools, timeout or any failed lane fails the aggregate. Reports identify exact checkout SHA, dirty state, lock/source hashes and future checks as deferred, never passed. Report retention is 14 days. The per-run Python environment is removed after the job. This is a core package build, not M5 plugin-package acceptance. Read-only GitHub API verification found only the owner as collaborator and fork-PR workflows disabled at the S05 snapshot; these server-side access settings complement the actor guards. An editable workflow alone is not a tamper-resistant trust boundary.

Credential patterns are a narrow working-tree check, not an entropy/history scan or security audit. Static typing/lint cover implemented core/scripts/tests; historical S04 spike source remains frozen and separately reviewed. Tests/CI contain synthetic architectures. Current private-plan limitations still require manual review/merge discipline. Separate Astra review is recorded outside the pipeline without paid model API calls.
