# Cross-Machine Handoff

Updated: 2026-11-03 | S01-S05 complete. S06 / M2 is implemented and CI-tested on `codex/s06-provider-catalogs`; the fixes for the five P2 findings from Astra/High review at `5569459` are committed at `dc54b4d`, which passes CI with 12 lanes and 637 tests. Claude Fable 5.1 / High reviewed that commit under D-020 and requests one change (N1), so M2 is not closed. D-019 closes its asset-rights exit item for the private personal release. M7 Claude Code preparation started early under D-015.

## Goal and current source

Personal ChatGPT Work-first plugin on mingrammer/diagrams + Graphviz for AWS/Azure/GCP/Huawei/on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code acceptance is later; D-015 started its preparation early. Keep English docs and one [requirements baseline v0.12](../requirements/requirements.md).

Branch: `codex/s05-core-quality-gate`. M1 executable/workflow source reviewed and CI-tested at `785e1eecb646476691859f14dd4399ac564011ca`, milestone base `ff53a88944e981be2bbbab171e0ccf8cecdb4e41`. Later closure commits are docs/evidence only. Verify final HEAD/latest CI before resuming; main has not been merged. M7 preparation is on `codex/m7-claude-plugin`, stacked on the S05 head; its prefix keeps the existing workflow trigger. S06 branched from `c6a59e5` on `codex/m7-claude-plugin`, so it inherits the S05 core and the gate, which now has 12 lanes. The CI-tested S06 code head is `dc54b4d`, including the F1-F5 fixes and the owner's D-016 to D-020. Verify HEAD and the latest CI before resuming. Main has not been merged.

D-013/D-014 select per-machine native Python/Graphviz in the separate ChatGPT Work page. Docker, central hosting, public renderer and renderer/model API keys are unnecessary. S04's installed alpha.3 three-node plugin remains separate from M1 core package 0.2.0a1; this activity did not upgrade that plugin/runtime.

## Read order

1. This file, [milestones](milestones.md) and [S06 evidence](evidence/S06-provider-catalogs.md).
2. [Core contract/setup](../design/core-contract.md), relevant requirements and the S05 and S06 records.
3. Relevant decision, quality-gate and model-policy sections.

## Verified state

- M0/S01-S04 feasibility complete: [closeout](evidence/S04-closeout.md). Native alpha.3 local tests pass; owner reported actual separate Work alpha.3/Darwin, PNG and five files. This is not full product/two-machine acceptance.
- M1-01..04 complete: closed strict schema, CLI/discovery, bounded data parsing, IDs/refs/cycles, explicit views/exclusions and Kubernetes context. Results disclose core_only with pending catalog/provider/render layers; no product render command exists yet.
- Actual fix-head [CI run 41426653007](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41426653007) / job 125214762630 passed all eight lanes and 82 tests at 785e1ee, clean checkout/source/lock hashes verified. CI wheel bytes match local and pass clean install plus ownership rejection outside the checkout. [Proof](evidence/S05-validation-proof.json).
- Astra/High initially found two P2 issues: alternate ownership edges bypassed Kubernetes context rules; docs gate required historical output files outside the repo. Shared ownership validation and portable link policy fix them; re-review at 785e1ee confirms both with no additional actionable findings. Root separately verified fix-head CI. Actual implementation used inherited Sol/XHigh; no model setting changed.
- Gate: docs/traceability/proof hashes, narrow credential patterns, Ruff lint/format, strict mypy, actionlint, schema/core tests and core package build. Catalog/license/provider/render/visual/plugin lanes must be activated as components arrive. No mandatory paid model API call. Do not call deferred checks passed.
- Runner ID 2, macbook-pro-m2-max-mingrammer, label mingrammer-macos-arm64; native shell jobs. Existing seven registrations preserved. Current read-only API snapshot: owner is the only collaborator, private fork-PR workflows disabled, no fork write tokens/secrets. Actor checks supplement server-side access policy; keep external code off the personal host. Current private plan lacks required-check enforcement; manual review/merge remains necessary.
- [S06 / M2](evidence/S06-provider-catalogs.md): catalog `2026.11.0` has 26 taxonomy IDs, 148 records and 56 sourced rules (59 after the review fixes), and the eight on-premises assets are bundled with attribution and hashes. Actual CI [run 41473877379](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41473877379) at `6929253` passes 12 lanes with 520 tests and none skipped, and sabotage checks confirm the new lanes fail when they should. The owner accepted the eight on-premises symbols and the 15 Huawei icons on their sheets, the latter at SHA-256 `959b8b22f6ff93e328a4dacc9d4f27971a55a431360ee25d7252224cc8f1d35e`. That covers the sheets only, so rendered visual acceptance stays with M4 and M6, and rights status under D-018 and O-002 does not change. **Independent Astra/High review now covers `c6a59e5..5569459` and requests changes for five P2 findings**: ALB multi-VPC attachment, subnet membership encoding bypass, order-dependent scope ancestry, contradictory Pod scheduling, and EKS managed-node-group/cluster VPC mismatch. See the [review and reproducible probes](evidence/S06-astra-review.md). **Follow-up:** the fixes are committed at `dc54b4d` and pass actual CI [run 41488737943](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41488737943) with 637 tests; see [fix evidence](evidence/S06-review-fixes.md). Under D-020, [Claude Fable 5.1 / High reviewed them](evidence/S06-fable-review.md): F1-F4 are fixed, F5 is partly fixed, and N1 is a new P2 with four new P3 findings. The owner's installed plugin does not have this work yet. The original implementation used Claude Opus 5.5 and the fixes used GPT-6 Astra, not Sol.
- Huawei: source availability is not redistribution/output permission. [D-018](decisions.md#confirmed-user-direction) accepts the LATAM color library for the owner's private personal use only, which is risk acceptance, not clearance. D-019 closes M2's asset-rights exit item on that basis, because the owner will not distribute publicly. It replaced the JuanDiaz00 line-art pack that D-017 first chose. All 15 required items that need an icon have one, pinned at commit `52c33aa`, and Subnet and Security Group stay labeled boundaries. O-002 blocks public distribution, and the `catalog-license` lane fails on a public repository or a missing upload block. Keep this repository private; once committed, these files stay in its history. D-016 accepts the GCP icons.
- Existing S04 source/fonts/proofs remain available; no runtime cache, Docker resource, cloud service, account plugin, merge or release was changed by S05. Historical host paths are provenance text; reproducible doc links stay inside the repository.
- [M7 Claude Code preparation](evidence/M7-claude-plugin.md): `plugins/cloud-architecture-diagrams` validates models through the core and cannot render. Packaging at `22fc85e` left the wheel byte-identical to the S05 CI wheel; core `0.2.0a2` then added a usage exit code. GitHub and real-config installs, live English/Thai/edit invocations and a Code tab runtime check pass on one Mac. The owner's install is pinned to the branch, so re-add the marketplace after a merge. A same-session review found 10 issues, all fixed at `0220e94`, which passed actual CI run 41443551856. A separate Claude session then reviewed `c5f74b4..a94b47a` as a substitute, not Astra: no Critical or High issues, with all three Medium and six Low findings fixed by core `0.2.0a4`. Those fixes passed actual CI run 41453874994 at `917f46f`, and the owner's install holds that commit; no review pass has covered them. A second machine, interactive permission prompts and the Astra/High review remain open. Run 41441398887 at `359f1ea` confirms the move of `actions/upload-artifact` to Node 24, with no job annotations.

## Keeping the Claude plugin in step

Core changes reach the plugin through symlinks, so no copy step exists, and Claude Code versions the plugin by commit, so no version bump is needed. Checks in the `claude-plugin` lane fail on purpose when the core moves: add new enumerated kinds and cluster modes to the skill's model guide, and rewrite the skill's stated capabilities when rendering arrives. Any new file or symlink in the plugin needs an allowlist update. Anything under `src` ships in the plugin, so the `catalog-license` lane fails on any visual asset there that the rights manifest does not list. When M3 moves `diagrams` to runtime, the plugin's locked environment changes with it.

## Next steps

1. Settle N1 from the [Fable review](evidence/S06-fable-review.md) of `dc54b4d`: self-managed EKS nodes in another VPC still pass. Fix and recheck it with CI at the fix commit, or record the owner's explicit disposition. N2-N5 are P3. Review of the earlier M7 Medium/Low fixes remains outstanding.
2. Close M2 once N1 is settled; the owner settled the asset-rights exit item under D-019 on 2026-11-03. Kubernetes representations have not been shown to the owner; the session plan lists that inspection, but it is not an exit item.
3. Update the owner's installed plugin only if asked. It remains on `917f46f`, so it has none of the S06 work.
4. S07 / M3 renderer: honor each record's `representation`, draw Azure icons unmodified, keep `required_label` on assets, never substitute for `blocked`, and carry the private-use limit into any bundle that uses Huawei icons. Later M4 references/visuals, M5 full Work plugin and M6 two-machine release acceptance remain open.

## Resume prompt

```text
Continue from doc/project-management/HANDOFF.md and the S06 evidence. Verify git
status and the latest successful GitHub quality-gate SHA first. M2 still needs
N1 from evidence/S06-fable-review.md settled, with CI at any later fix commit.
D-019 closes its asset-rights exit item for the
private personal release. D-018 allows Huawei icons for private personal use only;
it does not clear their rights.

For S07 / M3, read M3 in milestones.md, FR-040..048 and the core contract's
catalog section. Keep the same checkout and a codex/ branch; keep docs English.
Render only through each catalog record's representation. Huawei source
availability is not redistribution permission: keep public distribution blocked
under O-002, and draw no silent generic substitute for a type without an icon. Keep S04 alpha.3 and existing runner registrations unchanged. Record
the model actually used. No Docker cleanup, cloud host, public release or
automatic merge is part of this activity.
```
