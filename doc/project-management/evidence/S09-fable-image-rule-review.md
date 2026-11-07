# Review of the Image Rule and the Work Check After the Release

Date: 2026-11-07 (Asia/Bangkok) | Range: `9317be6..a4537a7` on `codex/work-check-skill-rule` | Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), started at Medium, in a fresh read-only agent | Implementer: Claude Opus 5.5, so reviewer and implementer share a vendor

**Disposition: approved, with four P3 findings and no P1 or P2.** The reviewer started with no context from the implementing session. It had the diff, the files, the Work session record and the bundles, and none of the implementer's conclusions. The commit adds D-042's rule to both skills, a test for each, and the records of [the Work check after the release](S09-Work-validation.md#after-the-release).

## Findings

| ID | Severity | Where | Finding | Fix direction |
|---|---|---|---|---|
| F1 | P3 | Both skills, the paragraph that starts "Hand over a bundle" | It puts `node: unspecified` under Kubernetes detail views, but the renderer draws that line in any view. The paragraph's list of English text also leaves out the notes the renderer adds in any view, such as `subnet:`, `location:`, `network:` and `namespace:`, the typed-reference notes in detail views, such as `service:`, `target:` and `storage class:`, and the `DRAFT` and icon-rights lines. A chat could then tell the user that an overview has no English property lines | Name the notes drawn in any view apart from the detail lines, and add "and similar" or name the `DRAFT` and rights lines |
| F2 | P3 | `tests/test_work_plugin.py`, `tests/test_claude_plugin.py`, the new tests | They pin "Never edit, translate, redraw or convert", the three examples and "stays in English", but not "never show a changed image in their place", which is what check 5's chat broke, or "Copying the files unchanged is fine" or the categories of English text | Also assert the clause about showing a changed image and the category names |
| F3 | P3 | Same tests | A change to the paragraph's opening words raises `StopIteration` rather than a failed assertion. Reading every baseline means a later baseline change that drops the ClusterIP Service would fail a skill test for an unrelated reason | Use an assertion with a message, or pin one named baseline |
| F4 | P3 | [S09 Work check](S09-Work-validation.md#after-the-release), check 3 | "All 10 IDs" does not say what it counts. The model holds 11: its own ID, the view, the VPC, four resources and four relationships, and all 11 stayed. Earlier sections give a count the same way without saying what it covers | State the count and what it covers |

## What the reviewer checked

- **The skill against the renderer.** The three examples are true: `type:` and `ports:` come from the detail properties, `node: unspecified` from the Pod note, provider headings from `provider` grouping, `Legend` and the edge kinds from the drawing code, and each type name from the service label, which is left out when it equals the name. Names, labels, titles, `environment` and the relationship fields are drawn as written. F1 covers what the list omits.
- **Conflicts.** None. The paragraph extends the one before it from generated code to changed images, and agrees with the Work skill's Report step and the Claude skill's step that shows `diagram.png`.
- **The tests.** Both pass. They catch the core sentence's removal or an example that stops being true. F2 and F3 cover their gaps. The reviewer did not repeat the five sabotage edits.
- **The records against the session record and bundles.** Originator, model, effort, approval policy and sandbox for all six turns. Each check: the version, core and runtime state in check 1, with no `setup_runtime` call; the `SCHEMA_FIELD_INVALID` on the missing `environment` and its correction in check 2; the IDs kept and added and the two renders in check 3; `REFERENCE_MISSING` with no render in check 4; in check 5 the model's origin in the app's memory and an earlier bundle, the two pairs of renders, the shared `model.json` digest, the Ingress and PVC notes, and every step of the chat's changes to the images, including that the ZIP holds the original files byte for byte; the six types in check 6, and its web searches. Also the reads of `src`, the server and the S04 skill, and no `busy` or `RUNTIME_INSTALLING`. D-042 and HANDOFF items 3 and 5 to 8 match, and neither installed plugin holds the paragraph.
- **Overclaims.** None found. The record states that the owner did not report how the images appeared or whether the files opened.
- **Reproduction and CI.** Rendering the GKE overview, GKE detail and serverless models again reproduces `diagram.svg`, `diagram.png` and `view.json` byte for byte. The Work plugin's content digest, recomputed from the clean tree, is `2d1966a9c1e8`. Actual CI [run 42361496323](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42361496323) passed at `a4537a7`.

Not checked: the owner's Thai reply quoted in D-042, which is not in the session record; re-rendering the two AWS three-tier bundles; the sabotage edits; the full gate; the PNGs by eye; the check 3 model beyond its IDs and labels.

## The implementer's check of the findings

F1 is confirmed in `src/cloud_architecture_diagrams/render/graph.py`, where the Pod's `node: unspecified` line and the membership notes are added before the guard for detail views, and in check 5's overview SVG, which draws `node: unspecified`. F2, F3 and F4 are confirmed by reading. That session fixed none of them before the owner's word below.

## Fixes

On the owner's word on 2026-11-07, "Fix all four", Claude Opus 5.5 fixed each finding.

| ID | Fix |
|---|---|
| F1 | Both skills now say what any view can show apart from what Kubernetes detail views add. Any view can show provider and legend headings, each node's type name, notes on where a resource sits, which start with a word such as `subnet:`, `location:` or `namespace:`, and `node: unspecified` on a Pod placed on no Node. Detail views add property lines, such as `type: ClusterIP` and `ports: 80:8080/TCP`, and reference notes, such as `service:` and `storage class:`. The `DRAFT` lines of a lenient render and the lines on icon rights are named too |
| F2 | Both tests now pin "never show a changed image in their place", "Copying the files unchanged is fine", the `DRAFT` lines, the legend headings and the type name. They also check which part of the rule each example is in |
| F3 | Both tests find the paragraph with an assertion that names it. They check the examples against two named baselines instead of all of them: `subnet:` in `aws-three-tier--overview`, and `type: ClusterIP`, `ports: 80:8080/TCP` and `storage class:` in `aws-three-tier--eks-namespaces` and not in the overview. A change to those two baselines can still fail the test, but the message names the example |
| F4 | Check 3 now says "All 11 IDs" and lists what they are. The two earlier runs' edits also said 10, and their bundles hold the same 11, so they now say so too |

Seven sabotage edits to each skill, 14 in all, each failed its test with a named assertion. They dropped the clause about showing a changed image, the copying sentence, the `DRAFT` sentence or the type name. They moved `node: unspecified` into the detail sentence, changed the paragraph's opening words, or changed `type: ClusterIP` to `type: NodePort`. `src` did not change. The Work plugin's version is now `0.1.0-alpha.1+189d172ffd72`, and two builds gave the same files. The local gate passes 17 lanes. Fable's review of these fixes is the next section.

## Review of the fixes

Date: 2026-11-07 (Asia/Bangkok) | Range: `a4537a7..4ae6bf0` | Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), started at Medium, in a fresh read-only agent | Implementer: Claude Opus 5.5

**Disposition: approved, with three P3 findings and no P1 or P2.** The reviewer judged F1 to F4 resolved from the code and files. It counted the IDs in all six bundles, rebuilt the Work plugin from the clean tree at `4ae6bf0` as `0.1.0-alpha.1+189d172ffd72`, ran both tests and repeated one sabotage edit. Actual CI [run 42375980874](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42375980874) passed at `4ae6bf0`.

| ID | Severity | Where | Finding | Fix direction |
|---|---|---|---|---|
| R1 | P3 | Both tests, the check against the two baselines | It looks for whole drawn lines. `storage class:` is a whole line only because the PVC's note, `storage class: web-storage`, is longer than 20 characters and wraps after the colon. With a shorter storage class name the test fails, although the view draws what the rule says | Check that a drawn line starts with each example |
| R2 | P3 | Both skills, the paragraph that starts "Hand over a bundle" | The legend draws each line kind, such as `traffic` and `storage`, in English, but the paragraph names only its headings. Group boxes carry notes too, and some notes are not about place, such as `security: ALB` in check 5's overview | Name the legend's line kinds, and describe the notes as a resource's or box's memberships, with `security:` as an example |
| R3 | P3 | This record, the end of "The implementer's check of the findings" | "None is fixed, and they wait for the owner" still stands above "Fixes" | Say that none was fixed in that session |

Not checked by the reviewer: a second build, the full gate, the other sabotage edits, the PNGs by eye, and the provider headings beyond `External`.

The implementer confirmed R1 in the `aws-three-tier--eks-namespaces` baseline, where the PVC's lines are `storage class:` and then `web-storage`, and `LABEL_WIDTH` is 20. R2 is confirmed in `draw.py`, which labels each legend line with its kind, and in `graph.py`, which adds notes to group boxes. R3 is confirmed by reading. None was fixed before the owner's word below.

## Fixes after the second review

On the owner's word on 2026-11-07, "Fix all three", Claude Opus 5.5 fixed each finding.

| ID | Fix |
|---|---|
| R1 | Both tests now match each example by the start of a drawn line. A storage class note short enough not to wrap, `storage class: gp3`, passes both |
| R2 | Both skills now name the legend's line kinds, such as `traffic` and `storage`, and describe the notes as what a resource or box belongs to, with `security:` among the examples. Both tests check the two line kinds against the baselines' legends and `security:` against the overview |
| R3 | The end of "The implementer's check of the findings" now says that none was fixed before the owner's word |

Eleven sabotage edits to each skill, 22 in all, each failed its test with a named assertion. They repeat the earlier seven and also drop the provider headings, the legend's line kinds or `security:`, or name a line kind never drawn. `src` did not change. The Work plugin's version is now `0.1.0-alpha.1+5fc47e5a0839`, and two builds gave the same files. The local gate passes 17 lanes. Fable's review of these fixes is the next section.

## Review of the second fixes

Date: 2026-11-07 (Asia/Bangkok) | Range: `4ae6bf0..4977b0e` | Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), started at Medium, in a fresh read-only agent | Implementer: Claude Opus 5.5

**Disposition: approved, with two P3 findings and no P1 or P2.** The reviewer judged R1 to R3 resolved. It checked the paragraph against the renderer again, ran both tests and four sabotage edits of its own, and rebuilt the Work plugin twice as `0.1.0-alpha.1+5fc47e5a0839` with the same files. Actual CI [run 42377049892](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42377049892) passed at `4977b0e`.

| ID | Severity | Where | Finding | Fix direction |
|---|---|---|---|---|
| R4 | P3 | This record, the end of "Fixes" | "Fable has not reviewed these fixes" stands just above "Review of the fixes", as R3's sentence did | Say that the review follows |
| R5 | P3 | `decisions.md`, the header | It says "Updated: 2026-11-05", although D-042 was added and changed on 2026-11-07. This came before the diff | Move the date when a decision changes |

The reviewer judged some omissions not worth adding to a list that says "such as": a Pod's `node:` note that names its Node, the `replicas:` and `labels:` property lines, a fallback node's provider and type line, and the type names on group boxes. Not checked by the reviewer: the full gate, the other 18 sabotage edits, the PNGs by eye, provider headings other than the six in `PROVIDER_LABELS`, and the CI run's outcome.

The implementer confirmed R4 by reading. The same sentence also ends "Fixes after the second review", just above this section. R5 is confirmed in the header and in `git log`. None was fixed when this section was written.

## Fixes after the third review

On the owner's word on 2026-11-07, "Fix both", Claude Opus 5.5 fixed both findings. For R4, the sentence that ended "Fixes" and the same sentence that ended "Fixes after the second review" now say that Fable's review of those fixes is the next section. For R5, the header of `decisions.md` now says 2026-11-07. Only records changed, so the skills, the tests and the Work plugin's version, `0.1.0-alpha.1+5fc47e5a0839`, stay as they were. The docs check passes.
