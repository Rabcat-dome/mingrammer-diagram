# Independent review of aefcdbc

**Disposition: changes requested.** Three P2 findings. No new P1 finding established.

- Reviewer: OpenAI Codex, GPT-6. The exact served model suffix and configured reasoning-effort setting are not exposed to this session; neither an Astra suffix nor a High setting is independently verified. This is an independent OpenAI review, with no delegated agents.
- Date: 2026-11-04, Asia/Bangkok.
- Base: `556945952fef1461c03451ba76ed3f652909edde`.
- Head reviewed: `aefcdbcbf7157de92eecd7a50bd52d3c661c455f`; the checkout's HEAD matched.
- Stopping point: completed the requested sequence through **4, release checks and sampled traceability**. This was a targeted review, not an exhaustive audit of every changed file or every requirement.
- The first pass examined code before the Fable reports. Independent observations were saved in `reports/astra-review-work/independent-observations.txt` before opening those reports. The M7 and S06–S10 Fable reviews were subsequently read to distinguish existing findings.

## Findings

### F1 — P2: a PNG with no decodable pixels is published as a complete bundle

**Location:** `src/cloud_architecture_diagrams/render/checks.py:231–236`, in `check_png`; publication follows the check in `render/__init__.py`.

The verifier counts compressed IDAT bytes and checks chunk CRCs, but never decodes the pixel stream. Nonempty IDAT data plus an IEND chunk is sufficient. A CRC authenticates neither the zlib stream nor the required scanlines.

**Concrete failing state:** let the real renderer produce the SVG and PNG for a single `external.system.other` node. Preserve the PNG's real IHDR dimensions, replace all pixel data with one IDAT chunk containing `b"not a zlib stream"`, recompute its CRC, and append a valid empty IEND chunk. The SVG, font log and all other output remain untouched.

**Confirmed result:** `render_model` returns `rendered=true`, no diagnostics, and a six-file bundle whose manifest says `status: complete`. Decoding that IDAT with zlib fails with `incorrect header check`. The manifest checksums faithfully describe an unusable image. This violates the valid-PNG and verified-output claims even though staging and rename are atomic.

Reproduction: `uv run --frozen python reports/astra-review-work/probe_png.py`. The saved outcome is `reports/astra-review-work/png-result.json`, and the malformed bundle remains locally under `reports/astra-review-work/png-renders/`.

**Confirmation boundary:** this is an end-to-end output-fault injection around a real Graphviz run. It establishes the validation/publication defect; it does **not** establish a hostile JSON input that makes an unmodified Graphviz emit that stream, or a sandbox escape.

**Why the tests miss it:** `tests/test_render_security.py:539–565` corrupts signatures, lengths, dimensions or CRCs, not a correctly framed PNG with an invalid compressed stream. Its `rebuilt_png` helper at lines 568–575 even uses `IDAT=b"x"` as a supposedly valid image for size tests. `test_every_fixture_view_produces_a_complete_bundle` at `tests/test_render_smoke.py:87` reuses `check_png`, so it is not an independent decoding check. Reference-image comparisons cover normal outputs, not this failure state.

**Fix direction:** decode and validate PNG pixel data with bounded output allocation before publication, including stream completion, scanline sizes and legal header/chunk structure. Add correctly checksummed invalid/truncated IDAT cases. Keep the file and pixel bounds in force during decoding.

### F2 — P2: shutdown can miss a process created before registration

**Location:** `plugins/cloud-architecture-work/server/work_adapter/runtime.py:252–262`, together with `runtime.py:224–237` and `protocol.py:258–264`.

`run_core` creates a detached child and only afterward registers it under `self.guard`. `stop_all` takes a single snapshot of registered children and returns after stopping those children. The server then exits without joining its daemon call workers. A worker that is suspended between process creation and registration is absent from that snapshot. The `self.stopping` check in `_register` helps only if the worker survives long enough to reach it.

**Concrete failing state:** a tool call is starting its child when stdin closes or the server receives its shutdown signal. Pause the call worker immediately after the OS creates the child, but before `_register`; run `stop_all` and let the server exit.

**Confirmed result:** the server exits 0, `stop_all` reports no registered processes, and the detached child remains alive. The probe explicitly killed its surviving child afterward. The same create-then-register pattern exists in setup at `runtime.py:376–404`, where an orphan could keep installing after the host is gone.

Reproduction: `uv run --frozen python reports/astra-review-work/probe_shutdown.py`. Result: `reports/astra-review-work/shutdown-result.json`, including `child_alive_after_server_exit: true`.

**Confirmation boundary:** a deterministic scheduling hook holds the actual `run_core` lifecycle at the vulnerable interval and substitutes a harmless sleeping process for the core. No production code was edited. The orphan is confirmed; a naturally occurring race in the actual Work app, a continuing real installer, and leftover real-render scratch from this exact interval were not demonstrated.

**Why the tests miss it:** `test_shutdown_stops_a_running_core` (`tests/test_work_plugin.py:1609`) waits for the stand-in's PID before closing. The real-core cleanup test at line 1638 waits for a request directory. These exercise established calls, not the interval before registration. Early-cancel handling likewise assumes the worker eventually reaches `_register`; server exit removes that assumption.

**Fix direction:** coordinate creation/registration with shutdown so shutdown cannot finish while a spawn is in progress, refuse new starts once stopping begins, and wait for the relevant workers to finish cleanup before exiting. Add a deterministic test at this interval for both calls and setup.

### F3 — P2: a cross-provider security membership changes the enclosing provider

**Location:** `src/cloud_architecture_diagrams/render/graph.py:296–305` and `graph.py:609–618`.

`_container` accepts a selected security boundary regardless of its provider. `_under_providers` then adds provider boxes only around parentless groups and nodes. A resource already nested in a boundary of another provider never receives its own provider box. `_implies_another_scope` protects explicit administrative scopes, but does not protect provider identity.

**Concrete input:** a GCP `gcp.compute.compute_engine` resource `app`, with `placement.security_boundaries=["trust"]`; an `external` `security_zone` boundary `trust`; and a provider-grouped view selecting both. There are no administrative scopes or other placements. This is a declared security membership, not a declaration that the compute instance belongs to External.

**Confirmed result:** strict validation passes without diagnostics and a normal, unmodified render publishes successfully. Its tree is `_provider.external -> trust -> app`, while `app.provider` remains `gcp`. There is no `_provider.gcp` group. The image encloses the Compute Engine node inside the “External” provider boundary. Security membership has therefore changed the visual provider context.

Input: `reports/astra-review-work/cross-provider-trust.json`. Reproduction: `uv run --frozen python reports/astra-review-work/probe_semantics.py`; the `cross-provider-trust` entry in `semantics-results.json` records the tree and successful bundle path under `reports/astra-review-work/renders/`. This case uses no Huawei assets.

**Why the tests miss it:** the ownership cases at `tests/test_render_smoke.py:892` and `tests/test_references.py:235,328` exercise administrative scopes within one provider. The hybrid tests at `tests/test_references.py:534,561` use a separate trust zone for each provider; they never give a resource a cross-provider zone. Checking node IDs, type icons or the set of providers on that fixture does not assert that every node's enclosing provider agrees with its declared provider.

**Fix direction:** preserve each entity's provider context in provider grouping. A cross-provider security membership can remain an explicit note or use a representation that does not imply a different provider. Test both the resulting ancestry and preservation of the security membership.

## Release and traceability sample

The gate passed with the defects above. Its traceability guard (`scripts/release_audit.py:132–176`) checks IDs, state vocabulary, referenced test existence, evidence links and owner-decision IDs. It does not prove the assertion made by a named test. I opened relevant test bodies, rather than treating their names as evidence; additional extracted bodies are in `reports/astra-review-work/sampled-test-bodies.txt`.

| Record in `doc/project-management/evidence/S10-p0-traceability.json` | Assessment against requirement text and tests |
|---|---|
| **FR-040, line 1258, `met`** | Too generous: the requirement at `doc/requirements/requirements.md:113` promises valid SVG/PNG. F1 publishes an undecodable PNG. The named invalid-PNG test omits this state. Mark partial until fixed. |
| **FR-043, line 1428, `met`** | Too generous for its usable-artifact/no-partial-success clause (`requirements.md:116`). F1 returns success and an unusable PNG. File presence, digest checks and injected missing-file tests do not establish usable pixel content. Mark partial until fixed. |
| **NFR-010, line 2808, `met`** | Too generous for “only after all requested outputs validate” (`requirements.md:238`). F1 demonstrates the missing validation. The atomic write behavior itself was not disproved. Mark partial until fixed. |
| **FR-021, line 870, `met_with_owner`** | Too generous as a general claim of appropriate provider grouping (`requirements.md:99`). F3 gives the wrong enclosing provider. D-023 accepts 26 specific reference views; it does not accept this unseen counterexample. Keep that acceptance, but mark the overall requirement partial until fixed. |
| NFR-003, line 2426, `met` | No additional overstatement established in the sampled traversal/symlink and SVG cases. Opened the bundle/root symlink tests and output-link refusal test. This is not a proof against every local filesystem race. |
| NFR-004, line 2514, `met_with_owner` | No new state objection in the sample. The requirement explicitly permits the D-018 private-use exception. Opened notice/upload-marker checks and read D-018/D-019. This review grants no distribution rights. |

NFR-009 is already `partly`; its line 2803 statement that kills and cleanup pass needs the F2 qualification. I did not upgrade that existing partial state into a separate duplicate finding.

I read `scripts/reproduce_core.py` and the committed reproduction-proof test. I did not rerun the fresh GitHub clone/Python-download reproduction. The source-digest omissions are already S10 Fable P3-A and are not reported again. I also rejected my initial concern that merely changing a wheel notice would evade the whole gate: `scripts/repository_checks.py:148–176` compares wheel contents with source digests, beyond the release audit's filename checks.

## Execution and coverage

1. **Render isolation:** read the six requested modules, plus the render entry point, data validation/models, CLI signal handling and DOT construction. The existing security lane ran, including hostile text, path/symlink rejection, sandbox checks, limits and cleanup. F1 is the additional output-verification finding. No hostile-model route to arbitrary execution, external writes, symbolic-link traversal or active SVG was established.
2. **Work adapter:** read all four requested adapter modules, the runtime script and builder. The package-contract lane ran. Inspected fixed artifact names, closed arguments, command construction, setup's locked sync, per-process render locking, cancellation/termination and content-free logging. F2 is the additional shutdown finding. No tool-argument route to arbitrary filesystem reads or arbitrary package selection was established.
3. **Picture/model fidelity:** read graph mapping, drawing, semantics and rules data; examined the relevant base-to-head semantic changes and representative tests. F3 reproduced through a real render. A supplementary two-region relation-order probe also flipped validation, but its first-match ancestor resolver predates this range; it is not asserted as a newly introduced finding or a full base-runtime reproduction. Did not manually inspect every reference image.
4. **Release checks:** read release audit, reproduction script, the traceability records, requirement rows, selected owner decisions, package-content checks and named tests above. Completed the sample and stopped here. No claim that all 71 traceability records were independently verified.

Commands and evidence:

- `uv run --frozen python scripts/quality_gate.py`: first run **passed 17/17 lanes, 1,461 tests, zero skipped/failures/errors**. Console: `reports/astra-review-work/gate-console.log`. Python 3.13.7, Darwin arm64, Graphviz 16.1.0.
- A second run of that same gate, with `TMPDIR`, pytest's cache, Ruff's cache and mypy's cache under `reports/astra-review-work/`, also **passed 17/17 lanes, 1,461 tests, zero skipped/failures/errors, exit 0**. Its console is `gate-reports-only-console.log`; `reports/quality-gate.json` and the lane XML reports hold this final run. The first run's retained pytest temporary directories were relocated beneath `reports/astra-review-work/initial-gate-tmp/`; provenance is in `relocated-gate-temp.json`.
- Ran the three additional local probe scripts named in F1–F3. None changes tracked source. Fault injection exists only in the review processes/scripts under `reports/`.
- The gate includes real local sandbox/Graphviz tests, package building, isolated package installs and release audit. It is a local result, not a new CI run or a clean-working-tree release attestation.

**Not run/read:** actual ChatGPT Work acceptance, host UI/account transport, `work_host_check.py` as a separate command, a second machine, the full fresh-clone reproduction, a new official-provider/documentation web audit, broad fuzzing, or a full re-review of the base. Did not inspect `.claude/worktrees`. Did not use the uncommitted Work validation record as evidence. No Huawei icon or image was displayed through a remote tool or sent anywhere by this review; the gate's Huawei rendering/package fixtures remained local. Nothing was committed, pushed, published or installed into the owner's live plugin.

The checkout had five pre-existing modified documentation files at entry: `ACTIVITY-LOG.md`, `HANDOFF.md`, `evidence/S09-Work-validation.md`, `evidence/S09-work-plugin.md`, and `milestones.md`, all under `doc/project-management/`. They were left untouched. After the second gate, the tracked-file binary diff still matched the entry snapshot exactly. All three finding locations are in files added after the specified base. Existing Fable findings and accepted deferrals are not counted as new findings here.
