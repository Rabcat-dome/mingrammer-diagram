# Cross-Machine Handoff

Updated: 2026-11-02 | S04 final review pending. Native alpha.3 checks pass; the owner confirms actual Work alpha.3/Darwin, visible PNG and all five exports.

## Goal and direction

Build a personal Work-first plugin on mingrammer/diagrams and Graphviz for AWS/Azure/GCP/Huawei/on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code is later. Keep docs English and use the single [requirements v0.9](../requirements/requirements.md).

D-013 selects runtime installation on each machine. Native Python + Graphviz is the default; direct scripts and optional local stdio MCP use the same controlled renderer. Docker, a central service, public renderer and renderer/model API keys are unnecessary. D-014 confirms the separate ChatGPT Work mode/page, not Codex, as the target.

Branch: `codex/s04-runtime-proof`. Alpha.2 review: base `720831733bdb99061f62f7d509d95a65aa7f748b`, head `1fd2d72a22183b65d76ea0bea255702a769ae62f`. Alpha.3 changes are newer; verify final HEAD and exact re-review evidence.

## Read order

1. This file and [milestones](milestones.md).
2. Relevant requirements, [current S04 evidence](evidence/S04-native-runtime.md), [Work result](evidence/S04-Work-validation.md) and [setup](../../spikes/s04-local-plugin/README.md).
3. [Native review](evidence/S04-native-alpha2-review.md), [decisions](decisions.md), [model strategy](model-strategy.md) and [quality gate](quality-gate.md) as needed.

## Verified state

- S01/S02 scope and source research are complete. Huawei asset redistribution/output rights remain O-002; no Huawei pack is bundled. Eight draw.io-type on-premises mappings are selected; exact assets/terms remain M2 work.
- S03 installed separate runner ID 2, `macbook-pro-m2-max-mingrammer`, label `mingrammer-macos-arm64`, preserving seven existing services. S04 preflight run 41328404188 passed and saw native dot 16.1.0/uv 0.13.0. This was the main-branch preflight, not native product CI. Required-check enforcement is unavailable on the current private plan; keep owner-only trust/manual merge discipline. Recheck availability before future jobs.
- Installed identity: `cloud-architecture-diagrams@mingrammer-local`, version `0.1.0-alpha.3`. Source: `spikes/s04-local-plugin/`; package/ZIP are ignored output. Build, register/install with supported CLI and run setup on each Mac. Never edit cache source directly.
- Tested macOS 27.0.1 ARM64, private Python 3.13.7, diagrams 0.25.1, Graphviz 16.1.0, pinned MCP 2.3.0 and bundled Noto Sans/Thai with OFL notices. Setup records source/binary/font hashes. Native dependencies were installed; no global pip/user-font installation occurred.
- Direct script, installed MCP and relocated-ZIP tests pass, including all five artifact reads/hashes and inline PNG equality. Seven path, four resource and six signal/EOF shutdown regressions pass, plus deleted-intermediate and CLI/MCP 1 MiB input bounds. Cancelable nonblocking POSIX stdio uses a small private bridge to pinned MCP 2.3; revalidate it on SDK upgrades.
- Descriptor-anchored artifacts reject symlink components/files and root replacement. Renderer networking is denied by tested macOS sandbox-exec. CPU/file/wall bounds apply; RSS/scratch controls are sampled and can overshoot. English/Thai PNG is readable; cross-machine SVG font appearance remains open.
- The owner confirmed plugin visibility/selectability in the separate Work page, then reported alpha.3/Darwin, visible PNG and all five files after the supplied prompt. See [owner proof](evidence/S04-Work-owner-proof.json). No Work transcript/bundle hashes were supplied; local byte verification remains separate evidence. This is Work feasibility, not full product/two-machine acceptance.
- Authorized existing chats: host check `01a1964a-784d-7751-bfe5-57e0bbb4cf39`, Astra/High review `01a1964a-7a2a-70e3-a577-84316bb691b0`. The Codex host chat retained alpha.1 and correctly stopped the native check. Computer Use refuses direct ChatGPT UI control; do not bypass or restart the app automatically.
- Astra/High confirmed the alpha.1 symlink fix in alpha.2, then found two P2 issues: helper shutdown left a renderer alive; deleting DOT intermediates could race lstat. Alpha.3 fixes both with targeted/integration regressions. Final independent re-review remains pending.
- Historical Docker/HTTP/emulated-amd64 research is retained separately. No cloud host, public endpoint, account plugin, merge or product release was created.

## Next steps

1. Re-review the frozen alpha.3 head with Astra/High, resolve confirmed findings and record exact base/head. Owner already authorized follow-ups to both existing chats until S04 finishes.
2. Once re-review passes, summarize M0 feasibility and close S04 with the actual Work owner evidence. Keep production hard-limit/OS/SVG/asset-rights gaps assigned to later milestones; do not claim release acceptance.
3. Continue S05/M1 core schema/package and deterministic native CI. Docker remains optional. M2 handles catalogs/approved assets; M5 polished installation/upgrade/removal; M6 the same version on two independently prepared supported machines.

## Resume prompt

```text
Continue from doc/project-management/HANDOFF.md on codex/s04-runtime-proof.
D-013 is per-machine native Python/Graphviz installation; D-014 targets the
separate ChatGPT Work page. Alpha.3 script/MCP checks pass and the owner reports
Work alpha.3/Darwin, a visible PNG and five exports. Verify final HEAD and actual
Astra re-review status, finish S04, then start S05 only after M0 closure.
Keep English docs and distinguish local SDK, Codex host, owner Work evidence,
CI and full product/two-machine acceptance.
```
