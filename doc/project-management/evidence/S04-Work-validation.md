# S04 ChatGPT Work Acceptance Check

Updated: 2026-11-02 | Target: the separate ChatGPT Work page/mode, not Codex.

The owner explicitly confirmed this target and reported that **Cloud Architecture Diagrams (S04)** is visible/selectable under the local source in Work. The owner then ran the prompt in Work and reported alpha.3 / Darwin, a visible PNG and all five files. These are owner-reported Work results, distinct from automated SDK checks.

## Installed native candidate

- Plugin: `cloud-architecture-diagrams@mingrammer-local`.
- Candidate: `0.1.0-alpha.3`, native macOS Python/Graphviz. Docker and a central service are unnecessary.
- Source: **Cloud Architecture Local** (`mingrammer-local`), already registered on this Mac.
- Check actual runtime version/system before rendering: old chats may keep alpha.1 processes after disk updates.

The [official packaging guide](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list) describes local marketplace sources in Work and Codex. The [desktop-only guide](https://developers.openai.com/plugins/deploy/desktop-only) requires local execution for native helpers. [MCP host guidance](https://learn.chatgpt.com/docs/extend/mcp) does not promise local transports from a cloud-only chat. These documents support the test path; they are not evidence that this account's Work call passed.

## Work prompt

Use a Work task with access to this Mac and select the installed plugin. No cloud renderer, tunnel, public MCP connection or new account plugin is part of this check. Paste:

```text
Use Cloud Architecture Diagrams (S04) in this ChatGPT Work task.
First call the plugin's runtime-info tool and require version 0.1.0-alpha.3,
system Darwin and native execution. If an older/container runtime appears,
stop and report it; do not count that as a native test.
Render exactly these three labels, interpreting JSON Unicode escapes normally:
{"request":{"labels":["Client","Application \u0e23\u0e30\u0e1a\u0e1a","Database \u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25"]}}
Retrieve SVG, PNG, source JSON, DOT and manifest through the plugin. Verify the
bundle/file checksums, show the PNG inline and provide actual downloadable
outputs. If this Work host does not expose the MCP tools but can execute local
files, use the plugin's fixed scripts/render.py with the same labels on stdin;
record that direct-script route and the returned native version/system instead.
Do not generate architecture Python, rerun setup, change configuration, use
Docker, or invent download links. Report any missing local execution, tool,
preview or export capability exactly.
```

The direct-script fallback is an existing packaged capability, not permission to run arbitrary supplied code. On this Mac its installed path is `/Users/visarut.pha/.codex/plugins/cache/mingrammer-local/cloud-architecture-diagrams/0.1.0-alpha.3/scripts/render.py`. The script's input is `{"labels":[...]}`; the MCP tool's input has the outer `request` object.

## Record actual result

| Check | Status |
|---|---|
| Separate Work page/mode is the intended target | Owner confirmed |
| Plugin visible and selectable in Work | Owner confirmed |
| Actual Work invocation uses alpha.3 / Darwin | Passed, owner report |
| PNG visible in Work | Passed, owner report; the supplied prompt used English labels |
| SVG/PNG/JSON/DOT/manifest retrieved from Work | Passed, owner report |
| Method and runtime identity | Owner used the supplied plugin-tool prompt in the separate Work page; alpha.3 / Darwin |

Owner response on 2026-11-02: `plugin_version: 0.1.0-alpha.3 and system: Darwin`; PNG visible; all five files available. No Work bundle ID, file hashes or tool transcript was supplied. Work UI/download is established by this owner report, while byte/hash checks and English/Thai rendering are established separately by local SDK/CLI evidence. This is S04 feasibility, not full product or two-machine release acceptance.

Do not relabel Codex or SDK evidence as this Work result. Computer Use refuses direct control of the ChatGPT app; no bypass or app restart is performed automatically. If the local source/version needs an app reload, the owner should choose a safe time after active tasks and saved changes are accounted for. A stale connection or inaccessible output is a failed/pending check, not acceptance.
