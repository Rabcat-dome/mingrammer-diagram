# Cloud Architecture Diagram Plugin

Planning repository for a personal plugin built on `mingrammer/diagrams` and Graphviz. Target coverage: AWS, Azure, GCP, Huawei Cloud, and on-premises architecture.

The deliverable is an installable plugin usable across machines. Its bundled skill provides workflow instructions; it is one component inside the plugin. D-013 selects runtime installation on every machine using the plugin; the S04 candidate contains dependencies in a local Docker image.

**Status:** S01-S03 complete; S04 is in progress. D-013 selects an installable local plugin with runtime setup on each machine and supersedes the central server. Requirements are revision 0.7. Local container and installed-plugin SDK checks are recorded separately from pending actual Work verification. Product quality gates start in M1; Huawei packaging rights remain open.

## Read next

| Document | Purpose |
|---|---|
| [Requirements](doc/requirements/requirements.md) | Single product baseline, provider coverage, acceptance criteria |
| [Milestones](doc/project-management/milestones.md) | Tasks, dependencies, exit evidence, delivery order |
| [Session plan](doc/project-management/session-plan.md) | Ten work packages, collaboration points and copyable new-session/review prompts |
| [Model strategy](doc/project-management/model-strategy.md) | Development, code review, runtime model policy |
| [Quality gate](doc/project-management/quality-gate.md) | Proposed GitHub Actions pipeline and self-hosted runner constraints |
| [Decisions](doc/project-management/decisions.md) | Confirmed scope, recommendations, open questions, source reconciliation |
| [Handoff](doc/project-management/HANDOFF.md) | Small starting context for another machine or chat |
| [Activity log](doc/project-management/ACTIVITY-LOG.md) | Completed work and planned next activities |
| [S02 icon research](doc/project-management/evidence/S02-icon-sources-and-rights.md) | Candidate sources, Huawei rights gap, on-premises gaps and detailed Kubernetes asset readiness |
| [S03 runner preflight](doc/project-management/evidence/S03-repository-runner-preflight.md) | Installed runner, two successful GitHub jobs, tooling and current limitations |

[S04 evidence](doc/project-management/evidence/S04-runtime-and-hosting.md) and [local plugin setup](spikes/s04-local-plugin/README.md) distinguish installed SDK feasibility from actual Work behavior. The earlier [loopback HTTP experiment](spikes/s04-runtime/README.md) is historical research.

All project documentation is English. Start a new session with the handoff and current milestone; load other documents only when needed.
