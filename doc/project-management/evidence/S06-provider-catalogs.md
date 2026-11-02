# S06 — Provider Semantics, Catalogs and Icon Rights

Date: 2026-11-02 | Tasks: M2-01..06 | Branch: `codex/s06-provider-catalogs`, from `c6a59e5` | Updated for owner decisions D-016 and D-017

**Result: the catalogs, semantic rules, on-premises assets and both new gate lanes are implemented, and actual CI passes at `4b9b826`. The owner's later decisions D-016 and D-017 are implemented on top and pass the full local gate, but they are uncommitted and have no CI. M2 cannot close yet:** Huawei rights are not cleared, seven required Huawei items have no icon, the required Astra/High review has not happened, and the owner has not yet inspected the Huawei icons.

## Task status

| Task | Status | Result |
|---|---|---|
| M2-01 | Complete | 26 frozen taxonomy IDs, 148 catalog records in catalog `2026.11.0`, and a machine-readable inventory of all 93 items named in requirements section 6 |
| M2-02 | Complete | AWS, Azure and GCP native types, native IDs and documented placement rules, with fixtures |
| M2-03 | Partial | Huawei types, native service codes, IAM and enterprise-project distinctions and per-service rules are complete. **Eight items have icons for private personal use under D-017, and seven have none under O-010** |
| M2-04 | Complete, contact sheet accepted by the owner | Physical and logical on-premises types, plus the eight D-010 representations with exact source conditions, attribution and original and derived hashes |
| M2-05 | Complete | The `catalog-license` lane runs real inventory, license, asset and evidence checks, and fails on missing rights or assets |
| M2-06 | Complete | 22 Kubernetes kinds, 11 cluster modes with node-pool mappings, and rules applied on all five hosting environments |

## Exit criteria

| Criterion | State |
|---|---|
| All five hosting inventories and the Kubernetes detail catalog meet minimum breadth | **Met.** A test parses the requirements table, so the inventory cannot drift from it |
| Rules have evidence | **Met.** All 56 rules cite sources: provider or Kubernetes documentation for provider behavior, and the requirements for project-defined checks. All 129 source pages were fetched, and 76 specific claims matched, on 2026-11-02 |
| Asset rights are established | **Not met for Huawei.** D-017 accepts the risk for private personal use and establishes no rights. The other packs are recorded below with their real strength of evidence |
| No Huawei completion through unapproved icons or undisclosed generic replacements | **Met.** Tests reject both, Huawei is not marked complete, and icons appear only as the owner decided, with their limit disclosed |
| Astra/High review | **Not performed.** See [model and review](#model-and-review) |

## Validation

Actual Quality gate [run 41462453632](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41462453632), job 125334691898, passed all 12 lanes at `4b9b826819d9b54cb8086a7305a8257bd7f66ab5`, from a clean checkout on the self-hosted runner `macbook-pro-m2-max-mingrammer` with Python 3.13.7. The 480 tests include none skipped, and the job has zero annotations. The wheel it built has the same SHA-256 as the local build, `1441a118...0f7f`.

The D-016 and D-017 work followed. On it, the full local `scripts/quality_gate.py` passes all 12 lanes with 514 tests, none skipped. **No actual CI covers this later work yet**, because it is uncommitted. The counts below are from that local run:

| Lane | Tests | Work done |
|---|---|---|
| `schema-core` | 91 | Existing core tests, updated for the new result scope |
| `catalog-license` (new) | 66 | Script checks on the real repository, then tampering tests, including guessed Huawei mappings and clearance claims |
| `provider-semantics` (new) | 310 | 13 positive models, 276 expanded negative cases, four warning cases and coverage tests |
| `claude-plugin` | 47 | Package contract and clean-copy runtime, including catalog data in the copy |

A test lane now fails if it runs no tests, and the gate report carries `release_blockers`, so a green gate cannot read as release clearance.

Sabotage checks confirmed the lanes do real work. Each change was made to the real repository, failed its lane and was restored, with the `src` tree digest identical afterwards:

| Change | Lane result |
|---|---|
| An unlisted `huawei-ecs.png` placed under `src` | `catalog-license` failed: asset not in the rights manifest |
| ALB loses its two-zone rule | `provider-semantics` failed on `aws-alb-subnets-same-zone` |
| Huawei ECS given a generic native class | `catalog-license` failed: Huawei services must not use a substitute |
| AWS subnet changed to regional | `provider-semantics` failed three cases |

The real wrapper in `plugins/cloud-architecture-diagrams/bin/cloud-diagrams` ran from a fresh private environment that holds no `diagrams` package: capabilities, a filtered catalog search, a valid Huawei model with one `ASSET_PRIVATE_USE_ONLY` and nine `ICON_UNAVAILABLE` warnings, and a model with Thai labels. The owner's installed plugin, S04 alpha.3, the Codex marketplace and the runner registrations were not changed, so the installed Claude plugin does not have this work yet.

## Catalog design

Catalog data lives in `src/cloud_architecture_diagrams/catalog_data`, so it ships with the wheel and reaches the Claude plugin through its link. [The contract guide](../../design/core-contract.md#catalogs-and-provider-semantics) describes it, and `schemas/catalog-v1.schema.json` publishes its record format.

| Provider or platform | Records | Representation |
|---|---|---|
| AWS | 22 | 13 native classes, 9 labeled boundaries |
| Azure | 23 | 13 native classes, 9 labeled boundaries, 1 labeled node |
| GCP | 24 | 16 native classes, 8 labeled boundaries |
| Huawei Cloud | 25 | 7 private-use assets, **9 blocked**, 9 labeled boundaries, one of which carries the VPC icon |
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
| GCP | `diagrams` dependency | [Weaker](https://cloud.google.com/icons): the official library offers them for diagrams and technical documentation, with no license text. Accepted by the owner under D-016, citing [upstream coverage](https://diagrams.mingrammer.com/docs/nodes/gcp). That reason is coverage, so it adds no license |
| Kubernetes | `diagrams` dependency | [Apache-2.0 or CC-BY-4.0](https://github.com/kubernetes/community/blob/309fa9adfc84a8d04b0817a8b11124bf479a8d5e/icons/README.md). The `diagrams` copies are 256-pixel files, not byte-identical to the 128-pixel community PNGs, so a visual sample matches but exact origin is not proven |
| Generic and on-premises | `diagrams` dependency | MIT, with no per-icon origin recorded upstream |
| Huawei Cloud | **Bundled for private personal use only**, 8 PNG files | Owner risk acceptance under D-017. **Not cleared.** See [below](#huawei-cloud-icons-under-d-017) |

`native_icons.json` locks the file and SHA-256 behind all 62 allowed classes in the pinned `diagrams` 0.25.1 wheel, and the lane compares them with the installed package. `diagrams` is a development dependency for now, so the plugin's runtime stays unchanged until M3. Upstream copies may be older than each provider's current set; FR-048 and M4 check that.

### Huawei Cloud icons under D-017

**The owner decided on 2026-11-02 to use the `JuanDiaz00/Huawei-Cloud-draw.io-icons` pack, for private personal use only.** D-017 records this as the owner accepting the rights risk for that use. It is not permission from any rights holder: rights are not cleared and redistribution permission is not established. O-002 keeps public distribution blocked.

**Source facts, unchanged by the decision:**

| Fact | Value |
|---|---|
| Repository and pin | `JuanDiaz00/Huawei-Cloud-draw.io-icons`, commit `ea52d7356e172a85cde7538f293a663eb137611d`, still `main` on 2026-11-02 |
| File | `HuaweiCloud Icons.xml`, Git blob `0bd260648d2525e86c87c671ea9f9deb8d825a14`, SHA-256 `1afc1f2a0fda735c7b9eda88466725b720045493e61a04d392467596b8c976cd`. S02's hashes still match |
| Origin | The README names VeryIcon. VeryIcon attributes the pack to AIyangyang and states it is free for personal and commercial purpose, which is that site's claim and shows no authorization from Huawei |
| License | No license file, and GitHub reports none |
| Actual format | All 155 entries are PNG, 8-bit RGBA, base64 in a draw.io mxlibrary. 154 are 256x256 and one is 512x512. Each is 2.4 to 12.6 KB, 1 MB in total, with no duplicates. Declared sizes match the real ones |
| Actual appearance | **Every image is pure black line art on a transparent background**, measured on all 155: none has an opaque non-black pixel, and 74 to 90 percent of each image is transparent |

`S06-huawei-pack-inventory.json` lists all 155 entries with index, title, size and SHA-256, and holds no artwork. `scripts/build_huawei_assets.py` refuses a file that differs from the pin. Each bundled PNG is byte-identical to its decoded entry.

**Coverage of the 17 required items**, also available as `huawei_icon_coverage` in `reports/catalog-license.json`:

| State | Items |
|---|---|
| **Mapped (8):** the source title names the service | VPC `network-vpc`, ECS `computing-ecs`, ELB `network-elb`, EIP `network-eip`, RDS `database-rds`, IAM `managementdeployment-iam`, VPN `network-vpn-2`, FunctionGraph `computing-fgs` |
| **Labeled boundary (2):** no icon needed under section 6 | Subnet, Security Group |
| **No clear match (7):** visibly no icon, no substitute, O-010 | NAT Gateway, CCE, OBS, API Gateway, Direct Connect, Cloud Eye, LTS |

FunctionGraph goes beyond the seven P-013 found by title. Huawei's own [API path](https://support.huaweicloud.com/intl/en-us/api-functiongraph/functiongraph_06_0144.html) uses `fgs`, and its [template reference](https://support.huaweicloud.com/eu/tr-aos/fgs-function.html) says `HuaweiCloud.FGS.Function` creates FunctionGraph functions, so this title names the service. It is the one mapping that depends on an alias, so it needs the owner's eye too.

Close candidates were left unmapped on purpose:

| Item | Closest entry | Why not |
|---|---|---|
| OBS | `storage-55` | VeryIcon names it only "Storage"; it looks like a category icon |
| CCE | `other-cluster-computing-platform-services` | Names no container service, and depicts servers |
| LTS | `log-and-trace-consolele` | Names no Log Tank Service |
| Direct Connect | `cc-21` | VeryIcon names it `cc`, the code for Cloud Connect, a different service |
| Cloud Eye | `cmc` | The code does not name Cloud Eye, documented as CES |
| NAT Gateway, API Gateway | None | No candidate title |

![Mapped icons and unmapped candidates](S06-huawei-icon-review.png)

**How the limits are enforced.** The `catalog-license` lane fails when any of these breaks:

- The package lacks `Private :: Do Not Upload`, which PyPI rejects on upload. The `package-contents` lane checks the built wheel for it as well.
- In Actions, the event reports the repository as public. Outside Actions this cannot be read, and the report says `not_checked_outside_actions`.
- The private pack claims a license or redistribution evidence, loses its pinned hashes, or names a decision that does not say private personal use. A pack also cannot become `approved` on owner risk acceptance.
- A source title does not name the service, so mapping OBS to `storage-55` fails.
- `NOTICE.md` or the plugin README stops stating the limit.

Sabotage checks confirmed three of these on the real repository: a reported-public repository, a removed classifier, and OBS mapped to `storage-55` each failed the lane, and the files were restored. These guards catch mistakes in the repository. They cannot stop someone copying the files, and the lane only runs when a job does, so flipping the repository to public would be caught at the next run, after the fact.

**What this leaves open for the owner:**

1. **The pack is monochrome line art, while the requirements call for icons close to Huawei's published color conventions** (D-008, FR-048, T-016). This may not be what the owner pictured, and black lines would vanish on a dark background. S02 found the LATAM library has exact titles for all 17 items in color SVG, with the same uncleared rights. The owner could extend the private-use decision to it, which would also close O-010. Nothing has been changed on that basis.
2. **O-010:** identify the seven items by eye, choose another source, or accept labeled text, which changes T-004.
3. **Git history:** once these files are committed, making the repository public would first require removing them from history.
4. **Generated diagrams:** sharing an image that shows these icons outside private use is not covered by D-017.

Written consent from Huawei remains the only route to public distribution. Draft request, not sent:

> Please identify the license or permission that applies to the Huawei Cloud service icons published at https://open.huaweicloud.com/openplatform/icons (manifest.v1.json generated 2026-07-31). We plan to use them in an architecture-diagram plugin: storing the files, converting formats locally, bundling them with the plugin, and producing downloadable diagrams that show them. Please confirm the permitted uses and any attribution, trademark or modification conditions, in writing.

**Other sources, unchanged:** Huawei operates an [official icon library](https://open.huaweicloud.com/openplatform/icons) with a manifest of 196 logos, SHA-256 `2862d932cdaff5ca1407910d5b0a85cf826cbda9b5576e93d0291626208f1f69`, generated 2026-07-31, with every architecture icon marked as planned and no license field. The [Huawei Cloud site terms](https://www.huaweicloud.com/intl/en-us/declaration-sg/sa_st.html) require prior written consent to reproduce, modify or distribute site content and express written permission for logos, and [Huawei's corporate terms](https://www.huawei.com/en/legal) say the same. `huaweicloud-latam/drawio-libraries` still has no license file. None of these is adopted. This is a reading of published terms, not legal advice.

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

`scripts/build_onprem_assets.py` is a small stencil interpreter with no third-party input. `assets-source/drawio/networks-subset.xml` keeps the seven shapes verbatim, so the lane repeats the SVG derivation with no network and compares it byte for byte, and each shape's canonical digest is recorded. PNGs were rendered once with rsvg-convert 2.63.4, and the lane checks their recorded digests, signature and size. SVGs pass an allowlist with no scripts, external references or links. 

**Owner inspection:** on 2026-11-02 the owner reviewed all eight symbols on this contact sheet and accepted them, as relayed through the parent session. The acceptance covers [this sheet](S06-onprem-contact-sheet.png) only, SHA-256 `eb52f3bc5f9de8dd724f0ba8374daebcbcee9cd13105dd756981bd38a9537913`. Rendered visual acceptance, including how these look at diagram size, stays with M4 and M6.

## What later milestones depend on

- **M3** must honor `representation`, including `required_label` for assets, and must not substitute for `blocked`. Azure icons must be drawn unmodified. Huawei PNGs are black on transparent, so they need a light background, and a bundle using them must carry the private-use limit in its manifest.
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

1. Owner: inspect the Huawei icon sheet, and decide O-010, including whether line art is acceptable.
2. Owner: authorize a commit and push of D-016 and D-017, so actual CI covers them. Update the installed plugin only if asked.
3. Arrange the Astra/High review of this work, then close M2 or record its remaining blocker.
4. S07 / M3 can proceed in parallel.
