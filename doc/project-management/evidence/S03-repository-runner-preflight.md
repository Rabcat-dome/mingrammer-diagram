# S03 Repository and Runner Preflight

Date: 2026-11-01 (Asia/Bangkok) | Task: M0-04 | Status: Complete; separate service runner installed and two real preflight jobs passed.

The owner explicitly authorized the additional Mac runner, commit/push and real GitHub testing as D-011. This record supplements the [quality gate plan](../quality-gate.md); product scope remains [requirements revision 0.5](../../requirements/requirements.md). Actual job metadata and parsed reports are in [S03-runner-job.json](S03-runner-job.json). Renderer/runtime proof remains S04; a successful preflight does not establish a working product quality gate or Work plugin.

## Repository and trust evidence

| Check | Verified result |
|---|---|
| Repository / identity | `Rabcat-dome/mingrammer-diagram`, personal-user-owned, private, not archived/disabled; GitHub CLI API identity `Rabcat-dome`, admin/push/pull access |
| Connector | Metadata lookup returned 404; CLI access independently verified the repository. CLI is the fallback for this private repository. |
| Initial Git state | No local commits or remote branches; initial runner/workflow lists both empty |
| Published state | Initial tree pushed to `main` at `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e`; workflow dispatched from that commit |
| Actions | Enabled; allowed actions `all`; server setting does not require SHA pinning; default workflow token read-only and PR review approval disabled |
| Collaborators | API returned only owner `Rabcat-dome` at inspection |
| Test workflow trust | Owner/main-only manual dispatch, `permissions: {}`, no checkout, third-party actions, installs or network calls in the probe script; five-minute job timeout and project concurrency group |
| Rulesets / protection | Both API reads returned 403 requiring a plan change for this private repository. Server-enforced required checks are not established. |

CI can execute and report results with the current plan. Until repository capabilities change, review the exact commit, require applicable results and record review before manual merge/release. This policy does not technically prevent bypass. No repository visibility, account plan, Actions settings or other repository settings were changed. Future PR execution must retain the trusted/untrusted lanes in the quality-gate plan.

## Installed runner and service

| Item | Verified value |
|---|---|
| Runner / ID | `macbook-pro-m2-max-mingrammer` / `2` |
| Scope / group | This repository / `Default` |
| Version / platform | Runner `2.338.2`; macOS `27.0.1` build `26A434`; native ARM64 |
| Labels | `self-hosted`, `macOS`, `ARM64`, `mingrammer-macos-arm64` |
| Root / permissions | `/Users/visarut.pha/Library/GitHubActions/mingrammer-macos-arm64`, mode `0700` |
| Work folder | `_work` under the runner root; no spaces in the path |
| Service label | `actions.runner.Rabcat-dome-mingrammer-diagram.macbook-pro-m2-max-mingrammer` |
| LaunchAgent plist | `~/Library/LaunchAgents/actions.runner.Rabcat-dome-mingrammer-diagram.macbook-pro-m2-max-mingrammer.plist` |
| Service entry point | Runner root's `runsvc.sh`; installed/started using its `svc.sh` |
| Account | `visarut.pha`; same user as the existing services, not a separate low-privilege CI account |
| Actual job PATH | `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`; matches the new cached service PATH |
| Post-test API | Online and idle at evidence capture; continuous availability is not established |

The package came from a cached original `actions-runner-osx-arm64-2.338.2.tar.gz`, verified before extraction against the [official release](https://github.com/actions/runner/releases/tag/v2.338.2): SHA-256 `25a065af409ffa317ab4d5a3b614dd15fc9c40f2172bc1b35a1b1258e919a388`. A redundant new download was cancelled after finding the matching complete archive; the temporary partial file was cleaned up. The cached archive and its existing installation were unchanged.

The short-lived registration token stayed in process memory and was supplied through the runner's secret input environment mechanism, verified in the [pinned runner source](https://github.com/actions/runner/blob/v2.338.2/src/Runner.Listener/CommandSettings.cs). No token, credential file, service logs or runner binary was added to the project. The root remains outside the repository.

All seven previous runner services remained loaded after setup, eight total. They belong to `Assess-Management`, `Zensical-from-MKDocs`, `azimutt-mod`, `java-migration`, `openmetadata-for-migration`, `rule-engine`, and `structurizr`; none was moved, reconfigured or relabeled. Separate registrations provide routing, while sharing host resources and account privileges. This LaunchAgent operates in the user's login session; runner availability depends on the Mac, session and network being available.

## Real GitHub execution

Tested commit: `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e`.
Workflow: [runner-preflight.yml](../../../.github/workflows/runner-preflight.yml).
Workflow Git blob: `db8af1e674f40b48a6b4eb980591bbc4766ba7de`.
Workflow SHA-256: `08337c1a87c09d601c277c7db01592662e4c39619505f875f0cf8d6641798734`.

| Dispatch | GitHub evidence | Job times (UTC) | Result |
|---|---|---|---|
| 1 | [Run 41283576002](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283576002) / [job](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283576002/job/124780247773) | `2026-11-01T07:08:31Z` to `2026-11-01T07:08:43Z` | Success; runner ID 2 |
| 2 | [Run 41283801076](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283801076) / [job](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283801076/job/124780902569) | `2026-11-01T07:11:46Z` to `2026-11-01T07:11:57Z` | Success; runner ID 2 |

Both jobs ran on runner ID 2 with the four expected labels. All setup/probe/completion steps succeeded. Parsed logs confirm `github_actions: true`, the tested commit, service user/PATH, Darwin ARM64, Python 3.13.7 at `/usr/local/bin/python3`, uv 0.13.0, Git 2.54.0 and actionlint 1.7.12. Temporary write/read/cleanup passed; available disk was about 265-266 GiB, shared rather than reserved.

`dot` was absent on the actual service job PATH. Both reports explicitly state `graphviz_found: false`, `render_check: not_executed` and `quality_gate: not_executed`. No Graphviz/font/diagrams dependency was installed. Existing system Thai-font candidates were inspected only; selection, licensing and visual rendering remain S04.

After the first successful job, one API observation reported offline while the LaunchAgent/listener stayed running. Diagnostics showed broker HTTP request timeouts. A later no-cache API read returned online without restarting/reconfiguring the service; the second dispatch then passed on the same runner. This is observed recovery, not a proven root cause or continuous-availability guarantee. If scheduling stalls, compare current API status, service status and diagnostics before changes. No firewall setting was changed.

## Local verification and operational handoff

Actionlint 1.7.12 passed with the [custom-label configuration](../../../.github/actionlint.yaml). The embedded probe compiled and passed locally before publication, explicitly reporting `github_actions: false`. Documentation, ID/link, JSON, whitespace and targeted credential-pattern checks were performed; final counts are in the activity log. These are local checks, separate from the two actual jobs. No separate model code review or Work invocation occurred.

The job-logs REST output was initially blocked by GitHub CLI's terminal-escape protection. Logs were successfully read through `gh run view --log`, captured without printing raw control sequences, and parsed into the metadata-only JSON evidence. The evidence capture initially required an online snapshot and stopped when it observed offline; this prompted the diagnostic check and second actual dispatch rather than an assumed health result.

To inspect this runner later:

```sh
cd /Users/visarut.pha/Library/GitHubActions/mingrammer-macos-arm64
./svc.sh status
gh api repos/Rabcat-dome/mingrammer-diagram/actions/runners
gh run list --repo Rabcat-dome/mingrammer-diagram --workflow runner-preflight.yml
```

New service logs are under `~/Library/Logs/actions.runner.Rabcat-dome-mingrammer-diagram.macbook-pro-m2-max-mingrammer/`; detailed diagnostics are in the runner root's `_diag/`. Inspect selected fields and avoid copying credentials or complete environment dumps into evidence. If this setup is later retired, stop/uninstall this service and remove only runner ID 2 after verifying its current identity.

O-005 is resolved for S03: the owner selected the runner route and real execution is verified. M0 remains open for S04 Work invocation/artifact delivery and versions/fonts/isolation/limits. Huawei rights remain O-002, and M1 implements the product quality gate. Follow-up evidence/status documentation does not change the tested workflow; compare its recorded Git blob when resuming.

## Primary platform references

- [Runner scope and registration](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners).
- [Mac service setup](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/configure-the-application).
- [Runner requirements](https://docs.github.com/en/actions/reference/runners/self-hosted-runners) and [label routing](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow).
- [Manual dispatch](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow) and [secure use](https://docs.github.com/en/actions/reference/security/secure-use).

Platform guides support the setup/behavior descriptions. Repository, machine and job results come from this session's live inspection and the linked GitHub runs.
