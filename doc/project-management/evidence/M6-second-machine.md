# M6-01 — The Second Machine

Date: 2026-11-05 (Asia/Bangkok) | Task: M6-01 | Plugin: `0.1.0-alpha.1+d27ef23f6f94` | Core: `0.5.0a1` | Decision: D-029

**Result: M6-01 passes on the owner's report (D-029). The same plugin version completes the Work workflow on two Apple silicon Macs with independently installed runtimes, and the core reproduces on the second one, with all 26 views identical to the baselines.** This describes `0.1.0-alpha.1+d27ef23f6f94`. [D-030](M6-p0-gaps.md) later moved the plugin to `0.1.0-alpha.1+88ce2c0cd0dc`, and under D-032 the owner chose not to rerun the second Mac, so that version passed on the [first Mac](S09-Work-validation.md#final-version) only.

## What differs between the machines

| | First Mac | Second Mac |
|---|---|---|
| Account in the session record | `visarut.pha` | `visarut.phartchayanusit` |
| System | Darwin 27.2.0 arm64 | Darwin 27.0.0 arm64 |
| uv | 0.13.0 | 0.13.7 |
| Graphviz | 16.1.0 | 16.1.0 |
| Install route | A build from this repository | The versioned ZIP, checked by SHA-256, with no checkout |
| Runtime | Removed, then set up by the chat | Set up by the chat for the first time |

## The Work chat

One new Work chat ran all five prompts of the [Work check](S09-Work-validation.md), in its own folder outside any checkout. The session record has originator `codex_work_desktop` and GPT-6.1 Sol / High. "Owner" marks what only the owner could see, and the rest was checked from the session record and the files.

| Check | Result |
|---|---|
| Version the chat reports | `0.1.0-alpha.1+d27ef23f6f94`, as expected |
| Runtime reaches `ready` | Passed, in under 30 seconds: `RUNTIME_NOT_READY`, `setup_runtime`, then `ready`. No blockers |
| An approval prompt | Owner: an allow prompt appeared once, at first use. See [below](#the-allow-prompt) |
| PNG visible in the chat | Passed. Owner: it appears as on the first Mac, as a normal image that can be downloaded |
| All six files | Each of the four bundles holds all six. Owner: this check passes |
| Edit keeps IDs and returns the updated source | Passed. All 10 IDs stayed, and `s3`, `app-1-s3` and `app-2-s3` were added. No existing resource or relationship changed. The view gained only those three, and the assumptions were extended to cover the bucket |
| Invalid model gives `REFERENCE_MISSING` and no image | Passed, at `/relationships/0/target_ref`, and no bundle was made |
| Kubernetes overview and detail, with readable Thai | Passed. Both views share one model, so their IDs agree. Owner: passed |
| Anything unexpected | The first AWS model failed with two `SCHEMA_FIELD_INVALID`, and the chat corrected it. No `busy` answer, and no `RUNTIME_INSTALLING` |

The chat read only the plugin's skill, model guide and two examples. It read no `src`, no other plugin's skill and no checkout, so this is the first run that shows the plugin's skill alone is enough, on one model.

Rendering all four models from the second Mac on the first gives the same `diagram.svg`, `diagram.png` and `view.json`, byte for byte. These are not kept in the repository. The owner keeps the session record and bundles under `~/Downloads/second-machine-evidence`.

## The allow prompt

The owner reports an allow prompt that appeared once, at first use, and that everything worked after it. The session record has approval policy `never` and `danger-full-access`, the same as the first Mac, where the owner saw none, and it holds no approval record. So the prompt came from somewhere the session does not record, and this page does not know what it asked. The README's statement that the app may ask for approval stands. A chat under a stricter setting has still not run.

## Core reproduction

[The proof](M6-second-machine-proof.json) comes from `scripts/reproduce_core.py` on the second Mac, at `fd3cc80`. It cloned the repository, downloaded its own Python 3.13.7 and packages, and took both routes. All 26 views match the baselines in both routes, the routes agree, and the wheel has the digest CI and the first Mac's proof record. Its source digest equals this checkout's.

The two machines share Graphviz 16.1.0, Python 3.13.7 and the locked packages, which is the pinned runtime NFR-001 asks about, and they differ in the system release and uv. A different Graphviz has not been compared. The owner's copy of the proof left iCloud Drive before it reached the repository, so this file is re-created from what the Claude session read, and it has the original's 797 bytes.

## Limits

- Two Macs, both Apple silicon, with Homebrew. Intel Macs, Windows and Linux stay unverified, as the README states.
- One model, GPT-6.1 Sol, on both.
- Both machines were on one person's accounts.
- The chats had full access, so how the app asks under a stricter setting is unverified.
