"""D-049: an editable draw.io copy of the checked drawing, built from its SVG. Nothing runs here.

Every position comes from the SVG that `check_svg` and `check_content` already accepted, so the copy
opens looking like the PNG without a second Graphviz run. Groups become containers that carry their
contents, resources keep their verified icons, and each line stays attached to both of its ends.
Text is plain text (`html=0`), so no model value can become markup in draw.io.
"""

import base64
import hashlib
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterator

from .checks import DATA_PNG, FONT_STACK, HREF, SVG, decoded_png
from .draw import EDGE_STYLES, LABEL_POINTS, TEXT_COLOR
from .errors import RenderFailure
from .graph import GraphGroup, GraphNode, RenderGraph
from .icons import VerifiedIcon
from .limits import Limits

MEDIA_TYPE = "application/vnd.jgraph.mxfile"
# draw.io keeps an image inside a style, where `;` separates entries, so its data URI has none.
DRAWIO_PNG = "data:image/png,"
ROOT_TRANSFORM = re.compile(
    r"^scale\((?P<sx>[0-9.]+) (?P<sy>[0-9.]+)\) rotate\(0\) "
    r"translate\((?P<tx>-?[0-9.]+) (?P<ty>-?[0-9.]+)\)$"
)
NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?(?:e-?[0-9]+)?")
TITLE_LINE_POINTS = 16
LEGEND_SAMPLE_INSET = 12
# Graphviz's own patterns, so a line looks the same in both files.
DASHES = {"dashed": "5 2", "dotted": "1 5"}
Box = tuple[float, float, float, float]

# One closed vocabulary for the check, so the copy can carry nothing this module did not write.
STYLE_KEYS = {
    "shape", "image", "imageAspect", "aspect", "verticalAlign",
    "align", "html", "fontFamily", "fontSize", "fontColor", "rounded",
    "absoluteArcSize", "arcSize", "container", "collapsible", "fillColor", "strokeColor",
    "strokeWidth", "dashed", "dashPattern", "spacingLeft", "spacingTop", "edgeStyle", "endArrow",
    "endFill", "startArrow", "labelBackgroundColor", "text", "connectable", "imageWidth",
    "imageHeight", "imageAlign", "imageVerticalAlign",
}  # fmt: skip
# Commas only for the font list, as the SVG names it, so a viewer without Noto still reads text.
SAFE_VALUE = re.compile(r"^[A-Za-z0-9#., -]*$")
NAMED_COLORS = {"white": "#ffffff", "black": "#000000"}
CELL_ATTRIBUTES = {"id", "parent", "value", "style", "vertex", "edge", "source", "target"}
GEOMETRY_ATTRIBUTES = {"x", "y", "width", "height", "relative", "as"}
TEXT_STYLE = {
    "html": "0",
    "fontFamily": FONT_STACK,
    "fontSize": LABEL_POINTS,
    "fontColor": TEXT_COLOR,
}
CONTAINER_STYLE = {
    "container": "1",
    "collapsible": "0",
    "verticalAlign": "top",
    "align": "left",
    "spacingLeft": "6",
    "spacingTop": "2",
}


def _number(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def _style(entries: dict[str, str]) -> str:
    return "".join(f"{key}={value};" for key, value in entries.items())


def _text(lines: tuple[str, ...] | list[str]) -> str:
    return "\n".join(lines)


def _add(holder: ET.Element, tag: str, attributes: dict[str, str]) -> ET.Element:
    # `SubElement` names its own first argument `parent`, so attributes always go in as a dict.
    return ET.SubElement(holder, tag, attributes)


def _geometry(holder: ET.Element, box: Box, left: float = 0.0, top: float = 0.0) -> None:
    x, y, width, height = box
    _add(
        holder,
        "mxGeometry",
        {
            "x": _number(x - left),
            "y": _number(y - top),
            "width": _number(width),
            "height": _number(height),
            "as": "geometry",
        },
    )


class _Page:
    """Moves Graphviz's coordinates, whose y axis runs upward, onto the SVG's page."""

    def __init__(self, root: ET.Element) -> None:
        self.by_id = {element.get("id"): element for element in root.iter(f"{{{SVG}}}g")}
        self.canvas = self.element("graph:root")
        match = ROOT_TRANSFORM.match(self.canvas.get("transform", ""))
        sizes = NUMBER.findall(root.get("width", "")), NUMBER.findall(root.get("height", ""))
        if match is None or not all(sizes):
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
        self.scale = float(match["sx"])
        self.shift = (float(match["tx"]), float(match["ty"]))
        self.width, self.height = float(sizes[0][0]), float(sizes[1][0])

    def point(self, x: float, y: float) -> tuple[float, float]:
        return (x + self.shift[0]) * self.scale, (y + self.shift[1]) * self.scale

    def element(self, identifier: str) -> ET.Element:
        element = self.by_id.get(identifier)
        if element is None:
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio", identifier.partition(":")[2])
        return element

    def box(self, points: list[tuple[float, float]]) -> Box:
        placed = [self.point(x, y) for x, y in points]
        if not placed:
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
        left, top = min(x for x, _ in placed), min(y for _, y in placed)
        right, bottom = max(x for x, _ in placed), max(y for _, y in placed)
        return left, top, right - left, bottom - top


def _pairs(text: str) -> list[tuple[float, float]]:
    numbers = [float(item) for item in NUMBER.findall(text)]
    return list(zip(numbers[::2], numbers[1::2], strict=False))


def _outline(element: ET.Element, entity: str | None) -> ET.Element:
    for child in element:
        if child.tag in (f"{{{SVG}}}path", f"{{{SVG}}}polygon"):
            return child
    raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio", entity)


def _outline_points(shape: ET.Element) -> list[tuple[float, float]]:
    return _pairs(shape.get("points") or shape.get("d") or "")


def _line_points(path: ET.Element) -> list[tuple[float, float]]:
    """Graphviz writes a line as one move and a run of cubic pieces. Only piece ends lie on it."""
    pairs = _pairs(path.get("d", ""))
    return [pairs[0], *pairs[3::3]] if pairs else []


def _color(value: str) -> str:
    """Graphviz writes some colors by name. draw.io gets every one as a hex value, or none."""
    value = value.lower()
    if value in {"none", "transparent"}:
        return "none"
    return NAMED_COLORS.get(value, value).upper()


def _shape_style(shape: ET.Element) -> dict[str, str]:
    entries = {
        "rounded": "1" if shape.tag == f"{{{SVG}}}path" else "0",
        "absoluteArcSize": "1",
        "arcSize": "12",
        "fillColor": _color(shape.get("fill", "none")),
        "strokeColor": _color(shape.get("stroke", "#7B8894")),
    }
    dashes = shape.get("stroke-dasharray")
    if dashes:
        entries |= {"dashed": "1", "dashPattern": " ".join(NUMBER.findall(dashes))}
    return entries


def _line_style(kind: str, directed: bool) -> dict[str, str]:
    color, line = EDGE_STYLES[kind]
    style = {
        "edgeStyle": "none",
        "rounded": "0",
        "endArrow": "block" if directed else "none",
        "endFill": "1",
        "startArrow": "none",
        "strokeColor": color.upper(),
        # draw.io centres a label on its line, so a backing keeps the line from crossing it.
        "labelBackgroundColor": "#FFFFFF",
        **TEXT_STYLE,
        "fontSize": "10",
    }
    if line in DASHES:
        style |= {"dashed": "1", "dashPattern": DASHES[line]}
    if line == "bold":
        style["strokeWidth"] = "2"
    return style


class _Writer:
    def __init__(self, graph: RenderGraph, page: _Page) -> None:
        self.graph = graph
        self.page = page
        self.nodes = {node.id for node in graph.nodes}
        self.boxes: dict[str, Box] = {}
        self.cells = ET.Element("root")
        _add(self.cells, "mxCell", {"id": "0"})
        _add(self.cells, "mxCell", {"id": "1", "parent": "0"})

    def _vertex(
        self, identifier: str, parent: str | None, box: Box, value: str, style: dict[str, str]
    ) -> ET.Element:
        """draw.io places a child relative to its container, so its box is moved by the parent's."""
        self.boxes[identifier] = box
        holder = "1" if parent is None else f"group:{parent}"
        left, top = (0.0, 0.0) if parent is None else self.boxes[holder][:2]
        cell = _add(
            self.cells,
            "mxCell",
            {
                "id": identifier,
                "parent": holder,
                "value": value,
                "style": _style(style),
                "vertex": "1",
            },
        )
        _geometry(cell, box, left, top)
        return cell

    def _ordered_groups(self) -> Iterator[GraphGroup]:
        """draw.io reads a parent before its children, so containers go outside in."""
        done: set[str | None] = {None}
        pending = list(self.graph.groups)
        while pending:
            ready = [group for group in pending if group.parent in done]
            if not ready:
                raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
            for group in ready:
                done.add(group.id)
                pending.remove(group)
                yield group

    def add_groups(self) -> None:
        for group in self._ordered_groups():
            outline = _outline(self.page.element(f"group:{group.id}"), group.id)
            self._vertex(
                f"group:{group.id}",
                group.parent,
                self.page.box(_outline_points(outline)),
                _text(group.lines),
                {**_shape_style(outline), **CONTAINER_STYLE, **TEXT_STYLE},
            )

    def _icon(self, element: ET.Element, node: GraphNode) -> tuple[Box, str]:
        images = element.findall(f"{{{SVG}}}image")
        if len(images) != 1:
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio", node.id)
        image = images[0]
        x, y = float(image.get("x", "0")), float(image.get("y", "0"))
        width = float(NUMBER.findall(image.get("width", "0"))[0])
        height = float(NUMBER.findall(image.get("height", "0"))[0])
        encoded = base64.b64encode(decoded_png(image.get(HREF, ""))).decode()
        return self.page.box([(x, y), (x + width, y + height)]), DRAWIO_PNG + encoded

    def _labelled(self, element: ET.Element, icon: Box) -> Box:
        """The box Graphviz gave the node: its icon and the text below, so lines stop where they do.

        Left to right, `draw` adds as much room above the icon as the text takes below it.
        """
        baselines = [float(text.get("y", "0")) for text in element.findall(f"{{{SVG}}}text")]
        x, top, width, height = icon
        bottom = max([top + height, *(self.page.point(0, y)[1] + 4 for y in baselines)])
        if self.graph.direction == "LR":
            middle = top + height / 2
            top = middle - (bottom - middle)
        return x, top, width, bottom - top

    def add_nodes(self) -> None:
        image_style = {"shape": "image", "imageAspect": "1", "aspect": "fixed"}
        for node in self.graph.nodes:
            identifier = f"node:{node.id}"
            element = self.page.element(identifier)
            if node.icon and not node.fallback:
                box, image = self._icon(element, node)
                self._vertex(
                    identifier,
                    node.group,
                    self._labelled(element, box),
                    _text(node.lines),
                    {
                        "shape": "label",
                        "image": image,
                        "imageWidth": _number(box[2]),
                        "imageHeight": _number(box[3]),
                        "imageAlign": "center",
                        "imageVerticalAlign": "top" if self.graph.direction == "TB" else "middle",
                        "verticalAlign": "bottom",
                        "align": "center",
                        "fillColor": "none",
                        "strokeColor": "none",
                        **TEXT_STYLE,
                    },
                )
                continue
            outline = _outline(element, node.id)
            frame = self.page.box(_outline_points(outline))
            style = {**_shape_style(outline), "verticalAlign": "bottom" if node.icon else "middle"}
            self._vertex(identifier, node.group, frame, _text(node.lines), {**style, **TEXT_STYLE})
            if node.icon:
                # A stand-in keeps its frame, which is what marks it, and its icon sits inside.
                box, image = self._icon(element, node)
                cell = _add(
                    self.cells,
                    "mxCell",
                    {
                        "id": f"icon:{node.id}",
                        "parent": identifier,
                        "value": "",
                        "style": _style(
                            {**image_style, "image": image, "connectable": "0", "html": "0"}
                        ),
                        "vertex": "1",
                    },
                )
                _geometry(cell, box, frame[0], frame[1])

    def _end(self, identifier: str) -> str:
        return f"node:{identifier}" if identifier in self.nodes else f"group:{identifier}"

    def add_edges(self) -> None:
        for edge in self.graph.edges:
            path = self.page.element(f"edge:{edge.id}").find(f"{{{SVG}}}path")
            if path is None:
                raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio", edge.id)
            source, target = self._end(edge.source), self._end(edge.target)
            # Graphviz writes a line from its tail to its head, in all 47 fixture views.
            points = [self.page.point(x, y) for x, y in _line_points(path)]
            cell = _add(
                self.cells,
                "mxCell",
                {
                    "id": f"edge:{edge.id}",
                    "parent": "1",
                    "value": _text(edge.lines),
                    "style": _style(_line_style(edge.kind, edge.directed)),
                    "edge": "1",
                    "source": source,
                    "target": target,
                },
            )
            geometry = _add(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            if len(points) > 2:
                bends = _add(geometry, "Array", {"as": "points"})
                for x, y in points[1:-1]:
                    _add(bends, "mxPoint", {"x": _number(x), "y": _number(y)})

    def add_legend(self) -> None:
        if not self.graph.legend:
            return
        outline = _outline(self.page.element("legend"), None)
        box = self.page.box(_outline_points(outline))
        style = {**_shape_style(outline), **CONTAINER_STYLE, **TEXT_STYLE}
        self._vertex("legend", None, box, "Legend", style)
        _, _, width, height = box
        step = (height - 2 * TITLE_LINE_POINTS) / len(self.graph.legend)
        directed = {edge.kind for edge in self.graph.edges if edge.directed}
        for index, kind in enumerate(self.graph.legend):
            y = _number(2 * TITLE_LINE_POINTS + step * (index + 0.5))
            cell = _add(
                self.cells,
                "mxCell",
                {
                    "id": f"legend:{kind}",
                    "parent": "legend",
                    "value": kind,
                    "style": _style(_line_style(kind, kind in directed)),
                    "edge": "1",
                },
            )
            geometry = _add(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            start = {"x": _number(LEGEND_SAMPLE_INSET), "y": y, "as": "sourcePoint"}
            end = {"x": _number(width - LEGEND_SAMPLE_INSET), "y": y, "as": "targetPoint"}
            _add(geometry, "mxPoint", start)
            _add(geometry, "mxPoint", end)

    def add_title(self) -> None:
        lines = (*self.graph.title_lines, *self.graph.notice_lines)
        baselines = [
            float(text.get("y", "0")) for text in self.page.canvas.findall(f"{{{SVG}}}text")
        ]
        if not baselines:
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
        top = self.page.point(0, min(baselines))[1] - TITLE_LINE_POINTS
        style = {
            "text": "",
            "align": "center",
            "verticalAlign": "top",
            "fillColor": "none",
            "strokeColor": "none",
            **TEXT_STYLE,
            "fontSize": "12",
        }
        box = (0.0, top, self.page.width, TITLE_LINE_POINTS * len(lines) + 8.0)
        self._vertex("title", None, box, _text(lines), style)


def build_drawio(root: ET.Element, graph: RenderGraph, limits: Limits) -> bytes:
    page = _Page(root)
    writer = _Writer(graph, page)
    writer.add_groups()
    writer.add_nodes()
    writer.add_edges()
    writer.add_legend()
    writer.add_title()
    document = ET.Element("mxfile", {"host": "cloud-architecture-diagrams"})
    diagram = _add(document, "diagram", {"id": graph.view_id, "name": graph.view_id})
    model = _add(
        diagram,
        "mxGraphModel",
        {
            "grid": "0",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "1",
            "pageScale": "1",
            "pageWidth": _number(page.width),
            "pageHeight": _number(page.height),
            "background": "#FFFFFF",
            "math": "0",
            "shadow": "0",
        },
    )
    model.append(writer.cells)
    data: bytes = ET.tostring(document, encoding="utf-8", xml_declaration=True)
    if len(data) > limits.file_bytes:
        raise RenderFailure("RENDER_ARTIFACT_LIMIT", "/drawio")
    return data


def _style_entries(style: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    for item in filter(None, style.split(";")):
        key, separator, value = item.partition("=")
        if not separator or key not in STYLE_KEYS or key in entries:
            raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
        entries[key] = value
    return entries


def _icon_digest(style: dict[str, str]) -> str:
    image = style.get("image", "")
    if not image.startswith(DRAWIO_PNG):
        raise RenderFailure("RENDER_CONTENT_MISSING", "/drawio")
    return hashlib.sha256(decoded_png(DATA_PNG + image.removeprefix(DRAWIO_PNG))).hexdigest()


def _cells(data: bytes, allowed_icons: set[str]) -> dict[str, ET.Element]:
    """A closed vocabulary over the parsed copy, as `check_svg` has over the SVG."""

    def unsafe() -> RenderFailure:
        return RenderFailure("RENDER_CONTENT_MISSING", "/drawio")

    if b"<!" in data:
        raise unsafe()
    try:
        document = ET.fromstring(data)
    except ET.ParseError as error:
        raise unsafe() from error
    diagrams = list(document)
    if document.tag != "mxfile" or len(diagrams) != 1 or diagrams[0].tag != "diagram":
        raise unsafe()
    models = list(diagrams[0])
    if len(models) != 1 or models[0].tag != "mxGraphModel" or len(models[0]) != 1:
        raise unsafe()
    cells: dict[str, ET.Element] = {}
    for cell in models[0][0]:
        identifier = cell.get("id", "")
        if cell.tag != "mxCell" or set(cell.attrib) - CELL_ATTRIBUTES or identifier in cells:
            raise unsafe()
        cells[identifier] = cell
        style = _style_entries(cell.get("style", ""))
        if cell.get("value") and style.get("html") != "0":
            raise unsafe()
        for key, value in style.items():
            if key == "image":
                if _icon_digest(style) not in allowed_icons:
                    raise unsafe()
            elif not SAFE_VALUE.match(value):
                raise unsafe()
        for part in cell.iter():
            known = (
                part is cell
                or (part.tag == "mxGeometry" and not set(part.attrib) - GEOMETRY_ATTRIBUTES)
                or (part.tag == "Array" and part.attrib == {"as": "points"})
                or (part.tag == "mxPoint" and not set(part.attrib) - {"x", "y", "as"})
            )
            if not known:
                raise unsafe()
    for identifier, cell in cells.items():
        references = [cell.get(key) for key in ("parent", "source", "target")]
        if any(item is not None and item not in cells for item in references) or (
            identifier != "0" and cell.get("parent") is None
        ):
            raise unsafe()
    return cells


def check_drawio(
    data: bytes, graph: RenderGraph, icons: dict[str, VerifiedIcon], limits: Limits
) -> None:
    """Checked like the SVG: nothing outside the vocabulary, plain text, and every element there."""
    if len(data) > limits.file_bytes:
        raise RenderFailure("RENDER_ARTIFACT_LIMIT", "/drawio")
    cells = _cells(data, {icon.sha256 for icon in icons.values()})

    def missing(entity: str | None = None) -> RenderFailure:
        return RenderFailure("RENDER_CONTENT_MISSING", "/drawio", entity)

    for group in graph.groups:
        found = cells.get(f"group:{group.id}")
        if found is None or found.get("value") != _text(group.lines):
            raise missing(group.id)
    nodes = {node.id for node in graph.nodes}
    for node in graph.nodes:
        found = cells.get(f"node:{node.id}")
        if found is None or found.get("value") != _text(node.lines):
            raise missing(node.id)
        if node.icon:
            holder = cells.get(f"icon:{node.id}") if node.fallback else found
            if holder is None or (
                _icon_digest(_style_entries(holder.get("style", "")))
                != icons[node.icon.reference].sha256
            ):
                raise missing(node.id)

    def end(identifier: str) -> str:
        return f"node:{identifier}" if identifier in nodes else f"group:{identifier}"

    for edge in graph.edges:
        found = cells.get(f"edge:{edge.id}")
        if (
            found is None
            or found.get("value") != _text(edge.lines)
            or found.get("source") != end(edge.source)
            or found.get("target") != end(edge.target)
            or _style_entries(found.get("style", "")).get("endArrow")
            != ("block" if edge.directed else "none")
        ):
            raise missing(edge.id)
    title = cells.get("title")
    if title is None or title.get("value") != _text((*graph.title_lines, *graph.notice_lines)):
        raise missing()
    if graph.legend and "legend" not in cells:
        raise missing()
