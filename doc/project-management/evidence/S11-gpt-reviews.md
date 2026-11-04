# S11 — GPT reviews of everything after S06

Date: 2026-11-04 (Asia/Bangkok) | Base `5569459` | Head `aefcdbc` | Decision: D-025

**Result: both reviewers requested changes. The Claude session reproduced or confirmed all 15 findings, and nothing is fixed yet.** Neither reviewer found a way for a hostile model alone to write outside the output root, follow a symbolic link or put active content in the SVG. That is what they looked for and did not find, and it is not a proof.

## Why this ran

Since this base, Claude Opus 5.5 did the implementation and Claude Fable 5.1 did the reviews, so they shared a vendor. These two reviews are from another vendor, on top of the Fable reviews.

| Reviewer | Model in the host's session record | Report | Disposition |
|---|---|---|---|
| Astra | `gpt-6-astra` / high | [Report](S11-astra-review.md) | Changes requested, three P2 |
| Sol | `gpt-6.1-sol` / high | [Report](S11-sol-review.md) | Changes requested, one P1, five P2, eight P3 |

Neither reviewer could read its own model setting, so the model comes from the session record. The owner chose Astra, and the first chat ran on Sol, the default in this host's settings. It finished before the Astra chat began, so both are recorded. Sol's report was at the path Astra would write to, so it was moved out of `reports/` three minutes after the Astra chat began, and Astra's calls had not read it by then. Both reviewers say they read the Fable reviews only after their first pass. The gate passed for both, with 17 lanes and 1,461 tests, so these findings are all things the gate does not catch.

## Findings

"Reproduced" means the Claude session ran the failing case itself, without the reviewers' scripts. "Read" means it confirmed the code does this and did not run the failure.

| ID | Finding | Reviewer | Their rank | Check | Proposed action |
|---|---|---|---|---|---|
| G1 | CI uploads all of `reports/`, including private-use bundles and the wheel with Huawei icons, while the step's name says "synthetic" | Sol | P1 | Read. The runner's latest copy has 20 private-use bundles and the wheel. GitHub holds 65 live artifacts, 670 MiB, each expiring after 14 days | Upload a list of text reports only. The repository is private and already tracks 36 Huawei icon files, so the audience is the same, and this session ranks it P2 |
| G2 | A PNG with valid framing and an undecodable pixel stream is published as complete | Both | P2 | Reproduced at `check_png`. It needs a fault in the engine's output, and no model input is known to cause it | Decode the stream, within the limits, before publishing |
| G3 | The Work plugin sends private-use image bytes to the host, as a preview and through `read_artifact` | Sol | P2 | Read `_published` | The owner's decision, below |
| G4 | The server can exit while a child it just started is still running, because registration follows the start | Both | P2 | Read. Each reviewer forced this with its own probe, and this session did not | Shutdown waits for starts in progress, for calls and for setup |
| G5 | With two `located_in` relations, swapping their order flips strict validation | Sol, and an Astra supplement | P2 | Reproduced in both reviewers' forms | Refuse a boundary with more than one region |
| G6 | A Pod assigned to a Node only by a `scheduling` edge is labelled `node: unspecified` beside that edge, and sits directly under the cluster | Sol | P2 | Reproduced | Use the edge for the label and the nesting |
| G7 | A resource in another provider's security zone is drawn inside that provider's box, with no box for its own provider | Astra | P2 | Reproduced: `_provider.external`, then `trust`, then the GCP resource | Keep each entity's provider context, and keep the membership visible |
| G8 | If the final directory sync fails after the rename, the render reports failure with a complete bundle visible | Sol | P3 | Read | Report success after the commit point, with a warning |
| G9 | 16 nested boundaries in a provider view publish with 17 levels, against a declared limit of 16 | Sol | P3 | Reproduced | Check depth after adding the provider box |
| G10 | `read_artifact` returns an outside file through a hard link in a bundle folder. It needs existing local state, and a tool argument alone cannot create it | Sol | P3 | Reproduced | Refuse a file with more than one link |
| G11 | A late cancellation can leave a stale token, which would cancel a later call that reuses the ID | Sol | P3 | Read | Clear the token when the call ends |
| G12 | A request ID that is an array or object, or bad JSON with a control character in its ID, ends the server | Sol | P3 | Reproduced on the installed server | Refuse the frame with a protocol error |
| G13 | Setup's `uv sync` permits source builds, whose build dependencies the lock does not cover. A completed unlocked install is unconfirmed | Sol | P3 | Read: the command has no `--no-build` | Add `--no-build`, once every locked package is shown to have a wheel |
| G14 | The release audit passes an empty sdist and a wheel of empty files. The gate's other wheel checks still cover the wheel, and nothing else covers the sdist's contents | Sol | P3 | Reproduced | Require the sdist's contents, and read the wheel's |
| G15 | `reproduce_core.py` exits zero when the routes disagree, or with no views | Sol | P3 | Read line 221 | Include both in the exit status |

The [`busy` answers](S09-Work-validation.md#busy-answers) from the Work run are a further open P3, and the same fix batch can take them.

## Report states these affect

These are at `aefcdbc`. The [P0 report](S10-p0-traceability.md) is unchanged for now, because the fixes above are meant to restore them.

| ID | State | Named by | Linked finding |
|---|---|---|---|
| FR-040, FR-043, NFR-010 | `met` | Both | G2 |
| FR-021 | `met_with_owner` | Astra | G7 |
| FR-046 | `met` | Sol | G9 |
| NFR-003 | `met` | Sol | G10. Astra sampled it and found no overstatement, and its report does not mention hard links |
| FR-048 | `met_with_owner` | Sol | G5, G6 |
| NFR-004 | `met_with_owner` | Sol | G1, G3. Astra sampled it and raised no objection, and the two disagree here |

## Decisions left for the owner

- **G3.** D-018 accepts the rights risk for private personal use and says nothing about sending images to a chat host. A Huawei view can keep its preview, with this stated in the README, or it can stay on disk and be opened by its path.
- **G1's existing artifacts.** They expire by themselves within 14 days. Deleting them sooner cannot be undone.

## Limits

- Fixes that touch the Work plugin change its version, so the [Work check](S09-Work-validation.md) must run on the fixed version.
- G2's and G4's consequences need a fault or an exact timing, and neither was seen happening on its own.
- Neither reviewer ran real Work, a second machine or the fresh-clone reproduction, and neither audited all 71 report records.
- Both reviewers share a vendor with each other, and neither shows the code is correct.
