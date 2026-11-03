# S09 Fable Review

Reviewer: Claude Fable 5.1 (`claude-fable-5-1`) / High, in a fresh agent under D-021. Implementer: Claude Opus 5.5, so the two share a vendor, which reduces some shared assumptions and does not remove them. The agent worked from a copy outside the checkout, changed nothing in it, and did not use an account or a paid model. It cannot accept the Work check, which only the owner can run.

## First pass: `43b444d..0dd1da1`

**Request changes**, on two P2 findings. No P0 or P1. It reran the lane (123 passed), the full gate in its copy, lint, format and strict mypy, and `scripts/work_host_check.py` against the real engine (35 of 35), and it confirmed that the S04 fixture and its marketplace have no diff from `43b444d`.

| Finding | Severity | Failure the reviewer reproduced | Disposition |
|---|---|---|---|
| P2-1 | P2 | `prune --apply` raised `TypeError` on Apple's Python 3.9.6, which the README names as enough, because `shutil.rmtree` takes `dir_fd` only from 3.11. The syntax checks and the tests, which ran on 3.13, could not see it | Fixed: removal by descriptor, and every server test now runs on `/usr/bin/python3` |
| P2-2 | P2 | Closing the tool process during first setup recorded `RUNTIME_SETUP_FAILED`, "could not build", with an empty detail, and the next chat relayed that false cause | Fixed: a stopped setup records nothing, and the state stays `not_installed` |
| P3-1 | P3 | A stop during the setup probe wrote a `ready` marker with a failed probe forever. After an upgrade with the same lock, the marker described the previous release | Fixed: no marker after a stopped probe, and the marker names the version it probed with |
| P3-2 | P3 | The skill said `content[1]` is the image after `render_model`, which is false on any failure and for a PNG too large to preview | Fixed in the skill |
| P3-3 | P3 | The skill said the plugin sends nothing anywhere, and also that setup reaches the network | Fixed in the skill and README |
| P3-4 | P3 | While setup ran, `get_capabilities` also said to call `setup_runtime` | Fixed: the blocker is now `RUNTIME_INSTALLING` |
| P3-5 | P3 | `list` and `prune` reported nothing to do when the root could not be read | Fixed: the tool answers `ARTIFACT_UNSAFE`, and the script answers `OUTPUT_ROOT_UNAVAILABLE` and exits 1 |
| P3-6 | P3 | A client's request ID could name setup's internal key and cancel it | Fixed: internal keys are objects |
| P3-7 | P3 | The real-core shutdown test closed the server before the core had created anything | Fixed: it now waits for the scratch folder to exist |
| P3-8 | P3 | The evidence said the `--locked` sabotage was rerun, and the proof held only the first run | Fixed: the sabotage set was rerun and recorded at the fix head |
| P3-9 | P3 | A cancel landing after the core finished leaves a published bundle the client never hears about | Open. It conforms to the protocol, and the bundle shows up in `list_bundles` |
| P3-10 | P3 | A release with a new lock left the old 60 MB runtime behind | Fixed: a successful setup removes it |
| P3-11 | P3 | `remove` deleted whatever the test-only variable pointed at | Fixed: it deletes only what setup made, by name |

The reviewer also confirmed the following as measured: 35 of 35 on the host's engine, setup in 4.4 seconds from an empty uv cache, a largest reference PNG of 383,538 bytes, no blocking on the server's stderr, early-cancel behavior, protocol behavior, and the absence of model text from the log and runtime files. It could not check the live rehearsal table, because no transcript was in the repository, and it ran nothing in the Work page, nothing on another Mac, and no Python download during setup.

## Recheck: `0dd1da1..4466ace`

**Approve.** The same agent worked from a fresh copy. It reproduced each P2 scenario against the fixes: under Python 3.9.6, `prune --apply` removed a bundle holding a subfolder, a symbolic link to `/etc/hosts` and a FIFO, and `/etc/hosts` stayed untouched. Stopping setup at 0.4, 0.9 and 2.0 seconds left no failure record and no marker, and the next chat reported `not_installed`. It confirmed the fixes for P3-1 to P3-7, P3-10 and P3-11, reran the lane and the host check (35 of 35), and found no regression in the cancel paths. No P0, P1 or P2 remained.

## Bounded check: `4466ace..82f14e0`

After that approval, the implementer found the README's build command failing on Apple's Python, and the recheck had raised a traceback from `prune` as a residual P3. Both fixes changed code after the approved commit, so the same agent reviewed that diff.

**Approve, and its approval carries to `82f14e0`.** It reproduced the failure on the earlier script and the fix on the new one, with a byte-identical archive from Python 3.9.6 and 3.13.7. It reran the lane (131 passed), lint, format and strict mypy. It did not rerun the host check, because no server code changed, though the implementer did at this commit, with 35 of 35.

## What stays open

| Finding | Why it stays |
|---|---|
| P3-9 | A cancel that lands after the core finished leaves a bundle the client is not told about. This conforms to the protocol |
| P3-12 | `scripts/runtime.py` labels any `OSError` as `OUTPUT_ROOT_UNAVAILABLE`, naming the Documents path, even when `setup` is what failed. Only reachable from a terminal with an unusual precondition, and the exit code stays 1 |
| P3-13 | `ARTIFACT_UNSAFE` on a root denied by permissions says "not an ordinary folder", which is the wrong words for that case |

## After the approval

One test changed, and no shipped code: `test_a_client_request_id_cannot_cancel_setup` replaces a check that the sabotage rerun showed proved nothing. It was confirmed to fail when the sabotage is applied. The reviewer has not seen this test.
