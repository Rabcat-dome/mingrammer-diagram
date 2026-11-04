# Bounded recheck of the three S11 fixes

- Date: 2026-11-05, Asia/Bangkok.
- Base: `b3485c3136839080e5eeae87b413da651038ef9b`.
- Head: `ae8520f3f1a30dbecb11e26921e366ae613e2ea7`, verified checkout HEAD on `codex/s11-review-fixes`.
- Scope: `git diff b3485c3 ae8520f -- scripts plugins tests`. The earlier `doc/project-management/evidence/S11-astra-recheck.md` supplied the definitions of R1–R3; unchanged code was read only as needed to exercise this diff.
- Reviewer: Codex; this filename does not attest to a particular served model or reasoning setting. No delegated agents.

## Verdicts and independent execution

| Finding | Verdict | Own failing input and observed head behavior |
|---|---|---|
| R1: incomplete sdist accepted | **Partly fixed** | Removed only `src/cloud_architecture_diagrams/models.py` from the freshly built real sdist, retaining the real wheel. Audit now refuses it with exactly `sdist: lacks src/cloud_architecture_diagrams/models.py`. However, equal-size invalid source is still accepted (N1), and removing that module from both archives also returns `passed: true, errors: []`. Cross-archive agreement is not an independent completeness check. The exact original one-sided omission is fixed. |
| R2: required files supplied by another root | **Fixed** | Moved only the real sdist's `<root>/pyproject.toml` to `other-root/pyproject.toml`. Audit refuses it with exactly `sdist: has 2 top-level entries where one folder is expected`. The unmodified real pair passes. |
| R3: malformed request echoes invalid ID | **Fixed** | Sent five malformed frames to the actual source stdio server: positive overflow with false method, negative overflow with missing method, array with false method, object with missing method, and boolean with missing method. Every response strictly parses as JSON and has error `-32600`, `id: null`. Then exercised nine valid IDs through missing-method errors, unknown-method errors and successful pings: all 27 retained their IDs. Process exited 0. |

Valid IDs exercised: `0`, `-9`, `2**100`, empty string, a Thai string containing backslash/quote, `1.5`, `-0.0`, `1e308`, and `5e-324`. The server ran with a fresh HOME and data directory under `reports/astra-short-work/server-home`. It received no rendering or artifact-reading requests.

## Confirmed new findings

### N1 — P3: equal-size source corruption passes the new comparison

**Location:** `scripts/release_audit.py:125` (comparison introduced at lines 111–127); test coverage at `tests/test_release_audit.py:385–390`.

**Concrete input:** take the freshly built real wheel/sdist pair; replace the sdist member `src/cloud_architecture_diagrams/models.py` with exactly its original byte count of ASCII `!` bytes. Keep every name, size and other file unchanged. The wheel remains unmodified.

**Wrong result:** `audit()` returns `passed: true, errors: []`. Compiling the changed source bytes independently raises `SyntaxError` on line 1. The new comparison sees matching integer sizes and never compares contents.

**Confirmed:** yes, both audit acceptance and invalid Python. Evidence: `astra-short-work/results.json` entries `same-size-corrupt` and `same-size-compile`; reproducible script `astra-short-work/probe.py`; altered pair under `astra-short-work/same-size-corrupt/`. No corrupted-sdist rebuild was necessary or performed.

**Remedy:** compare file contents or digests, not just byte counts, and add an equal-length unequal-content test. The new test uses `b"x"` versus `b"two"`; it detects size disagreement only, despite its broader name.

### N2 — P3: a valid explicit directory entry makes a buildable sdist fail

**Location:** `scripts/release_audit.py:115–121`, particularly the new source-only-name rejection at line 121.

**Concrete input:** append a normal tar directory member `<root>/src/cloud_architecture_diagrams/render` (`DIRTYPE`, zero size) to the freshly built real sdist, without changing any file; pair with the real wheel. Explicit directory members are ordinary archive structure. The existing size reader includes them, and the new comparison mistakes this directory for a missing wheel file.

**Wrong result:** `audit()` returns `passed: false` with exactly `wheel: lacks cloud_architecture_diagrams/render`.

**Confirmed:** yes. Extracted this modified sdist locally and successfully built its wheel with `python -m build --no-isolation --wheel` (exit 0). Thus the false rejection affects a buildable repack of the real source archive, not only a fake unit fixture. The exact builder-produced, unmodified pair passes.

Evidence: `astra-short-work/results.json` entry `explicit-directory`, `astra-short-work/directory-build.log`, and the modified archive and rebuilt wheel in `explicit-directory/` and `directory-built/` beneath that work directory.

**Remedy:** compare regular package files, excluding directory entries on both archive sides while preserving required-file validation.

No P1 or P2 was established. The paired omission in R1 is a residual inventory limitation of the attempted R1 fix, not a separately counted new finding: deleting the same required runtime module from both sides satisfies this symmetric comparison. Validate an intended inventory or exercise the source-built distribution to close that limitation.

## Tests and whether they fail for their stated reasons

Requested commands executed successfully:

```sh
uv run --frozen python -m build --no-isolation --outdir reports/dist
uv run --frozen python -m pytest -q tests/test_release_audit.py
uv run --frozen python -m pytest -q tests/test_work_plugin.py -k "invalid_request or id_that or fractional"
```

Results: build exit 0; **65 passed** release tests; **15 passed, 150 deselected** Work tests. `PYTEST_ADDOPTS` redirected basetemp and pytest cache under the scratch directory. Work fixtures supply throwaway HOME directories, including their setup server. Logs: `astra-short-work/build.log`, `pytest-release.log`, `pytest-work.log`.

Additional bounded checks:

- `uv run --frozen python reports/astra-short-work/probe.py`: real baseline audit, four modified real sdist cases, paired omission, compile check, 32 real stdio frames and four in-memory audit-test mutation checks.
- Disabled `package_differences` in memory for the added missing-source, missing-wheel and different-source tests, separately. Each failed at its intended assertion. Disabled the root-count behavior in memory for the second-root test; it too failed at its intended assertion. No import/collection failure was counted. The missing-source mutation used its `models.py` parameter; normal pytest covered both parameters.
- `uv run --frozen python reports/astra-short-work/test_protocol_reasons.py`: invoked all five new invalid-ID cases against an in-memory Server/client harness, then restored the old unsanitized `error()` behavior in memory. Each case passed on head and failed its intended error/ID assertion with the old behavior. The three new positive valid-ID cases passed. Real subprocess evidence comes from the selected pytest suite and independent wire probes, not this harness.
- Extracted the explicit-directory sdist and ran `uv run --frozen python -m build --no-isolation --wheel --outdir <scratch>/directory-built <scratch>/directory-source/<root>`: exit 0.

The negative tests exercise the advertised missing-file, split-root and invalid-ID paths. The content-difference test is weaker than its name: only unequal lengths are checked. The real-package test verifies names and sizes, not byte identity or usability. The positive good-ID test verifies preservation; it is not expected to distinguish the old unsanitized implementation, which already preserves good IDs. Mutation results are retained in `results.json` and `protocol-test-reasons.json`.

## Boundaries and repository state

Did not run the full gate, full Work suite, CI, remote reproduction, exhaustive fuzzing, or unrelated feature reviews. Did not install a plugin into the owner's host, commit, push, publish, or transmit archives/artwork. No Huawei image was opened or visually inspected; local packaging copied binary assets without displaying them. The requested test fixtures perform their own local runtime setup.

All custom scripts, modified archives, wire results and auxiliary logs are under ignored `reports/astra-short-work/`. The requested build output is under `reports/dist`, and this report is at the requested ignored path. Initial and final normal-HOME `git status --porcelain=v1` are both empty. No tracked file was edited; mutations existed only in process memory or scratch archives.

**Disposition: changes requested.**
