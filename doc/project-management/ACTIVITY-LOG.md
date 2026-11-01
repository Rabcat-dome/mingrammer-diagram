# Activity Log

Purpose: concise English continuity record for another machine or chat. Current state and resume instructions: [HANDOFF](HANDOFF.md).

## 2026-10-31 — Requirements and delivery planning

Completed activities:

- Read the supplied v1.1 requirements without treating embedded proposals as user approvals.
- Inspected the initially empty Git working tree and checked ancestor instructions.
- Prepared one consolidated requirements draft covering five environments, provider semantics, Huawei asset rights, Work integration and release acceptance.
- Split implementation into M0–M6 with tasks, dependencies, exit evidence and a later Claude Code phase.
- Recommended Sol implementation and separate Astra code review, with effort/risk guidance and no mandatory model API in rendering.
- Recommended phased GitHub Actions quality gates using verified self-hosted capacity; documented native macOS vs Linux/container routing and untrusted-PR controls.
- Recorded open runtime/icon/runner decisions and a compact cross-machine handoff.

Verified observations:

- No implementation or existing workflow was available to test.
- Local Git remote is configured; connector metadata lookup returned 404, leaving remote access/visibility unverified.
- Current shell is Darwin/ARM64, Python is available, and `dot` is not on its PATH. Runner service environment was not inspected or changed.
- Official model/plugin/runner documentation and upstream diagrams custom-node/license/provider inventory sources were read; source links and snapshot details are in [decisions](decisions.md).

Documentation validation passed: 8 English Markdown files, 21 local links/anchors, 60 unique requirement IDs, 15 acceptance scenarios and 30 task IDs. No broken local references, undefined checked IDs, unbalanced code fences, Thai text or unintended trailing whitespace were found. This is documentation validation, not implementation acceptance.

Pending activities:

- Jointly refine/accept the requirement draft; evaluate O-001 execution routes against the confirmed portability goal.
- Complete M0 runtime, icon-rights, repository/runner and version/limit feasibility work.
- Begin M1 implementation and CI only after applicable M0 decisions/evidence exist.

No code review, pipeline execution, renderer installation, Work plugin installation, cloud provisioning, commit or push was performed in this planning pass.

## 2026-10-31 — Cross-machine plugin clarification

- User confirmed that cross-machine use is the reason for requesting a plugin and asked whether the proposed skill would still be a plugin.
- Clarified the product structure: installable plugin containing a workflow skill and renderer tool integration. Recorded D-006 and added P0 FR-066.
- Strengthened T-010/M6-01 to require the same plugin version to complete the Work diagram workflow on two supported machines, in addition to clean-runtime core reproduction.
- Kept remote MCP as a technical recommendation; host mode, hosting destination and provisioning remain undecided.
- Updated the requirements baseline to revision 0.2, related milestones, release gate, README and handoff. No implementation or deployment was performed.

Revision 0.2 documentation checks passed: 8 English Markdown files, 21 local links/anchors, 61 unique requirement IDs, 15 acceptance scenarios and 30 task IDs; no checked-reference, code-fence or whitespace errors. Plugin behavior remains unimplemented and untested.

## 2026-10-31 — New-session work breakdown

- Added a session plan mapping S01–S10 onto the existing M0–M6 tasks, with dependencies, deliverables, owner collaboration points and model recommendations from the existing policy.
- Included a reusable session starter and a separate review-session prompt, with exact-commit review evidence and an initial-tree option for the first commit.
- Identified S01 as the starting discussion; S02 icon-rights research and S03 runner preflight can proceed independently, followed by S04 runtime proof.
- Linked the session plan from README and HANDOFF. No new chats were created/dispatched and no implementation was started.

Session-plan documentation checks passed: 9 English Markdown files, 27 local links/anchors, 61 unique requirement IDs, 15 acceptance scenarios, 30 milestone tasks and 10 session entries; no checked-reference, code-fence or whitespace errors. Implementation, pipeline and Work acceptance remain pending.

## 2026-10-31 — S01 scope discussion started

- Started S01/M0-01 at the user's request and reread the current scope, session plan, handoff and decisions. Verified that the repository still has no commits and no applicable ancestor AGENTS.md was present.
- Prepared a session-specific scope record and six synthetic acceptance briefs, including authoring requests, inspection/rejection points and iterative-edit checks.
- Recommended retaining all five environments and every named minimum-catalog item. Proposed solution-architecture depth and a white/provider-icon visual starting point without recording them as accepted scope.
- Requested two owner preferences: architecture granularity and visual style. Answers and joint scope acceptance remain pending; S01 is not complete.
- Linked the briefs from the requirements, milestones, session plan, decisions and handoff. No later session, implementation, renderer/Work test, code review, commit or deployment was started.

Initial S01 proposal documentation checks passed: 10 English Markdown files, 34 local links/anchors, 61 requirement IDs, 15 acceptance scenarios, 30 milestone tasks, 24 decision/proposal/question IDs and six ordered briefs. Owner preference answers had not yet been incorporated at that point.

## 2026-10-31 — S01 answers incorporated and scope planning completed

- Received explicit owner answers: solution architecture with cluster-level Kubernetes; white/provider-icon starting point close to each provider's architecture conventions published on its website.
- Recorded D-007/D-008 and resolved O-008. Updated O-004 to retain actual rendered comparison/acceptance as later work rather than an unanswered style preference.
- Opened official AWS/Azure/GCP/Huawei visual-reference entry points and recorded them in the S01 result. This is source research, not an icon redistribution clearance or completed image audit.
- Updated the single requirements baseline to revision 0.3, adding FR-048/T-016 for provider-aware visual fidelity while retaining all named minimum-catalog items.
- Completed S01/M0-01 scope planning with six working scenario briefs. Other M0 tasks, full baseline/release acceptance, actual image acceptance, implementation, runtime proof and separate model review remain pending.

Final S01 documentation checks passed: 10 English Markdown files, 35 local links/anchors, 62 unique requirement IDs, 16 acceptance scenarios, 30 milestone tasks, 26 decision/proposal/question IDs and six ordered briefs. No checked-link/ID, code-fence, English-only, stale-preference-status or whitespace errors. This validates documentation consistency, not rendering or release acceptance.

## 2026-10-31 — Kubernetes detail correction

- The owner corrected the first granularity answer: Kubernetes must be detailed. D-009 supersedes the earlier cluster-only limit recorded above; overall solution-architecture depth and provider-reference visuals remain.
- Updated the single baseline to revision 0.4 with shared Kubernetes detail inventory, FR-018/FR-029 and T-017 across EKS/AKS/GKE/CCE/on-premises. Defined explicit cluster/namespace/ownership/placement, traffic, storage, configuration and security relationships without live discovery or secret payloads.
- Added M2-06 and M4-05; updated schema/renderer/Work task descriptions, S06/S08 ranges, reference scenario subviews, quality gate, model-policy risk examples, README and handoff.
- Read current primary Kubernetes concept pages linked in the baseline. No implementation, runtime or model review was performed.

Revision 0.4 documentation checks passed: 10 English Markdown files, 35 local links/anchors, 64 requirement IDs, 17 acceptance scenarios, 32 milestone tasks, 27 decision/proposal/question IDs and six reference families. No checked-reference, code-fence, English-only, stale cluster-only scope or whitespace errors. This is documentation validation; implementation and runtime acceptance remain pending.

## 2026-10-31 — S02 icon sources, rights evidence and gaps

- Continued to S02 at the user's request. Completed M0-03 source/rights research and gap inventory, while distinguishing this from asset packaging clearance.
- Inspected Huawei LATAM color libraries at v3.2 / commit 52c33aa12fb816a5de403da85067e1c0f039b5be: 15 libraries, 262 entries (254 SVG, eight groups), with title/format candidates for all 17 named minimum items. No license/notice file or clear plugin-redistribution grant was found in the audited repository/README/release evidence; O-002 remains open.
- Reverified diagrams source at 8c1446fbfa4a8d88e5c7bca7101ddc5af7933379, inspected its MIT license/classes/complete resource tree, and recorded 21 on-premises coverage rows including eight neutral gaps. Its latest release observed is v0.25.1; no dependency pin was selected.
- Recorded 18 detailed Kubernetes asset candidates and read the upstream Kubernetes icon license choice. Inspected an MIT-licensed Tabler neutral-symbol source and checked ten SVG paths individually after a directory listing returned only its first 1,000 entries.
- Added the S02 English assessment and structured metadata inventory. Recorded conditional P-011/P-012 recommendations and updated requirements links, milestones, session plan, handoff, README and the quality-gate evidence contract. Product scope remains revision 0.4.
- Source inspection did not execute upstream scripts, convert/bundle icon assets, install/render a plugin, send permission requests, run a separate model review or commit/push changes. S03 is the next session; independent runtime/runner work need not wait for Huawei packaging clearance.

S02 documentation/inventory checks passed: 11 English Markdown files, one JSON inventory, 44 local links/anchors, 64 requirement IDs, 17 scenarios, 32 tasks and 29 decision/proposal/question IDs. Verified source indices/counts, the 17 Huawei mappings, 21 on-premises rows/eight neutral gaps, 18 Kubernetes candidates and ten neutral SVG paths. No checked-link/ID, code-fence, English-only, whitespace or raw-artwork-in-inventory errors. These are evidence consistency checks, not rendering or packaging clearance.

## 2026-10-31 — User-supplied Huawei alternative and draw.io on-premises mappings

- Assessed JuanDiaz00/Huawei-Cloud-draw.io-icons at ea52d7356e172a85cde7538f293a663eb137611d. Parsed the complete XML: 155 PNG entries, seven unambiguous minimum-service title matches and ten remaining alias/mapping gaps. Its README names VeryIcon; that site's personal/commercial-use claim was recorded separately from still-unestablished source-asset redistribution scope.
- The connector could not read the large XML. After local Python TLS verification failed, system curl retrieved the pinned public file with TLS verification retained; checked its Git blob ID and recorded the source XML SHA-256. Saved metadata only, not artwork.
- Inspected current draw.io code/asset conditions and a reproducible v29.3.2 generic-network stencil source. Both relevant snapshots have Atlassian ecosystem conditions; the historical root also declares CC-BY-4.0 for JGraph-provided icons with third-party qualifications. No blanket Apache-2.0 claim is made for art.
- Mapped the eight on-premises concepts to seven verified generic symbols plus explicit labels/compositions. Recorded D-010 and baseline revision 0.5/FR-014; exact export, source conditions/attribution, visual fit and package checks remain M2/M4 work.
- Added a follow-up assessment/metadata inventory and updated decisions, milestones, session plan, README and handoff. Kept the LATAM color/SVG source as the preferred technical Huawei candidate and the user-supplied PNG source as an alternative; neither is adopted or cleared for bundling.
- No upstream source code was executed, no source artwork was saved/bundled, and no renderer/Work/pipeline test, separate model review, commit, push or external permission request was performed.

S02 follow-up checks passed: 12 English Markdown files, two JSON inventories, 54 local links/anchors, 64 requirement IDs, 17 scenarios, 32 tasks and 31 decision/proposal/question IDs. Verified 155 PNG metadata entries, seven title/index matches plus ten unresolved Huawei items, and complete coverage of the eight original on-premises concepts using seven source symbol IDs. No checked-link/ID, JSON, code-fence, English-only, whitespace or raw-artwork errors. Runtime export/rendering and actual package checks remain pending.

## 2026-11-01 — S03 repository and runner investigation

- Continued M0-04. Rechecked repository/ancestor instructions and local Git state; no applicable AGENTS.md, local commits or remote branches exist.
- The GitHub connector still returns 404. GitHub CLI live API identity `Rabcat-dome` has admin access to the existing private repository. Actions is enabled with read-only default token permissions; the repository has zero eligible runners/workflows and only the owner in the collaborator snapshot.
- Inspected seven loaded local runner LaunchAgents and selected non-secret registration/cached-PATH metadata; all belong to other repositories. The representative Assess-Management API runner is online/idle, macOS ARM64, version 2.338.0, with an AMS-specific label. No registration was borrowed, stopped or reconfigured.
- Python 3.13.7, uv 0.13.0 and actionlint 1.7.12 are available locally. Graphviz `dot` is absent from the current shell and seven cached runner PATHs. System Thai font candidates exist; no rendering or redistribution check occurred. The metadata reader initially rejected a UTF-8 BOM and was corrected using utf-8-sig without modifying service files.
- Rulesets and branch-protection APIs returned 403 requiring a plan change for this private repository. Updated the quality-gate plan to distinguish CI reporting/manual merge policy from unavailable server-enforced required checks. No account/visibility/settings changes were made.
- Added an owner/main-only manual runner-preflight workflow and actionlint custom-label configuration. The first lint identified the undeclared custom label; adding its explicit configuration resolved the error. The local embedded probe passed temporary write/read/cleanup and reported Graphviz absent, with rendering/product checks explicitly unexecuted.
- Added the S03 evidence record and P-014 additional-registration proposal; updated shared status/handoff. Requirements remain revision 0.5. Runner setup and a real service job remain pending; M0-04 is not complete. No dependency installation, commit/push, separate model review, Work invocation or remote job was performed.

S03 checks passed: actionlint 1.7.12 and the local embedded Python probe, including temporary write/read/cleanup and explicit non-Actions/non-render/product-gate status. Documentation consistency passed for 13 English Markdown files, two JSON inventories, two YAML files, 66 local links/anchors, 64 requirements, 17 scenarios, 32 tasks and 32 decision/proposal/question IDs. No checked-link/ID, JSON, fence, newline or whitespace errors. Actual registration/service-job evidence remains pending; no commit or push was performed.

## 2026-11-01 — D-011 runner setup authorized and installed

- The owner explicitly selected the additional runner plus commit/push and real GitHub testing. Recorded D-011; baseline product scope remains revision 0.5.
- Rechecked live CLI identity/admin access, private visibility, empty remote branches and zero initial runners before setup. The connector remains unavailable for this private repository; CLI is used for registration and forthcoming dispatch.
- Verified official v2.338.2 macOS ARM64 package digest `25a065af409ffa317ab4d5a3b614dd15fc9c40f2172bc1b35a1b1258e919a388`. Reused a matching cached original archive; cancelled only this session's redundant stalled download and cleaned its temporary partial file.
- Registered runner ID 2, `macbook-pro-m2-max-mingrammer`, with project label `mingrammer-macos-arm64`. Installed/started its separate LaunchAgent; API verified online/idle, version 2.338.2. All seven previous services remain loaded. No Graphviz/font dependency or repository setting was changed.
- Registration token remained outside tool output/project files. Extended the probe to report actual service user, PATH and macOS version. Updated actionlint/local probe checks pass; publication and real-job evidence are in progress at this checkpoint.

## 2026-11-01 — S03 actual GitHub jobs completed

- Published the initial documentation/workflow tree to private `main` at `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e` under D-011. This bootstrap uses the default branch because manual workflow dispatch requires its file there; future feature branches follow the project branch policy.
- Actual run [41283576002](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283576002), job 124780247773, passed on runner ID 2. Afterward one API observation showed offline while the listener/service stayed running; diagnostics showed broker HTTP timeouts and a subsequent fresh read returned online without restart.
- Ran a second actual dispatch to investigate subsequent scheduling: [41283801076](https://github.com/Rabcat-dome/mingrammer-diagram/actions/runs/41283801076), job 124780902569, passed on the same runner and tested SHA. Evidence capture recorded online/idle afterward; continuous availability is not claimed.
- GitHub CLI rejected direct raw job-log output containing terminal escape sequences. Read rendered logs through `gh run view --log`, captured/stripped control sequences and parsed the probe reports. The initial evidence capture stopped on the offline snapshot; diagnosis and the second run resolved the immediate scheduling concern without hiding that observation.
- Added metadata-only `S03-runner-job.json`: both run/job URLs and SHAs, expected labels/runner ID, step results, actual service user/PATH/tools, temporary write/read/cleanup and workflow/package digests. Both reports confirm Graphviz absent and rendering/product quality checks unexecuted. No secret or raw service log was added.
- Closed M0-04/O-005, retained the single requirements baseline at revision 0.5 and updated README, handoff, milestones, session plan, decisions and quality-gate status. S04 runtime/Work/Graphviz/font/isolation/limit proof is next. No separate model review or product acceptance occurred.
- Follow-up changes persist evidence/status only; the tested workflow and actionlint configuration remain unchanged from the initial tested commit.

Final checks passed: actionlint 1.7.12; 13 English Markdown files, three JSON evidence inventories, two YAML files, 71 local links/anchors, 64 requirements, 17 scenarios, 32 tasks and 33 decision/proposal/question IDs. No checked-link/ID, JSON, fence, newline, whitespace or targeted credential-pattern errors. Both actual job records match the tested commit/runner, and the workflow Git blob/SHA-256 remain unchanged; the product requirements file also remains unchanged from the initial commit. Final live API check returned runner ID 2 online/idle and all eight LaunchAgent services loaded. The follow-up commit contains evidence/status documentation only.

## 2026-11-01 — S04 central-server direction and local runtime proof

- Started S04/M0-02/M0-05 on `codex/s04-runtime-proof` from `afbaccad87019d35bff12d335ec534166752f0bf`. Rechecked local state and applicable instructions. Consulted official OpenAI plugin/MCP/Work guidance and plugin-creator local/Sites runtime references.
- The owner selected Work Cloud/Web with a central server. Recorded D-012 and requirements revision 0.6; updated FR-060/064/066 and T-010/011 consistently. This does not approve a hosting provider, billing or deployment. No production host was inferred from another project.
- Prepared a bounded synthetic spike under `spikes/s04-runtime/`: pinned multi-platform Python base, direct Alpine packages, hash-locked Python dependencies, controlled plain-node renderer, development-authenticated SDK HTTP server and reproducible verification harness.
- Validated Python 3.13.13, diagrams 0.25.1, native Graphviz 12.2.1, Python binding 0.20.3, SDK 2.3.0 and Noto Sans/Thai fonts inside isolated Linux images. The macOS host's Graphviz/fonts were not changed. Recorded exact font file hashes/name-table notices and installed package inventories.
- Passed native ARM64 renders for 3/30/100/200-node chains (three fresh workers per size), meaningful negative checks, cgroup/temporary-storage configuration checks, authenticated local SDK HTTP discovery/render, protected host downloads and matching artifact/image hashes. Fixed an initial test assumption: the network-none namespace has inactive kernel tunnel devices, so inspect interface state and routes rather than requiring only a loopback entry.
- Built linux/amd64 and smoke-tested English plus English/Thai fixtures under emulation, matching the inspected Cloud Run runtime contract. This is not a Cloud Run run or native-x86 benchmark. Visually inspected the native PNG: labels/boxes/edges readable and no observed clipping; this is not owner/provider-style acceptance.
- Added S04 English assessment, metadata-only proof, SVG/PNG fixture and reproduction README. Recorded P-015 runtime candidate and P-016 Cloud Run evaluation proposal. Requested provider/server, project, region and monthly budget inputs; no cloud resource, public endpoint, account plugin, new Work chat or separate Astra review was created.
- The HTTP proof uses local development bearer auth and temporary files, while only the CLI worker had network-none isolation. Production user auth/requester isolation, durable protected artifact delivery/retention, actual Work invocation/download, cloud controls and final product limits remain open. M0-02/M0-05 and S04 are not complete; the full product quality gate remains M1.

The later D-013 entry below supersedes this central-hosting direction; final source/evidence checks are recorded after it.

## 2026-11-01 — D-013 per-machine local plugin direction

- The owner replaced the assumed free public rendering MCP/central-server route with installation on each machine using the plugin. Recorded D-013, retired D-012/P-016/O-006 hosting inputs and updated the single baseline to revision 0.7. No cloud deployment is needed or authorized by this choice.
- Built an actual S04 local plugin pilot, `cloud-architecture-diagrams` version `0.1.0-alpha.1`, with portable manifest/MCP configuration, synchronized CLI compatibility overlay, useful bundled skill, real stdio server, versioned runtime setup/preflight and a self-contained ZIP. This is a three-node runtime proof; the full provider/Kubernetes product remains M1-M6 work.
- Registered only the new `mingrammer-local` marketplace and installed through the bundled Codex CLI. Existing marketplaces/plugins were preserved and no cache file was edited directly. Runtime state/image and scoped output directory were created locally; no account upload or public publication occurred.
- Installed pinned rendering dependencies in a local Docker image; host Python/Graphviz/fonts were unchanged. Launch checks source fingerprint/image provenance and starts a network-none, read-only, bounded container under the non-root desktop UID with only the designated output bind. No public port, renderer token or model API key is needed. Setup/launch reject remote/TCP Docker contexts; a negative test confirms this before contacting a remote daemon.
- SDK tests passed from the installed cache and a ZIP relocated to a path containing spaces: discovery/preflight, English/Thai fixture, five artifact reads with matching hashes, inline PNG equality, five negative cases per run, inspected resource/network/mount controls and zero remaining pilot containers after disconnect. Visually inspected the new PNG; labels/arrows are readable without observed clipping. A same-Mac relocation is not a second-machine test.
- Corrected SDK integration assumptions found during testing: list_tools returns a result object, runtime metadata now explicitly uses structured content, and a strict nested request rejects unknown request fields. Expected fixture errors return safe tool diagnostics. Initial failed harness runs are not reported as passes.
- Updated English requirements, milestones, session plan, decisions, quality gate, model policy and handoff. Historical local HTTP proof is retained and labeled superseded for hosting. Actual Work chat preview/export, separate Astra review, final host modes/limits and M0 closure remain pending. No new chat/subagent was created.

S04 final checks passed: 16 English Markdown files, six JSON files, two YAML configuration files, 96 local links/anchors, 64 requirement IDs, 17 acceptance scenarios, 32 milestone tasks and 37 decision/proposal/question IDs. Python syntax, proof/source hashes, targeted credential patterns and Git whitespace checks passed. Portable plugin/MCP manifests passed their official Agent Plugins 1.0.0 schemas; generated skill YAML and compatibility-manifest identity were checked. CLI listing confirms the local plugin installed/enabled; installed and relocated SDK runs passed with zero remaining pilot containers. These are local checks, not a new Actions job, actual Work execution, independent Astra review or product acceptance.

Publication checkpoint: S04 source/evidence committed at `07e507f958e11350b45a73c0dbcf04dca679e212` and pushed to private branch `codex/s04-runtime-proof`. `main` was not merged or changed. The following continuity update records that checkpoint; review must use the branch's final HEAD and base `afbaccad87019d35bff12d335ec534166752f0bf`. No new Work chat, account upload, release or Actions dispatch was performed.

## 2026-11-01 to 2026-11-02 — Live desktop test, Astra review and native execution

- The owner explicitly authorized two local chats on the existing checkout: host test 01a1964a-784d-7751-bfe5-57e0bbb4cf39 and GPT-6 Astra/High review 01a1964a-7a2a-70e3-a577-84316bb691b0. No worktree, cloud host or account plugin was created. Both reviewed/tested the frozen alpha.1 source at 7208317.
- Native app-server discovery found all three actual plugin tools. The host chat rendered English/Thai labels and read all five artifacts through real plugin calls, with matching bytes/hashes and inline PNG. The verified mode was Codex Desktop; direct ChatGPT UI access was denied by Computer Use. Actual ChatGPT Work mode/UI export remains open. Thai label literals in the English Markdown report were converted to equivalent JSON Unicode escapes; artifact bytes/proof were retained.
- Astra/High's initial turn hit a usage limit; after the owner resumed it, review completed with one P2: an existing output-root symlink could broaden the writable Docker mount. The reviewer used a mocked launcher, made no source edits and verified frozen source/package/artifact evidence. Recorded exact base/head and limitations in the review report.
- The owner questioned why Docker was needed and noted direct script execution, then requested continuation. Docker was our implementation choice, not a user requirement. Implemented P-017/native alpha.2 and baseline revision 0.8, preserving the same plugin identity and local-install route D-013. A direct script and stdio MCP share controlled rendering code; neither requires a central/listening server or model key.
- Installed native Graphviz 16.1.0 via Homebrew and verified a fresh login shell. Native dependencies include three required upgrades: libunistring 1.4.2 to 1.5, libvmaf 3.1.0 to 3.2.1, dav1d 1.5.3 to 1.5.4; automatic cleanup was disabled. Setup creates a private Python 3.13.7 environment with hashed dependencies and bundled pinned Noto fonts/OFL notices. No global pip/user-font installation or Docker uninstallation occurred.
- Fixed output-root handling with no-follow directory traversal, descriptor-anchored artifacts, private ownership and root identity checks. Seven real filesystem regressions passed. Native wall/CPU/file limits, a sampled RSS/scratch watchdog and macOS renderer network denial were verified. Timeout handling also kills descendants after the worker parent exits; a targeted regression passed. Sampled watchdogs are not kernel quotas or the old Docker controls.
- Native direct-script execution passed with a failing Docker shim/irrelevant remote Docker setting. Installed native MCP and relocated ZIP checks passed discovery, rendering, all five artifact reads/checksums and negative requests. PNG was visually inspected. Portable manifests passed official schemas and skill YAML parsed. Current-chat metadata still showed cached alpha.1, so native installation is not misreported as a reloaded live connection.
- Historical alpha.1 proof now records its exact source_ref for hash validation after source changes. Fresh native proof/fixtures, desktop host evidence, native host discovery and review disposition are recorded separately. The new native diff still needs independent review; exact Work-mode/UI and two-machine acceptance remain pending. M0-02/M0-05 and the product quality gate are not closed.

Actual runner preflight run 41328404188 / job 124913107050 passed at main SHA afbaccad87019d35bff12d335ec534166752f0bf. The service found native dot 16.1.0 and uv 0.13.0; rendering and product checks remained explicitly unexecuted. This verifies service tool visibility after native dependency installation, not the feature branch or native renderer in CI.

Native checkpoint checks passed: 19 English Markdown files, 12 JSON files, 113 local links/anchors, 64 requirements, 17 scenarios, 32 tasks and 38 decision/proposal/question IDs. Python syntax, current/historical source hashes, schemas/YAML, direct/MCP/relocated artifact checks, seven filesystem and four resource cases passed. Existing runner preflight passed and found native Graphviz; the native product pipeline, exact Work UI and fresh native independent review remain pending.

Native source/package checkpoint: `b5524a916d36256335ccfe6c1f1ecc3f2ed4e31d`, published on codex/s04-runtime-proof. The following continuity-only commit records it and preserves the upstream OFL notice bytes through a narrowly scoped whitespace attribute; application code/docs remain checked. The native direct/MCP proof is from 2026-11-02 Asia/Bangkok.
