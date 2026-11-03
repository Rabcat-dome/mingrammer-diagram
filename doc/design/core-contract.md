# Core Contract v1.0.0

S05 / M1, S06 / M2 and S07 / M3 implementation guide, subordinate to the single [requirements](../requirements/requirements.md). Package `0.5.0a1` is a core development version; installed Work plugin `0.1.0-alpha.3` remains the independent S04 fixture. This change does not replace that plugin. The renderer is an engineering slice, so coverage, visual quality and official-reference comparison stay with M4.

## Setup and discovery

Use Python 3.13.7 and uv 0.13.0. The runtime dependencies are Pydantic, `diagrams` 0.25.1 and Python `graphviz`; `uv.lock` freezes dependency versions and hashes. Build backend hatchling 1.27.0 is also pinned. Rendering also needs Graphviz `dot` on `PATH`, tested with 16.1.0, and macOS `sandbox-exec`. Validation and discovery need neither, and nothing needs Docker, a Work SDK or a model API.

```sh
uv sync --locked --python 3.13.7
uv run --locked cloud-diagrams capabilities
uv run --locked cloud-diagrams schema
uv run --locked cloud-diagrams validate < tests/fixtures/core-valid.json
uv run --locked cloud-diagrams validate --view detail < tests/fixtures/kubernetes-valid.json
uv run --locked cloud-diagrams catalog --provider aws --query "load balancer"
uv run --locked cloud-diagrams render --output rendered < tests/fixtures/core-valid.json
uv run --locked cloud-diagrams render --output rendered --view detail < tests/fixtures/kubernetes-valid.json
uv run --locked python scripts/quality_gate.py
```

Exit 0 means the command succeeded; exit 2 means invalid input, or a view that cannot be drawn as asked, including an image over the pixel, scale or file limit; exit 4 means this render failed and published nothing, with JSON diagnostics on stdout; exit 64 means the command was used incorrectly. A result with a core error stops there, reporting `validation_scope: core_only` and `catalog`, `provider_rules` and `render` as pending. A sound model also runs the semantic layer and reports `core_catalog_provider`, with `catalog_version` and only `render` pending on a `validate` result. A published `render` result reports nothing pending. Lenient mode marks a draft and turns one thing into a warning, an unknown `service_type`, keeping its provider, type and label. Every other error stays fatal.

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

Entity, relationship and view IDs share a global namespace. Diagram metadata ID is separate. IDs use lowercase ASCII letters followed by letters/digits/dot/underscore/hyphen, at most 64 characters. Text labels preserve English/Thai; control characters and unpaired surrogates fail. Properties are closed typed data, not a bag of executable options. Native metadata label keys and empty values are preserved. The semantic layer checks Kubernetes, AWS, Azure and GCP label syntax; Huawei Cloud and on-premises labels are not syntax-checked. Unknown fields, arbitrary Graphviz/style keys, code and Secret data payload fields fail schema checks. String content is data and is never interpreted as code or HTML, including by the renderer below.

Ownership, location, network attachment, security membership and deployment context remain separate. Shared VPC/multiple network attachments can reference distinct scopes without inventing a single nesting tree. Scope ownership must keep provider identity. Reference existence/kind checks precede per-service placement rules. Containment/ownership and each typed boundary-membership dimension reject cycles; ordinary traffic/replication cycles are allowed.

## Kubernetes context

Kubernetes is represented by optional resource context, retaining the hosting provider. It is not a provider enum value. Cluster markers carry their own identity; other represented kinds reference a Cluster. Namespace references are required for namespaced kinds and forbidden for cluster-scoped kinds. An abstract `IngressController` may omit namespace; if supplied, the namespace must be in the same cluster.

Typed references check cluster/provider and, where applicable, namespace consistency. Resource-to-Kubernetes `ownership` edges use the same supported workload-owner kind/context rules as `kubernetes.owner_ref`; administrative Scope ownership remains separate and provider-consistent. Use membership/context for logical cluster/namespace grouping. They distinguish node pools, declared Pod-to-Node placement, workload ownership, Ingress-to-Service, Service-to-Pod targets, PVC/PV/StorageClass, ConfigMap/Secret and ServiceAccount. Namespace grouping does not assign Pods to Nodes. Missing Pod node placement remains unspecified. Secret markers are reference-only and cannot carry properties; actual secret data is outside the contract.

The context rules use the concepts in [Kubernetes namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/) and [owners/dependents](https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/). The core fixture is not live discovery, Kubernetes API validation or proof of runtime reachability/enforcement. Provider mappings and kind-specific rules are in the next section. Label selectors are not modeled; Service targets remain explicit `target_refs`.

## Catalogs and provider semantics

`catalog_data` holds versioned JSON: the taxonomy, one file per provider plus common and Kubernetes records, the rule table, the required-item inventory, the rights manifest and the native-icon lock. `schemas/catalog-v1.schema.json` publishes the record format. Each record has a stable type ID, its providers, entity, display name, optional native ID, one taxonomy ID, capabilities, placement rule, representation, status and sources. The file header carries the catalog version. `cloud-diagrams catalog` returns bounded, filterable results, and `capabilities` lists `release_blockers`.

A resource resolves by `service_type`. A scope or boundary resolves by provider and kind, so it needs no type field. A resource's type must belong to its provider, so no provider is substituted, and its taxonomy must be the type's one primary ID.

Placement rules apply to what a model declares, so an unspecified zone or subnet stays valid while a contradictory one fails. A subnet's network is found through its parent and through any VLAN and VRF in between. Scope kind, location scope, network form, subnet counts and zones, security-group scope and host type are data on each record, with a few provider-specific checks for Azure subscriptions, GCP Shared VPC and Huawei projects. `catalog_data/rules.json` gives every diagnostic code its message, remedy and sources. A test requires each code to have a negative case, and each type to appear in a passing fixture.

Subnet network membership resolves both `parent_ref` and `network_member_of`; cloud subnets permit one network, while on-premises logical overlaps remain supported. ALB subnet attachments stay in one VPC. Singleton ownership kinds are checked across scope ancestry, independent of reference order; repeating a compatible ancestor does not create a second owner. IAM and enterprise-project dimensions remain separate.

A Pod's concrete Node scheduling edges must agree with `node_ref` and each other. Repeated agreeing declarations, unspecified placement, workload scheduling across Nodes and NodePool targets remain allowed, and NodePool edges are not reconciled with `node_ref`. An EKS managed or self-managed node group must use its cluster's declared VPC when both are supplied; different subnet lists are allowed. This rule does not constrain generic or hybrid Kubernetes nodes or Fargate profiles.

Kubernetes adds cluster modes that map each cluster type to its control-plane ownership and its allowed node-pool types, an owner matrix, per-kind reference and property rules, and rules that keep scheduling, membership, policy, storage, configuration and traffic relationships distinct. Nothing infers reachability, controller availability or a Pod's node. API versions were verified against Kubernetes 1.37.

A record's `representation` says how M3 must draw it: a controlled `diagrams` class, a bundled asset with its required label, a labeled boundary or node, or `blocked`. A blocked type is `semantics_only`: it validates, warns with `ICON_UNAVAILABLE`, and takes no substitute, so `render` refuses it in both modes with `RENDER_TYPE_BLOCKED`. No type is blocked at this catalog version. A `private_use_only` type uses an icon accepted under D-018 for private personal use only, and any model using one warns once with `ASSET_PRIVATE_USE_ONLY`. The package carries `Private :: Do Not Upload`, and the gate fails on a public repository. See the [S06 evidence](../project-management/evidence/S06-provider-catalogs.md).

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

These bound core parsing and validation. The renderer's own limits are below, and M4-04 refines them with measurements.

## Controlled rendering

`cloud-diagrams render --output DIR [--mode strict|lenient] [--view ID]` reads the model from stdin, validates it, draws one view and publishes one new bundle under `DIR`. Validation is unconditional: `render_model` is the only entry point, and a model reaches the mapper only after `validate_model` passes it, so no flag or field skips a check. A failed validation creates no output directory. The first view is the default; run once per view, so an overview and a detail view of one model are separate renders with stable IDs.

**Mapping (M3-01).** Only `view.entity_refs` and `view.relationship_refs` are drawn, and nothing infers a relationship. Each record draws through its `representation`:

| Representation | Drawn as |
|---|---|
| `native_class` | Its `diagrams` class, which must match the icon lock's resource and digest before use |
| `custom_asset` | The verified bundled PNG, with the catalog label, so an asset keeps its `required_label` |
| `labeled_boundary` | A cluster, or a labeled dashed box where the view's grouping does not nest it. An `asset` on the record adds an icon marker inside |
| `labeled_node` | A labeled box with no icon |
| `blocked` | Nothing: the render fails with `RENDER_TYPE_BLOCKED` |

Clusters form a tree, and these dimensions do not. Each entity therefore nests under the first selected container its view's `grouping` allows, and every other selected membership stays visible as a text note on the node, such as `security: Web tier`. A declared subnet, zone or rack stays noted even when the view does not select it, so a view can leave out those boxes and keep the fact, and a region is noted only when selected. A resource or boundary never nests inside a scope it does not declare or inherit, so an account-scoped service whose region sits in a project's box nests by its account instead. The order a view lists its entities does not change the nesting. Where two groups could each nest in the other through different dimensions, ID order decides which box holds which, and the other fact stays a note. A resource with several subnets nests under their common network and names them. Namespace and worker placement stay separate facts: `namespace` grouping never puts a Pod inside a Node, `node` grouping nests only a Pod with a declared `node_ref`, each view states the other dimension in a note, and a Pod without a Node reads `node: unspecified`. A group with no members still draws, because Graphviz would otherwise drop it. `provider` grouping adds synthetic provider boxes whose IDs cannot equal a model ID. `view.json` keeps every declared membership and the whole normalized graph, free of host paths, for M4 comparison.

**Presentation (FR-042, FR-048).** In a `provider`-style view, `GROUP_STYLES` in `render/draw.py` gives a group the border and fill read from the [provider references](../project-management/evidence/S08-reference-diagrams.md#provider-references). It is a closed table, so no model value reaches it. A provider box is tinted only when a view holds several providers. Members with no edge in the view are arranged in rows by invisible layout edges, which draw nothing and hold no model text, because Graphviz would otherwise stack them in one column. A left-right icon sits at the middle of its node, so edges meet the icon and not its label. A legend sample has an arrowhead only for a kind that has a directed edge in the view.

| Grouping | Nests by |
|---|---|
| `none` | Nothing; every entity is a node |
| `provider` | Provider, then every declared dimension, with Kubernetes context first |
| `scope` | Scopes |
| `network` | Networks, subnets, VLANs and VRFs |
| `namespace` | Kubernetes Cluster, Namespace and NodePool |
| `node` | Kubernetes Cluster, NodePool and Node |
| `physical` | Regions, zones, sites, data centers, rooms and racks |

**Input safety (FR-045, T-009).** The model has no field for a path, URL, icon, class, attribute or color. `service_type` resolves only by exact catalog lookup, and a catalog class path must be in the icon lock before any import. Labels are escaped for Graphviz so that `<...>` cannot become an HTML label, `\N` cannot become an escape sequence and `&amp;` stays those five characters; a test reads the DOT back through Graphviz and finds only the expected graph. Direction, grouping, style and legend are closed lists, and edge colors come from one table keyed by relationship kind. HTML-like input is drawn as literal text, not rejected, because a label such as `App <prod>` is legitimate data. No DOT or PDF export exists; FR-044 is P1.

**Execution (NFR-002, NFR-009).** Only `dot` runs, under `sandbox-exec` and with an empty inherited environment. The profile denies network, new processes, writes outside the request directory and reads from the account's home directory. Everything `dot` reads is copied there first: icons by SHA-256 name after their digests are verified, and the two fonts. One `dot` run writes both images, so they share one layout. `dot -v` reports the font files it really resolved, and a render that used anything but the bundled fonts fails with `RENDER_FONT_UNAVAILABLE`. A host without the sandbox fails closed with `RENDER_ISOLATION_UNAVAILABLE`; rendering is verified on macOS only.

| Render bound | Value | Enforcement |
|---|---|---|
| Entities / relationships per view | 200 / 300 | Rejected before Graphviz, with a suggestion to split |
| Group nesting | 16 levels | Rejected before Graphviz |
| Wall time | 55 s | Process group killed |
| CPU time | 45 s soft, 50 s hard | `RLIMIT_CPU` |
| Memory | 1 GiB | Sampled process-group RSS, not a kernel cap |
| Temporary storage | 256 MiB | Sampled request-directory bytes, not a quota |
| Each file | 16 MiB | `RLIMIT_FSIZE`, then checked on read |
| PNG pixels | 32,000,000 | Checked at full size from the SVG and again on the finished file; exit 2 |
| PNG side | 32,767 pixels | Cairo shrinks a larger image, which is compared with the SVG, recorded as `png.scale` and reported as `RENDER_PNG_SCALED` |
| PNG scale | At least 0.5 | Below it, labels are unreadable, so `RENDER_PNG_SCALE_LIMIT` refuses the render; exit 2 |

The entity and relationship limit is an upper bound, not a promise that a view fits. The pixel limit applies to the full-size image, so it can refuse a view inside 200 / 300, most often one with many icons and labeled edges, and a PNG cannot pass by being shrunk first. M4-04 sizes these numbers from icon views. A file over 16 MiB also exits 2. Time, memory and temporary storage exit 4, because host load can move them.

**Publication (FR-043, NFR-003, NFR-010).** `render` creates a missing output root with mode 0700. An existing root must be a real directory owned by the user and not writable by group or others, and a symbolic link or `..` anywhere in its path is refused. Access is held by descriptor. A random-suffix bundle name means no render overwrites another. Scratch lives in a hidden `.request-*` directory, which is removed on success, failure and SIGTERM, SIGINT or SIGHUP. SIGKILL cannot run cleanup, so it can leave one behind. Nothing is published until these pass:

- The PNG's chunks and checksums, and the pixel limit.
- The PNG's size against the SVG's. A uniform shrink to at least half size is disclosed, and anything else fails.
- An allowlist over the final SVG's elements and attributes. Every `image` must be a base64 PNG whose digest is one of this render's verified icons; a script, an event handler, an external reference, a `style` or a document type fails.
- Every selected entity, relationship, label, title line and icon really being in the SVG. Graphviz exits 0 even when an image cannot load, so its exit status proves little here.
- No distortion: uniform root scaling, no rotation, and `preserveAspectRatio` that keeps each icon's proportions, as Azure's terms require.

The bundle is then written to a stage directory, read back and renamed into place.

| File | Holds |
|---|---|
| `diagram.svg` | Portable image with icons embedded. Text stays text and names Noto first, so a viewer without those fonts falls back and its metrics can differ |
| `diagram.png` | The same layout as a raster, at the `png.scale` the manifest records |
| `model.json` | The exact input bytes |
| `view.json` | The view, its excluded IDs and the normalized graph |
| `diagnostics.json` | Validation and render warnings |
| `manifest.json` | FR-047: package, schema, catalog, engine and font versions, input digest, mode, draft state, limits, isolation, icons with their digests, rights, PNG size and scale, and output checksums. It holds no timestamp or host path, so only `bundle_id` differs between repeat renders |

**Strict and lenient (T-007).** Strict rejects an unknown `service_type` and draws nothing. Lenient draws it in a dashed frame with the catalog's approved generic symbol, keeping its provider, type and name, and adds `RENDER_GENERIC_FALLBACK`. A lenient image always carries a visible `DRAFT` line, and the manifest records `draft` and each fallback. A provider icon is never borrowed.

**Rights (FR-052).** `rights` in the manifest and in the result covers only the packs this image really uses, with their status, license, attribution and conditions. An image using a private-use pack carries `private_use_only: true`, the D-018 limit and O-002, in the bundle and as a line in the image itself, since an image can leave its bundle. A bundled pack's attribution is drawn the same way. Icons delivered by `diagrams` keep their terms in the manifest.

Bundled fonts are Noto Sans 2.015 and Noto Sans Thai 2.002 under the SIL Open Font License, recorded in `catalog_data/assets.json`. Rendering downloads nothing, and it needs no second model call.

## Quality gate and trust

[Workflow](../../.github/workflows/quality-gate.yml) runs only explicit owner actions on this repository's main/codex branches, plus owner-created same-repository PRs. Fork/external PR actions are not scheduled on the personal runner. Checkout/upload actions are pinned to verified upstream commits, repository permissions are read-only and checkout credentials are not persisted. Dependencies use the locked native environment; see [uv's CI guide](https://docs.astral.sh/uv/guides/integration/github/), [checkout](https://github.com/actions/checkout) and [upload-artifact](https://github.com/actions/upload-artifact).

Portable documentation links must resolve inside the repository; historical host paths are provenance text, with repository-relative evidence copies for actual links. Every implemented lane runs: docs/traceability and frozen proof hashes, narrow credential patterns, Ruff lint/format, strict mypy, actionlint, schema/core tests, catalog and license checks, provider semantics, render security, render smoke, Claude plugin package contract, core package build and wheel contents. Missing tools, timeout or any failed lane fails the aggregate. Reports identify exact checkout SHA, dirty state, lock/source hashes and future checks as deferred, never passed. Report retention is 14 days. The per-run Python environment is removed after the job. This is a core package build, not M5 plugin-package acceptance. Read-only GitHub API verification found only the owner as collaborator and fork-PR workflows disabled at the S05 snapshot; these server-side access settings complement the actor guards. An editable workflow alone is not a tamper-resistant trust boundary.

Credential patterns are a narrow working-tree check, not an entropy/history scan or security audit. Static typing/lint cover implemented core/scripts/tests; historical S04 spike source remains frozen and separately reviewed. Tests/CI contain synthetic architectures. Current private-plan limitations still require manual review/merge discipline. Separate model review is recorded outside the pipeline without paid model API calls.
