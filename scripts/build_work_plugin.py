"""Build the installable Work plugin: real files only, because the host drops symbolic links."""

# The README runs this with `python3`, which on a new Mac is Apple's 3.9.
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "plugins/cloud-architecture-work"
PLUGIN = "cloud-architecture-work"
MARKETPLACE = "mingrammer-work"
IGNORED = {"__pycache__", ".DS_Store", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
MARKER = "build.json"
STRICT_SEMVER = re.compile(r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?")
# A fixed time, so that the same content always gives the same archive.
ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def collect() -> dict[str, bytes]:
    """Every packaged file by its path, reading through the links into the one copy of the core."""
    files: dict[str, bytes] = {}
    for folder, directories, names in os.walk(SOURCE, followlinks=True):
        directories[:] = sorted(item for item in directories if item not in IGNORED)
        for name in sorted(names):
            if name not in IGNORED and not name.endswith(".pyc"):
                path = Path(folder) / name
                files[path.relative_to(SOURCE).as_posix()] = path.read_bytes()
    # Not a link like the others: a pyproject.toml in that folder would make Ruff treat it as its own
    # project, and the lint lane would then skip the adapter while still passing.
    files["pyproject.toml"] = (ROOT / "pyproject.toml").read_bytes()
    return files


def content_digest(files: dict[str, bytes]) -> str:
    listing = [[name, hashlib.sha256(files[name]).hexdigest()] for name in sorted(files)]
    return hashlib.sha256(json.dumps(listing).encode()).hexdigest()


def marketplace_entry() -> dict[str, Any]:
    return {
        "name": MARKETPLACE,
        "interface": {"displayName": "Cloud Architecture Diagrams"},
        "plugins": [
            {
                "name": PLUGIN,
                "source": {"source": "local", "path": f"./plugins/{PLUGIN}"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            }
        ],
    }


def write_tree(root: Path, files: dict[str, bytes]) -> None:
    for name, data in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def write_archive(path: Path, tree: Path) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(p for p in tree.rglob("*") if p.is_file()):
            info = zipfile.ZipInfo(
                f"{PLUGIN}-marketplace/{item.relative_to(tree).as_posix()}", ZIP_TIME
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, item.read_bytes())


def source_commit() -> tuple[str | None, bool]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    except (OSError, subprocess.SubprocessError):
        return None, True
    return commit, dirty


def build(output: Path) -> dict[str, Any]:
    if output.exists() and any(output.iterdir()) and not (output / MARKER).is_file():
        raise SystemExit(
            f"Refusing to replace {output}: it is not an earlier build of this plugin."
        )
    files = collect()
    manifest = json.loads(files["plugin.json"])
    base = manifest["version"]
    if not STRICT_SEMVER.fullmatch(base) or manifest["name"] != PLUGIN:
        raise SystemExit("plugin.json needs this plugin's name and a strict semantic version.")
    content = content_digest(files)
    # The host caches by version and an old chat keeps its old process, so a change in content has to
    # change the version, and the version has to identify the content.
    manifest["version"] = version = f"{base}+{content[:12]}"
    files["plugin.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()

    stage = output.with_name(f"{output.name}.building-{os.getpid()}")
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    try:
        tree = stage / "marketplace"
        write_tree(tree / "plugins" / PLUGIN, files)
        catalog = tree / ".agents/plugins/marketplace.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps(marketplace_entry(), indent=2) + "\n")
        if any(path.is_symlink() for path in tree.rglob("*")):
            raise SystemExit("A symbolic link reached the package, and the host would drop it.")
        archive = stage / f"{PLUGIN}-{version}.zip"
        write_archive(archive, tree)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (stage / f"{archive.name}.sha256").write_text(f"{digest}  {archive.name}\n")
        pyproject = files["pyproject.toml"].decode()
        core = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
        commit, dirty = source_commit()
        report = {
            "plugin": PLUGIN,
            "marketplace": MARKETPLACE,
            "version": version,
            "base_version": base,
            "content_sha256": content,
            "core_version": core.group(1) if core else None,
            "lock_sha256": hashlib.sha256(files["uv.lock"]).hexdigest(),
            "archive": archive.name,
            "archive_sha256": digest,
            "files": len(files),
            "source_commit": commit,
            "source_dirty": dirty,
        }
        (stage / MARKER).write_text(json.dumps(report, indent=2) + "\n")
        shutil.rmtree(output, ignore_errors=True)
        output.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {**report, "marketplace_root": str(output / "marketplace")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/work-plugin")
    args = parser.parse_args()
    print(json.dumps(build(args.output.absolute()), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
