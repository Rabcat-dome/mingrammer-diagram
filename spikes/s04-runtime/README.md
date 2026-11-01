# S04 Runtime Spike

Historical HTTP research: central hosting was superseded by D-013. Use the [local plugin pilot](../s04-local-plugin/README.md) for the current route.

This is a synthetic feasibility spike for the [S04 investigation](../../doc/project-management/evidence/S04-runtime-and-hosting.md). It is separate from the future core schema, provider catalogs, renderer and release plugin. The selected product target is Work Cloud/Web with a central remote MCP service (D-012).

## Reproduce locally

Requires Python 3 on the developer host and a running Linux Docker engine. No host Graphviz or font installation is needed.

```sh
docker build --tag mingrammer-s04:local spikes/s04-runtime
python3 spikes/s04-runtime/verify.py
```

The harness uses the built immutable local image ID, starts bounded worker containers, tests a temporary authenticated HTTP server bound to `127.0.0.1`, downloads/checks artifacts and removes its test containers. It generates a development token in memory; it does not persist credentials. Outputs go to ignored `output/`. Published evidence is a separate reviewed snapshot under `doc/project-management/evidence/`.

For the historical amd64 portability smoke:

```sh
docker buildx build --platform linux/amd64 --load --tag mingrammer-s04:amd64 spikes/s04-runtime
```

The committed evidence includes an amd64 smoke test under emulation on this ARM64 Mac. It is not a Cloud Run execution or a native x86 performance benchmark. The full verification harness uses the native `:local` image.

## Contents and bounds

- `Dockerfile`: base image digest, pinned direct Alpine packages, non-root runtime and hash-locked Python dependencies.
- `render_fixture.py`: fixed synthetic chain sizes 3/30/100/200; only label data is accepted, with no arbitrary Python, paths, URLs or Graphviz attributes. Uses plain nodes with no external icon assets.
- `server.py`: SDK Streamable HTTP tools `runtime_info_tool` and `render_fixture`; the latter accepts exactly three literal labels and returns a PNG plus protected local artifact URLs.
- `verify.py`: actual container/MCP/download and negative checks, resource-configuration inspection, and three fresh-worker render measurements per size.

Worker runs use network `none`, 1 CPU, 1 GiB memory with no swap, 64 PIDs, read-only root, dropped capabilities and a 256 MiB `/tmp` tmpfs. The HTTP test needs a bridge network for its local transport; its renderer child shares that namespace. Network isolation observed in the CLI worker must not be claimed for the HTTP child. Production process isolation is still design work.

The worker limits input to 1 MiB, labels to 256 Unicode code points, individual files to 16 MiB and PNG area to 32 million pixels. The server imposes a 55-second worker wall timeout, kills the worker process group on timeout, and allows one render at a time. The benchmark does not exercise timeout/OOM behavior or prove production limits for arbitrary architectures. SVG font families are declared but fonts are not embedded; browser font portability remains unproved. PNG text was visually checked.

## Deployment boundary

This server deliberately uses a development shared bearer token and a temporary artifact directory. It is not the production authentication or storage design. Do not expose it as the release service. `S04_TOKEN` and `S04_ARTIFACT_ORIGIN` are supplied only by the local harness.

D-013 supersedes this central-service experiment. The selected route is the [local stdio plugin](../s04-local-plugin/README.md), with per-machine setup; no hosting project/region, remote OAuth or cloud deployment is needed. Actual Work local invocation/preview/export remain to be verified. No public endpoint, cloud resource or account plugin was created by this spike. There is no mandatory model API call or model API key.

The base digest and Python hashes are frozen. Alpine transitive packages still resolve from their branch repositories; the evidence records the actual installed inventory. The Dockerfile alone is not a promise of byte-identical future builds. Release image/dependency provenance and notices remain M1/M2 work.
