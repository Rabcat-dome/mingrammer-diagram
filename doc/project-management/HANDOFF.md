# Cross-Machine Handoff

Updated: 2026-11-02 | M0/S04 in progress. Native alpha.2 direct-script/MCP checks pass; exact Work-mode/UI and fresh native review remain pending.

## Goal and current direction

Build a personal Work-first architecture plugin for AWS/Azure/GCP/Huawei/on-premises with detailed Kubernetes and provider-reference visuals. Claude Code is later. Keep docs English and use the single [requirements v0.8](../requirements/requirements.md).

D-013 selects installation on every machine and supersedes central hosting. After the owner questioned Docker, the implementation default became **native Python + Graphviz**, with a direct script command and optional stdio MCP helper. Docker is not required. MCP stdio is a local process interface, not a central/listening server. Do not reopen provider/project/region/budget questions or require a renderer/model API key.

Branch: `codex/s04-runtime-proof`. The alpha.1 review covered base `afbaccad87019d35bff12d335ec534166752f0bf` through `720831733bdb99061f62f7d509d95a65aa7f748b`; native source is newer. Native source checkpoint: `b5524a916d36256335ccfe6c1f1ecc3f2ed4e31d`. Verify final HEAD before review.

## Read order

1. This file and [milestones](milestones.md).
2. Relevant requirement IDs, [native S04 evidence](evidence/S04-native-runtime.md) and [setup/direct script](../../spikes/s04-local-plugin/README.md).
3. [Review record](evidence/S04-astra-review.md), [decisions](decisions.md), [model strategy](model-strategy.md) and [quality gate](quality-gate.md) as needed.

## Verified state

- S01 scope planning and S02 source/rights research are complete. Solution architecture with detailed Kubernetes remains required. Huawei redistribution/extraction/output-use rights remain O-002; no Huawei package is cleared/bundled. Eight draw.io-type generic on-premises mappings are selected, with exact assets/terms/export later in M2.
- S03/M0-04 installed separate runner ID 2, `macbook-pro-m2-max-mingrammer`, label `mingrammer-macos-arm64`. Two initial jobs passed; historical transient broker/offline recovery and private-plan enforcement limits are in [S03 evidence](evidence/S03-repository-runner-preflight.md). Recheck availability before jobs. No M1 product gate exists yet.
- Alpha.2 installed identity: `cloud-architecture-diagrams@mingrammer-local`. Source is `spikes/s04-local-plugin/`; generated package/ZIP are ignored. The supported CLI installer preserves identity/marketplace and updates the cache; never edit cache source directly.
- Native runtime: macOS 27.0.1 ARM64, private Python 3.13.7 environment, diagrams 0.25.1, Graphviz 16.1.0, SDK 2.3.0 and bundled Noto Sans/Thai with OFL notices. Setup uses uv and records native binary/font/source hashes. Homebrew installed Graphviz/dependencies and three required dependency upgrades; no global pip/user-font installation was made. See the native proof for exact changes.
- Direct script, installed MCP and relocated-ZIP SDK tests pass. All five files and inline PNG match hashes. Seven filesystem regressions and resource cases cover timeout, RSS, scratch bytes and an exited parent with a live descendant. Renderer networking is denied by the tested macOS profile. RSS/disk limits are sampled, not kernel quotas or Docker isolation; production NFR-009 acceptance remains open.
- Output paths are private real directories, opened without following symlink components; descriptor-relative artifact access and root identity checks fix the confirmed P2 alpha.1 finding. Native PNG English/Thai text is readable. Cross-machine SVG font appearance and another physical machine remain untested.
- The owner authorized two local chats: host test `01a1964a-784d-7751-bfe5-57e0bbb4cf39` and Astra/High review `01a1964a-7a2a-70e3-a577-84316bb691b0`. Both completed alpha.1 work. [Live host evidence](evidence/S04-work-host-check.md) establishes Codex Desktop tool calls/artifact reads, not a different ChatGPT Work mode. Computer Use refused direct ChatGPT UI access; no bypass was attempted.
- Astra/High completed the frozen alpha.1 review with one P2 output-root symlink finding; locally fixed/tested in alpha.2. The old review does not cover the new native diff.
- A parent-chat call still reported alpha.1 after installing alpha.2. Existing MCP connections can retain the old Docker process; a fresh/reloaded local chat must report alpha.2/Darwin/native before its results count as native. Fresh native host discovery and SDK checks are separate evidence, not proof of a specific Work UI.
- Historical Docker/HTTP/emulated-amd64 results remain under `spikes/s04-runtime/`. No cloud host, public endpoint, account upload or product release was created. Existing Docker software/images were not uninstalled and are not needed by the native path.

## Next steps

1. Use the native follow-up's exact prompts to review the new diff with Astra/High and test alpha.2 in a fresh/reloaded local host. Record exact versions/base/head and findings. Do not relabel the alpha.1 review as approval of native code.
2. Obtain actual ChatGPT Work mode/UI preview/export evidence, with owner help where the app cannot inspect itself. Do not equate SDK/native Codex success with another Work mode.
3. Finalize supported modes, native resource/transport limits and M0-02/M0-05 exit evidence. Keep sampled-limit/OS/SVG/second-machine gaps explicit. S04/M0 is not closed; do not start S05 as if it were.
4. Then continue S05/M1 schema/core package and deterministic CI on native runner shell steps. Keep Docker optional. Preserve owner-only self-hosted trust and manual merge discipline until the real product gate exists.
5. Carry O-002 and exact generic/Kubernetes asset/rule tasks into M2/M4. M5 must deliver polished install/preflight/upgrade/removal; M6 must complete the same version on two independently prepared supported machines.

## Resume prompt

```text
Continue from doc/project-management/HANDOFF.md on codex/s04-runtime-proof.
D-013 is per-machine local installation. Native alpha.2 uses Python/Graphviz
and direct scripts; Docker and a central server are not required. Read native
S04 evidence and actual review/host state, verify Git HEAD, then complete the
native review and exact Work-mode proof. Keep docs English and distinguish
local SDK, live Codex host, actual Work UI, CI and owner acceptance.
```
