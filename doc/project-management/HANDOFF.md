# Cross-Machine Handoff

Updated: 2026-11-02 | S01-S05 complete. S06 / M2 catalogs and approved assets are next. M7 Claude Code preparation started early under D-015.

## Goal and current source

Personal ChatGPT Work-first plugin on mingrammer/diagrams + Graphviz for AWS/Azure/GCP/Huawei/on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code acceptance is later; D-015 started its preparation early. Keep English docs and one [requirements baseline v0.9](../requirements/requirements.md).

Branch: `codex/s05-core-quality-gate`. M1 executable/workflow source reviewed and CI-tested at `785e1eecb646476691859f14dd4399ac564011ca`, milestone base `ff53a88944e981be2bbbab171e0ccf8cecdb4e41`. Later closure commits are docs/evidence only. Verify final HEAD/latest CI before resuming; main has not been merged. M7 preparation is on `codex/m7-claude-plugin`, stacked on the S05 head; its prefix keeps the existing workflow trigger.

D-013/D-014 select per-machine native Python/Graphviz in the separate ChatGPT Work page. Docker, central hosting, public renderer and renderer/model API keys are unnecessary. S04's installed alpha.3 three-node plugin remains separate from M1 core package 0.2.0a1; this activity did not upgrade that plugin/runtime.

## Read order

1. This file, [milestones](milestones.md) and [S05 evidence](evidence/S05-core-and-ci.md).
2. [Core contract/setup](../design/core-contract.md), relevant requirements and [S05 final review](evidence/S05-astra-review.md).
3. S02 icon/rights records and relevant decision/quality-gate/model-policy sections for S06.

## Verified state

- M0/S01-S04 feasibility complete: [closeout](evidence/S04-closeout.md). Native alpha.3 local tests pass; owner reported actual separate Work alpha.3/Darwin, PNG and five files. This is not full product/two-machine acceptance.
- M1-01..04 complete: closed strict schema, CLI/discovery, bounded data parsing, IDs/refs/cycles, explicit views/exclusions and Kubernetes context. Results disclose core_only with pending catalog/provider/render layers; no product render command exists yet.
- Actual fix-head [CI run 41426653007](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41426653007) / job 125214762630 passed all eight lanes and 82 tests at 785e1ee, clean checkout/source/lock hashes verified. CI wheel bytes match local and pass clean install plus ownership rejection outside the checkout. [Proof](evidence/S05-validation-proof.json).
- Astra/High initially found two P2 issues: alternate ownership edges bypassed Kubernetes context rules; docs gate required historical output files outside the repo. Shared ownership validation and portable link policy fix them; re-review at 785e1ee confirms both with no additional actionable findings. Root separately verified fix-head CI. Actual implementation used inherited Sol/XHigh; no model setting changed.
- Gate: docs/traceability/proof hashes, narrow credential patterns, Ruff lint/format, strict mypy, actionlint, schema/core tests and core package build. Catalog/license/provider/render/visual/plugin lanes must be activated as components arrive. No mandatory paid model API call. Do not call deferred checks passed.
- Runner ID 2, macbook-pro-m2-max-mingrammer, label mingrammer-macos-arm64; native shell jobs. Existing seven registrations preserved. Current read-only API snapshot: owner is the only collaborator, private fork-PR workflows disabled, no fork write tokens/secrets. Actor checks supplement server-side access policy; keep external code off the personal host. Current private plan lacks required-check enforcement; manual review/merge remains necessary.
- Huawei source availability is not redistribution/output permission. O-002 remains a packaging/release blocker; no Huawei pack is bundled. Eight draw.io-type generic on-premises concepts are selected; exact assets/conditions/hashes remain M2. Full provider/Kubernetes kind/API/rule inventory and assets are S06 work.
- Existing S04 source/fonts/proofs remain available; no runtime cache, Docker resource, cloud service, account plugin, merge or release was changed by S05. Historical host paths are provenance text; reproducible doc links stay inside the repository.
- [M7 Claude Code preparation](evidence/M7-claude-plugin.md): `plugins/cloud-architecture-diagrams` validates models through the core and cannot render. Actual CI run 41440133540 passed 10 lanes at `22fc85e`; the wheel is byte-identical to the S05 CI wheel. GitHub and real-config installs, live English/Thai/edit invocations and a Code tab runtime check pass on one Mac. The owner's install is pinned to the branch, so re-add the marketplace after a merge. A second machine, interactive permission prompts and independent review remain open. The later move of `actions/upload-artifact` to Node 24 still needs an actual CI run.

## Keeping the Claude plugin in step

Core changes reach the plugin through symlinks, so no copy step exists. Three checks in the `claude-plugin` lane fail on purpose when the core moves: bump `plugin.json` with `__version__` (an installed plugin keeps its cache until the version changes), add new enumerated kinds to the skill's model guide, and rewrite the skill's stated capabilities when rendering arrives. New top-level runtime folders need a new symlink and an allowlist update.

## Next steps

1. Start S06 / M2-01..06: taxonomy, all five provider catalogs, detailed Kubernetes catalog/provider mappings, exact approved icons/terms/hashes and meaningful provider/asset rule checks in the existing gate.
2. Preserve ownership/location/network/security/deployment as separate dimensions. Treat Secret resources as references, never payloads. Use current primary sources and retain provider-native identity; do not infer reachability/controller availability.
3. Resolve Huawei rights with evidence or retain an explicit packaging/release blocker; no silent generic substitution. Later M3 renderer, M4 references/visuals, M5 full Work plugin and M6 two-machine release acceptance remain open.

## Resume prompt

```text
Start S06 / M2 from doc/project-management/HANDOFF.md and milestones.md.
Verify M1 final reviewed code and successful GitHub quality-gate SHA first.
Use the same checkout and a codex/s06-provider-catalogs branch; keep docs English.
Read requirements sections 6/6.1, M2-01..06 and the core contract guide. Freeze
exact catalog/type IDs, provider/native identity, taxonomy, placement semantics,
Kubernetes API/provider mappings and approved renderer/icon provenance. Use
current primary sources. Preserve ownership/location/network/security/deployment
as independent dimensions and keep Kubernetes as a platform, not a provider.
Implement catalog/schema/license/rule checks with meaningful positive/negative
fixtures and integrate mandatory lanes into the existing native quality gate.
Huawei source availability is not redistribution permission: resolve O-002 with
actual terms/evidence or retain an explicit packaging/release blocker. Do not
bundle uncleared assets or silently substitute generic Huawei icons. Implement
the eight approved draw.io-type on-premises mappings with exact rights/hashes.
Use Sol for implementation and an independently authorized Astra/High review.
Keep S04 native plugin alpha.3 and existing runner registrations unchanged unless
a concrete M2 requirement requires a documented versioned change. No Docker
cleanup, cloud host, public release or automatic merge is part of this activity.
```
