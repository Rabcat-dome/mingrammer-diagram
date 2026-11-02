# M7 Claude Code Plugin Preparation

Recorded: 2026-11-02 (Asia/Bangkok) | Base: `c5f74b4` | First tested code: `22fc85e` | Review fixes: `0220e94`, `87acce5` and `917f46f` | Branch: `codex/m7-claude-plugin` | Host: macOS ARM64, Claude Code 2.1.309.

**M7-01 and M7-02 are complete. M7-03 is verified on one Mac for local-path, GitHub and real-config installs and for updating an installed plugin; a second machine and interactive permission prompts remain. M7-04 has not started.** This is a preparation build under D-015. It authors and validates models; it cannot render diagrams, and it does not change the Work first-release target.

Actual CI and the GitHub and real-config installs below ran against commit `22fc85e`, before the review fixes. See [Same-session review](#same-session-review) and [Separate-session review](#separate-session-review) for what changed afterward and what has been rerun.

## Delivered

| Item | Result |
|---|---|
| [Plugin](../../../plugins/cloud-architecture-diagrams/README.md) | `cloud-architecture-diagrams`, versioned by Git commit, running core `0.2.0a4` |
| [Marketplace](../../../.claude-plugin/marketplace.json) | `mingrammer-local`, with a relative source. The Codex marketplace and S04 plugin are unchanged |
| Skill | `architecture-model`, with a model guide and the two valid core fixtures as examples |
| Command | `bin/cloud-diagrams` runs the core in a private hash-locked environment. It installs dependencies only, so no build backend runs and no install writes into the plugin |
| Gate | New `claude-plugin` and `package-contents` lanes |

The plugin links `pyproject.toml`, `uv.lock`, `src` and the examples back into the repository, so there is one copy of the core. Claude Code [dereferences symlinks that stay inside the marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#share-files-within-a-marketplace-with-symlinks) at install time. A test holds every path in the plugin to an allowlist, which keeps research records and uncleared assets out of the distribution. Files under `src` ship by design, so assets placed there rely on the M2 catalog-license lane.

There is no MCP server. A Claude Code session already has Bash and Read, so a second tool contract would add context cost without adding capability. Rendering can arrive as a CLI subcommand with M3.

## Verified

| Check | Result |
|---|---|
| Actual CI: [run 41440133540](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41440133540), job 125259629499 | Passed all 10 lanes on `macbook-pro-m2-max-mingrammer` from a clean checkout of `22fc85e`, with 82 core tests and 14 plugin tests and none skipped. Read from the run's report artifact |
| Low fixes in actual CI: [run 41453874994](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41453874994), job 125305537335 | Passed all 10 lanes at `917f46f`, with 90 core tests and 43 plugin tests, none skipped, and zero job annotations. Wheel SHA-256 `47232d0c03562539367e29eeb2f61ab89596f8bc661258db220f26f8a71affd7` matches the local build |
| Medium fixes in actual CI: [run 41449921613](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41449921613), job 125292308226 | Passed all 10 lanes at `87acce5`, with 87 core tests and 24 plugin tests, none skipped, and zero job annotations. Wheel SHA-256 `6a1ab1b3eca6c4ed6978d842a691d4985f63d569c8e6fc35c7b288784dbff036` matches the local build |
| Review fixes in actual CI: [run 41443551856](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41443551856), job 125271024270 | Passed all 10 lanes at `0220e94`, with 86 core tests and 17 plugin tests, none skipped, and zero job annotations. Wheel SHA-256 `da0bd7af66be5fbb910f8d5c1539a26378432c2d985e326fa764b963ba81b4e1` matches the local build |
| Node 24 action: [run 41441398887](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41441398887), job 125263877372 | Passed all 10 lanes at `359f1ea` with `actions/upload-artifact` v7.0.2 and zero job annotations, so the Node.js 20 warning is gone. The uploaded artifact downloaded and read back correctly |
| Wheel | At `22fc85e`, local and CI SHA-256 `fc138b2236a30100a01d1d6a381fd96b6eb70913d3ccbd6832c6d142b1560e8a`, byte-identical to the S05 CI wheel, so packaging left the core unchanged. Core `0.2.0a2` later changes the wheel on purpose, for the usage exit code |
| `claude plugin validate --strict` on marketplace and plugin | At `22fc85e`, passed. With the fixed version removed, non-strict validation passes and `--strict` fails only on the deliberate missing-version warning. The separate public-directory profile reports a missing license and icon; public submission is out of scope |
| Install from the private GitHub repository in a throwaway `CLAUDE_CONFIG_DIR` | `Rabcat-dome/mingrammer-diagram#codex/m7-claude-plugin` cloned over HTTPS with the machine's credentials. Cache has 0 symlinks and is 148 KB; valid and invalid paths behaved. Uninstall and marketplace removal then left no entries |
| Install from the local repository path and a fresh `git clone` in throwaway configs | Installed. Cache has 0 symlinks, and symlink and executable modes survive Git |
| Install into the owner's real config, as the owner requested | `settings.json` gained only `extraKnownMarketplaces` and `enabledPlugins`, with no existing value changed. First use created the private environment and validated a fixture |
| Update of the owner's install | `plugin marketplace update` and `plugin update` moved it from `0.2.0-alpha.1` to `0220e94300cb` with `settings.json` unchanged. On the updated copy, a `pydantic.py` in the working directory did not run, and exit codes 0, 2 and 64 behaved. A new headless session authored and validated a model with no permission denials. A running session keeps the old skill until restart, and the old cached version stays on disk under Claude Code's management |
| Second update of the owner's install | Moved it from `0220e94300cb` to `87acce5fee50` with `settings.json` unchanged. On that copy, `view_exclusions` covered every view, a planted `pydantic.py` did not run, and exit codes 2 and 64 behaved. A new headless session with two views validated a model with no permission denials and reported the exclusions |
| Third update of the owner's install | Moved it from `87acce5fee50` to `917f46f6b1b1` with `settings.json` unchanged. On that copy, exit codes 0, 2 and 64 behaved, a missing `HOME` exited 3 under `/bin/dash`, and planted project files with a relative `XDG_DATA_HOME` did not run. A new headless session validated a model with no permission denials |
| New headless session with no `--plugin-dir` | Loaded the installed plugin and listed its skill |
| Desktop Code tab | The skill appeared in the already running session after install. Invoking it resolved `${CLAUDE_PLUGIN_ROOT}` to the installed cache path, and `capabilities` ran from there. No model was authored in this check |
| Clean-copy tests in the gate | Run the command from a dereferenced copy outside the checkout and prove the copy's own core is the one executing |
| Exit codes | 0 valid, 2 invalid with JSON on stdout, 3 for a missing uv, a failed setup, an unusable `HOME` or an unexpected runtime failure with empty stdout, 64 for command misuse with empty stdout |

Model-authoring invocations used `claude -p --plugin-dir` with the owner's existing login, Sonnet 5.5 and no session persistence. Only Skill, Read, Write and Edit were pre-approved, so each Bash call depended on the skill's own `allowed-tools`.

| Prompt | Skill triggered | Outcome |
|---|---|---|
| English: model an AWS three-tier app | Yes | Model saved, `valid: true` with no permission denials. Stated core-only scope and no image. Added no unrequested security or connectivity |
| Thai: model a GKE cluster with Deployment, Service, Ingress and PVC | Yes | Model saved, `valid: true`. Reported in Thai with assumptions and the pending checks. One chained command was refused and retried, which led to the skill's instruction to run the command on its own |
| English: edit the saved model to add a WAF and an S3 read path | Yes | No existing ID removed; one resource and two relationships added; re-validated |
| Thai: draw a GKE architecture diagram | No | `diagram-design`, another installed plugin, handled it. This is acceptable while this plugin cannot render |
| English: mermaid flowchart of a purchase approval | No | Correct: not an infrastructure model |

## Findings

- **Empty wheel, now fixed and gated.** The `src` symlink made hatchling's once-per-directory walk enter the plugin first, which dropped the real `src` from the sdist. The wheel, built from that sdist, shipped no code while `package-build` still reported success. The sdist now skips the plugin directories. The `package-contents` lane compares the wheel with `src`; it failed on the empty wheel and passes after the fix.
- **`bin/` was not on the Bash path.** The [documented behavior](https://code.claude.com/docs/en/plugins/components.md#executables) did not appear on 2.1.309, either with `--plugin-dir` or for the installed plugin in a new headless session: the bare command was not found in any probe. The skill therefore uses `${CLAUDE_PLUGIN_ROOT}/bin/cloud-diagrams`, and that path was both substituted and pre-approved in `allowed-tools`.
- **Plugin data is unavailable to Bash.** `CLAUDE_PLUGIN_DATA` is not exported to Bash tool commands, so the environment lives under `~/.local/share` and uninstalling does not remove it. The plugin README documents the removal step.
- **The owner's install is pinned to this branch.** The default branch does not contain the plugin yet, so the marketplace was added with a branch ref. Remove and add it again after a merge.

## Same-session review

A high-effort review of `c5f74b4..64aec62` ran with the Claude Code review skill in the same session that wrote the code. It is not an independent review. It reported 10 findings, and all are fixed:

| Finding | Fix | Check |
|---|---|---|
| Files in the working directory could shadow modules and run through the pre-approved command | The wrapper runs Python with `-P`, later replaced by `-I` | Reproduced before the fix; new test passes |
| A saved gate report failed the docs check, because digests followed symlinks that `git show` returns as link text | Digests skip symlinks | A report from `64aec62` failed the docs check; new test compares digests with `git show` |
| Gate digests omitted the wrapper and `SKILL.md` | Digests cover every source file Git tracks or would add | New test |
| Exit 2 also meant command misuse | The core CLI exits 64 on usage errors, as core `0.2.0a2` | Reproduced before the fix; new tests in both lanes |
| Ignored files in `src`, such as `.DS_Store`, failed the wheel check | The check uses `files()` | New test, plus an empty-wheel negative |
| The package allowlist checked only top-level names | It now checks every path | A stray nested file failed the test |
| Content could change while the version stayed the same, leaving installed copies stale | The manifest omits `version`, so Claude Code uses the commit | A throwaway install reported the commit as its version |
| The model guide's example failed validation | The example declares its resource | New test validates every guide example |
| An unquoted command broke on a path with a space | The skill and its `allowed-tools` rule quote the path | A live run from a path with a space had no permission denials |
| A test requested an unused fixture | Removed | Lint and type checks |

After the fixes, the full gate passed locally and live English and Thai runs saved valid models with no permission denials. The Thai run loaded the plugin from a path containing a space.

## Separate-session review

A fresh Claude Code session reviewed `c5f74b4..a94b47a` read-only. Record it as a substitute review, not the Astra/High review the [model strategy](../model-strategy.md) names. It used the same model as the implementation, `claude-opus-5-5`, with session effort `xhigh`, and the implementing session wrote its brief, so its independence is limited. It found no Critical or High issues. It did not run the core tests or the full gate locally, relying on CI artifacts, and it had no `claude` CLI for installs, live runs or permission checks.

The owner asked for the three Medium findings to be fixed:

| Medium finding | Fix | Check |
|---|---|---|
| A result disclosed exclusions only for the first or selected view, so a complete first view hid a later partial view (FR-025) | Core `0.2.0a3` adds `view_exclusions` for every view and warns once per partial view. `selected_view` and `excluded_ids` keep their meaning | Reproduced before the fix; new test. A live run with a complete first view reported the second view's four excluded IDs from one validation |
| The guide called `taxonomy` a closed list and the `k8s.<kind>` rule firm, while the validator enforces neither | The guide and the skill's caveat now say so. Enforcement stays with M2 | Reproduced with `made.up`. A test fails when enforcement arrives, and another compares the guide's list with the requirements |
| No test protected the wrapper's setup flags | New tests cover a stale lock, an unchanged plugin tree, the exact installed package set and a fake uv that drains stdin | Removing each of `--locked`, `--no-dev`, `--no-install-project`, `</dev/null`, `>&2`, `-P` and `-B` now fails a test. The `-B` case needed `PYTHONDONTWRITEBYTECODE` removed from the test environment, because that variable masked it, including in CI |

The owner then asked for the six Low findings to be fixed too:

| Low finding | Fix | Check |
|---|---|---|
| The exit-code contract omitted exit 1 for a non-UTF-8 locale or a failed `exec`, and `/bin/dash` exited 2 when `HOME` and `XDG_DATA_HOME` were unset | Core `0.2.0a4` writes results as UTF-8. The wrapper maps any status other than 0, 2 and 64 to 3, and checks `HOME` explicitly | New tests under `/bin/sh` and `/bin/dash`, a missing core file and an ASCII output encoding |
| A relative `XDG_DATA_HOME`, or a colon in the plugin path, could run project files | Only absolute locations count, and Python runs with `-I` and an explicit import path | New tests with a planted `bin/python`, hostile Python variables and a path containing a space and a colon |
| The gate doc named a removed version check, and only `render_available` was pinned | The row is reworded, `commands` and `pending_checks` are pinned, and a test compares `pyproject.toml` with `__version__` | Tests |
| `package-contents` compared file names only | It compares a SHA-256 for each file | New test with the right name and different content |
| Gate digests omitted `pyproject.toml` | Digests include it and `uv.lock` | A test requires every plugin link target to be covered |
| Spaces, hostile variables and project files had no test, the guide test ran one way, and the guide omitted the `ownership` rule | New tests cover these, 13 guide lists must now match the contract exactly, and the guide states the rule and adds the Service type and port protocol values | Tests |

Removing or weakening any of 11 wrapper behaviors now fails a test: `--locked`, `--no-dev`, `--no-install-project`, `</dev/null`, `>&2`, `-I`, `-B`, the status mapping, the two absolute-path checks and the colon-safe import path. A relative `PATH` remains outside this protection, since control of the environment can already choose which programs run.

The review also noted two M1 items outside this range: `field` echoes rejected key names, and `ID_DUPLICATE` does not name the duplicate ID.

## S06 follow-up

S06 / M2 moved the core, and the checks built to catch that fired as intended. Five `claude-plugin` tests failed, and each was resolved by updating the skill, guide or expected contract, not by loosening a check. The caveat test now requires that `service_type` and `taxonomy` are rejected and no longer called unchecked. New tests cover catalog data in a clean copy, the Huawei warning, and the guide's type IDs and Kubernetes mappings. The plugin allowlist did not change, because catalogs and assets arrive through the `src` link, and the `catalog-license` lane covers them. The owner's installed plugin was not updated. See the [S06 evidence](S06-provider-catalogs.md).

## Not verified

- A second machine, any other operating system, and first-run setup with an empty uv cache.
- Interactive permission prompts, and how much `allowed-tools` admits at runtime, including whether a redirect such as `schema > file` prompts. Headless runs exercised `allowed-tools`, but the Code tab check ran under bypass permissions, so it did not.
- Authoring a model from the Code tab.
- The Astra/High review the model strategy names. Implementation and both reviews above used Claude Opus 5.5, and the Medium and Low fixes have not been reviewed by any pass.

Prompts were run once each, so trigger rates are observations rather than measurements. Provider semantics are unchanged from M1: a passing result does not establish that a service type exists or that a placement is legal.
