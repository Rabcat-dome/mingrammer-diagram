# Decisions, Open Questions and Source Reconciliation

Updated: 2026-11-02 | Status: Joint-planning record; D-013 selects per-machine local plugin/runtime installation.

## Confirmed user direction

| ID | Direction | Origin |
|---|---|---|
| D-001 | Build a personal plugin based on `mingrammer/diagrams`, adding Huawei visuals and targeting AWS/Azure/GCP/Huawei/on-premises | Current user request |
| D-002 | Target ChatGPT Work first; prepare for Claude Code later | Current user request; overrides attachment's Claude Cowork wording |
| D-003 | Put requirements under repository-relative `doc/requirements` and planning under `doc/project-management` | Current user request; `/doc/...` interpreted as folders within this project |
| D-004 | All repository documentation is English; include a portable activity summary/handoff | Current user request |
| D-005 | Specify development/review models and assess a pipeline using existing self-hosted runner capacity | Current user request; does not establish runner registration for this repository |
| D-006 | Deliver an installable plugin usable across machines. A skill may be bundled inside it; the final deliverable must remain a plugin. | User clarification on 2026-10-31; D-013 subsequently selects per-machine local runtime installation |
| D-007 | Release 1 targets solution architecture overall: network/subnet, VM, database/storage and security, retaining existing minimum-catalog items. Kubernetes depth is governed by the subsequent D-009 correction. | Initial S01 answer, amended by the owner's Kubernetes clarification on 2026-10-31 |
| D-008 | Start with white/provider-icon visuals close to each provider's published architecture conventions, including native service labels and meaningful boundaries/layout | Explicit S01 style answer on 2026-10-31; actual rendered samples still need later inspection |
| D-009 | Kubernetes is detailed release-1 scope, including node pools/groups/nodes, namespaces, workloads/Pods, Service/Ingress and related storage/configuration/security relationships. This supersedes the earlier cluster-only limit; overall solution-architecture depth and D-008 visual direction remain. | Explicit user correction on 2026-10-31 |
| D-010 | Use draw.io-type generic symbols/compositions for the eight on-premises gaps, with explicit type labels and applicable source/attribution checks before bundling. Keep the existing diagrams/Graphviz renderer. | User requested draw.io icon types as replacements on 2026-10-31; exact source-file/package clearance remains implementation evidence |
| D-011 | Add a separate runner for this repository on the existing Mac, commit/push the documentation and workflow to the private repository, and execute the real preflight job | Explicit owner selection on 2026-11-01; authorizes the P-014 setup and initial publication/test, without changing other projects' registrations |
| D-012 | Historical central-server direction, superseded by D-013 | Initial S04 owner selection on 2026-11-01; no hosting was provisioned |
| D-013 | Install the renderer/runtime on each machine using the plugin; supersede D-012 central hosting and use the desktop/local execution route for the first proof | Explicit owner correction on 2026-11-01 replacing the assumption of a free public renderer with per-machine installation; no hosted renderer is required |
| D-014 | The first-release target is the separate ChatGPT Work mode/page, not Codex in the app. Codex runtime tests do not replace actual Work invocation/preview/export evidence. | Explicit owner clarification on 2026-11-02; owner also confirmed the plugin is visible/selectable in Work |
| D-015 | Prepare a Claude Code plugin package now, ahead of M7's "later" position, reusing the M1 core. The Work first-release target, M2-M6 order and P0 scope stay as they are. | Explicit owner request on 2026-11-02 after bringing Claude Code to read the project. The unchanged first-release priority is this session's reading of that request, not a separate owner statement; correct it here if the priority has moved |

## Recommendations and disposition

| ID | Proposal | Rationale / resolution point |
|---|---|---|
| P-001 | Canonical JSON + taxonomy + provider catalogs + controlled renderer; wrap upstream first | Retains semantics and portability; freeze contract in M1 |
| P-002 | Installable plugin with a bundled workflow skill and renderer tools | Product structure retained; D-013 replaces the original remote-service recommendation with local runtime installation. |
| P-003 | Local stdio MCP on each supported desktop, with per-machine installer/preflight | Selected route under D-013; Alpha.3 uses native Python/Graphviz with a direct script and stdio; the earlier Docker runtime is historical. The owner reports Work alpha.3/Darwin, a visible PNG and five files. |
| P-004 | Sol implementation, Astra separate code review; deterministic CI, no mandatory model API in renderer | Balance repeatable development with deeper review; detailed policy in model strategy |
| P-005 | Quality gate pipeline starts in M1 and expands through M5 | Catch schema, semantics, asset-rights, render and adapter failures at their introduction |
| P-006 | Strict final output; lenient mode only for disclosed draft fallback | Never downgrade structural/security errors or known invalid placement |
| P-007 | Promote provenance, source export, bounded execution and reproducibility metadata to P0 | Required for reviewable plugin output and predictable execution |
| P-008 | English/Thai request and label support with English documentation | Fits intended use; exact fonts and visual fixtures chosen in M0/M4 |
| P-009 | Initial proposal: solution-architecture depth with a cluster-only Kubernetes limit | Overall depth accepted as D-007; the Kubernetes limit was superseded by D-009 and is not current scope. |
| P-010 | Start with a white/provider-icon style, labeled boundaries and restrained colors | Refined and accepted as D-008: approximate each provider's published architecture conventions; actual sample acceptance remains later work. |
| P-011 | Prefer the Huawei LATAM draw.io color family at a pinned revision as the Huawei technical source | S02 found candidates for all 17 named minimum items, but no clear plugin-redistribution grant in audited sources. Conditional recommendation only; O-002 remains open. |
| P-012 | Original neutral-icon options included generic/project-authored/Tabler symbols; Kubernetes standard symbols use their declared source license | On-premises visual preference is now resolved by D-010 in favor of draw.io-type generic mappings. Tabler remains an alternative, not the selected default for these eight concepts. M2 verifies exact assets/terms and computes SHA-256. |
| P-013 | Keep JuanDiaz00/Huawei-Cloud-draw.io-icons as an alternative Huawei technical source | User-supplied repo contains 155 PNG entries sourced from VeryIcon. Seven minimum items are unambiguous by title; remaining mapping and source-asset redistribution evidence need review. LATAM color/SVG remains the preferred technical candidate, not an adopted/cleared package. |
| P-014 | Add a separate repository-scoped macOS ARM64 runner on the existing Mac, with custom label `mingrammer-macos-arm64` | Accepted as D-011 and implemented: runner ID 2, v2.338.2, separate LaunchAgent, labels verified; initial tree published and two real jobs passed. S03 records the transient broker/offline observation and final online/idle snapshot. |
| P-015 | Historical Linux-container runtime candidate | Alpha.1 SDK/live Codex Desktop evidence is retained. Docker was an implementation choice, not a user requirement; P-017 is the new native default. |
| P-016 | Historical proposal to evaluate GCP Cloud Run | Retired by D-013. No cloud-hosting inputs, deployment, remote OAuth or public renderer are required for the selected route. |
| P-017 | Native private Python environment + system Graphviz, with direct script and stdio interfaces | Introduced in alpha.2 and hardened in alpha.3 after the owner questioned Docker and requested continuation. No required Docker/server. Native checks and owner-reported Work feasibility pass; final Astra/High review passes for the pilot; production limits remain later work. |
| P-018 | M1 core uses a strict closed Pydantic contract, generated JSON Schema, bounded reference/context validation and native deterministic CI | Implementation selection under existing M1 scope. Core results disclose pending catalog/provider/render layers. Python 3.13.7/uv 0.13.0, locked packages and hatchling 1.27.0 selected; no Docker/model API or S04 plugin upgrade required. |
| P-019 | Claude Code adapter as `plugins/cloud-architecture-diagrams`: bundled skill plus a `bin/cloud-diagrams` wrapper over the existing CLI, symlinks into the repository for one copy of the core, and no MCP server | Implemented under D-015. A Claude Code session already has Bash and Read, so a second tool contract would add context cost without adding capability; rendering can arrive as a CLI subcommand with M3. The manifest omits `version` during preparation, so installs follow commits; set an explicit version at release. [Evidence](evidence/M7-claude-plugin.md) |

| P-020 | Catalog data as versioned JSON under `src`, resolved by provider plus kind for scopes and boundaries and by `service_type` for resources, with product variants as separate types and a closed rule table carrying its sources | Implemented in S06. Adds `external.entity` and the `security_group` boundary kind, both additive, so schema 1.0.0 stays. A rule fires only on what a model declares, so missing placement stays unspecified. [Evidence](evidence/S06-provider-catalogs.md) |
| P-021 | Deliver AWS, Azure, GCP, Kubernetes and generic icons through the pinned `diagrams` wheel with a per-class SHA-256 lock, and bundle only the eight draw.io-derived on-premises assets | Implemented in S06. Nothing from the dependency packs is copied into this repository. `diagrams` stays a development dependency until M3 needs it at runtime |
| P-022 | Pin draw.io to tag v29.3.2, commit `48b181339578e11da7052ebf5b1fba8499418b77`, and keep the seven audited shapes verbatim in `assets-source/drawio` so derivation repeats offline | Implemented in S06. Corrects S02, which named the tag object `bc0ccab` as a commit. The stencil file is no longer published at current tags |

P-015 is historical. P-017 is the current native implementation default, not proof of every OS or final product limits. P-002's plugin structure remains; P-003's local route is selected by D-013. P-009/P-010 are resolved by D-007/D-008 with D-009's detailed-Kubernetes correction.

P-011/P-013 are source recommendations, not user decisions or packaging clearance. D-010 resolves the on-premises symbol direction from P-012 without granting third-party rights or approving a specific source package.

## Open decisions

| ID | Question | Working assumption / next action | Needed by |
|---|---|---|---|
| O-001 | Which Work execution modes satisfy the cross-machine plugin requirement? | D-013 selects local per-machine installation; D-014 confirms the separate Work page. Owner reports alpha.3/Darwin, PNG preview and five files. Resolved for M0: S04 supports the tested macOS local Work route; cloud-only/other-OS modes are unverified and not promised. | Resolved in S04 / M0-02 |
| O-002 | Which Huawei icon source/version and redistribution terms are acceptable? | **Open packaging and release blocker.** S06 found a Huawei-operated manifest of 196 logos with no license, and Huawei Cloud site terms that require prior written consent to reproduce or distribute content and express written permission for logos. LATAM v3.2 / commit 52c33aa12fb816a5de403da85067e1c0f039b5be covers 17 named items technically, and JuanDiaz00's PNG repack remains an alternative; neither has a license. No source is adopted or cleared, nothing is bundled and no permission request was sent. Owner choice: request written consent (recommended, with [draft wording](evidence/S06-provider-catalogs.md#huawei-cloud-o-002-stays-open-with-stronger-evidence)) or explicitly reduce scope to labeled text. | M2-03/package release |
| O-003 | Which exact product variants/type IDs implement the minimum catalog? | Resolved by S06: catalog `2026.11.0` freezes 148 records and 22 Kubernetes kinds verified against release 1.37. The owner can still rename or adjust coverage. See the [S06 record](evidence/S06-provider-catalogs.md). | Resolved in M2-01/M2-06 |
| O-004 | Which exact rendered examples establish visual acceptance? | Direction resolved as D-008: white/provider-icon visuals close to each provider's published conventions. Six briefs and official source entry points are prepared; actual image comparison/acceptance remains M4/M6 work (FR-048/T-016). | M4-03/M6 |
| O-005 | Which runner is eligible for this repository, with which trust/visibility policy? | Resolved by D-011 and S03: private repository; owner-only manual workflow on `main`; separate runner ID 2, v2.338.2, project label and actual service environment verified by two successful jobs. The current plan lacks server-enforced required checks; retain manual merge/release discipline and recheck availability before future jobs. | Resolved in S03 / M0-04 |
| O-006 | Which hosting destination/project/region/budget is needed? | Retired: D-013 supersedes central hosting. No owner hosting answer or cloud deployment is needed. Per-machine prerequisites are implementation evidence under O-001. | Closed by scope change |
| O-007 | Which versions/fonts/isolation and numeric limits are practical? | Native alpha.3 tests Python 3.13.7, diagrams 0.25.1, Graphviz 16.1.0, SDK 2.3.0 and bundled Noto fonts on macOS ARM64. CPU/file/wall limits and sampled RSS/scratch controls pass targeted checks; full production bounds remain open; Work feasibility is owner-confirmed. Historical container quotas do not apply to native execution. Candidate selection is complete for M0; full production controls remain M3. | Resolved for M0-05; production M3 |
| O-008 | What architecture granularity is required in release 1? | Resolved by D-007/D-009: solution architecture overall with detailed Kubernetes views. Existing required items such as Azure NIC remain in scope. | Resolved in S01 |
| O-009 | Is Google's icon-library wording enough for GCP icons? | The page offers its icons for diagrams and technical documentation but states no license text, unlike the explicit AWS and Microsoft statements. Working assumption for this private plugin: acceptable through the `diagrams` dependency, recorded as `publisher_invitation`, with nothing copied here. Recheck before any wider distribution. | Owner, by M6 |

Product-size limits remain proposed. S04 implements the fixed-fixture bounds recorded in its evidence; they are not full-product benchmarks or hard memory/disk guarantees. Work transport/request limits may require lower product limits or a later asynchronous design.

S01 result record: [release scope and scenario briefs](evidence/S01-release-scope.md). Scope-planning work is complete with explicit granularity/style answers; the record separates confirmed decisions from working examples and later acceptance evidence.

S02 research record: [sources, rights and gaps](evidence/S02-icon-sources-and-rights.md), with [structured inventory](evidence/S02-icon-inventory.json). M0-03 research is complete; Huawei package clearance is unresolved. S03/S04 can proceed without treating that clearance as granted.

S02 follow-up: [additional Huawei source and draw.io mappings](evidence/S02-additional-icon-sources.md), with [supplemental metadata](evidence/S02-supplemental-icons.json). Eight on-premises concepts are mapped; exact export/visual/asset-condition checks remain M2/M4 work. Source and stencil terms are recorded separately from application-code licenses.

## Source reconciliation

Input: `cloud-architecture-diagram-plugin-requirements.md`, document CADP-REQ-001 v1.1, supplied from the owner's Downloads folder. This repository's revision 0.10 is a planning baseline, not evidence of a v1.1 implementation release. Revision 0.2 added cross-machine delivery, revision 0.3 initial S01 depth/style, revision 0.4 detailed Kubernetes, revision 0.5 draw.io-type on-premises mappings under D-010/FR-014, revision 0.6 the historical central-server target under D-012, and revision 0.7 the superseding local-install route under D-013, revision 0.8 the native default/direct-script clarification, revision 0.9 the explicit separate Work-mode target (D-014), and revision 0.10 the frozen taxonomy with `external.entity` and the S06 Huawei finding. These do not approve source-asset rights.

Source fingerprint: SHA-256 `af3fd7fe7ff0d6b0b6da937839833bb4fc17b68bcc74f41581865ed1358ad3ee` (575 lines, read on 2026-10-31). The attached file remains unchanged. The baseline is self-contained; another machine does not need the Downloads path. No duplicate normative copy is maintained.

| Source content | Treatment here |
|---|---|
| Sections 1–4, 11–12: goals, functional/non-functional scope, acceptance | Consolidated in requirements sections 1–4 and 7–8; retain original FR/NFR/T IDs where applicable |
| Sections 2, 5–8: taxonomy, provider mappings, separate placement dimensions | Retained as proposed core design in requirements sections 3, 5–6; “accepted” labels are not carried forward as approvals |
| Section 8 illustrative JSON | Not declared executable schema; M1 chooses consistent reference fields and validates fixtures |
| Sections 9–10: local default, platform wrappers, repository structure | D-013 selects per-machine local installation and supersedes D-012; actual local Work feasibility is owner-confirmed; use requested `doc` paths |
| Section 13: broad phases and late platform integration | Replaced with M0–M6 and early runtime proof; complete Work integration is part of release 1 |
| Sections 14–15: risks/open decisions and recommendation | Converted into open decisions, milestone exit evidence and pipeline checks |
| FR-008/028/045/046/047/055, NFR-009/010/011 | Promoted applicable source/view/label/control/limit/version/discovery/CI behavior to P0; optional automation/expansion remains P1 |
| Claude Cowork and ChatGPT Work together | Replace with Work first and future Claude Code. No Cowork compatibility claimed. |
| “Five reference diagrams” vs hybrid acceptance | Require six scenarios: five environment examples plus one combined hybrid model |
| No language/host artifact details | Add FR-060..065, NFR-013..015 and T-013..015 for Work, edits, privacy, labels and packaging |
| User follow-up: plugin portability | Add FR-066; explicitly bundle the skill inside the plugin and require two-machine Work acceptance in T-010 |
| S01 answers: solution architecture and provider-published visual conventions | Add confirmed release-depth boundaries and FR-048/T-016; retain the minimum catalog and prepare six working scenario briefs |
| S01 correction: Kubernetes at detail level | Supersede the earlier cluster-only limit; add shared Kubernetes catalog/rules/detail-view scope and FR-018/FR-029/T-017, with explicit M2/M4 tasks |
| S02 user follow-up: Huawei alternative and draw.io-type on-premises symbols | Assess the alternative without assuming rights/complete coverage; resolve the eight generic symbol concepts under D-010 while retaining source/attribution checks |
| S04 owner correction: per-machine local installation | D-013 supersedes D-012. Update FR-060/064/066 and T-010/011 for local installation/preflight; retire hosting inputs and retain actual Work proof. |

S04 result: [runtime investigation](evidence/S04-runtime-and-hosting.md). Historical loopback HTTP checks are retained as research; the current deliverable is a native local plugin pilot with direct script execution, optional stdio MCP and per-machine setup. Requirements are revision 0.9. Actual Work feasibility is owner-confirmed; final alpha.3 Astra/High review confirms both fixes with no new confirmed actionable runtime finding. [S04/M0 is closed](evidence/S04-closeout.md); full product/two-machine release acceptance remains later work.

## Current verification and sources

Historical planning checks on 2026-10-31 (repository/runner facts superseded by S03 below):

- The local repository initially contained only `.git`; no commits, implementation, existing docs, or workflow files were present. No applicable `AGENTS.md` was found in its ancestor chain.
- Local Git remote: `https://github.com/Rabcat-dome/mingrammer-diagram.git`. GitHub connector metadata lookup returned 404; repository visibility/access and runner registration remain unverified.
- Current shell: Darwin/ARM64; Python found; `dot` absent from this shell PATH. No dependency installation was performed.
- The inspected upstream `diagrams/` directory has AWS/Azure/GCP/onprem/custom entries and no Huawei entry. Snapshot reference: [upstream commit 8c1446f](https://github.com/mingrammer/diagrams/commit/8c1446fbfa4a8d88e5c7bca7101ddc5af7933379). This is research evidence, not the selected dependency pin. Recheck the selected release in M0/M2.
- [Upstream license](https://github.com/mingrammer/diagrams/blob/8c1446fbfa4a8d88e5c7bca7101ddc5af7933379/LICENSE) is MIT. This does not establish third-party icon redistribution rights.

S03 checks on 2026-11-01: [runner/service evidence](evidence/S03-repository-runner-preflight.md) and [actual jobs](evidence/S03-runner-job.json). Under D-011, runner ID 2 was installed, initial tree pushed to main and two jobs passed. Existing seven services stayed loaded; transient broker/offline recovery and the plan limitation were recorded. Those service jobs found no host Graphviz. S04 first tested isolated images, then installed native Graphviz 16.1.0 and bundled fonts. The later runner preflight passed with dot on its PATH; Work feasibility is owner-confirmed. Alpha.3 Astra/High review is complete; product gates remain S05/M1 work.

Platform sources read for planning:

| Source | Supported point |
|---|---|
| [OpenAI plugin quickstart](https://developers.openai.com/plugins/quickstart) | Remote MCP can be connected as a personal plugin and tested in a Work chat; verify actual account access |
| [OpenAI plugins guide](https://learn.chatgpt.com/docs/plugins) | Supported surfaces and capability differences; plugin hooks are not a universal cloud execution path |
| [OpenAI models](https://learn.chatgpt.com/docs/models) | Current model IDs/roles informing our recommended allocation; availability varies |
| [Diagrams installation](https://diagrams.mingrammer.com/docs/getting-started/installation) and [custom nodes](https://diagrams.mingrammer.com/docs/nodes/custom) | Separate Graphviz dependency and custom local icon mechanism |
| [GitHub self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners) | Labels, scheduling and Linux/Docker requirement for container jobs |
| [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use) | Least privilege, untrusted code and persistent runner considerations |

Provider evidence is linked next to semantic anchors in the requirements. Detailed service rules, Huawei documentation and icon terms must be verified during catalog implementation; the supplied draft is not a substitute for primary sources.

S05/M1 result: [core and real CI evidence](evidence/S05-core-and-ci.md). The core 0.2.0a1 package, strict schema/reference/context checks and native quality gate pass 82 tests and actual runner checks at 785e1ee. Astra/High confirmed both initial P2 fixes with no additional actionable findings. This completes M1 foundation only; M2 catalogs/rights/provider semantics and later rendering/Work/two-machine acceptance remain open. No required Docker or model API call was added.

S06/M2 result: [provider catalogs and rights](evidence/S06-provider-catalogs.md). Requirements revision 0.10 adds the `external.entity` taxonomy ID and records the Huawei finding. Catalogs, rules, on-premises assets and both gate lanes pass locally; O-002 remains a blocker, and actual CI and the Astra/High review are outstanding.

M7 preparation result under D-015: [Claude Code plugin evidence](evidence/M7-claude-plugin.md). The requirements baseline is unchanged: the Claude Code adapter stays outside first-release P0, and its acceptance remains M7 work.
