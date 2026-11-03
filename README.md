# Cloud Architecture Diagram Plugin

Planning repository for a personal plugin built on `mingrammer/diagrams` and Graphviz. Target coverage: AWS, Azure, GCP, Huawei Cloud, and on-premises architecture.

The deliverable is an installable plugin usable across machines. Its bundled skill provides workflow instructions; it is one component inside the plugin. D-013 selects runtime installation on every machine using the plugin; the S04 native default uses a private Python environment and system Graphviz, without requiring Docker.

**Status:** S01-S08 complete, and M2, M3 and M4 closed on 2026-11-03 for the private personal release. Huawei icons are accepted for private personal use only, with rights not cleared, so **keep this repository private**. [S07 / M3 controlled rendering](doc/project-management/evidence/S07-controlled-rendering.md) passes actual CI and its Fable/High review, and the owner passed three samples of its output. [S08 / M4 reference diagrams](doc/project-management/evidence/S08-reference-diagrams.md) pass actual CI and their Fable/High review, and the owner passed the images. The M5 Work plugin and M6 two-machine acceptance remain open. See the [M1 core and Quality Gate](doc/project-management/evidence/S05-core-and-ci.md) and [M2 catalogs](doc/project-management/evidence/S06-provider-catalogs.md) evidence.

A preparation build of the [Claude Code plugin](plugins/cloud-architecture-diagrams/README.md) authors, validates and renders models through the same core; see the [M7 evidence](doc/project-management/evidence/M7-claude-plugin.md). ChatGPT Work remains the first-release target.

## Read next

| Document | Purpose |
|---|---|
| [Core contract/setup](doc/design/core-contract.md) | Implemented M1 schema, CLI, validation layers, bounds and local quality-gate commands |
| [Requirements](doc/requirements/requirements.md) | Single product baseline, provider coverage, acceptance criteria |
| [Milestones](doc/project-management/milestones.md) | Tasks, dependencies, exit evidence, delivery order |
| [Session plan](doc/project-management/session-plan.md) | Ten work packages, collaboration points and copyable new-session/review prompts |
| [Model strategy](doc/project-management/model-strategy.md) | Development, code review, runtime model policy |
| [Quality gate](doc/project-management/quality-gate.md) | Proposed GitHub Actions pipeline and self-hosted runner constraints |
| [Decisions](doc/project-management/decisions.md) | Confirmed scope, recommendations, open questions, source reconciliation |
| [Handoff](doc/project-management/HANDOFF.md) | Small starting context for another machine or chat |
| [Activity log](doc/project-management/ACTIVITY-LOG.md) | Completed work and planned next activities |
| [S02 icon research](doc/project-management/evidence/S02-icon-sources-and-rights.md) | Candidate sources, Huawei rights gap, on-premises gaps and detailed Kubernetes asset readiness |
| [S06 catalogs and rights](doc/project-management/evidence/S06-provider-catalogs.md) | Provider and Kubernetes catalogs, semantic rules, on-premises assets, Huawei blocker and validation results |
| [S03 runner preflight](doc/project-management/evidence/S03-repository-runner-preflight.md) | Installed runner, two successful GitHub jobs, tooling and current limitations |

[Current S04 native evidence](doc/project-management/evidence/S04-native-runtime.md) and [local plugin setup](spikes/s04-local-plugin/README.md) distinguish installed SDK feasibility from actual Work behavior. The earlier [loopback HTTP experiment](spikes/s04-runtime/README.md) is historical research.

All project documentation is English. Start a new session with the handoff and current milestone; load other documents only when needed.
