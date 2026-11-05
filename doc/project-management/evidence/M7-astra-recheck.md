# M7 bounded independent recheck

Reviewed 2026-11-05 on `codex/m7-close`, at **`d0b34550e186339542a331bf178b21aff2fd5f8e`**, against **`8f9c246d31c508be6cf53ebc22b4527a6d8e0a68`**. Scope: `plugins/cloud-architecture-diagrams`, `tests/test_claude_plugin.py`, and `doc/project-management`. I read `doc/project-management/evidence/M7-astra-review.md` first. Core code was consulted only to check the guide's two stated exceptions. The other worktree was not inspected or changed.

**Approved for closing M7 for acceptance copy `ea6c802ec4d3ad1cbb669d0f56ebdb48eb24f3e0`, under D-035's one-Mac limit.** F1's substantive acceptance gap is closed. No new P1 or P2 issue was found in the scoped changes. Two minor record discrepancies are detailed below; neither prevents identifying the accepted package or establishing its installed-session workflow. This is review approval, not an owner closure decision or a public-release approval.

Reviewer identity: my supplied instructions identify me as **Codex, based on GPT-6**. The exact model variant and reasoning-effort setting are not exposed to me. I cannot independently assert that this recheck is `gpt-6-astra` / High merely from the requested report name or the earlier review's recorded launcher.

All new scripts, input models, text-only log extracts, test copies, private runtimes, and generated bundles are under astra-m7-recheck-work. No new Claude session was needed or run. For the permission-documentation question, I independently parsed the existing tool inputs/results rather than presenting an old permission observation as a new head session.

## Disposition of the earlier findings

“Fixed” includes the explicitly offered documentation/recovery remedies; it does not mean an unsupported invocation route now works. Inputs below are independently constructed probes or independently computed evidence checks. The concrete inputs and complete textual results are in probe-summary.json, with individual `*.input.json`, `*.stdout`, and `*.stderr` files alongside it.

| ID | Status | Location at this head | Counterexample/input and observation |
|---|---|---|---|
| **F1, formerly P2** | **Fixed** | `doc/project-management/evidence/M7-claude-plugin.md:186` | My fresh `recheck-d036` model contains all five D-036 type IDs, including separate ECS service and Fargate resources hosted by its ECS cluster. Through the actual installed wrapper, strict validation and rendering both exit **0**, `draft: false`, no diagnostics. Catalog is `2026.11.1`, with **53 AWS-filtered records**. The three final session logs identify this installed copy and contain successful strict renders. See the identity and log audit below. |
| **F3, P3** | **Fixed** | `plugins/cloud-architecture-diagrams/README.md:52` | The counterexample is `"<plugin>/bin/cloud-diagrams" capabilities > /dev/null`. My independent tool-ID/result join of `reports/astra-m7-work/06-dev-null.jsonl` finds one admitted Bash call, no denial, and a successful result. The older real-config edit also contains admitted `ls -la` and `find architecture -type f \| head -50`. The current README explicitly acknowledges `/dev/null`, safe read-only commands, host decisions, and user permissions, and dates the measured behavior to CLI 2.1.309. The skill allow rule did not change in this diff. No new permission session was run; this fixes the documentation claim, not a newly measured universal permission contract. |
| **F4, P3** | **Fixed** | `doc/project-management/evidence/M7-permission-requests.json:7` and `:108`; `M7-claude-plugin.md:172` | I sent permission-only requests for absolute outside-project `mkdir`, relative `../stand-in-outside/marker`, and a project symlink escaping to that directory. The historical server allows all three, matching the corrected historical method statement. The final server denies all three and allows `mkdir inside-marker`, matching the final method statement. No mkdir command was executed. All six recorded request streams contain no mkdir request; the old **2/6/5** and final **3/1/2** request counts stand. |
| **F5, P3** | **Partly fixed** | `doc/project-management/evidence/M7-claude-plugin.md:125`, `:180`, `:224`; `doc/project-management/milestones.md:120`, `:124` | The four specifically identified errors are corrected: my log join yields **6+4+6=16** historical wrapper executions, plus two denied compound attempts; unknown `aws.compute.not_a_service` exits **2** with `CATALOG_TYPE_UNKNOWN`; `taxonomy: made.up` in lenient mode exits **2** with `CATALOG_TAXONOMY_UNKNOWN`; rendering succeeds; the earlier P2 is now described as fixed. However, the current milestone summary still says the three earlier P3s “stay open,” despite the new C1/C2/C3 dispositions and successful probes. See the remaining P3 below. |
| **F6, P3** | **Fixed** | `plugins/cloud-architecture-diagrams/skills/architecture-model/references/model-guide.md:172`, `:179` | My on-premises model links an `IngressController` in `ns-a` to a `ConfigMap` in `ns-b`: strict **0**, no diagnostics. Changing only the source kind/type to `Ingress` produces **2**, `K8S_RELATIONSHIP_CROSS_SCOPE`. My Node with `deployment_context: ["pool"]` validates with **0**, no diagnostics; replacing it with a namespaced Pod gives **2**, `K8S_SCHEDULING_CONTEXT_INVALID`. Both corrected exceptions match the core. |
| **C1, P3** | **Fixed** | `tests/test_claude_plugin.py:618` | `HOME=relative`, empty `XDG_DATA_HOME`, and `capabilities` gives **3**, empty stdout, the absolute-path explanation, and no files in my empty project. I also mutated only pytest's disposable wrapper copy from the absolute-HOME pattern `/*)` to `?*)`. The new regression test **fails at line 628** on that mutant. Thus it detects the old unguarded-relative-HOME defect; the unmodified suite passes. |
| **C2, P3** | **Fixed by a recovery hint** | `plugins/cloud-architecture-diagrams/bin/cloud-diagrams:50`; `tests/test_claude_plugin.py:632` | In my private runtime only, I removed `site-packages/pydantic` but retained its dist-info. Two subsequent `capabilities` calls still exit **3** with `ModuleNotFoundError`, but both now name the exact private venv to remove and say to retry. Removing only that named scratch venv and retrying gives **0**. Automatic self-repair is not claimed. |
| **C3, P3** | **Fixed by documenting the limitation** | `plugins/cloud-architecture-diagrams/README.md:54`; wrapper `:9`; `tests/test_claude_plugin.py:648` | A new external symlink to the wrapper, under my scratch `external/bin/`, still exits **3**, empty stdout. In this nested scratch case uv discovers the enclosing project but the derived `src` is wrong, giving `ModuleNotFoundError: cloud_architecture_diagrams`. The README now says to use the real path and explicitly identifies the unsupported symlink route; the regression test pins exit 3. This is not a symlink-resolution implementation fix. |

**F2:** The records state its status fairly: `M7-claude-plugin.md:209` explicitly leaves the manifest/P-019 question for the owner and does not claim it is fixed. No additional F2 disposition is made here.

## Installed identity and final-session evidence

The local installed-plugin registry gives:

- Path: `~/.claude/plugins/cache/mingrammer-local/cloud-architecture-diagrams/ea6c802ec4d3`.
- Full commit: **`ea6c802ec4d3ad1cbb669d0f56ebdb48eb24f3e0`**.
- Registry version: `ea6c802ec4d3`; last update: `2026-11-05T15:12:44.916Z`.
- **Zero symlinks** in that installed tree.
- **38 text files match the accepted commit byte for byte**: manifest, wrapper, README, skill/guide/examples, Python source, catalog JSON, project file, and lockfile. Linked examples were compared with their targets at the accepted commit. Image/font contents were not independently compared.
- There is **no diff from `ea6c802` to this head** in the plugin, core source, project/lock files, or linked example fixtures. The later commit changes records only. This closes the previous ambiguity between an older installed catalog and a newer checkout.

The installed wrapper reports core/package `0.5.0a2`, catalog `2026.11.1`, `render_available: true`, and an empty render host-blocker list. The separate public-distribution blocker O-002 remains disclosed; it is not a host blocker. My wrapper calls used `XDG_DATA_HOME=<repo>/reports/astra-m7-recheck-work/runtime-data`, not the owner's runtime. Identity checks and five-type input retain the evidence.

I parsed JSONL with a script that retains text and tool inputs/results, drops image blocks, and suppresses long encoded strings. No raw JSONL was printed. Tool-use IDs were joined to results and permission denials; “attempted,” “executed,” and “successful” were counted separately.

| Recorded session | Turns | Permission requests | Wrapper mentions | Executed without request | Successful wrapper results | Render |
|---|---:|---:|---:|---:|---:|---|
| `final-create` | 19 | 3 | 11 | 10 | 10 | strict, non-draft |
| `final-edit` | 20 | 1 | 11 | 11 | 10 | strict, non-draft |
| `final-english` | 11 | 2 | 4 | 4 | 4 | strict, non-draft |
| **Total** | **50** | **6** | **26** | **25** | **24** | **3 successful renders** |

The recorded **25 executions** is correct. One compound catalog loop was denied before execution. One executed command, `catalog --provider aws --entity database --limit 50`, returned usage exit **64**; the session recovered with supported queries. I independently reproduced that exit 64. It is not a permission denial or a plugin runtime defect, and the record does not call all 25 executions successful.

Each init record reports Claude Code **2.1.309**, `claude-sonnet-5-5`, default permissions, and the plugin source `cloud-architecture-diagrams@mingrammer-local` at the accepted cache path, rather than an inline plugin source. The Skill itself requested approval in each run. This corroborates installed-plugin selection and no blanket Skill pre-approval. Exact launch flags and the private-Git update action remain implementer/owner provenance; I did not independently repeat installation or infer every launch flag from the init event.

The supplied create model and its render graph contain four D-036 types: ECS cluster, ECS Fargate, Lambda, and WAF. The model adds the cluster, and the final Thai explanation says why. It does **not** contain `aws.containers.ecs_service`; see the P3 precision issue below. My separate direct-wrapper fixture covers all five successfully, but is not retroactive evidence of all five in the Claude session.

The edit session performs **no Write/Edit/MultiEdit**. The immutable create and edit bundle models are structurally identical; all IDs are retained. Its cache queries return no AWS cache type, also reproduced with the installed catalog taxonomy filter. It then validates and renders successfully. This is a correct conditional no-op, not an additional demonstrated file-edit workflow; the older installed real-config edit remains the evidence for that operation.

The English model and `view.json` contain replicas `2`, `app=web` labels, `ClusterIP`, Pod port `8080/TCP`, and Service ports `80:8080/TCP`. Their presence in render data is verified. The claim about what the picture visibly shows remains the implementer's visual observation, not mine.

All three recorded bundles still contain all six reported artifacts, with filesystem sizes matching the tool results. Their four JSON artifacts per bundle also match recorded SHA-256 values. PNG/SVG files were checked by existence and size only: I did not open them for inspection, hash their contents, or display images. My new five-type bundle has the same complete artifact structure and no render fallback. See bundle audit.

## Remaining and new concrete P3 record issues

**R1 — remaining F5, P3: the milestone summary still reports C1/C2/C3 as open.**

Location: `doc/project-management/milestones.md:120` (a changed line). Input: evaluate its current “three P3 findings stay open” statement against the new `M7-claude-plugin.md:214–216` disposition rows and the HOME mutation, damaged-runtime recovery, and external-symlink probes above. Observed wrong result: the current status summary says all three remain open, while the dispositions resolve them through a test, recovery guidance, and a documented limitation. Remedy: update the summary to distinguish resolved findings from intentionally retained behavior. `HANDOFF.md:43` has the same stale statement, and unchanged line 48 still says no live session has used the D-036 types; those are supporting consistency cleanup, not separate new changed-line findings.

**N1 — new P3: “All the new types” overstates the recorded session's type coverage if read as D-036's five catalog additions.**

Location: `doc/project-management/evidence/M7-claude-plugin.md:192`. Input: intersect the resource `service_type` values from the `final-create` Write input and immutable bundle model with the five D-036 IDs. Observed result: **four present, `aws.containers.ecs_service` absent**. The Fargate resource is correctly represented as `aws.containers.ecs_fargate`; the five-type set treats the generic ECS service as a separate catalog ID. Remedy: say “the four new types used by this model” or list the types. No new live run is needed to fix that wording. This does not reopen F1: that finding required a distinguishing new-type installed workflow, which the session provides, and direct wrapper coverage of the fifth type also passes.

No new P1/P2 was reproduced. These P3s concern precision of the closing record; they do not show an installation, validation, permission, or rendering failure.

## Validation, limits, and exit judgment

The scoped plugin suite passed: **63 passed, no skips**, using `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_claude_plugin.py -q -p no:cacheprovider --basetemp=reports/astra-m7-recheck-work/pytest`. The scratch-only HOME mutant produced the expected **one failing test**. Test failure fixture output was sanitized to remove environment values. The scoped `git diff --check` passed.

I did not run a new Claude session, interactive onboarding, a Code-tab authoring flow, a permission-dialog observation, an “always allow” test, a second Mac, any other OS, a private-Git install/update, the full repository gate, remote CI verification, an uncached-download benchmark, or visual/image-digest review. I did not reopen the broader renderer/catalog review or inspect `codex/aws-next-types`. The existing suite's normal packaging/render operations ran, but no image was displayed or visually inspected. Huawei icons remain limited to private personal use; nothing was published.

The written M7 exit asks for an installed private-repository version, validated models and retrievable SVG/PNG in actual Claude sessions, and independent review. D-035 accepts one Mac. The accepted identity is now explicit, installed-session outputs exist, the package matches the accepted commit and current head, and this recheck supplies an independent recorded assessment. Headless sessions satisfy the written “actual Claude Code sessions” condition. A drawn permission dialog is still unobserved, explicitly disclosed, and is not an additional requirement I impose on that exit. The two minor wording issues above do not invalidate those demonstrated conditions.

The tracked tree remained clean at the same head. There was no commit or push, and no owner config/plugin edit. Before/after hashes of `~/.claude.json`, `~/.claude/settings.json`, and the installed-plugin registry are unchanged; all 38 checked installed text files are unchanged. Integrity record.

Disposition: **approved for closing M7** for acceptance copy **`ea6c802ec4d3`**, with the stated one-Mac, headless-session, unseen-dialog and non-visual-review limits. F2 remains the owner's recorded decision.

## Recorded by the implementer

Claude Opus 5.5 ran this recheck the same way as [the review](M7-astra-review.md), and Codex's log header again records `gpt-6-astra` and `high`. The evidence the report names stays in the git-ignored `reports/astra-m7-recheck-work/`, so its links are plain words here. R1 and N1 are fixed in the commit that adds this record, after the recheck, and no independent review covers those wording changes.
