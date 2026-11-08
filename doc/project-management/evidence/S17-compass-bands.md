# North-South Bands and East-West Lines

Date: 2026-11-08 (Asia/Bangkok) | Decision: D-055 | Requirement: FR-068 | Implementer: Claude Opus 5.5 | Core: `0.6.0a1` to `0.7.0a1` | Branch: `codex/compass-bands`, from `main` at `186b26d`

## What the owner asked

The owner asked, translated from Thai, whether a drawing style could be set for a north-south and east-west network architecture. This session answered that views set only `direction`, `grouping` and `style`, so the picture cannot be asked for, and showed a Graphviz 16.1 trial in which `newrank` with `rank=same` held two nodes in different clusters on one row and `constraint=false` kept a line between them level. It proposed `bands` and `east_west_refs` on a view, and the owner answered "Yes, start".

## The contract

`View` gains two optional fields, so schema `1.0.0` stays and every existing model is unchanged:

- `bands`: at most 32 `Band` objects, `{id, entity_refs}`, from north to south. `entity_refs` holds 1 to 1000 IDs.
- `east_west_refs`: at most 4000 relationship IDs, drawn level.

Both hold only IDs, so FR-045 holds: no rank, weight or other Graphviz value reaches the model. Validation adds six codes, all fatal in both modes:

| Code | When |
|---|---|
| `VIEW_BAND_DIRECTION` | A view with bands or east-west lines is not `TB` |
| `VIEW_BAND_ID_DUPLICATE` | Two bands in one view share an ID |
| `VIEW_BAND_ENTITY_EXCLUDED` | A band names a declared entity the view does not select |
| `VIEW_BAND_CONFLICT` | An entity is in two bands |
| `VIEW_EAST_WEST_UNSELECTED` | An east-west line is declared but not selected |
| `VIEW_EAST_WEST_CONFLICT` | A line, alone or through a chain of lines, would join two bands |

An undeclared ID in a band is `REFERENCE_MISSING`, an undeclared line `VIEW_RELATIONSHIP_MISSING`, and a repeat in either list `REFERENCE_DUPLICATE`. `Levels` in `validation.py` holds the rows as a union of equal-level sets. Validation uses it to find conflicts, and the mapper uses the same class to build the rows it draws.

## Drawing

The normalized graph gains `bands`, each band's entities with the ends east-west lines join to it, and `levels`, each set of ends that joins no band. Both are empty in every reference view, so the 26 `*.graph.json` baselines gain two empty lists and nothing else, and every SVG and PNG digest is the one D-048 accepted. `scripts/update_visual_baselines.py` accepted them with that reason.

Only a view with bands or east-west lines changes the DOT:

- `newrank=true`, so a row can hold nodes in different clusters.
- Each band and level is a `rank=same` subgraph. Each band also holds an invisible marker, `band:<index>`, and invisible lines between the markers keep the bands in order.
- A group a band or level names gets an invisible anchor, as a group at the end of a line already does.
- A line whose ends are both in bands, or on one level, takes `constraint=false`, so no line moves a row.
- A labeled line within one row carries its text as `xlabel`.
- With two or more bands, every entity no band names gets a weightless invisible line from the first band's marker and one to the last band's marker.

No layout line touches an entity in a band, so none can double a drawn line. The draw.io copy reads only the graph's own nodes and lines, so it leaves the markers out.

## Trials

Each trial rendered `tests/fixtures/compass-valid.json`, a synthetic two-region AWS model with customers, an on-premises router, VPC peering and database replication. Its second view is the same selection without bands.

| Trial | Result |
|---|---|
| Bands as `rank=same` only | The app servers and databases sat level, and both east-west lines ran straight across. Customers were on the first rank, but so were the peering's VPC anchors and the empty Subnet A2, so the AWS boxes rose far above the customers |
| First band `rank=source`, last `rank=sink` | No change. Under `newrank`, Graphviz 16.1 still put the loose anchors on the first rank |
| Weightless lines from north and to south for every unbanded node | Customers above every box and the router below every box. Kept |
| Replication label as `label` | dot gave the label a rank of its own, so the level line bent up through it, and App B's line to its database went around it |
| Level line labels as `xlabel` | The line stayed level with its text above. Kept |
| Order lines through each band's first entity | The `render-smoke` lane's straight-line check failed on the load balancer's line to App A: the order line ran between the same two entities, and dot spread the pair apart and curved the drawn one |
| Order and holding lines between invisible band markers | Every line straight, with the same rows. Kept |
| VPN left unbanded | It landed on the data row between the two databases, and the replication line went over it. The guide now says to band such a node, and the fixture gives the VPN a `transit` row |

The final picture draws customers, the load balancer, both app servers on one row, both databases on one row with replication level between them, VPC peering level between the two VPC boxes, the VPN, and the on-premises router at the bottom.

## Guidance

The shared model guide has a section on north-south bands and east-west lines, with the rules above and an example, and both skills' step 4 says to use it when the user asks for a north-south and east-west network picture or for rows such as Internet, edge, application, data and on-premises. The core contract and FR-068 record the fields, codes and drawing.

## Tests

- `tests/test_contract.py`: the fixture validates strict, 12 contradiction cases in both modes each give their code and path, five bounded-value cases give `SCHEMA_FIELD_INVALID`, a view without bands keeps `LR`, and `Levels` joins lines to a band or keeps them apart.
- `tests/test_render_smoke.py`: from the SVG, each band's icons share a row and the rows run in order, customers are above every AWS box and the router below them, and both east-west lines are level. From the DOT, views without rows get no `newrank`, `rank=same`, `xlabel` or weightless line, every line in the banded view takes `constraint=false`, level labels are `xlabel`, an unbanded end keeps its line's constraint, and one band holds nothing else. A band that names a group with no line of its own holds the group's anchor on that row, and the group's box reaches it. The fixture also runs through every fixture-wide render check, including the straight-line check and the draw.io copy.

Each of 14 sabotage edits, one per rule above, failed a named test: the six validation checks, the joined ends of a level, `newrank` for every view, no `rank=same`, no `constraint=false`, labels instead of `xlabel`, no holding lines, order lines through each band's first entity, and no anchor for a banded group.

## Reproduction

- The core reproduces from a new clone of `3058eb6`: the same wheel, SHA-256 `332afdee0d354356472680cf5f65c968e5dc296a45d7ec6d889f3dc209834d0d`, and all 26 reference views match by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## Review

On the owner's word, "Start review", Claude Fable 5.1 reviewed `186b26d..000c024` in a fresh agent on its own clone, started at High, though it could not confirm that effort from inside the run. It read the evidence and the diff, ran 22 probe models of its own through every grouping, lenient fallback, groups in bands and lines to their own containers, ran the four changed lanes with 611 tests, and ran the whole gate, which passed every lane at `000c024`.

**It requested changes, with no P0 or P1 finding.** Nothing crashed, nothing invalid reached the renderer, every view without bands kept its DOT, and nothing from the model reaches Graphviz but quoted node IDs.

| ID | Severity | Finding |
|---|---|---|
| F1 | P2 | Icons on one band line up only when their nodes hold as many text lines. dot puts the middles of a rank's nodes on one line, and an icon sits at the top of its node, so in a Kubernetes detail view a Pod with nine lines had its icon 50 pt above one with three |
| F2 | P2 | A level line meets a node at its middle, which in a top-down view is below the icon once the text runs long, so the line's arrow lands on the text |
| F3 | P2 | The holding lines to and from every unbanded node took a point on every rank they crossed, and a Kubernetes detail view with two one-entity bands grew from 1269 × 1053 pt to 2393 × 1543 pt |
| F4 | P3 | The guide and the core contract said no group's box is drawn above the first band, but a box that holds a banded entity wraps it, as the fixture's External box does |
| F5 | P3 | A level line between an entity and its own VPC pulls the VPC's anchor onto the entity's row, and the VPC's peering then went 334 pt around what lay between |
| F6 | P3 | No test had a row with unequal text or a level line between icon nodes with notes |

This session confirmed F1 and F3 from the reviewer's probe output, and F2 in its own render of the fixture.

## Fixes after the review

On the owner's word, "Yes, fix them", Claude Opus 5.5 fixed F1, F3, F4 and F6, and recorded F2 and F5 as limits.

- **F1:** each icon node on a row is as tall as the row's tallest text, so the icons line up and a shorter text sits lower under its icon. The reviewer's Pods now have their icons at the same height, and so do its PersistentVolumeClaim and PersistentVolume.
- **F3:** an unbanded node takes a holding line from north only when no other line ranks it below anything, and one to south only when none ranks it above anything. The lines `_arrange` adds count as ranking lines. The reviewer's view is now 1464 pt wide, against 1269 pt without bands and 2393 pt before, and the fixture's picture does not change. Without the line from north, dot happened to keep a node with no lines off the first row in this session's probes, so that line is a safeguard that a DOT-level test guards.
- **F2, a limit:** no Graphviz setting lets a line end on part of a node. With F1, a level line meets the icons while the row's tallest text runs to three lines, and a test holds that. The guide says to keep names short on such a row. A node built as a table with a port on its icon would fix it, but that changes how the SVG is checked and how the draw.io copy is read, so it is left for later.
- **F4:** the guide and the core contract now say that no entity outside the bands, and no box that holds none of their entities, is drawn above the first or below the last.
- **F5, a limit:** the guide says to draw no level line between an entity and a box that holds it.
- **F6:** four new render tests: icons line up on a row whose texts differ, a level line meets icons whose text runs to three lines, a node already ranked takes no holding line, and two bands keep the Kubernetes detail view within a quarter of its width without them.

Each of five sabotage edits failed a named test: no row height, holding lines to every node from north or to south, no holding line from north, and `_arrange`'s lines left uncounted. The local gate passes 16 of 17 lanes with 2,374 tests, and `release-audit` waits for a reproduction proof of the fixed source. The Work plugin becomes `0.1.0-alpha.1+f6e08e40e0cf`.

- The fixed core reproduces from a new clone of `a04e5b1`: the same wheel, SHA-256 `af26930fb84bb45c9b2891d196fa2da22184bedbc56d87463b00473f2bd6345d`, and all 26 reference views match by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## Recheck of the fixes

On the owner's word, "Start recheck", the same Claude Fable 5.1 agent reviewed `000c024..0ddd2cc` on its own clone. It confirmed F1, F3, F4 and F6 fixed, with icons on each row and level at a spread of 0.0 pt and the Kubernetes detail view 1464 pt wide with two bands and 1378 pt with three, and accepted F2 and F5 as limits. It ran the four changed lanes with 615 tests and the whole gate, which passed every lane at `0ddd2cc`.

**It requested changes again, with no P0 or P1 finding.**

| ID | Severity | Finding |
|---|---|---|
| F7 | P2 | A regression from the F3 fix: an unbanded node with lines both in and out took no holding line, so a node on a loop, such as a line to itself, two lines each way between two caches or a loop of three, could lose its ranking line when dot turned a line round to break the loop. Cache A then sat on the top row and the AWS boxes rose above north. Before the fix all three were held |
| F8 | P3 | An unbanded node whose only line runs into the first band rose above north, before and after the fix, because that line and the holding line from north form a loop and dot turned the holding line round |
| F9 | P3 | The fixture without its `transit` band grew from 1333 to 1639 pt wide after the F3 fix |

This session reproduced F7 with two caches each way, which put the AWS box above the customers.

## Fixes after the recheck

On the owner's word, "Yes, fix them", Claude Opus 5.5 fixed F7 and F8 and measured F9.

- **F7:** every unbanded node on a loop of ranking lines, found as a strongly connected component, takes both holding lines, and a line from a node to itself ranks nothing. Other nodes keep the narrower holding of the F3 fix.
- **F8:** a line into the first band from outside the bands, or out of the last band, takes `constraint=false` and ranks nothing, because it could hold only with an end above north or below south. The guide says such a line is drawn running up or down as it must. dot already turned a line out of the last band round by itself, so a DOT-level test guards that half.
- **F9, measured:** the view is still 1639 pt wide. Its rows and lines are correct, and the width comes from dot placing the customers to the right of the AWS box. The Kubernetes width test still holds the case F3 was about.
- Fable's probe script run against this tree draws every probe with no unbanded node above north or below south, no box above north, and icon spreads of 0.0 pt on every row.
- Six new render tests: five cases of lines among unbanded nodes, each keeping the nodes and the AWS boxes between north and south, and one on the DOT for lines into north and out of south. Each of five sabotage edits failed a named test: no holding for loops, a loop search that finds nothing, self-loops ranking, and lines into north or out of south ranking. The local gate passes 16 of 17 lanes with 2,380 tests, `release-audit` waits for a reproduction proof of this source, and the Work plugin becomes `0.1.0-alpha.1+74c5538a3c35`.
- The core reproduces from a new clone of `03bdb6b`: the same wheel, SHA-256 `3e1345e57e5d3e448298054f76be61a2c9009212fe85e05c9e1c90e352ca3cff`, and all 26 reference views match by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## Second recheck

On the owner's word, "Yes, fix them", the same Fable agent reviewed `0ddd2cc..03bdb6b` on its own clone. It confirmed F7 fixed for every loop among the lines it drew, including loops through a banded node, a level's anchor, a plain group's anchor and `_arrange`'s lines, confirmed F8 fixed, and accepted F9 as measured. It ran the four changed lanes with 621 tests, and the gate passed every lane but the reproduction test, which waited for its proof.

**It requested changes, with no P0 or P1 finding.**

| ID | Severity | Finding |
|---|---|---|
| F10 | P2 | A chain of unbanded nodes from a lower band back up to a higher one, such as the database to two nodes to the load balancer, or one node from the VPN's band to App A's, is a loop only through the bands' order, which the loop search did not see. Its nodes took no holding line, one fell to the south row, and the AWS box reached about 240 pt below the on-premises router. `000c024` held both cases |

This session reproduced F10 with Fable's probe script.

## Fixes after the second recheck

On the owner's word, "Yes, finish it", Claude Opus 5.5 fixed F10 as Fable suggested: the loop search counts each row, band or level, as one node and adds the bands' order as lines, so a node on a loop through the rows takes both holding lines. Fable's two probe scripts, 32 probes in all, draw no unbanded node above north or below south and no AWS box outside them, with icon spreads of 0.0 pt on every row. The fixture's picture and the Kubernetes width do not change. Two new cases join the test of lines among unbanded nodes, and each of two sabotage edits, rows left out of the loop search and the bands' order left out, failed both. The local gate passes 16 of 17 lanes with 2,382 tests, `release-audit` waits for a reproduction proof of this source, and the Work plugin becomes `0.1.0-alpha.1+2df5c202a539`.

- The core reproduces from a new clone of `f6f4841`: the same wheel, SHA-256 `43d4dab0d0373f5a0a30dc1ce8171800107801f6267c7cfe6a71fd3caa80ab4d`, and all 26 reference views match by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## Third recheck

The same Fable agent reviewed `bc5f728..f6f4841` on its own clone. It confirmed F10 fixed and found no false loops: every earlier probe kept its width, and only true loops changed. It ran the four changed lanes with 623 tests, and the gate passed every lane but the reproduction test, which waited for its proof.

**It requested changes, with no P0 or P1 finding.**

| ID | Severity | Finding |
|---|---|---|
| F11 | P2 | The loop search folds each level into one node, but the holding check looked up each node by its own ID, which never appears among the folded names. So an end of a free level on a loop, such as two databases drawn level, each replicating both ways with a reader, took no holding line, rose to the top row and lifted the AWS box above north |

## Fix after the third recheck

F11 was a bug in the F10 fix the owner had approved, so Claude Opus 5.5 fixed it as part of finishing F10: each node is looked up as its row in the loop search's result. Fable's three probe scripts, 44 probes in all, now keep every unbanded node and the AWS box between north and south, and the two F11 probes are 1846 pt wide, as Fable measured with the same patch. A new test draws two levelled databases each with a two-way reader, and putting the bug back fails it. The local gate passes 16 of 17 lanes with 2,383 tests, `release-audit` waits for a reproduction proof of this source, and the Work plugin becomes `0.1.0-alpha.1+fee9566f6d58`.

- The core reproduces from a new clone of `1435e98`: the same wheel, SHA-256 `bbdb472318a8e9ae9e05aa1f09e435fb6d793fb6666c71f48aa61bceaec91b9f`, and all 26 reference views match by both routes, with no mismatch. With that [proof](S10-core-reproduction-proof.json), `release-audit` passes its 67 tests.

## Fourth recheck

The same Fable agent reviewed `3e21947..1435e98` on its own clone. **It approved S17, with no finding at P2 or above.** It confirmed F11 fixed, and checked that the lookup cannot give a holding line to a banded node, since those are skipped first, and that a looped band row cannot mark a free level's end. Its three probe sets, 44 probes, render strict with every unbanded node and the AWS box between north and south, the bands in order, and icon spreads of 0.0 pt on every row. Against `f6f4841`, no view without a loop through a level changed width. It ran the four changed lanes with 624 tests, and the gate passed every lane but the reproduction test, which waited for its proof.

It would leave four P3 items open: F2 and F5, which the guide records as limits; F9, a view 1639 pt wide against 1333 pt at `000c024`, with correct rows; and the top-down legend stretched to the full height of every top-down view, which predates S17.
