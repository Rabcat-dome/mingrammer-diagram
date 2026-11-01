# Cross-Machine Handoff

Updated: 2026-11-01 | Stage: M0. S01-S03 complete; S04 local plugin/runtime SDK proof passed; actual Work proof and independent review pending.

## Goal and current direction

Build a personal ChatGPT Work plugin using mingrammer/diagrams + Graphviz for AWS, Azure, GCP, Huawei and on-premises, with detailed Kubernetes and provider-reference visuals. Claude Code is later. Documentation is English and the single normative baseline is [requirements revision 0.7](../requirements/requirements.md).

**D-013 supersedes D-012:** install the renderer/runtime on each machine using the plugin. The product remains an installable plugin with a bundled skill and local tools. Work Desktop/local execution is the first host to verify. No central server, hosting project/region/budget answer, public renderer or mandatory model API key is needed. Do not reopen the cloud-hosting question or assume cloud-only/mobile support.

## Read order

1. This file and the active [milestone](milestones.md).
2. Relevant IDs in the [requirements](../requirements/requirements.md).
3. [S04 evidence](evidence/S04-runtime-and-hosting.md), [local plugin instructions](../../spikes/s04-local-plugin/README.md), [decisions](decisions.md), [model policy](model-strategy.md) or [quality gate](quality-gate.md) as needed.

Use the [session plan](session-plan.md) to split work. No new chats were created/dispatched. Do not start S05 as though M0 were closed.

Working branch: `codex/s04-runtime-proof`; base: `afbaccad87019d35bff12d335ec534166752f0bf`. Verify current HEAD before review.

## Verified state

- S01/M0-01 scope planning is complete: solution architecture overall, detailed Kubernetes (D-009), white/provider-aware visuals (D-008). [Six scenario families](evidence/S01-release-scope.md) need later real rendering/owner acceptance.
- S02/M0-03 research found technical Huawei mapping candidates for all 17 minimum items, but redistribution/extraction/output-use clearance remains open (O-002). The user-supplied JuanDiaz00 alternative and eight draw.io-type on-premises mappings are assessed in [S02 follow-up](evidence/S02-additional-icon-sources.md). No Huawei asset package is adopted/bundled. Detailed Kubernetes catalog/rules remain M2/M4 work.
- S03/M0-04 is complete under D-011. Private repository access is available through CLI; the GitHub connector returns 404. Initial `main` commit `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e` passed two real preflight jobs; [S03 evidence](evidence/S03-repository-runner-preflight.md) records the transient offline/broker recovery and actual job environment.
- Runner ID 2, `macbook-pro-m2-max-mingrammer`, v2.338.2, label `mingrammer-macos-arm64`, runs as a separate LaunchAgent under `~/Library/GitHubActions/mingrammer-macos-arm64`. Existing seven services were preserved. Required-check enforcement is unavailable on the private repository's current plan; recheck live status before jobs and preserve owner-only trust. No product pipeline has run.
- The host has Python 3.13.7 and Docker; native host Graphviz remains absent. S04 Linux images contain Python 3.13.13, diagrams 0.25.1, Graphviz 12.2.1, SDK 2.3.0 and Noto Sans/Thai. No host Graphviz/font installation was made.
- Current S04 prototype: `cloud-architecture-diagrams@mingrammer-local`, version `0.1.0-alpha.1`, installed through the bundled Codex CLI 0.166.0-alpha.5.1. [Proof JSON](evidence/S04-local-plugin-proof.json) records the actual cache, immutable image ID, source/archive hashes and checks. Source is under `spikes/s04-local-plugin/`; build artifacts are ignored.
- Installed-cache and relocated-ZIP SDK tests passed: three tools discovered, English/Thai fixture rendered, five local artifacts read with matching checksums, invalid requests rejected, inline PNG matched, network-none/read-only/non-root/resource controls inspected and no pilot containers left after disconnect. Relocation is on the same Mac, not second-machine acceptance. PNG was visually inspected; SVG font portability remains open.
- Setup downloads/builds the runtime separately on each machine; MCP startup checks the image/source fingerprint and performs no install. Rendering mounts only `~/Documents/CloudArchitectureDiagrams`; files persist until user removal. Docker must be running. This is a fixed three-node feasibility pilot, not the full provider/Kubernetes renderer or release installation experience.
- Earlier authenticated loopback HTTP/amd64-emulation work is retained as historical research under `spikes/s04-runtime/` and [historical metadata](evidence/S04-runtime-proof.json). D-013 retires that hosting proposal. No cloud resource, public endpoint or account plugin was created.

## Next activities

1. Continue S04/M0-02 in a locally executing Work Desktop chat. The local plugin is installed, but the current chat may need a fresh session to discover it. Follow the concrete prompt in the [local plugin README](../../spikes/s04-local-plugin/README.md). Record actual tool discovery/invocation, visible PNG preview and retrieved SVG/PNG/JSON/DOT/manifest; SDK evidence does not satisfy this check.
2. Review the final commit in a separate Astra/High pass. No independent model review has been executed. Use [model strategy](model-strategy.md); record model/effort, base/head SHAs, findings/disposition and checks. Do not label a self-check as Astra review.
3. Finish M0-05 supported local host modes, runtime/fonts and provisional limits from actual Work evidence. Timeout/OOM/cancellation stress, complete transport limits and SVG font appearance remain open. M0-02/M0-05 are partial; S04/M0 is not complete.
4. After applicable M0 exit evidence, continue S05/M1 canonical model/schema, package and deterministic quality gate. For Docker on the Mac runner, first verify actual service-account daemon/context access; do not use Linux-only GitHub container/service jobs on macOS.
5. Carry O-002 into M2-03 before bundling Huawei icons; no permission request was sent. Carry D-010's generic on-premises mappings into M2-04 with exact source/terms/attribution/export checks.
6. M5 replaces the pilot with the full local adapter and polished setup/preflight/upgrade/removal. M6 must run the same plugin version and complete Work workflow on two independently prepared machines. No automatic dependency or credential sync is established.

## Resume prompt

```text
Continue this Cloud Architecture Diagram Plugin project from doc/project-management/HANDOFF.md.
D-013 selects an installable local plugin with runtime installation on each machine;
it supersedes D-012 central hosting. Read the active milestone and relevant requirement
IDs, verify Git state, then continue S04 actual local Work preview/export and M0 review.
Target Work first; Claude Code is later. Keep docs English and distinguish local SDK,
Actions checks, real Work behavior, independent review and owner acceptance.
Update HANDOFF.md and ACTIVITY-LOG.md with verified outcomes.
```

## Update discipline

Record completed task IDs, actual checks/results, final commit when available, unresolved decisions and next steps. Keep this file compact; detailed evidence belongs with the relevant milestone. Recheck dynamic dependency/model/runner facts before relying on older snapshots.
