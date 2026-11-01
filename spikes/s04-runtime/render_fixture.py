"""S04 controlled synthetic fixture, not the production schema or renderer."""

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import resource
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata
import xml.etree.ElementTree as ET

MAX_INPUT = 1024 * 1024
MAX_FILE = 16 * 1024 * 1024
DEFAULT_LABELS = ["Client", "Application", "Database"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(args):
    result = subprocess.run(args, capture_output=True, text=True, check=True, timeout=10)
    return (result.stdout + result.stderr).strip()


def font_metadata(family):
    path = Path(command(["fc-match", "-f", "%{file}", family]))
    data = path.read_bytes()
    names = {}
    table_count = struct.unpack_from(">H", data, 4)[0]
    for offset in range(12, 12 + table_count * 16, 16):
        tag, _, table_offset, _ = struct.unpack_from(">4sIII", data, offset)
        if tag != b"name":
            continue
        _, count, strings = struct.unpack_from(">HHH", data, table_offset)
        for index in range(count):
            platform_id, _, _, name_id, length, position = struct.unpack_from(
                ">HHHHHH", data, table_offset + 6 + index * 12
            )
            if name_id not in (0, 1, 5, 13, 14):
                continue
            raw = data[table_offset + strings + position : table_offset + strings + position + length]
            encoding = "utf-16-be" if platform_id in (0, 3) else "mac_roman"
            value = raw.decode(encoding, errors="replace")
            if name_id not in names or platform_id == 3:
                names[name_id] = value
    return {"requested_family": family, "file": str(path), "sha256": digest(data),
            "name_records": {str(k): v for k, v in names.items()}}


def runtime_info():
    cgroups = {}
    for name in ("memory.max", "memory.swap.max", "pids.max", "cpu.max"):
        path = Path("/sys/fs/cgroup") / name
        cgroups[name] = path.read_text().strip() if path.exists() else None
    info = {"python": platform.python_version(), "system": platform.system(),
            "machine": platform.machine(), "uid": os.getuid(),
            "graphviz": command(["dot", "-V"]),
            "packages": {name: importlib.metadata.version(name) for name in ("diagrams", "graphviz", "mcp")},
            "fonts": [font_metadata(name) for name in ("Noto Sans", "Noto Sans Thai")],
            "cgroups": cgroups}
    return info


def validate(request):
    if not isinstance(request, dict) or set(request) - {"node_count", "labels"}:
        raise ValueError("S04_INVALID_FIELDS")
    count = request.get("node_count", 3)
    if type(count) is not int or count not in (3, 30, 100, 200):
        raise ValueError("S04_INVALID_SIZE")
    labels = request.get("labels", DEFAULT_LABELS)
    if not isinstance(labels, list) or len(labels) != 3:
        raise ValueError("S04_INVALID_LABELS")
    for label in labels:
        if not isinstance(label, str) or not 1 <= len(label) <= 256:
            raise ValueError("S04_LABEL_LIMIT")
        if any(unicodedata.category(c) in ("Cc", "Cs") for c in label):
            raise ValueError("S04_LABEL_CONTROL")
    return count, labels


def render(request, destination):
    from diagrams import Diagram, Edge, Node
    from graphviz import escape

    count, labels = validate(request)
    destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    with Diagram(
        "S04 runtime fixture", filename=str(destination / "diagram"), show=False,
        direction="LR" if count == 3 else "TB", outformat=["svg", "png"],
        graph_attr={"fontname": "Noto Sans", "pad": "0.3", "bgcolor": "white", "dpi": "96"},
        node_attr={"fontname": "Noto Sans Thai", "fontsize": "16", "fixedsize": "false",
                   "height": "0.65", "width": "1.8", "labelloc": "c", "margin": "0.2",
                   "style": "rounded,filled", "fillcolor": "#eef4fb", "color": "#315a7d"},
        edge_attr={"fontname": "Noto Sans", "fontsize": "11"},
    ) as diagram:
        nodes = [Node(escape(labels[i] if count == 3 else f"Node {i + 1:03}"),
                      nodeid=f"n{i}", shape="box") for i in range(count)]
        for index, (source, target) in enumerate(zip(nodes, nodes[1:])):
            source >> Edge(label="HTTPS" if count == 3 and index == 0 else "") >> target
        (destination / "source.dot").write_text(diagram.dot.source, encoding="utf-8")

    svg_path = destination / "diagram.svg"
    svg = svg_path.read_text(encoding="utf-8")
    # Remove Graphviz's fixed external DTD declaration; do not fetch a DTD.
    import re
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.S)
    svg_path.write_text(svg, encoding="utf-8")
    root = ET.fromstring(svg)
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] in ("script", "foreignObject", "image"):
            raise ValueError("S04_UNSAFE_SVG")
        if any(key.rsplit("}", 1)[-1].lower().startswith("on") or key.rsplit("}", 1)[-1] == "href"
               for key in element.attrib):
            raise ValueError("S04_UNSAFE_SVG_ATTRIBUTE")
    png = (destination / "diagram.png").read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("S04_INVALID_PNG")
    width, height = struct.unpack(">II", png[16:24])
    if width * height > 32_000_000:
        raise ValueError("S04_PIXEL_LIMIT")
    (destination / "source.json").write_text(json.dumps(request, indent=2, ensure_ascii=True) + "\n")
    files = {}
    for path in destination.iterdir():
        if path.stat().st_size > MAX_FILE:
            raise ValueError("S04_ARTIFACT_LIMIT")
        files[path.name] = {"bytes": path.stat().st_size, "sha256": digest(path.read_bytes())}
    result = {"scope": "synthetic-runtime-only", "node_count": count, "edge_count": count - 1,
              "elapsed_seconds": round(time.monotonic() - started, 4),
              "png_dimensions": [width, height], "files": files,
              "production_semantics": "not_tested", "work_host": "not_tested"}
    (destination / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (45, 50))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))
    if sys.argv[1:] == ["info"]:
        print(json.dumps(runtime_info()))
        return
    raw = sys.stdin.buffer.read(MAX_INPUT + 1)
    if len(raw) > MAX_INPUT:
        raise ValueError("S04_INPUT_LIMIT")
    request = json.loads(raw)
    validate(request)
    if len(sys.argv) == 3 and sys.argv[1] == "render":
        # The path is supplied by the trusted harness/server, never the request.
        target = Path(sys.argv[2]).resolve()
        if not target.is_relative_to(Path("/tmp")):
            raise ValueError("S04_OUTPUT_ROOT")
        print(json.dumps(render(request, target)))
    else:
        with tempfile.TemporaryDirectory(prefix="s04-") as temporary:
            print(json.dumps(render(request, Path(temporary) / "result")))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(2)
