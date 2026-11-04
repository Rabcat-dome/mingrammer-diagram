# S09 ChatGPT Work Acceptance Check

Target: the separate ChatGPT Work page or mode, not Codex (D-014). Automated checks and rehearsals stay in the [S09 evidence](S09-work-plugin.md), and only what the owner reports below counts as a Work result.

**Status: check 5 passed in Work on 2026-11-04, and checks 2, 3 and 4 have not run. M5 stays open.**

## What the owner runs

Install, from a checkout of `main`, with the commands in the [plugin README](../../../plugins/cloud-architecture-work/README.md#install). Then restart the ChatGPT app, switch to Work mode, open a new chat and select **Cloud Architecture Diagrams**. The S04 plugin stays enabled and unchanged.

The expected version is `0.1.0-alpha.1+03840aacc866`, from the [S11 fixes](S11-gpt-reviews.md#fixes). The results below are for `0.1.0-alpha.1+f242304382f3`, the version before them, so check 5 runs again on this one. Each prompt runs in the same chat unless it says otherwise.

| # | Prompt | What it checks |
|---|---|---|
| 1 | `Use Cloud Architecture Diagrams. Check that its runtime is ready, set it up if it is not, and tell me the plugin version, the runtime state, whether rendering is available and any blockers.` | Install, discovery, approval prompt, setup, version |
| 2 | `Draw an AWS three-tier web application: an Application Load Balancer, two EC2 app servers and an RDS database in one VPC. Show me the picture and give me all six files.` | Rendering, preview, retrieval |
| 3 | `In that diagram, add an S3 bucket that both app servers read from, and draw it again. Keep everything else as it is. Tell me which IDs you kept and added.` | Edit flow, stable IDs, updated source |
| 4 | `Validate this model and tell me what is wrong, without fixing it: {"schema_version":"1.0.0","metadata":{"id":"x","title":"X","environment":"prod","assumptions":[]},"resources":[{"id":"app","name":"App","provider":"aws","service_type":"aws.compute.ec2","taxonomy":"compute.vm"}],"relationships":[{"id":"r1","source_ref":"app","target_ref":"ghost","kind":"traffic"}],"views":[{"id":"v","title":"V","entity_refs":["app"]}]}` | Invalid input: expects `REFERENCE_MISSING` and no image |
| 5 | In Thai, ask for a GKE architecture with a Deployment, Service, Ingress and PVC, with both an overview view and a detail view, and with Thai names on the labels. The session that started this check gives the exact sentence, because repository documents stay English | Kubernetes overview and detail, Thai labels, same IDs in both views |

## Result

Run on 2026-11-04 (Asia/Bangkok) in one chat, with GPT-6.1 Sol / High. The owner reports that the run was in Work, and the host's session record agrees: its originator is `codex_work_desktop`, where a Codex session on this Mac the same day has `Codex Desktop`.

| Check | Result |
|---|---|
| Plugin visible and selectable in Work | Passed. The owner's prompt selected it by its `plugin://` link |
| Version the chat reports | `0.1.0-alpha.1+f242304382f3`, as expected |
| An approval prompt for `setup_runtime`, and what it looked like | None in the session record, where the chat's approval policy is `never`. Whether the app showed one is not yet reported |
| Runtime reaches `ready` | Passed, in under a minute: `RUNTIME_NOT_READY`, then `RUNTIME_INSTALLING`, then `ready` |
| PNG visible in the chat, and how it appeared | Both render results held an image, the answer embedded both, and the owner accepted that answer. How they appeared is not yet reported |
| All six files open from Work | Partly. All six files of both bundles came back through `read_artifact`, after a [retry](#busy-answers). Whether the answer's file links open is not yet reported |
| Edit keeps IDs and returns the updated source | Not run |
| Invalid model gives `REFERENCE_MISSING` and no image | Not run |
| Kubernetes overview and detail both draw, with readable Thai | [Passed](#check-5-in-work) |
| Anything unexpected | [Four `busy` answers](#busy-answers), and the chat calling its own run Codex |

## Check 5 in Work

The local `cloud-architecture-work` plugin validated the GKE model in strict mode and rendered both views with readable Thai labels. The detail view was rendered from the overview bundle's model. Ingress (`app-ingress`), Service (`app-service`), Deployment (`app-deployment`) and PVC (`app-pvc`) kept the same IDs in both views. The two `model.json` files have the same SHA-256 (`11a52f4a43debd030ec31d8abf11cc8fed3de4c4e6e3a1991b08e87301cdc7a7`). The owner then told the chat, translated from Thai: "record that it passed."

Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- Overview `gke-web-storage--overview--4269037e6861b375`
- Detail `gke-web-storage--detail--20c28cf1dcd9775d`

The chat first recorded this as a Codex run with the Work result pending. The owner corrected that, and this page now follows the owner and the session record.

This run has limits as acceptance evidence:

- The chat was not new. An earlier turn had read this repository's records and run its tests, and the repository was its working folder.
- It read `src` while writing the model, so it does not show that the plugin's skill alone is enough.
- The prompt was not the sentence this check planned. It also asked outright to keep the IDs.

### What the Claude session checked on disk

The owner's Claude Code session checked the files and the host's session record the same day. It read the chat's prompts, its messages to the owner, and the tool names and statuses, so this is not a second opinion on what the app showed.

- The installed plugin's files equal the build, and its version is the expected one.
- Both bundles exist with the digest above, both are `complete`, and `diagnostics.json` says `strict`. Its only diagnostics are `VIEW_EXCLUSIONS` warnings, for each view's disclosed exclusions.
- Rendering each view again from the repository at `aefcdbc` gives the same `diagram.svg`, `diagram.png` and `view.json`. The four IDs are in both graphs, and the ReplicaSet is only in the detail view.
- These are the only bundles in the folder, so no AWS bundle from checks 2 and 3 exists on this Mac. The session record shows no such prompt either.

## Busy answers

The chat read 12 files at once, all six of both bundles. Eight came back and four answered `busy` with `TOO_MANY_CALLS`, and it read those four again one at a time, which worked. `MAX_CALLS` is 8 in `protocol.py`, and no render was running. Sending 12 reads at once to the installed server again gave 4, 4 and 3 refusals in three tries, while 6 and 8 reads gave none.

At that version the skill's `busy` row said "Another render is running", which was the wrong cause although its remedy worked, and no test covered `TOO_MANY_CALLS`. [S11](S11-gpt-reviews.md#fixes) fixed both.

## What is left

- All five prompts in Work, on the expected version. Prompts 2, 3 and 4 have never run, and prompt 1 did not run as its own prompt, though this chat went through each of its steps.
- A new chat, opened outside this repository, so that the plugin's skill is all it has to go on.
- The owner reports whether the app showed an approval prompt, how the PNG appeared and whether the file links open.

A change to the plugin's content changes its version, so a fix after that run needs its own run.
