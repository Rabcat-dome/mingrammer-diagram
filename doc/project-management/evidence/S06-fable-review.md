# S06 / M2 fix review by Fable

Date: 2026-11-03 (Asia/Bangkok). Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) / High, in a fresh agent with no prior project context, started from the owner's Claude Opus 5.5 session. Under [D-020](../decisions.md#confirmed-user-direction) this is a recorded substitute for Astra/High, not an Astra review. The fixes were written by GPT-6 Astra / High.

**Disposition: changes requested, on one P2 finding.** F1, F2, F3 and F4 are fixed at their root. F5 is only partly fixed, which is finding N1. The other four findings are P3. There are no P0 or P1 findings. The reviewer states that if the owner explicitly dispositions N1 as out of scope for M2, the rest of this review supports approval.

## Identity and scope

- Base: `556945952fef1461c03451ba76ed3f652909edde`. Head: `dc54b4dc5a74ffa8c8680da72e3bef4ff08893ef`, branch `codex/s06-provider-catalogs`. The tree was clean at the start and end of the review, and the reviewer edited nothing in the repository.
- Reviewed the `src` and `tests` diff with the surrounding code, against the [original review](S06-astra-review.md) and the requirement IDs it names. The [fix evidence](S06-review-fixes.md) was given as claims to verify.
- Out of scope: rendering, visual acceptance, Work integration, the Huawei rights decisions and the earlier M7 fixes.

## Original findings

All probes ran in both `strict` and `lenient` modes.

| Finding | Verdict | Evidence |
|---|---|---|
| F1: ALB in two VPCs | **Fixed.** `max_networks: 1` on the ALB record | The original case and reversed attachment order give `PLACEMENT_NETWORK_COUNT_INVALID`. Subnets from two VPCs under one attachment give `PLACEMENT_SUBNET_NETWORK_MISMATCH`. One VPC split over two entries and EC2 in two VPCs stay valid. The real CLI returns `valid=false` and exit 2 in both modes |
| F2: subnet membership encodings | **Fixed.** `semantics.py:187-197`, used at 268-271, 274-284 and 407-409 | A relation-only mismatch is rejected for AWS, Azure, GCP and Huawei. Conflicting declarations give `BOUNDARY_NETWORK_COUNT_INVALID` in either order. A relation-only subnet in another region gives `BOUNDARY_REGION_MISMATCH`. Agreeing encodings and on-premises overlaps stay valid |
| F3: scope-reference order | **Fixed.** `semantics.py:163-185` | Azure, Huawei and GCP contradictions give `PLACEMENT_SCOPE_CARDINALITY` in every order tried, including on boundaries. Coherent lineages stay valid. Huawei enterprise projects stay independent |
| F4: contradictory Pod scheduling | **Fixed.** `semantics.py:634-656` | Reference/edge and edge/edge conflicts give `K8S_NODE_ASSIGNMENT_CONFLICT` on EKS, AKS, GKE, CCE and on-premises. Reversed edges and a Node named as a Pod's context are closed by existing rules. Repeated agreeing edges, unspecified placement, a Deployment over two Nodes and a NodePool edge stay valid |
| F5: EKS node group VPC | **Partly fixed.** `semantics.py:579-591` | Managed node groups are rejected in another VPC, in both VPCs, when declared before the cluster, and under Auto Mode. Different subnets in the same VPC and unspecified sides stay valid. Sibling types still pass; see N1 and N2 |

## New findings

### N1 — P2: self-managed EKS nodes may still declare a different VPC from their cluster

Location: `src/cloud_architecture_diagrams/semantics.py:580`, which hard-codes `aws.containers.eks_managed_node_group`.

```python
d = load("providers/aws")
clone(d, "boundaries", "vpc", "vpc-other")
clone(d, "boundaries", "app-a", "app-other", parent_ref="vpc-other")
item(d, "resources", "self-managed")["placement"]["network_attachments"] = [
    {"network_ref": "vpc-other", "subnet_refs": ["app-other"]}]
# observed: valid=True with no errors, strict and lenient
```

The rule's own source, [AWS EKS compute](https://docs.aws.amazon.com/eks/latest/userguide/eks-compute.html), lists Auto Mode managed nodes, self-managed nodes, managed node groups, Fargate and hybrid nodes. It then says the same-VPC requirement applies to nodes "excluding hybrid nodes". The claim recorded in `S06-source-checks.json` is therefore broader than the code that cites it. This is the F5 defect on the neighbouring catalog record, not a new requirement.

Fix direction: match the set of non-hybrid AWS NodePool types, or add a catalog flag on those records instead of a type literal. Keep the hybrid exemption, and add negative cases for each covered type alongside the same-VPC/different-subnet control.

### N2 — P3: a Fargate profile in another VPC is accepted

The N1 mutation applied to `fargate` returns `valid=true` in both modes. The Fargate pages constrain subnet privacy and refer to "your cluster's VPC", but do not state VPC membership outright, so the compute page covers Fargate only by inference. Either include it under N1 on that reading, or record the exclusion in the rule's remedy so it is a decision rather than an omission.

### N3 — P3: an EKS or Auto Mode cluster may declare subnets in two VPCs

Both records have `min_subnets` and `min_subnet_zones` but no `max_networks`, so a cluster attached to two VPCs returns `valid=true`. The original review limited F1 to the ALB, so this is outside its letter. The reviewer did not fetch the EKS network-requirements page and cites no source; the fix is one data field and a negative case once sourced.

### N4 — P3: a Pod on a Node in one pool may also carry a NodePool edge to another pool

Adding an edge `pod-a -> pool-b` while `pod-a.node_ref = node-a`, whose pool is `pool`, returns `valid=true`. The F4 fix direction said not to treat a NodePool target as a concrete Node, so this is a design gap rather than a defect against the review. The contract should either say NodePool edges are not reconciled with `node_ref`, or check that the Node's pool is among the declared pools.

### N5 — P3: `test_relation_only_subnet_still_checks_network_region` does not pin the fix

`tests/test_provider_semantics.py:275-285` moves `az-a` to another region, but `public-a` and `data-a` also sit in `az-a` with a `parent_ref`, so the existing path already emits the expected code. The test passes against the base source and would not fail if the relation-only region check were removed. Fix: give the subnet its own zone, or assert the diagnostic's `entity_id` is `app-a`.

## Regression and test checks

- Valid in both modes at the head: multi-VPC EC2, on-premises overlaps and VLAN-only membership, Huawei `[sub, proj, ep]` permutations, coherent Azure and GCP lineages, a different subnet in the same VPC, unspecified Pod placement, a Deployment over two Nodes, a Pod-to-NodePool edge and a generic Node in another network under EKS. The six baseline fixtures pass unchanged.
- One intended behaviour change: Huawei `[sub, proj, ep]` was rejected at the base and is accepted now, and a new test pins it.
- The new tests fail without the fixes, except N5. With base source and base catalog, 42 of 427 fail. With base source and head catalog, 40 fail. With head source and base catalog, 27 fail.
- Coverage gaps: N1 and N2 negatives, a managed node group attached to both VPCs and the Auto Mode variant, and relation-only mismatch fixture cases for Azure, GCP and Huawei.
- Catalog sources: the ALB creation page and the Kubernetes assignment page support their rules. The EKS rule is supported but under-implemented. The four subnet `max_networks` limits are consistent with previously recorded pages, which were not re-fetched.

## Checks and evidence boundaries

| Evidence | Result and attribution |
|---|---|
| Tests and static checks | Reviewer ran the two semantic test files (499 passed), the full `pytest` suite (637 passed), `ruff check`, `ruff format --check` and `mypy src` (clean) |
| Probes and removal runs | Reviewer ran its own probes through `validate_json`, one real CLI call on the F1 model, and three runs against source copies with the fixes removed. The probe script stayed in the session's temporary directory and is not in this repository |
| Primary sources | Reviewer fetched the AWS EKS compute, Fargate, Fargate-profile and ALB creation pages through a web-fetch agent, so it read summaries rather than raw pages |
| Root verification of the findings | Claude Opus 5.5, the session that started the review, independently reproduced N1, N2, N3, N4 and N5 with its own probes at `dc54b4d`, and read the AWS sentence in the raw page. This confirms the findings. It does not repeat the reviewer's conclusions that F1-F4 are fixed |
| Actual CI | Root verified [run 41488737943](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41488737943), job 125425825434, at `dc54b4d`: 12 lanes, 637 tests, none skipped, on `macbook-pro-m2-max-mingrammer` from a clean tree. The visibility guard read private, the wheel SHA-256 `f9ce65e5e99fd08e6d48b8d67459c0ddd0b63ad85bc436fa1c7fa9798ed1996a` matches the local build, and the job has no annotations |
| Not run by the reviewer | `scripts/quality_gate.py` and `scripts/catalog_checks.py` as scripts, the proof digest comparison, GitHub CI, re-fetching the subnet, Azure, Huawei and Kubernetes pages, and the EKS network-requirements page |

## Limits

- This is not the Astra/High review the model policy names for M2. D-020 records the owner's choice to substitute it for this review only.
- Fable shares a vendor with the model that wrote the original S06 implementation, though not with the model that wrote these fixes. It had no contact with either session. Different models reduce some shared assumptions and do not prove correctness.
- Probes exercise the public validation API and one CLI call. Nothing here is a runtime, deployment or reachability claim.

## Follow-up: N1 fix and deferrals

On the owner's instruction on 2026-11-03, Claude Opus 5.5 fixed N1 and N5 above `dc54b4d`. Fable did not write this code.

- **N1:** `EKS_CLUSTER_VPC_POOLS` covers managed and self-managed node groups. Hybrid nodes stay generic and exempt. New negative cases cover self-managed nodes in another VPC, in both VPCs and under an Auto Mode cluster, along with the managed variants this review listed as coverage gaps. The compatibility test now runs both pool types.
- **N5:** the test now asserts that the diagnostic names `app-a`.
- **Tests fail without the fixes:** against the source at `dc54b4d`, the three self-managed cases fail and nothing else does. Against the source at `5569459`, the N5 test fails as well.

The owner accepted this plan for the P3 findings:

- **N2, deferred:** Fargate profiles stay out of the rule because the AWS pages only imply the constraint. The rule's remedy and the core contract say so, and a test pins it. Revisit if AWS states it outright.
- **N3, deferred:** a single-network limit on EKS clusters needs a source first. It is one data field and a negative case for later catalog work.
- **N4, deferred:** the core contract now says NodePool edges are not reconciled with `node_ref`, so this is a recorded limit rather than an omission.

Not done: relation-only mismatch fixture cases for Azure, GCP and Huawei remain a coverage gap, though the code path is shared with the AWS case.

M2 stays open until N1 is fixed and rechecked, or the owner explicitly dispositions it. The asset-rights exit item is closed for the private personal release under D-019.
