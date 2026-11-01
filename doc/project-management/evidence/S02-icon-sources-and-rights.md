# S02 — Icon Sources, Rights Evidence and Coverage Gaps

Checked: 2026-10-31 | Task: M0-03 | Status: Research complete; Huawei redistribution evidence remains unresolved.

Scope follows [requirements revision 0.5](../../requirements/requirements.md), including detailed Kubernetes. This is research evidence, not an approved release asset manifest or a legal clearance. The structured [icon inventory](S02-icon-inventory.json) records source commits, Git blob IDs, candidate mappings and limitations. No icon binaries, extracted SVGs or third-party XML libraries are bundled in this repository.

Follow-up: the user supplied a second Huawei repository and requested draw.io-type on-premises symbols. The [additional source assessment/mappings](S02-additional-icon-sources.md) supersede the unresolved symbol-choice status of the eight initial on-premises gaps; asset preparation and Huawei rights evidence remain pending.

## 1. Findings and next action

- A concrete Huawei source is available: [huaweicloud-latam/drawio-libraries](https://github.com/huaweicloud-latam/drawio-libraries). Its color collection has technical candidates for all 17 named Huawei minimum items, including group representations for subnet/security group.
- The audited publisher repository has no license/notice file, GitHub license metadata is null, and its README/release text does not supply a clear extraction/conversion/plugin-redistribution grant. This is an evidence gap under FR-052/NFR-004; it is not a claim that no separate permission exists.
- On-premises coverage can use existing generic candidates and labeled boundaries. Eight neutral device/service concepts need an explicit symbol choice; named product logos must not imply an unspecified deployment product.
- Detailed Kubernetes has 18 directly relevant candidate assets already in diagrams. The upstream Kubernetes icon set explicitly offers Apache-2.0 or CC-BY-4.0; exact origin matches and applicable notices still need to be retained when assets are selected.
- S03 runner preflight and S04 runtime proof can proceed with a separately approved small fixture. Huawei asset packaging cannot be marked cleared from this research alone. No source-permission request was sent.

## 2. Audited sources and rights disposition

| Source | Snapshot and evidence | Disposition |
|---|---|---|
| Huawei LATAM draw.io library | Commit `52c33aa12fb816a5de403da85067e1c0f039b5be`; latest release observed [v3.2](https://github.com/huaweicloud-latam/drawio-libraries/releases/tag/v3.2), published 2025-01-31. Read the [pinned README](https://github.com/huaweicloud-latam/drawio-libraries/blob/52c33aa12fb816a5de403da85067e1c0f039b5be/README.md), release body and complete recursive tree. | Preferred technical candidate; redistribution evidence pending. The publisher describes color icons as matching console/product pages and the line family as no longer maintained. Recommend the color family; do not silently mix families. Corporate authorization/global-official-pack status was not independently established. |
| Huawei InnoStage Workbench documentation | [Official design workflow](https://support.huaweicloud.com/intl/en-us/qs-haydncsf/haydncsf_03_0004.html) describes its element library and export workflow. | Style/workflow reference. Exporting diagrams from that service does not by itself establish a right to redistribute its source icon library inside another plugin. |
| mingrammer/diagrams | Reverified `master` at `8c1446fbfa4a8d88e5c7bca7101ddc5af7933379`; [root MIT license](https://github.com/mingrammer/diagrams/blob/8c1446fbfa4a8d88e5c7bca7101ddc5af7933379/LICENSE). Recursive tree complete; no Huawei provider found. Latest release observed is [v0.25.1](https://github.com/mingrammer/diagrams/releases/tag/v0.25.1), published 2025-11-22. | Renderer/code candidate with MIT notice requirements. Asset presence is technically verified; brand/source-specific provenance remains a separate check. The research snapshot is not the selected dependency version. |
| Kubernetes community icons | Commit `309fa9adfc84a8d04b0817a8b11124bf479a8d5e`; [icon README/license statement](https://github.com/kubernetes/community/blob/309fa9adfc84a8d04b0817a8b11124bf479a8d5e/icons/README.md). It declares a choice of Apache-2.0 or CC-BY-4.0 and separately identifies logo trademark terms. | Recommend recording the Apache-2.0 option for selected standard resource icons, with applicable notices and trademark conditions. No release assets have yet been adopted; do not assume every diagrams image is proven identical to that source. |
| Tabler neutral icons | Commit `ed177a085b652fe04ec4f37ced867c94621e7840`; [MIT license](https://github.com/tabler/tabler-icons/blob/ed177a085b652fe04ec4f37ced867c94621e7840/LICENSE). Ten unbranded SVG candidate paths were checked individually at this commit. | Optional source for neutral on-premises symbols, preserving its notice. The visual fit/type distinction remains M2/M4 work. Not a source for Huawei/vendor-native service icons. |

Public availability is not sufficient redistribution evidence: [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository) distinguishes public visibility/forking from a license to reproduce/distribute. Our packaging disposition above is an application of the existing provenance gate to the evidence found, not a new approval process.

Discovery followed a third-party project's pointer to the original Huawei publisher repository. No mirrored icon pack, marketplace “free use” claim, screenshot or unrelated Huawei service agreement was used as licensing authority.

## 3. Huawei technical mapping candidates

All 15 color XML libraries were read as data at the pinned commit. They contain **262 entries: 254 embedded SVG entries and 8 mxGraph group definitions**. This is not a count of unique services: product variants and groups are separate entries. No source scripts were executed and no conversion/rendering test was performed.

The English/Portuguese READMEs and changelog were also checked, and all 254 SVG payloads were decoded only in memory for rights-related keyword screening; no matching notice was found. This supports the recorded evidence gap but cannot rule out a separate permission agreement. The embedded artwork itself was not visually audited.

The following mapping covers the 17 named minimum items; the complete source paths, exact titles, entry indices and Git blob IDs are in the JSON inventory. Technical match means title/format existence, not visual, semantic or licensing approval.

| Required item | Source library | Candidate representation |
|---|---|---|
| VPC | Networking; Groups | Service SVG and VPC group |
| Subnet | Groups | Labeled group; no standalone service SVG found in the audited color entries |
| Security Group | Groups | Labeled group; no standalone service SVG found in the audited color entries |
| ECS | Compute and Containers | Elastic Cloud Server SVG |
| ELB | Networking | Elastic Load Balance SVG |
| EIP | Networking | Elastic IP SVG |
| NAT Gateway | Networking | NAT Gateway SVG |
| CCE | Compute and Containers; Groups | Service SVG and cluster group; detailed internal resources use the Kubernetes catalog |
| RDS | Databases | Generic RDS SVG; product-specific RDS variants are also present, with selection deferred to M2 |
| OBS | Storage | Object Storage Service SVG |
| IAM | Management and Governance | Identity and Access Management SVG |
| API Gateway | Middleware | APIG SVG |
| FunctionGraph | Compute and Containers | FunctionGraph SVG |
| VPN | Networking | Virtual Private Network SVG |
| Direct Connect | Networking | Direct Connect SVG |
| Cloud Eye | Management and Governance | Source title uses Cloud Eye Service / CES |
| LTS | Management and Governance | Source title contains the typo `Log Tank Servce (LTS)`; retain provenance text while normalizing the user-facing label against current service documentation in M2 |

Account, IAM-project and enterprise-project context can be explicit renderer groups. Region/AZ group definitions exist. Group availability does not establish a universal cloud hierarchy. Recreate appropriate grouping from the canonical model; do not execute or import arbitrary mxGraph payloads as renderer configuration.

### Rights evidence needed before Huawei packaging

The evidence must cover extracting the embedded SVGs, local format conversion where required, bundling versioned assets in the private plugin and/or renderer, producing downloadable architecture diagrams, and the applicable attribution/trademark/modification conditions. A permission record must identify the asset family/version and a rights holder or authorized publisher. Another “MIT” wrapper repository cannot grant rights it does not hold.

Prepared request wording (not sent):

> Please identify the license or permission applicable to the color libraries in huaweicloud-latam/drawio-libraries at revision 52c33aa12fb816a5de403da85067e1c0f039b5be. We plan to extract SVGs, convert them locally if needed, bundle them in a private architecture-diagram plugin or authenticated renderer, and distribute generated diagrams. Please confirm the permitted uses and required attribution, trademark and modification conditions.

No asset is cleared by asking the owner to approve an unknown license. Existing written permission or a clearly licensed source can resolve the evidence gap; otherwise it remains an M2-03/package release issue. The requirement for recognizable Huawei service assets is retained.

## 4. On-premises coverage and gaps

The diagrams snapshot has 173 on-premises, 27 generic and 46 Kubernetes resource files. Counts are file inventory, not proof of semantic service coverage. Public class/alias names were checked for the selected candidates. The structured inventory has 21 on-premises coverage rows:

| Coverage group | Verified candidates / treatment | Remaining work |
|---|---|---|
| Data center, rack | `generic.place.Datacenter`, `generic.compute.Rack` | Review appearance/source notices and actual grouping semantics |
| Subnet, router, firewall | `generic.network.Subnet`, `Router`, `Firewall` | Verify mappings and readable style; do not imply real policy enforcement |
| L2/L3 switch | `generic.network.Switch`; named Cisco L2/L3 candidates exist separately | Use explicit layer labels with a neutral symbol; use Cisco imagery only for a named Cisco device with applicable terms |
| Physical server, relational DB | `onprem.compute.Server`, `generic.database.SQL` | Preserve physical-vs-VM and database meaning; do not choose a named database product silently |
| Room, security zone, VLAN, VRF, Kubernetes cluster | Labeled model/view boundaries | These do not require copying a provider icon; preserve overlapping physical/logical memberships |
| Eight neutral gaps | Load balancer, hypervisor, VM, NAS, SAN, identity service, backup system, monitoring | Select or author neutral symbols; make type differences explicit with labels/relations. Named HAProxy/QEMU/VMware/Dex/Prometheus icons are not generic substitutes. |

Tabler candidates include server, database, router, network, archive, desktop, analytics, users and shield shapes, with source paths/digests recorded in the inventory. They are candidates for a consistent neutral vocabulary, not claims of native NAS/SAN/VM semantics. Labeled project-authored geometry is another option for missing distinctions. Do not add an icon-pack runtime dependency or fetch icons during a render.

## 5. Detailed Kubernetes asset readiness

Verified diagrams candidates cover Node, Namespace, Deployment, ReplicaSet, StatefulSet, DaemonSet, Job, CronJob, Pod, Service, Ingress, NetworkPolicy, ConfigMap, Secret, ServiceAccount, PV, PVC and StorageClass. This is the 18-path candidate subset; icon existence does not implement FR-018/FR-029.

Three distinctions need explicit mapping work in M2-06:

- A node pool/group is provider-specific grouping, not an assumed core Kubernetes object.
- Ingress and an ingress controller are distinct; an Ingress icon does not identify the controller implementation.
- Cluster/control-plane context must not fabricate managed control-plane VMs. Namespace membership and Pod-to-Node placement remain independent.

Prefer matching the standard resource symbols to the explicitly licensed Kubernetes source. Preserve license selection, original source, transformations and notices. Resolve controller-specific assets only for the controller stated in the architecture.

## 6. Packaging and evidence handoff

M2 should pin approved sources and record original/derived SHA-256 values, license/permission references and attribution in the real asset manifest. The current JSON records **Git blob SHA-1 IDs**, not asset SHA-256 hashes. No binary/derived asset checksums are claimed because no extracted assets were saved or packaged.

Before conversion, validate the selected SVG data and reject executable/external references under the existing renderer security requirements. Use bounded, pinned local conversion only if the selected Graphviz/diagrams runtime needs a derived format. Test SVG/PNG output portability and visual fidelity in S04/M3/M4; no such tests passed in S02.

| Work | Outcome |
|---|---|
| M0-03 source/rights research and gap inventory | Complete; source snapshots and unresolved permission evidence recorded |
| O-002 Huawei asset selection/redistribution evidence | Open; color source recommended conditionally, not adopted for release |
| M2-03 Huawei packaging | Requires actual permission/license evidence and asset validation |
| M2-04 neutral on-premises choices | Eight initial gaps now have draw.io-type mappings under D-010; exact export, conditions and visual checks remain |
| M2-06 detailed Kubernetes assets | Candidate subset plus declared upstream license identified; origin/style/mapping checks remain |
| Next session | S03 repository/runner preflight, then S04 runtime proof as feasible |

Validation passed: 11 English Markdown files, one JSON research inventory, 44 local links/anchors, 64 requirement IDs, 17 acceptance scenarios, 32 task IDs and 29 decision/proposal/question IDs. Inventory checks confirmed 15/262 Huawei library counts, 17 required mappings and indices, 21 on-premises rows/eight gaps, 18 Kubernetes candidates and ten neutral SVG paths. Checked links/IDs, code fences, English-only text, whitespace and absence of raw artwork in the evidence JSON passed. Source trees and XML inventories were inspected; no implementation, plugin installation, icon conversion, runtime render, separate model review, commit or push occurred.
