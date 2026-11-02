# S06 review fixes and local verification

Date: 2026-11-02 (Asia/Bangkok). Implementation and verification: GPT-6 Astra (`gpt-6-astra`) / High in the same chat that produced the [original review](S06-astra-review.md), following the owner's request to make the work pass. No parallel agents or model-setting changes.

**All five reported failures are fixed and the local gate passes.** This is not an independent review of the fixes or M2 closure.

## Tested source

Branch: `codex/s06-provider-catalogs`; HEAD remains `556945952fef1461c03451ba76ed3f652909edde`. Changes are uncommitted. The [machine-readable proof](S06-review-fixes-proof.json) includes the full gate result, per-file source SHA-256 digests, lock digest and 22 CLI outcomes. Its `working_tree_dirty=true` and `source_ref=null` correctly distinguish these files from committed HEAD. No installed plugin, commit, push, merge or external service was changed.

## Finding disposition

| Finding | Fix | Regression coverage |
|---|---|---|
| F1: multi-VPC ALB | ALB catalog sets `max_networks=1` | Invalid two-VPC ALB rejected in both modes; existing valid ALB and multi-VPC EC2 remain valid |
| F2: subnet relation bypass | Resolve network IDs from parent and typed membership; compare attachments and subnet/network regions; cloud subnet records limit membership to one network | Relation-only and agreeing encodings pass for AWS/Azure/GCP/Huawei; conflicts and relation-only region mismatch fail; on-premises overlaps remain valid |
| F3: scope reference order | Collect effective ancestors, collapse compatible same-lineage ancestors and reject multiple incompatible singleton scopes; ambiguous ancestors cannot win by array order | Azure resource and boundary tests cover both orders and coherent/conflicting lineages; Huawei IAM ancestors and enterprise-project refs stay independent |
| F4: contradictory Pod scheduling | Collect concrete Node assignments across `node_ref` and scheduling edges before validating cardinality | Reference/edge and edge/edge conflicts fail across all five hosts; matching assignments, unspecified placement, replicated workload and NodePool targets pass |
| F5: EKS node-group VPC mismatch | Compare declared VPC sets for EKS managed node groups and their EKS/Auto Mode clusters | Wrong VPC rejected; a different subnet in the same VPC and either side's unspecified network remain valid; generic/hybrid nodes are not included in this rule |

Added diagnostics: `BOUNDARY_NETWORK_COUNT_INVALID`, `K8S_NODE_ASSIGNMENT_CONFLICT`, and `AWS_EKS_NODE_GROUP_NETWORK_MISMATCH`. The catalog now has 59 rules. Existing codes for scope cardinality, subnet mismatch and network count are reused with clearer remedies. No schema shape, inventory breadth, icon mapping or rights status changed.

The two new external rule references were fetched over HTTPS and their claims matched in `S06-source-checks.json`: [AWS EKS compute](https://docs.aws.amazon.com/eks/latest/userguide/eks-compute.html) explicitly distinguishes same-VPC placement from same-subnet placement and exempts hybrid nodes; [Kubernetes assignment](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/) documents concrete Node assignment. The other rules retain their previously recorded provider references. Python's local certificate lookup failed on the initial source-fetch attempt; normal TLS-verified `curl` succeeded, without disabling verification.

## Validation

- `uv run --frozen python scripts/quality_gate.py`: **12 lanes passed; 637 tests executed; none skipped** (91 schema/core, 72 catalog/license, 427 provider semantics, 47 Claude-plugin contract tests). This includes lint, formatting, strict typing, workflow checks, package build and package-content checks. The 117 additional collected tests exercise the fixes and compatible controls.
- Targeted catalog/semantic run before the final six compatibility controls: 493 passed. The complete gate includes those additional six controls; no failed test was waived.
- Real `cloud-diagrams validate` CLI: **22 negative invocations** cover all new `review-f*` fixture cases, expanded across hosts, in both modes. Each returns `valid=false`, its expected error and exit **2**. The first probe harness incorrectly expected exit 1; after checking the existing CLI contract, only that harness assertion was corrected. Application behavior was not changed to accommodate it.
- Final documentation/traceability, secret-pattern and whitespace checks are run after these records are written. The proof's source hashes must still match the current checkout.

Reproduce the regression suite with `uv run --frozen python -m pytest tests/test_provider_semantics.py tests/test_catalog_license.py -q`. The new negative fixture IDs begin with `review-f`; `test_negative_case_fails_with_its_code` checks every case in strict and lenient modes. The compatibility tests follow `test_kubernetes_catalog_covers_every_kind_with_its_namespace_scope`. The proof records actual CLI outputs independently of the test helper's assertions.

## Remaining exit conditions

The original five findings are locally addressed, awaiting independent fix review. This chat's follow-up inspection and tests are same-session verification because the original reviewer also wrote the fixes. Actual CI run 41475449582 still identifies the old HEAD, not these uncommitted changes; CI must run against any later authorized fix commit. Earlier M7 Medium/Low fixes, rendered visuals, Work integration and two-machine acceptance are not newly reviewed here.

Huawei rights remain uncleared. D-018 accepts private personal risk only, and O-002 still blocks public distribution. A passing local gate did not make the decision on the M2 asset-rights exit item; the owner made it later under D-019. M2 remains open.

## Follow-up

These changes were committed at `dc54b4d`, and actual CI [run 41488737943](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41488737943) passes there. The statement above that all five failures are fixed held for the reported cases. A later [independent review](S06-fable-review.md) under D-020 confirms F1-F4 and finds F5 only partly fixed, because self-managed EKS nodes in another VPC still pass.
