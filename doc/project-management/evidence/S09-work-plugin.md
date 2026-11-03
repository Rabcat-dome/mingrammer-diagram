# S09 — ChatGPT Work Plugin

Dates: 2026-11-03 to 2026-11-04 (Asia/Bangkok) | Tasks: M5-01..04 | Branch: `codex/s09-work-plugin`, from `main` at `43b444d` | Plugin: `cloud-architecture-work` `0.1.0-alpha.1` plus a content digest | Core: `0.5.0a1`, unchanged

**Result: M5 stays open. The plugin is built and passes everything that can run without the owner, including the host's own engine. Nothing here is a Work result: M5-04 needs the owner's run in actual Work, recorded in the [Work check](S09-Work-validation.md).**

## Task status

| Task | Status | Evidence |
|---|---|---|
| M5-01 Adapter and capability discovery | Built | [The adapter](#what-was-built). Eight tools with one result envelope, covering FR-055, FR-063 and FR-064 |
| M5-02 Runtime setup, preflight, upgrade, removal, artifact retrieval, isolation, retention | Built, and run through the host's engine | [Through the real host](#through-the-real-host). Local mode needs no authentication, and P-034 records retention |
| M5-03 Versioned plugin with bundled skill and references | Built | `scripts/build_work_plugin.py`, with a deterministic ZIP. The host installs it byte for byte |
| M5-04 Actual Work installation, discovery, rendering, invalid input and edit | **Waiting for the owner** | The [Work check](S09-Work-validation.md) holds the exact steps and an empty result table |

## Exit criteria

| Criterion | Status |
|---|---|
| Installed plugin works in the selected Work mode | Not yet known. The host's engine runs it, and only the owner can run the Work page |
| Artifacts are retrievable | Through the host's engine, all six files read back and match their checksums. In the Work user interface: not yet known |
| Supported host modes are stated accurately | Done in the [plugin README](../../../plugins/cloud-architecture-work/README.md#where-it-runs) and in `get_capabilities`. Work is named as selected, and the README sends the reader here for what has been checked |
| Local CLI or protocol tests alone do not satisfy M5-04 | Respected: nothing here claims M5-04 |

## What was built

| Item | Result |
|---|---|
| [Plugin source](../../../plugins/cloud-architecture-work/README.md) | Portable `plugin.json` and `mcp.json`, the skill, the server and a runtime script. `src`, `uv.lock`, the model guide and the examples are links into the repository, so there is one copy of each |
| `server/work_adapter` | A stdio MCP server using only the Python standard library, and it parses on Python 3.9. Each tool runs one core subcommand in a new process. The core is unchanged and does not know about it |
| `scripts/runtime.py` | `preflight`, `setup`, `list`, `prune` and `remove`, for use from a terminal |
| `scripts/build_work_plugin.py` | Writes a local marketplace of real files, a deterministic ZIP and its SHA-256. The version gets a digest of the content |
| `scripts/work_host_check.py` | Installs the build into a throwaway host profile and runs it through the host's engine, with no account and no model |
| `tests/test_work_plugin.py` | The `package-contract` lane, the 16th |
| Skill | `architecture-model`, written for tool calls, with the model guide and the two core examples as progressive references |

The [core contract](../../design/core-contract.md#work-adapter) states the tool contract, result statuses and limits. P-032, P-033 and P-034 in the [decisions](../decisions.md#recommendations-and-disposition) record the choices and their reasons.

## What the host really does

These come from `codex-cli 0.166.0-alpha.5.1`, the engine inside the ChatGPT app on this Mac, which also runs as the app's own `app-server` process. They were measured with a throwaway `CODEX_HOME`. Work mode may add more on top of this engine, and only the owner's run can show that.

| Question | Measured | Effect on the design |
|---|---|---|
| Symbolic links in a plugin | `plugin add` leaves all of them out of its cache and says nothing | The package is built from real files, and a test fails on any link |
| Root `plugin.json` and `mcp.json` alone | Recognized, with no `.codex-plugin` manifest | Portable manifests only |
| Version with build metadata, such as `0.1.2+abc123` | Accepted, and used as the cache folder's name | The content digest goes there |
| Re-adding an unchanged version with changed files | Refreshes the cache | Not relied on, since the digest changes the version anyway |
| A new version | Replaces the old cache folder, so an open chat's process loses its files | `PLUGIN_UPDATED` says so instead of crashing |
| `plugin remove` | Removes the cache and config entry, and keeps `PLUGIN_DATA` | The runtime has its own `remove` command |
| What a server's environment holds | `HOME`, `LOGNAME`, `PATH`, `SHELL`, `TMPDIR`, `USER`, `LC_CTYPE`, `PLUGIN_ROOT`, `PLUGIN_DATA` | Nothing depends on a variable set only in a shell |
| Protocol | The client asks for `2025-06-18` and sends `notifications/cancelled` when it gives up | Negotiation and cancel are implemented |
| Result size | 8 MiB of binary content returned intact. A 16 MiB file left the call hanging with no error until the client gave up | `read_artifact` refuses over 8 MiB, and the file stays reachable by path. Real PNGs were at most 384 KB in the reference set |
| Argument size | A 3 MiB argument arrived intact | The frame limit is 4 MiB, above the core's 1 MiB |
| Tool time limit | A call ran for 130 seconds directly and 70 seconds from the agent with no cut, although OpenAI's documentation gives 60 seconds as a default | The adapter stops itself at 58 seconds anyway |
| How the agent reaches a tool, on `gpt-6.1-sol` | Through JavaScript in a tool named `exec`: `tools.mcp__cloud_architecture__render_model(...)`. Tools can be left out of `exec`'s description and listed only in `ALL_TOOLS`. An image reaches the model only through `image(result.content[1])`, as an `input_image` | The skill says all of this, because no model could guess it |
| Which tools ask first | Under approval policy `never`, `setup_runtime`, which is marked as reaching the network, was refused with "requires approval". `render_model`, marked as writing only locally, ran | `get_capabilities` gives the terminal command as a fallback. What the prompt looks like in Work is an open question for the owner |
| Server `instructions` | Appended to every tool's description | Kept to one sentence |
| Where the host keeps tool calls | `sessions/.../rollout-*.jsonl` in its home folder holds the arguments, including model text | The README says so, because the plugin cannot prevent it |

OpenAI's pages describe local stdio plugins for the desktop app, Work mode included, and imply that web and cloud threads cannot use them. Several things above are not on any page we read, so they can change with the app. `scripts/work_host_check.py` fails if they do.

## Through the real host

`scripts/work_host_check.py` drives the host's own client over its `app-server` protocol, and then its own agent against a local stand-in for the model API that plays a fixed script. It uses a throwaway profile and a throwaway `HOME`, with no account and no model. It covers:

- **Install:** every built file arrives byte for byte, with no links. The version matches, the marketplace lists it as installed and enabled, and the skill is in the prompt a model would receive.
- **Discovery:** exactly the eight tools.
- **Setup:** a fresh machine reports `not_installed`, and a call before setup gets `RUNTIME_NOT_READY`. Setup then finished in 4.4 seconds with an empty uv cache, and can render. This Mac already had Python 3.13.7, so uv did not download Python.
- **Tools:** catalog, schema, invalid input with its code, a render with an inline PNG, all six files back through the host matching their checksums, another view from an earlier bundle, an edit that keeps every ID and leaves the old bundle unchanged, every Kubernetes view, and Thai text.
- **Scope:** traversal, a missing bundle and an unlisted file are refused, and the root and bundles are private to the user.
- **Upgrade:** the old process reports `PLUGIN_UPDATED`, and a new session runs the new version on the same runtime with no second setup.
- **The agent's path:** tool names, the approval refusal, image forwarding, a failed call, and a model kept between `exec` calls with `store`.
- **Removal:** the runtime goes, bundles stay, and no install or config entry remains.

The [proof](S09-host-check-proof.json) records each check. It passes 35 of 35. This is the host's engine and not the Work user interface: it says nothing about what the Work page shows, whether its approval prompt appears, or what a real model does with the skill.

## Rehearsal with a live model

A skill sentence no unit test had read once broke a live session of the Claude plugin, so this skill went through live sessions before the owner's time. This ran on Claude Code 2.1.309 with Sonnet 5.5 and the owner's existing login, over the built package's MCP server. **It is not the Work host and not the model Work would use.** It reaches tools directly instead of through `exec`, so it tests the skill's instructions and the tool contract, not the host. Only the MCP tools and Read were allowed, and each prompt ran once, so these are observations rather than rates.

| Prompt | Turns | Denials | Outcome |
|---|---|---|---|
| English: an AWS three-tier application | 17 | 0 | Rendered. Reported assumptions, what validation does not prove and a layout flaw it saw in the PNG. It added no unrequested security or connectivity |
| Thai: GKE with Deployment, Service, Ingress and PVC, overview and detail, Thai labels | 11 | 0 | Both views rendered, with readable Thai. All six files linked for each. Replied in Thai |
| English: add a WAF to the latest diagram | 14 | 0 | Stopped without changing anything, because the catalog has no AWS WAF, and offered a lenient draft |
| English: add an S3 bucket both app servers read | 8 | 0 | Found the source through `list_bundles`. All 4 resources and 4 relationships unchanged, one resource and two relationships added, and a new bundle |
| English: validate a model with a dangling reference | 5 | 0 | `REFERENCE_MISSING`, named the fix options, drew nothing, and said the later layers had not run |

The WAF result changed the plan. The earlier M7 check used a WAF, and the owner's Work check would have hit the same gap, so it uses S3 instead, and the skill now names this case. WAF is outside the requirement baseline, so this is a coverage limit and not a defect. See [what this does not establish](#limits-and-what-this-does-not-establish).

## Sabotage

The `package-contract` lane has to fail when the source breaks, so 27 changes were made to the source, one at a time, at `5ac927d`, with the lane's own command run after each. Each was then reverted, and the tree was checked clean. The [proof](S09-sabotage-proof.json) records them.

**26 of the 27 failed the lane. Removing `--locked` from setup did not.** The old stale-lock test used a lock so broken that uv failed either way. The test now uses a lock that no longer matches the project, requires it not to be rewritten, and fails without the flag. This was rerun; see the proof for the commit and result.

## Findings from building it

- **The lint lane skipped the adapter while passing.** A link named `pyproject.toml` in the plugin folder made Ruff treat that folder as its own project, so `lint` and `format` passed without reading `server/`. It showed only because one command printed "no Python files". The link is gone, the build adds that file, the adapter is held to Python 3.9 by Ruff, and tests fail if the lanes stop seeing it.
- **Host installs drop links silently.** The Claude plugin's approach of linking into the core does not survive this host, so a marketplace pointed at the source folder would install a broken plugin with no error. The README says to install only the build.
- **A plan based on a documentation summary would have been wrong twice.** The 60-second default did not apply on the measured paths, and the model does not call tools directly on this host.
- **A tool result can hang the host.** A 16 MiB result produced no error at all, only a call that never returned, so the limit has to be enforced before sending.
- **Preflight ran what `PATH` chose.** An early version ran `dot -V` unsandboxed inside a tool marked read-only, while the core takes care to run that query sandboxed. Preflight now only locates the binaries.

## Requirement coverage

| ID | Status |
|---|---|
| FR-055 | Discovery through `get_capabilities`, `get_schema` and bounded `search_catalog`, tested through real pipes and the host's engine |
| FR-060 | Pending: needs the owner's run in Work |
| FR-061 | The skill guides lookup, assumptions, validation, rendering and ID-preserving edits. Rehearsed on one other model, and pending in Work |
| FR-063 | Eight statuses with stable codes, and each core outcome has a test, including crashes and partial bundles |
| FR-064 | Setup, preflight and removal, with a real render as the setup probe. Prerequisites and supported modes are documented. Macs other than this one are M6 |
| FR-065 | The core has no change for this adapter, and a test fails if it imports one |
| FR-066 | The versioned plugin and its route exist for one machine. Two machines are M6 |
| NFR-013 | Local mode: per-request directories in the core, a private root, and fixed names with no links at retrieval. P-034 records retention |
| T-011, T-013, T-017 | Automated parts pass through the host's engine. Work results are pending |
| T-014, privacy part | Tested: no model content in the adapter's log or runtime files, and rejected values are not echoed. The adapter has no network code, and the core's sandbox denies the renderer network access. Remote artifact isolation and expiry do not apply to local mode. The host's own session record does hold the model, and the README says so |
| T-009 | Traversal, symbolic links, a special file, an oversize frame, a repeated key and hostile environment variables, through the tool surface |

## Limits and what this does not establish

- **Nothing has run in the Work page.** Its user interface, approval prompts, image display and file opening are all unknown until the owner reports them. S04 alpha.3 gives feasibility on the same Mac, and it was a different plugin.
- **No real model has used this skill on the Work host.** GPT models reach tools through `exec`, and only a scripted stand-in has done that here. The Claude rehearsal reaches tools directly.
- One Mac only: macOS 27 on Apple silicon, with Python 3.13.7 already present. Another Mac, a Python download and the system's Documents permission prompt are M6.
- Host behavior is measured on one version and can change with an app update.
- The `Documents` folder syncs if the owner has turned that on. That is stated, not prevented.
- A file over 8 MiB is reachable only by its path. None of the reference views comes close.
- The catalog holds the required minimum, so a common service such as AWS WAF is refused in strict mode. Widening it is later work outside the baseline.
- Huawei rights stay uncleared. D-018 and O-002 apply to this package as to every other, and the README, manifest and results all say so. The ZIP must not be uploaded to an account, shared in a workspace or published.

## Model and review

Claude Opus 5.5 (`claude-opus-5-5`) did the implementation, tests and records, in a session started from the owner's main session. The project policy names Sol for M5, so this is a recorded substitution, and no model setting changed. Sonnet 5.5 ran the live rehearsal only.

Review under D-021 is pending, and will be recorded in `S09-fable-review.md`. Claude Fable 5.1 and Claude Opus 5.5 share a vendor, so that review reduces some shared assumptions and does not remove them.

## Next steps

1. Fresh Fable/High review of this branch, then fix its P0-P2 findings.
2. The owner installs the reviewed build and runs the [Work check](S09-Work-validation.md).
3. M5 closes only on that report.
