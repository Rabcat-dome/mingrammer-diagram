# Independent recheck of the S11 fixes at 3aa566d

**Disposition: changes requested.** One P2 and three P3 new findings. G1 to G15 are each fixed for the case the reviewers named; the P2 is a side effect of the G5 fix that refuses models that were valid at the base and were never order-dependent.

- Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), through Claude Code. The reasoning-effort setting is not exposed to this session and is not stated here.
- Date: 2026-11-04, Asia/Bangkok.
- Base: `aefcdbcbf7157de92eecd7a50bd52d3c661c455f`. Head: `3aa566dd7412a5f769f39827b6b9bff28c0817a5`, on `codex/s11-review-fixes`, in the checkout `/Users/visarut.pha/Documents/source/easybuy/mingrammer-diagram`. The checkout was clean on entry and is clean on exit.
- No prior context on this project. I read the diff (`git diff aefcdbc 3aa566d`) and the two GPT reports before the "Fixes" section of `S11-gpt-reviews.md`, then treated that section as claims. No tracked file was edited except transiently during the sabotage pass below, and each was restored through `git checkout --` before the next step; `git status` is empty.
- No Huawei image was opened or sent anywhere. The one real engine image I processed as bytes is from `tests/fixtures/core-valid.json`, which holds GCP types only. Every probe ran under a throwaway `HOME` beneath `reports/fable-recheck-work/`.

## G1 to G15

"Own probe" means an input I wrote, not the test the fix added. Probe scripts and their output are under `reports/fable-recheck-work/` (`probe_*.py`, `*.txt`, `sabotage.json`).

| ID | Verdict | What I ran and saw |
|---|---|---|
| G1 | Fixed | Read `.github/workflows/quality-gate.yml`: one upload step, `path` is `reports/*.log`, `reports/*.xml`, `reports/*.json`. After the full gate, listed every file those globs match (29 files, 29 KB largest) and grepped them for `\x89PNG`, `iVBORw0`, `<svg` and `data:image`: no hit. Read `tests/test_visual_regression.py` to see what a failing run would print: its asserts compare digests and change lists, not image bytes, so a failing run's log does not carry icon data either. `reports/quality-gate.json` holds lane names, timings and digests only. I did not trigger CI or fetch an artifact. |
| G2 | Fixed | `probe_g2_png.py`: took the real engine PNG (617x1025, RGBA 8-bit, chunks bKGD, IDAT..., IEND, all five filter types in use) and sent 25 crafted files through `check_png`. Refused: garbage IDAT with a valid CRC, one row short, one byte long, filter 7 in a middle row, trailing bytes inside the IDAT after the stream end, two zlib streams back to back, raw deflate, a stream needing a preset dictionary, palette, Adam7, a second IHDR. Accepted, as they should be: the real image, `tEXt` before IDAT, `tEXt` after the last IDAT, IDAT split into 64-byte chunks, an empty IDAT between IDATs, level 0 and level 9 recompression, 16-bit RGB, 1-bit gray, gray+alpha, 8-bit RGB at the same size, rows using filters 0 to 4. End to end with the real engine's output replaced after it ran: garbage IDAT and an illegal filter leave nothing published (`RENDER_PNG_INVALID`, exit 4, empty tree); a level-9 recompression publishes. The gate's render-smoke, visual-regression and `test_every_reviewed_image_passes_the_decode` (26 baselines) passed, so no real engine image is refused. |
| G3 | Addressed by decision, not by code | D-026 keeps the preview and file reads. Read `tools.py` `_published` and `read_artifact`: the preview is returned for any PNG under `MAX_PREVIEW_BYTES` (5 MiB) with no check of `rights`, and `read_artifact` returns `diagram.png` and `diagram.svg` bytes for any bundle. The README's new paragraph states exactly that, and "no setting turns this off" is true of the code. |
| G4 | Fixed | `probe_g4_g11_runtime.py` with a stand-in `Popen` that creates a real `/bin/sleep 60` child and then sleeps 1 s before returning: `stop_all()` called in that window blocked 1.01 s, the child was dead afterwards, the call returned `cancelled=True`, status -15. A `run_core` after stopping started no child. The same window in `setup()` returned `RUNTIME_SETUP_INTERRUPTED`, no failure file, no marker. `cancel()` issued during the held start did not deadlock (returned after the start, child dead, no stale early token). Lock order: `Server.cancel` takes `calls_guard` then `runtime.guard`; nothing in `Runtime` takes `calls_guard`, so no inversion. |
| G5 | Fixed for the reported case; see P2 below | `probe_g5_semantics.py` at head and at base (base source extracted to scratch, `PYTHONPATH`). Azure VNet `located_in` two regions in either order, and parent region A plus `located_in` region B: head gives `BOUNDARY_LOCATION_MULTIPLE` in all orders; base gave nothing. Parent A plus `located_in` A, and an AWS security group in VPC(A) plus `located_in` A, stay valid. But see P2: the rule also refuses `environment` and `security_zone` boundaries (location `any`), which were valid at base in both orders, with members in both regions. |
| G6 | Fixed | `probe_graph.py`: Azure fixture with `node_ref` removed and a `scheduling` edge added. Pod nests under `aks-node-1` whether or not the edge is selected in the view; no `node: unspecified`; in the namespace view the note reads `node: node-1`; with the Node left out of the view the Pod sits under the cluster, keeps the note and `view.json` declares `node: [aks-node-1]`. Two edges to two Nodes, or `node_ref` plus an edge elsewhere: `K8S_NODE_ASSIGNMENT_CONFLICT`, and nothing renders in strict or lenient mode, so the mapper's last-wins dictionary is never reached with a conflict. A Node-to-Pod edge is `K8S_RELATIONSHIP_INVALID`. |
| G7 | Fixed | `probe_graph.py`: GCP Compute Engine in an `external` security zone, provider view: chain `['_provider.gcp']`, note `security: Shared trust zone`, `trust` under `_provider.external`, `view.json` memberships keep `security: [trust]`. A same-provider zone still nests the resource. `network` grouping leaves the note and draws no zone (the zone is not a network group), as before. The gate's `test_every_provider_box_holds_only_that_provider` passed over all reference fixtures and visual regression is unchanged. |
| G8 | Fixed | `probe_g8_sync.py`: `os.fsync` made to fail only on the root after the bundle name is in it (`ENOSPC`). Result `RENDER_OUTPUT_WRITE_FAILED`, `rendered=False`, tree empty (no bundle, no `.part`), and a retry publishes. A failure on the stage sync before the rename still leaves nothing. |
| G9 | Fixed | `probe_graph.py`: provider view with 15 nested `environment` levels renders with 16 drawn levels; 16 and 17 model levels are `RENDER_GROUP_DEPTH_LIMIT`. Network grouping: 16 levels map, 17 refused. A single-provider view does add the provider box, so the 15-level bound is right for every provider view. |
| G10 | Fixed | `probe_g10_links.py`: core render into the throwaway Work folder (all six files `st_nlink == 1`), then `model.json` replaced by a hard link to a file outside the root: `read_artifact` gives `ARTIFACT_UNSAFE` and the outside text is not in the answer. A second link made inside the bundle to `manifest.json` is refused the same way; `list_bundles` then reports that manifest unreadable. An APFS clone (`cp -c`) leaves `st_nlink == 1` and the read works, so a good bundle is not refused by cloning. |
| G11 | Fixed | `probe_g4_g11_runtime.py`: a cancel delivered after the call left `calls` and before `runtime.finished()` is ignored, leaves no early token, and the call is answered; a cancel delivered while the call is still in `calls` but its process has ended sets the token and `finished()` clears it (0 tokens after, no answer, which is the protocol's rule). A cancel for an unknown ID leaves no token. |
| G12 | Fixed | `probe_g12_server.py` against the real server (`/usr/bin/python3 -I -B server/main.py`, Python 3.9.6, throwaway HOME): array, object, boolean and null IDs get `-32600`; bad JSON with a control character or an escape in the ID gets `-32700` with `id: null`; cancels naming an array or with list params are ignored; params or arguments that are not objects, a non-string tool name, a non-string method, 100,000 nested arrays, a bare scalar and `{}` all get a reply; a `ping` succeeded after each, and the server exited 0 on EOF. See P3 on `1e400`. |
| G13 | Fixed | Read the command. Parsed `plugins/cloud-architecture-work/uv.lock`: 43 packages, none sdist-only, each with a `py3-none-any` or macOS arm64 wheel. `uv sync --dry-run --offline --locked --no-dev --no-install-project --no-build --python 3.13.7` against the plugin project (which carries the root `pyproject.toml`) resolved with exit 0. The gate's package-contract lane ran the real setup with `--no-build` and passed. |
| G14 | Fixed for the named cases; see P3 below | `probe_g14_g15_audit.py`: an empty sdist gives seven `lacks` errors; a wheel of empty files gives six `is empty` errors; whole archives pass; the gate's real `reports/dist` passes (141 sdist entries, 86 wheel entries). But names are matched by suffix, so misplaced files satisfy it (P3). |
| G15 | Fixed | `proof_passed` on every combination: `views: 0`, `routes_agree: False`, a mismatch, or `wheel_matches_expected: False` fail; `None` for the wheel passes. The committed proof passes it, its `source_digest` equals this checkout's, and its `wheel_sha256` equals the wheel the gate just built. `src`, `scripts` and `plugins` are identical between `9fb199d` and `3aa566d`. |
| `busy` | Fixed | Read the SKILL.md row and `test_too_many_calls_at_once_get_a_stable_busy_answer`; both causes are named. |

### Do the new tests fail for the reason their names give

`sabotage.py` undid one fix at a time by a text edit, ran only that fix's named test, and restored the file. All 13 failed on the assertion that names the behaviour, never on an import or fixture error (`reports/fable-recheck-work/sabotage.json`):

| Undone | Test | Failure line |
|---|---|---|
| G7 `_implies_another_provider` filter | `test_a_foreign_security_zone_keeps_a_resource_in_its_own_provider` | `['trust', '_provider.external'] == ['_provider.gcp']` |
| G9 provider-box allowance | `test_the_depth_limit_counts_the_provider_box` | `[] == ['RENDER_GROUP_DEPTH_LIMIT']` |
| G6 `or scheduled` | `test_a_scheduling_edge_alone_places_a_pod_on_its_node` | `'aks-cluster' == 'aks-node-1'` |
| G5 `spans_regions` call | `test_a_boundary_in_two_regions_fails_in_either_order` | `'BOUNDARY_LOCATION_MULTIPLE' in set()` |
| G2 `_check_pixels` call | `test_pixels_that_do_not_decode_block_the_bundle` | `[] == ['RENDER_PNG_INVALID']` |
| G8 `stage = name` | `test_a_failed_sync_after_the_rename_leaves_nothing_published` | bundle left in tree |
| G14 `empty_required` | `test_a_wheel_of_empty_files_fails_the_audit` | expected `is empty` errors, got none |
| G15 predicate | `test_a_reproduction_proof_fails_unless_it_proved_something` | `True is False` |
| G11 order of pop and `finished` | `test_a_cancel_arriving_as_a_call_ends_leaves_no_token` | `tokens: 1, answered: False` |
| G12 `_valid_id` in `handle` | `test_an_id_that_is_not_a_string_or_number_is_refused` | `-32603 == -32600` (the frame guard alone keeps the server up; the ID check gives the right code) |
| G4 start inside the lock | `test_shutdown_stops_a_core_caught_between_its_start_and_its_registration` | child alive after `stop_all` |
| G10 `st_nlink` check | `test_a_hard_link_in_a_bundle_is_not_read` | the read succeeded (`KeyError: 'code'`) |
| G13 `--no-build` | `test_setup_refuses_a_source_build` | flag absent |

## New findings

### P2 — The G5 rule refuses multi-region `environment`, `security_zone` and `cluster` boundaries that were valid at the base and never order-dependent

`src/cloud_architecture_diagrams/semantics.py:166-173` (`spans_regions`) and `:292-295`; message and remedy in `catalog_data/rules.json:18`; contract sentence in `doc/design/core-contract.md:54`.

`spans_regions` runs for every boundary kind. Kinds whose catalog location is `any` (`environment`, `security_zone`, `cluster` for every provider, per `catalog().group_type(...).placement.location`) may be `located_in` several regions, and nothing consults their region: `region_of` is used for subnets, networks, zones, Huawei projects and `security_group` with region scope, never for these kinds.

Failing input (`probe_g5_members.py`): an AWS `environment` "Production" with `located_in` `region-a` and `region-b`, and two EC2 instances, one in each region, with `deployment_context: ["prod"]`. Same with a `security_zone` and `security_boundaries`.

- Base (`aefcdbc`): valid in both relation orders, with or without members, so there was no order dependence to remove for these kinds. (Reversing the two relations changed nothing, unlike the Azure VNet case the reviewers reported, where the network's region is compared with its subnets' and attachments'.)
- Head: `BOUNDARY_LOCATION_MULTIPLE` in both orders, remedy "Declare one boundary per location". The same environment `located_in` two zones of one region stays valid, so the rule is not even a consistent "one location" rule.

Wrong result: a non-contradictory model that FR-021 ("environment groups") and FR-048 ("preserve correct model semantics") cover cannot say that one production environment, or one trust zone, spans two regions, which is the ordinary shape of a disaster-recovery design. The fix record says "a boundary that reaches two regions used to depend on their order, and now always fails"; the first half is false for these kinds. Why the tests miss it: the three new semantics tests use an Azure `network`; nothing exercises a two-region boundary of an `any` kind. Fix direction: apply the rule only where a boundary's region is read (kinds with `regional` or `zonal` location, which is what the two reviewers reported), or refuse only when the regions actually disagree with something; and say in the contract which kinds it binds. Confirmed by running both source trees.

### P3 — The archive audit matches required names by suffix, so a misplaced file satisfies it

`scripts/release_audit.py:62-63` (`_is`), used by `missing_names` and `empty_required`.

`_is(name, item)` is `name == item or name.endswith("/" + item)`. Confirmed with crafted archives (`probe_g14_g15_audit.py`): an sdist with no top-level `README.md` but a `tests/README.md` passes; `pyproject.toml` only at `tests/data/pyproject.toml` passes; a wheel with every required file under `extra/` passes; an empty top-level `README.md` beside a non-empty `tests/README.md` passes the emptiness check. The new tests use exact names, so they do not see it. The gate's package-contents and clean-install lanes still cover the wheel; nothing else covers the sdist's layout, which was G14's point. Fix: match the sdist's names exactly after the top folder is stripped, and match wheel names exactly for `cloud_architecture_diagrams/...` paths.

### P3 — A numeric request ID that overflows a float is echoed as `Infinity`, which is not JSON

`plugins/cloud-architecture-work/server/work_adapter/protocol.py:61-63` (`_valid_id`) and `:98` (`json.dumps` with its default `allow_nan`).

Confirmed against the real server: the frame `{"jsonrpc":"2.0","id":1e400,"method":"ping"}` is answered with `{"jsonrpc":"2.0","id":Infinity,"result":{}}`. A client's JSON parser rejects that line, and the server never learns. This predates the fix, but the new `_valid_id` now states that any float is acceptable. The new ID tests use integers, strings, arrays, objects, booleans and null. Fix: refuse a non-finite float in `_valid_id` (or `allow_nan=False` in `send`, with the error path handling the exception). The server itself stays up, so this is P3.

### P3 — The contract's limits table does not say that the provider box counts toward the 16 group levels

`doc/design/core-contract.md:118` still reads "Group nesting | 16 levels | Rejected before Graphviz". The code now refuses a provider view with 16 model levels (`graph.py:654-658`), and only the fix record says "a provider view takes 15 model levels". A modeller reading the contract would expect 16 to fit. Confirmed by `probe_graph.py` (16 model levels, provider grouping: refused). Add the sentence to the table row or the prose.

### Notes that are not findings

- `_handle_safely` answers an unexpected failure with `id: null` although `_recovered_id(frame)` could often name the request. Error quality only.
- If `threading.Thread.start()` ever raised in `tool_call`, the ID would stay in `self.calls` and count toward `MAX_CALLS` for the life of the server. Not confirmed, pre-existing, and now swallowed by the frame guard instead of ending the process.
- `uv sync --no-build` under a host that sets `UV_NO_BINARY` fails setup rather than building; that is the intended trade.
- `check_png` refuses a non-IDAT chunk *between* IDATs but accepts one after the last IDAT, which is the right reading of the PNG rule; my probe's label said otherwise and the code is correct.

## Records

- `S10-p0-traceability.json`: nine records changed (FR-021, FR-040, FR-043, FR-046, FR-048, NFR-003, NFR-004, NFR-009, NFR-010). Each new `checks` entry names a test that exists in the named file, and the lane matches `scripts/quality_gate.py` (`tests/test_references.py` runs in `render-smoke`, `tests/test_provider_semantics.py` in `provider-semantics`). Against the requirement text at `requirements.md:99,113,116,119,121,231,232,237,238`: the G2 and G8 tests do bear on "valid PNG", "no success for partial artifacts" and "manifest only after outputs validate"; the depth tests on FR-046; the hard-link test on NFR-003's confinement; the held-start and memory-bound tests on NFR-009, which stays `partly` with its open text unchanged and still accurate. The weakest links: NFR-004's new test (`test_ci_uploads_only_text_reports`) is about an upload, while the requirement is about an inventory and blocking packaging; it supports the owner note rather than the requirement. FR-048's `met_with_owner` is unchanged; with the P2 above, "preserve correct model semantics" has a new gap for multi-region `any`-kind boundaries, which the owner should weigh. The regenerated `.md` intro now says the Work run is not finished rather than parked, matching D-024's state. The release-audit lane, which guards the records' structure, passed.
- `S10-core-reproduction-proof.json`: now at `9fb199d`; its source digest equals this checkout's and its wheel digest equals the wheel the local gate built. I did not rerun the clone-and-install reproduction.
- D-026 (`decisions.md:34`): consistent with the code (preview and reads unconditional on `rights`) and with the README paragraph. The decision text correctly says the owner's "fix it" did not address either default, so both remain the session's choices.

## What ran

- `uv run --frozen python scripts/quality_gate.py`: 17/17 lanes passed, exit 0 (`reports/fable-recheck-work/gate-console.log`). Darwin arm64, Graphviz as recorded by the gate.
- The nine probe scripts and the sabotage pass listed above, with outputs beside them. Everything under `reports/`, which git ignores.
- `git diff aefcdbc 3aa566d` in full for code, tests, workflow, contract and records; the two GPT reports; `S11-gpt-reviews.md`; `checks.py`, `bundle.py`, `graph.py` (nesting, notes, provider boxes, depth), `semantics.py` (ancestors, boundaries, security, scheduling), `artifacts.py`, `runtime.py`, `protocol.py` in full, `tools.py` (preview and `read_artifact`), `release_audit.py`, `reproduce_core.py` (predicate and main), `quality_gate.py` lanes, `build_work_plugin.py` (project files), catalog boundary kinds and locations, the plugin README and SKILL.md rows.

## Not run or read

- Actual CI, its artifacts or the 42 KB claim; the real Work host; a second machine; the fresh-clone reproduction.
- Every one of the 71 traceability records: only the nine the diff touched.
- The reviewers' own probe scripts under `reports/astra-review-work/` and `reports/sol-review-work/`; every failing input here is mine.
- The hybrid and Huawei reference images: never opened. Huawei-bearing fixtures were exercised only by the gate's own lanes.
- Timing-sensitive races at the instruction level (a cancel's check-and-set under one lock): I confirmed the lock order and the ordering with forced interleavings, not with a scheduler.
- Whether `uv` would fetch anything for `--no-build` on a cold cache: the dry run was offline against the local cache, and the gate's real setup passed.
