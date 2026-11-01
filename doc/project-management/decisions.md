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

## Recommendations and disposition

| ID | Proposal | Rationale / resolution point |
|---|---|---|
| P-001 | Canonical JSON + taxonomy + provider catalogs + controlled renderer; wrap upstream first | Retains semantics and portability; freeze contract in M1 |
| P-002 | Installable plugin with a bundled workflow skill and renderer tools | Product structure retained; D-013 replaces the original remote-service recommendation with local runtime installation. |
| P-003 | Local stdio MCP on each supported desktop, with per-machine installer/preflight | Selected route under D-013; Alpha.2 uses native Python/Graphviz with a direct script and stdio; the earlier Docker runtime is historical. Actual Work behavior remains pending. |
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
| P-017 | Native private Python environment + system Graphviz, with direct script and stdio interfaces | Implemented in alpha.2 after the owner questioned Docker and requested continuation. No required Docker/server. Native checks pass; exact Work mode, fresh native review and final production limits remain pending. |

P-015 is historical. P-017 is the current native implementation default, not proof of every OS or final product limits. P-002's plugin structure remains; P-003's local route is selected by D-013. P-009/P-010 are resolved by D-007/D-008 with D-009's detailed-Kubernetes correction.

P-011/P-013 are source recommendations, not user decisions or packaging clearance. D-010 resolves the on-premises symbol direction from P-012 without granting third-party rights or approving a specific source package.

## Open decisions

| ID | Question | Working assumption / next action | Needed by |
|---|---|---|---|
| O-001 | Which Work execution modes satisfy the cross-machine plugin requirement? | D-013 selects local per-machine installation; prove Work Desktop/local tool invocation, preview and export. SDK/cache checks do not prove actual Work behavior. | M0-02 |
| O-002 | Which Huawei icon source/version and redistribution terms are acceptable? | LATAM v3.2 / commit 52c33aa12fb816a5de403da85067e1c0f039b5be covers 17 named items technically. The user supplied JuanDiaz00's 155-PNG alternative, whose README names VeryIcon; that site claims free personal/commercial use, but source-asset plugin redistribution remains unestablished in audited evidence. No source is adopted/cleared and no permission request was sent. | M2-03/package release |
| O-003 | Which exact product variants/type IDs implement the minimum catalog? | Retain the five environments and named inventory, plus detailed Kubernetes kinds under D-009/FR-018/FR-029. M2 freezes cloud/platform variants, API versions and IDs against current documentation. | M2-01/M2-06 |
| O-004 | Which exact rendered examples establish visual acceptance? | Direction resolved as D-008: white/provider-icon visuals close to each provider's published conventions. Six briefs and official source entry points are prepared; actual image comparison/acceptance remains M4/M6 work (FR-048/T-016). | M4-03/M6 |
| O-005 | Which runner is eligible for this repository, with which trust/visibility policy? | Resolved by D-011 and S03: private repository; owner-only manual workflow on `main`; separate runner ID 2, v2.338.2, project label and actual service environment verified by two successful jobs. The current plan lacks server-enforced required checks; retain manual merge/release discipline and recheck availability before future jobs. | Resolved in S03 / M0-04 |
| O-006 | Which hosting destination/project/region/budget is needed? | Retired: D-013 supersedes central hosting. No owner hosting answer or cloud deployment is needed. Per-machine prerequisites are implementation evidence under O-001. | Closed by scope change |
| O-007 | Which versions/fonts/isolation and numeric limits are practical? | Native alpha.2 tests Python 3.13.7, diagrams 0.25.1, Graphviz 16.1.0, SDK 2.3.0 and bundled Noto fonts on macOS ARM64. CPU/file/wall limits and sampled RSS/scratch controls pass targeted checks; full production/Work bounds remain open. Historical container quotas do not apply to native execution. | M0-05/M1 |
| O-008 | What architecture granularity is required in release 1? | Resolved by D-007/D-009: solution architecture overall with detailed Kubernetes views. Existing required items such as Azure NIC remain in scope. | Resolved in S01 |

Proposed numeric limits are not benchmarks or implemented guarantees. The reference host and actual Work transport/request limits may require lower limits or a later asynchronous job design.

S01 result record: [release scope and scenario briefs](evidence/S01-release-scope.md). Scope-planning work is complete with explicit granularity/style answers; the record separates confirmed decisions from working examples and later acceptance evidence.

S02 research record: [sources, rights and gaps](evidence/S02-icon-sources-and-rights.md), with [structured inventory](evidence/S02-icon-inventory.json). M0-03 research is complete; Huawei package clearance is unresolved. S03/S04 can proceed without treating that clearance as granted.

S02 follow-up: [additional Huawei source and draw.io mappings](evidence/S02-additional-icon-sources.md), with [supplemental metadata](evidence/S02-supplemental-icons.json). Eight on-premises concepts are mapped; exact export/visual/asset-condition checks remain M2/M4 work. Source and stencil terms are recorded separately from application-code licenses.

## Source reconciliation

Input: `cloud-architecture-diagram-plugin-requirements.md`, document CADP-REQ-001 v1.1, supplied from the owner's Downloads folder. This repository's revision 0.8 is a planning baseline, not evidence of a v1.1 implementation release. Revision 0.2 added cross-machine delivery, revision 0.3 initial S01 depth/style, revision 0.4 detailed Kubernetes, revision 0.5 draw.io-type on-premises mappings under D-010/FR-014, revision 0.6 the historical central-server target under D-012, and revision 0.7 the superseding local-install route under D-013, and revision 0.8 the native default/direct-script clarification. These do not approve source-asset rights.

Source fingerprint: SHA-256 `af3fd7fe7ff0d6b0b6da937839833bb4fc17b68bcc74f41581865ed1358ad3ee` (575 lines, read on 2026-10-31). The attached file remains unchanged. The baseline is self-contained; another machine does not need the Downloads path. No duplicate normative copy is maintained.

| Source content | Treatment here |
|---|---|
| Sections 1–4, 11–12: goals, functional/non-functional scope, acceptance | Consolidated in requirements sections 1–4 and 7–8; retain original FR/NFR/T IDs where applicable |
| Sections 2, 5–8: taxonomy, provider mappings, separate placement dimensions | Retained as proposed core design in requirements sections 3, 5–6; “accepted” labels are not carried forward as approvals |
| Section 8 illustrative JSON | Not declared executable schema; M1 chooses consistent reference fields and validates fixtures |
| Sections 9–10: local default, platform wrappers, repository structure | D-013 selects per-machine local installation and supersedes D-012; actual local Work capability proof remains pending; use requested `doc` paths |
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

S04 result: [runtime investigation](evidence/S04-runtime-and-hosting.md). Historical loopback HTTP checks are retained as research; the current deliverable is a native local plugin pilot with direct script execution, optional stdio MCP and per-machine setup. Requirements are revision 0.8. Actual Work proof, second-machine release acceptance and separate Astra review remain pending; M0-02/M0-05 are not closed.

## Current verification and sources

Historical planning checks on 2026-10-31 (repository/runner facts superseded by S03 below):

- The local repository initially contained only `.git`; no commits, implementation, existing docs, or workflow files were present. No applicable `AGENTS.md` was found in its ancestor chain.
- Local Git remote: `https://github.com/Rabcat-dome/mingrammer-diagram.git`. GitHub connector metadata lookup returned 404; repository visibility/access and runner registration remain unverified.
- Current shell: Darwin/ARM64; Python found; `dot` absent from this shell PATH. No dependency installation was performed.
- The inspected upstream `diagrams/` directory has AWS/Azure/GCP/onprem/custom entries and no Huawei entry. Snapshot reference: [upstream commit 8c1446f](https://github.com/mingrammer/diagrams/commit/8c1446fbfa4a8d88e5c7bca7101ddc5af7933379). This is research evidence, not the selected dependency pin. Recheck the selected release in M0/M2.
- [Upstream license](https://github.com/mingrammer/diagrams/blob/8c1446fbfa4a8d88e5c7bca7101ddc5af7933379/LICENSE) is MIT. This does not establish third-party icon redistribution rights.

S03 checks on 2026-11-01: [runner/service evidence](evidence/S03-repository-runner-preflight.md) and [actual jobs](evidence/S03-runner-job.json). Under D-011, runner ID 2 was installed, initial tree pushed to main and two jobs passed. Existing seven services stayed loaded; transient broker/offline recovery and the plan limitation were recorded. Those service jobs found no host Graphviz. S04 subsequently installed Graphviz/fonts inside isolated local images; product gate/Work/model-review evidence remains pending.

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
