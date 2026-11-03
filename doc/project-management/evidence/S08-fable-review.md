# S08 / M4 review by Fable

Date: 2026-11-03 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session, which set its effort to High. The reviewer cannot read that setting, so it reports its effort as unverified from its side. This is the M4 review under [D-021](../decisions.md#confirmed-user-direction). Claude Opus 5.5 and Claude Sonnet 5.5 wrote the work, so reviewer and implementers share a vendor.

**Disposition at `1ee4a58`: changes requested, on two P2 findings.** There are no P0 or P1 findings, and nine more are P3. The reviewer found the model semantics true to the briefs otherwise. The [recheck](#recheck-at-b00b90d) found that the first fix for P2-1 was incomplete, with a new P2 that is fixed in turn and needs a further recheck.

## Identity and scope

- Base `02dc709`, head `1ee4a58`, which passed actual CI [run 41658114802](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41658114802).
- The reviewer edited nothing tracked, and its full gate passed 15 lanes and 1,228 tests.
- It did not check timing numbers, the official provider pages or color fidelity, the Thai sample image, a second machine, or 12 of the 14 sabotage changes. It reran the other two.

## Findings

The root session reran P2-1 and P3-1, and read the others.

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| P2-1 | A boundary could nest in a scope it does not declare. The new rule guarded resources only, so an NSG owned by one resource group sat under another's box, which is the same false ownership reading as the OBS case | Azure fixture with the region scoped to `rg-net` and the NSG, owned by `rg-app`, located in it: the NSG nested under `rg-net` | Fixed for this shape at `b00b90d`, with tests over three orders. The second pass there did not make the tree independent of order in general; see P2-3 |
| P2-2 | The T-004 edit test was a tautology and rendered nothing, while the evidence claimed the check | `tests/test_references.py`: the set equality held by construction | Fixed. It renders both models and requires every shared node, group and edge to be identical, with only the cluster added |
| P3-1 | The record's "about 2300x3800" for the AWS fixture was false at the head. That figure came from before later margin and note changes, and this session did not remeasure it | 2803x4785 at the head; 1868x5292 at the base | Fixed in the evidence |
| P3-2 | A left-right edge arriving from above stops at the node's invisible top, up to the label's height from the icon | 89 pt in the hybrid overview's replica arrow | Stated in the deviations for the owner. Not changed |
| P3-3 | In T-003 the external load balancer and the GKE Ingress read as two in series, while the GKE controller would provision that load balancer | Read only | Fixed in the model's assumptions: the load balancer is managed outside the cluster, and an in-cluster controller serves the Ingress |
| P3-4 | T-006's link mix came from a layout sweep, and only the evidence said so | Read only | Fixed in the model's assumptions |
| P3-5 | The baseline tool removed the baselines before rendering, and kept scratch in a tracked folder | Read only | Fixed: it renders under `reports/` first |
| P3-6 | "From 180" and "from 140" overstated thresholds taken from a scan in steps of 10 | 175 publishes at 27.4 Mpx, and a line of 135 is refused | Fixed in the evidence and P-031 |
| P3-7 | A change reaching only the SVG left identical before and after images | Read only | Fixed: the lane also writes the current SVG |
| P3-8 | A subnet with no path to any network accepts any `network_ref`, which predates S08, and the contract did not describe the VLAN and VRF lookup | Reviewer's probe | The contract now states the lookup. The hole stays open for the owner |
| P3-9 | The row test used one size and one direction | Read only | Fixed: four more sizes and both directions |

## Recheck at `b00b90d`

The same reviewer checked `1ee4a58..b00b90d` and **requested changes on one new P2**. The other fixes held, including the P2-1 shape over all 5,040 orders. CI passed at that head, [run 41662654248](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41662654248), with 1,241 tests. The root session read the code and added its own test of the same selection, and did not repeat the 300-order scan.

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| P2-3 | `_settle_scopes` revisited only a group whose current parent was wrong, never one that had skipped a candidate which later moved. So the tree of a valid model still depended on `entity_refs` order, and a node pool could land outside its cluster, against FR-018 | A provider view of `gcp-shared-vpc.json` with the projects, VPC, subnet, cluster, pool, Node and region selected: reversed order put the pool in its project, and 166 of 300 random orders differed | Fixed: every group is recomputed in ID order until none moves. Tests shuffle that selection 60 times and every reference view 12 times, and a nesting loop runs in three orders |
| P3-10 | The GCP assumption denies a GKE-provided controller, while the model still named the controller `gke-ingress` and the edge "To the GKE Ingress" | Read only | Fixed: renamed and reworded, with a baseline update |
| P3-11 | This record said a second pass made the result independent of order, which was false, recorded High although the reviewer could not confirm it, and said three sizes where the test adds four | Reviewer's reading | Fixed here |

## What held

Per the reviewer: all 26 view sizes and the measurement table match; invisible layout edges never reach the SVG; `_arrange` handled empty and nested groups in four groupings and both directions; no over-rejection from the wider subnet lookup; and every requested component is present with no link outside the briefs. It inspected ten images and found them consistent with the evidence.

## Disposition

| Findings | State |
|---|---|
| P2-1, P2-2, P3-1, P3-3 to P3-7, P3-9 | The recheck confirms them, with P2-1 completed by the P2-3 fix |
| P2-3, P3-10, P3-11 | Fixed; further recheck pending |
| P3-2, the rest of P3-8 | Open for the owner |

The model strategy lets P3 findings wait, and this session fixed those that were cheap or that corrected its own record. This approves nothing beyond what it states, and it does not replace the owner's inspection of the output.
