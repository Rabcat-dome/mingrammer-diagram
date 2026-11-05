# Model Strategy and Code Review

Model guidance verified: 2026-10-31 | Review state updated: 2026-11-03 | Status: Recommended policy, not an account configuration change.

## Selection

Use **GPT-6.1 Sol (`gpt-6.1-sol`)** for normal development and **Claude Fable 5.1 (`claude-fable-5-1`)** for independent code review (D-021). Use Medium effort for bounded implementation, High for schema/semantic/security work and milestone reviews.

The [official model guide](https://learn.chatgpt.com/docs/models) describes Sol as suitable for sustained work at lower cost than Astra, Astra for the most demanding work, Terra for writing/visual understanding, and Luna for focused repeatable tasks. The allocation below is our project recommendation, not a vendor guarantee of review accuracy. Account/client availability must be checked when work starts; record any substitution.

| Work | Recommended model / effort | Reason |
|---|---|---|
| Requirements, architecture trade-offs, runtime decision | Sol / High; Fable / High decision review | Overlapping provider dimensions and host constraints |
| Normal Python, CLI, catalog and test implementation | Sol / Medium | Bounded work with executable acceptance evidence |
| Schema, hierarchy, Kubernetes detail semantics, isolation, path handling, auth, CI trust rules | Sol / High | Errors affect all adapters and potentially host access |
| Every code PR review | Fable / Medium; High for high-risk changes | Separate review pass focused on regressions and missing cases |
| M3, M5 and final M6 review | Fable / High | Architecture/semantics/security and release decisions |
| Diagram visual inspection assistance | Terra / Medium, optional; Fable if semantic interpretation is difficult | Layout/label inspection; still requires fixtures and owner review |
| Mechanical catalog formatting, ID inventory, short summaries | Luna / High, optional, after deterministic validators exist | Narrow repeatable work; no authority to approve semantic or license changes |

Avoid automatic Max/Ultra use. Increase effort only when a concrete unresolved problem warrants it. This strategy does not request parallel agents or change the current session model.

## Review workflow

1. Implement a small requirement-linked change with targeted validation.
2. Start a separate Fable review pass over the base-to-head diff, relevant surrounding code, requirement IDs, and actual check results. A separate pass can be another session; no sub-agent is required.
3. Ask for actionable findings with severity, file/line, failure scenario, evidence, and remedy. Focus on correctness, provider semantics, unsafe execution/input, artifact portability, CI trust, compatibility, and missing meaningful tests.
4. Fix confirmed findings, rerun affected checks, and request review of the updated commit. Preserve dismissed findings with reasons.
5. Record model ID, effort, base/head SHA, checks inspected, unresolved findings and disposition. A review of an old SHA does not cover later code changes.

If Fable is unavailable, record the limitation and use an available capable model in a fresh review pass; retain human review for high-risk changes. Do not silently label a self-check as an independent Fable review. Different models reduce some shared assumptions; they do not prove correctness.

Suggested review instruction:

```text
Review this base-to-head diff against the linked requirement IDs.
Inspect surrounding code and supplied test evidence. Report actionable bugs,
regressions, semantic mistakes, security problems and missing high-value cases.
For each finding give severity, file/line, a concrete failure scenario, evidence,
and a fix direction. State checks not run and review limitations. Do not edit code.
```

Astra/High reviewed alpha.1 (afbacca to 7208317) and found one P2 output-root symlink issue. The alpha.2 review (7208317 to 1fd2d72) confirmed that fix and found two P2 issues: helper shutdown cleanup and a deleted-file race. The [alpha.3 Astra/High review](evidence/S04-native-alpha3-review.md), base 1fd2d72 to 2fc8047, confirms both fixes with no new confirmed actionable runtime finding. See [initial review](evidence/S04-astra-review.md) and [native review](evidence/S04-native-alpha2-review.md). Local tests and an earlier review do not approve later code.

S05 used GPT-6.1 Sol / XHigh inherited from the current app setting; the project recommendation remains High for this work and no model setting was changed. Separate GPT-6 Astra / High reviewed ff53a88 to e645415, found two P2 issues and confirmed both fixes at 785e1ee with no additional actionable findings. [Exact review/evidence](evidence/S05-astra-review.md) separates reviewer checks from root's actual fix-head CI verification.

S06 used Claude Opus 5.5 (`claude-opus-5-5`), the model of the session the owner started, rather than Sol, with no model setting changed. A separate GPT-6 Astra (`gpt-6-astra`) / High review now covers `c6a59e52a2e5f2824b4c08062041c15dca8c9bbd..556945952fef1461c03451ba76ed3f652909edde`, with implementation source equal to `6929253`. It requests changes for five P2 semantic findings, independently reproduced in both validation modes despite 382 passing catalog/semantic tests. No model setting changed and no parallel agents were used. M2 remains open for finding resolution/disposition, fix-head re-review and the owner's asset-rights exit decision. The earlier M7 Medium/Low fixes were not reviewed in this pass. See the [independent review](evidence/S06-astra-review.md) and [implementation evidence](evidence/S06-provider-catalogs.md#model-and-review).

On the owner's subsequent instruction to fix the findings, the same GPT-6 Astra / High chat implemented F1-F5. The local gate passes 12 lanes and 637 tests, with 22 CLI rejection probes. This is implementation and same-session verification, not an independent fix review. [Fix evidence and source digests](evidence/S06-review-fixes.md) identify the tested working tree, later committed at `dc54b4d`.

Under D-020, Claude Fable 5.1 (`claude-fable-5-1`) / High reviewed `5569459..dc54b4d` in a fresh agent, as the owner's chosen substitute for Astra/High on this review only. It is not recorded as an Astra review. It found F1-F4 fixed and F5 partly fixed, with one new P2 and four new P3 findings. Claude Opus 5.5 then fixed the P2 and one P3, and the same reviewer approved `5f391eb`; see the [fix review](evidence/S06-fable-review.md). That last change shares a vendor with its reviewer.

D-021 replaces Astra with Fable for every review from 2026-11-03, on the owner's request, and lifts D-020's one-review limit. Earlier reviews stay recorded under the models that ran them. The S06 and S07 implementation also ran on a Claude model, so a Fable review of that work shares a vendor with it. Name the implementing model in each review record so that limit stays visible.

D-025 adds GPT-6 Astra / High and GPT-6.1 Sol / High reviews of `5569459..aefcdbc`, on top of Fable's, because that work's implementer and reviewer shared a vendor. Claude Opus 5.5 fixed the findings. See [S11](evidence/S11-gpt-reviews.md).

S12 used Claude Opus 5.5 (`claude-opus-5-5`), the model of the session that ran it, rather than the planned Sol, with no setting changed. Claude Fable 5.1 reviewed it under D-021, in fresh agents started at High, though neither could confirm that effort. See [its record](evidence/S12-fable-review.md).

S07 / M3 used Claude Opus 5.5 (`claude-opus-5-5`), the model of the session that ran S07, rather than the planned Sol/High, with no model setting changed. This is a recorded substitution. Under D-021, Fable/High [reviewed it](evidence/S07-fable-review.md) in a fresh agent and requested changes on three P2 findings. It approved their fixes at `c8fc687`, after finding a regression in the first fix. Claude Opus 5.5 wrote the fixes, so that review shares a vendor with them. See the [S07 evidence](evidence/S07-controlled-rendering.md#model-and-review).

S08 / M4 used Claude Opus 5.5 rather than the planned Sol/Medium, with six Claude Sonnet 5.5 agents writing the reference models under its brief, and no model setting changed. This is a recorded substitution. Fable/High [approved it](evidence/S08-fable-review.md) at `a407a7a` after three P2 findings. See the [S08 evidence](evidence/S08-reference-diagrams.md#model-and-review).

S09 / M5 used Claude Opus 5.5 (`claude-opus-5-5`) rather than the planned Sol/High, with no model setting changed. This is a recorded substitution. Under D-021, Fable/High [reviewed it](evidence/S09-fable-review.md) in a fresh agent, requested changes on two P2 findings and approved `aa813ed`. Fable and Opus share a vendor. See the [S09 evidence](evidence/S09-work-plugin.md#model-and-review).

## Pipeline policy

Deterministic checks are the required automated gate. AI review starts as a required recorded review activity, performed manually in the development tool; it is not an API dependency for every CI run.

Automated model review is optional later. First prove authentication, repository data permissions, token/cost ceiling, read-only execution, model availability, and a stable reporting contract. Timeout/unavailable review means “review pending,” never “review passed.” It must not approve/merge changes or execute instructions from repository content.

Critical/High findings block release until resolved. Medium findings require explicit disposition. AI output is evidence for a human decision, not a substitute for tests or owner acceptance.

## Runtime model policy

The plugin uses the user's selected Work host model to interpret requests and author the architecture JSON. It must not silently select a different host model. Recommend Sol for ordinary diagram work and Astra for difficult multi-cloud reasoning; rendering remains model-independent.

No mandatory second LLM service or model API key is needed for validation/rendering. Do not assume a Work subscription grants API credits or automated review access. Provider choices come from catalogs and context, with uncertainty disclosed; a more capable model does not replace semantic validation.

For Claude Code support, reuse tool/model contracts and select the Claude model when the adapter's acceptance phase begins, using then-current official documentation and actual account availability. M7 preparation under D-015 used Claude Opus 5.5 (`claude-opus-5-5`), the model of the owner's session rather than a project selection, with Sonnet 5.5 and Haiku 5.5 for headless checks. A same-session high-effort review with that model found 10 issues, all fixed; it is not an independent pass. A later fresh Claude session reviewed the same work with the same model, which is a substitute of limited independence; under D-021, [Fable/High approved `c5f74b4..c6a59e5`](evidence/M7-fable-review.md) The P2 it found at the head, from S06, is fixed, and three P3 findings stay open.

## Token and cost discipline

- Load [HANDOFF](HANDOFF.md) plus the active milestone first; retrieve only relevant requirements/catalog entries.
- Keep one requirement baseline. Link IDs instead of copying entire specifications into issues/prompts.
- Use filtered catalog discovery, compact schema errors, structured diffs and bounded tool responses.
- Review changed code and its dependencies; do not repeatedly send unrelated repository content.
- Record actual usage when available; model names/effort are not cost estimates. Re-evaluate the allocation at milestone boundaries using observed defects, latency and usage.
