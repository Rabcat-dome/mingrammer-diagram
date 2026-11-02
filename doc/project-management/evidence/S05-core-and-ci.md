# S05 Core Contract and First Quality Gate

Started: 2026-11-02 | Branch: `codex/s05-core-quality-gate` | Base: `ff53a88944e981be2bbbab171e0ccf8cecdb4e41` | Status: Local implementation/checks passed; actual CI and independent review pending.

## Implemented scope

- M1-01: core package `0.2.0a1`, Python 3.13.7, locked Pydantic/development dependencies, CLI and core wheel/sdist build. Existing S04 plugin/runtime remains alpha.3 and is unchanged.
- M1-02: strict versioned [schema](../../../schemas/architecture-v1.schema.json), metadata/scopes/boundaries/resources/placement/relationships/views, structured bounded diagnostics, strict/lenient core behavior and Kubernetes context. See [contract guide](../../design/core-contract.md).
- M1-03: global IDs, typed/dangling refs, same-provider administrative scope, containment/ownership cycles, explicit views/exclusions and Kubernetes cluster/namespace/owner/node/storage/config references. Ordinary traffic cycles remain valid.
- M1-04: [workflow](../../../.github/workflows/quality-gate.yml) and same local aggregate command run docs/traceability/frozen-proof checks, narrow credential patterns, lint/format/types, actionlint, schema/core tests and core package build. All lanes are mandatory; future provider/catalog/render/plugin checks are explicitly deferred.

Core validation results disclose `core_only` and pending catalog/provider/render checks. No new Work rendering, catalog/license clearance, production renderer or two-machine acceptance is claimed. English/Thai data is supported; documentation is English. No Docker resource, runtime cache, existing runner registration or main branch was changed.

## Local evidence

65 tests passed. Positive fixtures pass both independent JSON Schema and core validation. Negative tests cover malformed/duplicate/oversize/deep/nonstandard JSON, unknown versions/fields/providers, strict field types/port bounds, IDs/references/cycles, missing views/endpoints, Kubernetes wrong kind/cluster/namespace/role, Secret payloads and independent namespace/node dimensions. Diagnostics do not echo rejected payload values.

Local aggregate lanes passed. Clean wheel installation used a separate temporary Python environment, hash-locked runtime requirements and a working directory outside the checkout; imported package came from that environment's site-packages and validated the Kubernetes fixture. A controlled PATH without actionlint produced aggregate failure while all other lanes passed; missing required checks cannot silently pass. These are local checks, not GitHub job evidence.

## CI and review

Actual runner job, exact tested SHA, reports and Astra/High review are pending. The project runner was rechecked online/idle before implementation. The workflow executes only explicit owner actions in the private repository; it does not enable external/fork PR code on the personal host. Read-only token, pinned actions, no persisted checkout credentials, per-run environment cleanup and 14-day synthetic artifact retention are configured.

M1/S05 remains in progress until actual runner evidence and required independent review are recorded. No merge or release is implied.
