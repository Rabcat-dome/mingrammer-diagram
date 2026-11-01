# S04 Local Runtime and Plugin Proof

Date: 2026-11-01 (Asia/Bangkok) | Tasks: M0-02, M0-05 | Status: local feasibility/install checks; actual Work proof and independent review pending.

The owner first selected central execution (D-012), then replaced it with **runtime installation on every machine using the plugin** (D-013). D-013 is current. Requirements revision 0.7 reflects this choice; O-006 hosting inputs are retired. No cloud server, public endpoint or account plugin was created. A free public rendering MCP is not a project dependency; this record does not claim an exhaustive survey of public services.

## Selected route

Installable local plugin -> bundled workflow skill and stdio MCP -> locally installed Docker renderer -> local artifact bundle. Each machine performs runtime setup. This retains the plugin deliverable; a standalone skill is insufficient. Work Desktop/local execution is the first host to prove. Cloud-only execution and mobile support are not assumed.

The [desktop-only plugin guide](https://developers.openai.com/plugins/deploy/desktop-only) documents local MCP and locally running threads. The [plugin packaging guide](https://developers.openai.com/plugins/build/plugins) describes portable manifests and local marketplaces. These support the chosen direction; CLI/SDK success does not establish actual Work chat behavior.

## Reproduction and current evidence

Current source/install instructions: [local plugin pilot](../../../spikes/s04-local-plugin/README.md). Historical loopback HTTP source: [runtime experiment](../../../spikes/s04-runtime/README.md). Published historical metadata: [runtime proof](S04-runtime-proof.json). Current local-install evidence: [local plugin proof](S04-local-plugin-proof.json).

The pilot is version `0.1.0-alpha.1`, installed as `cloud-architecture-diagrams@mingrammer-local` using the supported Codex CLI. Its self-contained generated ZIP includes the real server, installer/launcher, locked runtime inputs and useful workflow skill. No cache file was edited directly. Runtime setup builds a local image and stores its immutable ID/source fingerprint; launch checks both and starts without installing dependencies. No model key or renderer token is required.

The SDK integration harness exercises the installed cache and a relocated ZIP on this Mac. It checks three-tool discovery, runtime preflight, English/Thai three-node rendering, five artifact reads, inline PNG equality/checksums, invalid labels/unknown inner request fields/traversal, isolation configuration and cleanup after disconnect. The JSON records actual checks, source hashes and limitations; this is not an actual Work invocation or second-machine test.

## Runtime candidate

| Component | Tested candidate |
|---|---|
| Host | macOS ARM64, Apple M2 Max; host Python 3.13.7 and Docker Engine 29.9.2 |
| Container | Python 3.13.13 / Alpine 3.22.4; multi-platform base digest pinned in Dockerfile |
| Rendering | diagrams 0.25.1; Python Graphviz binding 0.20.3; native Graphviz 12.2.1; Fontconfig 2.15.0 |
| MCP | Python SDK 2.3.0 with hashed dependency lock |
| Fonts | Noto Sans Regular 2.015 and Noto Sans Thai Regular 2.002; package 2025.05.01-r0 |
| Font provenance | Actual name-table metadata/file hashes identify Noto authors and SIL OFL 1.1; release notices still require packaging verification |
| Local controls | Network none; non-root desktop UID/GID; read-only root; one scoped output bind; one CPU; 1 GiB/no swap; 64 PIDs; 256 MiB tmpfs; dropped capabilities/no-new-privileges |

The host still has no native `dot`; runtime dependencies are in local images. Setup downloads dependencies; rendering has no outbound network. No provider/Huawei artwork is used. Transitive Alpine packages are inventoried, not all frozen to immutable repositories. Images are local, not pushed to a registry. See [diagrams installation](https://diagrams.mingrammer.com/docs/getting-started/installation), [Docker controls](https://docs.docker.com/engine/containers/resource_constraints/) and [Noto Thai OFL](https://github.com/notofonts/thai/blob/main/OFL.txt) for primary references.

## Historical HTTP experiment

Before D-013, local authenticated Streamable HTTP discovery/render/download, ten negative cases and native worker controls passed. The bearer token was generated in memory and not persisted. The temporary server was bound to host loopback and removed. Its HTTP renderer child shared a bridge namespace; only the CLI workers used network none. That development server is not the selected product transport, production authentication or a deployment candidate now.

Three fresh worker containers per synthetic chain size produced these medians, timed inside rendering after imports:

| Nodes / edges | Median render/validation seconds |
|---|---|
| 3 / 2 | 0.0965 |
| 30 / 29 | 0.1477 |
| 100 / 99 | 0.3771 |
| 200 / 199 | 0.4444 |

Docker/image/Python startup, imports and transport time are excluded. The historical amd64 image was smoke-tested under emulation on this ARM64 Mac; it proves neither native x86 performance nor a second machine. No p95/SLA, 300-edge capacity or realistic Kubernetes/readability claim follows from these plain chains. Authoritative trials/package inventories are in the historical JSON.

## Gaps and next proof

The current tool accepts exactly three labels of 1-256 Unicode code points. Its worker enforces a 1 MiB input ceiling, 16 MiB file limit, 32-million-pixel PNG post-check and CPU limits; the server applies a 55-second child timeout/process-group kill. The product's proposed 200-node/300-edge, 60-second/1-GiB limits remain provisional (O-007). MCP envelope limits, timeout/OOM and cancellation stress paths are not proven.

SVG references fonts without embedding/outlining them; cross-machine appearance remains open. The [local PNG](S04-local-plugin-fixture.png) was visually checked for English/Thai labels, with a matching [SVG](S04-local-plugin-fixture.svg); this is not provider-style or owner acceptance. Local files persist until user removal. Full semantics, detailed Kubernetes/catalogs, asset rights, strict final product contracts, polished installation/upgrades/removal and the real M1 quality gate remain later work.

Next: verify the installed plugin in an actual locally executing Work Desktop chat, including discovery, tool call, preview and complete export; record the host/version. Review the final source and local installation/isolation decision in a separate Astra/High pass. Finalize host modes/limits, then close applicable M0 tasks and continue S05/M1. Second-machine full workflow remains M6 acceptance. No further cloud provider/project/region/budget answer is needed.
