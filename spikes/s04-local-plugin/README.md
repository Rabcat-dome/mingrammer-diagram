# S04 Local Plugin Pilot

Decision: D-013. Status: experimental runtime proof, not the complete architecture plugin.

The selected product is an installable plugin with a bundled skill and local stdio MCP tools. Each machine installs its own runtime. This pilot uses Docker to contain Python, Graphviz and English/Thai fonts; the host needs Python 3.10+ and a running Linux Docker engine. macOS ARM64 is the tested host. Other operating systems, a second physical machine and actual Work preview/export remain unverified.

## Build and install on this desktop

From the repository root, with the Codex CLI available as `codex`:

```sh
python3 spikes/s04-local-plugin/build.py
codex plugin marketplace add "$PWD" --json
codex plugin add cloud-architecture-diagrams@mingrammer-local --json
python3 spikes/s04-local-plugin/output/cloud-architecture-diagrams/scripts/setup.py
uv run --no-project --python 3.13 --with mcp==2.3.0 python spikes/s04-local-plugin/verify.py
```

On this Mac the bundled CLI is `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. Use the supported CLI installer; do not edit the cache. Rebuild/reinstall for changed source. The S04 version is `0.1.0-alpha.1`; it has not been uploaded to an account or published. The generated marketplace points at the generated package; rebuild it after cloning on another machine. Source checkout/build is a development path, not the final FR-066 release installation experience.

The builder produces a self-contained plugin directory and ZIP under ignored `output/`. The portable root manifest and `mcp.json` describe the real stdio launcher. A generated legacy overlay supports the installed CLI; both manifests identify the same plugin/version. The ZIP contains only one plugin and includes runtime source, hash-locked Python dependencies, setup/launch scripts, README and one useful workflow skill. The source marketplace is outside the ZIP.

Setup builds a local image and records its immutable ID and runtime-source fingerprint under `~/.local/share/cloud-architecture-diagrams/`. Initial setup downloads public dependencies; startup does not download/install anything. Changing the source/version requires setup again. Rendering needs no central server, public rendering MCP or model API key. Docker must stay running. Setup/launch reject remote or TCP Docker endpoints; the pilot requires a local Unix socket (or named pipe on an unverified Windows host).

## Tool and artifact contract

- `get_runtime_info`: actual runtime/package/font versions, non-root UID and cgroup configuration.
- `render_fixture`: `{"request":{"labels":["Client","Application","Database"]}}`; exactly three literal labels, with an inner request that rejects unknown fields. This is a fixed synthetic fixture, not the release architecture schema/catalog.
- `read_fixture_artifact`: a returned bundle ID and one of the five allowlisted filenames. Reads are confined to the plugin's output directory.

Only `~/Documents/CloudArchitectureDiagrams` is mounted from the host. Complete bundles are published there atomically with PNG/SVG, request JSON, DOT and manifest; the PNG is also returned as MCP image content. Outputs are retained until the user removes them. The container uses network `none`, read-only root, dropped capabilities, no-new-privileges, one CPU, 1 GiB memory/no swap, 64 PIDs and a 256 MiB `/tmp`. On POSIX desktops it runs under the calling non-root UID/GID so the scoped output mount remains writable. It receives no host model/API credentials.

The SDK harness starts the actual installed cache, verifies discovery/render/read and byte checksums, inspects container controls and negative requests, then repeats from a ZIP extracted to a different path containing spaces. It verifies no pilot containers remain after client disconnect. Relocation on the same Mac is not second-machine acceptance.

## Actual Work verification still required

The local plugin was installed through this desktop's CLI. This active chat may require a fresh local-execution chat to discover newly installed components. No new chat was created automatically. In a locally executing Work Desktop chat, enable/mention **Cloud Architecture Diagrams (S04)** and request:

```text
Use the Cloud Architecture Diagrams S04 plugin. Call get_runtime_info,
then render_fixture with three labels: Client, Application, Database.
Inspect the output, display its PNG, and attach the SVG, PNG, source JSON,
DOT and manifest. Report tool or file-access failures exactly.
```

Record the actual host mode, tool invocation, visible preview and retrieved files under M0-02. Use a separate Astra/High review against the final commit before closing M0. See the [S04 evidence](../../doc/project-management/evidence/S04-runtime-and-hosting.md) and [handoff](../../doc/project-management/HANDOFF.md).

## Remaining product work

Provider catalogs/icons and rights, canonical architecture JSON, detailed Kubernetes, full validation, polished per-machine install/preflight/upgrade/removal, automated product gates and two-machine Work acceptance remain M1-M6 work. SVG references font families without embedded fonts; cross-machine SVG appearance is not proven. MCP envelope-size limits, timeout/OOM stress, cancellation under rendering, symlink-race hardening and complete dependency/license notices remain release work. Direct base/OS packages and Python hashes are pinned; transitive Alpine repositories are still mutable and actual image provenance is recorded. Do not call this pilot release-ready.
