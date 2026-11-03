# Cloud Architecture Diagrams for ChatGPT Work

This plugin turns an architecture request into a versioned JSON model, checks it against provider catalogs and placement rules, and draws one view at a time to SVG and PNG with a controlled local Graphviz renderer. It covers AWS, Azure, GCP, Huawei Cloud, on-premises and detailed Kubernetes, in English and Thai.

It is for private personal use only: it includes Huawei Cloud icons whose rights are not cleared, so do not publish it, share it in a workspace, submit it to a directory or make its repository public. The installed `Cloud Architecture Diagrams (S04)` pilot is a separate plugin and stays as it is.

## Where it runs

| Host | Status |
|---|---|
| ChatGPT desktop app, Work mode, on macOS with Apple silicon | The selected mode. See the [S09 evidence](../../doc/project-management/evidence/S09-work-plugin.md) for what has been checked there |
| ChatGPT on the web or on mobile, and threads that run in the cloud | Not supported: they cannot reach a process on this Mac |
| Intel Macs, Windows and Linux | Not verified. Rendering refuses to run without the macOS sandbox |
| Codex in the ChatGPT desktop app | Not verified as a user experience. It shares the engine with Work, and Work stays the acceptance target |

## Requirements

Each Mac needs its own setup, and nothing syncs between machines.

- `python3`, version 3.9 or later, which starts the plugin's tool process. Apple's Command Line Tools provide one.
- [uv](https://docs.astral.sh/uv/) and [Graphviz](https://graphviz.org/download/). Tested with uv 0.13.0 and Graphviz 16.1.0.
- macOS `sandbox-exec`, which ships with macOS.
- Network access for the first setup only. Setup builds a private Python 3.13.7 environment from the hash-locked `uv.lock`, including the pinned `diagrams` package and its icons, about 60 MB on disk. Rendering itself downloads nothing and has no network access, so it works offline once setup has finished.

```bash
brew install uv graphviz
```

Docker, a central server, an account connection and a model API key are not required.

## Install

The host leaves symbolic links out of what it installs, so install the built package and never `plugins/cloud-architecture-work` itself. From a checkout of the repository, build it into a folder that will stay in place, because the host keeps pointing at it:

```bash
python3 scripts/build_work_plugin.py --output ~/.local/share/cloud-architecture-diagrams/work-release
```

The command prints the version, which has the form `0.1.0-alpha.1+<content digest>`, so every different package has a different version. It also writes a versioned ZIP with its SHA-256 beside the folder, for moving to another machine. Unzip that into a folder that will stay, and use its root in place of `marketplace` below.

The `codex` command is inside the ChatGPT app:

```bash
export PATH="/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS:$PATH"
```

```bash
codex plugin marketplace add ~/.local/share/cloud-architecture-diagrams/work-release/marketplace
```

```bash
codex plugin add cloud-architecture-work@mingrammer-work
```

Restart the ChatGPT app. In Work mode, open a new chat and select **Cloud Architecture Diagrams**. The first request asks the plugin to build its private runtime, and the app may ask you to approve that, because it reaches the network. It took under 5 seconds on the tested Mac, which already had Python 3.13.7, and it takes longer when uv has to download Python. The first use on a Mac can also bring up the system's request to let ChatGPT use your Documents folder, and rendering needs it. To build the runtime from a terminal instead, run this inside the installed copy:

```bash
python3 ~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/*/scripts/runtime.py setup
```

## Use

Ask for an architecture in English or Thai, or for a change to an earlier one. The bundled skill looks up exact types, writes the model, validates it, draws what you asked for, and links every file.

| Tool | Purpose |
|---|---|
| `get_capabilities` | Versions, runtime state, what blocks rendering and how to fix it, limits, supported modes |
| `setup_runtime` | Build or repair the private runtime, behind the call |
| `get_schema` | The versioned JSON Schema, about 22 KB |
| `search_catalog` | Bounded search for provider and Kubernetes types |
| `validate_model` | Validate a model without drawing it |
| `render_model` | Validate, then draw one view into a new bundle, from a model or an earlier bundle's model |
| `read_artifact` | Read one file of a bundle |
| `list_bundles` | Recent bundles, newest first |

Every result starts with JSON text. `status` is `ok`, `validation_failed`, `runtime_failure`, `timeout`, `artifact_unavailable`, `runtime_unavailable`, `invalid_arguments` or `busy`, and anything but `ok` also has a stable `code`, a `message` and a `remedy`.

Each bundle holds `diagram.svg`, `diagram.png`, `model.json`, `view.json`, `diagnostics.json` and `manifest.json`. The SVG embeds its icons, and the manifest records versions, checksums and the terms of every icon pack shown. A bundle that shows Huawei icons states that it is for private personal use only. A file larger than 8 MiB cannot come back through the tool, because the host's transport hangs on results far smaller than the 16 MiB a file may reach, so that file stays available by its path.

## Where your data goes

Bundles live in `~/Documents/CloudArchitectureDiagrams/work`, private to your account. If you sync Documents with iCloud, they sync too. The runtime lives in `~/.local/share/cloud-architecture-diagrams/work-plugin`. The plugin's log holds tool names, status codes and timings, and never model content. Its tool process and its renderer send nothing anywhere.

Tool calls and their results, including the model and local file paths, are part of the chat, like anything else sent to the model you selected in Work. The app also keeps its own record of each chat, including those calls, under `~/.codex/sessions`. So do not put secret values in a model; the model format has no field for them.

Bundles stay until you remove them. Nothing deletes them automatically, and no tool can delete them. To see what is older than 30 days, and then delete it:

```bash
python3 ~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/*/scripts/runtime.py prune --older-than-days 30
```

```bash
python3 ~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/*/scripts/runtime.py prune --older-than-days 30 --apply
```

## Upgrade

Build the new version over the same folder and add the plugin again, which replaces the installed copy:

```bash
python3 scripts/build_work_plugin.py --output ~/.local/share/cloud-architecture-diagrams/work-release
```

```bash
codex plugin add cloud-architecture-work@mingrammer-work
```

Restart the app and open a new chat. A chat left open keeps its old tool process, and the plugin reports `PLUGIN_UPDATED` when that process's files are gone. A version with the same dependencies reuses the runtime, and one with new dependencies asks to build it again.

## Remove

The runtime lives outside the host's plugin data, so remove it first, while the script is still installed. Bundles and the Claude Code plugin's separate runtime stay.

```bash
python3 ~/.codex/plugins/cache/mingrammer-work/cloud-architecture-work/*/scripts/runtime.py remove
```

```bash
codex plugin remove cloud-architecture-work@mingrammer-work
```

```bash
codex plugin marketplace remove mingrammer-work
```

```bash
rm -rf ~/.local/share/cloud-architecture-diagrams/work-release
```

## How the package is built

`pyproject.toml`, `uv.lock`, `src`, the model guide and the examples are symbolic links in this folder, so there is one copy of the core and of the guide. `scripts/build_work_plugin.py` reads through them and writes real files, because the host drops links without saying so. Anything under `src` ships, so the `catalog-license` lane fails on any visual asset there that the rights manifest does not list. Everything else in the repository, including research records and uncleared source packs, stays out, and the `package-contract` lane holds the package to an allowlist. The tool process uses only the Python standard library, so it can answer and report what is missing before the runtime exists.
