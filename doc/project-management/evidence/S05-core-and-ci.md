# S05 / M1 Core Contract and Quality Gate Complete

Completed: 2026-11-02 (Asia/Bangkok) | Branch: `codex/s05-core-quality-gate`.
Milestone base: `ff53a88944e981be2bbbab171e0ccf8cecdb4e41`.
Final reviewed/tested executable source: `785e1eecb646476691859f14dd4399ac564011ca`.

**M1-01..04 / S05 are complete. S06 / M2 is ready.** This delivers the core foundation and first actual deterministic quality gate, not full architecture rendering or the product plugin.

## Delivered and verified

| Task | Implementation / exit evidence |
|---|---|
| M1-01 | Package 0.2.0a1, Python 3.13.7, hash-locked runtime/development dependencies, CLI/discovery and wheel/sdist. Clean installation of the actual CI wheel outside the checkout validated the fixture and rejected the ownership bypass in both modes |
| M1-02 | Closed strict [schema](../../../schemas/architecture-v1.schema.json), model/views/context, parser bounds and stable structured diagnostics. Positive fixtures pass independent JSON Schema and core checks; structural/security errors remain fatal in strict/lenient modes |
| M1-03 | Stable/global IDs, typed/dangling refs, scope ownership, cycles, explicit views/exclusions, independent Kubernetes cluster/namespace/owner/node/storage/config references. Both ownership encodings now share context validation; full suite 82 tests |
| M1-04 | Native [workflow](../../../.github/workflows/quality-gate.yml), same local aggregate command, reports and cleanup. Actual fix-head CI passed all eight lanes/82 tests on the project runner; independent Astra/High review confirmed both initial P2 fixes |

Use the [contract/setup guide](../../design/core-contract.md). Core validation always discloses `core_only` and pending catalog/provider/render checks. No render command is exposed. Existing S04 Work plugin/runtime stays alpha.3; this core development package is separate. Huawei assets/rights, provider semantics, production rendering, full Work integration and second-machine release acceptance remain their existing milestones.

## Evidence

- Initial [run 41423620941](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41423620941), job 125204824039, passed eight lanes/65 tests at e645415; [historical gate](S05-quality-gate-initial.json). That result did not cover later fixes.
- Final code [run 41426653007](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41426653007), job 125214762630, passed eight lanes/82 tests at 785e1ee; [final gate](S05-quality-gate-final.json). Clean checkout, exact source/lock hashes and cleanup were verified.
- [Validation proof](S05-validation-proof.json) records the actual CI job, clean-wheel install, identical local/CI wheel checksum, strict/lenient ownership rejection, initial missing-actionlint failure probe, model settings and read-only trust snapshot.
- [Astra review](S05-astra-review.md): initial two P2 issues were independently reproduced, fixed with failing-then-passing regressions and confirmed at the final source head. No additional actionable findings. A suspected newline defect was disproved; it is not a third finding.

Actual implementation model: GPT-6.1 Sol / XHigh, inherited from the current app setting; no model setting was changed. Independent review: GPT-6 Astra / High. No paid model API call was added to CI or core validation.

## Gate scope and constraints

Active lanes: docs-contract, secrets, lint, format, types, workflow, schema-core and package-build. Future catalog/license/provider/render/visual/plugin checks are deferred explicitly, never reported passed. Credential matching is narrow, not a full history/entropy audit. Static checks cover implemented core/scripts/tests; historical S04 spike source remains separately frozen/reviewed.

Only explicit owner actions in the private repository schedule this personal runner. API checks found only Rabcat-dome/admin and fork-PR workflows disabled, with fork write tokens/secrets disabled. Actor guards supplement those server-side access settings; editable workflow conditions alone are not a tamper-resistant boundary. Settings/registrations were preserved. The current repository plan still lacks server-enforced required checks; retain manual review/merge discipline.

Core parsing bounds are 1 MiB, 64 JSON levels, 1000 combined entities, 4000 relationships, 32 views and 100 error diagnostics. These are not final renderer-size or kernel resource guarantees. Full T-017/provider/visual/Work acceptance remains M2/M4/M5/M6. No new Work test or two-machine claim is made by this milestone.

Source after 785e1ee is unchanged by closure documentation. The final documentation commit also runs the gate through the existing owner-push trigger; verify its latest job when resuming. Main is unchanged; no merge, cloud deployment, Docker cleanup, account-plugin upload or product release occurred.
