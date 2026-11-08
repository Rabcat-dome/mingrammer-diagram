# Lines and the draw.io Copy

Date: 2026-11-08 (Asia/Bangkok) | Decisions: D-048, D-049 | Requirement: FR-067 | Implementer: Claude Opus 5.5 | Core: `0.5.0a3` to `0.6.0a1` | Branch: `codex/polyline-drawio`, from `main` at `60f4904`

## What the owner asked

After the D-046 run in Work, the owner asked, translated from Thai, whether lines could use right angles instead of curves, and whether a line crossing another could jump it with a gap or an arc. After this session's trials, below, the owner said "Drop line jumps, and try polyline". Shown polyline, the owner asked for it with one more thing: "we will use polyline, but want to add a draw.io file to the download, to edit further". Shown the plan, the owner said "Start both".

## Trials of right angles

Each trial changed the renderer in a scratch clone of `581cea0` and rendered reference views. The repository did not change, and the clone was restored after each.

| Trial | Lines | Labels on lines | Line ends | Result |
|---|---|---|---|---|
| `splines=ortho` | Right angles | Drift away from their lines, because `ortho` in `dot` does not handle edge labels | Stop short of icons, often in empty space | Refused |
| `ortho` with line labels as `xlabel` | Right angles | Next to their lines | Still stop short of icons, because `ortho` ends a line on the node's whole box, which holds the text | Refused |
| `ortho`, node box the icon alone, text allowed past it | Right angles | Next to their lines | Still short, because the box Graphviz routes to includes the text. Text also overlapped the icons | Refused |
| `ortho`, node text as `xlabel` | Right angles | Next to their lines | On the icons | Refused: Graphviz puts each node's text beside the icon where it finds room, over lines and box borders, because it keeps no room for it |
| `splines=polyline` | Straight segments, bent where they pass a box | On their lines | As with curves | Chosen (D-048) |

Graphviz has no line jumps in any mode, so a jump would need its own drawing after layout, and the PNG would then need a second rasterizer outside the controlled renderer. The owner dropped jumps.

## Straight lines (D-048)

`draw.py` sets `splines=polyline` where it set `spline`. Node and group positions do not change, so only lines change. The `visual-regression` lane found 15 of the 26 reference views changed, the ones with a curved line, and the other 11 match their baselines. `scripts/update_visual_baselines.py` accepted the 15 with the reason in `tests/baselines/baselines.json`. This session looked at the AWS, Azure and GKE views, and the owner reviews all 15 under T-016:

- AWS three-tier: `overview`, `zones`, `eks-namespaces`
- Azure hub-spoke: `overview`, `aks-namespaces`
- GCP shared VPC: `overview`, `projects`, `gke-namespaces`
- Huawei web: `overview`, `zones`, `cce-namespaces`
- Hybrid five: `overview`, `connectivity`, `data-flows`
- On-premises: `k8s-namespaces`

## The draw.io copy (D-049)

`render/drawio.py` writes `diagram.drawio` from the SVG that `check_svg`, `check_undistorted` and `check_content` have already accepted, so no second Graphviz run is needed:

- Every group is a container in its parent container, with Graphviz's outline, fill, border and dashes, so moving a box in draw.io moves what it holds.
- Every resource with an icon is one draw.io `label` box holding its verified icon and its text below, the box Graphviz gave it. Lines therefore stop where they stop in the PNG, below the text. A lenient stand-in keeps its dashed frame with its generic symbol inside, and a resource drawn as a box stays a box.
- Every relationship is attached to its source and target, with Graphviz's bend points in order from the source, its kind's color and dashes, and its arrow when it is directed. A line to a group attaches to the group's container.
- The legend, the title and every notice line, including the private-use lines of D-018, are text cells.
- All text is plain text (`html=0`), so a name such as `<b>App</b>` stays those characters. Text uses the SVG's font list, so draw.io without Noto falls back to a system font, and Thai uses the system's Thai font. A line's label has a white backing, because draw.io centres it on its line.

`check_drawio` then checks the copy as `check_svg` checks the SVG. It allows only the elements, attributes and style keys the exporter writes, plain text in every cell with text, style values without markup or links, and images that are this render's verified icons. Every reference must resolve, every group, resource, relationship, title line and notice line must be there with its text, and every relationship must join its own two ends, in its direction. A copy that fails, or one over the file limit, publishes nothing. The manifest lists it as `application/vnd.jgraph.mxfile`, and `manifest_version` moves to `1.2.0`.

The Work plugin lists `diagram.drawio` among the files `read_artifact` returns, as a binary resource, and its host check expects seven files. Both skills say that `diagram.drawio` is an editable copy for the user to change in draw.io, to hand over unchanged and never write, and that it opens in draw.io. Both READMEs and the core contract describe it.

The draw.io desktop app on this Mac opened the copies of the AWS overview, Azure overview, hybrid `data-flows`, GKE `gke-namespaces`, a Thai AKS detail view from the D-047 run, and a lenient stand-in, through its own export to PNG, all six from the final code. This session looked at four of those images, the AWS overview, the Thai AKS view, the stand-in and `data-flows`, and each showed the boxes, icons, text, notices and lines where the PNG has them. The Azure and GKE images were exported but not looked at. One place follows Graphviz exactly: in a left-to-right view a node's box reaches above its icon as far as its text reaches below, so a line that enters from above stops above the icon, in both files.

## Version

The core moves to `0.6.0a1` in `pyproject.toml`, `__init__.py` and `uv.lock`, and the contract says so. `uv lock --check` passes, and no dependency changes, but the project's own version is in the lock, so an install builds the Work runtime again.

## Checks

- New tests. The `render-smoke` lane checks every fixture view's copy against its own reading of the SVG and the graph: plain text in every text cell, each group in its parent container, each resource in its container with its verified icon at the SVG's place and its box reaching below its text, each relationship joined to its own ends in its direction, with the SVG line's own bend points in order from the source, the title and notice lines, and the legend. It also checks that names with markup stay those characters, that a copy failing its check publishes nothing, and that every line in every fixture view is straight segments. The `render-security` lane passes the published copy through `check_drawio`, refuses 13 tampered copies, among them an HTML label, an unknown style key, a link, an active style value, a foreign element, a document type, a foreign icon on a resource or on the title, swapped ends, a missing line, a changed name, a dangling parent and a lost notice, and refuses a copy over the file limit. The `package-contract` lane reads the copy back through `read_artifact`, and the plugin tests pin both skills' new clauses.
- Each of 16 sabotage edits failed a named test: plain text turned off, containers ignored, line ends swapped, bends reversed, the icon box without its text, foreign icons allowed, colons allowed in style values, the copy not checked, curves again, the Work server forgetting the copy, the Work skill letting the chat write one, the Claude skill not saying where it opens, notices left out, foreign cells allowed, markup labels allowed and arrows always drawn. The first run left three alive, and one was caught only by a crash. Two tamper cases now reach the check under test, and a written reversal of the bend points, which Graphviz never needed in any of the 47 fixture views, is gone.
- The Work plugin builds as `0.1.0-alpha.1+8c1b507a536f` twice, with the same ZIP, SHA-256 `3947a4cf42bddd452f917881c9a4c7aca647bb2d94d8947661114e5d87387ecf`, 99 files and lock `bf76c5683b8799d1`. `scripts/work_host_check.py` passes 35 checks through the host's own engine, on `codex-cli 0.167.0-alpha.3.2`, all seven files among them.
- The local gate passes 16 of 17 lanes with 2,074 tests and none skipped, on the uncommitted change over `60f4904`. `release-audit` fails only `test_the_reproduction_proof_passes_and_still_describes_this_source`, because the core reproduction proof describes the source before this change, and it can be made again only from a commit, as for D-044.

- The core reproduces from a new clone of `51ce3e7` in a clean runtime. It builds the wheel with SHA-256 `d5fddbc5099e7fddb35af0443db27f20cdbfa2e983d0cfaafb7b3ef6fa285331`, the same as the local build, and all 26 reference views match their baselines by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), the `release-audit` lane passes its 67 tests, so the local gate's only failure is gone.

Not done when this was written: an independent review, the owner's review of the 15 changed views, an install, and a run in Work.

## Review

Date: 2026-11-08 (Asia/Bangkok) | Range: `60f4904..3847358` | Reviewer: Claude Fable 5.1 (`claude-fable-5-1`), at High for renderer and security work under D-021, in a fresh agent working from its own clone | Implementer: Claude Opus 5.5, so reviewer and implementer share a vendor

**Disposition: approved, with six P3 findings and no P0 to P2.** No model text reached markup, a link, a style entry or an active attribute: a crafted lenient left-to-right model with `<script>`, `<b>`, `<img onerror>`, `javascript:` links, `%name%` placeholders, `;` style separators in names and labels, a name closing an `mxCell` element, an environment written as style entries, and Thai with a zero-width space rendered, passed `check_drawio`, and draw.io's own export showed every string as literal text. The reviewer's clone passed the full gate, 17 lanes with 2,074 tests, with the proof matching the source, and built the same wheel and the same Work plugin ZIP as recorded. The host check passed 35 checks with seven files. Rendering the AWS overview at `60f4904` and at `3847358` gave the same position for all 23 nodes and groups. It exported eight copies with draw.io and looked at seven. Of its own eight sabotage edits, six failed a test, and two are F3.

| ID | Severity | Where | Finding | Fix direction |
|---|---|---|---|---|
| F1 | P3 | `drawio.py`, `_cells`; the contract and this record | Only `mxCell` elements and what they hold were checked. An attribute on `mxfile`, `diagram` or `mxGraphModel`, text between elements, and a processing instruction passed, so "only the elements, attributes and style keys the exporter writes" overstated the check. None had an effect in draw.io | Check the outer elements' attributes, refuse stray text, and refuse a second `<?` |
| F2 | P3 | `drawio.py`, `check_drawio` | A copy could pass while differing from the picture: a resource moved out of its container, a group with `container=0`, a line written as a box, all positions zeroed or a colour changed. Only presence, text, ends and arrows were checked | Check each box's container, `container=1` on groups, and `edge="1"` on lines |
| F3 | P3 | `test_render_security.py` | Removing the arrow or the label comparison from `check_drawio` left every test passing, because no tamper case changed a line's arrow or label | Add those two cases |
| F4 | P3 | `drawio.py`, `add_legend` | The legend listed its kinds in the reverse of the PNG's order, because it was laid out from the graph rather than read from the SVG like everything else | Read each sample from the SVG |
| F5 | P3 | `drawio.py`, `add_edges` | A line to a group that holds its other end, such as `vpc` to `subnet`, started on the group's far border and crossed the subnet, and a loop became a short V above the icon, because draw.io starts a line on the border of the box it is attached to. 10 of the 270 fixture lines have an end inside the other, and none is a loop | Keep Graphviz's own ends for such lines |
| F6 | P3 | `HANDOFF.md`, item 11 | It still said there was no reproduction proof after `3847358` added one | Update it |

Not checked by the reviewer: the implementer's 16 sabotage edits and six exports, the owner's review of the 15 views, a run in Work, editing in draw.io, such as moving a container whose lines have fixed bend points, views near the size limits, and CI. CI [run 42449922130](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42449922130) passed at `3847358`, and [run 42449824519](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42449824519) at `51ce3e7` failed only `release-audit`, before the proof.

## Fixes after the review

On the owner's word on 2026-11-08, translated from Thai, "Go ahead as you recommend, 1 to 6", Claude Opus 5.5 confirmed and fixed each finding.

- F1: `check_drawio` now requires the file's one `host` attribute, a page named by a view ID, the model's own attributes with safe values, and a `root` without attributes. It refuses text outside attributes anywhere, and any processing instruction but the XML declaration. The contract's sentence is now true.
- F2: it requires every group's and every resource's cell to sit in the container its group is drawn in, every group to be a container, and every line to be a line at the page level.
- F3: ten new tamper cases cover F1 to F3: an attribute on the file, on the page and on the model, text between cells, a processing instruction, a resource moved out of its container, a container turned off, a line written as a box, an arrow removed and a changed line label. The `render-security` lane now refuses 23 tampered copies.
- F4: each legend sample is now read from the SVG, by the name `draw` gives it, so its place, order and length match the PNG. In hybrid `data-flows`, `traffic` is above `replication` in both. The per-view test compares every sample's start with the SVG.
- F5: a line to a group that holds its other end, and a loop, keep Graphviz's own ends as bends, so draw.io draws Graphviz's route. A new test draws `vpc` to `subnet` and a loop on `app`. The first version of this fix put resources and groups in one map, and a cluster drawn as both a group and a resource in it became its own parent, so the render never ended. They now have separate maps.
- F6: item 11 says the proof exists and CI passed.
- Each of 26 sabotage edits failed a named test: the 16 before, and one for each new check, the legend and the kept ends.
- The Work plugin builds as `0.1.0-alpha.1+a0465bcceca9` twice, with the same ZIP, SHA-256 `33597136bffb5f426e8959d31fd23e682c9770961d850f891c93d944ccc39e0f`, 99 files and lock `bf76c5683b8799d1`. The host check passes 35 checks. The local gate passes 16 of 17 lanes with 2,085 tests and none skipped, after one test's variables were renamed for `types`. The fixes change `src`, so `release-audit` waits for a new reproduction proof, which follows the commit.
- The core reproduces from a new clone of `192d554`: the same wheel, SHA-256 `5c9eaa6795ffa01b8c3b23b42c03e4e90b836995b0b1c45593d8c0e899b2f71d`, and all 26 reference views match their baselines by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## The owner's review

- Claude Opus 5.5 sent the owner a page with the 15 changed views, each beside its curved version, and two draw.io copies: the AWS overview, and an AKS detail view with Thai labels.
- The owner passed the 15 views on 2026-11-08 with "Pass, merge, install" (D-050), so their baselines stand as accepted. The other 11 reference views did not change. The two draw.io copies were for the owner to try, and the pass does not say how draw.io draws other views.

## Install

- `main` fast-forwarded from `60f4904` to `94b426c`, and actual CI [run 42461308175](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/42461308175) passed there. The tag does not move.
- The Work plugin built from `main` at `94b426c` is `0.1.0-alpha.1+a0465bcceca9`, with core `0.6.0a1`. Two builds gave the same ZIP, SHA-256 `33597136bffb5f426e8959d31fd23e682c9770961d850f891c93d944ccc39e0f`, the one recorded after the fixes, and the host check passed 35 checks in a throwaway profile on `codex-cli 0.167.0-alpha.3.2`. It is installed with `codex plugin add`, replacing `f6b9f6134e60`.
- `uv.lock` changed, so the plugin's `runtime.py setup` built the runtime again. It is `ready` on lock `bf76c5683b8799d1`, with Python 3.13.7, and its render probe passes.
- The Claude plugin moved from `9b77c56ee880` to `94b426c6aed7`.
- Through the installed Work server, `core-valid.json` drawn as its overview gives a bundle of seven files with `diagram.drawio` among them. `read_artifact` returns that copy as `application/vnd.jgraph.mxfile`, the same bytes as on disk, and the manifest is `1.2.0` with package `0.6.0a1`. The bundle stays in the owner's Work folder as `demo--overview--73956c34167d561c`.
- The installed Claude plugin's `render` of the Kubernetes example gives the same seven files. The draw.io desktop app exports its `diagram.drawio` with the same boxes, icons, line and labels as its PNG, in draw.io's own font.
- The ChatGPT app and any open Claude Code session need a restart to load these. No prompt has run in Work on this version.

## The run in Work

The owner ran four prompts in one new Work chat on `0.1.0-alpha.1+a0465bcceca9`. [The record](S09-Work-validation.md#the-drawio-copy-in-work) has the details. Prompts 2 and 4 passed: the chat linked all seven files with `diagram.drawio` among them, said it opens in draw.io, and handed over each file unchanged. Each bundle's `diagram.drawio`, exported by the draw.io desktop app, matches its PNG. In prompt 3, asked to open the draw.io file, add Cloud Monitoring and give back the updated file, the chat drew the change through the model, but then handed over a draw.io file it had written itself, with the earlier layout and the new cells placed by hand. In prompt 1 it chose the S04 plugin, so prompt 2 is what showed this version.

## The draw.io edit rule

On the owner's word on 2026-11-08, "Yes, fix the skill" (D-051), Claude Opus 5.5 added one paragraph to the section on editing in both skills. A request to change a diagram is a request to change its model, even when the user names `diagram.drawio` or asks for an updated draw.io file. The chat changes the model, renders again and hands over the new bundle as step 8 says. It never edits, patches, merges or restyles a `diagram.drawio`, or copies cells from one into another, even to keep the earlier layout, because such a file matches no picture and skips the plugin's checks. It tells the user that boxes can move, and that changes made by hand in draw.io are not in the new copy.

- A test in each plugin's lane requires that paragraph in the section on editing, with each of its clauses. Each of 7 sabotage edits failed it by name: the paragraph removed from either skill, moved out of the section, the ban softened, an exception for the layout, no word on moved boxes, and the updated draw.io file in place of the new bundle.
- `src` does not change, so the wheel and the core proof stand. The Work plugin builds as `0.1.0-alpha.1+4ce48c4beb7c` twice, with the same ZIP, SHA-256 `8a616d03ffc779f4d53824aba3692c81585639698df3519ebde26920326f24a1`, 99 files and lock `bf76c5683b8799d1`, and the host check passes 35 checks. The local gate passes 17 lanes with 2,087 tests and none skipped.
- Neither installed plugin has this paragraph. Prompt 3 runs again once the fixed Work plugin is installed.
- CI passed at `ef792fc`, and on the owner's answer "Commit, merge, install" `main` fast-forwarded to it. The Work plugin built from `main` there is `0.1.0-alpha.1+4ce48c4beb7c`, with the same ZIP as above from two builds, and the host check passed 35 checks. It is installed with `codex plugin add`, replacing `a0465bcceca9`. `uv.lock` did not change, so the runtime stays, and the installed server reports it `ready` with its render probe passing. The Claude plugin moved from `94b426c6aed7` to `ef792fc60079`. Both installed skills equal `main` and hold the paragraph.

## The rerun in Work

The owner ran prompts 1 to 3 again in one new Work chat on `0.1.0-alpha.1+4ce48c4beb7c`. [The record](S09-Work-validation.md#the-drawio-edit-rule-in-work) has the details. Asked again to open the draw.io file, add Cloud Monitoring and give back the updated file, the chat changed the model, rendered again and handed over the new bundle's `diagram.drawio` unchanged, and said the layout was recalculated. It wrote no draw.io file of its own. It did not show the new picture or link the bundle's other six files, and did not say that changes made by hand in draw.io are not carried over. The owner passed the run with those two gaps recorded (D-052).
