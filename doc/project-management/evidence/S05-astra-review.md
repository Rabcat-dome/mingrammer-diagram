# S05 Independent Astra Review

Date: 2026-11-02 | Model: GPT-6 Astra / High | Chat: `01a1964a-7a2a-70e3-a577-84316bb691b0`.

Initial review: base `ff53a88944e981be2bbbab171e0ccf8cecdb4e41`, head `e645415801f4dcafae9f53f08f56b74adb4936af`.

## Confirmed initial findings

1. **P2 - alternate Kubernetes ownership bypass** (`validation.py:323-328` at the reviewed head). Generic ownership edges checked endpoints/cycles but omitted the kind/cluster/provider/namespace rules applied to `kubernetes.owner_ref`. An explicit ReplicaSet-to-Pod ownership edge across namespaces passed both modes; encoding the same owner with owner_ref failed. The fix shares the same supported workload-owner rules across both encodings, while preserving same-provider administrative Scope ownership as a separate dimension.
2. **P2 - docs gate depends on historical files outside the repository** (`repository_checks.py:68-70`). Five absolute links in the historical S04 host report required the original user's output folder. With repository files intact but those artifacts unavailable, the mandatory lane failed. The fix records host paths as provenance text and retains actual repository-relative PNG/SVG evidence links. New portable link policy rejects absolute/outside-repository local links, even when those files happen to exist.

Targeted regressions failed against the original implementation (six ownership cases and one portable-docs case), then passed after the fixes. The expanded suite passes 82 tests, including valid/invalid alternate owners, wrong namespace/cluster/kind, mixed ownership cycles, administrative Scope ownership and a temporary clean repository without historical host artifacts. Full local gate passes. Independent confirmation of these fixes is pending re-review of the committed fix head.

## Review checks and disposition

The reviewer ran the original 65 tests without environment sync/pytest cache, checked CI source/lock hashes and the saved missing-actionlint aggregate failure, compared wheel Python sources with the frozen commit and imported the wheel from outside the checkout. The actual initial CI run 41423620941 passed eight lanes. Source/docs/runtime/cache were not modified by the reviewer; additional probes were isolated.

A suspected literal-backslash-n workflow defect was investigated and dismissed: byte inspection found actual LF (10), and job logs confirmed checks used the installed per-run environment. It is not a third finding.

The editable actor conditions are supplementary to current private access and server-side fork policy. Root read-only API checks found only Rabcat-dome/admin and fork-PR workflows disabled; settings were not changed. Broader provider/catalog/render semantics, production isolation, actual full Work plugin and second-machine release acceptance are outside this M1 review.
