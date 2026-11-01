# S04 Native Alpha.2 Astra Review

Date: 2026-11-02 | Model: GPT-6 Astra / High | Chat: `01a1964a-7a2a-70e3-a577-84316bb691b0`.

Reviewed base: `720831733bdb99061f62f7d509d95a65aa7f748b`.
Reviewed head: `1fd2d72a22183b65d76ea0bea255702a769ae62f`.

The reviewer confirmed the earlier output-root symlink fix, frozen source/archive/font/artifact hashes and documented scope. Two new confirmed P2 findings remained:

1. `execution.py:35-36,55-58` at the reviewed head: the renderer starts a separate session, but helper SIGTERM bypasses finally. A separate interpreter test confirmed that the helper exited while the renderer survived. Normal host shutdown could remove the watchdog's wall/RSS/disk enforcement and leave scratch data. Fix requires helper lifecycle cleanup and a real shutdown regression.
2. `execution.py:21-22`: a file deleted between enumeration and lstat raises FileNotFoundError and aborts an otherwise valid render. The reviewer inspected diagrams' deletion of DOT intermediates and reproduced the snapshot failure with an isolated mock. This was not presented as an observed integration failure. Fix requires one lstat per entry and skipping disappeared files.

Alpha.3 implements signal-aware process/request supervision and an async cancellation scope, plus a deletion-tolerant directory snapshot. Targeted tests cover direct and worker-thread SIGTERM/SIGINT, signal during spawn, actual MCP stdio shutdown during an outstanding call, process reaping, scratch cleanup and a deleted intermediate. The [final alpha.3 review](S04-native-alpha3-review.md) independently confirmed both fixes at 2fc8047 with no new confirmed actionable runtime finding. This historical alpha.2 review alone is not approval of alpha.3.

No tracked source, shared runtime or installed cache was changed by the reviewer. The review used isolated processes/mocks and excluded concurrent live-host evidence. Exact Work UI, another machine, hard kernel memory/disk quotas and full product acceptance remained outside the established evidence.
