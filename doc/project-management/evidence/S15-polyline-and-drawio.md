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

Not done when this was written: the reproduction proof, which follows in the next commit because it clones this one, an independent review, the owner's review of the 15 changed views, an install, and a run in Work.
