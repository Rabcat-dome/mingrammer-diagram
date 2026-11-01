# S04 / M0 Feasibility Closeout

Completed: 2026-11-02 (Asia/Bangkok) | Runtime: `0.1.0-alpha.3` | Reviewed code: `2fc8047242dbbf337a8c44ba09979b2f181adb32`.

**S04 and M0 feasibility are complete. S05 / M1 is ready to start.** This closes the execution-route/version/isolation investigation and its independent review, not the full architecture plugin or release acceptance.

## Exit evidence

| Task | Result / evidence |
|---|---|
| M0-01 | Scope planning complete in S01: five environments, detailed Kubernetes and provider-reference visual direction; [scope briefs](S01-release-scope.md) |
| M0-02 | Selected per-machine native local route under D-013/D-014. Owner reports actual separate Work alpha.3/Darwin, visible PNG and five files; [Work result](S04-Work-validation.md) |
| M0-03 | Huawei/on-premises research complete in S02; [rights/gaps](S02-icon-sources-and-rights.md). Huawei redistribution rights remain unresolved and block bundling/release, not the completed investigation |
| M0-04 | Separate self-hosted runner and real jobs passed; [S03 evidence](S03-repository-runner-preflight.md), [native PATH preflight](S04-native-runner-preflight.json). Final 2026-11-02 API check: runner ID 2 online/idle, project label unchanged |
| M0-05 | Native macOS candidate, versions/fonts, controls and numeric limits selected/proven for the fixed fixture; [native evidence](S04-native-runtime.md) and [proof](S04-native-runtime-proof.json) |
| Independent review | Astra/High reviewed alpha.3 base 1fd2d72 to head 2fc8047; both alpha.2 P2 issues fixed, no new confirmed actionable runtime finding; [final review](S04-native-alpha3-review.md) |

The supported S04 route is local execution on the tested macOS ARM64 host with per-machine Python/Graphviz setup. No central server, required Docker, public rendering MCP or model API key is needed. MCP stdio and the direct script invoke the same controlled renderer. Windows/Linux, cloud-only Work and a second physical machine are not proven.

## Selected prototype bounds

The fixture accepts exactly three literal labels, each 1-256 codepoints, with a 1 MiB CLI/MCP frame bound. Renderer limits: 55 seconds wall, CPU 45/50 seconds, 16 MiB per file, 1 GiB sampled process-group RSS and 256 MiB sampled scratch bytes. One render per helper is admitted at a time. Renderer/descendant networking is denied by the tested macOS policy. These are S04 bounds, not final product-size guarantees; sampled memory/disk controls can overshoot.

Direct script, installed MCP and relocated ZIP checks passed, including five artifact reads/hashes and English/Thai rendering. Seven filesystem, four resource, six shutdown and deleted-intermediate regressions passed. A same-Mac relocation proves packaging relocation, not second-machine acceptance. The owner's Work result supplies preview/export feasibility; no Work transcript, bundle ID, hashes or independently confirmed transport route was supplied.

## Carry forward

| Work | Owning milestone |
|---|---|
| Core package/schema/diagnostics/reference validation and actual deterministic quality gate | S05 / M1 |
| Provider/Kubernetes catalogs, approved exact assets, Huawei rights resolution | S06 / M2; unresolved rights block packaging/release |
| Full controlled renderer, final NFR-009 bounds/security/error behavior | S07 / M3 |
| Provider-reference diagrams, detailed Kubernetes and English/Thai visual acceptance | S08 / M4 |
| Polished plugin installation/preflight/upgrade/removal and host integration | S09 / M5 |
| Same version on two independently prepared machines, SVG/font portability, all P0 and owner release acceptance | S10 / M6 |

The quality-gate recommendation remains **yes**: implement deterministic native GitHub Actions checks in M1 and expand them with the product. Keep owner-only trusted self-hosted execution and manual merge discipline; the current private plan cannot enforce required checks. Record Astra review separately; CI/rendering require no paid model call. Main is unchanged; no merge, cloud deployment or product release is implied.

Use [HANDOFF](../HANDOFF.md) for the concise S05 starter and [session plan](../session-plan.md) for all activities.
