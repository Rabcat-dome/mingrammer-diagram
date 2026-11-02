# M7 Claude Code Plugin Preparation

Recorded: 2026-11-02 (Asia/Bangkok) | Base: `c5f74b4` | Branch: `codex/m7-claude-plugin` | Host: macOS ARM64, Claude Code 2.1.309.

**M7-01 and M7-02 are complete locally. M7-03 is partly verified. M7-04 has not started.** This is a preparation build under D-015. It authors and validates models; it cannot render diagrams, and it does not change the Work first-release target. Results below were taken from the working tree on the base commit, before it was committed, and no actual CI run exists for them yet.

## Delivered

| Item | Result |
|---|---|
| [Plugin](../../../plugins/cloud-architecture-diagrams/README.md) | `cloud-architecture-diagrams` version `0.2.0-alpha.1`, tracking core `0.2.0a1` |
| [Marketplace](../../../.claude-plugin/marketplace.json) | `mingrammer-local`, with a relative source. The Codex marketplace and S04 plugin are unchanged |
| Skill | `architecture-model`, with a model guide and the two valid core fixtures as examples |
| Command | `bin/cloud-diagrams` runs the core in a private hash-locked environment. It installs dependencies only, so no build backend runs and no install writes into the plugin |
| Gate | New `claude-plugin` and `package-contents` lanes |

The plugin links `pyproject.toml`, `uv.lock`, `src` and the examples back into the repository, so there is one copy of the core. Claude Code [dereferences symlinks that stay inside the marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#share-files-within-a-marketplace-with-symlinks) at install time. A test holds the package to an allowlisted tree, which keeps research records and uncleared assets out of the distribution.

There is no MCP server. A Claude Code session already has Bash and Read, so a second tool contract would add context cost without adding capability. Rendering can arrive as a CLI subcommand with M3.

## Verified

| Check | Result |
|---|---|
| `claude plugin validate --strict` on marketplace and plugin | Passed. The separate public-directory profile reports a missing license and icon; public submission is out of scope |
| Install from the local repository path in a throwaway `CLAUDE_CONFIG_DIR` | Installed. Cache has 0 symlinks and is 204 KB; the command ran from the cache. The real `~/.claude/plugins` was unchanged |
| Install from a fresh `git clone` checkout in a throwaway config | Symlink and executable modes survived Git; cache has 0 symlinks; valid and invalid paths behaved |
| Clean-copy tests in the gate | 14 tests passed. They run the command from a dereferenced copy outside the checkout and prove the copy's own core is the one executing |
| Exit codes | 0 valid, 2 invalid with JSON on stdout, 3 for a missing uv or a failed setup with empty stdout |
| Wheel | After the fix below, SHA-256 `fc138b2236a30100a01d1d6a381fd96b6eb70913d3ccbd6832c6d142b1560e8a` is byte-identical to the S05 CI wheel, so the core package is unchanged |

Actual Claude Code invocations used `claude -p --plugin-dir` with the owner's existing login, Sonnet 5.5 and no session persistence. Only Skill, Read, Write and Edit were pre-approved, so each Bash call depended on the skill's own `allowed-tools`.

| Prompt | Skill triggered | Outcome |
|---|---|---|
| English: model an AWS three-tier app | Yes | Model saved, `valid: true` with no permission denials. Stated core-only scope and no image. Added no unrequested security or connectivity |
| Thai: model a GKE cluster with Deployment, Service, Ingress and PVC | Yes | Model saved, `valid: true`. Reported in Thai with assumptions and the pending checks |
| English: edit the saved model to add a WAF and an S3 read path | Yes | No existing ID removed; one resource and two relationships added; re-validated |
| Thai: draw a GKE architecture diagram | No | `diagram-design`, another installed plugin, handled it. This is acceptable while this plugin cannot render |
| English: mermaid flowchart of a purchase approval | No | Correct: not an infrastructure model |

## Findings

- **Empty wheel, now fixed and gated.** The `src` symlink made hatchling's once-per-directory walk enter the plugin first, which dropped the real `src` from the sdist. The wheel, built from that sdist, shipped no code while `package-build` still reported success. The sdist now skips the plugin directories. The `package-contents` lane compares the wheel with `src`; it failed on the empty wheel and passes after the fix.
- **`bin/` was not on the Bash path.** The [documented behavior](https://code.claude.com/docs/en/plugins/components.md#executables) did not appear with `--plugin-dir` on 2.1.309: the bare command was not found in any of the probes. An installed plugin could not be probed, because a throwaway config has no login. The skill therefore uses `${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams`, and that path was both substituted and pre-approved in `allowed-tools`.
- **Plugin data is unavailable to Bash.** `CLAUDE_PLUGIN_DATA` is not exported to Bash tool commands, so the environment lives under `~/.local/share` and uninstalling does not remove it. The plugin README documents the removal step.

## Not verified

- Installing from GitHub. The branch is unpushed and the default branch does not contain the plugin. A local HTTP probe was blocked because the CLI's shallow clone needs a smart Git server.
- A second machine, any other operating system, and first-run setup with an empty uv cache.
- An interactive session, where a permission prompt and the skill's `allowed-tools` interact differently from headless mode.
- Actual CI for the two new lanes, which runs only after a push.
- Independent review. Implementation used Claude Opus 5.5; no separate review pass has been performed.

Prompts were run once each, so trigger rates are observations rather than measurements. Provider semantics are unchanged from M1: a passing result does not establish that a service type exists or that a placement is legal.
