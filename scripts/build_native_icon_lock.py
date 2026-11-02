"""Record the exact icon file behind each native class the catalog allows, from the pinned wheel."""

import hashlib
import importlib
import json
from importlib import metadata
from pathlib import Path

from cloud_architecture_diagrams.catalog import DATA, catalog


def locate(class_path: str) -> Path:
    module_name, class_name = class_path.rsplit(".", 1)
    node = getattr(importlib.import_module(module_name), class_name)
    module = importlib.import_module("diagrams")
    assert module.__file__
    return Path(module.__file__).resolve().parents[1] / str(node._icon_dir) / str(node._icon)


def lock() -> dict[str, object]:
    classes = {
        record.representation.class_path: record.representation.pack
        for record in catalog().records.values()
        if record.representation.kind == "native_class"
    }
    classes[catalog().fallback.class_path] = catalog().fallback.pack
    icons = {}
    for class_path, pack in sorted(item for item in classes.items() if item[0]):
        assert class_path
        path = locate(class_path)
        icons[class_path] = {
            "pack": pack,
            "resource": str(path.relative_to(path.parents[path.parts[::-1].index("resources")])),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return {
        "catalog_version": catalog().version,
        "package": "diagrams",
        "package_version": metadata.version("diagrams"),
        "icons": icons,
    }


if __name__ == "__main__":
    (DATA / "native_icons.json").write_text(json.dumps(lock(), indent=2) + "\n")
