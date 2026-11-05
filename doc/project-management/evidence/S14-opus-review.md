# S14 review: `201792c..da83f0a`

**Disposition: approved, with seven P3 findings for a later change, as D-041 provides. No P1 or P2 finding.** Fix F1 first: until then, P3-1 is fixed for kind but not for direction.

- Reviewer: Claude Opus 5.5 (`claude-opus-5-5`), as a fresh agent with no prior context. **The implementer was also Claude Opus 5.5, so this reviewer shares a model and vendor with the implementer.** This is not an independent-vendor opinion, and it is not the Codex CLI route D-041 names.
- Stable copy: `da83f0a`, extracted to `reports/opus-s14-work/da83`. The checkout stayed at `da83f0a` and its tracked files are clean. I committed and pushed nothing, opened no image and published nothing.
- Scratch: `reports/opus-s14-work/`. Key files are `matrix.out`, `cases.out`, `cases-base.out`, `fix-new.json`, `fix-base.json`, `mutations.out`, `mutations2.out`, `mutations3.out` and `p33/`.

## Answers

| Question | Answer |
|---|---|
| 1. Is the table right? | Yes for kind. Every row is accepted by strict validation in the direction the reference means, and no row names a kind the core refuses. Two limits remain: F1 (direction) and F4 (repeated facts) |
| 2. Did a picture change? | No. All 65 visual tests pass, covering graph and PNG for 26 views, and the range touches no baseline. The old and new mappers give identical lines for all 47 views of the 21 fixture models |
| 3. Are the tests strong enough? | They fail for the reasons their names give, but they miss three behaviours: F2 and F3. They also pin F1 as correct |
| 4. Are the records true? | Mostly. F5, F6 and F7 are the exceptions, and the checked statements are listed below |
| 5. Is P3-3 fixed? | Yes. `source_dirty` is `false` with an empty `HOME`, and it is still `true` for real dirt |

## Findings

### F1 (P3). A reversed `traffic` line hides a reference it does not state

- File: `src/cloud_architecture_diagrams/render/graph.py:255` and `:467`, which match an unordered pair. `tests/test_references.py:1075` asserts this behaviour.
- Input: `tests/fixtures/kubernetes-valid.json`, with `service` declaring `target_refs: ["pod-a", "pod-b"]`, plus one selected relationship `{"id": "hairpin", "source_ref": "pod-a", "target_ref": "service", "kind": "traffic", "label": "calls own Service"}`. Strict validation passes.
- Wrong result: the rendered `service` node reads `['service', 'Service', 'target: pod-b']`, and the SVG has no `target: pod-a`. The only line says the Pod calls the Service, so nothing says the Service targets `pod-a`. An edge `service -> ingress` likewise removes `service: service` from the Ingress.
- Why it matters: `matrix.out` tried the 43 legal source, field and target combinations against all 14 kinds, in both directions, directed and undirected. Validation refuses the reverse drawing line for the other seven fields; for `owner_ref`, that reverse is the dependent-to-owner line. So "in either direction" only ever applies to `traffic`, the one kind where direction changes the meaning.
- Not a regression: `201792c` hides this too. But the title of P3-1 says "kind or direction", and S14 records P3-1 as fixed.
- Fix cost: I sabotaged a scratch copy so that a directed `traffic` line hides the note only from reference holder to target. `test_references.py` and `test_visual_regression.py` then gave 2 failed and 219 passed. The two failures are the `service_refs` and `target_refs` cases of the test at line 1075, and no visual test failed.

### F2 (P3). Nothing tests a reference list with more than one target

- File: `tests/test_references.py:1038` cuts each list to one target.
- Input, sabotage A: in `graph.py:463-468`, drop the whole line when any one target is drawn.
- Input, sabotage B: use `targets[:1]`, so only the first target is ever named.
- Wrong result: both sabotages pass all 1,509 tests in the six render, semantic, reference, contract and visual files, the same count as the unsabotaged copy.
- The cases exist in the fixtures but no test asserts them. The `detail` views of `tests/fixtures/kubernetes/{aks,cce,eks,gke,onprem}.json` have a Service with one target drawn and another not. `kubernetes-valid.json` maps to `target: pod-a, pod-b`. These are not reference views, so the baselines do not see them.
- The shipped code is right. `cases.out` shows `target: pod-b` staying when only `pod-a` is drawn.

### F3 (P3). Nothing tests an undirected line

- File: `tests/test_references.py:1059`. `_with_edge` never sets `direction`.
- Input: sabotage `graph.py:255` so that only `direction == "directed"` edges enter `self.linked`.
- Wrong result: all 1,509 tests pass. `matrix.out` shows the shipped code does hide the note for an undirected line of the drawing kind, but no test holds that.

### F4 (P3, by design). A note repeats what a line of another kind says

- File: `graph.py:467`, and the rule in the model guide at line 103.
- Inputs, each strict-valid on `kubernetes-valid.json`:
  - `pod-a -> secret`, `dependency`, label `mounts secret`
  - `pvc -> pv`, `attachment`, label `bound to volume`
  - `ingress -> service`, `dependency`, label `routes to`
  - `deployment -> replicaset`, `management`, label `owns`
- Result: both the note and the line appear, for example `secret: secret` and `mounts secret` in the SVG. At `201792c` the note was hidden.
- Both statements are true and nothing is lost, and the review of P3-1 asked for this. No fix is needed. A sentence in the guide telling authors to use the drawing kind would settle it.

### F5 (P3). The core contract does not state the new rule

- File: `doc/design/core-contract.md:101`.
- Input: the text "any typed reference, such as `secret_refs`, that no selected relationship already draws".
- Wrong result: the contract is the rules document, but only the guide names the kinds and direction. Read plainly, the sentence supports the old behaviour, where any relationship counts. `M6-p0-gaps.md:28` uses the same wording, though that record is historical.

### F6 (P3). HANDOFF still lists the Work build as remaining

- File: `doc/project-management/HANDOFF.md:47`, with the same point at `:48` and `:49`.
- Input: line 47 says what remains includes "a Work plugin build to take core `0.5.0a2` and catalog `2026.11.2`". Lines 48 and 49 say the Work plugin "takes a new version".
- Wrong result: this contradicts line 50 and D-040. The `b3b15252a0c2` ZIP holds `catalog_version` `2026.11.2` and version `0.5.0a2`. What remains now is a rebuild for S14 and the deferred Work check.

### F7 (P3). "The gate passes 17 lanes" omits where and on what

- File: `doc/project-management/evidence/S14-open-p3-fixes.md:23`.
- Input: `reports/quality-gate.json` says commit `cad6098`, `working_tree_dirty: true`, `github_actions: false`. Actual CI [run 42064395540](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42064395540) at `cad6098` failed at `release-audit`.
- Wrong result: the sentence sits next to "at `cad6098`" and reads as a pass at that commit. It was a local pass on a dirty tree. The S13 record, by contrast, states a clean checkout and cites a run.
- The conclusion still stands. All 210 gate source digests match `cad6098`, `a8ab864` and `da83f0a`, and [run 42067738656](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42067738656) on `main` at `da83f0a` passes all 17 lanes.
- The failure log says only that the lane failed. My inference is that the proof still named the old commit, because the commit message says the proof follows and the next commit passes.

## 1. The table

Results below are for directed lines. Undirected lines gave the same outcome in every case.

| Field | Legal pairs found by trial | Line that hides the note | Reverse of it | Other kinds strict accepts, note stays |
|---|---|---|---|---|
| `service_refs` | Ingress to Service | `traffic` | Accepted, hides (F1) | `vpn`, `peering`, `replication`, `management`, `attachment`, `dependency`, `observability` |
| `target_refs` | Service to Pod | `traffic` | Accepted, hides (F1) | The same seven |
| `volume_claim_refs` | Pod or workload to PVC | `storage` | Refused | The same seven |
| `volume_ref` | PVC to PV | `storage` | Refused | The same seven |
| `storage_class_ref` | PVC or PV to StorageClass | `storage` | Refused | The same seven |
| `config_refs` | Pod, workload or IngressController to ConfigMap | `configuration` | Refused | The same seven |
| `secret_refs` | Pod, workload, ServiceAccount, Ingress or IngressController to Secret | `configuration` | Refused | The same seven |
| `service_account_ref` | Pod or workload to ServiceAccount | `configuration` | Refused | The same seven |
| `owner_ref` | The six owner pairs | `ownership`, owner to dependent | Refused | The same seven, plus `traffic` |

Resources outside Kubernetes cannot be targets, so they add no case:

- `secret_refs` pointing at `aws.security.secrets_manager` gives `K8S_REFERENCE_KIND_INVALID`.
- That type carrying a Kubernetes `Secret` context gives `CATALOG_KUBERNETES_KIND_MISMATCH`.
- A Kubernetes Secret on another provider gives `K8S_CLUSTER_MISMATCH`.
- A `configuration` line from a Deployment to Secrets Manager is valid, but it has no typed reference, so no note is involved.

The fixture claim holds. Across 168 selected typed-reference pairs in 47 views, none is joined by a line outside the table, and none by a reverse line other than the owner-to-dependent `ownership` line, which is the right direction. `tests/fixtures/semantics/cases.json` holds no whole models, so this scan did not cover it.

## 3. Sabotage

All of these ran in a scratch copy.

| Sabotage | Result |
|---|---|
| The five S14 names: any kind hides, `owner` removed, `service` removed, `claim` wrong kind, `owner` wrong kind | Each fails for the named reason. Any-kind fails 11 tests, the others 1 each |
| Each of the other seven lines removed, and each of the other seven given the wrong kind | Each fails at its own field (removing `secret` also fails the two real-model tests) |
| Direction-sensitive, never hide, always hide, `dependency` also hides | Caught |
| Unselected edges count, ID instead of name | Caught, by the real-model test |
| A new `_ref` field on the model | Caught by `test_every_typed_reference_field_is_covered_below` |
| Any line of that kind on the entity hides all its references | Caught only incidentally, by the two real-model tests |
| Whole line hidden, first target only, undirected ignored | **Survive** (F2, F3) |
| Validator refuses PVC to PV, `configuration` to ServiceAccount, or `configuration` to ConfigMap | Caught by real-model and semantic tests, not by the mapper test |

Calling the mapper directly costs little in practice. Only 15 to 17 of the 28 directed combinations per field can pass strict validation, so roughly 40 to 45% of the checked cases can never occur. The mapper test does not check that its drawing kind is accepted, but other tests catch that when the validator changes. The real weakness is that the test asserts reachable and unreachable reverse cases alike, which is how it pins F1.

## 4. Statements checked and found true

- **Code and guide:** the note rule as worded in S14, the guide and the docstring, apart from the direction issue in F1.
- **P3-2 table:** nine fields, 13 other kinds, and a separate test for the field list.
- **Validator sentence:** the mapper test does try directions the validator refuses. It also tries kinds the validator refuses, which the sentence understates. The real-model test uses `management` forward and `observability` reversed.
- **Baselines and versions:** no baseline changed, core is `0.5.0a2`, and the tag still resolves to `97b0841`, locally and on `origin`.
- **Proof:** `S10-core-reproduction-proof.json` matches `reports/work-build/s14-reproduce.out` field for field.
- **Work build:** `one` and `two` have the same version and digest `add3418f...`, and my clone of `201792c` reproduced that digest. `host-proof.json` has 35 passing checks for `b3b15252a0c2`, and it says this is not the Work interface.
- **Install:** `~/.codex/config.toml` and the plugin cache show `b3b15252a0c2` installed. I read these and changed nothing.
- **Codex stop:** the log shows `gpt-6-astra` at medium effort, the selected tests passed, the five sabotages failed as expected, its table remark "so far", the limit message for 1:51 AM on 6 November, and no report file.

**Not verifiable by me:** that no prompt has run in Work, and the owner's spoken decisions in D-040 and D-041.

**Needs updating once this report is accepted:** S14's "No independent review has finished", and D-041's Codex route. The owner should decide whether this same-model review satisfies D-041.

## 5. P3-3

| Build, with `HOME` set to an empty folder | Version | `source_dirty` |
|---|---|---|
| Real checkout at `da83f0a` | `300814610ce7`, ZIP `ac3cff69...`, identical to `reports/work-build/nohome` | `false` |
| Clone at `201792c` with a `.claude/` folder (the control) | `b3b15252a0c2` | `true` |
| Clone at `da83f0a` with a `.claude/` folder | `300814610ce7` | `false` |
| The same clone with an untracked file, then with a modified tracked file | | `true`, both |
| The same clone with `note.md~` | | `true` |

The last row is correct behaviour for an untracked file, but `*~` is in the owner's global ignores and not the repository's, so that one global-ignore difference remains. No test holds the `.gitignore` line. That is too small to rank as a finding.

## Not run

- `scripts/reproduce_core.py`, as instructed. I compared its saved output only.
- `scripts/quality_gate.py` locally. I read its saved report and the CI results.
- `test_work_plugin.py`, `test_claude_plugin.py`, `test_release_audit.py`, `test_catalog_license.py` and `test_repository_checks.py` locally. For these I rely on the green CI run on `da83f0a`, and the sabotage runs did not include them.
- `scripts/work_host_check.py`, any live Claude or Work session, and any second machine.
- I did not look at any picture. The checks use graph data, SVG text and the visual tests' own PNG comparison.

## Recorded by the implementer

Claude Opus 5.5 ran in a fresh agent at medium effort. Its scratch evidence stays in the git-ignored `reports/` folder, so its local links are plain words here. The dispositions are in [S14](S14-open-p3-fixes.md#follow-up-after-review).
