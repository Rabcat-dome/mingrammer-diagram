# Cloud Architecture Diagrams for Claude Code

This is a preparation build, versioned by Git commit so that installed copies can pick up every change. It reuses the project's core contract and catalogs to author and validate canonical architecture models, including provider placement and Kubernetes rules, and it renders a validated view to SVG and PNG through a controlled Graphviz renderer. It is for private personal use only: it includes Huawei Cloud icons whose rights are not cleared, so do not publish it or make its repository public. The installed ChatGPT Work pilot is a separate plugin.

## Requirements

macOS ARM64 is the tested host. Other systems are unverified.

- [uv](https://docs.astral.sh/uv/) on `PATH`, for example `brew install uv`. Tested with 0.13.0.
- [Graphviz](https://graphviz.org/download/) for rendering, for example `brew install graphviz`. Tested with 16.1.0. Validation and discovery work without it.
- macOS `sandbox-exec` for rendering. Without it `render` refuses to run, because it would otherwise lose its network and file isolation.
- Network access on first use only. The `cloud-diagrams` command creates a private Python 3.13.7 environment from the hash-locked `uv.lock` under `~/.local/share/cloud-architecture-diagrams/claude-plugin` (or `$XDG_DATA_HOME`). It includes the pinned `diagrams` package and its icons, about 40 MB. Rendering itself downloads nothing.

Docker, a central server and a model API key are not required.

## Install

These commands need the `claude` CLI on `PATH`; the CLI bundled with the desktop app is not on it by default.

The repository is private. Installing from GitHub uses your own Git credentials, for example after `gh auth login` and `gh auth setup-git`.

```bash
claude plugin marketplace add Rabcat-dome/mingrammer-diagram
```

```bash
claude plugin install cloud-architecture-diagrams@mingrammer-local
```

To try a checkout for one session without installing:

```bash
claude --plugin-dir plugins/cloud-architecture-diagrams
```

## Use

Ask for an architecture model in English or Thai, or invoke `/cloud-architecture-diagrams:architecture-model`. The skill writes a model file, validates it and, when you ask for a picture, renders it.

The skill runs `bin/cloud-diagrams` from the plugin root by its full path:

| Subcommand | Purpose |
|---|---|
| `capabilities` | Implemented capabilities, pending layers, limits and release blockers |
| `schema` | Versioned JSON Schema |
| `catalog [--provider P] [--query TEXT] [--type ID] [--entity E] [--taxonomy T] [--kubernetes] [--limit N]` | Search provider and Kubernetes types; results are bounded |
| `validate [--mode strict\|lenient] [--view ID] < model.json` | Validate a model from stdin |
| `render --output DIR [--mode strict\|lenient] [--view ID] < model.json` | Validate, then draw one view into a new bundle under `DIR` |

Exit codes: `0` success, `2` invalid model or a view that cannot be drawn as asked, with JSON diagnostics on stdout, `3` the runtime could not be prepared or failed unexpectedly, `4` a render failed and published nothing, with JSON diagnostics on stdout, `64` the command was used incorrectly.

Each bundle holds `diagram.svg`, `diagram.png`, `model.json`, `view.json`, `diagnostics.json` and `manifest.json`. The SVG embeds its icons, and the manifest records versions, checksums and the terms of every icon pack shown. A bundle that shows Huawei icons states that it is for private personal use only.

## Update

Marketplaces from other sources do not update automatically by default:

```bash
claude plugin marketplace update mingrammer-local
```

```bash
claude plugin update cloud-architecture-diagrams@mingrammer-local
```

## Remove

Uninstalling the plugin does not remove the private environment, which lives outside Claude Code's plugin data because that location is not available to Bash tool commands.

```bash
claude plugin uninstall cloud-architecture-diagrams@mingrammer-local
```

```bash
claude plugin marketplace remove mingrammer-local
```

```bash
rm -rf ~/.local/share/cloud-architecture-diagrams/claude-plugin
```

## How the package is built

`pyproject.toml`, `uv.lock`, `src` and the skill examples are symlinks into the repository, so there is one copy of the core. Claude Code replaces symlinks that stay inside the marketplace with real files at install time, so an installed plugin is self-contained. Anything under `src` ships, so the `catalog-license` lane fails on any visual asset there that the rights manifest does not list. `src/cloud_architecture_diagrams/assets/NOTICE.md` holds the attribution for the bundled on-premises symbols. Everything else in the repository, including research records and uncleared assets, stays out of the package.
