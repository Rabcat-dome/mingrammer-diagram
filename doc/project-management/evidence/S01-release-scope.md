# S01 — Release Scope and Reference Scenario Briefs

Updated: 2026-10-31 | Task: M0-01 | Status: Complete for scope planning; implementation and visual acceptance are later work.

This is a discussion/result record for [S01](../session-plan.md), not a second requirement baseline or executed test report. Product authority remains the current [CADP-REQ-001 baseline](../../requirements/requirements.md). The owner selected solution architecture overall, then explicitly corrected Kubernetes to detailed architecture (D-009), with visuals close to each provider's published conventions. The later S02 draw.io-type on-premises preference is D-010. Other technical recommendations are not blanket-approved by those answers.

## 1. Confirmed direction carried forward

- Deliver an installable personal plugin usable across machines, with any workflow skill bundled inside it.
- Support AWS, Azure, GCP, Huawei Cloud and on-premises; add Huawei icon coverage.
- Target ChatGPT Work first and keep a later Claude Code adapter possible.
- Keep documentation English and provide cross-machine handoff/activity records.
- Release 1 uses solution architecture overall (D-007) with detailed Kubernetes as an explicit exception (D-009). The owner's correction supersedes the earlier cluster-only limit.
- Use a white-background starting point close to each cloud provider's published architecture conventions (D-008), including recognizable native icons, service labels and boundary/layout treatment.

Remote hosting, exact Work modes, icon rights, runtime versions and runner eligibility remain S02–S04 decisions/investigations. S01 does not provision infrastructure or implement the core.

## 2. Release boundary and working catalog

Retain every named service/scope in requirements section 6, including the shared detailed Kubernetes inventory in section 6.1. Do not remove a provider, silently narrow Huawei coverage, or expand the release to every service exposed by upstream diagrams. M2 will freeze exact type IDs and supported product/API variants against current primary sources.

| Dimension | First-release interpretation | Later expansion |
|---|---|---|
| User outcome | Request, validate, render and iteratively edit architecture; retrieve SVG/PNG plus source/view/diagnostics/manifest | Inventory discovery, IaC import, deployment and cost estimation remain deferred |
| Provider breadth | All five environments and the existing minimum inventory | Additional service families and product variants |
| Architecture depth | Solution architecture overall, with detailed Kubernetes views | Detailed device configuration and packet-level routing |
| Kubernetes | Cluster/control-plane context, node pool/group, Node, Namespace, workload/Pod, Service/Ingress/controller, storage/configuration/security references | Live inventory, manifest import/deployment, arbitrary operators/CRDs and low-level component configuration |
| Explicit resource detail | Retain any currently required item, including Azure NIC, and explicit requested components; overview/detail visibility is a view choice | A uniform low-level resource inventory across every provider |
| Multiple views | Explicitly selected views are P0; use separate views to explain overlapping physical/network/ownership dimensions | Automatic splitting and all named view presets stay P1 |
| Provider fidelity | Provider-native identity and verified placement rules; no automatic cross-provider substitutions | Broader aliases or enterprise packs after their P1 work |

Solution architecture overall plus detailed Kubernetes is confirmed by the owner. The cloud catalog is retained and the Kubernetes detail inventory is added; exact type/API variants remain M2 work. These decisions do not demote existing P0 requirements or permit hiding a requested security component. An unknown or unverified capability is reported accurately; an icon alone does not establish semantic support.

## 3. Owner answers and recorded decisions

| Choice | Options presented | Recommendation | Recorded answer |
|---|---|---|---|
| Release granularity (O-008) | Solution architecture; detailed infrastructure; both from release 1 | Overall solution architecture, retaining explicit required details | Owner initially selected solution architecture, then corrected Kubernetes to detailed architecture; D-009 supersedes the original cluster-only limit in D-007 |
| Visual starting point (O-004) | White/provider-icon style; organization-specific theme; decide from first real sample | White background, provider icons and clear boundaries | Owner selected the first option and requested fidelity to each provider's published website examples; recorded as D-008 |

These answers were received through the two preference questions in this chat. Actual rendered sample acceptance remains M4/M6 work. S02/S03 research can proceed, followed by S04 runtime evidence.

The subsequent Kubernetes correction is release-1 scope. FR-018/FR-029/T-017 and M2-06/M4-05 now cover the shared detailed catalog, semantics and rendered subviews. The minimum inventory is authoritative in requirements section 6.1, not duplicated here. Provider-specific node pools/groups must be mapped according to their actual hosting mode; a logical namespace and a worker's physical placement are separate dimensions.

## 4. Reference scenario briefs

These are synthetic architecture-intent briefs for T-001..006. They are not claims about deployed infrastructure or completed renders. M2 verifies service-specific constraints; M4 creates the model fixtures and rendered acceptance samples. Regions, product variants, IDs and detailed network settings are chosen in those tasks rather than invented here.

### T-001 — AWS three-tier web application

Authoring request:

> Draw an AWS web application in one account and region across two availability zones. Include an ALB, application EC2 instances, RDS, S3, Security Groups and CloudWatch. Show the supplied subnet attachments, traffic directions and HTTPS/application-to-database labels. Preserve an explicitly supplied NAT/egress path.

- Inspect: account/region/network/AZ context; one logical ALB with its actual supplied attachments; application/data path and specified security/operations components.
- Reject: fabricated links, lost attachments, duplicated ALB interpreted as extra deployed resources, or a layout silently dropping security nodes.
- Edit check: rename the application tier and add an explicitly requested instance without replacing existing IDs.
- Kubernetes companion: use the same account/network model with an explicitly supplied EKS workload and a detail subview covering node group/Nodes, Namespace, Deployment/Pods, Service/Ingress and requested storage/security references.

### T-002 — Azure hub-and-spoke

Authoring request:

> Draw a hub-and-spoke design with a subscription, separate resource-group contexts, hub/spoke VNets and subnets, explicit peering, Azure Firewall and VPN Gateway. Include a spoke VM/NIC, NSG, Azure SQL Database, Blob Storage, identity context and Azure Monitor. Keep ownership separate from network attachment.

- Inspect: administrative vs network dimensions, explicit hub/spoke links and supplied flow labels; managed service connections follow the stated architecture intent.
- Reject: resource-group ownership inferred from visual subnet nesting, missing NIC/security relationships, or unsupported reachability claims.
- Edit check: add a second spoke with only the requested connections.
- Kubernetes companion: an AKS detail subview preserves the surrounding subscription/VNet model while showing declared node pool/Node placement, namespace/workload traffic and supplied storage/security relationships.

### T-003 — GCP Shared VPC

Authoring request:

> Draw a Shared VPC host project and service project with regional subnets, zonal Compute Engine workloads, a GKE cluster, a selected load-balancing product, Cloud SQL and Cloud Storage. Add a GKE detail view with declared node pools/Nodes, namespaces, workloads/Pods, Service/Ingress and requested storage/security references. Preserve the supplied network and project references.

- Inspect: network scope, regional/zonal placement and host/service-project references against catalog rules; avoid flattening ownership into network membership.
- Reject: treating the VPC as a single-region ownership boundary or silently relocating a service-project workload.
- Edit check: change a workload's requested zone while retaining its ID and validating the supplied subnet compatibility.

### T-004 — Huawei web application

Authoring request:

> Draw a Huawei Cloud web application with its stated account/project/region context, VPC/subnets, ELB, ECS, RDS, OBS, Security Group, EIP and NAT path. Include Cloud Eye and LTS. Use the curated Huawei icons and preserve explicitly supplied links and placements.

- Inspect: service-to-icon mapping and its rights evidence; actual per-service scope/placement; requested security, egress and observability.
- Reject: generic symbols presented as native Huawei icons, unsupported hierarchy assumptions, missing services, or invented network links.
- Edit check: add an explicitly requested CCE cluster with a detail subview showing node pool/Nodes, namespace/workload/Pod, Service/Ingress and supplied storage/configuration/security dependencies. API Gateway, FunctionGraph, IAM and connectivity remain required catalog checks even if not all appear in the web overview.

### T-005 — On-premises physical and logical views

Authoring request:

> Model a data center with a rack, router, switches, firewall, hypervisor, physical server/VMs, Kubernetes cluster, database, NAS/SAN, identity, backup and monitoring. Record the supplied VLAN/VRF, subnet and security-zone memberships. Produce separate physical/logical views and a Kubernetes detail view with declared Nodes, namespaces, workloads/Pods, Service/Ingress and supplied storage/security dependencies, all from the same model.

- Inspect: rack/device placement and logical memberships independently; preserve multi-network and compute-cluster membership across views.
- Reject: a false single containment tree, changed resource identity between views, or undeclared omission of requested components.
- Edit check: move a physical server to a different rack without changing its logical network memberships.

### T-006 — Five-environment hybrid overview

Authoring request:

> Create one overview containing on-premises and AWS, Azure, GCP and Huawei workloads. Use only the supplied VPN/dedicated-link endpoints and business data flows. Label provider/site, trust boundaries, link types and direction. Keep detail in explicit subordinate views where needed.

- Inspect: all five environments visible; explicit links match the model; legends distinguish connectivity from application/data flow; excluded detail is disclosed.
- Reject: an automatic full mesh, a missing environment, unlabeled security boundaries, or apparent connectivity added just for a cleaner layout.
- Edit check: add a stated on-premises-to-Huawei link without changing unrelated relationships.
- Detail access: clusters may stay compact in the hybrid overview, with explicit Kubernetes detail subviews preserving the same IDs and provider/site context.

These six scenario families may produce multiple images. Their Kubernetes detail subviews feed the focused T-017 fixture set across EKS/AKS/GKE/CCE/on-premises. Required kinds do not all need to appear in one image, but each needs catalog/rule coverage. Inspect namespace vs node placement, workload/Pod ownership, Service/Ingress and PVC/PV links, and ensure no secret payload is exported. Reject invalid cluster/namespace references or invented live placement.

## 5. Confirmed visual direction and official references

- White background with provider-specific iconography, meaningful service labels, boundary notation and recognizable reference-architecture layout. Preserve approved icon appearance and usage terms; do not force every cloud into the same decorative template.
- Offer left-right and top-bottom layout; recommend left-right for hybrid overviews and choose each scenario's detail direction from its content. Do not infer semantic hierarchy from layout.
- Distinguish ownership/location/network/security/physical group kinds by explicit labels and a small, consistent visual vocabulary; color alone cannot carry meaning.
- Label edge purpose/protocol when supplied, retain direction, and avoid invented relationships. Prefer separate explicit views over illegible clusters.
- Verify title, labels, icons, boundaries, legend, clipping and line crossings in the exported artifact. English/Thai labels must remain readable at the agreed normal viewing size.
- Keep custom company branding, multiple themes and pixel-identical vendor sample reproduction outside the proposed initial visual baseline unless requested.

The owner confirmed the direction, not a rendered sample. Specific colors/fonts/group treatments are implementation selections to be checked against references. Font/runtime choice belongs to S04; actual sample inspection belongs to S08. FR-048/T-016 now require provider-reference comparison.

Official pages opened on 2026-10-31:

| Provider | Official reference entry points | Project application / remaining work |
|---|---|---|
| AWS | [Architecture icons](https://aws.amazon.com/architecture/icons/) and [Architecture Center](https://aws.amazon.com/architecture/) | Use approved icon families and appropriate architecture grouping. The icon page warns that third-party libraries can be outdated; M2 compares the selected diagrams assets with the approved version. |
| Azure | [Architecture icons and guidelines](https://learn.microsoft.com/en-us/azure/architecture/icons/) and [hub-spoke reference](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke) | Keep recognizable icon appearance and nearby service names. The guide prohibits cropping/flipping/rotation/distortion; compare T-002's grouping and relationship presentation with the relevant reference. |
| GCP | [Official icon library](https://cloud.google.com/icons) and [landing-zone network designs](https://docs.cloud.google.com/architecture/landing-zones/decide-network-design) | Select a documented icon family/version and reference network/project grouping. The library distinguishes current product icons from legacy console icons; avoid silently mixing generations. |
| Huawei | [Well-Architected reference architecture](https://support.huaweicloud.com/intl/en-us/usermanual-architecture/architecture_03_0073.html) and [Design Center element overview](https://support.huaweicloud.com/intl/en-us/productdesc-haydncsf/haydncsf_02_0003.html) | Use published reference examples to select recognizable service/group treatment. The pages do not establish a redistributable icon pack; rights and a consistent asset family remain S02/M2 work. The reference is a paradigm rather than a universal mandatory visual standard. |

These are verified source entry points, not a completed screenshot/asset audit. S02/M2 record usable assets, exact versions, usage terms and differences. S08 selects the relevant example diagrams and retains comparison evidence for icon shape, labels, group boundaries, edge meaning and layout/readability. A clean generic Graphviz output alone does not satisfy the provider-fidelity requirement.

Hybrid views use native provider elements inside their respective contexts with consistent cross-provider spacing, flow labels and legend. For on-premises, retain clear device/site/rack/network/security notation without claiming one cloud provider's design is a universal on-premises standard.

## 6. S01 exit and downstream handoff

| Exit item | Current status |
|---|---|
| Confirmed user constraints carried forward | Recorded from the conversation |
| Minimum catalog recommendation | Existing cloud inventory retained plus detailed Kubernetes under D-009; exact product/API/type freeze remains M2 |
| Six acceptance briefs | Prepared with Kubernetes detail subviews as working M4 inputs; no rendered sample acceptance claimed |
| Granularity and visual direction | Owner answers and Kubernetes correction recorded as D-007/D-008/D-009 |
| Requirement/decision updates from actual answers | Baseline revision 0.4; FR-018/FR-029/T-017 added for detailed Kubernetes; provider-fidelity scope retained; O-008 resolved and O-004 actual visual acceptance deferred |
| S01 completion | Scope-planning work complete; other M0 tasks remain open |

Next action: S02 icon-rights research and S03 repository/runner preflight can proceed independently. S04 proves the runtime and records any reference-style limitations. Start M1 only after applicable M0 exit evidence exists. Owner approval of actual diagrams and the complete release remains later acceptance work.

Validation: revision 0.4 documentation checks passed for ten English Markdown files, 35 local links/anchors, 64 requirement IDs, 17 acceptance scenarios, 32 milestone tasks, 27 decision/proposal/question IDs and six reference families. Checked references, code fences, English-only text, stale cluster-only scope and whitespace passed. No renderer/Work/pipeline test or separate model review was run. No commit/push was performed; the repository had no commits when this session started.
