# S11 — GPT reviews of everything after S06

Date: 2026-11-04 (Asia/Bangkok) | Base `5569459` | Head `aefcdbc` | Decision: D-025

**Result: both reviewers requested changes. The Claude session reproduced or confirmed all 15 findings, and fixed them at `9fb199d`. [Fable requested changes](S11-fable-review.md) on those fixes at `3aa566d`, so they are not merged.** Neither reviewer found a way for a hostile model alone to write outside the output root, follow a symbolic link or put active content in the SVG. That is what they looked for and did not find, and it is not a proof.

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

## Fixes

Claude Opus 5.5 made these on `codex/s11-review-fixes`. No reference image changed: `visual-regression` passes against the baselines the owner passed, which are untouched. One thing does change for a model: a boundary that reaches two regions used to depend on their order, and now always fails.

| ID | Fix | A test that fails without it |
|---|---|---|
| G1 | CI uploads `reports/*.log`, `*.xml` and `*.json` only. The wheel and bundles stay on the runner, and the local reports held no PNG data or `<svg` when checked | `test_ci_uploads_only_text_reports` |
| G2 | `check_png` decodes the stream in bounded pieces. It checks each row's filter byte and the exact size, requires one stream in adjacent chunks, and refuses a second header, interlacing and palette images, which the engine does not write | `test_pixels_that_do_not_decode_block_the_bundle` |
| G3 | The README says that previews and files read through a tool reach the host (D-026) | `test_the_readme_says_what_reaches_the_host` |
| G4 | Starting a child and registering it are one step under the lock, so shutdown waits for a start in progress, and nothing starts once stopping | `test_shutdown_stops_a_core_caught_between_its_start_and_its_registration`, and the same for setup |
| G5 | A boundary whose parent and `located_in` relations reach two regions gets `BOUNDARY_LOCATION_MULTIPLE`, in either order | `test_a_boundary_in_two_regions_fails_in_either_order` |
| G6 | A `scheduling` edge to a Node gives a Pod with no `node_ref` its Node, for nesting and notes. An edge to a NodePool does not | `test_a_scheduling_edge_alone_places_a_pod_on_its_node` |
| G7 | In `provider` grouping nothing nests inside another provider's group, and the membership stays as a note | `test_a_foreign_security_zone_keeps_a_resource_in_its_own_provider` |
| G8 | A failed sync after the rename removes the bundle, so failure still means nothing was published, and a retry works | `test_a_failed_sync_after_the_rename_leaves_nothing_published` |
| G9 | The limit counts the provider box, so a provider view takes 15 model levels | `test_the_depth_limit_counts_the_provider_box` |
| G10 | A bundle file with more than one link is refused | `test_a_hard_link_in_a_bundle_is_not_read` |
| G11 | A finishing call leaves `calls` before its token clears, and a cancel checks and sets under one lock | `test_a_cancel_arriving_as_a_call_ends_leaves_no_token` |
| G12 | An ID that is not a string or number gets `-32600`, a cancel naming one is ignored, and any other failure on a frame gets `-32603` with only its type logged | `test_an_id_that_is_not_a_string_or_number_is_refused`, `test_an_unexpected_failure_on_a_frame_is_answered_and_the_server_goes_on` |
| G13 | Setup passes `--no-build`, and the real setup in `package-contract` shows the lock still installs | `test_setup_refuses_a_source_build` |
| G14 | The audit requires named files in each archive, and refuses a required file that is empty | `test_an_empty_source_archive_fails_the_audit`, `test_a_wheel_of_empty_files_fails_the_audit` |
| G15 | `reproduce_core.py` fails with no views or with routes that disagree | `test_a_reproduction_proof_fails_unless_it_proved_something` |
| `busy` | The skill's row names both causes, and the cap has a test | `test_too_many_calls_at_once_get_a_stable_busy_answer` |

### Sabotage

Undoing or weakening a fix, one change at a time, gave 47 changes, and each now fails a named test. Four passed at first, and each showed a real gap:

- An illegal bit depth was refused only because its size came out wrong, so a test now uses one whose size adds up.
- Dropping the check for a cancel that arrives before its child starts passed every test, and has done since S09. It now has a test.
- Removing the decode's memory bound passed, so a test now measures the peak.
- Applying the provider rule to every grouping passed, so a test now pins it to `provider` grouping.

No deterministic test covers a cancel's check and set being under one lock, because that needs two threads at one instruction.

### Validation

Actual CI [run 41856283191](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41856283191) passed 17 lanes and 1,527 tests with 0 skipped at `b862506`, on the runner, which is this same Mac. Its wheel has the digest the reproduction proof records. Its artifact is 42 KB, where earlier runs' were about 21 MiB, so G1's fix took effect from the first push of this branch. The artifact from that first push holds 29 text files, with no PNG data or `<svg` in any of them. [Run 41855686612](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41855686612) at `9fb199d` failed as expected, on the proof test alone, because the proof binds to the source and came in the next commit.

## Fable recheck

On the owner's word, Claude Fable 5.1 rechecked `aefcdbc..3aa566d` in a fresh agent, with its effort set to High, and [requested changes](S11-fable-review.md). It found G1 to G15 each fixed for the case the reviewers named, and four new findings. It shares a vendor with the implementer. The Claude session reproduced each one, except the contract row, which it read.

| Rank | Finding | Check |
|---|---|---|
| P2 | G5's fix over-reaches. It refuses an `environment`, `security_zone` or `cluster` in two regions, which was valid in either order at the base, and nothing reads their region | Reproduced at the head, for each of the three kinds |
| P3 | The audit matches required names by suffix, so `tests/README.md` satisfies `README.md` | Reproduced |
| P3 | A request ID of `1e400` is echoed as `Infinity`, which is not JSON | Reproduced on a build of this head |
| P3 | The contract's limits row does not say that the provider box counts | Read |

None of these is fixed yet.

## Report states these affect

The reviewers named these at `aefcdbc`. Their states in the [P0 report](S10-p0-traceability.md) stay as they were, because the fixes close what was named, and each record now names its new tests.

| ID | State | Named by | Linked finding |
|---|---|---|---|
| FR-040, FR-043, NFR-010 | `met` | Both | G2 |
| FR-021 | `met_with_owner` | Astra | G7 |
| FR-046 | `met` | Sol | G9 |
| NFR-003 | `met` | Sol | G10. Astra sampled it and found no overstatement, and its report does not mention hard links |
| FR-048 | `met_with_owner` | Sol | G5, G6 |
| NFR-004 | `met_with_owner` | Sol | G1, G3. Astra sampled it and raised no objection, and the two disagree here |

## Owner decisions

D-026 records two defaults the owner can still change:

- **G3.** D-018 accepts the rights risk for private personal use and says nothing about sending images to a chat host. A Huawei view keeps its preview, and the README states this.
- **G1's existing artifacts.** They expire by themselves within 14 days, and were not deleted, because deleting cannot be undone.

## Limits

- These fixes changed the Work plugin's version to `0.1.0-alpha.1+4e035b4d7e69`, so the [Work check](S09-Work-validation.md) must run on that version.
- The reproduction proof is now at `9fb199d`, and all 26 views match in both routes. It keeps the [limits S10 states](S10-release-checks.md#core-reproduction).
- G2's and G4's consequences need a fault or an exact timing, and neither was seen happening on its own.
- Neither reviewer ran real Work, a second machine or the fresh-clone reproduction, and neither audited all 71 report records.
- Both reviewers share a vendor with each other, and neither shows the code is correct.
