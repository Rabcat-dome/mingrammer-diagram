# S10 review by Fable

Date: 2026-11-04 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session, which set its effort to High. The reviewer cannot read that setting. This is the review of S10 under [D-021](../decisions.md#confirmed-user-direction), and reviewer and implementers share a vendor.

**Disposition at `65d800b`: changes requested, on one P1 and three P2 findings.** All four concern the record or one packaging setting, and the reviewer called the code sound. The fixes below need a recheck.

## Identity and scope

Base `b6997c6`, head `65d800b`, which passed actual CI [run 41783171328](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41783171328). The reviewer ran the full gate and edited nothing tracked. It did not run `scripts/reproduce_core.py`, repeat the 14 sabotage changes, verify the Work plugin's version string, open the tests behind the 38 IDs it did not sample, or look at actual CI.

## The P0 report

The reviewer sampled 33 of the 71 IDs across all states. **It found no state too generous, no `partly` hiding a `not_met`, and no `met_with_owner` reading more into D-018, D-022 or D-023 than they say.** It called T-002, the root session's override of an auditor's `partly`, defensible but the thinnest, and accepted it because the owner note discloses the reading.

## Findings

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| P1 | The reproduction proof was `{}` at the reviewed commit, and the guard checked only that the file exists | Read | Fixed. The real proof is committed, bound to a digest of its source, and a test requires it to pass and still match |
| P2 | The record said the lane fails if `.agents` or `doc` return to the sdist, and it did not | `forbidden_names` returned nothing for them | Fixed: the sdist has its own list |
| P2 | An sdist built in a worktree shipped its `.git` file, so the lane failed in every worktree and "the local gate passes" held only for a primary checkout | The reviewer's gate failed there | Fixed: the sdist excludes `/.git` |
| P2 | `CI_RESULT` was left in the record | Read | Fixed |
| P3 | The network test's wording overstated: it is in-process TCP only | Read | Fixed in the record |
| P3 | The guard let `met_with_owner` have no check, accepted a decision that does not exist, did not check a test's lane against its file, and caveats sit in owner notes | Read | The first two are fixed. The others are stated in the record |
| P3 | The page escaped a pipe wrongly, with no such text today | Read | Fixed |
| P3 | The inventory walks lock dependencies ignoring markers, and 12 of its 20 rows are there because `diagrams` declares `pre-commit` | Read and checked | Stated in the inventory. It fails closed if a marked package appears |
| P3 | NFR-013's remote half and FR-028's label text needed a sentence | Read | Fixed: both records carry a note |

## What held

Per the reviewer: the sdist's exclusions removed nothing a build needs; the wheel test proves a clean install, sharing only the base interpreter, a hash-verified uv cache and the lock; `reproduce_core.py` is honest about what it shares; the test totals match; and the new FR-004, FR-006, FR-029, T-017 and FR-061 tests fail for the right reasons.

## Disposition

| Findings | State |
|---|---|
| P1, the P2 findings, and P3 findings marked fixed | Fixed; recheck pending |
| Guard: a test's lane against its file, and caveats in owner notes | Stated in the record |

This approves nothing beyond what it states, and it does not replace the owner's decisions on the gaps or their run in Work.
