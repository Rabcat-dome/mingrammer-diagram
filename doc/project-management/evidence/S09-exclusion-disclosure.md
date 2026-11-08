# Naming What a View Leaves Out

Date: 2026-11-08 (Asia/Bangkok) | Decision: D-046 | Implementer: Claude Opus 5.5 | Work plugin: `0.1.0-alpha.1+594b3683feb0` to `0.1.0-alpha.1+f6b9f6134e60` | Core: `0.5.0a3`, unchanged

## What happened

FR-025 asks a view that selects part of the model to disclose the IDs it leaves out, and both skills said "Disclose the IDs listed for every view in `view_exclusions`". In two runs in actual Work, the chat did not name them:

- On 2026-11-07, under D-043, the GKE chat said that the overview leaves the ReplicaSet and PV to the detail view. It did not name the three relationships the overview also leaves out, or the Deployment to Pod line the detail view leaves out. See [the image rule in Work](S09-Work-validation.md#the-image-rule-in-work).
- On 2026-11-08, under D-045, the AWS chat said that the overview shows the zones as subnet labels. It did not name `az-a` and `az-b` as left out. See [the missing field in Work](S09-Work-validation.md#the-missing-field-in-work).

## Causes

- The IDs reach a chat only inside `result.view_exclusions`, as bare IDs after the rest of the result. The `VIEW_EXCLUSIONS` warning names none of them and says only "see view_exclusions".
- The skills said to disclose the IDs without saying how. A chat could give a reason in place of the items, or name the boxes and skip the lines.

## Changes

- The Work server adds `disclose` to a successful `validate_model` or `render_model` result whenever a view leaves something out, placed before `result`. It holds an instruction to tell the user every item by its name and its ID, relationships included, without summarizing, grouping or leaving any out, and each partial view's items in the core's order. An entity is its `id` and `name`. A relationship is its `id`, its two ends as `source -> target` names, and its `label` when it has one. `validate_model` lists every partial view, and `render_model` lists only the view it drew. A failed call, and a view that leaves nothing out, carry no `disclose`. The names come from the model the call sent, or from the bundle's `model.json` when the call passed `bundle_id`.
- Both tools' descriptions say that `disclose` lists each item by name and ID for the user.
- Each skill's Report step now says to tell the user every item, view by view, by its name and its ID, relationships included, with an example. It says not to summarize, group or leave out any, and never to put a reason, such as being shown another way, in place of naming them. The Work skill's Validate step says that `disclose` names them. The Claude plugin's command line prints no `disclose`, so its skill takes the IDs from `view_exclusions` and the names from the model.
- `src` does not change. The core stays `0.5.0a3`, `uv.lock` and the runtime stay as they are, and [the core reproduction proof](S10-core-reproduction-proof.json) still describes the source. This design is the implementer's choice; making the core's warning name the IDs would have needed a new core version.

## Checks

- Five new tests. The `package-contract` lane has `test_a_partial_view_names_what_it_leaves_out`, `test_a_whole_view_or_a_failure_discloses_nothing`, `test_a_render_discloses_only_the_view_it_drew` and `test_skill_names_each_item_a_view_leaves_out`. The `claude-plugin` lane has `test_skill_names_each_id_a_view_leaves_out`. The server's items are checked against names built from the model by the test itself, including a relationship with and without a label, and a render from a `bundle_id`.
- Each of 15 sabotage edits failed a named test: dropping `disclose` from either tool, listing every view on a render, listing a view that leaves nothing out, reducing a relationship or an entity to its ID, dropping a label, weakening the instruction, removing either tool's description, and restoring the old rule or removing a clause in either skill.
- The Work plugin builds as `0.1.0-alpha.1+f6b9f6134e60` twice, with the same ZIP, SHA-256 `19fee19fe46947b555952c7544eb62a5cc7a40c89c3e70c6e2174ff9b7c8abf0`, and the lock stays `d8d8163c50b1026c`.
- The local gate passes 17 lanes with 1,962 tests and none skipped, on the uncommitted change over `2938ad2`.

Not done when this was written: an independent review, an install, and a run in Work.
