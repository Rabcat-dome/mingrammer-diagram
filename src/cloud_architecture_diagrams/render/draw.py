"""RenderGraph to DOT through controlled `diagrams` classes. Nothing here runs Graphviz."""

import math
from itertools import pairwise
from typing import Any

from ..models import Relationship
from .graph import GraphEdge, GraphGroup, GraphNode, RenderGraph
from .icons import VerifiedIcon

FONT = "Noto Sans"
TEXT_COLOR = "#2D3436"
ICON_INCHES = 1.0
# A portrait icon fills the width and runs past this size, so the gap also covers its overhang.
ICON_GAP_INCHES = 0.15
# Thai marks stack above and below the line, so a line needs more height than Latin text alone.
LINE_INCHES = 0.23
FALLBACK_WIDTH_INCHES = 1.8
LABEL_POINTS = "11"
EDGE_POINTS = "10"
# One closed table, so no model value can choose a color, a style or a Graphviz attribute.
EDGE_STYLES: dict[str, tuple[str, str]] = {
    "traffic": ("#2D3436", "solid"),
    "vpn": ("#8E44AD", "dashed"),
    "peering": ("#2980B9", "bold"),
    "replication": ("#16A085", "dashed"),
    "management": ("#7F8C8D", "dotted"),
    "membership": ("#95A5A6", "dotted"),
    "scheduling": ("#D35400", "dashed"),
    "policy": ("#C0392B", "dotted"),
    "storage": ("#795548", "solid"),
    "configuration": ("#607D8B", "dashed"),
    "attachment": ("#34495E", "solid"),
    "ownership": ("#6C5CE7", "dashed"),
    "dependency": ("#2D3436", "dashed"),
    "observability": ("#27AE60", "dotted"),
}
assert set(EDGE_STYLES) == set(Relationship.model_fields["kind"].annotation.__args__)  # type: ignore[union-attr]
SECURITY_KINDS = {"security_zone", "security_group"}
PROVIDER_FILL = {
    "aws": "#FFF8EE",
    "azure": "#EFF6FC",
    "gcp": "#F1F6FE",
    "huawei": "#FDF1F1",
    "onprem": "#F4F5F6",
    "external": "#FAFAFA",
}
NESTED_FILLS = ("#FFFFFF", "#F7F9FA")
# Border color, border style and fill, read from the official diagrams pinned in the S08
# evidence. One closed table, keyed by provider and kind, so no model value can choose them.
GROUP_STYLES: dict[tuple[str, str], tuple[str, str, str]] = {
    ("aws", "region"): ("#147EBA", "solid", "#FFFFFF"),
    ("aws", "zone"): ("#147EBA", "dashed", "#FFFFFF"),
    ("aws", "network"): ("#7AA116", "solid", "#FFFFFF"),
    ("aws", "subnet"): ("#7D8998", "solid", "#F2F6FA"),
    ("aws", "security_group"): ("#DD344C", "solid", "#FFFFFF"),
    ("azure", "network"): ("#0078D4", "dashed", "#FFFFFF"),
    ("azure", "subnet"): ("#7F7F7F", "dotted", "#FFFFFF"),
    ("gcp", "organization"): ("#80868B", "solid", "#FFFFFF"),
    ("gcp", "folder"): ("#80868B", "dashed", "#FFFFFF"),
    ("gcp", "project"): ("#80868B", "dashed", "#F1F3F4"),
    ("gcp", "network"): ("#AECBFA", "solid", "#E8F0FE"),
    ("gcp", "region"): ("#A8DAB5", "solid", "#E6F4EA"),
    ("gcp", "subnet"): ("#C5B3E6", "solid", "#EDE7F6"),
    ("huawei", "region"): ("#7F9CC0", "solid", "#FFFFFF"),
    ("huawei", "zone"): ("#3B7DD8", "dashed", "#FFFFFF"),
}


def literal(lines: tuple[str, ...] | list[str], *, left: bool = False) -> Any:
    """Plain text only: `&` would decode as an entity, `\\` as an escape, `<...>` as HTML."""
    from graphviz import escape, nohtml

    separator = "\\l" if left else "\\n"
    text = separator.join(str(escape(line.replace("&", "&amp;"))) for line in lines)
    return nohtml(text + separator if left else text)


def build_dot(graph: RenderGraph, icons: dict[str, VerifiedIcon]) -> str:
    return _Drawing(graph, icons).source()


class _Drawing:
    def __init__(self, graph: RenderGraph, icons: dict[str, VerifiedIcon]) -> None:
        self.graph = graph
        self.icons = icons
        self.children: dict[str | None, list[GraphGroup]] = {}
        for group in graph.groups:
            self.children.setdefault(group.parent, []).append(group)
        self.members: dict[str | None, list[GraphNode]] = {}
        for node in graph.nodes:
            self.members.setdefault(node.group, []).append(node)
        self.node_ids = {node.id for node in graph.nodes}
        self.groups = {group.id: group for group in graph.groups}
        # D-055: the level each banded or east-west entity is drawn on, and whether a band fixes it.
        self.rows: dict[str, tuple[int, bool]] = {
            identifier: (index, index < len(graph.bands))
            for index, row in enumerate([*graph.bands, *graph.levels])
            for identifier in row
        }
        # Edges need a node to end on, and a group without its own marker has none. Nor has a
        # row anything to hold it on that level.
        self.anchors = {
            endpoint
            for edge in graph.edges
            for endpoint in (edge.source, edge.target)
            if endpoint not in self.node_ids
        } | {identifier for identifier in self.rows if identifier not in self.node_ids}
        self.drawn: dict[str, Any] = {}
        # A tinted box tells providers apart, which one alone does not need.
        self.many_providers = sum(group.entity == "provider" for group in graph.groups) > 1

    def source(self) -> str:
        from diagrams import Diagram, setcluster, setdiagram

        graph = self.graph
        diagram = Diagram(
            name="architecture",
            filename="graph",
            direction=graph.direction,
            outformat=["svg", "png"],
            show=False,
            graph_attr={
                "id": "graph:root",
                "label": literal([*graph.title_lines, *graph.notice_lines]),
                "labelloc": "b",
                "fontname": FONT,
                "fontsize": "12",
                "fontcolor": TEXT_COLOR,
                "bgcolor": "white",
                # A label can pass its node's width by about half an inch each side, here and in a
                # group's margin, so neither the canvas nor a border clips it.
                "pad": "0.6",
                # D-048: straight segments read as lines rather than curves, and keep their labels.
                # Right angles were tried and refused: `ortho` drops edge labels and ends lines on
                # the label's box rather than the icon.
                "splines": "polyline",
                "compound": "true",
                # Icon nodes keep a fixed width so that their icon keeps its size, and a wrapped
                # label can pass that width by up to 0.35 inches each side. These leave it room.
                "nodesep": "0.75",
                "ranksep": "0.9",
                # D-055: a level can hold entities in different groups, which needs global ranks.
                # Only views with rows set it, so every other view keeps its layout.
                **({"newrank": "true"} if self.rows else {}),
            },
            node_attr={
                "fontname": FONT,
                "fontsize": LABEL_POINTS,
                "fontcolor": TEXT_COLOR,
                "imagepos": "tc",
                "imagescale": "true",
                "labelloc": "b",
            },
            edge_attr={"fontname": FONT, "fontsize": EDGE_POINTS, "fontcolor": TEXT_COLOR},
        )
        # `with Diagram` would run Graphviz on exit, outside the sandbox and its limits.
        setdiagram(diagram)
        try:
            self._emit(None, 0)
            self._legend()
            self._arrange()
            self._rows(diagram.dot)
            self._edges()
        finally:
            setcluster(None)
            setdiagram(None)
        return str(diagram.dot.source)

    def _emit(self, parent: str | None, depth: int) -> None:
        from diagrams import Cluster

        for node in self.members.get(parent, []):
            self._node(node)
        for group in self.children.get(parent, []):
            # Cluster names its subgraph after its label, so two groups sharing a display name
            # would silently merge. Naming it by ID and setting the label afterwards keeps them apart.
            cluster = Cluster(group.id, graph_attr=self._cluster_attributes(group, depth))
            cluster.dot.graph_attr["label"] = literal(group.lines, left=True)
            with cluster:
                self._emit(group.id, depth + 1)
                self._anchor(group)

    def _anchor(self, group: GraphGroup) -> None:
        from diagrams import Node

        # Graphviz drops an empty cluster, which would silently omit a selected boundary.
        empty = not self.members.get(group.id) and not self.children.get(group.id)
        if group.id in self.anchors or empty:
            self.drawn[group.id] = Node(
                "",
                nodeid=f"_anchor.{group.id}",
                id=f"anchor:{group.id}",
                shape="point",
                width="0.02",
                height="0.02",
                style="invis",
            )

    def _cluster_attributes(self, group: GraphGroup, depth: int) -> dict[str, str]:
        attributes = {
            "id": f"group:{group.id}",
            "fontname": FONT,
            "fontsize": LABEL_POINTS,
            "fontcolor": TEXT_COLOR,
            "style": "rounded",
            "pencolor": "#7B8894",
            "bgcolor": "white",
            "labelloc": "t",
            "margin": "36",
        }
        if self.graph.style == "provider":
            if group.entity != "provider":
                attributes["bgcolor"] = NESTED_FILLS[depth % len(NESTED_FILLS)]
            elif self.many_providers:
                attributes["bgcolor"] = PROVIDER_FILL[group.provider]
        if group.boundary_kind in SECURITY_KINDS:
            attributes |= {"style": "rounded,dashed", "pencolor": "#C0392B"}
        kind = group.boundary_kind or group.scope_kind
        if self.graph.style == "provider" and kind and (group.provider, kind) in GROUP_STYLES:
            pen, line, fill = GROUP_STYLES[group.provider, kind]
            attributes |= {"pencolor": pen, "style": line, "bgcolor": fill}
        return attributes

    def _node(self, node: GraphNode) -> None:
        from diagrams import Node

        label = literal(node.lines)
        common: dict[str, str] = {"id": f"node:{node.id}"}
        if node.icon:
            icon = self.icons[node.icon.reference]
            text = ICON_GAP_INCHES + LINE_INCHES * len(node.lines)
            # An edge meets a node at its middle. Left to right that would land on the label, which
            # runs wider than the node, so an equal space above keeps the middle on the icon.
            sideways = self.graph.direction == "LR"
            height = ICON_INCHES + text * (2 if sideways else 1)
            attributes = common | {
                "shape": "none",
                "image": f"icons/{icon.file_name}",
                "imagepos": "mc" if sideways else "tc",
                "width": f"{ICON_INCHES:.2f}",
                "height": f"{height:.2f}",
                "fixedsize": "true",
            }
            if node.fallback:
                # The generic symbol is blank, so this frame is what marks the node as a stand-in.
                attributes |= {
                    "shape": "box",
                    "style": "rounded,dashed",
                    "color": "#C0392B",
                    "width": f"{FALLBACK_WIDTH_INCHES:.2f}",
                }
            node_class = icon.node_class or Node
            self.drawn[node.id] = node_class(label, nodeid=node.id, **attributes)
            return
        attributes = common | {
            "shape": "box",
            "fixedsize": "false",
            "width": "1.0",
            "height": "0.4",
            "margin": "0.15,0.1",
            "labelloc": "c",
            "style": "rounded" if node.drawing == "labeled_node" else "rounded,dashed",
            "color": "#7B8894",
        }
        self.drawn[node.id] = Node(label, nodeid=node.id, **attributes)

    def _legend(self) -> None:
        from diagrams import Cluster, Edge, Node

        if not self.graph.legend:
            return
        cluster = Cluster(
            "_legend",
            graph_attr={
                "id": "legend",
                "fontname": FONT,
                "fontsize": LABEL_POINTS,
                "fontcolor": TEXT_COLOR,
                "style": "rounded",
                "pencolor": "#AEB6BE",
                "bgcolor": "white",
                "labelloc": "t",
            },
        )
        cluster.dot.graph_attr["label"] = literal(["Legend"])
        # Across the ranks a label overprints a vertical sample, so top-down samples lie flat in one
        # rank each, and invisible lines through both ends stack those ranks.
        flat = self.graph.direction == "TB"
        directed = {edge.kind for edge in self.graph.edges if edge.directed}
        with cluster:
            previous: tuple[Any, Any] | None = None
            for kind in self.graph.legend:
                color, style = EDGE_STYLES[kind]
                start = Node(
                    "", nodeid=f"_legend.{kind}.a", shape="point", width="0.05", color=color
                )
                end = Node("", nodeid=f"_legend.{kind}.b", shape="point", width="0.05", color=color)
                start.connect(
                    end,
                    Edge(
                        forward=kind in directed,
                        label=literal([kind]),
                        color=color,
                        style=style,
                        fontname=FONT,
                        fontsize=EDGE_POINTS,
                        **({"constraint": "false"} if flat else {}),
                    ),
                )
                if flat and previous is not None:
                    previous[0].connect(start, Edge(style="invis"))
                    previous[1].connect(end, Edge(style="invis"))
                previous = start, end

    def _inside(self, identifier: str, group: str) -> bool:
        parent: str | None
        if identifier in self.node_ids:
            parent = next(node.group for node in self.graph.nodes if node.id == identifier)
        else:
            parent = identifier
        while parent is not None:
            if parent == group:
                return True
            parent = self.groups[parent].parent if parent in self.groups else None
        return False

    def _touched(self) -> set[str]:
        """Everything an edge or a row reaches, with the groups around it: those have a rank."""
        touched: set[str] = set()
        nodes = {node.id: node for node in self.graph.nodes}
        ends: list[tuple[str, ...]] = [(edge.source, edge.target) for edge in self.graph.edges]
        for items in [*ends, *self.graph.bands, *self.graph.levels]:
            for endpoint in items:
                touched.add(endpoint)
                parent = nodes[endpoint].group if endpoint in nodes else endpoint
                while parent is not None:
                    touched.add(parent)
                    parent = self.groups[parent].parent if parent in self.groups else None
        return touched

    def _contents(self, parent: str | None) -> list[str]:
        nodes = [item.id for item in self.members.get(parent, [])]
        return [*nodes, *(item.id for item in self.children.get(parent, []))]

    def _representative(self, identifier: str) -> Any:
        """The node that stands for a group in layout: its own, or the first one inside it."""
        if identifier in self.drawn:
            return self.drawn[identifier]
        return self._representative(self._contents(identifier)[0])

    def _arrange(self) -> None:
        """Graphviz stacks unconnected members in one long column, so ask for rows of them instead."""
        from diagrams import Edge

        touched = self._touched()
        for parent in [None, *self.groups]:
            loose = [
                item for item in self._contents(parent) if item not in touched and item != parent
            ]
            width = math.ceil(math.sqrt(len(loose)))
            for start in range(0, len(loose), width or 1):
                for first, second in pairwise(loose[start : start + width]):
                    self._representative(first).connect(
                        self._representative(second), Edge(style="invis")
                    )

    def _rows(self, dot: Any) -> None:
        """D-055: each band is one rank, north to south, and each other level one rank of its own."""
        from diagrams import Edge, Node

        # Each band holds an invisible marker, and the layout lines run between markers only. A
        # second line between two entities, such as App A under the load balancer, would make dot
        # spread the pair apart and curve the drawn one.
        markers = [
            Node(
                "",
                nodeid=f"_band.{index}",
                id=f"band:{index}",
                shape="point",
                width="0.02",
                height="0.02",
                style="invis",
            )
            for index in range(len(self.graph.bands))
        ]
        for index, row in enumerate([*self.graph.bands, *self.graph.levels]):
            # A cluster name would draw a box; this only holds the rank.
            with dot.subgraph(name=f"_row.{index}") as level:
                level.attr(rank="same")
                if index < len(markers):
                    level.node(markers[index].nodeid)
                for identifier in row:
                    level.node(self.drawn[identifier].nodeid)
        for upper, lower in pairwise(markers):
            upper.connect(lower, Edge(style="invis"))
        if len(markers) < 2:
            return
        # The first band is the top row and the last the bottom one. With newrank, Graphviz 16.1
        # puts a loose node on the first rank even under rank=source, and a group's box then rises
        # above north. A weightless line from north and one to south holds every other node
        # between them without pulling it anywhere.
        banded = {identifier for band in self.graph.bands for identifier in band}
        for identifier, node in self.drawn.items():
            if identifier not in banded:
                markers[0].connect(node, Edge(style="invis", weight="0"))
                node.connect(markers[-1], Edge(style="invis", weight="0"))

    def _level(self, edge: GraphEdge) -> bool:
        """A line whose ends both sit in bands, or on one level, must not move either end."""
        source, target = self.rows.get(edge.source), self.rows.get(edge.target)
        if source is None or target is None:
            return False
        return source[0] == target[0] or (source[1] and target[1])

    def _edges(self) -> None:
        for edge in self.graph.edges:
            self._edge(edge)

    def _edge(self, edge: GraphEdge) -> None:
        from diagrams import Edge

        color, style = EDGE_STYLES[edge.kind]
        attributes: dict[str, Any] = {
            "id": f"edge:{edge.id}",
            "color": color,
            "style": style,
            "fontname": FONT,
            "fontsize": EDGE_POINTS,
        }
        level = self._level(edge)
        if edge.lines:
            # D-055: dot gives a label on a line within one rank a rank of its own, which bends the
            # line up through it. An outside label is placed after layout and keeps the line level.
            flat = level and self.rows[edge.source][0] == self.rows[edge.target][0]
            attributes["xlabel" if flat else "label"] = literal(edge.lines)
        if level:
            attributes["constraint"] = "false"
        # Clipping at a border needs the far end outside that group, or Graphviz drops the edge end.
        if edge.source in self.anchors and not self._inside(edge.target, edge.source):
            attributes["ltail"] = f"cluster_{edge.source}"
        if edge.target in self.anchors and not self._inside(edge.source, edge.target):
            attributes["lhead"] = f"cluster_{edge.target}"
        self.drawn[edge.source].connect(
            self.drawn[edge.target], Edge(forward=edge.directed, **attributes)
        )
