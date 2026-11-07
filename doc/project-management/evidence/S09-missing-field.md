# A Missing Field in Work Chats' First Model

Date: 2026-11-07 (Asia/Bangkok) | Decision: D-044 | Implementer: Claude Opus 5.5 | Core: `0.5.0a2` to `0.5.0a3`

## What happened

In six Work sessions from 2026-11-05 to 2026-11-07, the first model a chat wrote failed with `SCHEMA_FIELD_INVALID` at `/metadata/environment`. In every one, `metadata` held only `id`, `title` and `assumptions`. The field is required, and any string of 1 to 256 characters without control characters passes. Each chat then read the full schema, about 22 KB, and added the field. The six are the session records under `~/.codex/sessions/` with originator `codex_work_desktop`, started at 10:28, 10:28, 10:30 and 14:25 on 2026-11-05 and at 16:21 and 22:47 on 2026-11-07, Asia/Bangkok time. They are outside the repository, and its own records name only some of them. The latest case is in [the image rule in Work](S09-Work-validation.md#the-image-rule-in-work).

## Causes

- Neither skill named `environment`. The Claude skill named `metadata.assumptions` and `metadata.id`, and the Work skill named only `metadata.assumptions`.
- The model guide showed the field only in its example, `"environment": "production"`, and did not say that it is required.
- The core gave a missing field the same code, message and remedy as an unknown or mistyped one. The remedy said: "Use schema discovery; remove unknown fields and correct field types/bounds."

`environment` is also drawn, because each view's title line reads "title (environment)". The image rule did not list it among the text drawn as written.

## Changes

- Each skill's step for writing the model now says that `metadata` needs `id`, `title` and `environment`, a short label that each view's title shows in brackets, written in the labels' language. Each image rule lists `environment` among the text drawn as written.
- The guide has a **Metadata** line. It says that the three fields are required and what `environment` holds, and that leaving it out fails with `SCHEMA_FIELD_MISSING`.
- The core reports a field that the schema requires and the model leaves out with `SCHEMA_FIELD_MISSING`, the message "A required field is missing." and the remedy "Add the field at this path; schema discovery lists each object's required fields." Every other schema failure keeps `SCHEMA_FIELD_INVALID`. [The contract](../../design/core-contract.md) says so. The core moves to `0.5.0a3`, as D-034 moved it for its new code.

## Checks

- Four new tests. The contract lane has `test_a_missing_field_has_its_own_code_and_remedy`. The Work plugin lane has `test_a_missing_field_tells_the_chat_to_add_it` and `test_skill_names_the_required_metadata`. The Claude plugin lane has `test_skill_and_guide_name_the_required_metadata`. The skill tests read the schema's required fields, and check the brackets against the title of the `aws-three-tier--overview` baseline.
- Ten sabotage edits each failed a named test, with twelve failures in all, because each of the two core edits fails in two lanes.
- At `2f60661`, the local gate passed 16 of 17 lanes. `release-audit` failed only because the [core reproduction proof](S10-core-reproduction-proof.json) described the old source. `scripts/reproduce_core.py` clones a pushed commit, so the proof followed in the next commit, as it did after D-034.
- The core reproduces from a new clone at `2f60661`. The clean runtime builds the wheel with SHA-256 `81bc0cedaf55f70ec5ef6e63ab81889f93d5d047a3172a280294904b8c51bccb`, the same as the local build, and all 26 reference views match their baselines by both routes. With that proof, the local gate passes 17 lanes.
- The Work plugin builds as `0.1.0-alpha.1+594b3683feb0` twice, with the same ZIP. `uv.lock` changed, so an install must build the runtime again.

Not done when this was written: an independent review, an install, and a Work run of this version.

## Review

Date: 2026-11-07 (Asia/Bangkok) | Range: `cdee5f0..b478a5d` | Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), started at High for schema work, in a fresh read-only agent | Implementer: Claude Opus 5.5, so reviewer and implementer share a vendor

**Disposition: approved, with three P3 findings in the records and no P1 or P2.** The reviewer probed the core with missing fields at eight paths, including nested models, list items and Kubernetes context, and each gave `SCHEMA_FIELD_MISSING` at the right path. The schema has no tagged unions, so every absent required field reaches the core as Pydantic's `missing`. A null, an empty string, a wrong value, an extra key and a top-level list still give `SCHEMA_FIELD_INVALID`, lenient mode gives the same codes, and the limit of 100 errors holds. No table or client enumerates the codes, and the Work server's `code` is the first error's. It found the version move complete, confirmed that `_title` puts the environment in brackets on every view, rebuilt the wheel with the proof's SHA-256, recomputed the proof's source digest and the plugin's content digest, ran the contract, release-audit and new tests, and repeated four sabotage edits. CI [run 42392263577](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42392263577) passed at `b478a5d`, and [run 42391750680](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42391750680) at `2f60661` failed only `release-audit`.

| ID | Severity | Where | Finding | Fix direction |
|---|---|---|---|---|
| F1 | P3 | This record, "Causes" | It says both skills name `metadata.assumptions` and `metadata.id`, but the Work skill names only `metadata.assumptions` | Say which skill names which |
| F2 | P3 | This record, "What happened" | The six sessions are counted from session records outside the repository, and the repository's own records name fewer | Say where the six are recorded |
| F3 | P3 | `HANDOFF.md`, item 9 | "Core is `0.5.0a3`, so the Work plugin becomes" reads as if the version alone changed the digest | Use "and" |

Not checked by the reviewer: the six-session count, the 10 sabotage edits, a full run of the gate or of the reproduction, and whether a long Thai title can wrap inside the brackets.

The implementer confirmed F1 in both skills at `cdee5f0`. For F2, the six session records under `~/.codex/sessions/` all have originator `codex_work_desktop`, and one more failure on 2026-11-05 came from a `codex_exec` test script, so it is not counted. F3 is confirmed by reading. None was fixed when this section was written.

## Fixes after the review

On the owner's word on 2026-11-07, "Fix all three", Claude Opus 5.5 fixed each finding. For F1, "Causes" says which skill named which field. For F2, "What happened" names the six session records, their originator and their start times, and says they are outside the repository. For F3, the handoff says "and" in place of "so". Only records changed, so the core, the skills, the tests and the Work plugin's version stay as they were.
