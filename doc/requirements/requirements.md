# Cloud Architecture Diagram Plugin Requirements

Document: CADP-REQ-001 | Revision: 0.9 | Updated: 2026-11-02

Status: Draft baseline with confirmed granularity/style and per-machine local-runtime direction; product implementation and release acceptance remain pending.

## 1. Authority and release scope

This is the single product requirement baseline. Planning documents describe delivery and evidence; they do not replace these requirements. `P0` is required for the first usable release. `P1` is a subsequent improvement unless explicitly selected into a milestone. `Deferred` is outside the first release.

The user's current request takes precedence over the supplied v1.1 draft. In particular, **ChatGPT Work first, Claude Code later** replaces the attachment's Claude Cowork target. The attachment's statements marked “Accepted Design” are input proposals, not evidence of approval. See [source reconciliation](../project-management/decisions.md#source-reconciliation).

### First release

- A personal ChatGPT Work plugin that turns architecture requests into reviewable structured models and SVG/PNG diagrams.
- AWS, Azure, GCP, Huawei Cloud, and on-premises support, including hybrid and multi-cloud views.
- A portable Python core using `mingrammer/diagrams` and Graphviz, versioned catalogs, approved icon assets, and a CLI for development/CI.
- An installable personal plugin usable across machines, containing a Work adapter, bundled workflow skill and local renderer setup. D-013 supersedes the central-server choice: install the runtime on each machine using the plugin, with no required public rendering MCP or hosted renderer. Native Python/script execution is the default; Docker is optional for development/CI and is not an end-user prerequisite. The owner confirmed the separate ChatGPT Work mode/page as the first-release target; Codex evidence alone is insufficient. Verify Work Desktop local execution first; supported modes and per-machine prerequisites must be proven.
- Iterative edits that retain stable resource IDs and return the updated source with the images.

### Confirmed architecture depth and visual direction (S01)

Release 1 targets **solution architecture overall, with detailed Kubernetes architecture**. General coverage includes network/subnet, compute, database/storage, security/identity, connectivity and observability. Kubernetes includes cluster/control-plane context, node pools/groups and nodes, namespaces, workloads/Pods, Services/Ingress, storage, configuration references and security relationships as defined in section 6.1. Detailed device/route configuration remains later expansion. Existing explicit minimum-catalog items, including Azure NIC, remain required; selected overviews may disclose omitted detail while explicit Kubernetes detail views retain the requested elements and canonical identities.

Use a white-background starting point and provider-aware iconography, labels, boundary notation and layout conventions close to the reference architectures published by each cloud provider. Use approved assets and record selected source/version references; comparable style is assessed against those examples. This is a fidelity goal, not pixel-identical reproduction or provider certification. Hybrid diagrams keep provider-recognizable elements with a consistent cross-provider legend; on-premises uses clear neutral infrastructure notation. The working conventions and official source links are in the [S01 record](../project-management/evidence/S01-release-scope.md#5-confirmed-visual-direction-and-official-references).

### Deferred

Claude Code adapter; Claude Cowork; cloud inventory/discovery; IaC import; deployment/provisioning; cost estimation; enterprise architecture repository; compliance certification; drag-and-drop editing; real-time collaboration; public marketplace submission; full coverage of every provider service.

## 2. Users and workflow

Primary users are cloud/solution architects, infrastructure engineers, and the project owner.

1. Request an architecture or supply a model. English and Thai requests/labels are supported; documentation remains English.
2. The host model identifies providers, intended relationships, and missing material details. It records assumptions and asks about uncertainty that changes architecture meaning.
3. Resolve resource types through the catalog, validate the model, and select a view.
4. Render through controlled tools; return an inline preview where supported, downloadable SVG/PNG, source JSON, and diagnostics.
5. Apply requested changes to the same model, disclose meaningful changes, and regenerate.

The plugin does not invent deployed resources, security controls, or connectivity. Optional design suggestions must be identified as suggestions before inclusion.

## 3. Product structure

```text
ChatGPT Work: skill + host model
              |
     versioned architecture JSON + selected view
              |
     platform adapter / controlled tool interface
              |
     schema + semantic validation
              |
     taxonomy + provider catalogs + licensed local icons
              |
     view builder -> diagrams -> Graphviz
              |
     SVG + PNG + model + view + diagnostics + manifest
```

Keep core and platform adapters separate. Start by wrapping the upstream dependency; an upstream fork is unnecessary unless a verified limitation requires it. A plugin manifest alone is not a runtime installer. Graphviz is a separate dependency in the [upstream installation guide](https://diagrams.mingrammer.com/docs/getting-started/installation).

The plugin is the installable product; its skill supplies instructions/references, and its execution tools invoke the renderer. This follows the [OpenAI plugin/skill distinction](https://learn.chatgpt.com/docs/skills-and-plugins). Cross-machine use is confirmed user intent. D-013 selects per-machine local execution and supersedes D-012's central-server route. The plugin must include a reproducible installer/preflight for its native local runtime and support direct controlled script execution. Local stdio MCP is a helper-process interface, not a central/listening server. This does not guarantee automatic installation/dependency sync or support for cloud-only chats. M0 must prove the selected local Work mode and artifact retrieval. See the [S04 runtime investigation](../project-management/evidence/S04-runtime-and-hosting.md).

## 4. Functional requirements

### Model and views

| ID | Priority | Requirement |
|---|---|---|
| FR-001 | P0 | Accept UTF-8 JSON. YAML is a P1 adapter using safe parsing into the same model. |
| FR-002 | P0 | Validate a versioned schema before rendering; reject unsupported versions clearly. |
| FR-003 | P0 | Represent scopes, boundaries, resources, placement, typed relationships, metadata, and selected views. |
| FR-004 | P0 | Require stable IDs and explicit references; reject duplicates, dangling references, and containment cycles. |
| FR-005 | P0 | Natural-language authoring produces data. Never execute user/LLM-authored Python or expressions. |
| FR-006 | P0 | Default to strict validation. Lenient draft mode permits only declared recoverable fallbacks and labels the result as a draft. Structural, security, and known semantic errors remain fatal in both modes. |
| FR-007 | P1 | Provide overview, network, deployment, security, and data-flow view presets. P0 permits explicit views without all presets. |
| FR-008 | P0 | Export the canonical model and selected view with each render. |

### Provider coverage

| ID | Priority | Requirement |
|---|---|---|
| FR-010 | P0 | AWS catalog and approved native icons for the minimum coverage in section 6. |
| FR-011 | P0 | Azure catalog and approved native icons for section 6. |
| FR-012 | P0 | GCP catalog and approved native icons for section 6. |
| FR-013 | P0 | Huawei catalog and curated service icons through controlled custom nodes. |
| FR-014 | P0 | On-premises catalog, native icons where suitable, and draw.io-type generic symbols/compositions for the eight identified gaps. Preserve semantic type labels, applicable source conditions and attribution; prepare permitted local assets for the existing renderer. |
| FR-015 | P0 | Combine all five environments in one model and selected views. |
| FR-016 | P1 | Version aliases, historical names, lifecycle status, and regional variants. |
| FR-017 | P1 | Add enterprise catalogs without changing renderer code. |
| FR-018 | P0 | Support the detailed Kubernetes inventory in section 6.1 across EKS, AKS, GKE, CCE and on-premises Kubernetes. Provide explicit detail views from the same canonical model as the cloud overview, preserving IDs and provider/cluster context. |

### Semantics and relationships

| ID | Priority | Requirement |
|---|---|---|
| FR-020 | P0 | Separate ownership, geography, networking, security, deployment, and physical placement. |
| FR-021 | P0 | Render appropriate provider/account/subscription/project, region/zone, network/subnet, security zone, data center/rack, cluster, and environment groups. |
| FR-022 | P0 | Enforce documented constraints for supported resource types. Visual nesting must not redefine ownership or attachment. |
| FR-023 | P0 | Typed directed/undirected relationships support labels, protocol, purpose, and optional security metadata. |
| FR-024 | P0 | Represent users, Internet, partners, SaaS, and external systems. |
| FR-025 | P0 | Preserve requested security, identity, routing, and operational components. Disclose excluded IDs when a view selects only part of the model; never silently drop components to improve layout. |
| FR-026 | P1 | Expand relationship vocabulary: dependency, replication, monitoring, management, routing, attachment, deployment, and location. |
| FR-027 | P1 | Emit evidence-based exposure/cross-boundary warnings without claiming that edges prove real reachability. |
| FR-028 | P0 | Display supplied HTTPS/port, VPN, peering, replication, and flow labels without changing their meaning. |
| FR-029 | P0 | Validate Kubernetes cluster/namespace scope, workload ownership, declared node placement, Service/Ingress targets and storage/configuration/security references separately. Distinguish management, membership, scheduling, policy and traffic relationships; never invent observed placement, controller availability or effective reachability. |

### Rendering and catalogs

| ID | Priority | Requirement |
|---|---|---|
| FR-040 | P0 | Produce valid SVG and PNG. SVG is portable with required icon content embedded or packaged in a verified self-contained form. |
| FR-041 | P0 | Use controlled renderer code, allowlisted classes/assets, and Graphviz. |
| FR-042 | P0 | Support top-bottom/left-right layouts, nested groups, readable labels, legends, and basic edge styles. |
| FR-043 | P0 | Return structured diagnostics and usable artifact references; do not report success for missing/partial artifacts. |
| FR-044 | P1 | Add PDF/DOT exports after testing their safety and portability. |
| FR-045 | P0 | Allow only bounded style/layout values; reject arbitrary Graphviz attributes, HTML labels, paths, and executable directives. |
| FR-046 | P0 | Enforce input/graph limits. Oversized inputs receive an actionable error or explicit suggestion to split views. Automatic overview/detail generation is P1. |
| FR-047 | P0 | Export engine, schema, catalog, asset/font versions, input digest, output checksums, and validation mode in a manifest. |
| FR-048 | P0 | Render provider-aware visuals close to selected official architecture references, including approved icon appearance, native service labels and appropriate grouping/connection conventions. Record source/version/date and material deviations. Preserve correct model semantics when layout conventions differ. |
| FR-050 | P0 | Resolve provider/type/version through a catalog to an allowed bundled asset or controlled native class. |
| FR-051 | P0 | Package approved Huawei and on-premises assets; no render-time icon downloads. |
| FR-052 | P0 | Record original source URL, license/usage terms, redistribution evidence, attribution, asset version/date, and checksum for every external icon pack and custom asset. Preserve dependency notices. |
| FR-053 | P0 | Strict mode rejects unknown service types. Lenient mode may use an approved generic icon while retaining provider/type/label and emitting a warning. Unknown providers and unsafe paths always fail. |
| FR-054 | P1 | Resolve aliases only with provider/context; ambiguous “ECS” must not choose a provider silently. |
| FR-055 | P0 | Expose schema/catalog/capability discovery to the host and CLI; return bounded, filterable catalog results. |

### ChatGPT Work integration

| ID | Priority | Requirement |
|---|---|---|
| FR-060 | P0 | Install and invoke the personal plugin with its local runtime in the supported Work Desktop/local execution mode; test actual tool discovery and output delivery there. Cloud-only compatibility is not assumed. |
| FR-061 | P0 | The skill guides catalog lookup, assumption handling, validation, rendering, and edits that preserve IDs. |
| FR-062 | P0 | Return preview where supported and retrievable SVG/PNG/source/diagnostics. Verify actual local Work file access and attachment/export; returning an inaccessible renderer path is insufficient. |
| FR-063 | P0 | Tool results distinguish success, validation failure, runtime failure, timeout, and unavailable artifact, with stable codes and actionable messages. |
| FR-064 | P0 | Install/preflight the native local Python/Graphviz/assets/fonts runtime on each supported machine without requiring Docker; verify execution permissions and local Work transport. Document OS/runtime prerequisites, first-install downloads, offline rendering behavior and supported host modes. |
| FR-065 | P0 | Keep the core independent of Work-specific APIs so a later Claude Code adapter reuses its model, catalogs, tests, and renderer. |
| FR-066 | P0 | Distribute an identifiable, versioned plugin through a supported installation/enablement route. Demonstrate its complete local Work diagram workflow from two supported machines with independently installed runtimes; document any per-machine setup/authentication. A standalone skill folder or manual source checkout is not the final user deliverable. |

## 5. Canonical model and taxonomy

The following is the product contract outline. M1 implements the [executable core JSON Schema](../../schemas/architecture-v1.schema.json) and [field/validation guide](../design/core-contract.md). The core result discloses pending catalog/provider/render checks; those later layers remain required. Product scope and requirement IDs are unchanged.

| Entity | Required meaning |
|---|---|
| Model metadata | `schema_version`, diagram ID/title, environment, assumptions, optional description |
| Scopes | ID, provider, kind, name, optional meaningful administrative parent |
| Boundaries | ID, provider, kind, name, scope references, and typed boundary relations |
| Resources | ID, provider, service type, primary taxonomy ID, display name, applicable properties |
| Kubernetes context | Cluster identity, namespace only for namespaced kinds, provider-specific node pool/group membership, workload ownership, declared scheduling/selection and typed dependency references |
| Placement | Separate `scope_refs`, `location`, `network_attachments`, `security_boundaries`, `deployment_context` |
| Relationships | ID, source/target references, kind, direction, optional protocol/label/security metadata |
| Views | ID/title, selected entity/relationship IDs, grouping policy, direction, allowed style values |

Use one primary taxonomy ID per type. Preserve native provider/service identity; a shared taxonomy category never establishes functional equivalence. Presentation groups cannot override canonical references. Multi-network resources retain every attachment even when a view shows one visual placement.

Initial taxonomy IDs, grouped for compact reference:

```text
governance.scope            location.site             onprem.facility
network.boundary            network.subnet            network.routing
network.connectivity        network.load_balancing    edge.delivery
compute.vm                  compute.physical          compute.containers
compute.serverless          application.platform      data.relational
data.nosql_cache            data.analytics_ai         storage.object
storage.block_file          integration.messaging     identity.access
security.control            security.secrets_keys     operations.observability
operations.backup_dr
```

Taxonomy availability does not require every provider to implement every category in release 1. Each catalog record includes a stable type ID, provider, display name, taxonomy, capabilities, documented scope/placement rules, renderer mapping, icon/license reference, status, and catalog version. Aliases are optional until P1. Schema/catalog breaking changes require migration guidance and a version change.

## 6. Minimum release catalog

These are required catalog targets, not claims that mappings/assets have already been verified. M2 freezes exact type IDs, product variants, current documentation, and icon mappings in a machine-readable inventory. A supported item needs a valid record, approved visual representation, applicable rules, and positive/negative fixtures. Scope/group items may use labeled boundaries instead of service icons.

| Environment | Minimum scope and services |
|---|---|
| AWS | Account, region, AZ, VPC, subnet; EC2, ALB, EKS, RDS, S3, IAM, Security Group, NAT Gateway, Internet Gateway, Site-to-Site VPN, Direct Connect, CloudWatch |
| Azure | Tenant, subscription, resource group, region, VNet, subnet; VM, NIC, Application Gateway, AKS, Azure SQL Database, Blob Storage, Entra ID/Azure RBAC context, NSG, Azure Firewall, NAT Gateway, VPN Gateway, ExpressRoute, Azure Monitor |
| GCP | Organization/folder/project, region/zone, VPC, subnet; Compute Engine, GKE, selected Cloud Load Balancing product, Cloud SQL, Cloud Storage, IAM, VPC firewall rule, Cloud NAT, Cloud VPN, Cloud Interconnect, Cloud Monitoring/Logging; Shared VPC host/service-project references |
| Huawei Cloud | Account, IAM project, enterprise-project context where applicable, region/AZ, VPC, subnet; ECS, ELB, EIP, NAT Gateway, CCE, RDS, OBS, IAM, Security Group, API Gateway, FunctionGraph, VPN, Direct Connect, Cloud Eye, LTS |
| On-premises | Site/data center, room/rack, security zone, VLAN, VRF, subnet; router, L2/L3 switch, firewall, load balancer, hypervisor, VM, physical server, Kubernetes cluster, database, NAS, SAN, identity service, backup system, monitoring |

For the eight on-premises gaps, use the [draw.io-type generic mappings](../project-management/evidence/S02-additional-icon-sources.md#2-drawio-type-symbols-for-the-eight-on-premises-gaps): load balancer, hypervisor, VM, NAS, SAN, identity service, backup and monitoring. Some types use labeled compositions rather than a dedicated icon. Keep NAS/SAN, hypervisor/VM and monitoring/display semantics distinct. This is an asset/style choice; diagrams/Graphviz remains the runtime backend.

Support networking, compute, containers, data/storage, identity/security, connectivity, and observability in every environment. Expanded analytics/AI, messaging, vendor appliances, and additional database variants are P1.

### 6.1 Detailed Kubernetes coverage (P0)

Use a shared Kubernetes catalog alongside the five provider catalogs. Kubernetes is a platform layer, not a sixth cloud provider: retain the hosting provider and cluster references. Exact type IDs, supported API versions and provider-specific node-pool/group mappings are M2 decisions.

| Area | Minimum detailed representations |
|---|---|
| Cluster and compute | Cluster, logical control-plane boundary, provider node pool/group where applicable, worker Node, declared zone/subnet attachment |
| Scope and placement | Namespace, cluster-scoped vs namespaced identity, explicit workload ownership and Pod-to-Node assignment when supplied |
| Workloads | Deployment, ReplicaSet, StatefulSet, DaemonSet, Job, CronJob and Pod; replica counts/labels where supplied |
| Traffic | Service with declared type/ports/targets, Ingress and its controller as separate concepts, links to supplied external load balancer and upstream/downstream services |
| Storage | PersistentVolumeClaim, PersistentVolume and StorageClass, with declared claim/binding/mount relationships |
| Configuration and security | ConfigMap and Secret references, ServiceAccount and NetworkPolicy relationships; no secret values or credentials in diagrams or exported source |

Support these kinds without requiring every diagram to contain all of them. In managed/abstracted modes, do not fabricate hidden control-plane machines, node pools or Pod placement. Preserve namespace grouping separately from node scheduling: a namespace is not a physical child of one worker node. Missing placement may remain unspecified rather than inventing a live topology.

The detailed view must retain supplied security, configuration and storage relationships. The cloud/hybrid overview can represent a cluster compactly and disclose omitted detail; this does not make Kubernetes support cluster-only. Required explicit Kubernetes detail views do not promote all P1 view presets or automatic splitting to P0. Live discovery, manifest import/deployment, arbitrary operator/CRD coverage and low-level component configuration are not required by this diagram-detail change.

Primary semantic references: [components](https://kubernetes.io/docs/concepts/overview/components/), [namespaces](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/), [workloads](https://kubernetes.io/docs/concepts/workloads/), [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/), [persistent volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) and [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/). These define the concepts; M2 still verifies supported versions, controller/network-plugin behavior and provider mappings. Drawing a policy or Ingress object does not prove its runtime enforcement.

### 6.2 Provider icon and semantic acceptance anchors

Huawei native service icons are a release objective, not silently replaceable with generic symbols. If rights cannot be established, record a release blocker and discuss a reduced scope explicitly. Do not infer icon rights from the upstream code license. `Custom` supports local assets in the [upstream guide](https://diagrams.mingrammer.com/docs/nodes/custom).

The [S02 source/rights assessment](../project-management/evidence/S02-icon-sources-and-rights.md) identifies a Huawei color-library candidate covering the named minimum inventory, plus on-premises/Kubernetes candidates and gaps. Huawei redistribution evidence remains unresolved; the research inventory is not a release asset allowlist. This finding does not change the P0 coverage or licensing requirements.

The [user-supplied Huawei pack follow-up](../project-management/evidence/S02-additional-icon-sources.md#1-huawei-repository-assessment) records a 155-PNG community alternative and its VeryIcon usage claim. It is not an adopted replacement or a packaging-rights resolution. Source selection remains evidence-based under FR-052/NFR-004.

#### Semantic anchors

- AWS subnets are AZ-scoped: test incompatible subnet/AZ references. [AWS subnet documentation](https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html).
- Azure administrative ownership and VNet/subnet attachment are separate dimensions. Use regional VNet constraints as documented; verify NIC/resource-group details during M2. [Azure network planning](https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-vnet-plan-design-arm).
- GCP VPC networks are global and subnets are regional; support Shared VPC references without forcing one ownership tree. [GCP VPC documentation](https://docs.cloud.google.com/vpc/docs/vpc).
- Huawei IAM projects, enterprise projects, service scope, and zone placement require per-service primary-source verification in M2; no universal hierarchy is assumed. Current Huawei documentation and icon rights remain unresolved.
- On-premises physical placement, virtualization membership, and logical network/security membership can overlap; test these independently.

## 7. Non-functional requirements

| ID | Priority | Requirement and evidence |
|---|---|---|
| NFR-001 | P0 | Reproduce materially equivalent output from the same input and pinned runtime/catalog/assets/fonts. Normalize generated IDs/timestamps for structural comparison; byte-identical images across platforms are not promised. |
| NFR-002 | P0 | No arbitrary code, dynamic imports from input, shell interpolation, remote assets, or uncontrolled Graphviz options. Render with network access disabled where the selected runtime permits. |
| NFR-003 | P0 | Confine input/output/assets to controlled roots; reject traversal, symlink escapes, unsafe URLs, and output collisions. Validate exported SVG for scripts, external references, and unsafe links. |
| NFR-004 | P0 | Ship license/attribution inventory for dependencies and external visual assets. Unknown redistribution rights block packaging of that asset. |
| NFR-005 | P0 | Machine-readable diagnostics include severity, stable code, entity/field reference, message, and remedy. |
| NFR-006 | P0 | Never silently omit requested security components or hide invalid semantics through layout/fallback behavior. |
| NFR-007 | P1 | Benchmark small (<=30 nodes/50 edges) and medium (<=100/150) fixtures with target render times of <5 s and <15 s; record p50/p95, cold/warm runs, fonts, versions, and reference machine before setting a release threshold. |
| NFR-008 | P1 | Stress-test 200 nodes/300 edges and assess readability; a stable render alone is insufficient for a useful large view. |
| NFR-009 | P0 | Bound parsing, render time, process memory, temporary storage, payload/label lengths, and artifact sizes. Kill timed-out child processes and clean request directories. Freeze numeric limits in M0/M1 using measurements. |
| NFR-010 | P0 | Produce collision-safe artifact bundles and checksums; publish a success manifest only after all requested outputs validate. |
| NFR-011 | P0 | Automate schema, semantic, catalog, security, rendering, and package checks in CI as their components arrive. See the [quality gate plan](../project-management/quality-gate.md). |
| NFR-012 | P1 | Extend catalogs through validated data packs with explicit compatibility versions. |
| NFR-013 | P0 | For remote execution: authenticate requests, isolate requester artifacts, use bounded retention and protected retrieval, avoid logging full architecture payloads, and document data location/deletion. Local mode uses per-request controlled directories. |
| NFR-014 | P0 | Handle English/Thai UTF-8 labels with licensed bundled/declared fonts; visually verify Thai rendering. The baseline remains English. |
| NFR-015 | P0 | Runtime rendering has no mandatory second LLM/API call or paid model key. The host model authors the data; validation/rendering are deterministic. |

## 8. Release acceptance matrix

All P0 requirements must pass, including those not repeated below. Attach requirement IDs to fixtures/checks; retain evidence at the release commit. `T-*` are planned scenarios, not test results.

| Scenario | Expected evidence | Primary milestone |
|---|---|---|
| T-001 AWS three-tier | SVG/PNG, valid subnet/AZ mapping, multi-subnet ALB representation verified against its product rules, requested security/monitoring retained | M4 |
| T-002 Azure hub/spoke | Ownership vs attachment preserved, explicit peering/VPN, supplied firewall/NSG shown | M4 |
| T-003 GCP Shared VPC | Global network/regional subnets, host/service-project references and workload placement validated | M4 |
| T-004 Huawei web app | ECS/ELB/VPC/subnet/RDS/OBS diagram; every required Huawei catalog item resolves with approved icon evidence | M4 |
| T-005 On-premises | Separate physical and logical views; rack, VLAN/VRF, security zone, and compute memberships retained | M4 |
| T-006 Five-environment hybrid | All five environment types present; only explicitly modeled connectivity shown, trust/link labels visible | M4 |
| T-007 Unknown type | Strict failure; lenient generic fallback warning and draft marking; no provider substitution | M3 |
| T-008 Invalid model | Duplicate/missing IDs, cycles, bad scope/attachment fail with actionable diagnostics in both modes | M1/M2 |
| T-009 Malicious input | Code, path/symlink escape, remote icon, SVG/Graphviz injection, oversize input and timeout fixtures fail safely | M3/M5 |
| T-010 Cross-machine plugin and reproduction | Install/enable the same plugin version on two supported machines and complete the local Work diagram workflow on both with independently installed runtimes, including artifact retrieval and documented setup/auth. Separately reproduce the core from a clean runtime; compare model/view semantics and versions | M6 |
| T-011 Work integration | Install, discovery, valid/invalid tool calls, authentication where applicable, visible preview, and retrieved complete bundle in the verified local Work mode | M5/M6 |
| T-012 Large view | P0 bounded rejection above limits; P1 200/300 stability and split-view/readability evaluation | M4 |
| T-013 Iterative edit | Stable IDs, changed requirements reflected, unrelated relationships retained, updated source returned | M5 |
| T-014 Language and privacy | English/Thai label inspection; remote artifact isolation/expiry and payload-log checks where applicable | M4/M5 |
| T-015 Packaging and CI | Clean install, notices/assets included, all applicable checks at release SHA, completed review evidence | M6 |
| T-016 Provider visual fidelity | Compare AWS/Azure/GCP/Huawei reference samples against selected official examples for icons, labels, boundaries and layout. Inspect hybrid consistency and neutral on-premises notation; document deviations and obtain actual visual acceptance | M4/M6 |
| T-017 Detailed Kubernetes | Exercise the section 6.1 catalog and provider mappings; render shared-model overview/detail views with namespace/workload/Pod/node relations, Service/Ingress path and PVC/PV relationships. Reject wrong-scope/cross-cluster references; preserve IDs across edits/views and exclude secret payloads. Include positive/negative mapping fixtures for EKS, AKS, GKE, CCE and on-premises | M1/M2/M4/M5 |

Owner acceptance requires inspection of the six reference scenarios T-001 through T-006 and an actual Work session. A green pipeline alone does not establish usable integration or correct architecture meaning.

The [S01 scenario briefs](../project-management/evidence/S01-release-scope.md#4-reference-scenario-briefs) provide working authoring requests, inspection points and iterative-edit checks for T-001..006. Architecture granularity and visual direction are confirmed in S01; the actual rendered scenarios remain subject to M4/M6 inspection and acceptance.

## 9. Change control

Keep existing requirement IDs when editing. Record changed priority, scope, rationale, affected tasks/tests, and owner decision in the [decision log](../project-management/decisions.md). Store implementation results separately from proposed behavior. Do not mark a milestone complete from a document update alone.
