"""Verified icon and font bytes. Only catalog data names them, and input can never reach a path."""

import hashlib
import importlib
import json
import os
import re
import struct
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
UNICODE_SUBTABLES = {(0, 3), (0, 4), (3, 1), (3, 10)}


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


def _segment_map(data: bytes, start: int) -> set[int]:
    """A cmap format 4 subtable: each segment maps by a delta, or through an array of glyphs."""
    count = struct.unpack_from(">H", data, start + 6)[0] // 2
    offsets_at = start + 16 + 6 * count
    columns = (start + 14, start + 16 + 2 * count, start + 16 + 4 * count, offsets_at)
    rows = zip(*(struct.unpack_from(f">{count}H", data, at) for at in columns), strict=True)
    found: set[int] = set()
    for index, (last, first, delta, offset) in enumerate(rows):
        for point in range(first, last + 1):
            glyph = point
            if offset:
                at = offsets_at + 2 * index + offset + 2 * (point - first)
                glyph = struct.unpack_from(">H", data, at)[0]
                if not glyph:
                    continue
            # Glyph 0 is the font's empty box, so a character mapped to it counts as absent.
            if (glyph + delta) & 0xFFFF:
                found.add(point)
    return found


def _group_map(data: bytes, start: int) -> set[int]:
    """A cmap format 12 subtable: runs of characters mapped to runs of glyphs."""
    found: set[int] = set()
    for index in range(struct.unpack_from(">I", data, start + 12)[0]):
        first, last, glyph = struct.unpack_from(">3I", data, start + 16 + 12 * index)
        found.update(range(first + (glyph == 0), last + 1))
    return found


def font_characters(data: bytes) -> set[int]:
    """What a font really holds, read from its own table rather than from a copied list."""
    tables = (
        struct.unpack_from(">4sIII", data, 12 + 16 * index)
        for index in range(struct.unpack_from(">H", data, 4)[0])
    )
    cmap = next(offset for tag, _, offset, _ in tables if tag == b"cmap")
    readers = {4: _segment_map, 12: _group_map}
    found: set[int] = set()
    for index in range(struct.unpack_from(">H", data, cmap + 2)[0]):
        platform, encoding, offset = struct.unpack_from(">HHI", data, cmap + 4 + 8 * index)
        if (platform, encoding) in UNICODE_SUBTABLES:
            start = cmap + offset
            found |= readers[struct.unpack_from(">H", data, start)[0]](data, start)
    return found


def drawable_characters(limits: Limits) -> set[int]:
    found: set[int] = set()
    for _, data in verified_fonts(limits):
        found |= font_characters(data)
    return found
