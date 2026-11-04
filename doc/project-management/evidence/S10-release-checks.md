# S10 — Release Checks Without Work

Date: 2026-11-04 | Tasks: part of M6-01, and M6-02 | Branch: `codex/s10-release-checks`, from `codex/s09-work-plugin` | Core: `0.5.0a1`

**Result: the parts of M6 that do not need Work are done, and M6 stays open.** D-024 parks the owner's run in actual Work, so M6-01's two-machine run, M6-03 and M6-04 are blocked, and there is no release and no tag. Of 71 P0 requirements and scenarios, [the report](S10-p0-traceability.md) finds 30 met, 14 met with the owner's acceptance, 17 partly met, 7 blocked on Work and 3 blocked on a second machine. None is wholly unmet, and 17 partial results are real work left. [Fable/High approved](S10-fable-review.md) this at `debd754`, which passes actual CI [run 41787236496](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41787236496) with 1,461 tests.

## Task status

| Task | Status | Result |
|---|---|---|
| M6-01, core reproduction | Done on this Mac | [A new clone and runtime](#core-reproduction) match every baseline |
| M6-01, two machines in Work | Blocked | D-024 |
| M6-02, distribution contents | Done | [The `release-audit` lane](#distribution-contents) reads all four packages |
| M6-02, notices | Done, with two gaps fixed | [Dependency licenses and icon terms](#fixes-this-found) |
| M6-02, P0 traceability | Done | [The report](S10-p0-traceability.md), held to the baseline by a guard |
| M6-02, clean-install smoke test | Done | The wheel installs alone and renders from outside the repository, in the lane |
| M6-03, final review | Blocked | Needs M6-01 |
| M6-04, tag and package | Blocked | Needs M6-03 |

## Core reproduction

`scripts/reproduce_core.py` clones the repository from GitHub at one commit, and points `HOME` and every cache at a new folder. It downloads its own Python 3.13.7 and packages, and takes two routes to the core: the lock with no development tools, and a wheel built with the locked tools and installed from hash-locked requirements. Each route renders all 26 reference views from outside the clone, and each result is compared with that commit's baselines. [The proof](S10-core-reproduction-proof.json) holds the results, at `7a42e97`: all 26 views match in both routes, and the routes agree. The wheel it builds has the digest of a local build at that commit, and actual CI's wheel at `debd754`, which changes only records, has it too.

The proof binds to a digest of the source, the lock, the references and the baselines, because it is committed after the commit it reproduced, and a test fails if that source changes without a new proof. [S11](S11-gpt-reviews.md#limits) replaced the proof at `9fb199d`, with the same result. This proves a clean Python runtime on one machine. It shares Graphviz, Homebrew's other tools, uv, macOS and the sandbox with this Mac, and the clone uses the owner's Git credentials. Both routes compare with baselines made here, so T-010's second machine stays open. NFR-001 does not promise byte-identical images across platforms, so what a second machine must match is M6's to decide.

## Distribution contents

The other lanes check how each package behaves. The new `release-audit` lane, the gate's 17th, reads what would leave the machine: the wheel, the sdist and both plugins.

| Check | Wheel | Sdist | Claude plugin | Work plugin |
|---|---|---|---|---|
| No local folder, cache, report, baseline, spike or `settings.local.json` | Checked | Checked | Checked | Checked |
| `NOTICE.md`, the Python inventory, both font licenses and the rights manifest | Checked | Not required | Checked | Checked |

The Claude plugin's README and skill, the Work plugin's README and `NOTICE.md` must also state the private-use limit. A test installs the built wheel alone into a new environment, renders a Huawei view from outside the repository, and reads the private-use limit from that bundle.

## Fixes this found

| Finding | Effect | Fix |
|---|---|---|
| A local sdist held `.claude/settings.local.json` and every agent worktree, including whole copies of the repository. S07 had noted the settings file and left it | Anyone given that archive would get local permission settings and unrelated copies. CI's sdist did not have this, because its checkout has no such folder | The sdist now leaves out `.claude`, `.agents`, `doc`, `spikes` and `assets-source`, and the lane fails if any of them returns or a `.git` reference ships, which a build inside a worktree would otherwise do |
| No license inventory for the 20 Python packages installed at runtime, while `NOTICE.md` said it covered NFR-004 | A P0 requirement was unmet while a record said otherwise | `assets/THIRD-PARTY-PYTHON.md` is generated from the lock and package metadata. The `catalog-license` lane fails if a package, version or stated license differs |
| Deleting the `diagrams` icon terms from `NOTICE.md` passed every check | FR-052's dependency notices could vanish unnoticed | The lane requires the terms for each icon source |
| Nothing checked that the core makes no network or model call, and `model_api_required` is a literal | NFR-015 rested on reading the code | A test reads the imports of everything in `src`, and another refuses any in-process TCP connection during a render. The Graphviz subprocess is covered by the sandbox test. UDP, DNS and C-level sockets are not |
| Setting the command line's default mode to lenient passed every test | FR-006 could regress for both plugins | A test runs `validate` and `render` with no mode |
| Removing the relationship endpoint checks passed every test | FR-004's dangling edges were unguarded, though the code was right | A test covers both endpoints in both modes |
| Giving two relationship kinds one style passed every test | FR-029's "distinguish" was unguarded | A test requires every kind's style to be unique and to reach the drawing |
| No test edited a Kubernetes model and compared IDs | T-017's "preserve IDs across edits" was unguarded | A test does this on all six references |
| No check read the manifest's font version | FR-047 was short one named field | The manifest test reads it |
| The core's independence check caught only one word | FR-065's guard was narrow | It reads the imports, and refuses either host's settings by name |
| Nothing pinned the Work skill's lookup, assumption and validation steps | FR-061's steps could vanish unnoticed | A test pins each step |

Adding the inventory to `src` and these changes to `pyproject.toml` change the Work plugin's version digest, because that version identifies its content. The [Work check](S09-Work-validation.md) names the current one. Fable/High approved S09's code before this, and the changes to what the plugin ships are the added inventory file and that packaging setting.

The audit also corrected records. S08 said "host-independent" and "met in tests" for more than its tests showed, S08's provider section still said the owner had not inspected, and the M7 header still said the plugin cannot render. A test named "across runs and hosts" ran one process, and it is renamed.

## The P0 audit

Three fresh Claude Opus 5.5 agents read each requirement's exact text, opened the test that claims it, and ran it. They were told a document's claim counts for nothing, and they ran their own sabotage to see whether tests really fail. The root session then re-judged the 14 records that later fixes changed, and merged them into [the JSON](S10-p0-traceability.json).

The guard in `release-audit` fails if an ID is missing or extra, a named test is gone, a link is broken, a claim has no check, or an owner's acceptance names no decision or one that does not exist. **It cannot tell whether a test checks enough.** That judgment came from reading, and the review below is its only second opinion. It also does not check a test's lane against its file, and a caveat on an owner's acceptance sits in that record's owner note, where FR-042, FR-045 and FR-048 show theirs.

### Gaps the owner may want to decide

These are not blocked on Work, and they remain `partly` because closing them is a choice, not a check.

| IDs | Gap | Choice |
|---|---|---|
| FR-018 | The renderer never draws a resource's `properties`, so a declared replica count, Service type or port does not reach the image. A typed reference such as `secret_refs` draws only if a relationship repeats it, and no diagnostic says so | Draw them, which changes images the owner has passed, or disclose them, or accept this |
| FR-010 to FR-014 | Section 6 asks for positive and negative fixtures per item, and negatives exist per rule. FR-012 to FR-014 also rest on owner decisions, and FR-014's source conditions have no test | Accept per-rule negatives, or add fixtures per item |
| FR-022 | A subnet with no path to any network accepts any `network_ref`, the open P3-8 from S08 | Refuse it, or keep it as an unspecified fact |
| FR-029 | `management` edges have no rule, so any endpoints pass | Add a rule |
| NFR-009 | The clause "freeze in M0/M1" was not met, because the limits were set in M3 and M4, and memory and temporary limits are sampled | Reword the requirement, or accept this |
| FR-050 | A model has no version input, so type resolution uses the one bundled catalog | Reword the requirement, or accept this |

### Weak tests the audit named

These pass and do not fail for the reasons their names suggest. Behavior is covered elsewhere unless noted, and they stay as they are for now:

- `test_manifest_comes_last_and_only_on_success` checks no order, and other tests cover the behavior.
- `test_every_render_code_is_exercised_by_a_test` looks only for strings, which is the open P3-3.
- `test_t003_the_vpc_is_global_and_its_subnets_regional` and `test_t005_every_requested_kind_of_device_is_in_the_model` read fixtures only.
- `test_hostile_text_stays_literal_text` puts the same text in all four edge fields, so it cannot see a dropped field. Only the baselines caught one.
- `test_labels_are_literal_utf8_and_json_depth_ignores_braces_in_strings` escapes its Thai, and `test_thai_and_english_labels_survive_literally` is what covers raw UTF-8.
- The Thai reference test reads the manifest's font list, which names both fonts on every render. `check_fonts_used` is what fails a render without the bundled fonts.

## Validation

The local gate passes 17 lanes and 1,461 tests with 0 skipped, at Python 3.13.7, uv 0.13.0 and Graphviz 16.1.0.

| Lane | Tests |
|---|---|
| `schema-core` | 97 |
| `catalog-license` | 86 |
| `provider-semantics` | 447 |
| `render-security` | 230 |
| `render-smoke` | 300 |
| `visual-regression` | 65 |
| `claude-plugin` | 60 |
| `package-contract` | 137 |
| `release-audit` | 39 |

All 14 sabotage changes to the new checks failed a named test: a package dropped from the inventory, a changed license, deleted icon terms, an audit that stops looking for local folders or requiring notices, a report guard that ignores a gone test or a missing ID, a page that differs from its JSON, a removed report entry, a lenient default, unchecked relationship endpoints, two kinds sharing a style, a network import in the core, and a Work skill losing its lookup step. "The audit stops requiring notices" passed every test at first, which showed the list itself had no test, so one now pins it.

Actual CI [run 41783171328](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41783171328) passed 17 lanes and 1,453 tests at `65d800b`, on the runner, which is this same Mac, and its wheel matched the local build. A first watch of that run ended before the run did, so its digest was empty, and the script now refuses an empty one. CI for the review fixes is in the [review](S10-fable-review.md).

## Limits and what this does not establish

- **Nothing here is a Work result**, and no release exists. D-024 keeps the target as ChatGPT Work.
- **One machine.** The CI runner, the audit and the reproduction all ran on this Mac.
- **The report describes a head, not a release**, and a state can go stale when code changes. The guard catches missing tests, not weakened ones.
- **`met_with_owner` covers M4 images.** T-016 and the owner's inspection repeat in M6.

## Model and review

Claude Opus 5.5 (`claude-opus-5-5`) did this work, including the three audit agents. The strategy names Sol/Medium for M6, so this is a recorded substitution, and no model setting changed.

Under D-021, Claude Fable 5.1 / High [reviewed `b6997c6..65d800b`](S10-fable-review.md) in a fresh agent, sampling 33 of the 71 IDs. It found no state too generous and **requested changes** on the record and one sdist exclusion. They are fixed, and it **approved `debd754`**. It shares a vendor with the implementing models.

## Next steps

1. The owner decides the [gaps above](#gaps-the-owner-may-want-to-decide), or leaves them.
2. M5-04 and M6-01's two-machine run wait for the owner to come back to Work. M6-03 and M6-04 follow.
