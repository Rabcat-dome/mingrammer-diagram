# S03 Repository and Runner Preflight

Date: 2026-11-01 (Asia/Bangkok) | Task: M0-04 | Status: D-011 runner registration/service verified online; initial publication and real-job evidence in progress.

This record supplements the [quality gate plan](../quality-gate.md). Product scope remains [requirements revision 0.5](../../requirements/requirements.md). The initial investigation was read-only. The owner subsequently authorized the additional runner, initial commit/push and actual test under D-011. Setup results below supersede the initial zero-runner snapshot; renderer dependencies and repository settings were not changed.

## Repository evidence before authorized setup

| Check | Observed result |
|---|---|
| Local repository | No commits; README and documentation untracked before S03. No remote branch returned by `git ls-remote --heads origin`. |
| Remote | `Rabcat-dome/mingrammer-diagram`, owned by a personal user account, private, not archived/disabled; default branch name `main`, but no branch exists yet |
| Connector access | GitHub connector metadata lookup still returns 404; this is a connector-access limitation, not a missing repository |
| CLI identity/access | GitHub CLI API identity `Rabcat-dome`; repository permissions include admin/push/pull |
| Collaborators | API returned only `Rabcat-dome`, role admin, at this snapshot |
| Actions | Enabled; allowed actions `all`; SHA pinning not required by server settings |
| Default workflow token | Read permission; PR review approval disabled |
| Eligible repository runners | Repository runners API returned HTTP 200 with `total_count: 0` and an empty list |
| Existing workflows | API returned `total_count: 0` |
| Rulesets / branch protection | Both read endpoints returned HTTP 403 with “Upgrade to GitHub Pro or make this repository public to enable this feature.” No server-enforced required-check rule is established. |

Commands used include `gh api user`, repository metadata/collaborators/branches, `actions/permissions`, `actions/permissions/workflow`, `actions/runners`, `actions/workflows`, `rulesets` and `branches/main/protection`. Only selected non-secret fields were recorded. Authentication credentials were not read into project files.

The ruleset/protection response is a current feature-availability limitation. CI can still execute and report failures. Until account/repository capabilities change, merging must follow a documented manual check policy; a passing Actions status alone does not technically prevent bypass. Keep the repository private. Do not change visibility or buy a plan as an incidental CI fix.

## Existing machine and runner scope

Seven loaded LaunchAgent services were found, each configured for a different repository: `Assess-Management`, `Zensical-from-MKDocs`, `azimutt-mod`, `java-migration`, `openmetadata-for-migration`, `rule-engine`, and `structurizr`. Their selected `.runner` metadata and cached `.path` files were inspected; credential files were not opened. UTF-8 BOM handling was needed for the metadata reader and corrected without changing the runner files.

As a representative live API check, `Rabcat-dome/Assess-Management` has runner `macbook-pro-m2-max` (ID 21), online and idle at observation, version 2.338.0, labels `self-hosted`, `macOS`, `ARM64`, `ams-macos-arm64`. Its local listener also reports version 2.338.0. This registration belongs to that repository; its online state and label do not make it eligible for this project. Other repositories' online/busy/version states were not exhaustively queried.

| Host or tooling check | Local observation; not a job result |
|---|---|
| OS / architecture | macOS 27.0.1, build 26A434; Darwin ARM64 |
| Existing service account | All seven inspected LaunchAgents use `visarut.pha`, the interactive user; this is not a separate low-privilege CI account |
| Existing runner paths | Separate directories; no spaces in the seven inspected runner roots |
| Representative cached service PATH | `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin` |
| Python | `/usr/local/bin/python3`, version 3.13.7 in the current shell |
| Dependency installer | `/opt/homebrew/bin/uv`, version 0.13.0 |
| Workflow lint | `/opt/homebrew/bin/actionlint`, version 1.7.12 |
| Git | `/usr/bin/git`, version 2.54.0 (Apple Git-157) |
| Graphviz | `dot` absent from current shell and all seven cached runner PATH lookups; Homebrew lists no installed `graphviz` formula. Other filesystem locations were not exhaustively searched. |
| Free disk | Approximately 267 GiB available during inspection; shared capacity, not a reserved render budget |
| Font candidates | System Thonburi, Sukhumvit Set, Tahoma and Arial Unicode files exist. No font was selected, redistributed or visually tested; a reproducible licensed font selection remains S04. |

Cached PATH resolution and loaded service metadata are supporting evidence. The future project's real job must establish its actual environment, version resolution, temporary-file access and scheduling. Existing services were not stopped, moved, reconfigured or relabeled. Multiple runner registrations on this host share CPU, memory, disk and the user's credentials; separate registrations are routing boundaries, not process isolation.

## Concrete runner recommendation

Add a separate repository-scoped registration on this Mac, keeping the existing projects' registrations intact:

| Item | Proposed value; not registered |
|---|---|
| Repository | `https://github.com/Rabcat-dome/mingrammer-diagram` |
| Runner name | `macbook-pro-m2-max-mingrammer` |
| Runner root | `~/Library/GitHubActions/mingrammer-macos-arm64` |
| Work folder | `_work` within that root |
| Default labels | `self-hosted`, `macOS`, `ARM64`; verify actual labels after registration |
| Custom label | `mingrammer-macos-arm64` |
| Initial job type | Native shell/Python; no container actions or service containers |
| Initial trust | Owner-only manual preflight on `main`, no checkout, no third-party actions, no repository token permissions |

An additional process/service registration is a setup choice, rather than proof that one already exists. The owner selected this recommendation under D-011; registration/service results follow below. Real-job evidence remains pending at this checkpoint. Use a separate low-privilege account when practical; reusing the current account carries the limitations above. Enforce job timeouts and per-project concurrency; this does not cap other repositories' simultaneous work on the same host.

## Authorized setup results

- D-011 explicitly authorizes a separate runner, commit/push and real testing on this private repository.
- Installed official runner v2.338.2 from a cached original macOS ARM64 release archive. SHA-256 `25a065af409ffa317ab4d5a3b614dd15fc9c40f2172bc1b35a1b1258e919a388` matched the official release digest before extraction. A redundant new download was cancelled after the verified complete archive was found; its temporary partial file was cleaned up.
- Registration: ID 2, name `macbook-pro-m2-max-mingrammer`, repository scope, group `Default`, version 2.338.2. API verified online/idle with `self-hosted`, `macOS`, `ARM64`, `mingrammer-macos-arm64`.
- Root: `/Users/visarut.pha/Library/GitHubActions/mingrammer-macos-arm64`, mode 0700, work folder `_work`. Cached PATH is `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin`.
- Installed/started LaunchAgent `actions.runner.Rabcat-dome-mingrammer-diagram.macbook-pro-m2-max-mingrammer` under `visarut.pha`. Its plist invokes the new root's `runsvc.sh`. All seven previous runner services remain loaded, eight total. This is a user login-session service and shares host resources/account privileges.
- The short-lived registration token was captured in process memory and supplied through the runner's secret input environment mechanism. No token or runner credential file was added to this repository.
- Initial commit/push and actual manual dispatch are the next authorized steps. Graphviz/font/render proof remains S04.

## Prepared workflow and activation sequence

Local candidate: [runner-preflight.yml](../../../.github/workflows/runner-preflight.yml). This is a scheduling/environment probe, separate from the future M1 product quality gate. It has a five-minute timeout, owner/main-only manual dispatch, zero token permissions, no checkout/actions/installs/network calls, and a temporary-file write/read/cleanup check. It reports selected tool paths/versions and explicitly records that rendering and the product quality gate did not execute. A missing `dot` is reported, not misrepresented as a successful render.

To obtain real evidence after the runner route is selected:

1. Register the additional runner and start its service, then read the repository runners API to verify name, labels, version and online state. Recheck local/remote Git state first.
2. Review and publish the intended initial repository tree, including the preflight workflow, to `main`. The repository currently has no remote branch; manual dispatch requires the workflow on the default branch. No initial commit or push was made in S03.
3. Dispatch the workflow as the owner. Record its tested commit, run/job URL and actual runner identity. If no eligible runner exists, do not leave a job queued as a substitute for evidence.
4. Inspect logs and summary, resolve failures, and record which tools are present. A local execution of the embedded probe does not count as a runner job.
5. S04 selects/proves Python, Graphviz, fonts and isolation/limits; M1 introduces the actual quality checks. Do not mark M0-04 complete until the real job exists.

If runner setup is deferred, continue independent S04 route investigation while retaining M0-04 as incomplete. GitHub-hosted execution is an alternative requiring an explicit route/quota choice; none was enabled. Migrating this personal repository to an organization solely to share runners is unnecessary for the recommended route.

## Validation and remaining work

Passed: actionlint 1.7.12 with the declared custom-label configuration; embedded Python compilation and a local probe execution using an isolated temporary directory. The probe reported native ARM64 Python 3.13.7, writable/readable temporary storage with cleanup, and Graphviz absent. It explicitly reported `github_actions: false`, `render_check: not_executed` and `quality_gate: not_executed`. Its locally simulated job-summary file was verified and removed with the temporary directory. This is not GitHub scheduling or service-job evidence.

Documentation/inventory checks passed: 13 English Markdown files, two JSON inventories, two YAML files, 66 local links/anchors, 64 requirement IDs, 17 scenarios, 32 tasks and 32 decision/proposal/question IDs. Checked local targets/headings, ID uniqueness/references, JSON parsing, fences, final newlines and whitespace, including untracked files. These checks do not establish runner registration, product behavior, source-asset rights or owner acceptance.

Open: O-005 initial publication and real-job evidence (setup choice resolved by D-011 and runner online); S04 runtime/Graphviz/font/isolation proof; M1 product checks; optional account-plan choice for server-enforced required checks. Huawei source rights remain independently unresolved in O-002. No separate model review or Work invocation was performed.

## Primary references

- [GitHub runner scope and registration](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners): repository versus organization scope and registration process.
- [Runner requirements](https://docs.github.com/en/actions/reference/runners/self-hosted-runners): Linux/Docker requirement for container actions/service containers and label-based routing.
- [Using runner labels](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-in-a-workflow): matching labels apply together to select eligible runners.
- [Manual workflow dispatch](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow): workflow file must be present on the default branch.
- [Secure use](https://docs.github.com/en/actions/reference/security/secure-use): least privilege and persistent-host trust considerations.

External references describe platform behavior. The repository/machine observations above come from this session's live CLI/API and local inspection; they are not inferred from those guides.
