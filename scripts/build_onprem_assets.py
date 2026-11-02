"""Derive the eight on-premises assets (D-010) from audited draw.io stencil shapes.

Run with --from-full to refresh the subset from a pinned networks.xml. Without it, the SVG
derivation runs from the repository's subset alone, so the gate can repeat it with no network.
PNG output needs rsvg-convert, and the gate checks recorded PNG digests instead of rebuilding.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBSET = ROOT / "assets-source/drawio/networks-subset.xml"
ASSETS = ROOT / "src/cloud_architecture_diagrams/assets/onprem"
MANIFEST = ROOT / "src/cloud_architecture_diagrams/catalog_data/assets.json"
# Palette default from the audited Sidebar-Network.js entry for these shapes.
FILL, STROKE, STROKE_WIDTH = "#CCCCCC", "#6881B3", 2.0
MARGIN = 4.0
PNG_LONG_EDGE = 256
SHAPES = {
    "Load Balancer": "mxgraph.networks.load_balancer",
    "NAS Filer": "mxgraph.networks.nas_filer",
    "Server": "mxgraph.networks.server",
    "Server Storage": "mxgraph.networks.server_storage",
    "Storage": "mxgraph.networks.storage",
    "Users": "mxgraph.networks.users",
    "Virtual Server": "mxgraph.networks.virtual_server",
}
# Layers are (shape, x, y, scale). Two layers make a composition, which is how the host and guest
# of a hypervisor, and the server and people of an identity service, stay readable as one symbol.
CONCEPTS: dict[str, dict[str, object]] = {
    "onprem-load-balancer": {
        "concept": "Load balancer",
        "label": "Load balancer",
        "composition": "direct",
        "layers": [("Load Balancer", 0.0, 0.0, 1.0)],
    },
    "onprem-hypervisor": {
        "concept": "Hypervisor",
        "label": "Hypervisor",
        "composition": "labeled host with a guest symbol, distinct from the VM asset",
        "layers": [("Server", 0.0, 0.0, 1.0), ("Virtual Server", 62.0, 40.0, 0.6)],
    },
    "onprem-vm": {
        "concept": "VM",
        "label": "VM",
        "composition": "direct virtual-server symbol, labeled VM",
        "layers": [("Virtual Server", 0.0, 0.0, 1.0)],
    },
    "onprem-nas": {
        "concept": "NAS",
        "label": "NAS",
        "composition": "direct NAS filer symbol",
        "layers": [("NAS Filer", 0.0, 0.0, 1.0)],
    },
    "onprem-san": {
        "concept": "SAN",
        "label": "SAN",
        "composition": "storage symbol labeled SAN; block and fabric links come from the model",
        "layers": [("Storage", 0.0, 0.0, 1.0)],
    },
    "onprem-identity-service": {
        "concept": "Identity service",
        "label": "Identity service",
        "composition": "labeled server with a people symbol; implies no named product",
        "layers": [("Server", 0.0, 0.0, 1.0), ("Users", 60.0, 44.0, 0.62)],
    },
    "onprem-backup-system": {
        "concept": "Backup system",
        "label": "Backup system",
        "composition": "server-storage symbol labeled as a backup service; no tape imagery",
        "layers": [("Server Storage", 0.0, 0.0, 1.0)],
    },
    "onprem-monitoring": {
        "concept": "Monitoring",
        "label": "Monitoring",
        "composition": "server symbol with a required Monitoring label, not a display symbol",
        "layers": [("Server", 0.0, 0.0, 1.0)],
    },
}


def number(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def shape_digest(shape: ET.Element) -> str:
    # Canonical form, so the digest matches between the full upstream file and the subset.
    return digest(ET.canonicalize(ET.tostring(shape, encoding="unicode"), strip_text=True).encode())


def load_shapes(path: Path = SUBSET) -> dict[str, ET.Element]:
    return {shape.attrib["name"]: shape for shape in ET.parse(path).getroot()}


def path_data(element: ET.Element) -> str:
    parts: list[str] = []
    for step in element:
        attrs = step.attrib
        if step.tag == "move":
            parts.append(f"M{number(float(attrs['x']))} {number(float(attrs['y']))}")
        elif step.tag == "line":
            parts.append(f"L{number(float(attrs['x']))} {number(float(attrs['y']))}")
        elif step.tag == "arc":
            parts.append(
                f"A{number(float(attrs['rx']))} {number(float(attrs['ry']))} "
                f"{number(float(attrs['x-axis-rotation']))} {attrs['large-arc-flag']} "
                f"{attrs['sweep-flag']} {number(float(attrs['x']))} {number(float(attrs['y']))}"
            )
        elif step.tag == "close":
            parts.append("Z")
        else:
            raise ValueError(f"Unsupported stencil path step: {step.tag}")
    return " ".join(parts)


def geometry(element: ET.Element) -> str:
    attrs = element.attrib
    if element.tag == "path":
        return f'<path d="{path_data(element)}"'
    # A stencil coordinate left out of the XML is zero in mxGraph.
    values = {key: float(attrs.get(key, "0")) for key in ("x", "y", "w", "h")}
    x, y, w, h = (number(values[key]) for key in ("x", "y", "w", "h"))
    if element.tag == "rect":
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}"'
    if element.tag == "roundrect":
        radius = min(values["w"], values["h"]) * float(attrs["arcsize"]) / 100
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{number(radius)}"'
    if element.tag == "ellipse":
        rx, ry = values["w"] / 2, values["h"] / 2
        cx, cy = values["x"] + rx, values["y"] + ry
        return f'<ellipse cx="{number(cx)}" cy="{number(cy)}" rx="{number(rx)}" ry="{number(ry)}"'
    raise ValueError(f"Unsupported stencil geometry: {element.tag}")


def shape_elements(shape: ET.Element, stroke_width: float) -> list[str]:
    """A small mxGraph stencil interpreter covering the tags these seven shapes use."""
    output: list[str] = []
    state = {"fill": FILL, "stroke": STROKE, "dash": ""}
    saved: list[dict[str, str]] = []
    current = ""
    foreground = shape.find("foreground")
    assert foreground is not None
    for element in foreground:
        if element.tag in {"rect", "roundrect", "ellipse", "path"}:
            current = geometry(element)
        elif element.tag in {"fillstroke", "fill", "stroke"}:
            fill = state["fill"] if element.tag != "stroke" else "none"
            stroke = state["stroke"] if element.tag != "fill" else "none"
            width = f' stroke-width="{number(stroke_width)}"' if stroke != "none" else ""
            dash = state["dash"] if stroke != "none" else ""
            output.append(f'{current} fill="{fill}" stroke="{stroke}"{width}{dash}/>')
        elif element.tag == "fillcolor":
            state["fill"] = element.attrib["color"]
        elif element.tag == "dashed":
            if element.attrib["dashed"] == "0":
                state["dash"] = ""
        elif element.tag == "dashpattern":
            pattern = " ".join(element.attrib["pattern"].split())
            state["dash"] = f' stroke-dasharray="{pattern}"'
        elif element.tag == "save":
            saved.append(dict(state))
        elif element.tag == "restore":
            state = saved.pop()
        else:
            raise ValueError(f"Unsupported stencil operation: {element.tag}")
    return output


def compose(asset_id: str, shapes: dict[str, ET.Element]) -> tuple[str, float, float]:
    layers = CONCEPTS[asset_id]["layers"]
    assert isinstance(layers, list)
    width = height = 0.0
    groups: list[str] = []
    for name, x, y, scale in layers:
        shape = shapes[name]
        width = max(width, x + float(shape.attrib["w"]) * scale)
        height = max(height, y + float(shape.attrib["h"]) * scale)
        inner = "\n".join(shape_elements(shape, STROKE_WIDTH / scale))
        transform = f"translate({number(x + MARGIN)} {number(y + MARGIN)}) scale({number(scale)})"
        groups.append(f'<g transform="{transform}">\n{inner}\n</g>')
    full_width, full_height = width + 2 * MARGIN, height + 2 * MARGIN
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {number(full_width)} '
        f'{number(full_height)}" width="{number(full_width)}" height="{number(full_height)}">\n'
        + "\n".join(groups)
        + "\n</svg>\n"
    )
    return svg, full_width, full_height


def refresh_subset(full: Path) -> None:
    root = ET.parse(full).getroot()
    wanted = [shape for shape in root if shape.attrib["name"] in SHAPES]
    assert {shape.attrib["name"] for shape in wanted} == set(SHAPES)
    subset = ET.Element("shapes", root.attrib)
    subset.extend(wanted)
    ET.indent(subset)
    SUBSET.write_text(ET.tostring(subset, encoding="unicode") + "\n")


def render_png(svg_path: Path, png_path: Path, width: float, height: float) -> tuple[int, int]:
    scale = PNG_LONG_EDGE / max(width, height)
    size = (round(width * scale), round(height * scale))
    subprocess.run(
        ["rsvg-convert", "-w", str(size[0]), "-h", str(size[1]), "-o", png_path, svg_path],
        check=True,
    )
    return size


def build() -> list[dict[str, object]]:
    shapes = load_shapes()
    records: list[dict[str, object]] = []
    for asset_id, concept in CONCEPTS.items():
        svg, width, height = compose(asset_id, shapes)
        base = asset_id.removeprefix("onprem-")
        svg_path, png_path = ASSETS / f"{base}.svg", ASSETS / f"{base}.png"
        svg_path.write_text(svg)
        pixels = render_png(svg_path, png_path, width, height)
        layers = concept["layers"]
        assert isinstance(layers, list)
        names = list(dict.fromkeys(layer[0] for layer in layers))
        records.append(
            {
                "id": asset_id,
                "pack": "drawio-network-2018",
                "concept": concept["concept"],
                "required_label": concept["label"],
                "composition": concept["composition"],
                "symbols": [SHAPES[name] for name in names],
                "original": [
                    {"name": name, "canonical_sha256": shape_digest(shapes[name])} for name in names
                ],
                "derived": {
                    "svg": {
                        "path": f"assets/onprem/{base}.svg",
                        "sha256": digest(svg_path.read_bytes()),
                    },
                    "png": {
                        "path": f"assets/onprem/{base}.png",
                        "sha256": digest(png_path.read_bytes()),
                        "width": pixels[0],
                        "height": pixels[1],
                    },
                },
                "changes": "Converted the stencil geometry to SVG, applied the palette's default "
                "colors, and rasterized to PNG"
                + ("; layered two symbols" if len(layers) > 1 else ""),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-full", type=Path, default=None)
    args = parser.parse_args()
    if args.from_full:
        refresh_subset(args.from_full)
    ASSETS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    manifest["assets"] = build()
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + "\n")
    print(json.dumps([item["id"] for item in manifest["assets"]]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
