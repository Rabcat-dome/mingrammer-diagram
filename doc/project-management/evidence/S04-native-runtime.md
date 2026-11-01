# S04 Native Runtime Follow-up

Dates: 2026-11-01 to 2026-11-02 (Asia/Bangkok) | Scope: M0-02/M0-05, fixed three-node prototype | Version: 0.1.0-alpha.3.

The owner questioned why Docker was needed and pointed out direct script execution. Docker was an implementation choice, not a user requirement. The native default now executes controlled Python scripts with system Graphviz. The plugin remains versioned/installable, with its workflow skill and optional local stdio MCP interface. No central service or listening HTTP port is required. This implements D-013 with less installation overhead; it does not add cloud-only support.

## Verified native behavior

[Proof JSON](S04-native-runtime-proof.json) contains source/archive hashes, installed dependency inventory, executable/font provenance and actual checks. [Setup/direct-command instructions](../../../spikes/s04-local-plugin/README.md) reproduce the pilot.

- Direct script rendering passed with a Docker executable shim that fails if invoked and a remote DOCKER_HOST value. The shim was not invoked; Docker is not on the renderer's controlled PATH.
- Installed alpha.3 MCP and a ZIP relocated to a path containing spaces passed discovery, preflight, three literal English/Thai labels, five artifact reads, matching byte/hash checks, inline PNG equality and invalid-input checks.
- Seven filesystem regressions passed: root symlink, ancestor symlink, artifact symlink, non-regular artifact, oversize artifact, root replacement and atomic cleanup after integrity failure. This addresses the confirmed alpha.1 output-root finding.
- Actual subprocess tests triggered and terminated on wall timeout, sampled group RSS and sampled scratch-space limits, including a parent that exited while its descendant held the pipes open. The setup's macOS network-denial probe returned EPERM. Native renderer children use that same sandbox-exec policy.
- Six isolated shutdown checks passed: main-thread SIGTERM, worker-thread SIGTERM/SIGINT, SIGTERM during spawn, actual MCP stdio SIGTERM with stdin still open, and stdin EOF during an outstanding tool. Each verified the helper status, renderer termination and request-directory removal. The deleted-intermediate regression passed; directory snapshots use a single lstat and skip vanished files.
- Direct JSON and MCP newline frames are bounded at 1 MiB. The MCP 2.3 adapter uses cancelable nonblocking POSIX pipes; a small private SDK dispatch bridge must be revalidated when upgrading the pinned SDK.
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

Astra/High's alpha.1 review found one P2 output-root symlink issue, fixed in alpha.2. The [alpha.2 native review](S04-native-alpha2-review.md), base 7208317 to head 1fd2d72, confirmed that fix and found two P2 issues: helper signal shutdown could leave an unsupervised renderer, and deleted DOT intermediates could abort directory sampling. Alpha.3 addresses both; its targeted tests and full native integration checks pass. The [final alpha.3 Astra/High review](S04-native-alpha3-review.md) at 2fc8047 confirmed both fixes with no new confirmed actionable runtime finding.

The [historical live chat](S04-work-host-check.md) proved alpha.1 calls/artifacts in Codex Desktop. The later [native host check](S04-native-live-host-check.md) correctly stopped because that connection still reported alpha.1 despite alpha.2 files on disk. Existing chats can retain an old process; SDK/install success does not establish a refreshed host connection.

The owner explicitly identified the separate ChatGPT Work page as the target, confirmed plugin visibility/selectability and then ran the supplied check there. On 2026-11-02 the owner reported **alpha.3 / Darwin, a visible PNG and all five files**. See [Work result and limitations](S04-Work-validation.md) and [owner proof](S04-Work-owner-proof.json). This establishes the S04 Work feasibility result by owner report; local SDK checks establish separate byte/hash evidence. Direct UI control was refused by Computer Use and was not bypassed. No automatic app restart was performed.

## Remaining work

RSS/disk watchdogs are sampled and can overshoot; they are not kernel hard quotas or Docker CPU/PID/read-only-root controls. Production NFR-009 acceptance, Windows/Linux setup, future macOS sandbox availability, provider/detailed-Kubernetes semantics, asset rights, polished install/upgrade/removal and two-machine acceptance remain later milestone work. The M1 product gate has not started. S04/M0 feasibility is closed in the [closeout](S04-closeout.md); continue S05/M1 without reopening cloud-hosting questions.
