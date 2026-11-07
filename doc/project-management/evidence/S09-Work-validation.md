# S09 ChatGPT Work Acceptance Check

Target: the separate ChatGPT Work page or mode, not Codex (D-014). Automated checks and rehearsals stay in the [S09 evidence](S09-work-plugin.md), and only what the owner reports below counts as a Work result.

**Status: all five checks pass in Work on the final version, `0.1.0-alpha.1+88ce2c0cd0dc`, on the first Mac (D-032), after passing on `0.1.0-alpha.1+d27ef23f6f94` on both Macs (D-027, D-029). M5 closed on 2026-11-05 under D-028.** **After the release, the five prompts and a sixth pass on `0.1.0-alpha.1+80cadf16a121` on the first Mac (D-042), as [After the release](#after-the-release) records.** **On `0.1.0-alpha.1+5fc47e5a0839`, prompt 1 and check 5 pass (D-043), and the chat shows the plugin's images unchanged, as [The image rule in Work](#the-image-rule-in-work) records.**

## What the owner runs

Install, from a checkout of `main`, with the commands in the [plugin README](../../../plugins/cloud-architecture-work/README.md#install). Then restart the ChatGPT app, switch to Work mode, open a new chat and select **Cloud Architecture Diagrams**. The S04 plugin stays enabled and unchanged.

The final version is `0.1.0-alpha.1+88ce2c0cd0dc`, which adds [D-030's detail lines](M6-p0-gaps.md#fr-018) to the [S11 fixes](S11-gpt-reviews.md#fixes) and the fix for the [second run's fault](#second-run). A change to the plugin's content changes its version, so a fix after this needs its own run. Each prompt runs in the same chat unless it says otherwise.

| # | Prompt | What it checks |
|---|---|---|
| 1 | `Use Cloud Architecture Diagrams. Check that its runtime is ready, set it up if it is not, and tell me the plugin version, the runtime state, whether rendering is available and any blockers.` | Install, discovery, approval prompt, setup, version |
| 2 | `Draw an AWS three-tier web application: an Application Load Balancer, two EC2 app servers and an RDS database in one VPC. Show me the picture and give me all six files.` | Rendering, preview, retrieval |
| 3 | `In that diagram, add an S3 bucket that both app servers read from, and draw it again. Keep everything else as it is. Tell me which IDs you kept and added.` | Edit flow, stable IDs, updated source |
| 4 | `Validate this model and tell me what is wrong, without fixing it: {"schema_version":"1.0.0","metadata":{"id":"x","title":"X","environment":"prod","assumptions":[]},"resources":[{"id":"app","name":"App","provider":"aws","service_type":"aws.compute.ec2","taxonomy":"compute.vm"}],"relationships":[{"id":"r1","source_ref":"app","target_ref":"ghost","kind":"traffic"}],"views":[{"id":"v","title":"V","entity_refs":["app"]}]}` | Invalid input: expects `REFERENCE_MISSING` and no image |
| 5 | Do not paste this row. Paste a Thai sentence asking for a GKE architecture with a Deployment, Service, Ingress and PVC, with both an overview view and a detail view, and with Thai names on the labels. The session that started this check gives the exact sentence, because repository documents stay English. Pasting this row made a chat draft a sentence and call no tool | Kubernetes overview and detail, Thai labels, same IDs in both views |

## The image rule in Work

Run on 2026-11-07 (Asia/Bangkok) on `0.1.0-alpha.1+5fc47e5a0839`, built from `9388fee`, on the first Mac, in one new Work chat outside this repository, after the ChatGPT app was restarted. The runtime was `ready`, with a passing render probe under this version, so `setup_runtime` did not run. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. Prompt 1 is the table's. The second prompt is check 5's Thai sentence, the same as in [After the release](#after-the-release). Prompts 2, 3, 4 and 6 did not run on this version.

The owner passed the run (D-043). The owner did not report separately on how the images appeared or whether the files opened. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a2`, with the runtime `ready`, rendering available and no blockers. It rendered the plugin's sample and copied its six files unchanged |
| 5. GKE with Thai labels | Passed. The chat showed the plugin's own images. It copied each bundle's six files into its folder with `cp`, and checked each copy's SHA-256 against the plugin's. All 12 copies match the bundles byte for byte, and no command edited, translated, redrew or converted an image. It told the user, in Thai, that the names, titles and arrow labels are Thai, and that type names, text on icons and values the plugin adds stay in English. Both views share one `model.json`, SHA-256 `04a3cad5892ada5ec4d0a001fd72cf3afbf209f81ed1b3e7940c21c9905b4368`, and every name, title and relationship label in it is Thai |

Other things seen in the session record and the images:

- English appears where the skill says: `Google Cloud`, each type name, `node: unspecified` in both views, and `type: ClusterIP` and `replicas: 1` only in the detail view.
- The first model failed with `SCHEMA_FIELD_INVALID` on `metadata.environment`, as check 2 did in earlier runs. The chat read the schema and corrected it.
- The chat said that the overview leaves the ReplicaSet and PV to the detail view. It did not list the three relationships the overview also leaves out, or the Deployment to Pod line the detail view leaves out, although the skill asks it to disclose every view's exclusions.
- The app's memory listed an earlier GKE chat and its model `gke-web-with-pvc`, but the chat wrote a new model, `gke-app-th`, and did not read the earlier one.
- As before, the chat read the runtime skill of the old S04 plugin in prompt 1, and searched the web for GKE and Kubernetes documents.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering both views again from `main` at `f22b75d` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`: GKE `gke-app-th--overview--cbde6c612099cbcc` and `gke-app-th--detail--e1461b068491d8ce`, and the sample `demo--overview--4ee9a80323d3e908`. This run covers one Mac and one model, under full access, with a runtime that was already set up, and two of the six prompts.

## After the release

Run on 2026-11-07 (Asia/Bangkok) on `0.1.0-alpha.1+80cadf16a121`, built from `5598159`, on the first Mac, in one new Work chat outside this repository. The runtime stayed as its setup that day left it, `ready` with a passing render probe, so `setup_runtime` did not run. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. Prompts 1 to 4 are the table's. Prompt 5 was a Thai sentence, translated here: "Use Cloud Architecture Diagrams to draw an application architecture on GKE with a Deployment, Service, Ingress and PVC. I want both an overview and a detail view, with Thai names on every label." A sixth prompt, for the AWS types of S12 and S13, asked for a CloudFront distribution protected by a CloudFront web ACL, in front of an API Gateway HTTP API, with a Lambda function behind it that reads and writes a DynamoDB table, and a Cognito user pool for sign-in.

The owner passed all six and asked for the skill change below (D-042). The owner did not report separately on how the images appeared or whether the files opened. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version and core `0.5.0a2`, with the runtime `ready`, rendering available and no blockers |
| 2. AWS drawing | Passed. The first model failed with `SCHEMA_FIELD_INVALID` on its `environment`, and the chat read the schema and corrected it, as in the earlier run. Strict, no warnings, and all six files |
| 3. Edit | Passed. All 11 IDs stayed unchanged: the model's own, the view, the VPC, four resources and four relationships. `s3`, `app-1-to-s3` and `app-2-to-s3` were added. The chat rendered twice, the second time only to name each read line's server in its label |
| 4. Invalid model | Passed. `REFERENCE_MISSING` at `/relationships/0/target_ref`, and no bundle |
| 5. GKE with Thai labels | Passed on the plugin's bundles, which the chat did not show, as the next paragraph says. Both views share one `model.json`, SHA-256 `e3477a3831a8d43921e396b33aaa2de8daf11a1b701b0616fb53be694ba75eca`, and the Thai names and labels draw. The detail view shows the D-030 lines and follows S14's rule: the Ingress keeps its `service:` note, because its line to the Service is `dependency`, not `traffic`, and the PVC's storage class note hides, because a `storage` line from the PVC draws it |
| 6. AWS serverless | Passed. Strict, no warnings, with `aws.network.cloudfront`, `aws.security.waf_cloudfront`, `aws.integration.api_gateway_v2`, `aws.compute.lambda`, `aws.database.dynamodb` and `aws.identity.cognito_user_pool`. This is the first live session to use S13's types |

For check 5, the chat did not show the plugin's images. It judged that the English text the renderer adds broke the request for Thai on every label, so it changed `diagram.svg` itself. It translated the provider headings, deleted each node's type name, and rewrote the property lines in Thai, losing `TCP` and `app=web`. Then it drew the PNG again with `rsvg-convert`, outside the sandbox and the font check. It linked the plugin's six files beside them as a ZIP. The skills of both plugins now forbid this, and say which text stays in English (D-042).

Other things seen in the session record:

- The chat started check 5's model from the GKE chat of 2026-11-05, through the app's memory and that chat's bundle, so that model was not written fresh.
- The chat read the plugin's `src` and server code in prompts 1, 3 and 5, and the runtime skill of the old S04 plugin, which stays installed.
- In prompt 3, the lines to S3 start short of the EC2 icons, which is S08's open P3-2.
- Prompt 6 also searched the web for AWS documents.
- No `busy` answer and no `RUNTIME_INSTALLING` appeared.

Rendering the five final bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web-app--overview--16f6e9c6c9645a75`, and after the edit `aws-three-tier-web-app--overview--b0d81fdd84d860f6`
- GKE `gke-web-with-pvc--overview--148c236ad466e6fe` and `gke-web-with-pvc--detail--77312d4c8ee9383f`
- AWS serverless `aws-serverless-http-api--overview--61cf1e2cf18e3e56`

Claude Fable 5.1 [approved the skill change and this record](S09-fable-image-rule-review.md) with four P3 findings, and they are [fixed](S09-fable-image-rule-review.md#fixes). Its [review of the fixes](S09-fable-image-rule-review.md#review-of-the-fixes) left three P3 findings, which are [fixed too](S09-fable-image-rule-review.md#fixes-after-the-second-review), and [a third review](S09-fable-image-rule-review.md#review-of-the-second-fixes) approved those fixes with two P3 findings in the records, which are [fixed too](S09-fable-image-rule-review.md#fixes-after-the-third-review). The change and its fixes make the Work plugin `0.1.0-alpha.1+5fc47e5a0839`, which is installed on the first Mac from `9388fee` and passes [the run of the image rule](#the-image-rule-in-work) (D-043). This run covers one Mac and one model, under full access, with a runtime that was already set up.

## Final version

Run on 2026-11-05 on `0.1.0-alpha.1+88ce2c0cd0dc`, on the first Mac, in one new Work chat outside this repository, after removing the runtime. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High, with approval policy `never` and `danger-full-access`. The owner passed all five. The rest was checked from the session record and the files.

| Check | Result |
|---|---|
| 1. Install and runtime | Passed. The chat reports this version, and setup reaches `ready` from `RUNTIME_NOT_READY` |
| 2. AWS drawing | Passed. Strict, no warnings, and all six files |
| 3. Edit | Passed. All 11 IDs stayed: the model's own, the view, the VPC, four resources and four relationships. `s3-bucket`, `app-1-s3` and `app-2-s3` were added, and no existing resource or relationship changed |
| 4. Invalid model | Passed. `REFERENCE_MISSING`, and no bundle |
| 5. GKE with Thai labels | Passed, at the second attempt. The first paste was this page's own table row, so the chat drafted a sentence and called no tool, and its row now says not to. The drafted sentence then ran. Both views share one model, and the detail view shows D-030's new `type: ClusterIP` line, with no such line in the overview |

Rendering all four bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. No `busy` answer and no `RUNTIME_INSTALLING` appeared. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web--overview--aa1d14ba097e636c`, and after the edit `aws-three-tier-web--overview--dc0cb58ed135873a`
- GKE `gke-thai-application--overview--4ddc97f3f718c736` and `gke-thai-application--detail--6cd7d16ed1f478fa`

The model in this run declared a Service type and no replicas or ports, so only `type:` was seen in Work. Tests and the owner's [reference images](M6-p0-gaps.md#fr-018) cover the other lines. The second Mac did not run this version (D-032).

## Result

This is the run on `0.1.0-alpha.1+d27ef23f6f94`, which closed M5.

Run on 2026-11-05 (Asia/Bangkok) in one new Work chat, with GPT-6.1 Sol / High, in a folder outside this repository, after removing the runtime. The session record has originator `codex_work_desktop`. "Owner" marks what only the owner could see, and the rest was checked from the session record and the files.

| Check | Result |
|---|---|
| Plugin visible and selectable in Work | Passed. The owner's prompts selected it by its `plugin://` link |
| Version the chat reports | `0.1.0-alpha.1+d27ef23f6f94`, as expected |
| An approval prompt for `setup_runtime`, and what it looked like | None. Owner: the chat had full access, so the app did not ask. The session record has approval policy `never` and `danger-full-access`. How the app asks under a stricter setting is unverified |
| Runtime reaches `ready` | Passed, in about 20 seconds from a removed runtime with a warm uv cache: `RUNTIME_NOT_READY`, `setup_runtime`, then `ready`. The marker names this version |
| PNG visible in the chat, and how it appeared | Passed. Owner: it appears as a normal image and can be downloaded |
| All six files open from Work | Passed. Owner: they open. Each bundle holds all six. The chat copied them to its own `outputs` folder by shell, and read `model.json` through `read_artifact` for the edit |
| Edit keeps IDs and returns the updated source | Passed. All 11 IDs stayed: the model's own, the view, the VPC, four resources and four relationships. `s3`, `app-1-to-s3` and `app-2-to-s3` were added, and nothing else in the model changed. The new bundle holds the updated source |
| Invalid model gives `REFERENCE_MISSING` and no image | Passed, at `/relationships/0/target_ref`, and no bundle was made |
| Kubernetes overview and detail both draw, with readable Thai | Passed. Both views share one model, so their IDs agree. Owner: passed |
| Anything unexpected | The chat's first AWS model failed with two `SCHEMA_FIELD_INVALID`, and it read the schema and corrected the model, which is the flow the skill describes. No `busy` answer, and no `RUNTIME_INSTALLING` |

Rendering all four bundles again from `main` gives the same `diagram.svg`, `diagram.png` and `view.json`. Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- AWS `aws-three-tier-web-app--overview--a6fa5cb47c9027c8`, and after the edit `aws-three-tier-web-app--overview--3e6416cdcb809f60`
- GKE `gke-web-app-th--overview--35a48b517c883c69` and `gke-web-app-th--detail--11eaebee4341d42f`

Four more Work chats ran at the same time, each with one of prompts 2 to 5 and the same version. They drew their own bundles, and none of the five chats saw `RUNTIME_INSTALLING`, which is what the second run's fault would have shown.

This result has limits:

- One Mac and one model. A second machine, a Python download and the system's Documents prompt stay for M6.
- The main chat read the plugin's skill and no `src`. It also read the runtime skill of the old S04 plugin, which stays installed, so this is not a run with this plugin alone.
- The chats had full access, so nothing here shows how the app asks under a stricter setting.

## Earlier runs

These ran on earlier versions, and are the history of how this result came about.

### First run

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

### Check 5 in Work

The local `cloud-architecture-work` plugin validated the GKE model in strict mode and rendered both views with readable Thai labels. The detail view was rendered from the overview bundle's model. Ingress (`app-ingress`), Service (`app-service`), Deployment (`app-deployment`) and PVC (`app-pvc`) kept the same IDs in both views. The two `model.json` files have the same SHA-256 (`11a52f4a43debd030ec31d8abf11cc8fed3de4c4e6e3a1991b08e87301cdc7a7`). The owner then told the chat, translated from Thai: "record that it passed."

Bundles under `~/Documents/CloudArchitectureDiagrams/work/`:

- Overview `gke-web-storage--overview--4269037e6861b375`
- Detail `gke-web-storage--detail--20c28cf1dcd9775d`

The chat first recorded this as a Codex run with the Work result pending. The owner corrected that, and this page now follows the owner and the session record.

This run has limits as acceptance evidence:

- The chat was not new. An earlier turn had read this repository's records and run its tests, and the repository was its working folder.
- It read `src` while writing the model, so it does not show that the plugin's skill alone is enough.
- The prompt was not the sentence this check planned. It also asked outright to keep the IDs.

#### What the Claude session checked on disk

The owner's Claude Code session checked the files and the host's session record the same day. It read the chat's prompts, its messages to the owner, and the tool names and statuses, so this is not a second opinion on what the app showed.

- The installed plugin's files equal the build, and its version is the expected one.
- Both bundles exist with the digest above, both are `complete`, and `diagnostics.json` says `strict`. Its only diagnostics are `VIEW_EXCLUSIONS` warnings, for each view's disclosed exclusions.
- Rendering each view again from the repository at `aefcdbc` gives the same `diagram.svg`, `diagram.png` and `view.json`. The four IDs are in both graphs, and the ReplicaSet is only in the detail view.
- These are the only bundles in the folder, so no AWS bundle from checks 2 and 3 exists on this Mac. The session record shows no such prompt either.

### Busy answers

The chat read 12 files at once, all six of both bundles. Eight came back and four answered `busy` with `TOO_MANY_CALLS`, and it read those four again one at a time, which worked. `MAX_CALLS` is 8 in `protocol.py`, and no render was running. Sending 12 reads at once to the installed server again gave 4, 4 and 3 refusals in three tries, while 6 and 8 reads gave none.

At that version the skill's `busy` row said "Another render is running", which was the wrong cause although its remedy worked, and no test covered `TOO_MANY_CALLS`. [S11](S11-gpt-reviews.md#fixes) fixed both.

### Second run

Run on 2026-11-05 on `0.1.0-alpha.1+2c3c9ea4f01c`, in a new Work chat. The session record has `codex_work_desktop` and GPT-6.1 Sol / High. The chat ran prompt 5's sentence as written, with the plugin selected, and no other prompt. The owner reported that the test was done, and has not yet said what the app showed or whether this run passes.

The Claude session checked these from the files and the session record:

- Both views validate in strict mode and draw. Both `model.json` files have the digest beginning `7be07b30`, so the IDs are the same in both views. Rendering each view again from `main` at `d5007d4` gives the same `diagram.svg`, `diagram.png` and `view.json`.
- The runtime was already `ready`, so no setup ran, and this run says nothing about an approval prompt.
- The chat read the plugin's skill, model guide and Kubernetes example. It did not read `src`, so this run supports the skill being enough, which the first could not. Its working folder was still this repository, and it ran `git status` and looked for `AGENTS.md` there.
- It read no file through `read_artifact`, and its answer embedded both images and linked all six files.

**A fault this run found.** One of five `search_catalog` calls sent at once answered `runtime_unavailable` with `RUNTIME_INSTALLING`, though the runtime was ready and no setup was running. The chat retried, and that worked. `_setup_locked_elsewhere` tests for a running setup by taking the setup lock exclusively without waiting, so two calls testing at once collide, and one reads the other as a setup. On the installed server with its ready runtime, 21 of 100 calls sent in fives gave this answer. The Claude session ranked it P2, because ordinary use reaches it and it states something false, though no data was at risk and waiting cleared it. No test covered readiness under parallel calls, and no reviewer found it.

The readiness test now takes the lock shared, which only a setup's exclusive lock can refuse, and a setup waits up to a second for a test to finish before it reports that another setup holds the lock. Three tests cover this, one of them sending the same parallel calls to the real server, and all 6 sabotage changes fail one of them. Actual CI [run 41958019512](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41958019512) passed 17 lanes and 1,569 tests at `b0a8b4d`. Under D-021, Claude Fable 5.1 / Medium [approved it](S11-fable-lock-review.md) in a fresh agent, and found no way to run two setups at once or to report a ready runtime as installing, with threads or with several processes. Two P3 findings stay open: `remove` deletes the lock file without taking the lock, which predates this fix, and one half of a new test goes through a private helper.
