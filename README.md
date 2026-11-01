# Cloud Architecture Diagram Plugin

Planning repository for a personal plugin built on `mingrammer/diagrams` and Graphviz. Target coverage: AWS, Azure, GCP, Huawei Cloud, and on-premises architecture.

The deliverable is an installable plugin usable across machines. Its bundled skill provides workflow instructions; it is one component inside the plugin. Renderer hosting and dependencies are a separate implementation decision.

**Status:** S01/S02 planning and research are complete. S03 investigation on 2026-11-01 confirmed private repository access. The owner authorized runner setup/publication/testing (D-011); the separate Mac ARM64 runner is now online. Workflow publication and its real job are in progress. Requirements remain revision 0.5; S04 runtime proof is next. No renderer, plugin or product quality gate is implemented. ChatGPT Work is first; Claude Code is later.

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
| [S03 runner preflight](doc/project-management/evidence/S03-repository-runner-preflight.md) | Verified access, runner scope, tooling, GitHub plan limitation and concrete setup recommendation |

All project documentation is English. Start a new session with the handoff and current milestone; load other documents only when needed.
