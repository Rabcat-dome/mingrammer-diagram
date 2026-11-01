# S04 ChatGPT Work Acceptance Check

Updated: 2026-11-02 | Target: the separate ChatGPT Work page/mode, not Codex.

The owner explicitly confirmed this target and reported that **Cloud Architecture Diagrams (S04)** is visible/selectable under the local source in Work. The owner then ran the prompt in Work and reported alpha.3 / Darwin, a visible PNG and all five files. These are owner-reported Work results, distinct from automated SDK checks.

## Installed native candidate

- Plugin: `cloud-architecture-diagrams@mingrammer-local`.
- Candidate: `0.1.0-alpha.3`, native macOS Python/Graphviz. Docker and a central service are unnecessary.
- Source: **Cloud Architecture Local** (`mingrammer-local`), already registered on this Mac.
- Check actual runtime version/system before rendering: old chats may keep alpha.1 processes after disk updates.

The [official packaging guide](https://developers.openai.com/plugins/build/plugins#build-your-own-curated-plugin-list) describes local marketplace sources in Work and Codex. The [desktop-only guide](https://developers.openai.com/plugins/deploy/desktop-only) requires local execution for native helpers. [MCP host guidance](https://learn.chatgpt.com/docs/extend/mcp) does not promise local transports from a cloud-only chat. These documents support the test path; they are not evidence that this account's Work call passed.

## Prompt supplied for the reported Work test

The coordinating chat supplied this English-label prompt, and the owner replied to that test question:

```text
Use Cloud Architecture Diagrams (S04). First call get_runtime_info and report
plugin_version and system. Continue only if version is 0.1.0-alpha.3 and system
is Darwin. Render the three-node fixture with labels Client, Application,
Database. Show the PNG preview and provide all five artifacts: PNG, SVG, source
JSON, DOT and manifest. Report any error.
```

This prompt requested plugin tool calls, but the owner supplied no tool transcript; the actual MCP versus direct-script route is not independently confirmed. Thai labels and Work-side hashes were not part of this reported result. Local English/Thai render and byte/hash checks remain separate evidence.

The package also supports a direct-script fallback when local file execution is available. On this Mac its installed path is `/Users/visarut.pha/.codex/plugins/cache/mingrammer-local/cloud-architecture-diagrams/0.1.0-alpha.3/scripts/render.py`. Input is `{"labels":[...]}` on stdin; the MCP tool uses an outer `request` object. This documents an existing capability, not an observed route in the owner's Work test.

## Record actual result

| Check | Status |
|---|---|
| Separate Work page/mode is the intended target | Owner confirmed |
| Plugin visible and selectable in Work | Owner confirmed |
| Actual Work invocation uses alpha.3 / Darwin | Passed, owner report |
| PNG visible in Work | Passed, owner report; the supplied prompt used English labels |
| SVG/PNG/JSON/DOT/manifest retrieved from Work | Passed, owner report |
| Runtime identity / method | Owner reports alpha.3 / Darwin after the supplied prompt; underlying MCP/direct-script route not independently confirmed |

Owner response on 2026-11-02: `plugin_version: 0.1.0-alpha.3 and system: Darwin`; PNG visible; all five files available. No Work bundle ID, file hashes or tool transcript was supplied. Work UI/download is established by this owner report, while byte/hash checks and English/Thai rendering are established separately by local SDK/CLI evidence. This is S04 feasibility, not full product or two-machine release acceptance.

Do not relabel Codex or SDK evidence as this Work result. Computer Use refuses direct control of the ChatGPT app; no bypass or app restart is performed automatically. If the local source/version needs an app reload, the owner should choose a safe time after active tasks and saved changes are accounted for. A stale connection or inaccessible output is a failed/pending check, not acceptance.
