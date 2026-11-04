"""NFR-004: write the inventory of Python packages the core installs, from `uv.lock` and their metadata.

The packages are not vendored: setup installs them from the hash-locked file. A package whose license
cannot be read stops the build, because unknown rights block packaging.
"""

import importlib.metadata as metadata
import sys
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "src/cloud_architecture_diagrams/assets/THIRD-PARTY-PYTHON.md"
PROJECT = "cloud-architecture-diagrams"
HEADER = """# Third-party Python packages

This inventory covers NFR-004 for the Python packages the core installs at runtime. `uv.lock` pins each one by hash, and setup installs it from there, so none is copied into this package. Each package's own license file arrives with it. `scripts/build_third_party.py` writes this file, and the `catalog-license` lane fails if it differs from the lock.

The list follows the lock for this platform. Many rows, such as `pre-commit` and `virtualenv`, are here only because `diagrams` declares `pre-commit` as a runtime dependency, and the core does not use them.

Graphviz is a separate program that each machine installs, under the Eclipse Public License 1.0. It is not bundled either.

Icons delivered by `diagrams` and the assets bundled here are in [NOTICE.md](NOTICE.md).

| Package | Version | License |
|---|---|---|
"""


def runtime_packages(lock: dict[str, Any]) -> dict[str, str]:
    """The project's runtime closure, without its development group."""
    packages = {item["name"]: item for item in lock["package"]}
    versions: dict[str, str] = {}
    pending = [item["name"] for item in packages[PROJECT]["dependencies"]]
    while pending:
        name = pending.pop()
        if name in versions:
            continue
        versions[name] = packages[name]["version"]
        pending += [item["name"] for item in packages[name].get("dependencies", [])]
    return versions


def license_of(name: str) -> str:
    data = metadata.metadata(name)
    if expression := data.get("License-Expression"):
        return expression
    classifiers = [
        item.split(" :: ")[-1]
        for item in data.get_all("Classifier") or []
        if item.startswith("License :: ")
    ]
    if classifiers:
        return ", ".join(sorted(classifiers))
    if (text := data.get("License")) and "\n" not in text and len(text) < 80:
        return text
    raise SystemExit(f"{name}: no readable license in its metadata")


def main() -> int:
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    rows = []
    for name, version in sorted(runtime_packages(lock).items()):
        if metadata.version(name) != version:
            raise SystemExit(f"{name}: installed {metadata.version(name)}, locked {version}")
        rows.append(f"| {name} | {version} | {license_of(name)} |\n")
    INVENTORY.write_text(HEADER + "".join(rows))
    print(f"{len(rows)} packages written to {INVENTORY.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
