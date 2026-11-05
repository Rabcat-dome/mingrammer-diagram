# M7 Claude Code Plugin Preparation

Recorded: 2026-11-02 (Asia/Bangkok) | Base: `c5f74b4` | First tested code: `22fc85e` | Review fixes: `0220e94`, `87acce5` and `917f46f` | Branch: `codex/m7-claude-plugin` | Host: macOS ARM64, Claude Code 2.1.309.

**M7-01 and M7-02 are complete, and M7-04 brought catalog discovery and rendering to the plugin. M7-03 is verified on one Mac, most recently on [a copy installed at `ea6c802`](#the-acceptance-copy), with [what a real session asks for](#what-a-real-session-asks-for). Nobody has seen a permission dialog drawn, and D-035 accepts one Mac in place of two. **M7 closed on the owner's word under D-039.** This is a preparation build under D-015. It authors and validates models, and since S07 it also renders them. It does not change the Work first-release target.

Actual CI and the GitHub and real-config installs below ran against commit `22fc85e`, before the review fixes. See [Same-session review](#same-session-review) and [Separate-session review](#separate-session-review) for what changed afterward and what has been rerun.

## Delivered

| Item | Result |
|---|---|
| [Plugin](../../../plugins/cloud-architecture-diagrams/README.md) | `cloud-architecture-diagrams`, versioned by Git commit, running core `0.5.0a1` at `97b0841` |
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
| Move of the owner's install to `main` | On 2026-11-03, `plugin marketplace remove`, `marketplace add` and `plugin install` moved it from `917f46f6b1b1` to `3d235fad83b0`. `settings.json` lost only the branch ref, apart from one key's position. On that copy, run from a folder outside the repository, the cache has 0 symlinks, `capabilities` reports `0.3.0a1` and `core_catalog_provider`, catalog search finds self-managed nodes, the AWS fixture exits 0, and the N1 model exits 2 with `AWS_EKS_NODE_GROUP_NETWORK_MISMATCH` in both modes. A new headless session on Haiku 5.5 lists the skill |
| New headless session with no `--plugin-dir` | Loaded the installed plugin and listed its skill |
| Choosing what a view selects | A live session on the installed `43b444d` rendered, with region and zone as loose boxes, because the skill did not say what each `grouping` can draw. The model guide now does, and it is tested against the mapper. Six new headless sessions on Sonnet 5.5 through `--plugin-dir` then rendered with no loose region or zone box: AWS and Azure twice, plus GKE and on-premises. The first three also showed sessions trying to write the model inside the plugin folder and an absolute redirect being denied, so the skill now names both. In the last three, AWS had no denials and the others had one or two for chained commands. A subnet that declares both a network parent and a VLAN still leaves the VLAN as an empty box beside it, which is the mapper's one-parent limit. This one-Mac check has no second machine or interactive prompts. A fresh Claude Fable 5.1 / Medium agent reviewed `43b444d..ccdd73a` under D-021 and approved it, having rendered a model built around the guide's example and checked each guide line against the mapper. It could not check the six sessions, whose output is not in the repository. Its three P3 findings are addressed: sharper wording on nesting in a scope, `TB` in the example, and a test comment stating that the row test is one-directional |
| Update of the owner's install to the S07 merge | On 2026-11-03 the owner ran `plugin marketplace update` and `plugin update`, which moved it from `f50e66d6d3d5` to `02dc709b4e5a`. An earlier update had already taken it to `f50e66d` with no record, so the records' `3d235fa` was stale; the two differ only in records. On that copy, from a folder outside the repository and with a throwaway data directory, `capabilities` reports `0.4.0a4`, `validate` and `render` exit 0, and the AWS PNG matches the sample the owner inspected byte for byte |
| First live render through the plugin | A new headless session on Sonnet 5.5, with only Skill, Read, Write and Edit pre-approved, got no image from the installed copy. The skill said the output root must be a real directory, so the session ran `mkdir`, was denied three times, and never tried `render`, which creates a missing root. S08 corrected the skill. Through `--plugin-dir` on the corrected copy, a new session took the same Thai request through model, validation, render and a look at the PNG in 14 turns with no denials. The installed copy gets this after the next merge |
| Update of the owner's install to `43b444d`, and a live render from it | Measured on 2026-11-03 by the session that started S09, and recorded here at its request. The owner ran `plugin marketplace update` and `plugin update`, which moved it from `02dc709b4e5a` to `43b444d564c7`. On that copy, from a folder outside the repository with a throwaway `XDG_DATA_HOME`, the cache has 0 symlinks, `capabilities` reports `0.5.0a1`, and rendering `eks-namespaces` from `tests/fixtures/references/aws-three-tier.json` exits 0 with a PNG matching its baseline digest, `917353b23bdeafe5...`. A new headless session with no `--plugin-dir`, on Sonnet 5.5, with only Skill, Read, Write and Edit pre-approved, took a Thai request through model, validation, render and a look at the PNG in 16 turns. It had one denial, a combined `mkdir` and `cat` to write the model file, and it then used Write. So the first render through the installed plugin in a live session is done, on one Mac, in headless mode. A second machine and interactive permission prompts stay open |
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
- **The owner's install followed this branch until 2026-11-03.** The default branch did not contain the plugin then, so the marketplace was added with a branch ref. After the merge it was removed and added again from the default branch.

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

A fresh Claude Code session reviewed `c5f74b4..a94b47a` read-only. Record it as a substitute review, not the Astra/High review the [model strategy](../model-strategy.md) then named. It used the same model as the implementation, `claude-opus-5-5`, with session effort `xhigh`, and the implementing session wrote its brief, so its independence is limited. It found no Critical or High issues. It did not run the core tests or the full gate locally, relying on CI artifacts, and it had no `claude` CLI for installs, live runs or permission checks.

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

Removing or weakening any of 11 wrapper behaviors now fails a test: `--locked`, `--no-dev`, `--no-install-project`, `</dev/null`, `>&2`, `-I`, `-B`, the status mapping, the two absolute-path checks and the colon-safe import path. A relative `PATH` remains outside this protection, since control of the environment can already choose which programs run. The [Fable review](M7-fable-review.md) found one exception to this count: weakening the `HOME` path check fails no test.

The review also noted two M1 items outside this range: `field` echoes rejected key names, and `ID_DUPLICATE` does not name the duplicate ID.

## S07 follow-up

S07 / M3 adds `render` to the core, and the `claude-plugin` lane failed as designed until the skill changed. The skill now covers rendering, including the host requirement, the bundle, draft marking and the private-use limit, and it still forbids drawing outside the controlled renderer. The wrapper passes exit 4 through, because a failed render carries JSON diagnostics that exit 3 would misreport. New clean-copy tests render a bundle from a copy with its own locked environment and confirm that fonts and private-use terms come from that copy. Moving `diagrams` to runtime grows the plugin's private environment from its Pydantic set by `diagrams`, `graphviz`, `jinja2`, `pre-commit` and their dependencies, plus about 38 MB of icons. `pre-commit` is only an upstream dependency declaration, and nothing here runs it.

These passed actual CI [run 41539921034](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41539921034) at `cddb497`. They have not run in a live Claude Code session, and S07 did not change the owner's installed plugin. See the [S07 evidence](S07-controlled-rendering.md).

## S06 follow-up

S06 / M2 moved the core, and the checks built to catch that fired as intended. Five `claude-plugin` tests failed, and each was resolved by updating the skill, guide or expected contract, not by loosening a check. The caveat test now requires that `service_type` and `taxonomy` are rejected and no longer called unchecked. New tests cover catalog data in a clean copy, the Huawei warning, and the guide's type IDs and Kubernetes mappings. The plugin allowlist did not change, because catalogs and assets arrive through the `src` link, and the `catalog-license` lane covers them. The owner's installed plugin was not updated. See the [S06 evidence](S06-provider-catalogs.md).

## Fable review

Under D-021, Claude Fable 5.1 / High reviewed `c5f74b4..c6a59e5` in a fresh agent, with priority on the Medium and Low fixes, and [approved the range](M7-fable-review.md). It found one P2 at the head, in a skill sentence S06 changed, and three P3 findings. The P2 is fixed, and [the M7 review](M7-astra-review.md) settles the three P3 findings. Claude Opus 5.5 wrote the code, so reviewer and implementer share a vendor.

## Acceptance measurements at `97b0841`

Measured on 2026-11-05 by Claude Opus 5.5 on the first Mac, with Claude Code 2.1.309, on the owner's installed copy `97b0841eb926`, which `plugin update` fetched from the private repository. None of this is an owner's report, and no second Mac took part.

| Check | Result |
|---|---|
| Installed copy | The cache has 0 symlinks and 1.6 MB. `capabilities` reports catalog `2026.11.0`, `render_available: true` and no host blockers. The AWS reference validates, and its `eks-namespaces` PNG matches the baseline digest `49b713ed...` |
| First run with nothing cached | With a new data folder, a new uv cache and a new folder for uv's Python, the first `capabilities` downloaded Python 3.13.7 and the packages and exited 0 in 3 seconds on this network. The environment took 59 MB, the cache 59 MB and Python 48 MB. The second run took 1 second, and the PNG has the same digest |

### What the skill's pre-approval admits

There are [24 cases](M7-permission-probe.json). Each is a new headless session on Haiku 5.5 in the default permission mode, with only project settings loaded and only Skill pre-approved. It invokes the skill and issues one command, and every issued command matched its case byte for byte. A refused command is one the host says needs approval.

| Outcome | Forms |
|---|---|
| Admitted | The command with or without arguments; stdin from a file inside the working folder, by relative or absolute path; `render --output` at a relative path, or at an absolute path outside the working folder |
| Refused | `&&`, `;`, a newline and `&`; a pipe in either direction; a stdout redirect, inside or outside the working folder; `$(...)` and backticks; a longer command name; any variable prefix, harmless or not; `$HOME` in an argument; stdin from a file outside the working folder; and, as the control, another command |

No refused command left its marker file. This settles the open question on redirects: `schema > file` is refused. One limit remains: the pre-approval does not read arguments, so a session that spells out a path can add a bundle folder anywhere the user can write, with no question. The [plugin README](../../../plugins/cloud-architecture-diagrams/README.md#use) now says so.

### New sessions through the installed copy

Each is a new headless session on Sonnet 5.5, with the owner's real config, no `--plugin-dir`, and only Skill, Read, Write and Edit pre-approved. Each took its request through to a rendered bundle. I looked at the pictures from the first three, and not the edit's.

| Request | Turns | Refused | Result |
|---|---|---|---|
| Thai: AWS ALB, ECS Fargate and RDS | 25 | A `for` loop of catalog searches, and a chained `sed` | Lenient draft, marked as one. ECS Fargate is not in the catalog, and the session said so and did not swap in EKS |
| English: GKE Deployment, Service, Ingress and PVC | 15 | `mkdir` chained to a Python generator, twice, and `mkdir` alone | Strict. The picture shows the declared replicas, Service type and ports |
| Thai: Huawei Cloud ELB, two ECS, RDS and OBS | 19 | `cd` into a path it had mistyped, twice | Strict, with `ASSET_PRIVATE_USE_ONLY` relayed and no suggestion to share |
| Thai: edit the AWS model to add WAF | 21 | None | Existing IDs kept. WAF is not in the catalog either, so it stays a lenient draft |

Sessions still try chained commands although the skill says not to, and each recovered. With Write pre-approved for this test, the GKE session wrote a generator at `../gen/gen.py`, and the Huawei session first wrote its model under its mistyped path, both outside the working folder. A session that asks before acting would have asked.

### What real use found

**Some characters draw as boxes.** Neither bundled font has `→ ← ↔ ↑ ↓ ⇒ ✓ ✗ ✔ ✘ ≥ ≤ ≠`. A label holding one draws as a hex box in the PNG, and neither validation nor render reports it. The Thai AWS session wrote `→` in its title at once, and found the box only because the skill tells it to look at the PNG. A title holding `→ ← ✓` reproduces it. I rate this P2, as silent unreadable text against FR-042. **Fixed on the owner's word under D-034:** `render` now refuses such a label with `RENDER_TEXT_UNDRAWABLE`, exit 2, naming the element and the code points, and [the reasons are in the contract](../../design/core-contract.md). The fonts do hold the bidi and format controls, so [S07's P3-2](S07-fable-review.md) stays open.

A new headless session on Sonnet 5.5 through `--plugin-dir` then checked the fix. Asked for the title `ALB → EC2 → RDS` and the view title `Web ✓`, it validated, got the refusal from `render`, changed them to `ALB > EC2 > RDS` and `Web OK`, rendered, and told the requester what it had changed and why. [Fable/Medium approved the change](M7-fable-glyph-review.md), with five P3 findings, of which four are fixed. The fifth predates it: U+2028 and U+2029 pass the schema and draw as a line break.

**Some lines start in mid-air.** A line leaving a node from above can start above its icon, with nothing visibly attached. It showed in two of the four pictures I looked at, Huawei ECS to OBS and EC2 to S3. This is [S08's P3-2](S08-fable-review.md), which the owner's image pass already covers, and it stays open.

**The AWS catalog has gaps that ordinary requests hit.** [S12](S12-aws-ecs-lambda-waf.md) later adds ECS, Fargate for ECS, Lambda and WAF, and these measurements describe the catalog before that. It holds 48 types. ECS, Lambda and WAF are not among them, and Fargate appears only as the EKS profile. The P0 provider list does not name them, and [the milestones](../milestones.md) leave expanded coverage as later P1 work, so this is within scope. Both AWS requests here still ended as drafts. Lenient mode did its job: each type kept its name, and the picture says draft.

### What a real session asks for

Measured on the installed copy `c6c7490d8ca7`. There are [three runs](M7-permission-requests.json), each a new headless session on Sonnet 5.5 in the default permission mode, with no tool pre-approved. Its `--permission-prompt-tool` is a small server standing in for the person who answers: it records every request, allows the skill, reads of the plugin or the project, writes inside the project and a bare `mkdir` with any target, which no run asked for, and denies the rest. All three ended with a rendered bundle, and I looked at the edit's picture.

| Run | Requests |
|---|---|
| New model, the owner's real config | 2: the skill, and writing the model |
| Edit that model, the owner's real config | 6: the skill, one Python script to change the model, denied, and four edits of the model |
| New model, project settings only | 5: the skill, reading the guide, reading an example, a line of catalog searches joined together, denied, and writing the model |

**The plugin's own command asked nothing in any run.** It ran 16 times in all, including `validate` and `render`, and two more calls naming it were refused because other commands were part of them. So a person in this mode answers once for the skill and once per file change, and more only when a session runs anything else. The owner's rule that allows reading their home folder is why the real config asks for no reads.

This is the host's own request stream, but not its look. How the app draws a request, and whether an "always allow" answer removes the repeats, stay unseen.

### The acceptance copy

The owner ran `plugin marketplace update` and `plugin update`, which moved the install to `ea6c802ec4d3`, fetched from the private repository. That copy has 0 symlinks, and its `bin`, `skills` and README match the commit byte for byte. It reports catalog `2026.11.1`, `render_available: true` and no host blockers, and it finds the D-036 types.

Three new headless sessions on Sonnet 5.5 then used that copy, with the owner's real config, no `--plugin-dir`, no tool pre-approved, and the same stand-in. Their records are [under `acceptance_copy`](M7-permission-requests.json). I looked at the first and third pictures.

| Request | Turns | Requests | Result |
|---|---|---|---|
| Thai: WAF, ALB, an ECS service on Fargate, RDS, S3 and Lambda | 19 | 3: the skill, a `for` loop of catalog searches, denied, and writing the model | Strict, with no draft. The four new types it used, ECS cluster, Fargate for ECS, Lambda and WAF, drew with their icons, and the session added the cluster and said why. It did not use the plain ECS service type, which the [recheck](M7-astra-recheck.md) validated and rendered through this copy directly |
| Thai: add a cache if the catalog has one, keep the IDs, draw again | 20 | 1: the skill | The catalog has none. The session said so, changed nothing and invented no ID, then validated and drew again |
| English: a Kubernetes detail on EKS | 11 | 2: the skill and writing the model | Strict. The picture shows the declared replicas, labels, Service type and ports |

The plugin's own command ran 25 times with no request.

### What did not run

An interactive terminal session. This Mac's CLI has never finished first-run setup, because the owner uses the app, and a session driven through a pseudo-terminal stopped at the theme chooser. Finishing it would change the owner's `~/.claude.json`, so the run stopped there, and that file shows no onboarding state afterward. So no permission dialog has been seen by anyone: the runs above record what the host asks, not how it looks.

## Astra review

Fable's credit ran out, so on the owner's word (D-038) this milestone's review went through Codex CLI with `gpt-6-astra` at high effort, in a new session with no prior context. Its [report](M7-astra-review.md) requested changes at `8f9c246`, and it also repeated six permission cases that found a gap in the README's wording. It shares no vendor with the implementer.

| Finding | Disposition |
|---|---|
| F1, P2: no session has used a copy installed at the acceptance commit | Addressed by [the acceptance copy](#the-acceptance-copy), at `ea6c802` |
| F2: the manifest's missing version against P-019 | Waits for the owner's word on closing M7 |
| F3: the README turned a sample into a promise | Fixed. `> /dev/null` and read-only commands such as `ls` pass, and the README now says what was measured |
| F4: the stand-in allows `mkdir` anywhere | Fixed in the method's statement. No run asked for `mkdir`, so the 2, 6 and 5 requests stand |
| F5: a wrong count and stale statements | Fixed. I had first written 16 and then wrongly changed it to 17 before this review |
| F6: the guide left out two exceptions the core accepts | Fixed |
| C1: no test for a relative `HOME` | Fixed |
| C2: a damaged environment names no way out | Fixed. The message names the environment, and a test removes it and recovers |
| C3: a symbolic link from elsewhere exits 3 | Documented in the README and the wrapper, and a test pins it |

A [bounded recheck](M7-astra-recheck.md) through the same route approved closing M7 for `ea6c802`, under D-035's one Mac. It found two wording problems, both fixed: this table overstated which new types the session used, and two summaries still called the earlier P3 findings open. F5 and F6 hold, and it ran no Claude session.

## Not verified

- A second machine, which D-035 accepts, and any other operating system.
- How a permission dialog looks, in the Code tab or a terminal, and what an "always allow" answer does. Headless runs record what the host asks, and the Code tab check ran under bypass permissions.
- Authoring a model from the Code tab.

Prompts were run once each, so trigger rates are observations rather than measurements. A passing result covers the core, the catalog and the documented provider rules. It does not establish that anything is deployed or reachable.
