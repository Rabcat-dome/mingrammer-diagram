# Cloud Architecture Diagrams for Claude Code

Version: `0.2.0-alpha.1`. This is a preparation build. It reuses the project's core contract to author and validate canonical architecture models. **It cannot render SVG or PNG diagrams yet**, and provider catalogs and placement rules are not implemented. The installed ChatGPT Work pilot is a separate plugin.

## Requirements

macOS ARM64 is the tested host. Other systems are unverified.

- [uv](https://docs.astral.sh/uv/) on `PATH`, for example `brew install uv`. Tested with 0.13.0.
- Network access on first use only. The `cloud-diagrams` command creates a private Python 3.13.7 environment from the hash-locked `uv.lock` under `~/.local/share/cloud-architecture-diagrams/claude-plugin` (or `$XDG_DATA_HOME`).

Docker, a central server and a model API key are not required.

## Install

These commands need the `claude` CLI on `PATH`; the CLI bundled with the desktop app is not on it by default.

The repository is private. Installing from GitHub uses your own Git credentials, for example after `gh auth login` and `gh auth setup-git`. The default branch does not contain the plugin yet, so name its branch until it merges:

```bash
claude plugin marketplace add 'Rabcat-dome/mingrammer-diagram#codex/m7-claude-plugin'
```

```bash
claude plugin install cloud-architecture-diagrams@mingrammer-local
```

To try a checkout for one session without installing:

```bash
claude --plugin-dir plugins/cloud-architecture-diagrams
```

## Use

Ask for an architecture model in English or Thai, or invoke `/cloud-architecture-diagrams:architecture-model`. The skill writes a model file and validates it. A request to draw a picture can go to another installed diagram plugin instead, because this one cannot render yet.

The skill runs `bin/cloud-diagrams` from the plugin root by its full path:

| Subcommand | Purpose |
|---|---|
| `capabilities` | Implemented capabilities, pending layers and limits |
| `schema` | Versioned JSON Schema |
| `validate [--mode strict\|lenient] [--view ID] < model.json` | Validate a model from stdin |

Exit codes: `0` success, `2` invalid model with JSON diagnostics on stdout, `3` the runtime could not be prepared.

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

`pyproject.toml`, `uv.lock`, `src` and the skill examples are symlinks into the repository, so there is one copy of the core. Claude Code replaces symlinks that stay inside the marketplace with real files at install time, so an installed plugin is self-contained. Everything else in the repository, including research records and uncleared assets, stays out of the package.
