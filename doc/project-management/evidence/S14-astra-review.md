# S14 independent bounded review

Date: 2026-11-06 (Asia/Bangkok)

Range: `201792cb9065a457a392e12f4be6a56a1a89089e..da83f0a93f075e672152bfe152ab4ef0e64d0ed7`.
Reviewed the requested merged change; any subsequent fix belongs in a later change under D-041.
Reviewer: Codex, described by the session as based on GPT-6. The exact serving model variant and effort are not exposed to me; the report filename does not establish that this is GPT-6 Astra. Implementer: Claude Opus 5.5.

## Findings

No actionable P1, P2 or P3 findings in this range. I found no validated counterexample where this change incorrectly adds a redundant typed-reference note or removes an otherwise unrepresented reference. This conclusion is limited to the rules and probes below, not a claim about every possible model.

## Isolation and method

Extracted both endpoints with `git archive` into `reports/astra-s14-review-work/base/` and `head/`. Tests imported the extracted head source explicitly via `PYTHONPATH` using the existing `.venv/bin/python`; they did not depend on the moving checkout's source. All scratch output is under `reports/astra-s14-review-work/`.

I inspected the previous run's scripts/results, reviewed their method, and reran its reference matrix, five mutations and build audit against my newly extracted endpoints. Old results were not treated as approval. I also independently audited fixture relationship pairs and reproduced the empty-HOME issue on both endpoints.

No tracked file was edited. No commit, push, tag, publication, owner configuration change, installed-plugin change, Claude session, or image viewing was performed. The requested visual tests rendered and compared image bytes locally; no image or image data was displayed.

## 1. Typed-reference table and actual semantics

Reviewed `src/cloud_architecture_diagrams/render/graph.py:254-259,433-471`, `src/cloud_architecture_diagrams/semantics.py:795-852`, the typed-reference checks in `validation.py`, and `doc/design/core-contract.md:44-46,64,101`.

| Reference | Drawing kind | Valid matching direction in the probed fixtures |
|---|---|---|
| `service_refs` | `traffic` | Ingress to Service, or reverse |
| `target_refs` | `traffic` | Service to Pod, or reverse |
| `volume_claim_refs` | `storage` | Workload/Pod to PVC |
| `volume_ref` | `storage` | PVC to PV |
| `storage_class_ref` | `storage` | PVC/PV to StorageClass |
| `config_refs` | `configuration` | Pod to ConfigMap |
| `secret_refs` | `configuration` | Workload/Pod to Secret |
| `service_account_ref` | `configuration` | Workload/Pod to ServiceAccount |
| `owner_ref` | `ownership` | Owner to dependent, opposite the typed reference |

The table agrees with the semantic kind rules. Other allowed generic kinds between these endpoints do not express the same typed reference. The mapper's unordered endpoint pair is appropriate here: traffic permits either direction, ownership is declared in the opposite direction to `owner_ref`, and invalid reverse storage/configuration models are rejected before normal rendering. The new mapper-only tests deliberately exercise those rejected directions; S14 correctly discloses this.

`probe.py` exercised each declared typed reference in `kubernetes-valid.json` and all six reference models, with no edge and with each of the 14 edge kinds in both directions. It ran the real validator before mapping. Results: 2,262 cases, 1,108 valid and 1,154 rejected; zero note mismatches among valid cases. It checked that unmatched kinds retain the note and matched kinds suppress it. Code inspection confirms selected relationships are also emitted as graph edges. These probes did not just call Pydantic.

`fixture_audit.py` additionally scanned all JSON fixtures for typed references joined by a relationship: 97 matching reference/edge pairs, none with a kind outside the table. This supports the S14 fixture statement independently of baseline success.

Evidence: `reference-matrix.json`, `reference-summary.json`, `fixture-audit.json`, and their scripts in the scratch directory.

## 2. Existing pictures

Ran:

```text
PYTHONPATH=<scratch>/head/src .venv/bin/python -m pytest \
  <scratch>/head/tests/test_references.py \
  <scratch>/head/tests/test_visual_regression.py -q \
  --basetemp=<scratch>/pytest-tmp -o cache_dir=<scratch>/pytest-cache
```

Result: **221 passed in 50.90s**. All 26 normalized graphs and all 26 image baselines passed, including the engine-version check. No baseline files changed in the reviewed diff. This is automated comparison, not human visual acceptance.

Evidence: `pytest-selected.log`.

## 3. Tests fail for their stated reasons

Each mutant had its own scratch source tree; no tracked source was sabotaged. Ran the nine-field note test and the two validated different-kind cases against each mutant.

| Mutation | Observed result | Actual failing assertion |
|---|---|---|
| Restore suppression by any kind | 11 failed | Note missing for an unrelated kind |
| Remove owner entry | 1 failed, 10 passed | Initial owner note absent |
| Remove service entry | 1 failed, 10 passed | Initial service note absent |
| Change claim mapping to configuration | 1 failed, 10 passed | Claim note remains when storage draws it |
| Change owner mapping to management | 1 failed, 10 passed | Owner note remains when ownership draws it |

These are assertion failures in the named behavior, not import, syntax, fixture setup or collection failures. The field inventory test remains a separate schema-coverage guard, as documented. The test oracle duplicates the mapping, so I did not rely on these tests alone to establish semantic correctness.

Evidence: `mutation-results.json`, `mutants/*/pytest.log`, `mutate.py`.

## 4. Records and author guide

Checked all changed documentation against code, fixtures and available local evidence. No contradicted changed statement was found.

- The guide's suppression rule matches the mapper. Its grouping rule agrees with the contract: only namespace/node detail views add these declared-property and typed-reference notes.
- S14's nine fields, 13 other kinds, five sabotage checks, validated management/observability cases and unchanged 26 views were independently reproduced above.
- The Work builder's content digest from the extracted base is `b3b15252a0c2a0528b829fba5fd1eea4a73e6851640bca96f2acb84f71f4d437`, matching the documented installed build's version suffix. Both stored `one` and `two` ZIP files match their recorded SHA-256 values, and those values are identical. Their markers name the full base SHA and `source_dirty: false`.
- `reports/work-build/host-proof.json` lists 35 passing checks and explicitly limits itself to the host engine/client with a throwaway profile and no model/account. This supports D-040's host-check wording; it is not actual Work UI or live-prompt evidence. Owner installation, owner approval, absence of live prompts, and earlier tool quota/credit events are historical/owner-reported facts, not independently observable facts established by this review. The records distinguish those limits.
- `reports/work-build/s14-reproduce.out` exactly matches the changed S10 proof JSON, including commit, source digest and wheel digest. The stored gate output lists 17 passed lanes. I inspected these existing outputs; I did not rerun the proof or full gate. Changes from `cad6098` to the requested head are confined to five management/evidence documents, consistent with the proof describing the same core source.
- D-041 and the S14 review section explicitly state that merging preceded completed independent review. Prior partial progress is not represented as approval.

Evidence: `work-audit.json`, `work-audit.log`, and the existing `reports/work-build/` text/JSON outputs. This review does not certify historical assertions beyond their available evidence.

## 5. Empty-HOME build

Created separate Git metadata around scratch copies of the archived endpoints, referencing the existing object database read-only. Set HEAD/index to each original commit without creating a commit. Added only a dummy `.claude/settings.local.json` in those copies. Ran the extracted builder with an empty HOME and global/system Git configuration disabled, writing build outputs under the scratch directory.

| Source | Git status before build | `source_dirty` |
|---|---|---|
| Base `201792c` | `?? .claude/` | `true` |
| Head `da83f0a` | clean | `false` |

The head build produced version `0.1.0-alpha.1+300814610ce7` and ZIP SHA-256 `ac3cff69799ee8e609598dd1436f28b70607208eedf96dd9eb40b46ae6864634`, identical to the existing `reports/work-build/nohome/build.json` archive. The fresh marker correctly records the requested head; the existing marker records `cad6098`. Thus P3-3 is reproduced and fixed, rather than inferred solely from the new ignore line.

Evidence: `build_probe.py`, `build-probe.json`, `nohome-base/build.json`, `nohome-head/build.json`.

## Additional checks and limits

Ran the complete selected files `test_provider_semantics.py` and `test_work_plugin.py`: **889 passed, 1 failed in 70.47s**. The failure was `test_s04_fixture_stays_frozen_and_separate` at `tests/test_work_plugin.py:432`: it invokes `git ls-files` from the archive folder, receives an empty list, and hashes `[]` rather than the fixture tree. Reran that exact test against the identical extracted source with the isolated Git index used above: **1 passed in 0.24s**. This is an archive-environment limitation, not a defect introduced by the bounded diff. Logs: `pytest-extra.log`, `pytest-git-recheck.log`.

Did not run `scripts/reproduce_core.py`, the full quality gate, all remaining pytest files, remote CI, a live Work session, a Claude session, a second-machine check, installation into the owner's profile, or human image inspection. Did not verify remote tags or historical quota/credit events. Existing proof/gate/host artifacts remain stored evidence rather than newly executed results. This approval covers the bounded source/documentation change, not release or two-machine acceptance.

Disposition: **approved**.

## Recorded by the implementer

Codex CLI ran it with `codex exec -m gpt-6-astra -c 'model_reasoning_effort="medium"'`, and its log header records `gpt-6-astra` and `medium`. Its scratch evidence stays in the git-ignored `reports/` folder, so its local links are plain words here. The dispositions are in [S14](S14-open-p3-fixes.md#follow-up-after-review).
