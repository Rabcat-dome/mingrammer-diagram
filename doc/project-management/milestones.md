# Milestones and Work Breakdown

Updated: 2026-11-05 | Status: S01-S04 / M0 feasibility complete; S05 / M1 complete; S06 / M2 complete on 2026-11-03 for the private personal release. S07 / M3 complete on 2026-11-03 under D-022. S08 / M4 complete on 2026-11-03 under D-023. S09 / M5 complete on 2026-11-05 under D-028. Huawei rights are not cleared: D-018 allows private personal use only, D-019 settles the asset-rights exit item for that use, and O-002 blocks public distribution. M7 Claude Code preparation started early under D-015.

Source of scope: [requirements](../requirements/requirements.md). Model abbreviations and review rules: [model strategy](model-strategy.md). Quality check definitions: [quality gate](quality-gate.md).

## Delivery order

```text
M0 Scope + runtime/icon/runner feasibility
 -> M1 Core contract + first CI checks
 -> M2 Provider catalogs + approved assets
 -> M3 Controlled rendering vertical slice
 -> M4 Five-environment coverage + visual verification
 -> M5 ChatGPT Work plugin
 -> M6 Reproduction + release acceptance

Later: M7 Claude Code adapter acceptance and selected P1 work
```

M0 investigates the Work execution route before core development. M5 delivers the complete plugin; a CLI demonstration is not completion of the first release. Catalog review may proceed by provider, but no parallel agent execution is implied by this plan.

## M0 — Scope and feasibility

Status: Complete for feasibility on 2026-11-02; see [M0/S04 closeout](evidence/S04-closeout.md). D-013/D-014 select per-machine native execution in the separate Work page. Owner reports alpha.3/Darwin, PNG and five files; Astra/High confirmed both earlier P2 fixes with no new confirmed actionable runtime finding. Production/other-OS/two-machine acceptance remains later work; Huawei rights remain unresolved for packaging.

| Task | Work | Dependency / output |
|---|---|---|
| M0-01 | Jointly refine scope, catalog breadth, and six representative diagrams | S01 scope planning complete: D-007/D-008/D-009 confirmed, detailed Kubernetes included, [six working briefs](evidence/S01-release-scope.md) prepared; rendered acceptance remains M4/M6 |
| M0-02 | Compare execution routes against cross-machine plugin delivery; prove Work can invoke a controlled renderer and retrieve SVG/PNG | Complete for the tested local route: [native proof](evidence/S04-native-runtime.md) and [owner Work result](evidence/S04-Work-validation.md); supported-mode and transcript limitations recorded |
| M0-03 | Investigate Huawei icon sources and terms; inventory upstream on-premises gaps | S02 research complete: [rights matrix/gaps](evidence/S02-icon-sources-and-rights.md) and source inventory; Huawei redistribution evidence still open, no extracted assets bundled |
| M0-04 | Verify repository access/visibility, runner assignment, OS/arch/labels, service PATH and tooling | Complete: [S03 runner/service evidence](evidence/S03-repository-runner-preflight.md), two successful actual jobs at `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e`; S04 later verified native Graphviz on service PATH; availability/enforcement limitations recorded |
| M0-05 | Select Python/diagrams/Graphviz/font versions, isolation strategy and numeric limits | Complete for prototype selection: alpha.3 native versions/fonts/direct/MCP, path/resource/shutdown checks and final Astra review pass on macOS ARM64. Sampled limits and production/other-OS gaps are carried to later milestones |

Exit: selected deployment route has real Work evidence; feasibility blockers and proposed fallback are recorded; runner evidence is current; scope is ready for implementation. Documentation alone does not satisfy M0-02 through M0-05.

## M1 — Core contract and CI foundation

Status: Complete on 2026-11-02. [S05 evidence](evidence/S05-core-and-ci.md) records 82 tests, actual fix-head CI/clean-wheel checks and final Astra/High review at 785e1ee. Implementation: Sol/High; review: Astra/High.

| Task | Work | Dependency / output |
|---|---|---|
| M1-01 | Bootstrap Python package, lockfile, CLI shell, development setup | M0-05 -> clean install and tool/version report |
| M1-02 | Implement architecture schema, model, strict/lenient error policy and diagnostics, including Kubernetes cluster/namespace/ownership/placement references | M0-01 -> versioned schema, valid/invalid fixtures; FR-001..006/018/029 |
| M1-03 | Implement ID/reference/cycle checks and view selection validation, including Kubernetes scope/placement separation | M1-02 -> T-008/T-017; ownership/attachment dimensions stay independent |
| M1-04 | Add documentation/static/schema/secret checks and aggregate CI result | M0-04 + working local commands -> first actual product quality-gate job and captured SHA |

Exit: valid JSON passes, malformed/dangling/cyclic input fails, diagnostic contract is stable, local and runner checks agree. No placeholder green jobs for unimplemented render/package checks.

## M2 — Provider semantics, catalogs and icon rights

Status: Complete on 2026-11-03 for the private personal release, at `5f391eb`. [Evidence](evidence/S06-provider-catalogs.md) records actual CI [run 41473877379](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41473877379) passing at `6929253`, including D-016, D-017 and D-018. The owner accepted the on-premises and Huawei icon sheets. Astra/High reviewed `5569459` and found five P2 issues. Under D-020, Claude Fable 5.1 / High, a recorded substitute for Astra/High, [reviewed the fixes](evidence/S06-fable-review.md) at `dc54b4d`, found F5 only partly fixed (N1), and approved `5f391eb` once N1 and N5 were fixed. Actual CI [run 41491565252](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41491565252) passes 12 lanes / 652 tests there. N2-N4 are deferred P3 findings with recorded reasons. D-019 closes the asset-rights exit item for the private personal release; D-018 accepts the risk rather than establishing rights, and O-002 still blocks public distribution. Policy: Sol/Medium, Sol/High for placement rules, review Astra/High. Actual implementation: Claude Opus 5.5, the model of the owner's session.

| Task | Work | Dependency / output |
|---|---|---|
| M2-01 | Freeze taxonomy and exact cloud/platform minimum type inventory | M1-02 -> catalog schema and inventory covering requirements sections 6/6.1. **Complete** |
| M2-02 | Map AWS/Azure/GCP native types and documented placement rules | M2-01 -> mapping records, primary-source links, positive/negative fixtures. **Complete** |
| M2-03 | Add Huawei type/icon mappings, IAM/enterprise-project distinctions and per-service rules | M0-03 + M2-01 + actual rights evidence -> approved assets, SHA-256 manifest and rules; FR-013. S02's technical source candidate is not packaging clearance. **Complete for private personal use only:** types and rules are done, and all 15 items that need an icon have one under D-018. Rights are not cleared, so public distribution stays blocked by O-002. The owner accepted the icon sheet, and rendered visual acceptance stays with M4 and M6 |
| M2-04 | Map on-premises physical/logical components and prepare the eight draw.io-type generic representations | M2-01 + D-010/S02 follow-up -> exact approved symbols/compositions, source conditions/attribution, original/derived hashes and physical-vs-logical fixtures; FR-014. **Complete;** the owner accepted the contact sheet, and rendered visual acceptance stays with M4 and M6 |
| M2-05 | Implement catalog inventory and license/asset checks | M2-02..04 + M2-06 -> every required cloud/Kubernetes item resolves, missing rights/assets fail CI. **Complete;** the `catalog-license` lane is active |
| M2-06 | Add shared Kubernetes detail catalog, provider node-pool/group mappings and semantic rules | M2-01 + M2-02..04 -> FR-018/029; positive/negative cluster/namespace, ownership, Service/Ingress and storage/config/security fixtures across the five hosting environments. **Complete;** the `provider-semantics` lane is active |

Exit: all five hosting inventories and the shared Kubernetes detail catalog meet minimum breadth; rules have evidence; asset rights are established. Do not mark Huawei complete using unapproved icons or undisclosed generic replacements. D-019 settles the asset-rights item for Huawei in the private personal release only.

## M3 — Controlled rendering vertical slice

Status: Complete on 2026-11-03 under D-022, with code at `c8fc687`, and merged into `main`. [Evidence](evidence/S07-controlled-rendering.md) records actual CI [run 41539921034](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41539921034) passing at `cddb497`. Under D-021, [Fable/High requested changes](evidence/S07-fable-review.md) on three P2 findings and approved their fixes at `c8fc687`, which passes actual CI [run 41589907300](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41589907300). Five P3 findings stay open, and the owner passed three samples of the first output. Planned implementation: Sol/High; actual implementation: Claude Opus 5.5 (`claude-opus-5-5`), the model of the session that ran S07. Review: Fable/High.

| Task | Work | Dependency / output |
|---|---|---|
| M3-01 | Build view-to-graph mapper with controlled classes/groups/edges and stable mapping, including separate Kubernetes overview/detail selection | M1 + catalog subset from M2 -> one small diagram, no executable input; preserve namespace/worker-placement dimensions |
| M3-02 | Add SVG/PNG export, portable SVG assets, diagnostic/model/view bundle and manifest | M3-01 -> FR-040..047; validate all outputs before success |
| M3-03 | Implement strict failure and lenient draft fallback behavior | M2 + M3-01 -> T-007 with retained provider/type |
| M3-04 | Add isolation, path/symlink controls, bounded parsing/rendering and SVG checks | M0-05 + M3-02 -> T-009 core cases, timeout cleanup and no runtime downloads |

Exit: repeatable CLI render from a clean setup; invalid input cannot bypass validation; usable SVG/PNG and complete bundle; required security tests pass. This is an engineering slice, not the finished plugin.

## M4 — Coverage and visual quality

Status: Complete on 2026-11-03 under D-023, and merged into `main`. [Evidence](evidence/S08-reference-diagrams.md) records actual CI [run 41664850907](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41664850907) passing at `a407a7a`. [Fable/High approved](evidence/S08-fable-review.md) it there after three P2 findings were fixed, four P3 findings stay open, and the owner passed the 26 views and the Thai sample. Planned implementation: Sol/Medium; actual: Claude Opus 5.5, with Claude Sonnet 5.5 agents writing the models. Review: Fable/High for semantics; optional Terra/Medium for image inspection assistance.

| Task | Work | Dependency / output |
|---|---|---|
| M4-01 | Build AWS, Azure, GCP, Huawei and on-premises reference models | M2 + M3 -> T-001..005 with expected semantics |
| M4-02 | Build one hybrid model containing all five environments | M4-01 -> T-006; explicit link types/trust boundaries |
| M4-03 | Verify TB/LR views, legends, icons, English/Thai labels, non-silent omissions and provider-reference fidelity | M4-01..02 + M4-05 + S01 official references -> reviewed samples, documented deviations and T-016 evidence; FR-048 |
| M4-04 | Add structural/visual regression checks; measure chosen limits and performance with icon views, where the pixel limit can bind before 200 / 300 | M3 -> normalized graph baseline, reviewed visual baseline, T-012 rejection evidence |
| M4-05 | Build detailed Kubernetes subviews and provider-mapping fixtures | M2-06 + M3 -> T-017: workload/Pod/node/namespace, Ingress/Service, storage/config/security relationships and cross-view stable IDs; cover EKS/AKS/GKE/CCE/on-premises |

Exit: six reference scenario families and their required Kubernetes detail subviews inspected by the owner/reviewer; T-017 passes and all required catalog entries have resolution/rule fixtures even if not all appear in one image. Record performance measurements; P1 automatic splitting and 200/300 stress work can remain deferred explicitly.

## M5 — ChatGPT Work integration

Status: **Complete on 2026-11-05 under D-028, and merged into `main`. M5-04's [five checks in Work](evidence/S09-Work-validation.md#result) pass on `0.1.0-alpha.1+d27ef23f6f94`, on the owner's report (D-027).** M5-01..03 are built and merged into `main`, and M5-04's automated part passes through the host's real engine. See the [S09 evidence](evidence/S09-work-plugin.md). [Fable/High approved](evidence/S09-fable-review.md) the code at `aa813ed`, which passes actual CI [run 41695136756](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41695136756). Planned implementation: Sol/High for local adapter/isolation, Sol/Medium for skill/docs; actual: Claude Opus 5.5. Review: Fable/High.

| Task | Work | Dependency / output |
|---|---|---|
| M5-01 | Implement selected tool adapter and capability discovery | M0-02 + M3 -> schema/catalog/validate/render/info contracts; FR-055/063/064 |
| M5-02 | Implement local runtime setup/preflight/upgrade/removal and scoped artifact retrieval/isolation/retention | M5-01 -> actual deployment-mode tests; NFR-013 |
| M5-03 | Package the versioned Work plugin with bundled skill, tool configuration and progressive-loading references | M4 + M5-01 -> installable product and repeatable setup/enablement instructions; FR-060/061/065/066 |
| M5-04 | Run actual Work installation, discovery, rendering, invalid input and edit flows, including Kubernetes overview/detail requests | M5-02..03 -> T-011/013/014/017; preview/download evidence, stable IDs |

Exit: installed plugin works in the selected Work mode, artifacts are retrievable, supported host modes are stated accurately. Local CLI or MCP protocol tests alone do not satisfy M5-04. D-013 selects per-machine local installation; no central host or cloud provisioning is required.

## M6 — Reproduction and personal release

Status: Open. Under D-024, [S10](evidence/S10-release-checks.md) did the clean-runtime core reproduction in M6-01 and all of M6-02, including the [P0 report](evidence/S10-p0-traceability.md), and [Fable/High approved](evidence/S10-fable-review.md) that part at `debd754`. M6-01's run on a second machine, M6-03 and M6-04 remain, so nothing is released. Implementation: Sol/Medium; final review: Fable/High and owner inspection.

| Task | Work | Dependency / output |
|---|---|---|
| M6-01 | Install/enable the same plugin version and complete the Work workflow on two supported machines; independently reproduce the core in a clean runtime | M5 -> T-010, plugin/version/setup/auth/artifact evidence from both machines, plus core reproduction results |
| M6-02 | Verify distribution contents, notices, full P0 traceability and clean-install smoke test | M1..M5 -> T-015, requirement-to-check/evidence report |
| M6-03 | Review final diff, six scenarios, release risks and unresolved findings | M6-01..02 -> review report at release SHA; owner disposition |
| M6-04 | Tag/package the personal release and update handoff/activity log | M6-03 -> reproducible artifact/checksums; installation and rollback notes |

Exit: all P0 pass; no unresolved Critical/High findings; justified Medium findings have owner disposition; actual Work plugin acceptance on two machines and clean-runtime reproduction evidence exist. No public directory submission is required.

## M7 — Claude Code adapter and later work

Status: Adapter preparation started under D-015; not complete and not a first-release requirement. See [M7 evidence](evidence/M7-claude-plugin.md). Implementation: Claude Opus 5.5, the model of the owner's session rather than a project selection. A same-session review and a separate-session Claude review ran; all their findings are fixed. Under D-021, [Fable/High approved `c5f74b4..c6a59e5`](evidence/M7-fable-review.md) The P2 it found at the head, from S06, is fixed and confirmed at `c8fc687`, and three P3 findings stay open.

| Task | Work | Dependency / output |
|---|---|---|
| M7-01 | Package the core as an installable Claude Code plugin with marketplace, bundled skill and command wrapper, reusing the core without a second copy | M1 + D-015 -> complete locally; `plugins/cloud-architecture-diagrams`, validate-only |
| M7-02 | Add plugin package and wheel-content checks to the quality gate | M7-01 -> complete; `claude-plugin` and `package-contents` lanes passed actual CI, most recently run 41453874994 at `917f46f` |
| M7-03 | Verify actual Claude Code installation and invocation | M7-01 -> local-path, private GitHub and real-config installs, plugin update, English/Thai/edit invocations and a Code tab runtime check verified on one Mac; interactive permission prompts, `allowed-tools` breadth and a second machine remain |
| M7-04 | Expose catalog discovery and rendering through the plugin as M2/M3 arrive, then update the skill's stated capabilities and plugin version | M2 + M3 -> catalog discovery and semantic validation reach the plugin and its skill in S06. S07 adds `render` to the skill and passes the clean-copy lane in actual CI at `cddb497`. A live session first rendered through `--plugin-dir` in S08, after a skill correction, on one Mac; see the [M7 evidence](evidence/M7-claude-plugin.md). The plugin stays versioned by commit, so no version bump applies |

Exit: the same plugin version installs from the private repository on two machines and produces validated models and, after M3, retrievable SVG/PNG in actual Claude Code sessions, with independent review recorded.

Later work, not scheduled:

- P1 view presets, YAML, aliases, enterprise packs, PDF/DOT, automatic splitting, 200/300 stress validation, and expanded catalog coverage.
- Optional shared-team features, IaC import/discovery, or public publication only under a separate scope decision.

## Planning discipline

Use one task ID per issue/PR when tracking begins. Each task records implementation model/effort, reviewed commit, review model/effort, checks, findings, and artifact evidence. Dependencies are exit conditions, not calendar promises. Estimate dates after M0 runtime/icon/runner uncertainties are resolved; do not treat this plan as a delivery commitment.
