# S07 — Controlled Rendering Vertical Slice

Date: 2026-11-03 | Tasks: M3-01..04 | Branch: `codex/s07-controlled-rendering`, from `f3f0789` | Package: `0.4.0a1` | Code head: `cddb497`

**Result: the renderer is implemented and passes all 14 lanes and 959 tests locally and in [actual CI](#actual-ci) at `cddb497`. M3 is not closed.** No reviewer has examined this code, and the owner has not inspected the output. The contract is in the [core contract](../../design/core-contract.md#controlled-rendering).

## Task status

| Task | Status | Result |
|---|---|---|
| M3-01 | Implemented | `render/graph.py` maps one view to a normalized graph, and `render/draw.py` turns that into DOT through controlled `diagrams` classes. Overview and detail are separate renders with stable IDs, and namespace and worker placement stay separate dimensions |
| M3-02 | Implemented | SVG with embedded icons, PNG, `model.json`, `view.json`, `diagnostics.json` and `manifest.json`, published atomically after every output check passes |
| M3-03 | Implemented | Strict rejects an unknown type and draws nothing. Lenient draws the approved generic symbol, keeps provider, type and name, and marks a draft in the image and the manifest |
| M3-04 | Implemented | `dot` runs alone under a sandbox and resource limits, with descriptor-anchored output, an SVG allowlist and cleanup on failure, timeout and signal. Rendering downloads nothing |

## Exit criteria

| Criterion | State | Evidence |
|---|---|---|
| Repeatable CLI render from a clean setup | Met | A fresh environment from `uv.lock` and a clean wheel install outside the checkout both render; see [clean setup](#clean-setup). Two renders of one input produce identical SVG, PNG and graph bytes |
| Invalid input cannot bypass validation | Met | `render_model` is the only entry point. 31 invalid and malformed inputs run in both modes, with every later render step replaced by a failing stub |
| Usable SVG and PNG with a complete bundle | Met in tests; owner inspection pending | All 19 views of the existing fixtures render, together reaching all 148 catalog types. Each output's content is checked against the graph. This session inspected samples; see [inspection](#inspection) |
| Required security tests pass | Met | `render-security` covers path, symlink, isolation, timeout, code, Graphviz and SVG injection and resource limits; see [validation](#validation) |

M3 also needs the Fable/High review under D-021 and the disposition of its findings. Those are open.

## Validation

`uv run --locked python scripts/quality_gate.py` passed all 14 lanes on this Mac, from a dirty tree, with 959 tests and none skipped. Python 3.13.7, uv 0.13.0 and Graphviz 16.1.0. The [proof](S07-controlled-rendering-proof.json) holds the full gate report and source digests. This is the local result, and [actual CI](#actual-ci) follows.

| Lane | Tests | Work done |
|---|---|---|
| `schema-core` | 91 | Existing core tests |
| `catalog-license` | 76 | Adds the bundled fonts to the rights checks, including tampering tests |
| `provider-semantics` | 442 | Unchanged |
| `render-security` (new) | 214 | Hostile labels, invalid input, paths, symlinks, tampered catalogs and engine output, real sandbox probes, limits and interrupts |
| `render-smoke` (new) | 84 | Every fixture view, representations, manifests, rights, strict and lenient, Kubernetes dimensions, groupings and exit codes |
| `claude-plugin` | 52 | Clean-copy renders in the plugin's own locked environment, and the rewritten skill |

The new lanes call real Graphviz and the real sandbox. They contain no skip, so a host without either fails them. A test requires every render diagnostic code to appear in these test files.

### Actual CI

Actual Quality gate [run 41539921034](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41539921034), job 125601156090, passed all 14 lanes at `cddb497d4ce1974f29874fe8ba5a9bc5d2726391`, from a clean checkout on the self-hosted runner `macbook-pro-m2-max-mingrammer` with Python 3.13.7 and Graphviz 16.1.0. Every lane's test count matches the table above, for 959 tests with none skipped, and the job has zero annotations. `render-security` and `render-smoke` ran real Graphviz and the real sandbox under the runner service. The repository-visibility guard read `private`, and O-002 stays in the report's `release_blockers`.

The wheel has the same SHA-256 as the local build, `49824a56749115381006bb3bd9c27a17917d9022819b22d007e13455006a9f08`, and all 124 source digests and the lock hash match the local gate. The job log names only the lanes, so these details come from the run's `reports` folder, read in place on the runner. That report names this commit and a clean tree. The artifact was not downloaded.

The runner is this same Mac, so CI proves a clean checkout and the runner's environment, not a second machine. The two sdists differ by one file: the local one also holds `.claude/settings.local.json`, which only a global Git ignore hides, so hatchling did not skip it. The CI sdist does not have it, and the wheel is not affected. S07 did not change the sdist settings, and this stays open as a follow-up.

### Sabotage checks

A green lane proves little until it is shown to fail. Each change below went into the real source, ran its lane and was restored, and `src` hashed the same afterwards at `91319a15a85209c5`.

| Change | Lane | Result |
|---|---|---|
| Labels written without escaping | `render-security` | Failed: `test_render_security.py::test_hostile_text_stays_literal_text[\\"]; injected [label=\\"]` |
| Engine run without the sandbox | `render-security` | Failed: `test_render_security.py::test_real_engine_run_uses_only_the_request_directory` |
| Sandbox profile allows network | `render-security` | Failed: `test_render_security.py::test_sandbox_denies_network_while_the_same_command_can_connect` |
| Sandbox profile allows reading home | `render-security` | Failed: `test_render_security.py::test_sandbox_denies_reading_the_home_directory` |
| Sandbox profile allows writes anywhere | `render-security` | Failed: `test_render_security.py::test_sandbox_confines_writes_to_the_request_directory` |
| SVG allowlist removed | `render-security` | Failed: `test_render_security.py::test_an_unsafe_svg_blocks_the_bundle[<lambda>0]` |
| Output symlinks followed | `render-security` | Failed: `test_render_security.py::test_a_symlinked_output_root_is_rejected` |
| Timeout never fires | `render-security` | Failed: `lane hung past 120 s; the gate's lane timeout fails it` |
| Request directory left behind | `render-security` | Failed: `test_render_security.py::test_a_bundle_collision_fails_and_keeps_the_first` |
| Asset digest not compared | `render-security` | Failed: `test_render_security.py::test_a_tampered_asset_digest_is_refused` |
| Validation skipped for semantic errors | `render-security` | Failed: `test_render_security.py::test_invalid_input_cannot_reach_the_renderer[strict-<lambda>0]` |
| System fonts allowed | `render-security` | Failed: `test_render_security.py::test_a_render_that_skipped_the_bundled_fonts_is_refused` |
| Huawei limit dropped from the manifest | `render-smoke` | Failed: `test_render_smoke.py::test_huawei_bundle_carries_the_private_use_limit` |
| Icons left as file references | `render-smoke` | Failed: `test_render_smoke.py::test_every_fixture_view_produces_a_complete_bundle[core-valid.json/overview]` |
| Draft marking removed | `render-smoke` | Failed: `test_render_smoke.py::test_lenient_rendering_of_a_clean_model_is_still_marked_draft` |
| Generic stand-in for a blocked type | `render-smoke` | Failed: `test_render_smoke.py::test_a_blocked_type_takes_no_substitute_in_either_mode` |
| Groups named by label so they merge | `render-smoke` | Failed: `test_render_smoke.py::test_groups_with_one_display_name_stay_separate` |
| Manifest omits the input digest | `render-smoke` | Failed: `test_render_smoke.py::test_manifest_records_what_fr_047_requires` |
| Pods nested inside Nodes in the namespace view | `render-smoke` | Failed: `test_render_smoke.py::test_namespace_grouping_does_not_assign_pods_to_nodes` |

All 19 changes failed their lane. The first version of the last case only added `node` to the namespace nesting list, and its lane passed, because a Node is not a group in that view and the change altered nothing. That was an inert sabotage rather than a test gap, so the table records the version that really nests Pods in Nodes. The timeout case hung until a 120 s limit stopped it, and the gate's own 180 s lane timeout would fail it the same way.

### Clean setup

| Route | Result |
|---|---|
| `uv sync --locked --no-dev` into a new empty environment, then the console script | Passed: rendered the Huawei fixture from 21 installed packages, with no development tools |
| Built wheel installed into a new environment, run from outside the checkout | Passed: `cloud_architecture_diagrams-0.4.0a1-py3-none-any.whl` rendered the same fixture from a directory outside the checkout, and its SVG, PNG and graph bytes match the route above |
| Plugin clean copy under the `claude-plugin` lane | Renders with its own locked runtime packages and a separate data directory |

### Measured render time

Three runs of each size on this Mac, with a connected synthetic graph of labeled nodes and no icons. This shows that the 55 s wall limit leaves a large margin at the view limit. It is not the NFR-007 benchmark, which M4-04 owns and which needs icon-heavy fixtures.

| Entities / relationships | Seconds per run | SVG bytes | PNG bytes |
|---|---|---|---|
| 30 / 50 | 0.22, 0.2, 0.21 | 40751 | 181890 |
| 100 / 150 | 0.34, 0.34, 0.33 | 127544 | 681081 |
| 200 / 300 | 0.49, 0.49, 0.49 | 253636 | 1283412 |

### Inspection

This session looked at the PNG output of the hybrid, AWS, on-premises, EKS and Kubernetes fixtures and at a Thai sample. Icons, cluster nesting, edges, the legend, DRAFT lines and the Thai text with its marks are present and legible. An independent renderer, `rsvg-convert` 2.63.4, also rasterized the Azure and Thai SVGs, showing the embedded icons with no file beside them. These are engineering checks, not owner acceptance. T-014 Thai inspection and the owner's review remain open.

Samples for the owner's inspection, regenerated from the final code: [AWS catalog view](S07-sample-aws.png), [Kubernetes grouped by worker Node, with one Pod left unspecified](S07-sample-kubernetes-by-node.png) and [Thai labels as a lenient draft with one generic fallback](S07-sample-thai-lenient-draft.png).

## Requirement coverage

These states were written from the local gate, and the same tests then passed in [actual CI](#actual-ci).

| ID | State | Where it is checked |
|---|---|---|
| FR-040 | Met locally | SVG and PNG for every fixture view, with embedded icons and an independent `rsvg-convert` read |
| FR-041 | Met locally | Native icons come only from locked `diagrams` classes, and bundled assets from the rights manifest |
| FR-042 | Met locally; polish in M4 | TB and LR, nested groups, wrapped labels, a legend and one edge style per relationship kind |
| FR-043 | Met locally | The result lists artifact paths and checksums, and `rendered` is true only after publication |
| FR-044 | Not implemented | P1, by design |
| FR-045 | Met locally | The closed schema, literal labels, and a read-back of the DOT through Graphviz. See P-026 on "reject" |
| FR-046 | Met locally | View limits and nesting depth, with a suggestion to split. Automatic generation is P1 |
| FR-047 | Met locally | Manifest test against each named field |
| FR-048 | Partly | Approved icons, native labels and grouping conventions. Reference comparison is M4 |
| NFR-001 | Met on this Mac | Identical SVG, PNG and graph bytes across repeat renders. The wheel route matches the lock route, and two-machine comparison is M6 |
| NFR-002 | Met locally | Real sandbox probes, each with a positive control |
| NFR-003 | Met locally | Symlinks, `..`, a replaced root, collisions, output links and the SVG allowlist |
| NFR-006 | Met locally | Every selected element must appear in the finished SVG, and empty groups still draw |
| NFR-009 | Met locally; numbers refine in M4 | Wall, CPU, memory, temporary storage, file and pixel limits, with cleanup on failure and signal |
| NFR-010 | Met locally | Stage, read back, then rename, with the manifest written last |
| NFR-014 | Inspected by this session only | Thai labels with bundled fonts; owner inspection is open |
| T-007 | Met locally | Strict failure, and a lenient draft that keeps provider, type and name |
| T-009 | M3 part met locally | Code, path and symlink escape, remote icon, SVG and Graphviz injection, oversize input and timeout. M5 adds its own part |

## Findings from building it

These would have shipped had the build trusted exit codes and upstream defaults.

| Finding | Effect had it shipped | Fix |
|---|---|---|
| **On macOS, Pango defaults to CoreText, which ignores fontconfig.** `FONTCONFIG_FILE` alone draws Helvetica | The manifest would claim Noto fonts the image did not use, and layout would depend on the host | Force `PANGOCAIRO_BACKEND=fc`, and read `dot -v` on every render; any other font fails with `RENDER_FONT_UNAVAILABLE`. A test proves the failure against real Graphviz without the variable |
| `diagrams.Cluster` names its subgraph after its label | Two boundaries with one display name, such as two "Production" scopes, silently merge | Name the cluster by ID and set the label afterwards |
| `with Diagram` runs Graphviz on exit | Graphviz would run outside the sandbox and limits | Never enter that context, and read `dot.source` |
| Python `graphviz` passes a `<...>` label through as HTML | A model could reach `<IMG SRC=...>` | Every label goes through one literal function, and a test reads the DOT back through Graphviz |
| Graphviz decodes `&amp;` and `&#60;` in plain labels | A literal label would change meaning | Encode `&` before escaping |
| Graphviz drops an empty cluster and exits 0 when an image cannot load | A selected boundary or icon could vanish from a "successful" render | Anchor every group, and compare the finished SVG with the graph |
| Each membership dimension is acyclic alone, not together | A `parent_ref` plus a `deployment_member_of` could loop the group tree | The mapper refuses to close a loop, and the dropped direction stays a note |
| `/bin/sh` on macOS is a launcher that starts another shell | The first sandbox probes "passed" because the shell never started | Probes now use `/bin/bash`, with a positive control in each. Same for the network probe, whose control connects without the sandbox |

**S04 note:** the S04 native runtime sets `FONTCONFIG_FILE` without the override, so its Noto claim probably did not hold on macOS. It was not re-run, and S04 stays frozen as a separate fixture. See P-027.

## Limits and what this does not establish

- **No review, and one machine.** Passing CI does not stand in for a review, and its runner is this same Mac.
- **FR-048 and T-016 are only partly addressed.** Icons, native labels and grouping conventions exist, but comparison with official references is M4 work.
- **Layout is an engineering slice.** Members with no edges stack in one long column, notes can be verbose, and a long single word can wrap awkwardly, as `PersistentVolumeClaim` does at the label width. These are presentation choices for M4 and the owner, not defects in the bundle.
- **macOS only.** Without `sandbox-exec`, `render` fails closed. Apple marks that tool deprecated, so a future macOS may need another route.
- **Memory and temporary storage limits are sampled**, so they can overshoot and are not kernel caps. SIGKILL cannot run cleanup, so it can leave a `.request-*` directory, and the process then ends at its CPU limit.
- **The SVG references its fonts rather than embedding them**, so a viewer without Noto falls back, and its metrics can differ. FR-040 requires embedded icons only, and this stays open from S04.
- **T-009's M5 part remains**, as does T-012's measured evaluation under M4-04. The 200 and 300 view limits come from the S04 sizes and this session's timing.
- **FR-044** PDF and DOT exports are not implemented. They are P1.
- `reports/render-smoke` holds bundles showing Huawei icons, and CI uploads `reports/` as a private artifact for 14 days. The wheel in that artifact already contains those icons, so this adds no new class of exposure, and the `catalog-license` lane still fails on a public repository.
- S07 did not change the owner's installed plugin. S04 alpha.3 and the runner registrations are unchanged. This branch is not merged, and nothing is released.

## Decisions for the owner

The session plan lists the owner's inspection of the first output. These proposals are recorded in [decisions](../decisions.md) and take effect until changed:

- P-025: a `blocked` type refuses to render rather than drawing a text-only box. No type is blocked today.
- P-026: HTML-like label text is drawn literally, not rejected.

## Model and review

Implementation used **Claude Opus 5.5 (`claude-opus-5-5`)**, the model of the session started for S07. The project policy names Sol/High for this milestone, so this is a recorded substitution, and no model setting changed.

D-021 names Fable/High for M3's review, replacing Astra/High. **That review has not happened.** Sabotage checks and self-review in this session are not a review.

## Next steps

1. Run the Fable/High review on `f3f0789..cddb497`, then dispose of its findings.
2. The owner inspects representative output and settles the presentation choices above.
3. Close M3 only after those. M4 then builds reference scenarios on this renderer.
