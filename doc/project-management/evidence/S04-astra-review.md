# S04 Independent Astra Review

Date: 2026-11-01 | Model: GPT-6 Astra / High | Scope: frozen alpha.1 diff only.

User-authorized review chat: `01a1964a-7a2a-70e3-a577-84316bb691b0`, local host. The reviewer confirmed model/effort from its session metadata. The initial turn hit a usage limit; the owner resumed it and the review completed. No model substitution is recorded.

Reviewed base: `afbaccad87019d35bff12d335ec534166752f0bf`.
Reviewed HEAD: `720831733bdb99061f62f7d509d95a65aa7f748b`.

## Confirmed finding

P2: `spikes/s04-local-plugin/launch.py:24-32` at the reviewed HEAD accepted a pre-existing output-root symlink because mkdir(exist_ok=True) follows it. The resulting writable Docker bind could expose a broader host directory than the declared output root. Tool-level artifact-file symlink checks did not protect the already-followed mount source. This violates NFR-003 and is separate from a speculative symlink race.

The reviewer confirmed acceptance with a mocked launcher and the host's symlinked /tmp, without invoking Docker or writing files. The real current output root was not a symlink. No additional material finding was reported within the documented historical HTTP research scope.

## Disposition

Fixed in the native alpha.2 source: directory components open without following symlinks, approved root identity is checked, and artifact directories/files are anchored with descriptors. Seven actual filesystem regressions include existing-root and ancestor symlinks. The Docker mount is no longer the default execution path. [Native proof](S04-native-runtime-proof.json) records checks.

The finding is implementation-fixed and locally tested, not independently reapproved. This Astra review does not cover the new native diff. Use a fresh base-to-HEAD review before M0 closure.

## Review evidence and limits

The reviewer inspected requirements/model policy/HANDOFF, both proof snapshots, launcher/server/worker, packaging and the historical HTTP spike. It checked frozen source/ZIP hashes, fingerprint, artifact checksums, manifests, Python syntax, JSON, SVG, dependency pins and whitespace; inspected English/Thai fixtures. It did not rerun Docker workloads/integration harnesses, actual Work flow, a second machine, timeout/OOM/cancellation stress or symlink-race cases. Concurrent host-test evidence was excluded. No tracked files were changed by the reviewer. This is review evidence, not release approval.
