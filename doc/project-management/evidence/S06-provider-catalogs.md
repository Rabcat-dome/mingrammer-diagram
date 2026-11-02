# S06 — Provider Semantics, Catalogs and Icon Rights

Date: 2026-11-02 | Tasks: M2-01..06 | Branch: `codex/s06-provider-catalogs`, from `c6a59e5`

**Result: the catalogs, semantic rules, on-premises assets and both new gate lanes are implemented, and the full local gate passes. M2 cannot close yet:** Huawei icon rights remain an explicit packaging and release blocker, the required Astra/High review has not run, and no CI run covers this work because nothing is committed or pushed.

## Task status

| Task | Status | Result |
|---|---|---|
| M2-01 | Complete | 26 frozen taxonomy IDs, 148 catalog records in catalog `2026.11.0`, and a machine-readable inventory of all 93 items named in requirements section 6 |
| M2-02 | Complete | AWS, Azure and GCP native types, native IDs and documented placement rules, with fixtures |
| M2-03 | Partial | Huawei types, native service codes, IAM and enterprise-project distinctions and per-service rules are complete. **Icons are blocked by O-002** |
| M2-04 | Complete, owner inspection pending | Physical and logical on-premises types, plus the eight D-010 representations with exact source conditions, attribution and original and derived hashes |
| M2-05 | Complete | The `catalog-license` lane runs real inventory, license, asset and evidence checks, and fails on missing rights or assets |
| M2-06 | Complete | 22 Kubernetes kinds, 11 cluster modes with node-pool mappings, and rules applied on all five hosting environments |

## Exit criteria

| Criterion | State |
|---|---|
| All five hosting inventories and the Kubernetes detail catalog meet minimum breadth | **Met.** A test parses the requirements table, so the inventory cannot drift from it |
| Rules have evidence | **Met.** All 55 rules cite sources: provider or Kubernetes documentation for provider behavior, and the requirements for project-defined checks. All 124 cited web pages were fetched, and 70 specific claims matched, on 2026-11-02 |
| Asset rights are established | **Not met for Huawei.** The other packs are recorded below with their real strength of evidence |
| No Huawei completion through unapproved icons or undisclosed generic replacements | **Met.** Tests reject both; every Huawei service is `semantics_only` with no icon |
| Astra/High review | **Not performed.** See [model and review](#model-and-review) |

## Validation

The full local `scripts/quality_gate.py` passed all 12 lanes at the working tree on top of `c6a59e5` on macOS ARM64. **No actual CI run covers this yet**, because committing and pushing wait for the owner.

| Lane | Tests | Work done |
|---|---|---|
| `schema-core` | 90 | Existing core tests, updated for the new result scope |
| `catalog-license` (new) | 34 | Script checks on the real repository, then tampering tests |
| `provider-semantics` (new) | 309 | 13 positive models, 276 expanded negative cases, three warning cases and coverage tests |
| `claude-plugin` | 47 | Package contract and clean-copy runtime, including catalog data in the copy |

A test lane now fails if it runs no tests, and the gate report carries `release_blockers`, so a green gate cannot read as release clearance.

Sabotage checks confirmed the lanes do real work. Each change was made to the real repository, failed its lane and was restored, with the `src` tree digest identical afterwards:

| Change | Lane result |
|---|---|
| An unlisted `huawei-ecs.png` placed under `src` | `catalog-license` failed: asset not in the rights manifest |
| ALB loses its two-zone rule | `provider-semantics` failed on `aws-alb-subnets-same-zone` |
| Huawei ECS given a generic native class | `catalog-license` failed: Huawei services must not use a substitute |
| AWS subnet changed to regional | `provider-semantics` failed three cases |

The real wrapper in `plugins/cloud-architecture-diagrams/bin/cloud-diagrams` ran from a fresh private environment that holds no `diagrams` package: capabilities, a filtered catalog search, a valid Huawei model with 16 `ASSET_RIGHTS_BLOCKED` warnings, and a model with Thai labels. The owner's installed plugin, S04 alpha.3, the Codex marketplace and the runner registrations were not changed.

## Catalog design

Catalog data lives in `src/cloud_architecture_diagrams/catalog_data`, so it ships with the wheel and reaches the Claude plugin through its link. [The contract guide](../../design/core-contract.md#catalogs-and-provider-semantics) describes it, and `schemas/catalog-v1.schema.json` publishes its record format.

| Provider or platform | Records | Representation |
|---|---|---|
| AWS | 22 | 13 native classes, 9 labeled boundaries |
| Azure | 23 | 13 native classes, 9 labeled boundaries, 1 labeled node |
| GCP | 24 | 16 native classes, 8 labeled boundaries |
| Huawei Cloud | 25 | **16 blocked**, 9 labeled boundaries |
| On-premises | 23 | 8 custom assets, 6 native classes, 9 labeled boundaries |
| Kubernetes | 22 | 18 native classes, 3 labeled boundaries, 1 labeled node |
| Common and external | 9 | Logical boundaries and external parties |

Choices made while freezing the inventory:

- **Product variants have their own types** where the difference changes a rule: zonal and regional AWS NAT gateways, three GCP load-balancer products, GKE Standard and Autopilot, CCE standard, Turbo and Autopilot.
- **`external.entity` is new.** FR-024's external parties had no taxonomy ID, so requirements revision 0.10 adds one.
- **`security_group` is a new boundary kind**, so AWS security groups, Azure NSGs and Huawei security groups stay distinct from a logical `security_zone`. The change is additive, so the schema stays at 1.0.0. A GCP VPC firewall rule stays a resource, because it is not a membership boundary.
- **Native IDs** use CloudFormation types for AWS, ARM types for Azure, Cloud Asset types for GCP and API group and version for Kubernetes. Each was checked against its reference page. Huawei records use the documented service code, because no equivalent resource-type reference was verified.

## Rules that older assumptions would have got wrong

Checking current sources changed several rules from what the requirements and memory suggested:

- AWS **regional NAT gateways** sit on the VPC with no public subnet, so a rule requiring a subnet would reject a valid design. They are now a separate type from zonal gateways.
- An EC2 instance **may** attach to several VPCs through its interfaces, so the rule is that its interfaces share one zone, not one VPC.
- Azure **Standard NAT Gateway is zonal and StandardV2 is zone redundant**, so `zone_ref` stays optional.
- GKE **Autopilot clusters are always regional**, and a node pool is documented as a Standard-cluster concept. CCE Autopilot is documented as serverless with no node management. Declaring a user node pool in either fails.
- Huawei **OBS and IAM are authorized globally** in Huawei's service table, although a bucket has a region. Authorization scope and location are separate, so OBS rejects an IAM project and keeps its region.

Some documented points are deliberately not enforced, because a false rejection would be worse than a gap:

| Not enforced | Why |
|---|---|
| RDS subnet group across two zones | AWS says "should", and listed subnets may not be the whole group |
| Azure `GatewaySubnet` and `AzureFirewallSubnet` names | `name` is a free display label, so a rule would reject a readable one |
| Node pools in EKS Auto Mode and AKS Automatic | The pages reviewed do not clearly forbid them, so only a warning about declared nodes applies |
| Azure NSG same-region association | No statement was verified |
| Huawei tag syntax, and one enterprise project per resource | No statement was verified |

Nothing here checks a live account, so a passing model is not proof of deployment, reachability or enforcement.

## Icon rights

The structured record is `src/cloud_architecture_diagrams/catalog_data/assets.json`, and `assets/NOTICE.md` ships with the package.

| Pack | Delivery | Evidence and its strength |
|---|---|---|
| draw.io Network 2018 | **Bundled**, 8 SVG and PNG pairs | CC BY 4.0 at the pinned source, with the stencil license's Atlassian restriction. Applies to the seven audited shapes only |
| AWS | `diagrams` dependency | [Explicit permission](https://aws.amazon.com/architecture/icons/) to create architecture diagrams, recognizing third-party libraries |
| Azure | `diagrams` dependency | [Explicit permission](https://learn.microsoft.com/en-us/azure/architecture/icons/) for architectural diagrams, training material and documentation. No cropping, flipping, rotating or distortion, so M3 must draw them unmodified |
| GCP | `diagrams` dependency | [Weaker](https://cloud.google.com/icons): the official library offers them for diagrams and technical documentation, with no license text. See O-009 |
| Kubernetes | `diagrams` dependency | [Apache-2.0 or CC-BY-4.0](https://github.com/kubernetes/community/blob/309fa9adfc84a8d04b0817a8b11124bf479a8d5e/icons/README.md). The `diagrams` copies are 256-pixel files, not byte-identical to the 128-pixel community PNGs, so a visual sample matches but exact origin is not proven |
| Generic and on-premises | `diagrams` dependency | MIT, with no per-icon origin recorded upstream |
| Huawei Cloud | **None** | Blocked by O-002 |

`native_icons.json` locks the file and SHA-256 behind all 62 allowed classes in the pinned `diagrams` 0.25.1 wheel, and the lane compares them with the installed package. `diagrams` is a development dependency for now, so the plugin's runtime stays unchanged until M3. Upstream copies may be older than each provider's current set; FR-048 and M4 check that.

### Huawei Cloud: O-002 stays open, with stronger evidence

This research went further than S02 and changed the finding from an evidence gap to a stated restriction:

- **New source:** Huawei operates an [official icon library](https://open.huaweicloud.com/openplatform/icons) with a machine-readable manifest of 196 logos, SHA-256 `2862d932cdaff5ca1407910d5b0a85cf826cbda9b5576e93d0291626208f1f69`, generated 2026-07-31. It covers 15 of the 17 named items; Subnet and Security Group have no entry and stay labeled boundaries, which needs no icon. Every entry marks its architecture icon as planned, and the page lists its draw.io and PPT packages as not yet connected. The manifest and the page carry no license field or notice.
- **Actual terms:** the [Huawei Cloud site terms](https://www.huaweicloud.com/intl/en-us/declaration-sg/sa_st.html) reserve all rights, say that site content may not be reproduced, modified or distributed without prior written consent, and require express prior written permission for logos. [Huawei's corporate terms](https://www.huawei.com/en/legal) say the same. These are general site terms, not a license written for icons, and no icon-specific grant was found. This is a reading of published terms, not legal advice.
- **Earlier candidates are unchanged:** `huaweicloud-latam/drawio-libraries` still has no license file and null license metadata, and its last commit remains `52c33aa`. `JuanDiaz00/Huawei-Cloud-draw.io-icons` also has none.

**Effect:** no Huawei file is bundled, the 16 service types are `semantics_only`, validation returns `ASSET_RIGHTS_BLOCKED`, `capabilities` and the gate report list the blocker, and tests reject a generic substitute. Semantics work is independent of this and is complete.

**The choice belongs to the owner.** Requirements section 6.2 calls for an explicit discussion before scope is reduced:

1. **Ask Huawei Cloud for written consent, or supply existing consent.** This is the recommendation, and the wording below is ready. Nothing has been sent, and sending is the owner's decision.
2. **Reduce scope explicitly**, with Huawei services drawn as visibly labeled text and disclosed as such. This changes FR-013 and T-004 and needs a recorded decision.

Draft request, not sent:

> Please identify the license or permission that applies to the Huawei Cloud service icons published at https://open.huaweicloud.com/openplatform/icons (manifest.v1.json generated 2026-07-31). We plan to use them in a private, non-commercial architecture-diagram plugin: storing the files, converting formats locally, bundling them with the plugin, and producing downloadable diagrams that show them. Please confirm the permitted uses and any attribution, trademark or modification conditions, in writing.

## On-premises representations

![The eight on-premises symbols](S06-onprem-contact-sheet.png)

| Concept | Source symbols | Representation |
|---|---|---|
| Load balancer | `mxgraph.networks.load_balancer` | Direct |
| Hypervisor | `server` + `virtual_server` | Host with a guest symbol, distinct from the VM asset |
| VM | `virtual_server` | Direct, labeled VM |
| NAS | `nas_filer` | Direct |
| SAN | `storage` | Storage symbol labeled SAN |
| Identity service | `server` + `users` | Server with a people symbol; implies no product |
| Backup system | `server_storage` | Server and storage; no tape imagery |
| Monitoring | `server` | Server with a required Monitoring label, not a display symbol |

**Source correction:** S02 called `bc0ccab` a commit, but it is the annotated tag object for v29.3.2. The commit is `48b181339578e11da7052ebf5b1fba8499418b77`. The audited blobs are unchanged: `networks.xml` is `24191cc` and its SHA-256 is `2921086e...3711`. That file is no longer published at the current v32.6.9 tag, so the pinned version stays the source. The current README widens the Atlassian restriction, which does not reach this project's targets.

`scripts/build_onprem_assets.py` is a small stencil interpreter with no third-party input. `assets-source/drawio/networks-subset.xml` keeps the seven shapes verbatim, so the lane repeats the SVG derivation with no network and compares it byte for byte, and each shape's canonical digest is recorded. PNGs were rendered once with rsvg-convert 2.63.4, and the lane checks their recorded digests, signature and size. SVGs pass an allowlist with no scripts, external references or links. Whether these look right at diagram size remains an owner and M4 judgment.

## What later milestones depend on

- **M3** must honor `representation`, including `required_label` for assets, and must not substitute for `blocked`. Azure icons must be drawn unmodified.
- **M3** moves `diagrams` to a runtime dependency, which changes the plugin's locked environment and needs its test updated.
- **M4** checks native icons against current provider sets under FR-048. S01's visual fidelity remains unproven.
- **M7-04** catalog discovery is available through the plugin. Rendering remains.

## Limits

- Sources were checked once on 2026-11-02. Nothing re-fetches them automatically, so `S06-source-checks.json` is a dated record.
- The claim patterns show that a statement was present on a page. Reading it correctly was this session's judgment, with no independent review.
- Rules cover documented constraints for the minimum catalog, not every provider constraint.
- `S06-source-checks.json` hashes reduced page text rather than storing it. Provider pages change often, so a later hash mismatch would not itself show that a rule is wrong.

## Model and review

Implementation used **Claude Opus 5.5 (`claude-opus-5-5`)**, the model of the session the owner started, with a reasoning-effort setting of 100 and no named level shown. The project policy names Sol for implementation; this deviates from that and no setting was changed.

Self-checks in this session are not a review. **The Astra/High review M2 requires has not been performed**, and M2 should not close until it has. Review of the M7 Medium and Low fixes also remains outstanding from earlier work. It is not part of this task.

## Next steps

1. Owner: inspect the on-premises symbols, decide the Huawei route under O-002, and decide whether the GCP evidence is enough under O-009.
2. Owner: authorize a commit and push, so actual CI can run on the self-hosted runner.
3. Arrange the Astra/High review of this diff, then close M2 or record its remaining blocker.
4. S07 / M3 can proceed in parallel, with Huawei services kept visibly icon-less.
