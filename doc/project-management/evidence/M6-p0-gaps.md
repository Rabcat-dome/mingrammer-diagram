# M6 — P0 Records Left Partly Met

Date: 2026-11-05 (Asia/Bangkok) | Decision: D-030 | Branch: `codex/m6-p0-gaps`

**Result: on the owner's word, 13 records left partly met are settled, and the [P0 report](S10-p0-traceability.md) now has 32 met, 37 met with the owner's acceptance and 2 partly met.** T-015 and T-016 stay partly met until M6-03, M6-04 and the owner's inspection. M6 stays open.

## What the owner decided

| IDs | Gap | Decision |
|---|---|---|
| FR-018 | Declared properties and typed references did not reach the drawing | [Draw them](#fr-018) |
| FR-010 to FR-014 | Negative fixtures exist per rule, and section 6 asked for them per item | Accept per rule, and reword section 6. FR-014's source conditions gain a test |
| FR-022 | A subnet with no path to any network accepts any `network_ref` | Accept, as an unspecified fact that contradicts nothing declared |
| FR-029 | `management` edges have no endpoint rule | Accept, because real models use them across kinds. An Ingress configuring a load balancer is one |
| FR-050 | A model cannot state a version | Reword to the one bundled catalog. The refusal of another `diagrams` version gains tests in the renderer and the lane |
| FR-065 | Test reuse has no check of its own | Accept, because both adapters live in one repository |
| NFR-009 | The numbers were frozen in M3 and M4, not M0 and M1, and no test pinned them | Reword to freezing by M4, and a test pins them. Memory and temporary limits stay sampled |
| T-012 | The P1 clause is deferred | Accept, which M4's exit allows |
| FR-004 | ID stability rests on the host | Closed by the edit check on both Macs, under D-027 and D-029 |

## FR-018

Section 6.1 asks for replica counts and labels where supplied, for a Service's declared type, ports and targets, and says the detail view must retain supplied security, configuration and storage relationships. The renderer read none of the properties, and typed references drew only if a relationship repeated them.

`namespace` and `node` grouping are the Kubernetes detail views. A resource's node there now also lists:

- `replicas`, `type`, `ports` in the form `80:8080/TCP`, and `labels` sorted by key. Zero replicas still show.
- Each typed reference that no selected relationship draws, by the entity's name: `service`, `target`, `claim`, `volume`, `storage class`, `config`, `secret`, `service account` and `owner`.

Other groupings leave these out, so an overview stays compact, as section 6.1 allows. A Secret's reference shows only its name, and the model format has no field for a value.

The references now declare a Service type and ports. Exactly the 11 Kubernetes detail views changed, and the baselines moved through `scripts/update_visual_baselines.py`:

- `aws-three-tier`: `eks-namespaces`, `eks-nodes`
- `azure-hub-spoke`: `aks-namespaces`, `aks-nodes`
- `gcp-shared-vpc`: `gke-namespaces`, `gke-nodes`
- `huawei-web`: `cce-namespaces`, `cce-nodes`
- `hybrid-five`: `k8s-detail`
- `onprem-physical-logical`: `k8s-namespaces`, `k8s-nodes`

The other 15 views are unchanged. An edge can still start across a node's lower label lines, as it did before, and more lines make that a little more visible. The owner reviews these images under T-016, and D-023's acceptance does not cover them.

## Effect on the Work checks

This changes `src` and the skill's guide, so the plugin's version is now `0.1.0-alpha.1+88ce2c0cd0dc`, and [M5's](S09-Work-validation.md) and [M6-01's](M6-second-machine.md) results describe the version before it. M6-01 asks for the same version on two machines, so the five prompts run again on both before release.
