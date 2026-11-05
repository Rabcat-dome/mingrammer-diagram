# S14 — Three Open P3 Findings

Date: 2026-11-05 (Asia/Bangkok) | Branch: `codex/open-p3-references` | Implementer: Claude Opus 5.5

**Result: P3-1, P3-2 and P3-3 of [the final review](M6-fable-final-review.md#findings) are fixed. No baseline changed, the core stays at `0.5.0a2`, and the tag `v0.1.0-alpha.1` does not move.** The owner said to go on to the next step, and the open P3 findings came next in the list they had been given. P3-4 is a reading of the records that the review says needs no change, so it stays as it is.

## What changed

| Finding | Before | Now |
|---|---|---|
| P3-1 | Any selected line between two entities hid a typed reference's note, whatever its kind | Only the kind that draws the reference hides it, in either direction: `traffic` for `service_refs` and `target_refs`, `storage` for the volume and storage class references, `configuration` for config, secret and service account references, and `ownership` for `owner_ref`. A line of another kind leaves the note |
| P3-2 | `test_every_kind_of_typed_reference_has_a_note` only compared field names | It now maps a model for each of the nine fields, and checks the note appears, disappears for the kind that draws it in both directions, and stays for all 13 other kinds. A separate test holds the list of fields |
| P3-3 | `build.json` said `source_dirty: true` on a clean checkout when Git's global ignores were absent | `.claude/` is in the repository's `.gitignore` |

The model guide states the rule for P3-1. The owner's reference images are unaffected: all 26 views match their baselines.

## Checks

Five sabotaged versions each fail a test for the reason named: any kind hiding the note, the `owner` line removed, the `service` line removed, and `claim` and `owner` tied to the wrong kind.

The test for each of the nine fields drives the mapper directly, so it also tries directions the validator would refuse. One real model through the validator covers `secret_refs`, in both directions, with `management` and `observability` lines.

No fixture draws a typed reference with a line outside the table, in any of the fixtures, and every view matches its baseline. The core reproduces from a new clone at `cad6098`, and the gate passes 17 lanes.

## Review

**No independent review has finished.** Fable's credit is used up (D-038). Codex CLI with `gpt-6-astra` at medium effort started on `cad6098`, then stopped at its usage limit with no report and no disposition. Before it stopped, its log said the selected tests passed, each sabotage failed as named, and the table matched the rules it had inspected so far. That is progress, not approval.

## Limits

- **The core version does not change.** As with D-036 and D-037, this waits for the next tag, so `0.5.0a2` covers more than one behaviour on `main`. A bundle's catalog version does not tell these apart here, and the plugin's commit or digest does.
- **No live session ran this.** It changes what a detail view says in an unusual case, and the tests hold it.
- **The Work plugin** is not rebuilt. D-040 defers its check, and the copy installed is older than this.
