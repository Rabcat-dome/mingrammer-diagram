"""RenderGraph to DOT through controlled `diagrams` classes. Nothing here runs Graphviz."""

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
        # Edges need a node to end on, and a group without its own marker has none.
        self.anchors = {
            endpoint
            for edge in graph.edges
            for endpoint in (edge.source, edge.target)
            if endpoint not in self.node_ids
        }
        self.drawn: dict[str, Any] = {}

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
                "pad": "0.3",
                "splines": "spline",
                "compound": "true",
                # Icon nodes keep a fixed width so that their icon keeps its size, and a wrapped
                # label can pass that width by up to 0.35 inches each side. These leave it room.
                "nodesep": "0.75",
                "ranksep": "0.9",
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
            "margin": "28",
        }
        if self.graph.style == "provider":
            attributes["bgcolor"] = (
                PROVIDER_FILL[group.provider]
                if group.entity == "provider"
                else NESTED_FILLS[depth % len(NESTED_FILLS)]
            )
        if group.boundary_kind in SECURITY_KINDS:
            attributes |= {"style": "rounded,dashed", "pencolor": "#C0392B"}
        return attributes

    def _node(self, node: GraphNode) -> None:
        from diagrams import Node

        label = literal(node.lines)
        common: dict[str, str] = {"id": f"node:{node.id}"}
        if node.icon:
            icon = self.icons[node.icon.reference]
            height = ICON_INCHES + ICON_GAP_INCHES + LINE_INCHES * len(node.lines)
            attributes = common | {
                "shape": "none",
                "image": f"icons/{icon.file_name}",
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
        with cluster:
            for kind in self.graph.legend:
                color, style = EDGE_STYLES[kind]
                start = Node(
                    "", nodeid=f"_legend.{kind}.a", shape="point", width="0.05", color=color
                )
                end = Node("", nodeid=f"_legend.{kind}.b", shape="point", width="0.05", color=color)
                start.connect(
                    end,
                    Edge(
                        forward=True,
                        label=literal([kind]),
                        color=color,
                        style=style,
                        fontname=FONT,
                        fontsize=EDGE_POINTS,
                    ),
                )

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
        if edge.lines:
            attributes["label"] = literal(edge.lines)
        # Clipping at a border needs the far end outside that group, or Graphviz drops the edge end.
        if edge.source in self.anchors and not self._inside(edge.target, edge.source):
            attributes["ltail"] = f"cluster_{edge.source}"
        if edge.target in self.anchors and not self._inside(edge.source, edge.target):
            attributes["lhead"] = f"cluster_{edge.target}"
        self.drawn[edge.source].connect(
            self.drawn[edge.target], Edge(forward=edge.directed, **attributes)
        )
