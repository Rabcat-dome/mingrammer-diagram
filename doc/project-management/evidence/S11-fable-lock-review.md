# Review of b0a8b4d: readiness checks no longer read each other as a setup

- Reviewer: Claude (model name as given to this session: Fable 5.1, id `claude-fable-5-1`), with no prior context on this change.
- Base: 762ab28
- Head: b0a8b4d418c381b38d8b65b0b8640cd227dd4a5e
- Scope: `git diff 762ab28 b0a8b4d -- plugins tests`, which touches only
  `plugins/cloud-architecture-work/server/work_adapter/runtime.py` and `tests/test_work_plugin.py`.
- Nothing tracked was edited. Scratch output is under `reports/fable-lock-work/` (git-ignored).

## The change

Before, both a readiness check (`Runtime._setup_locked_elsewhere`) and a setup took `setup.lock`
exclusively and non-blocking, so two checks at the same instant each read the other as a setup and
`state()` reported `installing`. The fix makes the check take a shared lock (`LOCK_SH | LOCK_NB`),
which only an exclusive holder (a setup) refuses, and makes `setup()` retry its exclusive lock for
up to `SETUP_LOCK_WAIT_SECONDS = 1.0` in 20 ms steps (`_take_setup_lock`), so a check caught in its
instant no longer makes a setup report `RUNTIME_SETUP_BUSY`.

## Verdict on the fault: gone

What I ran, all with `/usr/bin/python3 -I -B`, a throwaway HOME, and the server started the way the
host starts it (`server/main.py` over stdio):

1. Built a copy with `python3 scripts/build_work_plugin.py --output reports/fable-lock-work/build`
   (source commit b0a8b4d, clean). Set up a real runtime through `setup_runtime` (uv cache was warm;
   render probe passed).
2. Base reproduction: the same built plugin with `runtime.py` replaced by the 762ab28 copy, one
   server process, 40 rounds of 5 simultaneous `search_catalog` calls: 39 of 200 answered
   `runtime_unavailable` / `RUNTIME_INSTALLING` with no setup running.
3. Head, one process, same storm: 200 of 200 `ok`.
4. Head, three server processes sharing one data folder, each sending 60 rounds of 5 simultaneous
   `search_catalog`, while a fourth process polled `get_capabilities` continuously: 900 of 900 `ok`,
   45 of 45 polls `ready`. No `RUNTIME_INSTALLING`.
5. The named tests: `uv run --frozen python -m pytest -q tests/test_work_plugin.py -k "readiness_check
   or waits_out or never_read_as_installing or setup or shutdown or stopping"`: 14 passed.

## Attempts to break the fix

Each probe is a script in `reports/fable-lock-work/` run against the built head copy.

- Two setups at once (two processes, one fresh data folder, real `uv sync`): the first took the lock
  at once and held it 2.2 s; the second waited 1.009 s and returned `RUNTIME_SETUP_BUSY`. In an
  earlier run where the first setup finished within about 1 s, the second took the lock after it and
  ran its own setup, also `ready`: serialised, not concurrent. Two CLI `scripts/runtime.py setup`
  commands at once behave the same.
- A real setup reported as not running: a server in one process polling `get_capabilities` while a
  CLI setup ran in another saw `not_installed`, `installing`, `ready` in that order, and its next
  `search_catalog` was `ok`. A check against an exclusive holder in the same process also reports
  `installing` (flock locks are per open file description, so the same process conflicts with itself).
- Setup wrongly busy under dense polling: six processes taking and releasing the shared lock as fast
  as they could (about 610,000 checks in 5 s) while 200 setup lock attempts ran: all 200 taken,
  longest wait 75 ms, 32 of 200 had to retry at all. The 1 s budget is ample.
- Readiness check blocking: it uses `LOCK_NB` and never waits.
- Lock left held: `_take_setup_lock` returns with the lock held only inside `setup()`'s `with open`,
  so the handle closes on any exit, including `SetupInterrupted`. Confirmed free after an interrupted
  setup.
- Stop during the wait: `stop_all()` then `setup()` with a shared holder that released after 0.3 s:
  setup waited the check out, then `_start` refused to launch (stopping), giving
  `RUNTIME_SETUP_INTERRUPTED` after 0.32 s, no failure file written, lock free. The wait is bounded at
  1 s and runs on the daemon setup thread, so it cannot hold up the process exit.
- `remove` and `prune` commands: `prune` touches the output folder only and never the lock. `remove`
  is discussed as a finding below; its behaviour is unchanged by this diff.
- Non-EWOULDBLOCK `OSError` from `flock` (a filesystem without flock): the check reports `installing`
  as before; setup now spends 1 s before `RUNTIME_SETUP_BUSY` instead of returning at once. Same
  outcome as base, slightly slower; not a regression worth a finding.

### Do the new tests fail for the reason their names give?

Checked by running each test's body against the base copy of `runtime.py`:

- `test_a_readiness_check_reads_only_a_setup_as_a_setup`: on base, a shared holder makes the check
  return `True` and `state()` say `installing`; expected `False` / `not_installed`. Fails for the
  named reason.
- `test_setup_waits_out_a_readiness_check_but_not_a_setup`: on base it fails first with
  `AttributeError: module 'work_adapter.runtime' has no attribute '_take_setup_lock'`, before any
  behaviour is checked. Its second half would also fail for the named reason (base returns
  `RUNTIME_SETUP_BUSY` in 0.000 s, so `gave_up_in_time` is `False`). See P3-2.
- `test_parallel_calls_on_a_ready_runtime_never_read_as_installing`: the base reproduction above
  (39 of 200) shows it fails on base for the named reason; it passed on head.

## Findings

### P3-1 (pre-existing, not introduced by this diff, confirmed): `remove` deletes the lock file out from under a running setup

- File: `plugins/cloud-architecture-work/server/work_adapter/runtime.py`, `Runtime.remove`, lines
  525-541 (the `"setup.lock"` entry at line 531); `scripts/runtime.py remove` calls it without taking
  the lock.
- Input: process 1 holds the exclusive lock (a setup); process 2 runs `remove()`; process 3 calls
  `_setup_locked_elsewhere()` or `setup()`.
- Wrong result: after `remove`, the check returns `False` (the running setup is invisible because the
  new `setup.lock` is a different inode) and a second setup can take the lock, so two setups can run
  while the first's environment folder is being deleted beneath it. Confirmed with a probe
  (`B_before_remove: true`, `B_after_remove: false`, `B_second_setup_could_take_lock: true`).
- The base copy behaves identically; this diff neither causes nor fixes it. Out of scope, recorded so
  it is not lost. A fix would be for `remove` to take the exclusive lock first, or to refuse while it
  is held.

### P3-2 (test quality, confirmed): one new test does not fail on base for the reason its name gives

- File: `tests/test_work_plugin.py`, `test_setup_waits_out_a_readiness_check_but_not_a_setup`,
  lines 737-766.
- The test calls `runtime._take_setup_lock` directly, which does not exist on base, so on base it
  fails with `AttributeError` before asserting anything. Its `box.setup()` half does fail on base for
  the named reason (`gave_up_in_time` false), so the test is not vacuous, but the "waits out a
  readiness check" half is only exercised through the private helper, not through `setup()` itself.
  Replacing the helper call with a timed `box.setup()` under a short-lived shared holder would make
  the whole test fail on base for the named reason. Does not block.

No P1 or P2 findings. I found no way, with threads or with several processes on one data folder,
to make a ready runtime report `installing`, to run two setups at once, to leave the lock held, or to
make a setup report busy when no setup is running.

## Not run

- The full test gate, lint and type checks (already passed per the brief).
- A setup that downloads (every run used the warm uv cache).
- A `remove` or `prune` while a real server setup was mid-`uv sync` (only the lock-level interaction
  above).
- A SIGTERM to the server process during the 1 s wait at the protocol level (checked at the
  `Runtime` level only).
- Intel Macs, or any host but this one.

## Disposition

Approved. The fault is gone under single- and multi-process load, the fix is small and bounded, and
the two P3 items are respectively pre-existing and a test-strength note; neither blocks.
