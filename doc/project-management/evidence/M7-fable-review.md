# M7 plugin review by Fable

Date: 2026-11-03 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) / High, in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session. This is the M7 review under [D-021](../decisions.md#confirmed-user-direction). Claude Opus 5.5 wrote the code, so reviewer and implementer share a vendor.

**Disposition: approved for `c5f74b4..c6a59e5`.** The Medium and Low fixes hold at the root, and they still hold at `6353ef1`. One P2 existed at that head, in a sentence S06 changed, so it falls outside the reviewed range. It is now fixed, and three P3 findings are open. M7 is not closed, because a second machine and interactive permission prompts remain unverified.

## Identity and scope

- Range: `c5f74b4..c6a59e5`, with priority on `a94b47a..917f46f`, which no earlier pass covered. Reviewed at `6353ef1`, and every finding was checked there.
- The reviewer edited nothing in the repository. Its full gate at the head passed 14 lanes.
- Rendering was left to the [S07 review](S07-fable-review.md).

## Findings

The root session reran each one below at `6353ef1`, except where the row says otherwise.

| ID | Finding | Evidence | Fix direction |
|---|---|---|---|
| P2 | [`SKILL.md:36`](../../../plugins/cloud-architecture-diagrams/skills/architecture-model/SKILL.md) says lenient mode "bypasses every other error", which contradicts the core and the same sentence's own conclusion. `4b9b826` introduced it; `917f46f` read "bypasses no core error". No test guards it | `validate --mode lenient` with `taxonomy: "made.up"` exits 2 with `CATALOG_TAXONOMY_UNKNOWN` | Say "bypasses no other error", and add a test |
| P3 | The wrapper's `HOME` absolute-path check has no regression test | Changing `/*)` to `?*)` for `HOME` passed all 52 plugin tests in the reviewer's mutation run. The behavior itself is right. The root session confirmed by reading that no test sets a relative `HOME`, and did not rerun the mutation | Add a case with a relative `HOME` and no `XDG_DATA_HOME` |
| P3 | A damaged private environment never heals, and the failure gives no recovery hint | After deleting `site-packages/pydantic`, `uv sync` trusts the dist-info, and every run prints `ModuleNotFoundError` and exits 3 with "the runtime failed unexpectedly". The exit code is right, but the skill tells the model not to install packages | Name the environment directory on that path, or retry once with a reinstall |
| P3 | The wrapper fails when run through a symlink outside the plugin | `/elsewhere/cloud-diagrams capabilities` exits 3 with no `pyproject.toml` found, because `root` comes from `$0` unresolved. Nothing uses this route today, and whether Claude Code's `bin/` exposure could is unconfirmed | Resolve `$0` first, or document the limit |

## Medium and Low fixes

| Fix | Verdict |
|---|---|
| `view_exclusions` for every view | Fixed at the root; matches an independent computation |
| Guide caveats on `taxonomy` and `k8s.<kind>` | Fixed at `917f46f`; S06 enforcement supersedes them at the head |
| Wrapper setup-flag tests | Partly fixed; every behavior is protected except the `HOME` check above |
| Exit 1, dash exit 2 and UTF-8 output | Fixed at the root; the old wrapper reproduced the dash failure |
| Relative `XDG_DATA_HOME` and colon in the path | Fixed at the root |
| Gate doc wording, pinned contract fields and version test | Fixed |
| `package-contents` SHA-256 | Fixed, with a negative test |
| Digests covering `pyproject.toml` and `uv.lock` | Fixed, with a link-target test |
| Space, hostile-variable and project-file tests, 13 guide lists and the `ownership` rule | Fixed; S06 reworded the rule and it still states it |

## Claim that did not hold

The [M7 evidence](M7-claude-plugin.md) said removing or weakening any of 11 wrapper behaviors fails a test. That is false for the `HOME` check. The other 10 mutations each failed one test, as claimed.

## What held

- `/bin/sh` and `/bin/dash`; paths with spaces, colons and a leading dash; relative invocation.
- `LC_ALL=C`, ISO-8859-1, and hostile Python, uv and shell variables.
- Usage errors exit 64 with empty stdout. Empty stdin exits 2, and oversized input gives `INPUT_SIZE_LIMIT`.
- Four concurrent first runs into a new data home, and old and new plugin versions racing on one environment, all exit 0.
- Lock changes in both directions, deleted interpreter links and a read-only plugin copy recover or work correctly.
- The allowlist, link targets, Git file modes, per-file SHA-256, digests, guide lists and version agreement.
- CI run 41453874994 succeeded at `917f46f`, and a clean build there reproduced wheel `47232d0c...` byte for byte.

## Not run, and limits

The reviewer had no `claude` CLI on its PATH, so installs, `plugin validate`, live sessions, `allowed-tools` matching and redirection prompts did not run. A redirect such as `schema > file` may be admitted, which stays unconfirmed. No second machine or cold first run was tried. S06 and S07 code was examined only where it touches the skill, the wrapper or validation output.

Edge observations, not findings: closed stdin gives a traceback and exit 3, closed stdout gives a silent exit 0, and the allowlist test cannot see gitignored files.

## Disposition

On the owner's instruction, Claude Opus 5.5 corrected the P2 sentence to "bypasses no other error". A new test checks the core's behavior and the wording, and restoring the old wording fails it. The [re-review](S07-fable-review.md#re-review-at-93b7d11) confirms the fix at `93b7d11`, and the [final recheck](S07-fable-review.md#final-recheck-at-c8fc687) accepts the series as this P2's disposition. The three P3 findings are not fixed and stay open for the owner.
