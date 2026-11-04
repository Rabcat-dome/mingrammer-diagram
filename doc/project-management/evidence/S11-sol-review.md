# Independent code review

**Disposition — changes requested.**

**Reviewer** — OpenAI Codex, GPT-6 family. The exact serving variant and reasoning-effort setting were unavailable to the reviewer. The requested filename is not a model attestation.

**Base** `556945952fef1461c03451ba76ed3f652909edde`  
**Head** `aefcdbcbf7157de92eecd7a50bd52d3c661c455f`

I reviewed render isolation, the Work adapter and packaging, diagram semantics, then release verification. I stopped after the fourth area and the comparison with the recorded Fable reviews. Findings below concern distinct failures. I separated verified behavior, fault-injected reproductions, and untested consequences.

## P1

### 1. CI sends private-use Huawei artwork to GitHub artifact storage

`.github/workflows/quality-gate.yml:56–63`, `tests/test_render_smoke.py:54–80`, `tests/test_visual_regression.py:25–40`, `scripts/quality_gate.py:123`.

On an eligible owner-triggered CI run, the upload step runs even after a failed gate and takes all of `reports/`. The local gate generated **12 smoke bundles and eight visual-regression bundles** whose manifests declare private use and whose directories contain PNG and SVG. The local wheel in `reports/dist/` had 30 private Huawei PNG/SVG entries. All are inside the upload scope. The wildcard predates this range, and the added rendering lanes now put rendered copies there too. I confirmed the paths and classifications locally. I did not trigger CI, verify a historical remote upload, or transfer any files.

`test_a_path_inside_the_reports_folder_stays_ignored_by_git` only checks Git ignore behavior. The catalog checks verify repository visibility and the PyPI classifier, and the archive audit checks contents and notices. None checks what Actions uploads. Use an explicit upload allowlist of text reports and keep asset-bearing output outside that set.

## P2

### 2. A PNG with valid chunk checksums and invalid pixels publishes successfully

`src/cloud_architecture_diagrams/render/checks.py:209–237`, `src/cloud_architecture_diagrams/render/__init__.py:249–255`.

**Confirmed with injected engine-output corruption.** After a real, non-Huawei Graphviz render, I kept the real PNG dimensions and replaced IDAT with a one-byte payload and a correct CRC. The render returned success and wrote a complete manifest even though the pixel stream failed decompression. This requires bad engine output or modification of the engine's output file. I did not find a model-only route to synthesize that file. `test_an_invalid_png_blocks_the_bundle` covers truncation, wrong magic, invalid size and CRC corruption. Its companion `rebuilt_png` fixture at line 569 deliberately writes a dummy IDAT, so some size tests pass precisely because the compressed pixels are never checked.

### 3. Work sends private-use image bytes across its host boundary

`plugins/cloud-architecture-work/server/work_adapter/tools.py:588–605,638–688`.

A prompt-injected host can render a model whose result reports `rights.private_use_only: true`, or request `diagram.png` or `diagram.svg` from an existing private-use bundle. The adapter returns the PNG preview or image/resource bytes to the host without checking that flag. **Confirmed at the adapter boundary with synthetic bytes** for the automatic preview. The explicit PNG/SVG retrieval branches are confirmed by code inspection. Whether the real Work host forwards or retains those bytes off-device is unverified. The local rendering and the MCP handoff have separate privacy properties. `test_private_use_limit_reaches_the_tool_result` asserts the warning and flag in the first text item. It does not assert that the image stays on disk. The normal file-read test expects content to be returned and does not exercise a restricted bundle.

### 4. Work can exit while a child it just spawned is still running

`plugins/cloud-architecture-work/server/work_adapter/runtime.py:201–209,224–237,252–262,375–404`, `plugins/cloud-architecture-work/server/work_adapter/protocol.py:160–175,254–263`.

**Confirmed with a forced scheduling window and a real stand-in child.** Pause the daemon worker immediately after `Popen` creates the child and before it returns for registration, then deliver EOF. Shutdown snapshots an empty child registry and the server exits successfully while the child is still alive. I killed the stand-in after observing it. The same gap surrounds the setup subprocess. I did not reproduce a leaked real Graphviz process or setup directory in that window. The shutdown tests wait for a running core or a scratch folder. They cover termination after startup and never synchronize with the gap between spawn and registration.

### 5. Reordering two location relations reverses an Azure placement verdict

`src/cloud_architecture_diagrams/semantics.py:144–164,246–286,404–407`, `src/cloud_architecture_diagrams/catalog_data/rules.json:17–19,26`.

**Confirmed through strict validation.** In `tests/fixtures/references/azure-hub-spoke.json`, remove the spoke VNet's region parent and give it two `located_in` relations, one to a new Azure region and one to the original Southeast Asia region. The attached resources still declare Southeast Asia. With the original region last, the model validates. Reverse only the two relations and it fails with `PLACEMENT_REGION_MISMATCH`. The first discovered region wins, and the multiple-location check applies only to zonal boundaries. An ambiguous regional VNet should not switch between valid and invalid because of array order. The relation-only and wrong-region fixtures exercise single location paths. The nesting permutation tests shuffle `entity_refs`, leaving the underlying relations unchanged.

### 6. The node view says placement is unspecified beside an explicit Pod-to-Node assignment

`src/cloud_architecture_diagrams/render/graph.py:173–201,375–379,475–492`, `src/cloud_architecture_diagrams/semantics.py:650–672`.

**Confirmed with a complete render.** In the Azure reference fixture, remove `web-pod-1.kubernetes.node_ref` and add a selected `scheduling` edge from `web-pod-1` to `aks-node-1` in `aks-nodes`. Validation accepts it, and the semantic checker uses that form as a concrete assignment for conflict detection. The image draws the scheduling edge, labels the Pod `node: unspecified`, and places it directly under the cluster. The contract explicitly bases nesting on `node_ref`. The misleading result is the contradictory label, even if that nesting rule stays. `test_concrete_pod_assignments_and_broader_scheduling` tests validation only. The node-view and unspecified-placement tests start from `node_ref` presence or absence without asserting the edge-only rendering.

## P3

### 7. A failed final directory sync returns a render failure with a visible bundle

`src/cloud_architecture_diagrams/render/bundle.py:100–117`, `doc/design/core-contract.md:21`.

**Confirmed with a fault injected only at the output-root fsync.** A real render renamed the stage successfully, then returned `RENDER_OUTPUT_WRITE_FAILED` with `rendered=false`. The final bundle and complete manifest remained visible. This can cause a caller to retry after an apparently unpublished result. The existing write and publication tests fail before rename or at rename. This case concerns a filesystem error after the commit point, separate from the signal window already recorded in S07.

### 8. The provider wrapper takes the final group tree beyond the declared limit

`src/cloud_architecture_diagrams/render/graph.py:453–473,602–634`, `src/cloud_architecture_diagrams/render/limits.py:10`.

**Confirmed with a real render.** Sixteen nested external `environment` boundaries in a provider view publish with 17 nested groups because depth is checked before the provider wrapper is inserted. The manifest advertises a limit of 16. The two named depth tests use 15 and 17 model boundaries and miss exactly 16. The contract lists 16 group levels without an exception for the wrapper.

### 9. Work will read an outside file through a hard-linked artifact

`plugins/cloud-architecture-work/server/work_adapter/artifacts.py:55–85`, `plugins/cloud-architecture-work/server/work_adapter/tools.py:542–555,638–674`.

**Confirmed with synthetic content.** Create a bundle-shaped directory under the output root and hard-link a same-volume JSON file from outside it to `model.json`. `read_artifact` returns the outside content even without a manifest. The same reader supplies source bytes for rerendering. A host argument alone cannot create the hard link. The failure requires pre-existing local filesystem state. Traversal, symlink and FIFO tests pass because a hard link presents as a regular file through the descriptor checks.

### 10. A late cancellation can leave stale cancellation state behind

`plugins/cloud-architecture-work/server/work_adapter/protocol.py:143–150,177–184`, `plugins/cloud-architecture-work/server/work_adapter/runtime.py:201–222`.

**Confirmed by forcing the ordering with a stand-in runtime.** Deliver cancellation after `runtime.finished(id)` has discarded its token and before the worker removes that ID from `calls`. The server still considers the call live, and the runtime inserts an early-cancel token for a child that has already gone. The worker then finishes without clearing it. The token remains for the life of the server. The sleeping-core cancellation test only cancels while a child is registered. This differs from S09's recorded late cancellation that leaves a committed bundle.

### 11. Malformed protocol frames can terminate the adapter

`plugins/cloud-architecture-work/server/work_adapter/protocol.py:157–165,177–192,206–215,229–238`.

**Confirmed through the frame handler.** Send a `tools/call` request with an array ID, or malformed JSON whose first apparent ID is a quoted string with a raw control character. The first raises an uncaught `TypeError` in the live-call map. The second raises a fresh `JSONDecodeError` while recovering the request ID, outside the parse guard. Neither gets a protocol error response, and `serve` only catches its signal exception. This requires a malformed client frame, beyond model-selected tool arguments when the host itself generates compliant frames. The protocol-error and oversize tests use ordinary scalar IDs.

### 12. The Work install lock does not cover source-build dependencies

`plugins/cloud-architecture-work/server/work_adapter/runtime.py:370–395`.

`--locked --no-install-project` protects the project resolution and skips building the project itself. The command allows dependency source builds, inherits `UV_NO_BINARY_PACKAGE`, and requests neither wheel-only installation nor build-dependency hash enforcement. With `UV_NO_BINARY_PACKAGE=diagrams`, the actual locked command in offline dry-run mode planned a download despite the normal wheel being installed in the checkout environment. A source build can resolve its backend dependencies separately. **A completed unlocked backend install is unconfirmed.** The environment variable is host configuration, not a tool argument. The setup test asserts installed packages and the lock digest in the resulting environment, which would miss transient isolated build dependencies.

### 13. The release audit accepts an empty source archive

`scripts/release_audit.py:51–69,87–112`, `tests/test_release_audit.py:83–109,151–159`.

**Confirmed with local synthetic archives.** `audit()` accepted a valid but empty tarball as its sdist, along with a fake wheel made of empty entries whose names merely end in the required paths. The full gate's other wheel checks and clean wheel install provide independent protection for the wheel. The sdist test only inspects forbidden names and the normal-build count. It never installs or builds from the sdist. A tarball containing only one harmless entry would also satisfy the positive-count assertion.

### 14. The standalone reproduction script exits zero when its routes disagree

`scripts/reproduce_core.py:192–221`, `tests/test_release_audit.py:73–81`.

**Confirmed using stubbed clone, install and render results.** Both routes return all five per-view checks as true but disagree on the rendered manifest engine. The script writes `routes_agree=false` and exits zero. The same predicate permits zero views. The gate checks the existing committed proof's agreement and minimum view count, so it would reject those JSON results if committed. It does not exercise the standalone exit path.

## Traceability sample

I compared the requirement text at `doc/requirements/requirements.md:94–136,225–271` with the records and their named tests. The following states are too generous for the verified boundaries.

| Record and current state | Reason |
| --- | --- |
| FR-040 and FR-043, `met` at JSON lines 1257 and 1427 | A complete bundle can report success with an undecodable PNG. The named PNG test uses invalid CRC or framing mutations, and the normal complete-bundle test exercises ordinary engine output. |
| FR-046, `met` at line 1537 | The final provider tree can exceed its advertised depth. The named depth and view-size tests miss the wrapper boundary. |
| NFR-003, `met` at line 2425 | The symlink, traversal and unsafe-root checks support their specific guarantees. They do not support full read confinement when an artifact name refers to a hard-linked outside inode. |
| NFR-010, `met` at line 2807 | A success manifest can cover an invalid raster. The publication tests cover writes and pre-rename failures. |
| FR-048, `met_with_owner` at line 1622 | D-023 establishes M4 acceptance of the inspected images. The graph/image baseline tests do not establish preservation of semantics for edge-only placement or reordered regional relations. The requirement has an independent semantics clause. |
| NFR-004, `met_with_owner` at line 2513 | The inventory and private-use approval hold within their stated scope. The named notice and upload-block tests miss the CI artifact route that sends restricted assets and diagrams outside the local runtime. |

I also sampled T-002 and NFR-014. The T-002 test verifies peering and the absence of extra hub-to-spoke links. The S01 brief explicitly requests the VPN Gateway without a remote endpoint. Its owner note scopes the accepted interpretation to that fixture, so I did not count a missing tunnel as a new defect. NFR-014 has owner-backed visual evidence for the Thai sample, plus named preservation, rendering and font-resolution tests. I did not personally inspect the rendered image.

I also ran a synthetic trace mutation that marked every record `met` using one unrelated existing test and no evidence links. The guard accepted it. The fixture in `tests/test_release_audit.py:198` already expects unrelated checks to pass, and Fable recorded the narrower lane-matching gap. The guard checks record structure. The actual overclaims above come from comparing requirement text, tests and runtime behavior.

## What ran and where I stopped

- Ran `uv run --frozen python scripts/quality_gate.py` locally on Darwin arm64 with Python 3.13.7 and Graphviz 16.1.0. All **17 lanes and 1,461 tests** passed. The JSON records the requested head, a dirty tree and a null clean-source reference. The O-002 release blocker remains in that report.
- Ran local probes for group depth, final-directory sync failure, malformed PNG publication, a short-lived child writing above a reduced sampled scratch budget, artifact hard links, synthetic private-use preview handling, malformed frames, late cancellation, pre-registration shutdown, Pod placement, Azure location order, synthetic archive and trace acceptance, and reproduction exit status. The scratch-budget probe demonstrates the documented sampling gap. I found no hostile-model-only Graphviz/SVG injection, direct output traversal, symlink following from model input, or partial directory published by normal atomic rename.
- Verified the reproduction proof's source digest matches this checkout. Read the required renderer, adapter, build, semantics, rules, release and reproduction paths and sampled the named tests. Read the Fable evidence after the independent pass. Existing findings about the permissive sandbox read policy, bidi controls, post-publish signals, existing provider exceptions and proof-digest coverage are not repeated here.
- I left the original uncommitted S09 validation record and `.claude/worktrees` out of the manual review. Four additional project-management Markdown files appeared modified during the run. The reviewed source, tests, workflow, requirements and traceability JSON matched HEAD. The gate ran in the shared checkout and its documentation checks could see working-tree records.
- I did not edit tracked files, commit, push, publish, trigger CI, fetch CI artifacts, or transfer Huawei assets or images. I did not run the real Work UI, use a second machine, execute the remote clean reproduction, inspect host-side logs, or open Huawei images for visual review. The required gate created local render and build outputs, and my probes and report are under the ignored `reports/` directory.
