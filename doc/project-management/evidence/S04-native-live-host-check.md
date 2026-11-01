# S04 Native Live Host Check

Recorded: 2026-11-02T00:32:39.901822+07:00 | Frozen HEAD: 1fd2d72a22183b65d76ea0bea255702a769ae62f

**Result: stale live alpha.1 connection; native live test not run.**

The installed alpha.2 files and native state are present on disk, but this desktop chat's actual plugin connection still reports alpha.1/Linux/container execution. It fails the required native identity gate. No native render, artifact reads, invalid-input test, preview or export was attempted. No SDK/CLI fallback was substituted.

The owner's first-release target is the OTHER ChatGPT Work mode/page, explicitly distinct from Codex in this app. Even a future native Codex pass is runtime evidence only.

## Checkout and established host

- Existing checkout: /Users/visarut.pha/Documents/source/easybuy/mingrammer-diagram, branch codex/s04-runtime-proof.
- Observed and expected HEAD: 1fd2d72a22183b65d76ea0bea255702a769ae62f. Initial working tree was clean; every tracked file matched frozen HEAD before evidence creation.
- Read first: HANDOFF.md and S04-native-runtime.md. Applied installed alpha.2 runtime skill.
- Executor: local Codex Desktop, from CODEX_INTERNAL_ORIGINATOR_OVERRIDE=Codex Desktop and local process ancestry.
- Host: macOS 27.0.1 ARM64. App /Applications/ChatGPT.app, display name ChatGPT, bundle ID com.openai.codex, version 26.1027.30824 build 22943.
- Bundled CLI: codex-cli 0.166.0-alpha.5.1. Local ancestry leads to codex PID 31288 and app PID 31190.
- App name/local execution do not establish the target Work UI mode.
- No host UI inspection was retried; no self-app prohibition was bypassed or whole-app restart attempted.

## Actual tools and response

Discovered actual registry names associated with Cloud Architecture Diagrams (S04):

- mcp__architecture_runtime__get_runtime_info
- mcp__architecture_runtime__render_fixture
- mcp__architecture_runtime__read_fixture_artifact

Only mcp__architecture_runtime__get_runtime_info with an empty argument object was called. It returned isError=false, with no protocol error. The failure was runtime identity:

| Identity | Required | Actual live response |
|---|---|---|
| Version | 0.1.0-alpha.2 | 0.1.0-alpha.1 |
| System | Darwin | Linux |
| Execution | Native Python; no Docker | local stdio; network-none container |
| Python | Native candidate 3.13.7 | 3.13.13 |
| Graphviz | Native candidate 16.1.0 | 12.2.1 |
| Architecture | Native host ARM64 | Container aarch64 |

The response also reports diagrams 0.25.1, Python graphviz 0.20.3, MCP 2.3.0, UID 501, container cgroups and /usr/share/fonts/noto/ fonts. Its full targeted response is in [proof JSON](S04-native-live-host-proof.json). No live image ID was returned or freshly inspected.

## Disk-installed native identity

Read-only filesystem checks found:

- Installed root: /Users/visarut.pha/.codex/plugins/cache/mingrammer-local/cloud-architecture-diagrams/0.1.0-alpha.2; manifest version 0.1.0-alpha.2, local executor required.
- Stdio launcher: python3 -B followed by the installed scripts/launch.py.
- Native state: /Users/visarut.pha/.local/share/cloud-architecture-diagrams/0.1.0-alpha.2.json.
- State SHA-256: ed808c24b6ee3f911235b6dc97c2931f62640a93a230e71ada8947bd2fb3a1ab.
- State kind/version: native / 0.1.0-alpha.2.
- Source fingerprint: 74ed856c6ad3abb63d3e06571a2e8181599ffe7efdce8f23e7440698c14a2b77.
- Private Python: /Users/visarut.pha/.local/share/cloud-architecture-diagrams/runtime/0.1.0-alpha.2/venv/bin/python; no execution performed.
- Recorded Graphviz: dot - graphviz version 16.1.0 (20260904.0139).
- Read-only dot, fc-match and sandbox-exec hashes matched the state. Full cache hashes are in proof JSON.

These observations establish the disk installation, not the connected runtime. The native design has no container image; this live connection still reports the historical container.

## Refresh investigation, read only

OpenAI Docs was used to check supported options:

- [Official MCP documentation](https://learn.chatgpt.com/docs/extend/mcp) describes desktop MCP settings, a Restart action, and /mcp for connection visibility. The plugin-managed entry and action behavior were not observed in this installed app.
- [Official App Server documentation](https://learn.chatgpt.com/docs/app-server) lists config/mcpServer/reload to reload configuration and queue refresh for loaded threads. No matching exposed tool was found; no RPC transport was opened or mutation sent. It could affect other loaded threads.
- Installed CLI mcp --help and plugin --help exposed management commands but no reload/reconnect subcommand. Only help/version commands were run through the CLI.

No connection refresh, app restart, new chat, configuration edit, setup or cache change was performed. The follow-up authorized inspection of refresh mechanisms read-only.

## Conditional fixture and delivery

Planned request, with Thai label literals escaped as required in this English Markdown:

    {"request": {"labels": ["Client", "Application \u0e41\u0e2d\u0e1b\u0e1e\u0e25\u0e34\u0e40\u0e04\u0e0a\u0e31\u0e19", "Database \u0e10\u0e32\u0e19\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25"]}}

The failed identity gate prevented render_fixture and five read_fixture_artifact calls. No native bundle, file hashes, PNG/SVG copies, visual inspection, inline image or export links were created in this follow-up. Invalid-input testing was not run against the stale connection. Historical alpha.1 artifacts were not reused as native evidence.

## Exact Work-only proof still required

1. Confirm the OTHER ChatGPT Work page/mode visibly, including selected local execution/host mode and app version.
2. Select the same local-marketplace plugin there. Invoke actual tools there and require get_runtime_info to return alpha.2, Darwin and native Python execution.
3. Render the three literal labels, safely reject invalid input, read all five artifacts through those Work tool calls, and verify returned bytes/checksums against that run's exports.
4. Observe readable English/Thai PNG preview within that Work UI and successful retrieval/download of PNG, SVG, JSON, DOT and manifest.
5. Record owner-observed/UI evidence and the corresponding bundle paths/hashes without credentials. Codex, SDK and direct-script evidence do not satisfy this acceptance.

No Work action was performed here. After an owner-managed supported refresh/fresh or reloaded local session, the native preflight must pass before dependent runtime tests. Work target acceptance remains separate. S04/M0 is not closed.

## Scope and errors

Only this report and its proof JSON were authored. Tracked source, historical alpha.1 evidence, runtime, setup and plugin cache were left unchanged. No branches/worktrees, commits, pushes, deployments, account uploads or messages to other chats.

One evidence-write orchestration cell initially failed to parse with JavaScript SyntaxError: Unexpected token '{'. It executed no tool or write; the corrected writer produced these reports. The plugin itself returned no protocol error.

Final read-back validation: frozen HEAD/branch, all 65 tracked files, historical evidence, native runtime state and installed cache hashes matched; the English Markdown is ASCII with Unicode-escaped test labels. Only the two new evidence reports were authored.
