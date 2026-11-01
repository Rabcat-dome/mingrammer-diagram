# Quality Gate and Self-Hosted Runner Plan

Updated: 2026-11-01 | Status: Product quality gate remains proposed. S03 runner/service setup and two actual manual preflight jobs passed; M0-04 complete.

## Recommendation

**Yes: implement a GitHub Actions quality gate, starting in M1 and expanding with each component.** This project combines AI-authored input, provider-specific semantics, external icon assets and Graphviz output. Automated validation catches repeatable failures; diagram inspection and recorded code review cover meaning and usability.

The [S03 evidence](evidence/S03-repository-runner-preflight.md) verifies private/admin access, Actions enabled and the D-011 separate runner `macbook-pro-m2-max-mingrammer` (ID 2, v2.338.2) installed as a LaunchAgent. Its `mingrammer-macos-arm64` label and actual service environment were confirmed by two successful jobs. `dot` is absent on the real job PATH; Graphviz/font/render proof remains S04. One transient offline/broker-timeout observation recovered without a restart, followed by a successful second dispatch. Recheck current availability before future jobs.

The current private repository's rulesets/protection endpoints return 403 requiring an account-plan change. CI can run and report failures, but server-enforced required checks are unavailable at this snapshot. Until capability changes, use a manual policy: review the exact commit, require applicable CI results and record review before merge/release. Do not describe this as bypass-resistant enforcement. No plan purchase or visibility change is proposed as a prerequisite to continuing development.

## Proposed workflow shape

Proposed file: `.github/workflows/quality-gate.yml`, to be implemented in M1. The path is a plan, not an existing file. Local scripts must exist and pass before workflow steps call them. Add later checks when their code arrives; never make a placeholder check report that unimplemented behavior passed.

| Check | Starts | Blocking result | Evidence |
|---|---|---|---|
| `docs-contract` | M1 | Broken local links, duplicate requirement IDs, invalid task/test references, malformed examples | Documentation/contract report |
| `static` | M1 | Formatting/lint/type errors in implemented Python; invalid workflow syntax | Ruff/type checker/actionlint or selected equivalents |
| `schema` | M1 | Valid fixtures rejected; invalid IDs/references/cycles accepted | Unit/contract report with requirement IDs |
| `catalog-license` | M2 | Missing required types/assets, invalid mappings, missing rights/notice evidence | Inventory, asset digests and license report |
| `provider-semantics` | M2 | Provider/Kubernetes rules fail, wrong cluster/namespace scope, conflated ownership/placement, or invalid Service/Ingress/storage references | Rule fixtures and primary references; FR-018/029 and T-017 |
| `render-security` | M3 | Code/path/URL/Graphviz/SVG injection, limits, cleanup or isolation regression | Negative cases and bounded-execution results |
| `render-smoke` | M3/M4 | Invalid/missing SVG/PNG or bundle metadata, icon loss, unreadable required labels | Model, diagnostics, images, normalized graph |
| `visual-regression` | M4 | Unexpected structural/visual change lacking reviewed baseline update; unresolved provider-reference mismatch under FR-048/T-016 | Before/after/diff images, pinned official references and inspection/deviation notes |
| `package-contract` | M5 | Broken manifests, missing packaged assets/skills, tool contract or clean-install failure | Package inventory and protocol smoke result |
| `quality-gate` | M1 onward | Any applicable required check fails, is cancelled, or is unexpectedly skipped | Aggregate result at tested SHA |

Activate catalog/renderer checks as mandatory before merging their implementation milestone. The gate's list of applicable checks is explicit and versioned; a component cannot disable its own failed checks through path filtering. Keep `quality-gate` as the stable status name, and make it a required check if repository-plan capabilities later permit rules. Apply the manual merge/release policy while enforcement is unavailable. Manual Work acceptance and second-machine reproduction remain release evidence in M6.

## Execution lanes

| Lane | Route | Policy |
|---|---|---|
| Trusted development | Verified self-hosted runner, native Python/Graphviz | Bounded PR/push checks on code from authorized trusted contributors; read-only repository token by default |
| Untrusted PR/fork | Isolated disposable Linux runner/VM, if enabled | Do not run attacker-controlled code on the personal persistent host; without this lane, block external PR execution and require a separately reviewed trusted change |
| Container/Linux release checks | Verified Linux runner with Docker | Use when the selected deployment package needs a Linux/container image; do not route container jobs to a macOS runner |
| Actual Work acceptance | Selected Work environment | Install/invoke/download and inspect artifacts; protocol mocks are insufficient |

GitHub's [runner requirements](https://docs.github.com/en/actions/reference/runners/self-hosted-runners) require Linux plus Docker for Docker container actions/service containers. Prefer native jobs for a verified macOS runner. The [GitHub secure-use guide](https://docs.github.com/en/actions/reference/security/secure-use) explains persistent self-hosted runner risks and least-privilege workflow controls. These recommendations are directly relevant to code execution on the owner's machine.

## Completed preflight (M0-04)

1. Private/admin access and enabled Actions verified via CLI; connector access remains unavailable.
2. D-011 separate registration verified: runner ID 2, v2.338.2, native Mac ARM64, exact project labels, LaunchAgent installed/started. All seven previous services remain loaded.
3. Two actual service jobs verified user/PATH, Python 3.13.7, uv 0.13.0, Git/actionlint and temporary write/read/cleanup. Graphviz is missing; system font candidates are not a reproducible/rendered font selection.
4. [Published preflight workflow](../../.github/workflows/runner-preflight.yml) passed twice at `5c3859b4a865c3e65fc6ed80a389ec8f8a32182e`; [job metadata/reports](evidence/S03-runner-job.json) include tested SHA, workflow digest and actual runner identity. The reports explicitly state rendering/product checks were not executed.
5. [Actionlint labels](../../.github/actionlint.yaml) match API and job evidence: `self-hosted`, `macOS`, `ARM64`, `mingrammer-macos-arm64`. S03 documents the transient availability observation and current-plan enforcement limitation.

M0-04 is complete. Existing registrations/settings were preserved; renderer dependencies were not installed. The manual preflight uses no checkout or third-party actions and zero repository token permissions. M1 still must implement and execute the product quality gate; a preflight success is not evidence of schema, provider, asset, renderer or plugin correctness.

## S04 runtime evidence before M1

The [S04 evidence](evidence/S04-runtime-and-hosting.md) records synthetic render, English/Thai labels, installed local stdio plugin SDK checks, historical loopback HTTP/download research, negative cases and Docker resource configuration. It is not an Actions job, actual Work test or product quality-gate pass. The host remains without native Graphviz; tested Linux images contain the dependencies.

If M1 uses this Docker route on the existing Mac runner, use native shell steps invoking Docker CLI and verify that service account's actual daemon/context access first. This does not make GitHub `container:` or `services:` jobs supported on macOS. D-013 retires the central-host plan. An earlier amd64 smoke used emulation and does not prove another physical machine or OS. Preserve existing owner-only trust until the real product gate exists.

## Workflow controls

- Trigger on trusted PR updates and default-branch pushes; permit manual reruns. Establish repository visibility/trust policy before enabling self-hosted PR execution. A same-repository branch check alone does not establish author trust.
- Use `permissions: contents: read` by default; grant specific extra permissions only to the job that needs them. Disable checkout credential persistence for test jobs.
- Pin third-party actions to reviewed full commit SHAs; use a frozen dependency lock and recorded Graphviz/font versions. Do not run package installs with `sudo` in routine jobs.
- Do not use `pull_request_target` to check out and execute untrusted PR code. Do not interpolate PR titles, bodies or labels directly into shell commands.
- Run under a dedicated low-privilege account where feasible, outside personal credential locations. Workspace cleanup is required but does not establish isolation from malicious jobs.
- Use per-run temporary directories, job timeouts, bounded renderer child processes, and cleanup on failure. Avoid concurrent jobs that overwrite shared outputs or mutate global tools.
- Cache dependencies only with OS/architecture/lockfile keys and trusted origins. Do not restore executable artifacts from an untrusted PR into trusted jobs.
- Upload synthetic-fixture diagnostics/images/reports, even on failure where possible; do not upload customer architectures or secrets. Proposed CI artifact retention: 14 days, subject to repository limits/owner preference.
- Keep CI independent of paid model calls. Record the Astra review separately. Cloud deployment and publishing are outside the test job and require their own selected destination and release scope.

## Verification depth

Prioritize meaningful negative cases over high test counts: dangling/cyclic references, invalid provider placement, Kubernetes cluster/namespace scope and ownership/placement errors, bad Service/Ingress/storage references, secret payload exposure, generic fallback disclosure, requested-security omission, unsafe assets/paths, malicious labels/SVG, resource exhaustion, and inaccessible output bundles. T-017 must also preserve IDs between overview/detail views.

Store structural expectations alongside fixture JSON. Normalize volatile IDs/timestamps before comparisons. Pin reference render/font versions; visual differences across OS versions need review, not blind pixel acceptance. Baseline updates require an explanation of semantic and visual changes. Inspect labels, icons, boundaries, edge direction and clipping.

The S02 research inventory records source availability and Git blob IDs; it is not a release asset allowlist. The catalog/license gate must require actual permission/license references, applicable notices and original/derived asset SHA-256 values. Unknown Huawei redistribution evidence or null asset digests must not be treated as a passing package check.

Run the fast lane on ordinary changes. Run the full fixture set for core/schema/catalog/assets/renderer/adapter changes and every release candidate. Documentation-only changes can use the fast lane after scope detection is verified. The aggregate gate must still execute and distinguish intentional non-applicability from failed or cancelled dependencies.

## Release conditions

- All P0 requirements have check or manual acceptance evidence at the release SHA.
- Every applicable automated check passes; no required check is silently skipped.
- Required icons/notices have redistribution evidence, including Huawei assets.
- Astra review completed on the final code; confirmed Critical/High findings resolved, Medium findings dispositioned.
- Owner inspected T-001..006; the same plugin version completed the Work workflow on two supported machines (FR-066/T-010), and clean-runtime core reproduction passed. Record setup/authentication steps rather than assuming installation or credentials sync automatically.
- Setup, supported host modes, limitations, package digest, rollback steps and handoff are current.

Suggested tooling (Ruff, a type checker, pytest, actionlint, dependency/secret scanners) is a proposal. Pin exact tools and commands during M1; this document does not claim they are installed or that any checks passed.
