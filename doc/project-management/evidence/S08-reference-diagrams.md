# S08 — Reference Diagrams and Appearance

Date: 2026-11-03 | Tasks: M4-01..05 | Branch: `codex/s08-reference-diagrams`, from `main` at `02dc709` | Package: `0.5.0a1`

**Result: M4 is implemented and is not closed.** [Fable/High approved](S08-fable-review.md) it at `a407a7a`, which passes actual CI [run 41664850907](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41664850907) with 1,250 tests. It still needs the owner's inspection of the samples. The numbers below are from the local gate at the commit named in [validation](#validation).

## Task status

| Task | Status | Result |
|---|---|---|
| M4-01 | Implemented | AWS, Azure, GCP, Huawei and on-premises models under `tests/fixtures/references`, with expected semantics in `tests/test_references.py` |
| M4-02 | Implemented | `hybrid-five.json` holds all five environments, with typed links and a trust zone in each |
| M4-03 | Implemented; owner inspection pending | TB and LR, legends, English and Thai labels, disclosed omissions, [provider references and deviations](#provider-references) |
| M4-04 | Implemented | The `visual-regression` lane, reviewed baselines, and [measurements](#measurements) with icon views |
| M4-05 | Implemented | A namespace view and a worker-placement view for EKS, AKS, GKE, CCE and on-premises in the same models as their cloud views, with one namespace view in the hybrid |

## Exit criteria

| Criterion | State | Evidence |
|---|---|---|
| Six reference families and their Kubernetes subviews inspected by the owner and reviewer | **Open** | This session and the reviewer inspected images, and [Fable/High approved](S08-fable-review.md) at `a407a7a`. The owner's inspection remains |
| T-017 passes | Met in tests | [Kubernetes checks](#scenario-checks), together with the `provider-semantics` lane |
| All required catalog entries have resolution and rule fixtures | Met | `provider-semantics` and `render-smoke`, which require every type and rule to have a fixture and a render |
| Performance measurements recorded | Met | [Measurements](#measurements) and the [raw numbers](S08-render-measurements.json) |
| P1 automatic splitting and 200 / 300 stress deferred explicitly | Met | Automatic splitting is not implemented. [P-031](../decisions.md#recommendations-and-disposition) records what 200 / 300 means now |

## Reference scenarios

Every model is synthetic, sets `metadata.environment` to `reference` and lists every choice its brief did not supply in `metadata.assumptions`. Each entity and relationship reaches at least one view, and the validator lists what each view leaves out. The images are the [reviewed baselines](../../../tests/baselines).

| Scenario | File | Entities / relationships | Views, with PNG size in pixels |
|---|---|---|---|
| T-001 | `aws-three-tier.json` | 40 / 21 | `overview` 3163x3100, `zones` 1333x1654, `eks-namespaces` 1687x1741, `eks-nodes` 833x1341 |
| T-002 | `azure-hub-spoke.json` | 38 / 17 | `overview` 1949x2018, `ownership` 1342x2015, `aks-namespaces` 1687x1797, `aks-nodes` 833x1257 |
| T-003 | `gcp-shared-vpc.json` | 33 / 18 | `overview` 1593x1372, `locations` 1075x1339, `projects` 1493x1522, `gke-namespaces` 1631x1928, `gke-nodes` 833x1194 |
| T-004 | `huawei-web.json` | 39 / 18 | `overview` 1958x2329, `zones` 950x1625, `services` 950x1398, `cce-namespaces` 1631x1809, `cce-nodes` 950x1489 |
| T-005 | `onprem-physical-logical.json` | 50 / 13 | `physical` 1745x1981, `logical` 2153x3139, `k8s-namespaces` 1519x1836, `k8s-nodes` 616x1087 |
| T-006 | `hybrid-five.json` | 46 / 19 | `overview` 2078x3261, `connectivity` 950x2901, `data-flows` 2724x3293, `k8s-detail` 1117x1197 |

All 26 views publish at PNG scale 1.0, and the largest is 9.8 megapixels against the limit of 32.

### Scenario checks

`tests/test_references.py` runs in the `render-smoke` lane, and each check goes through the real validator and renderer.

| Scenario | Inspect | Reject | Edit check |
|---|---|---|---|
| T-001 | One ALB with both subnets; security groups, S3, CloudWatch, NAT and Internet gateway present; the AZ stays noted when its box is left out; HTTPS and application-to-database labels | An instance whose subnet is in another AZ: `PLACEMENT_SUBNET_ZONE_MISMATCH` | Rename a tier and add an instance; IDs and edges stay |
| T-002 | The VM nests by subnet in `overview` and by resource group in `ownership`, and neither view implies the other; NIC attachment and NSG are explicit; the peering is the only link joining hub to spoke | An attachment to another VNet's subnet: `PLACEMENT_SUBNET_NETWORK_MISMATCH` | Add a second spoke; only its own link appears |
| T-003 | The VPC has no region, and its subnets span two; a workload nests by service project while the VPC sits in the host project | A workload on a subnet in another region: `PLACEMENT_REGION_MISMATCH` | Move a workload to another zone; its ID and subnet stay |
| T-004 | All 12 required services draw their approved icon with no fallback; the bundle and image state the private-use limit; OBS does not sit in the IAM project's box; the egress path is only what is stated | Covered by the existing Huawei rules in `provider-semantics` | Add the CCE detail to the web model; the web IDs stay |
| T-005 | One server nests by rack in `physical` and by subnet in `logical`, keeping its ID and type; a firewall and a VM keep every overlapping membership | A subnet paired with a network it reaches only elsewhere: `PLACEMENT_SUBNET_NETWORK_MISMATCH` | Move a server to another rack; its logical memberships stay |
| T-006 | All five environments in the overview; links are the four stated ones, each touching on-premises, so no mesh; the legend tells link kinds from data flows; a trust zone per environment; the cluster stays compact, and its detail is disclosed | Covered by the generic check that a view draws exactly what it selects | Add a stated link; every other edge stays identical |
| T-017 | Ingress to Service to Pod, Deployment to ReplicaSet to Pod, and PVC to PV; each Pod sits in its namespace in one view and on its Node in the other, with the other fact as a note; a Pod with no Node reads `node: unspecified`; the cluster keeps its ID and provider across views | A namespace from another cluster: `K8S_NAMESPACE_MISMATCH`. A Secret with a value: `SCHEMA_FIELD_INVALID` | Covered above; each view keeps the same IDs |

Checks on every reference: strict validation with only the expected warnings, each view draws exactly what it selects, each left-out ID is disclosed, the first view draws in both directions with a matching legend, and every view stays at full PNG size. A Thai variant of the AWS overview renders strictly with the same IDs and uses Noto Sans Thai.

T-006's edit check differs from S01 in one way. The model already has an on-premises to Huawei link, so the test removes it and adds it back.

## Provider references

Pages opened on 2026-11-03 in the built-in browser. Official images are compared by eye and not stored here, because their copyright belongs to the providers. Border and fill colors in `GROUP_STYLES` are approximated from these images, and are not taken from a published specification. This is the T-016 comparison so far; the owner's acceptance is still open.

| Provider | Reference | What it shows | Used here |
|---|---|---|---|
| AWS | [VPC with servers in private subnets and NAT](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-example-private-subnets-nat.html) | A region box, dashed AZ columns, a green VPC, filled subnets, a red security group, and a label below each icon | Region and AZ borders, the VPC border, a subnet fill, the security-group border. `zones` gives AZ columns |
| Azure | [Hub-spoke network topology](https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke) | Dashed blue VNets, dotted gray subnets, no fill, and peering between VNets | VNet and subnet borders with no fill |
| GCP | [Shared VPC](https://docs.cloud.google.com/vpc/docs/shared-vpc) | Dashed gray projects, a light blue VPC, light green regions and light purple subnets, with service projects beside the host | All four treatments, and `projects` for the host and service split |
| Huawei | [Single-region e-commerce reference](https://support.huaweicloud.com/intl/en-us/usermanual-architecture/architecture_02_0115.html), updated 2025-05-22 | A thin solid region, dashed AZs, and a top-down flow. That page draws text boxes, not icons | Region and AZ borders, top-down direction, and `zones`. Icons stay the D-018 library |
| On-premises | None; a neutral notation under D-010 | Not applicable | Neutral borders, with security zones dashed red |
| Hybrid | No single reference; S01's left-right recommendation | Not applicable | Left-right, with a tint per provider box |

### Deviations

| Scope | Deviation | Why |
|---|---|---|
| AWS | AZ boxes do not cross the VPC. `overview` notes the AZ on each subnet, and `zones` draws AZ columns without the VPC | One box per entity: a cluster has one parent, and drawing an AZ inside a VPC would state a false hierarchy |
| AWS | Public and private subnets share one fill | The model has no such attribute, and reading it from a name would be a guess. The name says it |
| AWS, Azure, Huawei | A security group or NSG is an empty box, with `security:` notes on its members, not a box around them | A member usually has a subnet too, and nesting takes one parent |
| Azure | Peering is a bold blue line, not dotted | Dotted already means management, membership and policy here |
| Azure, GCP | `overview` leaves out subscription, resource groups and projects, which `ownership` and `projects` show | S01 asks that ownership stay apart from the network |
| GCP | Regions are not nested inside the VPC | A VPC is global and a region is not its child in the model. `locations` draws by region |
| All | Group kinds are text, with no small corner icon. A group whose type has an icon holds it as a separate tile | Graphviz has no corner placement for an image in a cluster, and this tile is what an edge can reach |
| All | Layout comes from Graphviz, so tiers do not line up as in a hand-drawn diagram, and some edges cross notes | The automatic layout is the design. Fewer notes and a chosen direction reduce it |
| Left-right views | An edge arriving from above or below stops at the node's invisible top or bottom, up to the label's height from the icon. In the hybrid overview the replica arrow ends 89 pt above the Huawei database icon | The equal space above the icon keeps horizontal edges off the label, and it costs this. The owner can choose |
| Hybrid | Dedicated links use kind `peering`, with a label naming the product | The schema has no dedicated-link kind |

## What changed in the renderer

The contract's [presentation paragraph](../../design/core-contract.md) states these. [P-029 to P-031](../decisions.md#recommendations-and-disposition) record the choices, which the owner can change.

| Change | Why |
|---|---|
| A closed table of borders and fills per provider and kind, used only in a `provider`-style view | FR-048 |
| A provider box is tinted only when a view holds several | D-008 starts from a white background |
| Members with no edge form rows, through invisible edges that draw nothing | S07 recorded one long column. It trades height for width: the AWS catalog fixture went from 1868x5292 to 2803x4785 |
| A left-right icon sits at its node's middle | Edges landed on label text, as a live session and this session's inspection both found |
| A top-down legend lies flat, and an arrowhead appears only for a kind with a directed edge | Labels overprinted the vertical samples, and the legend showed arrows on undirected kinds |
| A declared subnet, zone or rack is noted even when not selected | A view can drop those boxes and keep the fact, which also removed the repeated boxes |
| A resource or boundary does not nest in a scope it does not declare or inherit, and groups settle in ID order until none moves | OBS was drawn inside an IAM project although its scope is the account, and the [review](S08-fable-review.md) showed a boundary could do the same and that selection order could change the tree |
| A word up to three characters past the label width stays whole | `PersistentVolumeClaim` broke before its last letter |
| More canvas and group margin | A wide label touched the canvas edge in `logical` |

**The row layout moved the limit numbers.** Unconnected icons no longer form a tall image, so the S07 size tests now use a connected top-down line, and S07's figures, such as "0.608 at 197", describe the earlier layout.

## Findings from building it

| Finding | Effect had it shipped | Fix |
|---|---|---|
| A live session stopped at `mkdir`, because the skill said the output root must exist, although `render` creates it | The plugin produced no image in a session without broad permissions | The skill now says so, and a new session renders. See the [M7 evidence](M7-claude-plugin.md) |
| `subnet_networks` looked one hop, so a subnet that reaches its network through a VLAN and VRF was not checked. Found by the agent writing T-005, and reproduced here | A resource could pair a subnet with the wrong network and validate | The lookup follows VLAN and VRF, with a test on the wrong pair |
| OBS appeared under an IAM project | A false ownership reading, which S01's T-004 rejects | The nesting rule above |
| Agent worktrees were removed when an agent first stopped with no change, so five of the six resumed agents wrote in the shared checkout, and two collided in a shared scratch folder | A fixture briefly held another scenario's model | Each file was rechecked by its `metadata.id` and its tests. No agent changed code |

## Validation

The local gate passes **15 lanes and 1,250 tests with none skipped**, at Python 3.13.7, uv 0.13.0 and Graphviz 16.1.0. Actual CI [run 41658114802](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41658114802), job 125993790820, passed the same 15 lanes and tests at `1ee4a58` from a clean checkout on the runner, which is this same Mac, and its wheel matches the local build at SHA-256 `143ea72aed4e7a13e03d01a93dab3a8a2a0f96a711c78092831fb659413713e3`. That run had 1,228 tests, before the [review fixes](S08-fable-review.md) added 22. Actual CI [run 41662654248](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41662654248) also passed at `b00b90d` with 1,241.

| Lane | Tests | Work done |
|---|---|---|
| `render-security` | 228 | Tall views rebuilt, and a test that `render` creates a missing root privately |
| `render-smoke` | 293 | Adds `tests/test_references.py`, every reference view, and the presentation tests |
| `visual-regression` (new) | 65 | One structural and one image comparison per view, a check on the engine, and tests of the comparison itself |
| `claude-plugin` | 55 | The skill's sentence on the output root |
| Others | Unchanged in purpose | `schema-core` 91, `catalog-license` 76, `provider-semantics` 442 |

### The visual-regression lane

Each view's normalized graph must equal its [baseline](../../../tests/baselines), and its SVG and PNG must match the digests in `baselines.json`, which also records the engine and the reason for the last acceptance. A failure leaves before, after and diff images in `reports/visual-regression`. `scripts/update_visual_baselines.py --reason` is the only way to accept a change, and it should run only after someone has looked.

The graph is host-independent, so it should hold on any machine. The image comparison is exact, and NFR-001 does not promise byte-identical images across platforms, so another Graphviz build or a second machine will fail it. Its engine check names that cause, and M6 decides what tolerance two machines need.

The baselines hold Huawei icons, under the same private-use limit as the fixtures and `reports/`. They are excluded from the sdist, are not in the wheel, and stay in this private repository's history.

### Sabotage checks

Each change went into the real source, ran its tests and was restored, and the files hashed the same afterwards.

| Change | Tests | Failed |
|---|---|---|
| Rows of loose members removed | `render-smoke`, `visual-regression` | 18 |
| A group style changed | `visual-regression` | 3 |
| Provider tint kept on one provider | `render-smoke` | 1 |
| Left-right icon back at the top | `render-smoke`, `visual-regression` | 6 |
| Legend arrow on every kind | `render-smoke` | 1 |
| Top-down legend samples upright | `render-smoke` | 1 |
| A box may imply another scope | `tests/test_references.py` | 1 |
| Subnet and zone notes dropped | `tests/test_references.py`, `render-smoke` | 3 |
| Long word broken again | `render-smoke`, `visual-regression` | 11 |
| Subnet network read one hop only | `tests/test_references.py` | 1 |
| A link invented in the hybrid | `tests/test_references.py` | 1 |
| Reference label changed | `tests/test_references.py`, `visual-regression` | 5 |
| Baseline image edited by hand | `visual-regression` | 1 |
| The skill says the root must exist again | `claude-plugin` | 1 |

All 14 failed their lane. The first try at the one-hop case left broken indentation, so its failure proved nothing. Repeated with valid code, `test_t005_rejects_a_subnet_paired_with_a_network_it_reaches_only_elsewhere` is the test that fails. The review fixes add three more: a boundary left out of the scope rule fails 3 tests, the second pass removed fails 2, and a web-view node that changes when CCE is added fails 1. The fix for selection order adds two more: settling in one pass fails 4, and working in selection order fails 2. That second change first passed every test, because a fixed point alone settles those shapes, so a shuffled test over nesting loops was added and now catches it.

## Measurements

From [`scripts/measure_render.py`](../../../scripts/measure_render.py) on one Apple M2 Max with 64 GiB, macOS 27.2, Graphviz 16.1.0, Python 3.13.7 and the bundled Noto fonts, with seven runs of each. Views use real icons, labeled nodes and labeled edges. Cold is a new CLI process, including `uv run`. Warm is a further render in a process that has already rendered. With seven runs, p95 is the slowest run. This sets no release threshold, and NFR-007 is P1.

| Size | Outcome | Cold p50 / p95 s | Warm p50 / p95 s | NFR-007 target |
|---|---|---|---|---|
| 30 / 50 | Published, 7.8 Mpx | 0.54 / 0.55 | 0.37 / 0.38 | Under 5 s |
| 100 / 150 | Published, 17.4 Mpx | 0.95 / 0.98 | 0.78 / 0.80 | Under 15 s |
| 150 / 225 | Published, 23.3 Mpx | 1.16 / 1.22 | 1.00 / 1.01 | None |
| 197 / 300 | Refused, `RENDER_PIXEL_LIMIT` | 1.81 / 1.83 | 1.65 / 1.67 | None |

**Where the limits bind.** With the relationship count at 1.5 times the entities, labeled views publish at every scanned size up to 170 entities, at up to 30.2 Mpx, and are refused at every scanned size from 180. A connected top-down line shrinks its PNG from 120 entities and is refused at every scanned size from 140. These are scan points in steps of 10 and size does not rise smoothly with entities, so neither is a sharp threshold: the reviewer's own run published 175 at 27.4 Mpx and refused a line at 135. Selecting more than 200 entities or 300 relationships is refused with `RENDER_VIEW_TOO_LARGE`, which is T-012's rejection evidence. So 200 / 300 is an upper bound, and these views reach the pixel limit first, each with exit 2 and a request to split. T-012's P1 part, 200 / 300 stability, stays deferred.

Time is far from any limit: the slowest run is 1.83 s against 55 s.

## Requirement coverage

| ID | State | Where it is checked |
|---|---|---|
| T-001..006 | Met in tests; owner inspection open | [Scenario checks](#scenario-checks) |
| T-012 | P0 rejection met; P1 deferred | [Measurements](#measurements) |
| T-014 | English and Thai rendering checked here; owner inspection open; M5 adds the privacy part | `test_thai_labels_render_strictly_with_the_same_ids` |
| T-016 | Compared with the pinned references; owner acceptance open; M6 repeats it | [Provider references](#provider-references) |
| T-017 | Met in tests for M4; M5 adds its part | [Scenario checks](#scenario-checks) |
| FR-018, FR-029 | Met in tests | The same, with `provider-semantics` |
| FR-042 | Met in tests; owner inspection open | Direction, legend, grouping and labels |
| FR-048 | Implemented with recorded deviations; owner acceptance open | [Deviations](#deviations) |
| NFR-006 | Met in tests | Each view draws exactly what it selects, and each left-out ID is disclosed |
| NFR-007 | Measured on one machine | [Measurements](#measurements) |
| NFR-014 | Thai variant rendered; one more sample for the owner | T-014 above |

## Limits and what this does not establish

- **One machine.** The CI runner is this same Mac, and macOS moved from 27.0 to 27.2 during this work, with no change seen in renders.
- **Automated checks find a missing label, not an unreadable one.** This session looked at most views, but the owner's eye is the check for readability and fidelity.
- **The reference comparison is by eye**, against one page per provider, and the colors are approximate.
- **Some assumptions came from layout, not architecture.** The hybrid's three dedicated links and one VPN were chosen after a sweep, because that mix drew with no link crossing a trust zone. Its assumptions state the choice, and a real design should not be read from it.
- **A view with both sides over 32767 pixels was never run**, as in S07.
- **A subnet with no path to any network accepts any `network_ref`**, which predates this work and which the [review](S08-fable-review.md) lists as P3.
- **A live session rendered only through `--plugin-dir`** on this branch. The installed copy gets the skill correction after a merge.
- Four P3 findings from the [S07 review](S07-fable-review.md) stay open: P3-1, P3-2, P3-3 and P3-5. P3-4 is fixed here. Three M7 P3 findings also stay open.
- Nothing is merged or released, and `main` still holds `02dc709`.

## Model and review

Claude Opus 5.5 (`claude-opus-5-5`) did the renderer, tests, baselines and records, in the session that started from the owner's request. Six Claude Sonnet 5.5 agents wrote the six models under its brief, and it then trimmed some view selections. The project policy names Sol/Medium for M4, so this is a recorded substitution, and no model setting changed.

Under D-021, Claude Fable 5.1 / High [reviewed `02dc709..1ee4a58`](S08-fable-review.md) in a fresh agent and **requested changes on two P2 findings**. A recheck found the first fix incomplete and raised a third, on selection order. All three are fixed, and it **approved `a407a7a`**. It shares a vendor with the implementing models.

## Next steps

1. The owner inspects the samples and settles the presentation choices in P-029 to P-031.
2. Close M4 after that. The open P3 findings stay open unless the owner wants them fixed first.
3. Then choose the next milestone.
