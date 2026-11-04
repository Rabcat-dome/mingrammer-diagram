# Independent recheck of b3485c3

**Disposition: changes requested. Three confirmed P3 findings; no new P1 or P2 established.** The original failures are substantially addressed, but the source-archive audit still accepts broken packages and the finite-ID fix misses an error-response path. The gate passed **17/17 lanes, 1,550 tests, zero skipped, failures or errors**.

- Reviewer: OpenAI Codex, GPT-6 family. The exact served model suffix and configured reasoning effort are not exposed to this session. This report's filename does not attest to Astra or High. No delegated agents were used.
- Date: 2026-11-04, Asia/Bangkok.
- Base: `aefcdbcbf7157de92eecd7a50bd52d3c661c455f`.
- Head: `b3485c3136839080e5eeae87b413da651038ef9b`, verified as checkout HEAD on `codex/s11-review-fixes`.
- Checkout: `/Users/visarut.pha/Documents/source/easybuy/mingrammer-diagram`.
- Read the implementation diff before the fixes ledger. The prior reports and ledger were treated as claims, not proof. The probes below were written for this review; I did not use the earlier reviewers' probe scripts.
- No tracked file was edited, including during mutation checks. No commit, push, publication, CI trigger or installed-plugin modification occurred. No image was opened for visual inspection and no Huawei artwork was transmitted. The gate's local binary processing and packaging stayed local.

## Findings

### R1 — P3: an sdist missing a runtime-critical module still passes the new audit

**Location:** `scripts/release_audit.py:40` (`SDIST_REQUIRED`, through line 48), applied at `:123` and `:136`.

**Concrete failing state:** take the actual head sdist and omit only `src/cloud_architecture_diagrams/models.py`. Leave every other member intact and pair it with the unmodified, valid head wheel. This is an incomplete source distribution, not an altered application implementation or invalid test dependency environment.

**Confirmed by running:** `probe_release.py` constructs that archive under `astra-recheck-work/archives/missing-models/`. `release_audit.audit()` returns `passed: true`, `errors: []`, with 140 sdist members instead of 141. Building a wheel from that extracted sdist with the checkout's locked build tools succeeds. Extracting that wheel and importing its CLI in an isolated Python process fails:

```text
ModuleNotFoundError: No module named 'cloud_architecture_diagrams.models'
```

The CLI import resolves from the rebuilt wheel's extracted package, not the checkout's source. See `release-results.json` (`missing-models`, `missing-models-build`, `missing-models-cli`) and `sdist-build.log` under the work directory.

**Wrong result:** the audit certifies a source package that cannot run the CLI it is supposed to ship. The new seven-entry list closes the empty-tarball example, but does not establish the comment's claim that it checks what a build needs. This is a remaining verification hole, not evidence that the current unmodified sdist is broken.

**Why tests miss it:** `tests/test_release_audit.py:251` pins the incomplete list. The fake-archive helper supplies that list, and `test_the_audit_passes_when_each_archive_is_whole` accepts files containing only `b"x"`. Those tests establish names and nonzero sizes, not a complete working package. The clean wheel-install test and `scripts/repository_checks.py:package` protect the separately built wheel, not a wheel rebuilt from the sdist. No current gate lane builds and exercises that source archive.

**Fix direction:** compare the sdist's runtime source/assets against the intended inventory and/or rebuild and smoke-test the sdist in isolation. Merely adding `models.py` would leave the same hole for other essential modules.

### R2 — P3: stripping every archive member's first component lets files in another root satisfy required paths

**Location:** `scripts/release_audit.py:92–96`, especially `:94` in `sdist_sizes`.

**Concrete failing state:** in the actual sdist, move only `<package-root>/pyproject.toml` to `other-root/pyproject.toml`; leave all source files under their original root. The required project file is now outside the project it describes.

**Confirmed by running:** `probe_split_project.py` constructs `archives/split-project/`. The audit returns `passed: true`, `errors: []`. Building the extracted original package directory exits 1:

```text
ERROR Source .../cloud_architecture_diagrams-0.5.0a1 does not appear to be a Python project: no pyproject.toml or setup.py
```

Evidence: `split-project-results.json`. The archive's original project root has the source but no project definition; the other root has the project definition but no source.

**Wrong result:** the Fable suffix fix now matches paths exactly *after* normalization, but normalization discards each member's first directory independently. It never establishes that all required files share the package root. An unrelated root therefore supplies the missing project file. This remains a misplaced-file bypass of that fix.

**Why tests miss it:** the `archives()` helper at `tests/test_release_audit.py:268` always prepends the same `x-1/` root. The new misplaced-file tests vary paths only beneath that single root. Neither exercises multiple top-level directories. The normal archive passes because its layout is correct.

**Fix direction:** identify and validate a single distribution root before stripping it, then check required regular files beneath that root. Retain the exact-path and nonempty-file checks.

### R3 — P3: invalid-request replies bypass the finite-ID check and still emit Infinity

**Location:** `plugins/cloud-architecture-work/server/work_adapter/protocol.py:213–216`; the new `_valid_id` check is later at `:226–228`.

**Concrete input:** send either line to the actual stdio server:

```text
{"jsonrpc":"2.0","id":1e400,"method":false}
{"jsonrpc":"2.0","id":1e400}
```

**Confirmed by running:** `probe_adapter.py` starts the real server on `/usr/bin/python3 -I -B`, with a throwaway HOME. Both inputs receive:

```text
{"jsonrpc":"2.0","id":Infinity,"error":{"code":-32600,"message":"Not a JSON-RPC request."}}
```

A strict JSON parse rejects that response. The next ordinary ping succeeds and the server exits 0. An array ID combined with a non-string method is also echoed as an array. See `adapter-results.json`, `wire-9` through `wire-11`.

**Wrong result:** malformed requests still produce malformed JSON or invalid response IDs. The fix works when `method` is a string; the earlier invalid-request branch echoes the unvalidated ID. `send()` still allows nonfinite JSON numbers. This requires a malformed client frame, not an ordinary model-selected tool argument, and does not crash the server; hence P3.

**Why tests miss it:** `test_an_id_that_is_not_a_string_or_number_is_refused` supplies a valid string method (`tools/call`) for every invalid ID. The fractional-ID test also uses a valid method. Neither combines an invalid/nonfinite ID with the earlier invalid-request branch. The frame guard does not help: Python serializes `Infinity` without raising by default.

**Fix direction:** sanitize response IDs on every error path, preferably through one response-ID helper; cover invalid/missing method combined with nonfinite and non-scalar IDs.

## G1–G15 verdicts

“Fixed” means the reported behavior was closed in the exercised scope, not a proof against every input. “Partly fixed” identifies either a residual failure or, for G3, an intentional behavioral disposition rather than a prevention mechanism. Work evidence filenames below are under `reports/astra-recheck-work/`.

| ID | Verdict | Independent execution and assessment |
|---|---|---|
| G1 | Fixed | Read the complete workflow. `probe_release.py` enumerated the three exact upload globs after the gate: 29 text files, no PNG signature, PNG base64 prefix, `<svg` or `data:image` marker. Bundles/wheel are outside those globs. Read visual-regression failure reporting: it prints digest/change information and local paths, not image data. Did not upload or fetch anything. |
| G2 | Fixed | `probe_core.py`: generated legal grayscale/RGB/alpha PNGs at all supported depth combinations; all accepted. Bad filter, short/long pixel buffers and correctly checksummed garbage IDAT were refused. A real non-Huawei engine PNG passed, including IDAT splits of 1, 97 and 65,536 bytes. Fault injection after real rendering rejected garbage with no bundle; recompression published. A separate 32 MiB inflate attempt was refused with about 2.2 MiB traced peak allocation. The gate also decoded all reviewed baselines and passed visual regression. |
| G3 | Partly fixed; intentional disposition | Disclosure is fixed, transmission is deliberately retained by D-026. `probe_adapter.py` used synthetic sentinel bytes with `private_use_only: true`: `_published` still returned image content, and PNG/SVG reads still succeeded. No Huawei bytes were involved. README line 84 accurately describes this; there is no local-only switch. This is not an additional implementation finding under the recorded decision. |
| G4 | Fixed | `probe_adapter.py`: held actual `/bin/sleep` children between OS creation and return from the Popen hook for both core and setup. `stop_all` waited for release, then killed the child; both workers completed, and no subsequent core start occurred. Cancellation during the held start also completed without deadlock. An injected spawn exception released the lock. This verifies a finite held start, not a bound on an indefinitely blocked OS spawn. |
| G5 | Fixed | `probe_core.py`: fresh Azure models with two-region network, subnet, zone and security group declarations failed with `BOUNDARY_LOCATION_MULTIPLE` in both orders. Parent west plus located-in east failed; parent west plus located-in west passed. Environment/security-zone/cluster cases passed in both orders. No newly contradictory accepted placement established in these probes. |
| G6 | Fixed | Used the GKE Kubernetes fixture, not the fix's Azure case. Removed a Pod's `node_ref`, added a concrete scheduling edge, and mapped node/namespace/none views with the edge unselected and with the Node omitted. Node grouping used the assigned Node; omitted Node remained a `node: node-a` note; no false unspecified label. Conflicting Node assignments failed in strict and lenient modes. Existing gate tests also exercise complete rendered bundles. |
| G7 | Fixed | Fresh GCP compute/external trust-zone model retained `_provider.gcp`, put the trust group under `_provider.external`, and retained `security: trust` and membership metadata. Same-provider containment still worked. With the zone omitted from the view, its note is omitted as the selected-membership contract allows; the model/membership data remain. `core-results.json` and `supplement-results.json`. |
| G8 | Fixed | Injected the actual output-root fsync failure after rename: `RENDER_OUTPUT_WRITE_FAILED`, no surviving bundle or stage, then successful retry. Independently targeted the stage fsync before rename with the same clean failure. The first attempted pre-rename hook did not hit and was not counted; the corrected probe records one hit. |
| G9 | Fixed | Fresh environment chains: 15 model levels mapped to 16 provider-view groups; 16 and 17 model levels were refused. `none` grouping remained unaffected. The gate's provider-boundary render test passed, and disabling the depth check made that test fail at its expected assertion. The non-provider 16/17 test is a mapper unit test, not proof that its nested-subnet input is semantically valid. |
| G10 | Fixed | Own ordinary bundle: JSON/PNG/SVG reads succeeded. Replacing `model.json` with a hard link to an outside synthetic JSON file returned `ARTIFACT_UNSAFE` without the outside marker. Replacing it with a regular copy restored successful reading. The gate also tests refusal during rerender. No claim of protection against every concurrent filesystem mutation. |
| G11 | Fixed | Forced cancels immediately before and after `runtime.finished`, after removal from `calls`: both ignored, zero stale tokens, normal reply. A cancel while still in `calls` but after the toolbox result existed suppressed the reply and was cleared. Reviewed `calls_guard -> runtime.guard` ordering; Runtime has no inverse acquisition of `calls_guard`. |
| G12 | Fixed for the reported crashes | Real stdio process handled array/object/null/boolean IDs and malformed control-character JSON, then answered another ping and exited 0. Finite fractional IDs remained accepted. The remaining response-validation defect is R3/Fable-3, not a recurrence of the original server-termination failure. |
| G13 | Fixed | Read the real setup command and its new `--no-build`. Built this head's plugin locally and ran its actual setup offline against the review cache in a new private data directory: `ready: true`, Python 3.13.7, render probe passed. This independently confirms the current supported Mac lock installs with the flag; the gate's real setup also passed. `setup-result.json`. |
| G14 | Partly fixed | Independently constructed empty sdist and empty required wheel files were refused; the real wheel/sdist passed. However, an otherwise real sdist lacking `models.py` still passed and produced an unusable wheel: R1. |
| G15 | Fixed | Exercised all 24 combinations of positive/zero views, agreement, mismatches and expected-wheel True/False/None. Also ran the actual `main()` with clone/download/render operations stubbed locally: zero views returned 1; disagreeing successful routes returned 1; agreeing nonempty routes returned 0. Committed proof's source digest and wheel digest match this head/local wheel. No fresh remote reproduction was run. |

## Fable's four findings

Numbering below follows their order in `S11-fable-review.md`.

| Finding | Verdict | What I ran/read |
|---|---|---|
| Fable-1, over-broad multi-region refusal | Fixed | Fresh environment, security-zone and cluster boundaries located in west/east, both orders: valid. The regional/zonal control cases failed. Expanding `REGION_READ` back to include `any` in memory made the added positive test fail at its intended assertion. |
| Fable-2, required-path suffix matching | Partly fixed | Exact matching now rejects the original same-root misplaced-path cases; disabling exact matching makes the added misplaced-file test fail. But moving `pyproject.toml` to another archive root still passes normalization and audit, while an actual build fails: R2. |
| Fable-3, nonfinite request IDs | Partly fixed | `1e400`/negative overflow with a valid string method now return a valid `id: null` error. Invalid/missing method still echoes `Infinity`: R3, confirmed against the real server with a strict parser. |
| Fable-4, undocumented provider depth allowance | Fixed | `doc/design/core-contract.md:118` explicitly says 16 drawn levels and 15 model levels with the provider box. Read together with `graph.py:654–659`, the gate's depth test, and the independent 15/16/17 mapping results. |

The extra busy-answer change also passed the gate and an independent nine-call probe: eight held calls ran, the ninth got `TOO_MANY_CALLS`, all accepted calls eventually replied. The skill row names both capacity and render contention.

## Do the tests fail for their stated reasons?

The gate passed all new tests. I additionally disabled nine behaviors **in process memory**, in separate Python/pytest processes. No tracked source mutation was used. Each selected test failed with an assertion about the target behavior, with no collection/import error. Evidence: `check_test_reasons.py`, `test-reasons.json`, and the nine `*-mutant.log` files.

| Behavior disabled | Observed test failure |
|---|---|
| Pixel decoding | Garbage IDAT no longer yielded `RENDER_PNG_INVALID` |
| Multi-region refusal | Expected `BOUNDARY_LOCATION_MULTIPLE` absent |
| Exemption for `any`-location boundaries | Positive environment model now had an error |
| Scheduling-edge membership | Pod parent was the cluster instead of its Node |
| Provider separation | GCP resource was enclosed by the external trust/provider chain |
| Depth check | Over-limit provider view lacked the expected rejection |
| Empty archive-member check | Empty wheel produced no expected `is empty` errors |
| Exact required paths | Misplaced README no longer yielded `sdist: lacks README.md` |
| Reproduction agreement/coverage predicate | A false proof was accepted |

For the other changed tests I inspected their bodies and the independent execution evidence rather than claiming a full mutation campaign. The held-start tests actually create children; the final-sync test asserts its injection fired; the memory test measures peak allocation; the equal-size illegal-depth test isolates the depth rule. Their names are supported within those scopes. The setup test checks the command flag, not an attempted backend build; real successful setup supplies the complementary evidence. The multi-region “keeps its members” test checks validation, not picture contents. The “archive is whole” test is materially weaker than its name: its `b"x"` placeholders prove only the minimum path/size checks, as R1 demonstrates. The finite-ID tests are valid but omit R3's earlier branch.

## Changed traceability records and decisions

Compared all **nine changed records** with the corresponding requirement text and inspected the **89 distinct named test bodies** across those records. The extracted bodies are retained in `trace-dedup-bodies.txt`; `changed-trace-test-bodies.txt` also retains the complete changed records. The structural guard returned no errors. Newly added checks name existing tests in the correct gate lanes.

| Record | Assessment |
|---|---|
| FR-021, `met_with_owner` | Provider containment/notes tests directly support the repaired grouping behavior. D-023 remains acceptance of the named 26 views, not every future model. No new state objection from the G7 probes. |
| FR-040, `met` | Correctly checksummed undecodable pixel streams are now rejected before publication. Real engine and baseline PNGs still pass. This supports the repaired valid-output claim; it is not an exhaustive PNG-specification audit. |
| FR-043, `met` | New decode and final-sync tests directly address unusable/partial success. Independent post-rename failure leaves no bundle. Existing adapter integrity/status tests support their own boundaries. |
| FR-046, `met` | Provider wrapper now counts toward the documented nesting limit. Size-limit tests retain actionable split diagnostics. Non-provider depth coverage is explicitly mapper-level. |
| FR-048, `met_with_owner` | New scheduling and region tests address semantic fidelity, and the Fable multi-region fix restores the positive cases. These tests do not establish official visual resemblance; the owner note accurately leaves that with D-023 and the future T-016 repeat. No Huawei visual review performed here. |
| NFR-003, `met` | The new hard-link test supports the reader's added `st_nlink == 1` restriction, in addition to existing path/symlink/SVG confinement tests. Good ordinary-file reads passed. This does not establish universal filesystem-race resistance. |
| NFR-004, `met_with_owner` | Existing inventory/license/blocker tests bear on this requirement. The new CI-upload test supports the surrounding private-use handling, not license clearance itself. D-018's scoped exception and O-002 public-distribution block remain explicit. D-026 disclosure does not confer redistribution rights. |
| NFR-009, `partly` | Held-start and bounded-decode tests support the additions. Its existing numeric-freeze, sampling and Python-versus-engine limitations remain material, so retaining `partly` is appropriate. No bounded OS-spawn time is demonstrated by a lock around Popen. |
| NFR-010, `met` | Decode-before-manifest and final-sync cleanup are now exercised; independent failure injection agrees. Existing collision/checksum tests address separate clauses. R1/R2 concern release archives, not render-bundle atomicity. |

**D-025 (`decisions.md:33`):** consistent with the review ledger and model-strategy text: additional GPT reviews supplement the milestone review policy. Nothing in the code/README establishes the actual served models or effort settings of historical sessions; those remain provenance claims in the records. This review does not independently authenticate those host records.

**D-026 (`decisions.md:34`):** the code retains automatic previews below its size cap and explicit PNG/SVG reads; README line 84 discloses that they reach the host and that no switch disables them. The synthetic private-use probe confirms this boundary without sending icons. The decision clearly attributes the defaults to the Claude session and says the owner's “fix it” did not explicitly address them. The workflow retains `retention-days: 14`; actual pre-existing GitHub artifacts and their expiry were not inspected, fetched or deleted. This decision does not override the present user's prohibition on transmitting artwork.

No additional overstatement was established in these nine records for the repaired cases. R1/R2 mean the broader release-check claim that the sdist is usable is still too strong; they should not be treated as a license to close packaging acceptance based on this audit alone.

## Execution, isolation and limits

Commands ran in the requested checkout. The required gate command was:

```sh
uv run --frozen python scripts/quality_gate.py
```

It ran with `HOME`, `TMPDIR`, uv/Ruff/mypy/pytest caches redirected beneath `reports/astra-recheck-work/`. Result: exit 0, 17 passed lanes, 1,550 tests, zero skips/failures/errors, Python 3.13.7, Darwin arm64, Graphviz 16.1.0. Console: `gate-console.log`. The gate hardcodes its artifact paths under `reports/`; after testing, those generated logs/XML/JSON, wheel/sdist and render-output directories were relocated beneath `astra-recheck-work/gate-artifacts/`, with `gate-relocation.json` recording the move.

The gate records `working_tree_dirty: true` and `source_ref: null`. This is explained by HOME isolation: without the owner's global excludes file, `git status` shows the pre-existing untracked `.claude/` directory. With the original HOME, status was and remains empty. All **208 recorded source digests** match files at the requested head. This is a passing local check, not a fabricated clean-source or CI attestation.

Independent scripts executed:

- `probe_core.py`: region semantics, graph memberships, depth, PNG parsing and real engine-output faults, publication sync/retry.
- `probe_adapter.py`: real stdio malformed frames, deterministic child-start/stop/cancel interleavings, spawn-error lock release, late cancellation, synthetic private-use preview, ordinary versus hard-linked artifacts, nine-call capacity.
- `probe_release.py`: real/synthetic archive audits, missing-module sdist rebuild and CLI import, proof predicate combinations, source/wheel digest checks, upload-glob content scan, changed trace extraction.
- `probe_release_main.py`: actual reproduction `main()` exit decisions with external operations stubbed; no network clone.
- `probe_supplement.py`: corrected pre-rename sync injection, additional archive-layout and bounded-inflate checks.
- `probe_split_project.py`: split-root archive audit and failed actual build.
- `check_test_reasons.py`: nine in-memory behavior removals followed by the existing named tests.
- `scripts/build_work_plugin.py --output reports/astra-recheck-work/built-plugin`, then that package's real `scripts/runtime.py setup` with `UV_OFFLINE=1` and a fresh review-owned runtime directory. Setup returned ready and passed its real render probe. Plugin version: `0.1.0-alpha.1+03840aacc866`.

All probe results and logs are retained beside the scripts. Archive probes and existing archive tests were run before the gate's fixed output paths were relocated; rerun the gate first to recreate `reports/dist` when replaying those scripts. Synthetic private-use preview bytes were never icon bytes.

Read: the changed implementation/workflow/tests, the three prior reviews and fixes ledger; core contract; relevant requirement rows/semantic context; mapping, PNG validation/publication and semantic ancestry paths; full Work runtime/protocol/artifact reader and the relevant toolbox preview/read paths; release audit, reproduction script, gate, package builder and wheel-content checker; the changed trace records and named test bodies; D-025/D-026 and their related README/policy text.

Not run/read: actual ChatGPT Work acceptance or host transport/storage; CI or remote artifacts; a second machine; a fresh remote clone/Python-download reproduction; a complete re-audit of the 62 unchanged trace records; an exhaustive read of all unchanged source/fixture code; an independent provider-documentation/license audit; broad fuzzing; a complete mutation campaign; all OS/filesystem race interleavings or an indefinitely stalled spawn. No baseline or generated image was visually opened. PNG ancillary/unknown-chunk experiments did not demonstrate an unusable image in the available local decoder, and are not promoted to a new finding. The first pre-rename sync attempt and the README-only split-root experiment likewise are not claimed as confirmed failures; the corrected probes above provide the actual evidence.

The original and final normal-HOME `git status --porcelain=v1` outputs are both empty, and the tracked binary diffs are identical and empty. Scratch output and this report are ignored by Git.

**Disposition: changes requested — R1 P3, incomplete sdist accepted; R2 P3, required files accepted from a different archive root; R3 P3, invalid-request branch still emits nonfinite IDs.**

Report: `reports/astra-recheck-b3485c3.md`.
