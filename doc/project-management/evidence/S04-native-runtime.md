# S04 Native Runtime Follow-up

Dates: 2026-11-01 to 2026-11-02 (Asia/Bangkok) | Scope: M0-02/M0-05, fixed three-node prototype | Version: 0.1.0-alpha.2.

The owner questioned why Docker was needed and pointed out direct script execution. Docker was an implementation choice, not a user requirement. The native default now executes controlled Python scripts with system Graphviz. The plugin remains versioned/installable, with its workflow skill and optional local stdio MCP interface. No central service or listening HTTP port is required. This implements D-013 with less installation overhead; it does not add cloud-only support.

## Verified native behavior

[Proof JSON](S04-native-runtime-proof.json) contains source/archive hashes, installed dependency inventory, executable/font provenance and actual checks. [Setup/direct-command instructions](../../../spikes/s04-local-plugin/README.md) reproduce the pilot.

- Direct script rendering passed with a Docker executable shim that fails if invoked and a remote DOCKER_HOST value. The shim was not invoked; Docker is not on the renderer's controlled PATH.
- Installed alpha.2 MCP and a ZIP relocated to a path containing spaces passed discovery, preflight, three literal English/Thai labels, five artifact reads, matching byte/hash checks, inline PNG equality and invalid-input checks.
- Seven filesystem regressions passed: root symlink, ancestor symlink, artifact symlink, non-regular artifact, oversize artifact, root replacement and atomic cleanup after integrity failure. This addresses the confirmed alpha.1 output-root finding.
- Actual subprocess tests triggered and terminated on wall timeout, sampled group RSS and sampled scratch-space limits, including a parent that exited while its descendant held the pipes open. The setup's macOS network-denial probe returned EPERM. Native renderer children use that same sandbox-exec policy.
- [PNG](S04-native-runtime-fixture.png) was visually inspected: English/Thai labels and arrows readable, no observed clipping. The matching [SVG](S04-native-runtime-fixture.svg) still references fonts rather than embedding them; cross-machine SVG appearance remains open.

## Native runtime and host changes

| Component | Actual native candidate |
|---|---|
| Host | macOS 27.0.1 ARM64; Python 3.13.7 |
| Python packages | diagrams 0.25.1, Python graphviz 0.20.3, MCP 2.3.0, hash-locked private environment |
| Native engine | Homebrew Graphviz 16.1.0 and Fontconfig 2.18.3; executable hashes recorded and checked |
| Fonts | Noto Sans 2.015 and Noto Sans Thai 2.002; exact bytes match the historical container fonts; bundled OFL notices and pinned upstream release/archive/file hashes |
| Network | Renderer/descendants denied by the tested macOS sandbox-exec profile; helper uses stdio, no listener |
| Limits | 55 s wall; 45/50 s CPU; 16 MiB per file; 1 GiB sampled process-group RSS; 256 MiB sampled scratch size |

Installing Graphviz added its native dependencies. Homebrew also upgraded three required dependencies: libunistring 1.4.2 to 1.5, libvmaf 3.1.0 to 3.2.1 and dav1d 1.5.3 to 1.5.4; automatic cleanup was disabled. A fresh login shell resolves dot 16.1.0. [Actual runner preflight](S04-native-runner-preflight.json) run 41328404188 passed on the existing main-branch workflow and found dot 16.1.0 on the service PATH. It did not execute native plugin source or a product quality gate. No global pip or user-font installation was made. Existing Docker software/images were not uninstalled and are unnecessary for the new direct/native path.

The [upstream installation guide](https://diagrams.mingrammer.com/docs/getting-started/installation) explicitly supports running a Python diagram script after Graphviz installation. [Graphviz downloads](https://graphviz.org/download/) and the [Homebrew formula](https://formulae.brew.sh/formula/graphviz) describe the native engine. Font source/terms are in the package's [font inventory](../../../spikes/s04-local-plugin/assets/fonts/sources.json). Native graph rendering is independent of a cloud server.

## Review and host status

A separate GPT-6 Astra/High review of base afbaccad87019d35bff12d335ec534166752f0bf to HEAD 720831733bdb99061f62f7d509d95a65aa7f748b completed with one P2 finding. See [review evidence](S04-astra-review.md). The native implementation rejects that pre-existing output-root symlink and adds descriptor-anchored reads/writes. The review does not cover this new native diff; a fresh review remains required.

The [historical live chat](S04-work-host-check.md) proved alpha.1 tool calls and five artifact reads in Codex Desktop. Computer Use refused access to the ChatGPT app, so actual ChatGPT Work mode/UI preview/download was not established. A live call in the original parent chat still reported alpha.1 after alpha.2 installation: existing MCP processes can retain old code. Fresh native host discovery is recorded separately; neither it nor SDK tests substitute for the exact Work-mode acceptance.

## Remaining work and next prompts

RSS/disk watchdogs are sampled and can overshoot between checks. They are not kernel hard quotas or the old Docker CPU/PID/read-only-root controls. Full production NFR-009 acceptance, Windows/Linux setup, future macOS sandbox availability, detailed architectures, provider assets/rights, stable release install/upgrade/removal and two-machine acceptance remain open. S04/M0 is not closed and the M1 product gate has not started.

For the existing Astra review chat:

```text
Review the native alpha.2 change from 720831733bdb99061f62f7d509d95a65aa7f748b
to current HEAD on codex/s04-runtime-proof. Read S04-native-runtime.md and proof,
verify the output-root finding's fix and review native execution/resource/path
boundaries. Use Astra/High, read-only; record exact base/head and limitations.
```

For a fresh/reloaded local host chat:

```text
Use cloud-architecture-diagrams@mingrammer-local. Require get_runtime_info to
report 0.1.0-alpha.2, Darwin and native execution before rendering. Render three
English/Thai labels, inspect PNG and retrieve all five artifacts. Record the
actual host/mode. Do not equate Codex Desktop with unverified ChatGPT Work UI.
Do not rerun setup or alter runtime/config/source during this test.
```
