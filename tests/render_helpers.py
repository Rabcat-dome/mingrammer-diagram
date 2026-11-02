"""Shared helpers for the render lanes. Every model here is synthetic."""

import copy
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from cloud_architecture_diagrams.render import RenderResult, render_model
from cloud_architecture_diagrams.render.checks import SVG
from cloud_architecture_diagrams.render.limits import LIMITS, Limits
from cloud_architecture_diagrams.validation import Mode

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures"


def load(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((FIXTURES / name).read_text())
    return value


def encode(model: dict[str, Any]) -> bytes:
    return json.dumps(model, ensure_ascii=False).encode()


def render(
    model: dict[str, Any] | bytes,
    output: Path,
    *,
    mode: Mode = "strict",
    view: str | None = None,
    limits: Limits = LIMITS,
) -> RenderResult:
    payload = model if isinstance(model, bytes) else encode(model)
    return render_model(payload, str(output), mode=mode, view_id=view, limits=limits)


def codes(result: RenderResult) -> list[str]:
    return [item.code for item in result.diagnostics if item.severity == "error"]


def bundle_files(result: RenderResult) -> dict[str, bytes]:
    return {item.name: Path(item.path).read_bytes() for item in result.artifacts}


def manifest_of(result: RenderResult) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(bundle_files(result)["manifest.json"])
    return value


def graph_of(result: RenderResult) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(bundle_files(result)["view.json"])["graph"]
    return value


def svg_root(result: RenderResult) -> ET.Element:
    return ET.fromstring(bundle_files(result)["diagram.svg"])


def by_id(root: ET.Element) -> dict[str | None, ET.Element]:
    return {item.get("id"): item for item in root.iter(f"{{{SVG}}}g")}


def texts(element: ET.Element) -> list[str]:
    return [item.text or "" for item in element.iter(f"{{{SVG}}}text")]


def joined_text(element: ET.Element) -> str:
    return "".join("".join(texts(element)).split())


def tree(root: Path) -> list[str]:
    """Every name below an output root, including hidden scratch and stage directories."""
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def single_resource_model(name: str = "Application") -> dict[str, Any]:
    """The smallest drawable model, to vary one field at a time."""
    return {
        "schema_version": "1.0.0",
        "metadata": {"id": "probe", "title": "Probe", "environment": "test"},
        "scopes": [],
        "boundaries": [],
        "resources": [
            {
                "id": "app",
                "name": name,
                "provider": "external",
                "service_type": "external.system.other",
                "taxonomy": "external.entity",
            }
        ],
        "relationships": [],
        "views": [{"id": "main", "title": "Main", "entity_refs": ["app"]}],
    }


def amplified_model() -> dict[str, Any]:
    """Within 1 MiB, every node notes every long boundary name, multiplying the DOT source."""
    model = single_resource_model()
    boundaries = [
        {"id": f"b{index}", "name": "x" * 256, "provider": "external", "kind": "security_zone"}
        for index in range(100)
    ]
    identifiers = [item["id"] for item in boundaries]
    model["boundaries"] = boundaries
    model["resources"] = [
        model["resources"][0]
        | {
            "id": f"n{index}",
            "name": f"Node {index}",
            "placement": {"security_boundaries": identifiers},
        }
        for index in range(100)
    ]
    model["views"][0]["entity_refs"] = identifiers + [f"n{index}" for index in range(100)]
    return model


def large_model(entities: int, relationships: int) -> dict[str, Any]:
    """A connected view at a chosen size, for limits and for real engine time."""
    model = single_resource_model()
    prototype = model["resources"][0]
    model["resources"] = [
        copy.deepcopy(prototype) | {"id": f"n{index}", "name": f"Node {index}"}
        for index in range(entities)
    ]
    model["relationships"] = [
        {
            "id": f"r{index}",
            "source_ref": f"n{index % entities}",
            "target_ref": f"n{(index * 7 + 1) % entities}",
            "kind": "traffic",
        }
        for index in range(relationships)
    ]
    model["views"] = [
        {
            "id": "main",
            "title": "Main",
            "entity_refs": [f"n{index}" for index in range(entities)],
            "relationship_refs": [f"r{index}" for index in range(relationships)],
        }
    ]
    return model
