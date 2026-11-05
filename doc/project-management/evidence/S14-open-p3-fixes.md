# S14 — Three Open P3 Findings

Date: 2026-11-05 (Asia/Bangkok) | Branch: `codex/open-p3-references` | Implementer: Claude Opus 5.5

**Result: P3-1, P3-2 and P3-3 of [the final review](M6-fable-final-review.md#findings) are fixed. No baseline changed, the core stays at `0.5.0a2`, and the tag `v0.1.0-alpha.1` does not move.** The owner said to go on to the next step, and the open P3 findings came next in the list they had been given. P3-4 is a reading of the records that the review says needs no change, so it stays as it is.

## What changed

| Finding | Before | Now |
|---|---|---|
| P3-1 | Any selected line between two entities hid a typed reference's note, whatever its kind | Only the kind that draws the reference hides it. At `da83f0a` that held in either direction, and [the follow-up](#follow-up-after-review) adds direction. A line of another kind leaves the note |
| P3-2 | `test_every_kind_of_typed_reference_has_a_note` only compared field names | It now maps a model for each of the nine fields, and checks the note appears, disappears for the kind that draws it in both directions, and stays for all 13 other kinds. A separate test holds the list of fields |
| P3-3 | `build.json` said `source_dirty: true` on a clean checkout when Git's global ignores were absent | `.claude/` is in the repository's `.gitignore` |

The model guide states the rule for P3-1. The owner's reference images are unaffected: all 26 views match their baselines.

## Checks

Five sabotaged versions each fail a test for the reason named: any kind hiding the note, the `owner` line removed, the `service` line removed, and `claim` and `owner` tied to the wrong kind.

The test for each of the nine fields drives the mapper directly, so it also tries directions the validator would refuse. One real model through the validator covers `secret_refs`, in both directions, with `management` and `observability` lines.

No fixture draws a typed reference with a line outside the table, in any of the fixtures, and every view matches its baseline. The core reproduces from a new clone at `cad6098`, and the gate passes 17 lanes locally, on a tree whose only change was that proof, not yet committed. CI at `cad6098` failed `release-audit`, because the committed proof still described the source before. CI on `main` at `da83f0a` passes all 17 lanes.

## Review

**No independent review has finished.** Fable's credit is used up (D-038). Codex CLI with `gpt-6-astra` at medium effort started on `cad6098`, then stopped at its usage limit with no report and no disposition. Before it stopped, its log said the selected tests passed, each sabotage failed as named, and the table matched the rules it had inspected so far. That is progress, not approval. The owner chose to merge first and have it reviewed afterward (D-041).

Two reviews of `201792c..da83f0a` then ran. Claude Opus 5.5, in a fresh agent at medium effort, [approved it with seven P3 findings](S14-opus-review.md). It shares a model with the implementer. Codex CLI with `gpt-6-astra` at medium effort, queued for after its limit reset, [approved it with no findings](S14-astra-review.md). They differ on one point. Codex reads a `traffic` line as stating a typed reference in either direction, and Opus's F1 does not. I follow Opus, because a Pod sending traffic to a Service does not say that the Service selects the Pod.

## Limits

- **The core version does not change.** As with D-036 and D-037, this waits for the next tag, so `0.5.0a2` covers more than one behaviour on `main`. A bundle's catalog version does not tell these apart here, and the plugin's commit or digest does.
- **No live session ran this.** It changes what a detail view says in an unusual case, and the tests hold it.
- **The Work plugin** is not rebuilt. D-040 defers its check, and the copy installed is older than this.

## Follow-up after review

On `codex/s14-review-fixes`, after both reviews:

| Finding | Disposition |
|---|---|
| F1: a reversed `traffic` line hid a reference it does not state | Fixed. A line hides a note only running the way the reference means, `ownership` runs from the owner, and an undirected line counts either way. It predates S14 |
| F2: nothing tested a reference with more than one target | Fixed with a test |
| F3: nothing tested an undirected line | Fixed with a test |
| F4: a note can repeat a line of another kind | Kept by design, and the guide and the contract now say so |
| F5: the contract did not state the rule | Fixed |
| F6: HANDOFF listed the Work build as remaining | Fixed |
| F7: the gate's pass omitted where it ran | Fixed above |

Four sabotaged versions each fail a test for the reason named: direction ignored, undirected lines counted one way, ownership read from the dependent, and one drawn target hiding the whole line. No baseline changed.

