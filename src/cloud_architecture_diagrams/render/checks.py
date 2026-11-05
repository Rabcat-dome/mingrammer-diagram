"""Output checks, run before anything is published (FR-040, FR-043, NFR-003, NFR-010)."""

import base64
import binascii
import hashlib
import math
import re
import struct
import xml.etree.ElementTree as ET
import zlib

from ..diagnostics import Diagnostic
from .errors import RenderFailure, diagnostic
from .graph import RenderGraph
from .icons import PNG_SIGNATURE, VerifiedIcon
from .limits import Limits

PNG_HEADER_BYTES = 13
# Bit depths by color type. A palette image is left out: the engine does not write one, and without
# a check of its palette such a file would pass here and fail in a viewer.
PNG_DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16), 4: (8, 16), 6: (8, 16)}
PNG_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}
PNG_LAST_FILTER = 4
PNG_DECODE_PIECE = 1024 * 1024

SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
XML = "http://www.w3.org/XML/1998/namespace"
HREF = f"{{{XLINK}}}href"
FONT_STACK = "Noto Sans, Noto Sans Thai, sans-serif"
DOCTYPE = re.compile(rb"<!DOCTYPE svg PUBLIC \"-//W3C//DTD SVG 1\.1//EN\"\s+\"[^\"<>]*\">")
FORBIDDEN_MARKUP = re.compile(rb"(?i)<!doctype|<!entity|<\?xml-stylesheet")
ELEMENTS = {"svg", "g", "title", "polygon", "polyline", "path", "ellipse", "text", "image"}
ATTRIBUTES = {
    "width", "height", "viewBox", "id", "class", "transform", "fill", "stroke", "points", "d",
    "x", "y", "cx", "cy", "rx", "ry", "text-anchor", "font-family", "font-size", "stroke-width",
    "stroke-dasharray", "preserveAspectRatio", f"{{{XML}}}space", HREF,
}  # fmt: skip
ACTIVE_VALUE = re.compile(r"(?i)url\s*\(|javascript:|vbscript:|data:|https?:|file:|ftp:")
ROOT_TRANSFORM = re.compile(
    r"^scale\((?P<x>[0-9.]+) (?P<y>[0-9.]+)\) rotate\(0\) translate\([-0-9. ]+\)$"
)
ICON_HREF = re.compile(r"^icons/(?P<sha>[0-9a-f]{64})\.png$")
DATA_PNG = "data:image/png;base64,"
SVG_SIZE = re.compile(r"^(?P<points>[0-9]+(?:\.[0-9]+)?)pt$")
PIXELS_PER_POINT = 96 / 72
UNDRAWABLE_SHOWN = 8


def undrawable_text(graph: RenderGraph, characters: set[int]) -> list[Diagnostic]:
    """Graphviz draws an absent character as an empty box and reports nothing, so ask first."""
    drawn: list[tuple[str, str | None, tuple[str, ...]]] = [
        ("/title", None, graph.title_lines),
        ("/notices", None, graph.notice_lines),
        *(("/labels", group.id, group.lines) for group in graph.groups),
        *(("/labels", node.id, node.lines) for node in graph.nodes),
        *(("/labels", edge.id, edge.lines) for edge in graph.edges),
    ]
    found = []
    for field, entity, lines in drawn:
        absent = sorted({ord(character) for line in lines for character in line} - characters)
        if absent:
            # Code points name the problem without carrying the label itself (NFR-005).
            named = ", ".join(f"U+{point:04X}" for point in absent[:UNDRAWABLE_SHOWN])
            more = " and more" if len(absent) > UNDRAWABLE_SHOWN else ""
            item = diagnostic("RENDER_TEXT_UNDRAWABLE", field, entity)
            found.append(
                item.model_copy(update={"message": f"{item.message} Found {named}{more}."})
            )
    return found


def _local(tag: str) -> str:
    return tag.rpartition("}")[2]


def _strip(text: str | None) -> str:
    return "".join((text or "").split())


def _decoded(href: str) -> bytes:
    if not href.startswith(DATA_PNG):
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    try:
        return base64.b64decode(href.removeprefix(DATA_PNG), validate=True)
    except (binascii.Error, ValueError) as error:
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg") from error


def check_svg(data: bytes, allowed_icons: set[str]) -> ET.Element:
    """An allowlist over the final bytes: anything Graphviz would not emit here is rejected."""
    if FORBIDDEN_MARKUP.search(data):
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as error:
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg") from error
    if root.tag != f"{{{SVG}}}svg":
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    identifiers: set[str] = set()
    for element in root.iter():
        name = _local(element.tag)
        if not element.tag.startswith(f"{{{SVG}}}") or name not in ELEMENTS:
            raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
        for key, value in element.attrib.items():
            if key not in ATTRIBUTES:
                raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
            if key == HREF:
                if name != "image" or (
                    hashlib.sha256(_decoded(value)).hexdigest() not in allowed_icons
                ):
                    raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
            elif ACTIVE_VALUE.search(value):
                raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
            if key == "id":
                if value in identifiers:
                    raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
                identifiers.add(value)
            if key == "transform" and name != "g":
                raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    return root


def check_undistorted(root: ET.Element) -> None:
    """Icon terms such as Azure's forbid cropping, flipping, rotating and distorting (S06)."""
    for element in root.iter():
        name = _local(element.tag)
        if name == "image":
            ratio = element.get("preserveAspectRatio", "")
            if not ratio.endswith(" meet") or element.get("transform"):
                raise RenderFailure("RENDER_CONTENT_MISSING", "/svg")
        transform = element.get("transform")
        if transform is not None:
            match = ROOT_TRANSFORM.match(transform)
            if match is None or match["x"] != match["y"]:
                raise RenderFailure("RENDER_CONTENT_MISSING", "/svg")


def finalize_svg(raw: bytes, icons: dict[str, VerifiedIcon], limits: Limits) -> bytes:
    """Graphviz's external DTD is dropped, and each icon reference becomes its verified bytes."""
    stripped = DOCTYPE.sub(b"", raw, count=1)
    if FORBIDDEN_MARKUP.search(stripped):
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    try:
        root = ET.fromstring(stripped)
    except ET.ParseError as error:
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg") from error
    by_sha = {icon.sha256: icon for icon in icons.values()}
    for element in root.iter():
        name = _local(element.tag)
        if name == "image":
            match = ICON_HREF.match(element.get(HREF, ""))
            if match is None or match["sha"] not in by_sha:
                raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
            encoded = base64.b64encode(by_sha[match["sha"]].data).decode()
            element.set(HREF, DATA_PNG + encoded)
        elif name == "text":
            # Text stays text, so a viewer without Noto falls back and still reads the label.
            element.set("font-family", FONT_STACK)
    ET.register_namespace("", SVG)
    ET.register_namespace("xlink", XLINK)
    data: bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if len(data) > limits.file_bytes:
        raise RenderFailure("RENDER_ARTIFACT_LIMIT", "/svg")
    return data


def _own_text(element: ET.Element) -> str:
    return "".join(_strip(item.text) for item in element.findall(f"{{{SVG}}}text"))


def _holds(element: ET.Element, lines: tuple[str, ...]) -> bool:
    return _strip("".join(lines)) in _own_text(element)


def check_content(root: ET.Element, graph: RenderGraph, icons: dict[str, VerifiedIcon]) -> None:
    """Exit 0 from Graphviz proves little, so every selected element must really be in the image."""
    groups = {element.get("id"): element for element in root.iter(f"{{{SVG}}}g")}

    def missing(entity: str | None = None) -> RenderFailure:
        return RenderFailure("RENDER_CONTENT_MISSING", "/svg", entity)

    canvas = groups.get("graph:root")
    if canvas is None or not _holds(canvas, (*graph.title_lines, *graph.notice_lines)):
        raise missing()
    for group in graph.groups:
        element = groups.get(f"group:{group.id}")
        if element is None or not _holds(element, group.lines):
            raise missing(group.id)
    for node in graph.nodes:
        element = groups.get(f"node:{node.id}")
        if element is None or not _holds(element, node.lines):
            raise missing(node.id)
        images = element.findall(f"{{{SVG}}}image")
        if node.icon:
            expected = icons[node.icon.reference].sha256
            if (
                len(images) != 1
                or hashlib.sha256(_decoded(images[0].get(HREF, ""))).hexdigest() != expected
            ):
                raise missing(node.id)
        elif images:
            raise missing(node.id)
    for edge in graph.edges:
        element = groups.get(f"edge:{edge.id}")
        if element is None or not _holds(element, edge.lines):
            raise missing(edge.id)
    if graph.legend:
        legend = groups.get("legend")
        if legend is None:
            raise missing()


def _full_size(root: ET.Element, key: str) -> float:
    match = SVG_SIZE.match(root.get(key, ""))
    if match is None or float(match["points"]) <= 0:
        raise RenderFailure("RENDER_SVG_UNSAFE", "/svg")
    return float(match["points"]) * PIXELS_PER_POINT


def png_scale(root: ET.Element, size: tuple[int, int], limits: Limits) -> float:
    """Cairo shrinks an image past its side limit and only warns, so compare it with the SVG.

    The pixel limit applies at full size, or crossing the side limit would be a way past it.
    """
    width, height = size
    full_width, full_height = _full_size(root, "width"), _full_size(root, "height")
    if full_width * full_height > limits.pixels:
        raise RenderFailure("RENDER_PIXEL_LIMIT", "/png")
    if abs(width - full_width) <= 1 and abs(height - full_height) <= 1:
        return 1.0
    # Cairo scales by the longer side and truncates the other, so only the longer side gives it.
    scale = min(1.0, max(width, height) / max(full_width, full_height))
    if abs(width - full_width * scale) > 2 or abs(height - full_height * scale) > 2:
        raise RenderFailure("RENDER_PNG_INVALID", "/png")
    if scale < limits.minimum_png_scale:
        raise RenderFailure("RENDER_PNG_SCALE_LIMIT", "/png")
    # Rounded down, so that any real shrink reads below 1 and gets its warning.
    return math.floor(scale * 1000) / 1000


def _row_bytes(width: int, header: bytes) -> int:
    """A scanline's size with its filter byte, from a legal, non-interlaced image header."""
    if len(header) != PNG_HEADER_BYTES:
        raise RenderFailure("RENDER_PNG_INVALID", "/png")
    depth, color, compression, filtering, interlace = header[8:]
    if (
        depth not in PNG_DEPTHS.get(color, ())
        or compression != 0
        or filtering != 0
        # Neither engine route writes Adam7, so one here means the file is not what was asked for.
        or interlace != 0
    ):
        raise RenderFailure("RENDER_PNG_INVALID", "/png")
    return 1 + math.ceil(width * PNG_CHANNELS[color] * depth / 8)


def _check_pixels(stream: bytes, width: int, height: int, header: bytes) -> None:
    """Decode without keeping the output, so a stream cannot hold more memory than one piece."""
    row = _row_bytes(width, header)
    expected = row * height
    decoder = zlib.decompressobj()
    pending = stream
    seen = 0
    try:
        while not decoder.eof:
            piece = decoder.decompress(pending, PNG_DECODE_PIECE)
            pending = decoder.unconsumed_tail
            if not piece and not pending:
                break
            for at in range(-seen % row, len(piece), row):
                if piece[at] > PNG_LAST_FILTER:
                    raise RenderFailure("RENDER_PNG_INVALID", "/png")
            seen += len(piece)
            if seen > expected:
                raise RenderFailure("RENDER_PNG_INVALID", "/png")
    except zlib.error as error:
        raise RenderFailure("RENDER_PNG_INVALID", "/png") from error
    if not decoder.eof or decoder.unused_data or seen != expected:
        raise RenderFailure("RENDER_PNG_INVALID", "/png")


def check_png(data: bytes, limits: Limits) -> tuple[int, int]:
    """Walk every chunk and decode the pixels, because a valid checksum says nothing about them."""
    if len(data) > limits.file_bytes:
        raise RenderFailure("RENDER_ARTIFACT_LIMIT", "/png")
    if not data.startswith(PNG_SIGNATURE) or data[12:16] != b"IHDR":
        raise RenderFailure("RENDER_PNG_INVALID", "/png")
    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        raise RenderFailure("RENDER_PNG_INVALID", "/png")
    if width * height > limits.pixels:
        raise RenderFailure("RENDER_PIXEL_LIMIT", "/png")
    offset = len(PNG_SIGNATURE)
    header = b""
    stream: list[bytes] = []
    last = b""
    while offset + 12 <= len(data):
        length = int.from_bytes(data[offset : offset + 4])
        kind = data[offset + 4 : offset + 8]
        end = offset + 8 + length
        if end + 4 > len(data):
            raise RenderFailure("RENDER_PNG_INVALID", "/png")
        crc = int.from_bytes(data[end : end + 4])
        if zlib.crc32(data[offset + 4 : end]) != crc:
            raise RenderFailure("RENDER_PNG_INVALID", "/png")
        if kind == b"IHDR":
            if header:
                raise RenderFailure("RENDER_PNG_INVALID", "/png")
            header = data[offset + 8 : end]
        if kind == b"IDAT":
            # A PNG's pixels are one stream, and only adjacent chunks can continue it.
            if stream and last != b"IDAT":
                raise RenderFailure("RENDER_PNG_INVALID", "/png")
            stream.append(data[offset + 8 : end])
        last = kind
        offset = end + 4
        if kind == b"IEND":
            if offset != len(data) or not any(stream):
                raise RenderFailure("RENDER_PNG_INVALID", "/png")
            _check_pixels(b"".join(stream), width, height, header)
            return width, height
    raise RenderFailure("RENDER_PNG_INVALID", "/png")
