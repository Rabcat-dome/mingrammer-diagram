# S14 follow-up independent bounded review

Date: 2026-11-06 (Asia/Bangkok).

Range: `da83f0a93f075e672152bfe152ab4ef0e64d0ed7..c3fdae47058ca35709917027fe06d1298882c5c8`, requested branch `codex/s14-review-fixes`.

Reviewer: Codex, described by my instructions as based on GPT-6. The exact serving model variant and reasoning effort are not exposed to me; the filename does not establish GPT-6 Astra. Implementer: Claude Opus 5.5.

## Findings

No actionable P1, P2 or P3 findings. I found no strict-valid counterexample to the new suppression rule in the executed probes. This is a bounded review, not a proof over every possible model.

## Isolation

Extracted both endpoints with `git archive` into `reports/astra-s14b-work/{base,head}/`. Ran pytest from the extracted head, using the existing repository `.venv/bin/python` with `PYTHONPATH` explicitly set to the extracted source. Each mutation has its own source copy. Scripts, logs, model inputs and outputs are under `reports/astra-s14b-work/`. No project memory or earlier scratch scripts were used to decide the result; the two requested historical reviews were read as evidence to assess.

No tracked file, owner configuration or installed plugin was changed. No commit, push, publication or Claude session occurred. No image was opened for viewing or displayed, and no image data was printed. The requested automated rendering/comparison tests read image bytes internally.

## 1. Rule and semantic interpretation

Reviewed `src/cloud_architecture_diagrams/render/graph.py:254-265,439-478,736-738`, `semantics.py:795-852`, the reference-kind validation in `validation.py`, and the contract at `doc/design/core-contract.md:44,64,101`.

I agree with the new directional interpretation. `semantics.py:800-803` permits traffic in either direction except for prohibited endpoint kinds; it does not equate the two directions or infer Service selection from a Pod calling that Service. The existence of a valid reverse edge therefore does not establish that it depicts a typed target reference. Ownership explicitly checks the source as owner and target as dependent at `semantics.py:822-827`, matching the reversal of `owner_ref` in `_drawn_as`.

The drawing table is consistent with the reference semantics: traffic for Ingress-to-Service and Service-to-Pod; storage for claim, volume and storage class; configuration for ConfigMap, Secret and ServiceAccount; owner-to-dependent ownership. Undirected suppression in either orientation is the stated presentation convention. The validator still checks the stored source/target kinds even for undirected edges, so the mapper's reverse-undirected storage/configuration/ownership cases are not all strict-reachable. That is an existing validator restriction, not a regression in this diff.

Executed `probe.py` against each declared target in `kubernetes-valid.json` and all six reference models, varying all 14 kinds, both endpoint orders and directed/undirected: **4,368 cases, 2,084 strict-valid and 2,284 rejected; zero note mismatches among valid cases**. The probe isolates one reference target and checks actual mapped text after calling the real validator. It does not treat Pydantic parsing as strict validation. This matrix tests implementation consistency with the rule; the semantic judgment above is separate from that oracle.

A fixture scan found **97 reference/relationship pairs**, all using the expected kind and direction. No fixture exception was found. Evidence: `probe.py`, `probe.log`, `probe-results.json`.

Concrete base/head experiment: start from `kubernetes-valid.json`, keep Service `target_refs: ["pod-a"]`, select Service and Pod, and use only `pod-a -> service` of kind `traffic`. Strict validation passes. Base node text is `service Service namespace: namespace`; head adds `target: pod-a`. Both `namespace` and `node` grouping give that result. Changing the line to undirected suppresses the note on both endpoints of the reviewed range, as intended. Inputs are saved as `reverse-{namespace,node}-{directed,undirected}.json`; results are in `compare.log` and `graphs-comparison.json`.

A differently typed or oppositely directed line can have free text that repeats the reference. The updated contract and guide explicitly allow that duplication; edge label prose is not an alternate suppression key. I do not classify this documented behavior as a defect.

## 2. Existing pictures and selected pytest

Ran from the extracted head:

```text
PYTHONPATH=<scratch>/head/src <repo>/.venv/bin/python -m pytest \
  tests/test_references.py tests/test_visual_regression.py \
  tests/test_provider_semantics.py -q -p no:cacheprovider \
  --basetemp=<scratch>/pytest-tmp
```

**944 passed in 53.53s**: 158 reference tests, 65 visual tests and 721 provider-semantic tests. All 26 normalized-graph and 26 image-baseline comparisons passed, including the engine-version assertion. This is automated comparison, not human visual acceptance. No baseline is changed by this diff.

Additionally mapped all 47 views from strict-valid complete fixture models independently at base and head. Their full normalized graph objects are identical. Only the two custom directed reverse-traffic probes changed, as intended. Evidence: `pytest-selected.log`, `compare.py`, `compare.log`, `graphs-comparison.json`.

Initial test-launch attempts did not run tests: one named a nonexistent `test_semantics.py`, one used the wrong relative interpreter path, and pytest rejected a cache path containing `..`. Corrected the filename/path and disabled its cache provider for the successful run above. These were harness errors, not project failures.

## 3. Sabotage

Ran the nine-field mapper test plus the new reverse-traffic and multi-target tests against five independent scratch mutations. Inspected assertion failures, not just exit codes.

| Mutation | Result | Observed assertion failure |
|---|---|---|
| Treat every edge as both directions | 10 failed, 1 passed | Reverse directed edges remove the reference; the strict-valid Pod-to-Service test loses `target: pod-a` |
| Count undirected lines only in stored order | 9 failed, 2 passed | Reversed undirected drawing edges retain notes that should be suppressed |
| Read ownership from dependent to owner | 1 failed, 10 passed | Correct Deployment-to-ReplicaSet edge leaves `owner: deployment` |
| Hide the whole reference line when any target is drawn | 1 failed, 10 passed | The multi-target test loses `target: pod-b` when only `pod-a` is drawn |
| Iterate only the first target | 1 failed, 10 passed | The same multi-target test loses `target: pod-b` |

All failures occurred in the named behavior, not collection, imports, syntax or fixture setup. The four sabotages claimed in the follow-up record are reproduced, and the extra first-target mutation is also caught. Evidence: `mutate.py`, `mutations.json`, `mutants/*/pytest.log`.

## 4. Changed documentation and records

Read the entire bounded diff, including both newly added historical reviews, the activity log, HANDOFF, decisions, S14 follow-up, guide and contract.

- The current guide and contract accurately describe the implemented kind/direction rule, ownership reversal, undirected handling and permitted duplicate prose.
- The follow-up's F1–F5 dispositions agree with the code and tests above. Its four sabotage claims and unchanged-baseline claim were reproduced.
- The two historical review dispositions are accurately summarized: Opus approved with seven P3 items; Codex approved with none. Their disagreement is preserved rather than silently rewritten. The old “both directions” test description and “No independent review has finished” paragraph describe the initial S14 stage; the following text explicitly records what happened afterward. They are not the follow-up's current rule.
- HANDOFF now distinguishes the existing Work build from the deferred Work check and subsequent S14 rebuild. Stored `one` and `two` build markers identify `b3b15252a0c2`, core `0.5.0a2`, and source `201792c`; both ZIP hashes match their markers and each other. This supports build-content provenance, not present installation state.
- The revised local-gate wording agrees with the saved report: commit `cad6098`, dirty tree, `github_actions: false`, 17 passed lanes. All recorded source-file digests match that commit. Saved reproduction output exactly matches the committed S10 proof. Evidence: `records-audit.json`.
- The claim that the old CI failure was *because* of the stale proof is stronger than the Opus report's explicitly labeled inference. The commit history and later proof update are consistent with that explanation, but I did not independently establish causation. I found no demonstrated false statement to rate as a finding.

Not every historical assertion can be certified from this run. Remote CI outcomes, the exact historical dirty-file set, owner decisions/installation, absence of past live prompts, and historical model/quota events remain attributed records. I did not inspect owner configuration or refresh remote CI. Historical review test totals and builds are those reviewers' recorded results, not runs newly repeated in full here. No contradicted current implementation claim was found.

## Not run and limits

Did not run `scripts/reproduce_core.py`, `scripts/quality_gate.py`, the full pytest suite, plugin builds or host checks, remote CI/API checks, a Claude session, a live Work session, owner-profile installation, or a second-machine check. Did not view any image or publish any artifact. Stored build/proof/gate evidence was read and checked as stated, not represented as newly executed release validation.

Disposition: **approved**.

## Recorded by the implementer

Codex CLI ran it with `codex exec -m gpt-6-astra -c 'model_reasoning_effort="medium"'`, and its log header records `gpt-6-astra` and `medium`. Its scratch evidence stays in the git-ignored `reports/` folder, so its local links are plain words here. The CI cause it could not confirm is confirmed by that run's test report, as [S14](S14-open-p3-fixes.md#follow-up-after-review) records.
