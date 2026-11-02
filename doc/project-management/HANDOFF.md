# Cross-Machine Handoff

Updated: 2026-11-02 | S05 / M1 in progress. Core/schema/local quality gate pass; actual runner execution and independent review are next. S04/M0 remains complete.

## Goal and direction

Build a personal Work-first plugin on mingrammer/diagrams and Graphviz for AWS/Azure/GCP/Huawei/on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code is later. Keep docs English and use the single [requirements v0.9](../requirements/requirements.md).

D-013 selects runtime installation on each machine. Native Python + Graphviz is the default; direct scripts and optional local stdio MCP use the same controlled renderer. Docker, a central service, public renderer and renderer/model API keys are unnecessary. D-014 confirms the separate ChatGPT Work mode/page, not Codex, as the target.

Current branch: `codex/s05-core-quality-gate`, base `ff53a88944e981be2bbbab171e0ccf8cecdb4e41`. See [S05 implementation/evidence](evidence/S05-core-and-ci.md) and [core guide](../design/core-contract.md). Historical S04 branch: `codex/s04-runtime-proof`. Alpha.2 review: base `720831733bdb99061f62f7d509d95a65aa7f748b`, head `1fd2d72a22183b65d76ea0bea255702a769ae62f`. Final Astra/High review covered alpha.3 code head `2fc8047242dbbf337a8c44ba09979b2f181adb32`, base 1fd2d72. Later closure commits change only docs/evidence; verify final HEAD when resuming.

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

1. Complete S05 actual GitHub runner execution, record tested SHA/report and obtain independent Astra/High review of the frozen M1 diff. Core local checks and clean-wheel/missing-tool probes pass; this is not yet milestone closure.
2. Apply confirmed review fixes and rerun affected local/CI checks. Keep provider/catalog/renderer/Work plugin and release acceptance separate; installed S04 alpha.3 source is unchanged.
3. After M1 closure, S06/M2 freezes provider/Kubernetes catalogs and exact approved assets. Huawei rights remain unresolved; do not bundle uncleared assets. Later milestones are unchanged.

## Resume prompt

```text
Continue S05/M1 from doc/project-management/evidence/S05-core-and-ci.md on
codex/s05-core-quality-gate. Read doc/design/core-contract.md, relevant
requirements and M1-01..04. Verify Git HEAD, local/CI results and independent
Astra review status. Finish actual runner evidence and review/fixes before
closing S05. Keep English docs, core_only disclosure, native execution,
owner-only self-hosted trust and separate local/CI/Work/release evidence.
No merge, cloud service, Docker cleanup or product release is implied.
```
