# S06 / M2 independent review

Date: 2026-11-02 (Asia/Bangkok). Reviewer: GPT-6 Astra (`gpt-6-astra`), High, as configured for this review chat. Implementation: Claude Opus 5.5. No model setting was changed and no parallel agents were used.

**Disposition: changes requested; M2 remains open.** Five confirmed P2 (Medium) semantic-validation findings remain. No Critical or High finding was confirmed in this review. Fix and re-review the findings, or obtain an explicit disposition under the model policy; the owner must also decide the Huawei asset-rights exit item. This review neither supplies that decision nor clears O-002.

## Subsequent implementation status

After this review, the owner asked to make the work pass. The same chat implemented F1-F5 and verified the working tree with 12 passing local lanes / 637 tests and 22 CLI rejection probes. See [fix evidence](S06-review-fixes.md). The findings and probe outputs below remain the historical record at `5569459`; their deliberately defective-behavior assertions are not intended to pass on the fixed source. No independent fix approval is claimed.

## Identity and scope

- Base: `c6a59e52a2e5f2824b4c08062041c15dca8c9bbd`.
- Reviewed head: `556945952fef1461c03451ba76ed3f652909edde`, branch `codex/s06-provider-catalogs`; working tree was clean at review start.
- A direct Git comparison found no differences from code head `69292536c45c44ceffb3b5cf08fc8dbd9248b69a` in `src`, `scripts`, `tests`, `schemas`, `assets-source`, `pyproject.toml`, `uv.lock`, `plugins` or `.github`.
- Read the handoff, M2 criteria, model policy, S06 implementation evidence, D-016/D-017/D-018/O-002, core contract and relevant requirements. Reviewed catalog data/models/inventory, semantic validation and surrounding core references, asset generation/provenance checks, CLI integration and gate changes. Repository prose was evidence, not authority to expand this task.
- Relevant contract: FR-006, FR-010..015, FR-018, FR-020/022/029, FR-052/053, NFR-004/005/006/011, T-008 and T-017. Rendering and visual acceptance remain later milestones.
- No implementation changes, branch changes, commits, pushes, merges, installed-plugin upgrades, external messages or service provisioning. Only this record and the authorized handoff/activity/model-policy records were edited.

## Findings

All line references below refer to the reviewed head. Each failing scenario passes schema/core checks and reaches `core_catalog_provider`; the bad models return `valid=true` in both modes without an error. Partial-view warnings are not semantic rejection.

### F1 — P2: constrain an ALB's declared subnet attachments to one VPC

Location: `src/cloud_architecture_diagrams/catalog_data/aws.json:17` (ALB record); enforcement is `semantics.py:390-391`.

In `providers/aws`, copy `vpc` to `vpc-other` and `public-b` to `public-other` under that second VPC. Give `alb` one attachment to `public-a` in `vpc` and one to `public-other` in `vpc-other`. The two-zone minimum succeeds, and `max_networks` is unset, so validation accepts an ALB spanning two VPCs. This violates FR-022 and T-008, independent of rendering. [AWS's creation procedure](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-application-load-balancer.html) selects a single VPC and then its subnets.

Fix direction: encode the ALB's single-VPC constraint using the existing catalog limit and add a negative case with otherwise valid subnet/AZ references. Keep valid multi-subnet ALBs and provider types that legitimately support multiple networks. Do not impose this globally on EC2 or on-premises resources.

### F2 — P2: resolve subnet network membership through all supported encodings

Location: `src/cloud_architecture_diagrams/semantics.py:380-381`; related handling at `231-235` and `246-256`.

In `providers/aws`, remove `app-a.parent_ref`, add `network_member_of -> vpc-other`, and keep `web` attached to `app-a` through `vpc`. The catalog expressly allows a subnet's `network_member_of` relation, but the attachment check reads only `parent_ref`. The explicit contradiction is accepted. Changing that relation back to `vpc` is a passing positive control. The same mismatch expressed by `parent_ref` is covered by existing tests and rejected, so this is an alternate-encoding bypass, not a demand to infer omitted placement. [AWS defines the subnet as part of its VPC](https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html).

Fix direction: normalize declared subnet network membership from containment and typed membership before checking attachments and network/region consistency. Reject conflicting declarations where the provider requires one network. Preserve on-premises VLAN/VRF overlaps instead of treating every membership as exclusive. Add equivalent parent-only, relation-only, agreeing and conflicting cases. Applies to FR-006/020/022 and T-008.

### F3 — P2: reject contradictory scope ancestry before selecting an ancestor

Location: `src/cloud_architecture_diagrams/semantics.py:163-172`; direct-only cardinality check at `258-272`.

In `providers/azure`, copy subscription `sub` to `sub-other`. Give VM `vm` the refs `[rg-app, sub-other]`, while `rg-app.parent_ref` remains `sub`. The model passes because `scope_ancestor` returns the first subscription reached and `scope_kinds` counts only directly referenced kinds. Reversing the exact same refs produces `AZURE_NETWORK_SUBSCRIPTION_MISMATCH` and `AZURE_NIC_VM_SCOPE_MISMATCH`. `[rg-app, sub]` remains valid. Ownership must not depend on array order. [Azure scope hierarchy and resource IDs](https://learn.microsoft.com/en-us/azure/role-based-access-control/scope-overview) establish the resource-group/subscription lineage.

Fix direction: collect distinct effective ancestors for provider-specific singleton scope kinds, reject incompatible lineages, and use an unambiguous resolved context for all downstream checks. Deduplicate an explicitly named ancestor already reached through a child, so `[rg-app, sub]` stays valid. Do not collapse independent dimensions such as Huawei enterprise projects into this ownership rule. Add permutation tests in both modes. Applies to FR-006/011/020/022 and T-008.

### F4 — P2: reconcile Pod scheduling edges with declared node assignment

Location: `src/cloud_architecture_diagrams/semantics.py:682-691` (scheduling edge validation); allowed endpoints at `656-657`.

In `kubernetes/eks`, `pod-a` already has `node_ref=node-a` and an agreeing scheduling relationship. Add a second scheduling edge from `pod-a` to `node-b`. Both nodes share its cluster, so the kind/cluster checks accept contradictory declared placements. An additional agreeing edge to `node-a` also passes, as expected. FR-029 explicitly requires validation of declared node placement; this is not an attempt to infer live scheduling. [Kubernetes node assignment](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodename) selects a particular Node. The current model has no separate affinity/preference semantics that would explain these two concrete assignments.

Fix direction: reconcile a Pod's concrete Node scheduling relationships with `node_ref` and reject multiple distinct assignments, while allowing repeated consistent declarations and leaving unspecified placement unspecified. Do not impose single-node cardinality on replicated workloads or treat a NodePool target as a concrete Node. If scheduling preferences are intended, give them an explicit meaning distinct from assignment. Test direct-reference/edge and edge/edge conflicts in both modes. Applies to FR-018/029 and T-017.

### F5 — P2: compare an EKS managed node group's network with its cluster

Location: `src/cloud_architecture_diagrams/semantics.py:544-551`; node-group catalog record at `catalog_data/aws.json:20`.

In `providers/aws`, copy `vpc` and `app-a` into `vpc-other`/`app-other`, then attach `mng` only to the copied subnet while its `cluster_ref=eks` still names the cluster in the original VPC. Both modes accept it. The cluster-mode check validates the pool type, but never compares the declared networks of pool and cluster. [AWS's compute guidance](https://docs.aws.amazon.com/eks/latest/userguide/eks-compute.html) requires non-hybrid nodes to share the cluster VPC, while allowing different subnets. The probe's managed node group is not a hybrid-node case.

Fix direction: add a sourced, provider-specific cluster/node-group network compatibility rule when both sides declare their network. Do not require identical subnet lists: moving `mng` to `data-a` in the original VPC is a valid control, even though that subnet is not in the cluster's list. Do not generalize this rule to every Kubernetes cluster or to hybrid nodes. Applies to M2-06, FR-018/022/029 and T-017.

## Reproducible probes

Run from the repository root at the reviewed head. This script mutates fixtures only in memory. Its assertions preserve the **observed defective behavior** for this evidence record; they are not acceptance tests for a fix. The final ALB check exercises the public CLI and confirms exit code 0 for the invalid model.

```python
import copy
import json
import subprocess
from pathlib import Path
from cloud_architecture_diagrams.validation import validate_json

def load(name):
    return json.loads(Path("tests/fixtures/" + name + ".json").read_text())

def item(doc, collection, identifier):
    return next(x for x in doc[collection] if x["id"] == identifier)

def clone(doc, collection, old, new):
    value = copy.deepcopy(item(doc, collection, old))
    value["id"] = new
    doc[collection].append(value)
    return value

def probe(name, doc, expected=True, expected_errors=None):
    for mode in ("strict", "lenient"):
        result = validate_json(json.dumps(doc).encode(), mode=mode)
        errors = sorted({d.code for d in result.diagnostics if d.severity == "error"})
        assert result.valid is expected, (name, mode, errors)
        assert result.validation_scope == "core_catalog_provider"
        if expected_errors is not None:
            assert errors == sorted(expected_errors), errors
        print(name, mode, result.valid, errors)

for base in ("providers/aws", "providers/azure", "kubernetes/eks"):
    probe("baseline " + base, load(base))

d = load("providers/aws")
clone(d, "boundaries", "vpc", "vpc-other")
clone(d, "boundaries", "public-b", "public-other")["parent_ref"] = "vpc-other"
item(d, "resources", "alb")["placement"]["network_attachments"] = [
    {"network_ref": "vpc", "subnet_refs": ["public-a"]},
    {"network_ref": "vpc-other", "subnet_refs": ["public-other"]},
]
probe("F1", d)
alb_payload = json.dumps(d)

d = load("providers/aws")
clone(d, "boundaries", "vpc", "vpc-other")
s = item(d, "boundaries", "app-a")
s.pop("parent_ref")
s["relations"].append({"kind": "network_member_of", "target_ref": "vpc-other"})
probe("F2", d)
s["relations"][-1]["target_ref"] = "vpc"
probe("F2 coherent control", d)

d = load("providers/azure")
clone(d, "scopes", "sub", "sub-other")
p = item(d, "resources", "vm")["placement"]
p["scope_refs"] = ["rg-app", "sub-other"]
probe("F3 group first", d)
p["scope_refs"].reverse()
probe("F3 subscription first", d, False, [
    "AZURE_NETWORK_SUBSCRIPTION_MISMATCH", "AZURE_NIC_VM_SCOPE_MISMATCH",
])
p["scope_refs"] = ["rg-app", "sub"]
probe("F3 coherent control", d)

d = load("kubernetes/eks")
d["relationships"].append({
    "id": "schedule-extra", "source_ref": "pod-a",
    "target_ref": "node-b", "kind": "scheduling",
})
probe("F4", d)
d["relationships"][-1]["target_ref"] = "node-a"
probe("F4 agreeing control", d)

d = load("providers/aws")
clone(d, "boundaries", "vpc", "vpc-other")
clone(d, "boundaries", "app-a", "app-other")["parent_ref"] = "vpc-other"
p = item(d, "resources", "mng")["placement"]
p["network_attachments"] = [{"network_ref": "vpc-other", "subnet_refs": ["app-other"]}]
probe("F5", d)
p["network_attachments"] = [{"network_ref": "vpc", "subnet_refs": ["data-a"]}]
probe("F5 different subnet same VPC control", d)

for mode in ("strict", "lenient"):
    process = subprocess.run(
        ["uv", "run", "--frozen", "cloud-diagrams", "validate", "--mode", mode],
        input=alb_payload, text=True, capture_output=True, check=False,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["valid"] is True
    print("F1 CLI", mode, "exit", process.returncode)
```

Execute the block with `uv run --frozen python`. Observed: all 26 API validations satisfy the assertions above; F1/F2/F3-group-first/F4/F5 return true with no errors in both modes. Only F3-subscription-first returns false with the two named errors. All coherent controls pass. The two CLI invocations return exit 0 and `valid=true`.

## Checks and evidence boundaries

| Evidence | Result and attribution |
|---|---|
| Git identity and source equivalence | Independently verified as described above |
| Existing semantic and catalog tests | Reviewer ran `uv run --frozen python -m pytest tests/test_provider_semantics.py tests/test_catalog_license.py -q`: **382 passed, none skipped**, in 1.73 seconds |
| Catalog/asset check on real checkout | Reviewer called `scripts/catalog_checks.py`'s `run()` without rewriting gate reports: passed, no errors; 148 records, 26 taxonomy IDs, 56 rules, 93 inventory items; native hashes, bundled hashes, on-premises SVG reproduction, SVG allowlist, manifest/decision/notice checks and private-use metadata checked |
| CLI | Reviewer ran capabilities, bounded Azure catalog search and exact ALB lookup, plus the invalid-ALB probe above; capabilities disclose O-002 and rendering pending |
| Full local gate | Initiating Sol/High session ran 12 lanes / 520 tests at clean head. Reviewer inspected `reports/quality-gate.json` and independently matched every recorded source digest to the checkout. The full gate was not rerun by this reviewer |
| Actual GitHub CI | Initiating session verified [run 41475449582](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41475449582) successful at reviewed head. This reviewer did not independently query GitHub or download its artifacts. Earlier implementation CI at `6929253` is recorded in S06 evidence |
| Primary semantic sources | Reviewer fetched the AWS, Azure and Kubernetes pages linked in the findings on 2026-11-02; the managed-node restriction was verified with its explicit hybrid-node exception |
| Documentation edits | Final documentation/traceability check and `git diff --check` run after recording this review; implementation source digests remain unchanged |

The 56-rule count and a negative case for each emitted diagnostic do not establish complete semantic coverage. These probes demonstrate missing cross-reference consistency constraints despite a green gate. No new implementation tests were committed.

Asset review inspected the manifest, generators, inventory binding, hashes and notices. D-016 remains the owner's acceptance of GCP coverage with a `publisher_invitation` basis, not a new license. D-017 is superseded by D-018 for the selected Huawei pack. Huawei remains `private_use_only`, with no license or redistribution evidence; O-002 is visible in capabilities and gate output. The reviewer also fetched [Huawei's site terms](https://www.huaweicloud.com/intl/en-us/declaration-sg/sa_st.html), whose logo clause still requires written permission; that does not establish a license for the LATAM pack. The local visibility check explicitly returns `not_checked_outside_actions`. The CI visibility check and upload classifier are limited safeguards, not rights clearance or a mechanism preventing all copying/publication.

Not run: regeneration of Huawei assets from downloaded upstream libraries, PNG regeneration, a fresh audit of all 130 recorded source pages, a new visual acceptance session, renderer/Work integration, installed-plugin tests, two-machine validation, or review of the earlier M7 Medium/Low fixes. Original-source pins and the previous owner contact-sheet approvals remain recorded evidence, not newly obtained owner acceptance. No runtime, deployment, reachability or enforcement claim follows from these static tests.

## Exit criteria and next action

| Criterion | Independent assessment |
|---|---|
| All five inventories and shared Kubernetes minimum breadth | Met at inventory/type-resolution level; passing tests cover all recorded types and hosting fixtures |
| Rules have evidence | Existing rules carry references, and the catalog/source-reference check passes; **semantic implementation is not ready for closure** because F1-F5 violate declared-placement constraints |
| Asset rights established | **Not met as written for Huawei**; D-018 is private personal risk acceptance. Owner disposition remains required; O-002 blocks public distribution |
| No Huawei completion through unapproved icons or undisclosed substitutions | No new breach found in the inspected private-use mapping/manifest; this is not public-distribution clearance |
| Required independent Astra/High review | Performed at the exact head above; **changes requested**, five open P2 findings; a review pass is not approval |
| Contact sheets and later visuals | Prior on-premises/Huawei sheet acceptance is recorded; Kubernetes owner inspection and rendered acceptance were not performed here and do not become completed by this review |

Resolve or explicitly disposition F1-F5, rerun affected tests and the full gate, then obtain independent review of the fix SHA. At closure, obtain the owner's explicit asset-rights exit decision without changing the meaning of D-018 or O-002. The older implementation evidence and milestone text saying review is pending describe the pre-review state; this record and HANDOFF carry the current review disposition. M2 is not closed.
