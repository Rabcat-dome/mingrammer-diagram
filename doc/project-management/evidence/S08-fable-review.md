# S08 / M4 review by Fable

Date: 2026-11-03 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) / High, in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session. This is the M4 review under [D-021](../decisions.md#confirmed-user-direction). Claude Opus 5.5 and Claude Sonnet 5.5 wrote the work, so reviewer and implementers share a vendor.

**Disposition at `1ee4a58`: changes requested, on two P2 findings.** There are no P0 or P1 findings, and nine more are P3. The reviewer found the model semantics true to the briefs otherwise. The fixes below need a recheck.

## Identity and scope

- Base `02dc709`, head `1ee4a58`, which passed actual CI [run 41658114802](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41658114802).
- The reviewer edited nothing tracked, and its full gate passed 15 lanes and 1,228 tests.
- It did not check timing numbers, the official provider pages or color fidelity, the Thai sample image, a second machine, or 12 of the 14 sabotage changes. It reran the other two.

## Findings

The root session reran P2-1 and P3-1, and read the others.

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| P2-1 | A boundary could nest in a scope it does not declare. The new rule guarded resources only, so an NSG owned by one resource group sat under another's box, which is the same false ownership reading as the OBS case | Azure fixture with the region scoped to `rg-net` and the NSG, owned by `rg-app`, located in it: the NSG nested under `rg-net` | Fixed. The rule covers boundaries, and a second pass makes the result independent of selection order, with tests over three orders |
| P2-2 | The T-004 edit test was a tautology and rendered nothing, while the evidence claimed the check | `tests/test_references.py`: the set equality held by construction | Fixed. It renders both models and requires every shared node, group and edge to be identical, with only the cluster added |
| P3-1 | The record's "about 2300x3800" for the AWS fixture was false at the head. That figure came from before later margin and note changes, and this session did not remeasure it | 2803x4785 at the head; 1868x5292 at the base | Fixed in the evidence |
| P3-2 | A left-right edge arriving from above stops at the node's invisible top, up to the label's height from the icon | 89 pt in the hybrid overview's replica arrow | Stated in the deviations for the owner. Not changed |
| P3-3 | In T-003 the external load balancer and the GKE Ingress read as two in series, while the GKE controller would provision that load balancer | Read only | Fixed in the model's assumptions: the load balancer is managed outside the cluster, and an in-cluster controller serves the Ingress |
| P3-4 | T-006's link mix came from a layout sweep, and only the evidence said so | Read only | Fixed in the model's assumptions |
| P3-5 | The baseline tool removed the baselines before rendering, and kept scratch in a tracked folder | Read only | Fixed: it renders under `reports/` first |
| P3-6 | "From 180" and "from 140" overstated thresholds taken from a scan in steps of 10 | 175 publishes at 27.4 Mpx, and a line of 135 is refused | Fixed in the evidence and P-031 |
| P3-7 | A change reaching only the SVG left identical before and after images | Read only | Fixed: the lane also writes the current SVG |
| P3-8 | A subnet with no path to any network accepts any `network_ref`, which predates S08, and the contract did not describe the VLAN and VRF lookup | Reviewer's probe | The contract now states the lookup. The hole stays open for the owner |
| P3-9 | The row test used one size and one direction | Read only | Fixed: three more sizes and both directions |

## What held

Per the reviewer: all 26 view sizes and the measurement table match; invisible layout edges never reach the SVG; `_arrange` handled empty and nested groups in four groupings and both directions; no over-rejection from the wider subnet lookup; and every requested component is present with no link outside the briefs. It inspected ten images and found them consistent with the evidence.

## Disposition

| Findings | State |
|---|---|
| P2-1, P2-2 | Fixed; recheck pending |
| P3-1, P3-3 to P3-7, P3-9 | Fixed; recheck pending |
| P3-2, the rest of P3-8 | Open for the owner |

The model strategy lets P3 findings wait, and this session fixed those that were cheap or that corrected its own record. This approves nothing beyond what it states, and it does not replace the owner's inspection of the output.
