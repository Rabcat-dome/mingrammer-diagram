# M7 independent milestone review

Reviewed 2026-11-05 (Asia/Bangkok), on `codex/m7-close` at **`8f9c246d31c508be6cf53ebc22b4527a6d8e0a68`**. Comparison: `c6a59e5..8f9c246`, restricted to the Claude plugin and `tests/test_claude_plugin.py`, with core inspection only to check the plugin's promises. The separate `codex/aws-next-types` worktree was not inspected or changed.

Reviewer identity: this session identifies itself as Codex, based on GPT-6. **The exact model identifier and reasoning-effort setting were not exposed to me; I do not know them.** The report filename is not proof that the reviewer was GPT-6 Astra. Implementer: Claude Opus 5.5, as supplied by the requester. This is a fresh review of the specified records and source. The completed historical Fable review of `c5f74b4..c6a59e5` is evidence for that range; the later Fable milestone review that was started and stopped supplies no findings or approval.

**Changes requested.** No P1 or new P2 runtime defect was reproduced. There is one P2 acceptance-evidence gap for this head, five new P3 documentation/methodology findings, and the three earlier P3s remain open. The implementation works in the exercised paths, but the proposed closing record does not yet identify and demonstrate the final installed version consistently.

## Findings

### F1 — P2: The closing claim outruns the installed-version evidence

**Location:** `doc/project-management/milestones.md:120`, especially “leave only how a permission dialog looks”; exit at line 129. Supporting record: `doc/project-management/evidence/M7-claude-plugin.md:172`.

**Concrete input and observed result:** I ran `capabilities`, `catalog --provider aws --limit 200`, and `validate` on a model containing the five D-036 types through both the checkout wrapper and the owner's installed wrapper, with review-owned `XDG_DATA_HOME` directories. The registry and cache identify the installed version as `c6c7490d8ca7727e4e2bf7b782e775b3119c531a`. That copy reports catalog `2026.11.0` and 48 AWS-filtered records; this head reports `2026.11.1` and 53. Both report core `0.5.0a2`. The same five-resource model exits **2 with five `CATALOG_TYPE_UNKNOWN` errors** through the installed copy, and validates and renders with **exit 0** through this head. This is an observed version difference, not a defect in the older catalog.

The saved real sessions render successfully using `97b0841` or `c6c7490`, and the glyph session uses a checkout with catalog `2026.11.0`. None demonstrates installation from the private repository and model-to-artifact operation of `8f9c246`/catalog `2026.11.1`. My six new sessions load this head with `--plugin-dir`; they measure permissions, not the installed authoring/render workflow. Clean-copy tests demonstrate packaging mechanics but do not replace that host workflow.

**Impact/remedy:** D-035 waives the second Mac, not version identity. Before closing M7 for this head, record the chosen release/acceptance identity and one private-repository install/update plus an actual Claude session that validates and renders with that identity. A small AWS flow involving a newly added type would distinguish the versions. Preserve the older runs as historical evidence. This finding does **not** claim the head cannot install or render; it says that the remaining work is more than observing a dialog.

Evidence: final probes, input, head capabilities, installed capabilities.

### F2 — P3: Release-version policy is unresolved and the test enforces preparation policy

**Location:** `plugins/cloud-architecture-diagrams/.claude-plugin/plugin.json:2`, `tests/test_claude_plugin.py:121`, and `doc/project-management/milestones.md:127`; compare P-019 at `doc/project-management/decisions.md:68`.

**Concrete input and observed result:** The current CLI's `plugin validate <plugin>` passes with a missing-version warning. `plugin validate <plugin> --strict` exits **1** for that warning. The manifest has no version, and the test explicitly requires its absence. P-019 says to set an explicit version at release, whereas M7-04 says no version bump applies. No later decision in the requested records reconciles those positions.

**Impact/remedy:** Commit-based preparation installs work; this is not a broken-install finding. Record whether closing M7 is still a commit-versioned preparation acceptance or is the release P-019 anticipated. For a release, set the explicit version and update the test; otherwise record the policy exception and accepted commit. The validator's separate public-directory license/icon messages do not block this private plugin and are not findings here.

Evidence: normal validation, strict validation.

### F3 — P3: README turns sampled permission behavior into a universal promise

**Location:** `plugins/cloud-architecture-diagrams/README.md:52`.

**Concrete input and observed result:** In a new default-mode Haiku session with only project settings and only `Skill` pre-approved, I invoked the skill and issued exactly `"<plugin>/bin/cloud-diagrams" capabilities > /dev/null`. The host admitted it, with no permission denial. The README says a stdout redirect needs approval. The original 24 cases test redirects to ordinary files, not this exception. The saved real-config edit also executes `ls -la` and `find architecture -type f | head -50` without a permission request, despite the README's “any other command” wording.

**Impact/remedy:** Describe observed behavior for the tested host/settings and distinguish the skill's allow rule from the host's own safe-command handling and existing user permissions. Keep the ordinary-file redirect warning, but do not promise that every redirect or other command prompts. No arbitrary-command execution or harmful write was demonstrated: stderr redirection, process substitution, an expanding heredoc, and a symlink escaping the working directory were all denied in the new probes.

Evidence: six-probe summary, case `06-dev-null`; sanitized `dialogs/real-config-edit.jsonl` under scratch.

### F4 — P3: The permission stand-in does not enforce the documented mkdir boundary

**Location:** `doc/project-management/evidence/M7-permission-requests.json:7` and `M7-claude-plugin.md:172`. The server referenced by `reports/m7-acceptance/dialogs/real-config-create.mcp.json` implements the behavior.

**Concrete input and observed result:** I sent that existing server a `tools/call` permission request for `mkdir /private/tmp/astra-m7-z5hydaar/outside/stand-in-marker`, while its project was `/private/tmp/astra-m7-z5hydaar/cwd`. It returned **`behavior: allow`**. I did not execute the mkdir. The server's Bash branch checks only a command regex; unlike its file-tool branches, it never calls `inside()` for the mkdir target. The method says it allows a bare mkdir “there” and denies the rest.

**Impact/remedy:** Correct the method statement or constrain the target with the same resolved-path check, and retain a negative case. None of the three recorded request streams asks for mkdir, so this flaw does not overturn their actual 2/6/5 request outcomes. It does invalidate the claimed general boundary of the stand-in.

Evidence: permission-only counterexample.

### F5 — P3: The evidence still contains false present-tense statements and a wrong execution count

**Location:** `doc/project-management/evidence/M7-claude-plugin.md:180`, `:194`, and `:125`; also `doc/project-management/milestones.md:124`.

**Concrete checks and observed results:**

- Line 180 says the wrapper “ran 17 times.” Joining tool-use IDs to results and denials gives **6 + 4 + 6 = 16 successful wrapper executions** across real-create, real-edit and fresh-create. There are **18 Bash inputs naming the wrapper**, two denied before execution. The JSON's `bash_calls_naming_the_command` values **6/5/7 are correct for mentions**, not executions. The bare wrapper did not request permission in these runs.
- Line 194 says provider semantics are unchanged from M1 and a pass does not establish that a type exists. `validate` with `service_type: aws.compute.not_a_service` exits **2**, and `--mode lenient` with `taxonomy: made.up` also exits **2**. Current capabilities and successful validation report `core_catalog_provider`. The deployed-reality/reachability caveat remains appropriate; the M1-only claim is obsolete.
- Line 125 says none of the historical one P2 and three P3 findings is fixed. The P2 sentence now says “bypasses no other error,” and the negative lenient test passes. The linked completed review and milestone status themselves record that fix. The three P3s remain open.
- M7-01's current task row still calls the plugin “validate-only”; direct `render` produces a complete bundle at this head.

**Impact/remedy:** Update the present-tense summary and count executions separately from attempted commands. Retain dated historical observations with their versions. The pre-D-036 AWS draft outcomes are already identified as historical and are not false merely because the new catalog supports those services.

Evidence: session audit, direct checks, 60 passing tests.

### F6 — P3: The model guide omits two exceptions that the core accepts

**Location:** `plugins/cloud-architecture-diagrams/skills/architecture-model/references/model-guide.md:172` and `:179`.

**Concrete input and observed result:** Two minimal, fully selected on-premises Kubernetes models validate in strict mode with **exit 0 and no diagnostics**:

1. A same-cluster `IngressController` in `ns-a` has a `configuration` relationship to a `ConfigMap` in `ns-b`. The table says “same namespace”; `semantics.py` deliberately exempts an `IngressController` source from that relationship's namespace check.
2. A `Node` has `placement.deployment_context: ["pool"]`, where `pool` is a same-cluster `NodePool`. The guide unconditionally says this field cannot name a `Node` or `NodePool`; the core exempts a `Node` source.

**Impact/remedy:** Qualify the relationship table and the scheduling paragraph so an author does not reject supported representations or silently rewrite them. Preserve the distinction between typed references and explicit relationships. These are documentation discrepancies, not recommendations to weaken validation.

Evidence: guide checks, controller input, Node input.

## The three earlier open P3 findings

All three remain **P3**. None demonstrates a regression in the normal full-path invocation used by this skill.

| ID | File and line | Concrete reproduction and result | Reason for rating / remedy |
|---|---|---|---|
| C1 — missing HOME regression case | `tests/test_claude_plugin.py:599`; guarded code `bin/cloud-diagrams:15` | Current wrapper with `HOME=relative` and empty `XDG_DATA_HOME` correctly exits 3. In the test fixture's scratch copy only, change `/*) data=$HOME/.local/share ;;` to `?*) ...`; **all 60 tests still pass**. | The production behavior is correct; the protection lacks a regression test. Add a relative-HOME case without an absolute XDG override. |
| C2 — damaged runtime does not heal or explain recovery | `plugins/cloud-architecture-diagrams/bin/cloud-diagrams:32` and `:49` | Populate a review-owned data home, delete only its `site-packages/pydantic` directory while retaining dist-info, then call `capabilities` twice. Both runs exit **3**, with `ModuleNotFoundError` and “runtime failed unexpectedly”; neither repairs it or names the environment to recreate. | Requires local runtime damage and has a manual recovery path. Add a scoped recovery hint or one controlled repair attempt. |
| C3 — external symlink invocation fails | `plugins/cloud-architecture-diagrams/bin/cloud-diagrams:9` | Put a symlink to the wrapper in the external scratch directory and invoke its `capabilities`. It exits **3**, reporting no `pyproject.toml`, because it derives the project root from the link's location. | The skill uses the real full plugin path and does not rely on this route. Resolve the executable symlink or document the limitation. |

Evidence: mutation test result, scratch-only mutation hook, direct checks, external symlink result.

The separate glyph review's existing U+2028/U+2029 P3 is also relevant to guide line 22's “no newlines” wording. I reproduced strict validation accepting `a\u2028b`; I did not inspect its rendered appearance. It is not a new finding or a reason to reopen the renderer review.

## What the records prove, and what they do not

### Recorded permission and live-session results

The parser removed image blocks and encoded image data before inspection. No complete raw JSONL log was printed. Tool inputs, textual results and structured outcomes were used.

- **24 original probes:** all 24 issued Bash commands match `reports/m7-acceptance/probe/cases.json` byte for byte. All 24 admitted/denied outcomes match the tracked JSON: **7 admitted, 17 denied**. The no-argument command is admitted but returns usage exit 64; admission is not command success. Ordinary-file stdout redirects were denied. The no-marker statement is consistent with the denial results; it is not a proof about every shell spelling or every configuration.
- **Live installed sessions:** the recorded turn counts **25/15/19/21**, denial counts **2/3/2/0**, AWS lenient outcomes, GKE strict outcome and Huawei private-use warning all match the logs. Render results name complete six-file bundles; those files still exist and their sizes match the returned artifact metadata. I compared immutable model snapshots: the AWS WAF edit removes no existing ID and adds `waf`/`waf-alb`. The real-config S3 edit also preserves IDs and adds the bucket and two links. The duplicate `live-edit/thai-edit.jsonl` was not counted as another run.
- **Permission requests:** the `asks.jsonl` streams contain **2, 6 and 5** requests with the recorded allowed/denied answers. Bare wrapper calls run without a question after skill activation. The fresh-config run asks for guide/example reads; the real-config runs do not. Existing user permissions and the host's automatic handling matter. A scripted approval server is not a person clicking a dialog.
- **Glyph run:** the text/tool stream shows validation success, render refusal with `RENDER_TEXT_UNDRAWABLE`, two title edits, successful render, and disclosure of the substitutions. Current direct wrapper probes reproduce exit 2 in both strict and lenient modes for those unsupported characters. This verifies the refusal path without viewing images.

### Evidence boundaries for the exit

D-035 explicitly accepts one Mac and states that the Claude plugin has never run on the second. The old one-Mac installed sessions demonstrate that this adapter can author, validate, edit, render, and return artifact paths in real headless Claude sessions. Those are substantive acceptance results, not just unit-test substitutes.

Installation/update provenance from the private repository is recorded by the implementer; I verified the current local registry/cache identity but did not independently repeat a private-Git installation. The supplied logs demonstrate use of that cache. The final-head gap is F1: reusing those results for the newer catalog assumes successful installation and integration across a materially different package. D-036 intentionally leaves the core version unchanged, so `0.5.0a2` alone cannot establish identity.

The cold-start claim (fresh data/uv/Python caches, three seconds, 59/59/48 MB) is a recorded implementer measurement. The inspected acceptance directory has no corresponding complete timing/download transcript; my fresh private environments reused machine download caches. I therefore do not independently confirm the timing, full cold-download path or footprint. Likewise, PNG baseline-digest and visual-quality claims remain the earlier reviewer's observations; this review did not open images or verify image digests.

Unobserved: drawn permission dialogs, the effect of “always allow,” authoring/rendering in the Desktop Code tab, other operating systems, and a second Mac. The old Code-tab capabilities check under bypass permissions establishes neither default-mode prompting nor an authoring workflow. The written exit requires actual Claude sessions, which headless sessions can satisfy; unseen dialog appearance is a stated limitation, not a new runtime defect imposed by this review.

P-019's release-version decision, exact accepted plugin identity, and a current closure record still need resolution. This requested review supplies a new review record but does not retroactively turn the stopped Fable attempt into evidence or assert the unexposed reviewer model matches D-021.

## Independent execution at this head

**Plugin suite:** `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest tests/test_claude_plugin.py -q -p no:cacheprovider --basetemp=reports/astra-m7-work/pytest` — **60 passed, no skips**. The scratch-only HOME mutation also leaves 60 passing. No tracked test or wrapper was modified.

**Core-facing statements checked:** capabilities/schema/catalog discovery; strict valid/invalid models; lenient unknown-type draft and generic-fallback diagnostics; rejection of unknown taxonomy in lenient mode; render output creation and six-file artifact report; unsafe output failure; glyph rejection; new D-036 types; the guide's two semantic counterexamples. The suite covers the guide's enumerations, catalog IDs, mappings and copy-local assets/fonts. The advertised implemented commands, formats, limits and host requirements match current discovery output. This is a review with targeted runtime examples, not an exhaustive proof of every provider rule or every possible rendered view.

| Input | Observed wrapper exit / result |
|---|---|
| `capabilities`, schema/catalog, valid model | 0 |
| `{}` / unknown strict type / bad taxonomy in lenient mode | 2, JSON diagnostics |
| Missing uv or relative HOME without absolute XDG | 3, empty stdout and stderr explanation |
| `render --output <regular-file>` | 4, `RENDER_OUTPUT_PATH_UNSAFE`, no bundle |
| No arguments / invalid mode | 64, usage on stderr |
| Unsupported title characters | validation 0; rendering 2 in both modes |
| Unknown type rendered leniently | 0, draft plus `CATALOG_TYPE_UNKNOWN` and `RENDER_GENERIC_FALLBACK` |
| The five new D-036 types | head: validation/render 0; installed copy: validation 2 |

**Six paid permission probes:** used exactly the supplied CLI path and flags, from `/private/tmp/astra-m7-z5hydaar/cwd`, outside the repository. The environment builder removed every key beginning `CLAUDE_CODE` and the key `CLAUDECODE`. Each session invoked Skill once and Bash once; every command matched its requested text exactly. A review-owned `XDG_DATA_HOME` kept wrapper runtime changes in scratch. CLI-reported total cost: **USD 0.02072978**.

| Case | Command suffix after the quoted full wrapper path | Result |
|---|---|---|
| Baseline | `capabilities` | Admitted; current versions reported |
| stderr file | `capabilities 2> marker-stderr` | Denied; no marker |
| Process substitution | `validate < <(touch marker-process; cat model-link.json)` | Denied; no marker |
| Expanding heredoc | `validate <<EOF` with `$(touch marker-heredoc)` then `{}` in its body | Denied; no marker |
| Symlinked stdin | `validate < model-link.json`, pointing outside cwd | Denied; host resolved the outside target |
| Null-device redirect | `capabilities > /dev/null` | Admitted; no denial |

No interactive session was started. No seventh paid run was made. The stand-in counterexample was a local server request, not a model session or shell-command execution.

## Limits and workspace integrity

I did not run the full repository quality gate, fetch/revalidate remote CI runs, install/update/uninstall the owner's plugin, repeat private-Git installation, run an uncached download benchmark, execute the full authoring flow at this head, or inspect any image. Renderer/catalog code received only the checks needed for plugin claims; the other worktree and future catalog types were left alone. Public-directory release, publishing and rights clearance were not attempted.

All report, scripts, text-only log extracts, test copies and runtime outputs are under `reports/astra-m7-work/`, with only the required external permission working folder and its fixtures under `/private/tmp/astra-m7-z5hydaar/`. No images or image data were displayed or published. The tracked working tree remained clean at the same head; no commit or push was made.

The owner's `~/.claude/settings.json` and installed-plugin registry hashes were unchanged across the six CLI runs. **The hash of `~/.claude.json` changed during that interval.** I never wrote that file directly, did not complete onboarding, and have only before/after hashes, so I cannot distinguish CLI-maintained state from the other active Claude session's changes. I did not overwrite it to restore a stale snapshot. This limits any claim that the prescribed CLI runs left all Claude state byte-identical. Hash records are retained in scratch.

Disposition: **changes requested**. Resolve F1 for the chosen acceptance version and reconcile the release/evidence statements before closing M7. The existing wrapper P3s retain their ratings and can be explicitly dispositioned; no additional machine or public release is requested.

## Recorded by the implementer

Claude Opus 5.5 ran this review with `codex exec -m gpt-6-astra -c 'model_reasoning_effort="high"'`, and Codex's own log header records `gpt-6-astra` and `high`. The evidence the report names stays in the git-ignored `reports/astra-m7-work/`, so its links are plain words here. Each finding's disposition is in [the M7 evidence](M7-claude-plugin.md#astra-review).
