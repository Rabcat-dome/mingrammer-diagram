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
