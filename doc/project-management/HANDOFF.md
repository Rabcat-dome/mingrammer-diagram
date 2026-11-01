# Cross-Machine Handoff

Updated: 2026-11-02 | S01-S04 / M0 feasibility complete. S05 / M1 is ready; the full product is not implemented.

## Goal and direction

Build a personal Work-first plugin on mingrammer/diagrams and Graphviz for AWS/Azure/GCP/Huawei/on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code is later. Keep docs English and use the single [requirements v0.9](../requirements/requirements.md).

D-013 selects runtime installation on each machine. Native Python + Graphviz is the default; direct scripts and optional local stdio MCP use the same controlled renderer. Docker, a central service, public renderer and renderer/model API keys are unnecessary. D-014 confirms the separate ChatGPT Work mode/page, not Codex, as the target.

Branch: `codex/s04-runtime-proof`. Alpha.2 review: base `720831733bdb99061f62f7d509d95a65aa7f748b`, head `1fd2d72a22183b65d76ea0bea255702a769ae62f`. Final Astra/High review covered alpha.3 code head `2fc8047242dbbf337a8c44ba09979b2f181adb32`, base 1fd2d72. Later closure commits change only docs/evidence; verify final HEAD when resuming.

## Read order

1. This file and [milestones](milestones.md).
2. Relevant requirements, [current S04 evidence](evidence/S04-native-runtime.md), [Work result](evidence/S04-Work-validation.md) and [setup](../../spikes/s04-local-plugin/README.md).
3. [Final native review](evidence/S04-native-alpha3-review.md), [decisions](decisions.md), [model strategy](model-strategy.md) and [quality gate](quality-gate.md) as needed.

## Verified state

- S01/S02 scope and source research are complete. Huawei asset redistribution/output rights remain O-002; no Huawei pack is bundled. Eight draw.io-type on-premises mappings are selected; exact assets/terms remain M2 work.
- S03 installed separate runner ID 2, `macbook-pro-m2-max-mingrammer`, label `mingrammer-macos-arm64`, preserving seven existing services. S04 preflight run 41328404188 passed and saw native dot 16.1.0/uv 0.13.0. This was the main-branch preflight, not native product CI. Required-check enforcement is unavailable on the current private plan; keep owner-only trust/manual merge discipline. Recheck availability before future jobs.
- Installed identity: `cloud-architecture-diagrams@mingrammer-local`, version `0.1.0-alpha.3`. Source: `spikes/s04-local-plugin/`; package/ZIP are ignored output. Build, register/install with supported CLI and run setup on each Mac. Never edit cache source directly.
- Tested macOS 27.0.1 ARM64, private Python 3.13.7, diagrams 0.25.1, Graphviz 16.1.0, pinned MCP 2.3.0 and bundled Noto Sans/Thai with OFL notices. Setup records source/binary/font hashes. Native dependencies were installed; no global pip/user-font installation occurred.
- Direct script, installed MCP and relocated-ZIP tests pass, including all five artifact reads/hashes and inline PNG equality. Seven path, four resource and six signal/EOF shutdown regressions pass, plus deleted-intermediate and CLI/MCP 1 MiB input bounds. Cancelable nonblocking POSIX stdio uses a small private bridge to pinned MCP 2.3; revalidate it on SDK upgrades.
- Descriptor-anchored artifacts reject symlink components/files and root replacement. Renderer networking is denied by tested macOS sandbox-exec. CPU/file/wall bounds apply; RSS/scratch controls are sampled and can overshoot. English/Thai PNG is readable; cross-machine SVG font appearance remains open.
- The owner confirmed plugin visibility/selectability in the separate Work page, then reported alpha.3/Darwin, visible PNG and all five files after the supplied prompt. See [owner proof](evidence/S04-Work-owner-proof.json). No Work transcript/bundle hashes or independently confirmed MCP/direct-script route were supplied; local byte verification remains separate evidence. This is Work feasibility, not full product/two-machine acceptance.
- Authorized existing chats: host check `01a1964a-784d-7751-bfe5-57e0bbb4cf39`, Astra/High review `01a1964a-7a2a-70e3-a577-84316bb691b0`. The Codex host chat retained alpha.1 and correctly stopped the native check. Computer Use refuses direct ChatGPT UI control; do not bypass or restart the app automatically.
- Astra/High confirmed the alpha.1 symlink fix in alpha.2, then found two P2 issues: helper shutdown left a renderer alive; deleting DOT intermediates could race lstat. Alpha.3 fixes both with targeted/integration regressions. Astra/High confirmed both fixes at 2fc8047 with no new confirmed actionable runtime finding. S04/M0 feasibility is closed in the [closeout](evidence/S04-closeout.md).
- Historical Docker/HTTP/emulated-amd64 research is retained separately. No cloud host, public endpoint, account plugin, merge or product release was created.

## Next steps

1. Start S05 / M1-01..04: core package/schema/diagnostics/reference validation and deterministic quality gate. Use native shell jobs on `mingrammer-macos-arm64`, owner-only trusted execution and a read-only repository token; keep Docker optional. Record actual CI results separately from local checks and prior preflight jobs.
2. Review M1 using Astra/High on its final code. No merge/release is implied. Reuse this checkout and prefer a `codex/s05-core-quality-gate` branch; do not modify unrelated projects or existing runner registrations.
3. M2 resolves catalogs/exact asset rights; M3 final renderer bounds; M4 reference diagrams; M5 polished install/upgrade/removal; M6 two independently prepared machines and full owner release acceptance. Huawei rights remain a packaging/release blocker, not an assumed permission.

## Resume prompt

```text
Start S05 / M1 from doc/project-management/HANDOFF.md and session-plan.md.
Verify Git HEAD, M0 completion and the exact alpha.3 review record before edits.
Use the existing checkout; create a codex/s05-core-quality-gate branch when ready.
Read the single requirements v0.9 and M1-01..04; load other docs only as needed.
Implement the core package/schema/diagnostics/reference checks and deterministic
quality gate on the existing mingrammer-macos-arm64 runner using native shell
steps. Keep owner-only trusted execution, read-only repository permissions and
pinned dependencies/actions. AI review is recorded separately, without mandatory
model API calls. Use Sol/High for contract/security work and Astra/High review.
Preserve the S04 spike/evidence and keep the three-node feasibility fixture
separate from the full provider/Kubernetes product. No required Docker or
central server. Huawei rights remain unresolved; do not bundle uncleared assets.
Validate meaningful negative schema/reference/Kubernetes scope cases, execute
the actual trusted runner job when ready, and record local/CI/owner results
separately. Do not merge/release or claim two-machine acceptance automatically.
Keep all repository docs English; update handoff and activity log with exact
commits, test evidence, remaining tasks and a concise resume prompt.
```
