"""Verified icon and font bytes. Only catalog data names them, and input can never reach a path."""

import hashlib
import importlib
import json
import os
import re
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

from ..catalog import DATA, PACKAGE, Font, catalog
from .errors import RenderFailure
from .graph import GraphIcon, RenderGraph
from .limits import Limits
from .paths import open_directory, read_regular

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RELATIVE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")


@dataclass(frozen=True)
class VerifiedIcon:
    source: str
    reference: str
    pack: str
    data: bytes
    sha256: str
    node_class: Any = None

    @property
    def file_name(self) -> str:
        return f"{self.sha256}.png"


def _read(root: Path, relative: str, expected: str, limit: int, entity: str) -> bytes:
    """Read below a real root, with every level checked, and compare the recorded digest."""
    parts = Path(relative).parts
    if not RELATIVE.match(relative) or ".." in parts or not parts:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/assets", entity)
    directory = -1
    try:
        directory = open_directory(root.joinpath(*parts[:-1]))
        data = read_regular(directory, parts[-1], limit)
    except (OSError, ValueError, OverflowError) as error:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/assets", entity) from error
    finally:
        if directory >= 0:
            os.close(directory)
    if hashlib.sha256(data).hexdigest() != expected:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/assets", entity)
    return data


def _lock() -> dict[str, Any]:
    value: dict[str, Any] = json.loads((DATA / "native_icons.json").read_text(encoding="utf-8"))
    return value


def _native(reference: str, pack: str, limits: Limits) -> VerifiedIcon:
    """The class path comes from the catalog and must match the lock before any import."""
    lock = _lock()
    entry = lock["icons"].get(reference)
    module_name, _, class_name = reference.rpartition(".")
    if (
        entry is None
        or entry["pack"] != pack
        or not module_name.startswith("diagrams.")
        or lock["package_version"] != metadata.version("diagrams")
    ):
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/representation", reference)
    import diagrams

    try:
        node_class = getattr(importlib.import_module(module_name), class_name)
    except (ImportError, AttributeError) as error:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/representation", reference) from error
    if (
        not issubclass(node_class, diagrams.Node)
        or f"{node_class._icon_dir}/{node_class._icon}" != entry["resource"]
    ):
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/representation", reference)
    assert diagrams.__file__
    root = Path(diagrams.__file__).resolve().parents[1]
    data = _read(root, entry["resource"], entry["sha256"], limits.file_bytes, reference)
    return VerifiedIcon("native_class", reference, pack, data, entry["sha256"], node_class)


def _custom(reference: str, pack: str, limits: Limits) -> VerifiedIcon:
    asset = catalog().assets.get(reference)
    if asset is None or asset.pack != pack or not asset.derived.png.path.startswith("assets/"):
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/assets", reference)
    file = asset.derived.png
    data = _read(PACKAGE, file.path, file.sha256, limits.file_bytes, reference)
    return VerifiedIcon("custom_asset", reference, pack, data, file.sha256)


def verified_icon(icon: GraphIcon, limits: Limits) -> VerifiedIcon:
    pack = catalog().packs.get(icon.pack)
    # A blocked pack stays blocked even if a record points at it, so there is no substitute path.
    if pack is None or pack.status not in {"approved", "private_use_only"}:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/packs", icon.reference)
    build = _native if icon.source == "native_class" else _custom
    verified = build(icon.reference, icon.pack, limits)
    if not verified.data.startswith(PNG_SIGNATURE):
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/assets", icon.reference)
    return verified


def verified_icons(graph: RenderGraph, limits: Limits) -> dict[str, VerifiedIcon]:
    found: dict[str, VerifiedIcon] = {}
    for node in graph.nodes:
        if node.icon and node.icon.reference not in found:
            found[node.icon.reference] = verified_icon(node.icon, limits)
    return found


def verified_fonts(limits: Limits) -> list[tuple[Font, bytes]]:
    fonts = catalog().manifest.fonts
    if not fonts:
        raise RenderFailure("RENDER_ASSET_UNSAFE", "/catalog/fonts")
    return [
        (font, _read(PACKAGE, font.path, font.sha256, limits.file_bytes, font.family))
        for font in fonts
    ]
