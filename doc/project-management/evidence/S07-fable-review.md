# S07 / M3 review by Fable

Date: 2026-11-03 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) / High, in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session. This is the M3 review under [D-021](../decisions.md#confirmed-user-direction). Claude Opus 5.5 wrote the renderer, so reviewer and implementer share a vendor.

**Disposition at `6353ef1`: changes requested, on three P2 findings, all in output-size handling.** There are no P0 or P1 findings, and five more are P3. The P2 findings now have [fixes](#fixes), which need their own review. M3 stays open until that passes and the owner has inspected the output.

## Identity and scope

- Base `f3f0789`, code head `cddb497`, reviewed at `6353ef1`. `cddb497..6353ef1` changes only `README.md` and `doc/`, which the root session confirmed.
- The reviewer edited nothing in the repository. Its full gate at the head passed 14 lanes and 959 tests. CI succeeded at `cddb497` (run 41539921034) and at `6353ef1` (run 41579564625).
- It read `render/*`, `cli.py`, the validation, catalog, gate and plugin changes, the skill and the main tests, and ran more than 25 probes through the real CLI.

## P2 findings

The root session reran these through the real CLI at `6353ef1`, with the shipped limits unless stated.

### P2-1: an output-size failure of a valid model exits 4

`REQUEST_CODES` in [`render/errors.py`](../../../src/cloud_architecture_diagrams/render/errors.py) holds only `RENDER_VIEW_TOO_LARGE`, `RENDER_GROUP_DEPTH_LIMIT` and `RENDER_TYPE_BLOCKED`. `RENDER_PIXEL_LIMIT` and `RENDER_ARTIFACT_LIMIT` say to split the view, yet they exit 4. The [core contract](../../design/core-contract.md) gives exit 2 to "a view that cannot be drawn as asked", and the skill treats exit 4 as a failed render such as a host problem.

Reproduced: 197 GCP VM resources, 3 groups and 300 labeled edges, inside the 200 / 300 limit, exit 4 with `RENDER_PIXEL_LIMIT`.

Fix direction: move the pixel and artifact codes into `REQUEST_CODES`, consider the other limit codes whose remedy is to split, and align the skill and README.

### P2-2: the documented 200 / 300 bound is not always reachable with icons

The evidence's timing table used `large_model`, which has no icons or edge labels. With the pixel limit lifted, these views measure:

| Entities / relationships | Reviewer, mixed relationship kinds | Root session, traffic only |
|---|---|---|
| 197 / 300, labeled | 45 Mpx | 38.0 Mpx, 1.4 s |
| 197 / 300, unlabeled | 34 Mpx | 28.9 Mpx, 1.1 s |
| 197 / 100, labeled | 58 Mpx | Not run |
| 150 / 225, labeled | 18.6 Mpx | 17.6 Mpx, 0.9 s |

The limit is 32 Mpx, so the result depends on labels and relationship kinds, and some in-bound views pass. The wall limit keeps its margin. The pixel limit is what rejects these views.

Fix direction from the reviewer: size the limits from icon views or make the layout denser, and state in the contract that the pixel limit is the effective bound.

Root session's note for the owner: T-012 makes 200 / 300 stability P1 under M4, and rejection here is bounded and suggests a split. So stating the effective bound belongs in M3, and the numbers can stay with M4-04. The reviewer's severity stands until the owner decides.

### P2-3: a tall or wide layout publishes a downscaled PNG as complete

Cairo scales a bitmap to fit 32767 pixels and only warns on stderr. [`render/execution.py`](../../../src/cloud_architecture_diagrams/render/execution.py) reads only font lines from the engine log, and [`render/checks.py`](../../../src/cloud_architecture_diagrams/render/checks.py) checks the PNG structurally. The contract says `diagram.png` is the same layout as a raster.

| Entities, no edges | Exit and status | SVG size | PNG size | Scale |
|---|---|---|---|---|
| 197 | 0, `complete` | 473 x 53876 | 288 x 32767 | 0.61 |
| 130 | 0, `complete` | 473 x 35741 | 434 x 32767 | 0.92 |
| 110 | 0, `complete` | 473 x 30328 | 474 x 30328 | 1.00 |

Fix direction: compare the SVG size with the PNG header, or read the warning, and then either fail with a request-class code or record the scale in the manifest with a warning diagnostic.

## P3 findings

The root session confirmed P3-1 and P3-2's cause by reading the code, and reran P3-2's validation. It did not rerun the others.

| ID | Finding | Evidence | Fix direction |
|---|---|---|---|
| P3-1 | Sandbox reads are allowed by default outside `$HOME`, including earlier bundles in the same output root. This matches the contract, so it is hardening | `/etc/passwd`, `/etc/hosts` and a sibling bundle's `model.json` were readable. Network, fork and exec, `$HOME` data and writes outside the request directory were denied | Deny reads by default and allow the engine's paths and the request directory |
| P3-2 | Unicode bidi and format controls pass validation and reorder what the reader sees | A name holding U+202E validates and drew as `sub DESREVER line` in the PNG. U+2028 is also accepted | Reject U+202A-202E, U+2066-2069, U+200E-200F and U+2028-2029, and keep what Thai needs |
| P3-3 | `test_every_render_code_is_exercised_by_a_test` checks only that the string appears in the test files | `tests/test_render_smoke.py:845-851` | Collect codes from real failures |
| P3-4 | `--output /tmp/x` and `$TMPDIR/x` are refused on macOS, by design, and the skill and README do not warn | Both give `RENDER_OUTPUT_PATH_UNSAFE` | Add a sentence to the skill and the remedy |
| P3-5 | Unconfirmed, from code only: a signal after `publish` and before stdout is written would escape as a traceback with a complete bundle on disk | `cli.py:61-65`, `render/__init__.py:309-324`. The window is milliseconds and was not reproduced | Catch `RenderFailure` in `_render` |

## P-026

**The reviewer agrees with [P-026](../decisions.md#recommendations-and-disposition).** "Reject HTML labels" means refusing the mechanism, so text that resembles markup can stay literal, and the probes confirm that end to end. That reasoning does not cover Unicode format controls, which do change what the reader sees (P3-2).

## Claims that did not hold

| Claim in the [S07 evidence](S07-controlled-rendering.md) | Result |
|---|---|
| Each output's content is checked against the graph | The SVG only; see P2-3 |
| The wall limit leaves a large margin at the view limit | The timing came from icon-free graphs. The margin does hold, but the pixel limit rejects some of those views first; see P2-2 |
| FR-046 is met locally, with a suggestion to split | The pixel-limit suggestion exits 4; see P2-1 |
| A test requires every diagnostic code to appear in the test files | Accurate, but it is string presence only; see P3-3 |

The rest of what the reviewer checked held, including the test counts, the CI run, clean-setup repeatability, the sabotage-listed behaviors, cleanup, the Huawei limit, the Kubernetes dimensions and strict and lenient behavior.

## What held

- Hostile text stays literal in DOT, SVG and PNG, and the SVG stays inside its allowlist.
- `/tmp`, `$TMPDIR`, `..`, group-writable, regular-file and symlinked output roots are refused. Rendering under `$HOME` works.
- SIGTERM and SIGINT during `dot` kill the engine, remove the request directory and exit 4.
- Five concurrent renders into one root give five complete bundles, with no scratch left and matching checksums.
- Two Kubernetes renders match byte for byte, and the manifest differs only in `bundle_id`.
- Strict refuses an unknown type and writes nothing. Lenient keeps provider, type and name and marks a draft.
- A Pod never nests in a Node under namespace or provider grouping.
- Huawei bundles carry the private-use limit in the image and the manifest.
- Without `PANGOCAIRO_BACKEND=fc`, `dot -v` reports Helvetica, which confirms P-027.
- Every gate lane can fail.

## Not run, and limits

SIGHUP; memory, temporary-storage and CPU limits through the CLI at real sizes; Thai visual inspection; a hostile `dot` on `PATH`; parent-directory races, which need a second user; the `rsvg-convert` cross-check; and a second machine. The sandbox probe ran `/bin/bash` under the renderer's profile, as the tests do, not `dot` itself. The reviewer did not exercise the owner's installed plugin.

## Fixes

On the owner's instruction, Claude Opus 5.5 fixed the three P2 findings in core `0.4.0a2`. The P3 findings are not touched. The local gate passes 14 lanes and 971 tests with none skipped, 12 more than before.

| Finding | Fix | Check |
|---|---|---|
| P2-1 | `RENDER_PIXEL_LIMIT` and `RENDER_ARTIFACT_LIMIT` are now request codes and exit 2. Time, memory and temporary storage stay at exit 4, because host load can move them | Exit status is asserted for both codes, and a real render of an in-bound icon view under a lowered limit exits 2 and publishes nothing |
| P2-2 | The contract and the diagnostic now say the pixel limit can refuse a view inside 200 / 300, and M4-04 names icon views. The limits and the layout did not change. This follows the root session's note above, which went to the owner before the instruction to fix | A 150 / 225 icon view renders at full size under the shipped limits, and the [S07 evidence](S07-controlled-rendering.md#measured-render-time) adds icon measurements |
| P2-3 | Every render compares the PNG's size with the SVG's. A uniform shrink publishes with `png.scale` in the manifest, now version 1.1.0, and a `RENDER_PNG_SCALED` warning in the result and `diagnostics.json`. Any other difference fails with `RENDER_PNG_INVALID`. See P-028 for why a shrink warns and does not fail | A real 197-icon render reports the scale and the warning, all fixture views stay at 1.0, and PNGs of another shape or an SVG with no usable size block the bundle |

Each of these 10 changes went into the real source, ran the new and changed tests, and was restored, with the sources hashing the same afterwards:

| Change | Tests failed |
|---|---|
| Pixel limit back to exit 4 | 2 |
| Artifact limit back to exit 4 | 1 |
| Scale never measured | 7 |
| Warning not added | 2 |
| Warning dropped from the result | 2 |
| Scale left out of the manifest | 4 |
| Shape comparison removed | 3 |
| A zero SVG size accepted | 1 |
| Skill says lenient bypasses every other error | 1 |
| Skill drops the scaled warning | 1 |

## Disposition

| Finding | State |
|---|---|
| P2-1, P2-2, P2-3 | Fixed in core `0.4.0a2`; re-review pending |
| P3-1 to P3-5 | Open for the owner; not fixed |

A fix needs another review of the changed code. This approves nothing beyond what it states, and it does not replace the owner's inspection of the output.
