# Cross-Machine Handoff

Updated: 2026-11-01 | Current stage: M0 / S01/S02 complete; S03 runner installed/online, publication/job in progress; S04 not started.

## Goal

Build a personal ChatGPT Work plugin using `mingrammer/diagrams` + Graphviz for AWS, Azure, GCP, Huawei Cloud and on-premises architecture. Add Huawei icons with verified rights. Keep the core reusable for a future Claude Code adapter. All documentation is English.

The user confirmed cross-machine use as the reason for choosing a plugin. The skill is bundled inside the installable plugin; it does not replace that deliverable. Hosting remains undecided.

## Read order

1. This file, then the active milestone in [milestones](milestones.md).
2. Relevant IDs from the single [requirements baseline](../requirements/requirements.md).
3. [Decisions](decisions.md), [model strategy](model-strategy.md), or [quality gate](quality-gate.md) only as needed.

To split work into new chats, use the [session plan](session-plan.md). S03 has recorded findings and installed a separate runner under D-011; initial publication and a real job are in progress. S04 proves the runtime before M1 implementation and can proceed independently. No new chats have been created or dispatched.

## Current state

- Documentation draft prepared; owner refinement/acceptance remains pending.
- S01 scope planning is complete. [Six working scenario families](evidence/S01-release-scope.md) include detailed Kubernetes subviews after the owner's correction (D-009). Overall solution-architecture depth and white/provider-specific visuals remain (D-007/D-008).
- Requirements revision 0.5 retains detailed Kubernetes (FR-018/FR-029/T-017) and provider fidelity (FR-048/T-016), and adds the D-010/FR-014 draw.io-type on-premises preference. No rendered baseline is accepted yet.
- [S02 research](evidence/S02-icon-sources-and-rights.md) found 17/17 Huawei minimum mapping candidates in LATAM color libraries at v3.2 / commit 52c33aa12fb816a5de403da85067e1c0f039b5be. Plugin redistribution evidence is still missing. The inventory contains metadata only; no icon package is cleared or bundled.
- [S02 follow-up](evidence/S02-additional-icon-sources.md) maps the eight on-premises concepts to draw.io generic symbols/compositions (D-010). M2-04 handles selected-source terms/attribution, export and visual checks; the renderer remains diagrams/Graphviz.
- The user-supplied JuanDiaz00 Huawei alternative contains 155 PNG entries and cites VeryIcon. A free-personal/commercial-use claim was found there, but full minimum mapping/source-asset redistribution evidence remains unresolved. Keep it as an alternative; no Huawei asset source is adopted or cleared. S02 also records 18 Kubernetes asset candidates.
- [S03 findings](evidence/S03-repository-runner-preflight.md): CLI identity `Rabcat-dome` has admin access to the private repository; Actions is enabled. The GitHub connector still returns 404. Initial inspection found zero eligible runners and no remote branches/workflows. D-011 subsequently authorized setup/publication/testing; the new runner is online.
- Seven existing local runner services belong to other repositories. The separate `macbook-pro-m2-max-mingrammer` runner (ID 2, version 2.338.2) is online with custom label `mingrammer-macos-arm64`; all eight services are loaded. The prepared [manual preflight](../../.github/workflows/runner-preflight.yml) passes actionlint and its embedded probe runs locally; no GitHub job has run.
- macOS ARM64; Python 3.13.7, uv 0.13.0, actionlint 1.7.12. `dot` is absent from the shell and seven cached runner PATH lookups. The actual new service environment, Graphviz/fonts and render isolation remain unproved.
- Rulesets and branch-protection APIs return 403 requiring a plan change for this private repository. CI can report results, but server-enforced required checks are unavailable at this snapshot. Keep a manual review/merge policy unless capability changes; no plan/visibility setting was changed.
- No Python core, schema, catalogs, assets, renderer, plugin, deployment or product quality gate is implemented. No separate model review, render/Work test or real runner job was performed. The local repository still has no commits; no commit/push was performed.

## Proposed approach

Canonical JSON -> schema/semantic checks -> provider catalog/view mapper -> controlled diagrams/Graphviz -> SVG/PNG + model/view/diagnostics/version manifest. Never execute model-authored Python. Separate administrative, geographic, network, security, deployment and physical dimensions.

Recommend an installable plugin containing a workflow skill and authenticated remote MCP tools for Work Cloud/Web portability; keep local CLI in the core. Remote execution can reduce per-machine runtime setup, but runtime selection is still open. Do not infer laptop execution or automatic installation/credential sync from plugin installation. Use Sol for implementation and a separate Astra code review pass; see the model strategy for exact IDs/effort and substitution rules.

## Next activities

1. Carry forward D-006/FR-066: deliver a versioned plugin usable across machines, with its skill bundled inside.
2. Carry forward S01 decisions D-007/D-008/D-009: solution architecture overall, detailed Kubernetes, provider-reference visuals. Include M2-06/M4-05 and T-017; O-008 is resolved and O-004's sample acceptance remains M4/M6.
3. Carry forward D-010: use the eight draw.io-type generic mappings and source-version/conditions evidence from the S02 follow-up. Mapped concepts are not yet exported/approved asset files.
4. S03/M0-04/O-005: D-011 authorizes setup and publication; registration/labels are verified. Publish the initial tree/workflow and run the harmless manual job. The exact sequence is in the S03 record. M0-04 is incomplete until actual job evidence exists. Do not copy another project's runner labels.
5. S04/M0-02/O-001: compare runtime routes and prove actual Work tool invocation/artifact download; document modes/setup and select pinned runtime/fonts/limits (M0-05). Do not treat portability as approval of remote hosting.
6. Carry S02/O-002 into M2-03: obtain Huawei extraction/conversion/bundling/output-use permission evidence before packaging. A prepared request exists in the research record, but no message was sent. Proceed with independent runner/runtime work while this is unresolved.
7. Start M1 schema/package and first real quality gate checks after applicable M0 exit evidence exists. Use approved fixture assets for runtime proof; S02 research metadata is not an asset allowlist.

## Resume prompt

```text
Continue this Cloud Architecture Diagram Plugin project from doc/project-management/HANDOFF.md.
Read the active milestone and relevant requirements, verify current Git state,
and check whether open decisions have new answers before implementation.
Target ChatGPT Work first; Claude Code is later. Keep documentation English.
Distinguish planning, local checks, runner checks, installed Work behavior and
owner acceptance. Update HANDOFF.md and ACTIVITY-LOG.md with verified outcomes.
```

## Update discipline

After meaningful work, record completed task IDs, changed files, actual checks/results, commit SHA if any, unresolved decisions and next steps. Recheck dynamic facts such as models, dependencies, icons and runner registration. Keep this file short; place detailed evidence next to the relevant milestone/change.
