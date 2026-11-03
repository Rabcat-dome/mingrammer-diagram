"""M4-04 baselines: what a reference view looked like when it was last reviewed."""

import hashlib
import json
import struct
import subprocess
import zlib
from pathlib import Path
from typing import Any

from render_helpers import FIXTURES, ROOT, bundle_files, graph_of, render

from cloud_architecture_diagrams.render.execution import find_engine

BASELINES = ROOT / "tests/baselines"
RECORD = BASELINES / "baselines.json"
REFERENCES = FIXTURES / "references"
# Decoding is plain Python, so a very large image gets its before and after but no diff.
DIFF_PIXEL_LIMIT = 12_000_000


def reference_views() -> list[tuple[str, str]]:
    return [
        (path.stem, view["id"])
        for path in sorted(REFERENCES.glob("*.json"))
        for view in json.loads(path.read_text())["views"]
    ]


def view_key(scenario: str, view: str) -> str:
    return f"{scenario}--{view}"


def render_view(scenario: str, view: str, output: Path) -> dict[str, Any]:
    result = render((REFERENCES / f"{scenario}.json").read_bytes(), output, view=view)
    assert result.rendered, [item.code for item in result.diagnostics]
    files = bundle_files(result)
    return {"graph": graph_of(result), "svg": files["diagram.svg"], "png": files["diagram.png"]}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def engine_version() -> str:
    run = subprocess.run(
        [find_engine().path, "-V"], capture_output=True, text=True, timeout=30, check=True
    )
    return run.stderr.strip()


def graph_text(graph: dict[str, Any]) -> str:
    return json.dumps(graph, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def decode_png(data: bytes) -> tuple[int, int, int, list[bytes]]:
    """Width, height, bytes per pixel and unfiltered rows of the 8-bit images Cairo writes."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    position = 8
    width = height = channels = 0
    compressed = bytearray()
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position : position + 8])
        body = data[position + 8 : position + 8 + length]
        position += length + 12
        if kind == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and interlace == 0
            channels = {0: 1, 2: 3, 4: 2, 6: 4}[color]
        elif kind == b"IDAT":
            compressed += body
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    rows: list[bytes] = []
    previous = bytes(stride)
    for index in range(height):
        start = index * (stride + 1)
        rows.append(_unfilter(raw[start], raw[start + 1 : start + 1 + stride], previous, channels))
        previous = rows[-1]
    return width, height, channels, rows


def _unfilter(kind: int, line: bytes, above: bytes, channels: int) -> bytes:
    if kind == 0:
        return line
    if kind == 2:
        return bytes((a + b) & 255 for a, b in zip(line, above, strict=True))
    row = bytearray(line)
    for index, value in enumerate(row):
        left = row[index - channels] if index >= channels else 0
        up = above[index]
        corner = above[index - channels] if index >= channels else 0
        if kind == 1:
            predicted = left
        elif kind == 3:
            predicted = (left + up) // 2
        else:
            estimate = left + up - corner
            near = [abs(estimate - left), abs(estimate - up), abs(estimate - corner)]
            predicted = (left, up, corner)[near.index(min(near))]
        row[index] = (value + predicted) & 255
    return bytes(row)


def encode_png(width: int, height: int, channels: int, rows: list[bytes]) -> bytes:
    color = {1: 0, 2: 4, 3: 2, 4: 6}[channels]

    def chunk(kind: bytes, body: bytes) -> bytes:
        checksum = zlib.crc32(kind + body)
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", checksum)

    header = struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0)
    body = zlib.compress(b"".join(b"\0" + row for row in rows))
    return (
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", body) + chunk(b"IEND", b"")
    )


def compare_images(before: bytes, after: bytes) -> tuple[float | None, bytes | None]:
    """The share of pixels that changed, and an image marking them in red on a faded copy."""
    if before == after:
        return 0.0, None
    old = struct.unpack(">II", before[16:24])
    new = struct.unpack(">II", after[16:24])
    if old != new:
        return 1.0, None
    if old[0] * old[1] > DIFF_PIXEL_LIMIT:
        return None, None
    width, height, channels, old_rows = decode_png(before)
    other_width, other_height, other_channels, new_rows = decode_png(after)
    assert (width, height) == (other_width, other_height) and channels == other_channels
    changed = 0
    marked: list[bytes] = []
    for first, second in zip(old_rows, new_rows, strict=True):
        line = bytearray(255 - (255 - value) // 4 for value in second)
        if channels == 4:
            line[3::4] = b"\xff" * width
        if first != second:
            for index in range(width):
                offset = index * channels
                if first[offset : offset + channels] != second[offset : offset + channels]:
                    changed += 1
                    line[offset : offset + channels] = b"\xff\x00\x00\xff"[:channels]
        marked.append(bytes(line))
    return changed / (width * height), encode_png(width, height, channels, marked)
