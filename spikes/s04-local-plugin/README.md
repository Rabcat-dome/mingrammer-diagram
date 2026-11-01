# S04 Native Local Plugin Pilot

Current version: `0.1.0-alpha.2`. The default is native Python + Graphviz. Docker is not required; the earlier container is historical research. No central server or model API key is required.

## What runs locally

The plugin packages a workflow skill, controlled renderer scripts and optional MCP stdio tools. MCP stdio starts a local helper process without opening a listening port. The direct script uses the same renderer without an MCP client. Both return a synthetic three-node SVG/PNG fixture; provider catalogs and detailed Kubernetes remain later work.

## Setup on each Mac

Requires host Python 3.10+, uv and native Graphviz/Fontconfig. The tested host is macOS 27.0.1 ARM64, Python 3.13.7 and Graphviz 16.1.0. Other OS paths and future macOS sandbox availability are unverified.

From the repository root:

```sh
brew install uv graphviz
python3 spikes/s04-local-plugin/build.py
codex plugin marketplace add "$PWD" --json
codex plugin add cloud-architecture-diagrams@mingrammer-local --json
python3 spikes/s04-local-plugin/output/cloud-architecture-diagrams/scripts/setup.py
```

On this Mac the CLI is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. Setup creates a private Python 3.13 environment under `~/.local/share/cloud-architecture-diagrams/runtime/<version>`, syncs the hashed lock and verifies bundled Noto fonts. It records/checks native executable hashes. No global pip install or user-font installation is used. Initial setup downloads Python dependencies; rendering downloads nothing. The source's font binaries and SIL OFL notices are included in the ZIP.

## Execute a script directly

```sh
printf '%s' '{"labels":["Client","Application","Database"]}' |
  python3 spikes/s04-local-plugin/output/cloud-architecture-diagrams/scripts/render.py
```

After installation, the same `scripts/render.py` is inside the installed plugin root. JSON on stdin is data; arbitrary Python, paths and Graphviz options are not accepted. The command prints verified paths/checksums for PNG, SVG, source JSON, DOT and manifest under `~/Documents/CloudArchitectureDiagrams`.

For host tools, call `get_runtime_info`, `render_fixture` with `{"request":{"labels":["Client","Application","Database"]}}`, then `read_fixture_artifact`. Existing chats can retain the alpha.1 Docker process after a CLI upgrade; check the reported version and use a fresh/reloaded local chat for alpha.2. Do not claim an old live connection is native because the new package is installed.

## Verification and boundaries

Run the private runtime Python against `spikes/s04-local-plugin/verify.py`. It tests the direct command with a failing Docker shim and irrelevant remote Docker environment, installed MCP, relocated ZIP, complete artifact reads/hashes, invalid input, seven filesystem cases and timeout/RSS/scratch watchdog cases. [Native evidence](../../doc/project-management/evidence/S04-native-runtime.md) records results. A same-Mac relocation is not second-machine acceptance.

Output roots must be real, private directories. Descriptor-relative access rejects symlink components/files and detects root replacement. Bundles publish after integrity checks. macOS sandbox-exec denies renderer/descendant networking. CPU/file limits and a wall timeout apply; RSS and scratch size use a sampled watchdog, not kernel memory/disk quotas, CPU-core limits or a container sandbox. These limits still require production acceptance under NFR-009. Outputs remain until user removal. The renderer executes only project-controlled code.

Actual ChatGPT Work mode/UI export, cross-machine SVG font appearance, another physical machine and fresh independent review of alpha.2 remain open. [The earlier live desktop test](../../doc/project-management/evidence/S04-work-host-check.md) established alpha.1 in Codex Desktop, not a different Work mode. [Handoff](../../doc/project-management/HANDOFF.md) contains the next steps. No account plugin, public release or cloud host was created.
