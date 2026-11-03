"""M3 render-smoke lane: FR-040..047, T-007 and M3-01..03. Output lands in reports/render-smoke."""

import base64
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from render_helpers import (
    FIXTURES,
    ROOT,
    bundle_files,
    by_id,
    codes,
    encode,
    graph_of,
    icon_model,
    joined_text,
    large_model,
    load,
    manifest_of,
    render,
    single_resource_model,
    svg_root,
    texts,
    tree,
)

from cloud_architecture_diagrams import __version__
from cloud_architecture_diagrams.catalog import catalog
from cloud_architecture_diagrams.cli import capabilities
from cloud_architecture_diagrams.models import Architecture
from cloud_architecture_diagrams.render import BUNDLE_FILES, RenderResult, exit_status
from cloud_architecture_diagrams.render.checks import DATA_PNG, HREF, SVG, check_png, png_scale
from cloud_architecture_diagrams.render.draw import EDGE_STYLES, build_dot, literal
from cloud_architecture_diagrams.render.errors import MESSAGES
from cloud_architecture_diagrams.render.execution import find_engine
from cloud_architecture_diagrams.render.graph import GraphIcon, map_view, visible_width, wrap
from cloud_architecture_diagrams.render.icons import verified_fonts, verified_icon, verified_icons
from cloud_architecture_diagrams.render.limits import LIMITS
from cloud_architecture_diagrams.validation import Mode

OUTPUT = ROOT / "reports/render-smoke"
SCENARIOS = [
    (path.relative_to(FIXTURES).as_posix(), view["id"])
    for path in sorted(
        [
            *FIXTURES.glob("*.json"),
            *(FIXTURES / "providers").glob("*.json"),
            *(FIXTURES / "kubernetes").glob("*.json"),
        ]
    )
    for view in json.loads(path.read_text())["views"]
]


@pytest.fixture(scope="session")
def smoke_root() -> Path:
    # The gate uploads reports, so these synthetic bundles stay inspectable after a run.
    shutil.rmtree(OUTPUT, ignore_errors=True)
    OUTPUT.mkdir(parents=True, mode=0o700)
    return OUTPUT


@pytest.fixture(scope="session")
def rendered(smoke_root: Path) -> dict[tuple[str, str], RenderResult]:
    return {
        (name, view): render((FIXTURES / name).read_bytes(), smoke_root, view=view)
        for name, view in SCENARIOS
    }


@pytest.mark.parametrize(("name", "view"), SCENARIOS, ids=["/".join(s) for s in SCENARIOS])
def test_every_fixture_view_produces_a_complete_bundle(
    rendered: dict[tuple[str, str], RenderResult], name: str, view: str
) -> None:
    result = rendered[(name, view)]
    assert result.rendered, [item.model_dump() for item in result.diagnostics]
    assert exit_status(result) == 0
    assert result.pending_checks == []
    assert result.bundle_path and Path(result.bundle_path).name == result.bundle_id
    files = bundle_files(result)
    assert sorted(files) == BUNDLE_FILES
    root = ET.fromstring(files["diagram.svg"])
    assert root.tag == f"{{{SVG}}}svg"
    width, height = check_png(files["diagram.png"], LIMITS)
    assert width > 100 and height > 100
    manifest = manifest_of(result)
    assert manifest["status"] == "complete"
    for artifact in result.artifacts:
        data = files[artifact.name]
        assert artifact.bytes == len(data)
        assert artifact.sha256 == hashlib.sha256(data).hexdigest()
    for artifact, entry in manifest["artifacts"].items():
        assert hashlib.sha256(files[artifact]).hexdigest() == entry["sha256"]
        assert len(files[artifact]) == entry["bytes"]
    assert "manifest.json" not in manifest["artifacts"]
    assert files["model.json"] == (FIXTURES / name).read_bytes()


def test_all_fixture_views_draw_every_catalog_type(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    # A type no render reaches could hide a broken representation until a user finds it.
    seen: set[str] = set()
    for result in rendered.values():
        graph = graph_of(result)
        seen |= {node["type_id"] for node in graph["nodes"]}
        seen |= {group["type_id"] for group in graph["groups"] if group["type_id"]}
    assert seen == set(catalog().records), set(catalog().records) ^ seen


def test_every_catalog_icon_resolves_to_its_locked_bytes() -> None:
    data = catalog()
    resolved = 0
    for record in data.records.values():
        item = record.representation
        if item.kind == "native_class":
            assert item.class_path and item.pack
            icon = GraphIcon(source="native_class", reference=item.class_path, pack=item.pack)
        elif item.asset:
            pack = data.assets[item.asset].pack
            icon = GraphIcon(source="custom_asset", reference=item.asset, pack=pack)
        else:
            continue
        assert verified_icon(icon, LIMITS).data
        resolved += 1
    assert resolved == sum(
        1
        for record in data.records.values()
        if record.representation.kind == "native_class" or record.representation.asset
    )
    assert resolved > 90


@pytest.mark.parametrize(("name", "view"), SCENARIOS, ids=["/".join(s) for s in SCENARIOS])
def test_each_record_is_drawn_through_its_representation(
    rendered: dict[tuple[str, str], RenderResult], name: str, view: str
) -> None:
    result = rendered[(name, view)]
    graph = graph_of(result)
    root = by_id(svg_root(result))
    records = catalog().records
    group_ids = {group["id"] for group in graph["groups"]}
    drawn_as_marker = {node["id"] for node in graph["nodes"] if node["id"] in group_ids}
    for node in graph["nodes"]:
        element = root[f"node:{node['id']}"]
        images = element.findall(f"{{{SVG}}}image")
        item = records[node["type_id"]].representation
        if item.kind == "native_class":
            assert node["icon"]["reference"] == item.class_path
            assert len(images) == 1
        elif item.kind == "custom_asset" or item.asset:
            assert node["icon"]["reference"] == item.asset
            asset = catalog().assets[item.asset or ""]
            assert "".join(asset.required_label.split()) in joined_text(element), node["id"]
            assert len(images) == 1
        else:
            assert item.kind in {"labeled_node", "labeled_boundary"}
            assert node["icon"] is None and not images
            assert node["drawing"] == (
                "labeled_node" if item.kind == "labeled_node" else "labeled_box"
            )
    for group in graph["groups"]:
        if group["entity"] != "provider":
            element = root[f"group:{group['id']}"]
            label = records[group["type_id"]].representation.label
            if label and group["id"] not in drawn_as_marker:
                assert "".join(label.split()) in joined_text(element), group["id"]


def test_every_selected_entity_and_relationship_is_in_the_image(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    for (name, view_id), result in rendered.items():
        model = load(name)
        view = next(item for item in model["views"] if item["id"] == view_id)
        elements = by_id(svg_root(result))
        graph = graph_of(result)
        drawn = {node["id"] for node in graph["nodes"]} | {g["id"] for g in graph["groups"]}
        assert set(view["entity_refs"]) <= drawn
        for identifier in view["entity_refs"]:
            assert f"node:{identifier}" in elements or f"group:{identifier}" in elements
        for identifier in view.get("relationship_refs", []):
            assert f"edge:{identifier}" in elements


def test_azure_icons_are_embedded_byte_for_byte_and_never_distorted(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    # Microsoft's terms forbid cropping, flipping, rotating or distorting these icons.
    result = rendered[("providers/azure.json", "detail")]
    lock = json.loads(
        (ROOT / "src/cloud_architecture_diagrams/catalog_data/native_icons.json").read_text()
    )["icons"]
    azure = {
        entry["sha256"] for entry in lock.values() if entry["pack"] == "azure-architecture-icons"
    }
    root = svg_root(result)
    found = set()
    for image in root.iter(f"{{{SVG}}}image"):
        href = image.get(HREF, "")
        assert href.startswith(DATA_PNG)
        digest = hashlib.sha256(base64.b64decode(href.removeprefix(DATA_PNG))).hexdigest()
        assert image.get("preserveAspectRatio", "").endswith(" meet")
        assert image.get("transform") is None
        found.add(digest)
    assert found & azure and found <= azure | {
        entry["sha256"] for entry in lock.values() if entry["pack"] != "azure-architecture-icons"
    }
    transforms = [e.get("transform") for e in root.iter() if e.get("transform")]
    assert len(transforms) == 1 and "rotate(0)" in str(transforms[0])


def test_manifest_records_what_fr_047_requires(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    result = rendered[("providers/aws.json", "detail")]
    manifest = manifest_of(result)
    payload = (FIXTURES / "providers/aws.json").read_bytes()
    assert manifest["package_version"] == __version__
    assert manifest["schema_version"] == "1.0.0"
    assert manifest["catalog_version"] == catalog().version
    assert manifest["input"] == {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    assert manifest["validation"]["mode"] == "strict"
    assert manifest["validation"]["scope"] == "core_catalog_provider"
    assert manifest["validation"]["draft"] is False
    assert re.fullmatch(r"[0-9.]+", manifest["engine"]["graphviz"])
    assert manifest["engine"]["diagrams"] == "0.25.1"
    assert manifest["engine"]["python_graphviz"]
    assert manifest["view"]["id"] == "detail"
    assert manifest["isolation"]["network"] == "denied"
    assert manifest["limits"]["wall_seconds"] == LIMITS.wall_seconds
    assert {font["family"] for font in manifest["fonts"]} == {"Noto Sans", "Noto Sans Thai"}
    assert {font["sha256"] for font in manifest["fonts"]} == {
        font.sha256 for font, _ in verified_fonts(LIMITS)
    }
    assert manifest["assets"] and all(item["sha256"] for item in manifest["assets"])
    assert all(item["source_version"] for item in manifest["assets"])
    assert manifest["png"]["width"] > 0


def test_fixture_views_keep_the_png_at_full_size(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    for result in rendered.values():
        assert manifest_of(result)["png"]["scale"] == 1.0
        assert "RENDER_PNG_SCALED" not in {item.code for item in result.diagnostics}


@pytest.mark.parametrize("entities", [123, 133, 140, 168, 197])
def test_a_tall_view_discloses_its_shrunken_png(entities: int, tmp_path: Path) -> None:
    # Cairo shrinks past 32767 pixels and exits 0, so only this comparison can say so. Sizes differ
    # because it truncates the other side, and 168 lands the long side on 32766.
    result = render(icon_model(entities, 0), tmp_path / "out")
    assert result.rendered and exit_status(result) == 0, codes(result)
    png = manifest_of(result)["png"]
    full_height = float(svg_root(result).get("height", "").removesuffix("pt")) * 96 / 72
    assert png["height"] in (32766, 32767)
    assert png["scale"] == pytest.approx(32767 / full_height, abs=0.001) and png["scale"] < 1
    assert [item.severity for item in result.diagnostics if item.code == "RENDER_PNG_SCALED"] == [
        "warning"
    ]
    recorded = json.loads(bundle_files(result)["diagnostics.json"])["diagnostics"]
    assert "RENDER_PNG_SCALED" in {item["code"] for item in recorded}


@pytest.mark.parametrize(
    ("width", "height"),
    [(341.37, 3.0), (347.0, 3.0), (356.5, 3.0), (3.0, 341.37), (3.0, 347.0), (3.0, 356.5)],
)
def test_png_scale_reads_real_cairo_output(width: float, height: float, tmp_path: Path) -> None:
    source = tmp_path / "shape.dot"
    source.write_text(
        f'digraph {{ a [shape=box, fixedsize=true, width={width}, height={height}, label=""]; }}'
    )
    svg, png = tmp_path / "shape.svg", tmp_path / "shape.png"
    subprocess.run(
        [find_engine().path, "-Tsvg", "-o", str(svg), "-Tpng", "-o", str(png), str(source)],
        capture_output=True,
        check=True,
        timeout=60,
    )
    size = check_png(png.read_bytes(), LIMITS)
    assert 32766 <= max(size) <= 32767
    assert 0.8 < png_scale(ET.fromstring(svg.read_bytes()), size, LIMITS) < 1


def test_a_large_icon_view_inside_the_limits_renders_at_full_size(tmp_path: Path) -> None:
    result = render(icon_model(150, 225), tmp_path / "out")
    assert result.rendered, codes(result)
    png = manifest_of(result)["png"]
    assert png["scale"] == 1.0 and png["width"] * png["height"] <= LIMITS.pixels


def test_bundle_is_portable_and_free_of_host_details(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    for result in rendered.values():
        for name, data in bundle_files(result).items():
            assert str(ROOT).encode() not in data, name
            assert str(Path.home()).encode() not in data, name
        svg = bundle_files(result)["diagram.svg"]
        # Portable means self-contained: nothing here may resolve through the file system.
        assert b"icons/" not in svg and b"<!DOCTYPE" not in svg
        assert not re.search(rb"xlink:href=\"(?!data:image/png;base64,)", svg)
        assert not any(key in manifest_of(result) for key in ("created", "timestamp", "date"))


def test_huawei_bundle_carries_the_private_use_limit(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    result = rendered[("providers/huawei.json", "detail")]
    rights = manifest_of(result)["rights"]
    assert rights["private_use_only"] is True
    assert rights["blockers"] == ["O-002"]
    assert "D-018" in rights["distribution_limit"]
    assert "not cleared" in rights["distribution_limit"]
    pack = next(item for item in rights["packs"] if item["status"] == "private_use_only")
    assert pack["id"] == "huawei-latam-color" and pack["license"] is None
    assert pack["rights_basis"] == "owner_risk_acceptance"
    assert result.rights == rights
    # An image can leave its bundle, so the limit is drawn into it as well.
    canvas = by_id(svg_root(result))["graph:root"]
    text = " ".join(item.text or "" for item in canvas.findall(f"{{{SVG}}}text"))
    assert "private personal use only" in text
    assert "ASSET_PRIVATE_USE_ONLY" in {item.code for item in result.diagnostics}


def test_a_huawei_boundary_icon_alone_still_carries_the_limit(tmp_path: Path) -> None:
    # Only the VPC boundary uses an asset here, and a service-only check would miss it.
    model = {
        "schema_version": "1.0.0",
        "metadata": {"id": "vpc-only", "title": "VPC only", "environment": "test"},
        "boundaries": [{"id": "net", "name": "Main VPC", "provider": "huawei", "kind": "network"}],
        "views": [{"id": "main", "title": "Main", "entity_refs": ["net"]}],
    }
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    rights = manifest_of(result)["rights"]
    assert rights["private_use_only"] is True and rights["blockers"] == ["O-002"]
    assert by_id(svg_root(result))["node:net"].findall(f"{{{SVG}}}image")
    assert "Main VPC" in texts(by_id(svg_root(result))["group:net"])


def test_other_bundles_claim_no_private_use_limit(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    rights = manifest_of(rendered[("providers/aws.json", "detail")])["rights"]
    assert rights["private_use_only"] is False and rights["distribution_limit"] is None
    assert rights["blockers"] == [] and "aws-architecture-icons" in {
        item["id"] for item in rights["packs"]
    }


def test_a_view_that_excludes_huawei_icons_claims_no_limit(tmp_path: Path) -> None:
    # Rights follow the image rather than the model, so the model-level warning can stay alone.
    model = load("providers/huawei.json")
    model["views"][0]["entity_refs"] = ["region"] if "region" in str(model["boundaries"]) else []
    boundary = next(item for item in model["boundaries"] if item["kind"] == "region")
    model["views"][0]["entity_refs"] = [boundary["id"]]
    model["views"][0]["relationship_refs"] = []
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    assert manifest_of(result)["rights"]["private_use_only"] is False
    assert "ASSET_PRIVATE_USE_ONLY" in {item.code for item in result.diagnostics}


def test_drawio_symbols_keep_their_attribution(
    rendered: dict[tuple[str, str], RenderResult],
) -> None:
    result = rendered[("providers/onprem.json", "detail")]
    pack = next(
        item
        for item in manifest_of(result)["rights"]["packs"]
        if item["id"] == "drawio-network-2018"
    )
    assert "CC BY 4.0" in pack["attribution"] and pack["license"] == "CC-BY-4.0"
    canvas = by_id(svg_root(result))["graph:root"]
    assert "CCBY4.0" in joined_text(canvas)


def test_strict_mode_rejects_an_unknown_type_and_draws_nothing(tmp_path: Path) -> None:
    model = single_resource_model()
    model["resources"][0]["service_type"] = "external.system.madeup"
    output = tmp_path / "out"
    result = render(model, output)
    assert not result.rendered and not result.artifacts and result.bundle_path is None
    assert "CATALOG_TYPE_UNKNOWN" in codes(result)
    assert exit_status(result) == 2
    assert result.pending_checks == ["render"]
    assert not output.exists()


def test_lenient_mode_draws_a_marked_draft_and_keeps_provider_type_and_label(
    tmp_path: Path,
) -> None:
    model = single_resource_model("Legacy billing")
    model["resources"][0]["service_type"] = "external.system.madeup"
    result = render(model, tmp_path / "out", mode="lenient")
    assert result.rendered, codes(result)
    assert result.draft is True and exit_status(result) == 0
    warnings = {item.code: item for item in result.diagnostics if item.severity == "warning"}
    assert "CATALOG_TYPE_UNKNOWN" in warnings
    assert warnings["RENDER_GENERIC_FALLBACK"].entity_id == "app"
    manifest = manifest_of(result)
    assert manifest["validation"]["draft"] is True and manifest["validation"]["mode"] == "lenient"
    assert manifest["validation"]["generic_fallbacks"] == [
        {
            "entity_id": "app",
            "provider": "external",
            "service_type": "external.system.madeup",
            "label": "Legacy billing",
        }
    ]
    root = by_id(svg_root(result))
    node = joined_text(root["node:app"])
    for retained in ("Legacybilling", "Unknowntype", "external:external.system.madeup"):
        assert retained in node
    assert "DRAFT" in joined_text(root["graph:root"])
    [icon] = manifest["assets"]
    assert icon["reference"] == catalog().fallback.class_path
    assert icon["pack"] == "diagrams-generic"


def test_lenient_fallback_never_borrows_a_provider_icon(tmp_path: Path) -> None:
    # An unknown AWS type stays AWS and stays generic; T-007 forbids provider substitution.
    model = load("providers/aws.json")
    resource = next(
        item for item in model["resources"] if item["service_type"] == "aws.compute.ec2"
    )
    resource["service_type"] = "aws.compute.madeup"
    result = render(model, tmp_path / "out", mode="lenient")
    assert result.rendered, codes(result)
    graph = graph_of(result)
    node = next(item for item in graph["nodes"] if item["id"] == resource["id"])
    assert node["provider"] == "aws" and node["type_id"] == "aws.compute.madeup"
    assert node["fallback"] is True
    assert node["icon"]["reference"] == catalog().fallback.class_path
    assert node["group"] != "_provider.external"


def test_an_unknown_cluster_type_draws_as_a_node_and_cannot_lose_its_members(
    tmp_path: Path,
) -> None:
    # Kubernetes context would make it a group, but only a catalog type can hold other entities.
    model = kubernetes_model()
    cluster = next(item for item in model["resources"] if item["id"] == "cluster")
    cluster["service_type"] = "k8s.madeup"
    result = render(model, tmp_path / "out", mode="lenient", view="by-namespace")
    assert result.rendered, codes(result)
    graph = graph_of(result)
    assert "cluster" not in {group["id"] for group in graph["groups"]}
    element = by_id(svg_root(result))
    assert "node:cluster" in element and "node:pod-a" in element
    assert parent_chain(graph, "pod-a") == ["namespace"]


def test_lenient_rendering_of_a_clean_model_is_still_marked_draft(tmp_path: Path) -> None:
    result = render((FIXTURES / "core-valid.json").read_bytes(), tmp_path / "out", mode="lenient")
    assert result.rendered and result.draft
    assert manifest_of(result)["validation"]["generic_fallbacks"] == []
    assert "DRAFT" in joined_text(by_id(svg_root(result))["graph:root"])
    assert "RENDER_GENERIC_FALLBACK" not in {item.code for item in result.diagnostics}


def test_lenient_mode_still_rejects_every_other_error(tmp_path: Path) -> None:
    model = single_resource_model()
    model["resources"][0]["provider"] = "aws"
    output = tmp_path / "out"
    result = render(model, output, mode="lenient")
    assert not result.rendered and codes(result) and not output.exists()


def test_a_blocked_type_takes_no_substitute_in_either_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    data = catalog()
    record = data.records["external.system.other"]
    blocked = record.model_copy(
        update={
            "representation": record.representation.model_copy(
                update={"kind": "blocked", "blocker": "O-002", "pack": "huawei-cloud-icons"}
            ),
            "status": "semantics_only",
        }
    )
    monkeypatch.setitem(data.records, record.id, blocked)
    modes: tuple[Mode, ...] = ("strict", "lenient")
    for mode in modes:
        output = tmp_path / mode
        result = render(single_resource_model(), output, mode=mode)
        assert result.valid and not result.rendered
        assert codes(result) == ["RENDER_TYPE_BLOCKED"]
        assert exit_status(result) == 2 and not output.exists()
        # Validation warned that the type has no icon, and rendering must not contradict that.
        assert "ICON_UNAVAILABLE" in {item.code for item in result.diagnostics}


def kubernetes_model() -> dict[str, Any]:
    model = load("kubernetes-valid.json")
    pod = next(item for item in model["resources"] if item["id"] == "pod-b")
    del pod["kubernetes"]["node_ref"]
    every = [item["id"] for item in model["resources"]]
    model["views"] = [
        {"id": "overview", "title": "Overview", "entity_refs": ["cluster", "namespace", "pool"]},
        {"id": "by-namespace", "title": "Logical", "entity_refs": every, "grouping": "namespace"},
        {"id": "by-node", "title": "Placement", "entity_refs": every, "grouping": "node"},
    ]
    return model


def parent_chain(graph: dict[str, Any], identifier: str) -> list[str]:
    groups = {group["id"]: group for group in graph["groups"]}
    node = next(item for item in graph["nodes"] if item["id"] == identifier)
    chain = []
    current = node["group"]
    while current is not None:
        chain.append(current)
        current = groups[current]["parent"]
    return chain


def test_kubernetes_overview_and_details_select_separately_with_stable_ids(
    tmp_path: Path,
) -> None:
    model = kubernetes_model()
    output = tmp_path / "out"
    results = {view["id"]: render(model, output, view=view["id"]) for view in model["views"]}
    assert all(result.rendered for result in results.values())
    assert len({result.bundle_id for result in results.values()}) == 3
    overview = graph_of(results["overview"])
    assert {group["id"] for group in overview["groups"]} >= {"cluster"}
    assert "pod-a" not in {node["id"] for node in overview["nodes"]}
    assert results["overview"].excluded_ids
    for name in ("by-namespace", "by-node"):
        element = by_id(svg_root(results[name]))
        assert "node:pod-a" in element and "node:service" in element
    assert manifest_of(results["by-namespace"])["input"] == manifest_of(results["by-node"])["input"]


def test_namespace_grouping_does_not_assign_pods_to_nodes(tmp_path: Path) -> None:
    result = render(kubernetes_model(), tmp_path / "out", view="by-namespace")
    graph = graph_of(result)
    assert parent_chain(graph, "pod-a") == ["namespace", "cluster"]
    assert parent_chain(graph, "pod-b") == ["namespace", "cluster"]
    assert parent_chain(graph, "node-a") == ["pool", "cluster"]
    element = by_id(svg_root(result))
    # Worker placement survives as a stated fact, and missing placement stays unspecified.
    assert "node:node-a" in joined_text(element["node:pod-a"])
    assert "node:unspecified" in joined_text(element["node:pod-b"])
    assert "node" in next(n for n in graph["nodes"] if n["id"] == "pod-a")["memberships"]
    assert "node" not in next(n for n in graph["nodes"] if n["id"] == "pod-b")["memberships"]


def test_node_grouping_places_only_declared_pods_and_keeps_the_namespace(tmp_path: Path) -> None:
    result = render(kubernetes_model(), tmp_path / "out", view="by-node")
    graph = graph_of(result)
    assert parent_chain(graph, "pod-a") == ["node-a", "pool", "cluster"]
    # pod-b declares no Node, so it must not sit inside one.
    assert not {"node-a", "node-b"} & set(parent_chain(graph, "pod-b"))
    element = by_id(svg_root(result))
    assert "namespace:namespace" in joined_text(element["node:pod-a"])
    assert "node:unspecified" in joined_text(element["node:pod-b"])
    # A Node stays drawn through its own native class, as a marker inside its group.
    assert element["node:node-a"].findall(f"{{{SVG}}}image")
    assert "group:node-a" in element


def boundaries_model() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "metadata": {"id": "groups", "title": "Groups", "environment": "test"},
        "scopes": [{"id": "account", "name": "Same name", "provider": "aws", "kind": "account"}],
        "boundaries": [
            {
                "id": "vpc-a",
                "name": "Same name",
                "provider": "aws",
                "kind": "network",
                "scope_refs": ["account"],
            },
            {
                "id": "vpc-b",
                "name": "Same name",
                "provider": "aws",
                "kind": "network",
                "scope_refs": ["account"],
            },
        ],
        "resources": [
            {
                "id": "vm-a",
                "name": "VM A",
                "provider": "aws",
                "service_type": "aws.compute.ec2",
                "taxonomy": "compute.vm",
                "placement": {
                    "scope_refs": ["account"],
                    "network_attachments": [{"network_ref": "vpc-a"}],
                },
            },
            {
                "id": "vm-b",
                "name": "VM B",
                "provider": "aws",
                "service_type": "aws.compute.ec2",
                "taxonomy": "compute.vm",
                "placement": {"network_attachments": [{"network_ref": "vpc-b"}]},
            },
        ],
        "relationships": [
            {
                "id": "peer",
                "source_ref": "vpc-a",
                "target_ref": "vpc-b",
                "kind": "peering",
                "direction": "undirected",
                "label": "Peering link",
            },
            {
                "id": "app",
                "source_ref": "vm-a",
                "target_ref": "vm-b",
                "kind": "traffic",
                "protocol": "TCP 443",
                "security": "TLS",
            },
        ],
        "views": [
            {
                "id": "main",
                "title": "Main",
                "entity_refs": ["account", "vpc-a", "vpc-b", "vm-a", "vm-b"],
                "relationship_refs": ["peer", "app"],
            }
        ],
    }


def test_groups_with_one_display_name_stay_separate(tmp_path: Path) -> None:
    # diagrams names a subgraph after its label, which would merge these into one box.
    result = render(boundaries_model(), tmp_path / "out")
    assert result.rendered, codes(result)
    element = by_id(svg_root(result))
    assert {"group:account", "group:vpc-a", "group:vpc-b"} <= set(element)
    graph = graph_of(result)
    assert parent_chain(graph, "vm-a")[0] == "vpc-a"
    assert parent_chain(graph, "vm-b")[0] == "vpc-b"


def test_a_relationship_between_groups_is_drawn_to_their_borders(tmp_path: Path) -> None:
    model = boundaries_model()
    graph = map_view(Architecture.model_validate(model), _view(model), "strict", LIMITS)
    dot = build_dot(graph, verified_icons(graph, LIMITS))
    assert "compound=true" in dot
    assert 'lhead=cluster_"' not in dot
    assert re.search(r'lhead="?cluster_vpc-b"?', dot) and re.search(r'ltail="?cluster_vpc-a"?', dot)
    assert re.search(r"dir=none", dot)
    result = render(model, tmp_path / "out")
    element = by_id(svg_root(result))
    assert "Peeringlink" in joined_text(element["edge:peer"])
    assert "TCP443" in joined_text(element["edge:app"])
    assert "TLS" in joined_text(element["edge:app"])


def _view(model: dict[str, Any]) -> Any:
    return Architecture.model_validate(model).views[0]


def test_an_empty_group_is_still_drawn(tmp_path: Path) -> None:
    # Graphviz drops a cluster with no nodes, which would hide a selected boundary (NFR-006).
    model = boundaries_model()
    model["views"][0]["entity_refs"] = ["vpc-a"]
    model["views"][0]["relationship_refs"] = []
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    assert "Samename" in joined_text(by_id(svg_root(result))["group:vpc-a"])


@pytest.mark.parametrize(
    ("grouping", "groups"),
    [
        ("none", set()),
        ("scope", {"account"}),
        ("network", {"vpc-a", "vpc-b"}),
        ("physical", set()),
        ("namespace", set()),
        ("node", set()),
    ],
)
def test_each_grouping_nests_only_its_own_dimension(
    tmp_path: Path, grouping: str, groups: set[str]
) -> None:
    model = boundaries_model()
    model["views"][0]["grouping"] = grouping
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    graph = graph_of(result)
    assert {group["id"] for group in graph["groups"]} == groups
    # An entity that is not a group here is still drawn, so a grouping cannot hide it.
    element = by_id(svg_root(result))
    for identifier in model["views"][0]["entity_refs"]:
        assert f"node:{identifier}" in element or f"group:{identifier}" in element
    assert "edge:peer" in element and "edge:app" in element


def test_a_membership_that_nesting_cannot_show_stays_a_note(tmp_path: Path) -> None:
    # Graphviz can place a node in one cluster, but ownership and network both stay true.
    model = boundaries_model()
    model["views"][0]["grouping"] = "network"
    result = render(model, tmp_path / "out")
    node = joined_text(by_id(svg_root(result))["node:vm-a"])
    assert "scope:Samename" in node
    graph = graph_of(result)
    assert next(n for n in graph["nodes"] if n["id"] == "vm-a")["memberships"] == {
        "network": ["vpc-a"],
        "scope": ["account"],
    }


def test_multiple_subnets_nest_under_their_network_and_are_named(tmp_path: Path) -> None:
    result = render((FIXTURES / "providers/aws.json").read_bytes(), tmp_path / "out")
    graph = graph_of(result)
    model = load("providers/aws.json")
    balancer = next(
        item
        for item in model["resources"]
        if item["service_type"] == "aws.network.application_load_balancer"
    )
    attachment = balancer["placement"]["network_attachments"][0]
    assert len(attachment["subnet_refs"]) >= 2
    chain = parent_chain(graph, balancer["id"])
    assert attachment["network_ref"] in chain
    assert not set(attachment["subnet_refs"]) & set(chain)
    text = joined_text(by_id(svg_root(result))[f"node:{balancer['id']}"])
    assert "subnet:" in text


def test_direction_legend_and_style_stay_bounded_view_choices() -> None:
    model = boundaries_model()
    view = model["views"][0]
    view |= {"direction": "TB", "legend": False, "style": "neutral"}
    parsed = Architecture.model_validate(model)
    graph = map_view(parsed, parsed.views[0], "strict", LIMITS)
    dot = build_dot(graph, verified_icons(graph, LIMITS))
    assert "rankdir=TB" in dot and "_legend" not in dot
    assert "#FFF8EE" not in dot
    view |= {"direction": "LR", "legend": True, "style": "provider"}
    parsed = Architecture.model_validate(model)
    graph = map_view(parsed, parsed.views[0], "strict", LIMITS)
    dot = build_dot(graph, verified_icons(graph, LIMITS))
    assert "rankdir=LR" in dot and "_legend" in dot and "#FFF8EE" in dot


def test_every_relationship_kind_has_one_edge_style(tmp_path: Path) -> None:
    model = boundaries_model()
    model["relationships"] = [
        {"id": f"edge-{kind}", "source_ref": "vm-a", "target_ref": "vm-b", "kind": kind}
        for kind in EDGE_STYLES
    ]
    model["views"][0]["relationship_refs"] = [item["id"] for item in model["relationships"]]
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    assert set(graph_of(result)["legend"]) == set(EDGE_STYLES)
    legend = by_id(svg_root(result))["legend"]
    assert "Legend" in texts(legend)


def test_thai_and_english_labels_survive_literally(tmp_path: Path) -> None:
    name = "ระบบงานหลัก Payment สถาปัตยกรรมภาษาไทยที่ยาวมาก"
    model = single_resource_model(name)
    model["metadata"]["title"] = "สถาปัตยกรรม"
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    element = by_id(svg_root(result))
    assert "".join(name.split()) in joined_text(element["node:app"])
    assert "สถาปัตยกรรม" in joined_text(element["graph:root"])
    assert json.loads(bundle_files(result)["model.json"])["resources"][0]["name"] == name


def test_wrapping_never_splits_a_mark_from_its_base() -> None:
    text = "ที่" * 30
    lines = wrap(text, 20)
    assert "".join(lines) == text
    assert all(visible_width(line) <= 20 for line in lines)
    assert not any(line[0] in "ี่" for line in lines)
    assert wrap("one two", 20) == ["one two"]
    assert wrap("", 20) == [""]


def test_identical_input_renders_identical_output(tmp_path: Path) -> None:
    # NFR-001: only the collision-safe bundle name may differ between two runs.
    payload = (FIXTURES / "providers/hybrid.json").read_bytes()
    first = bundle_files(render(payload, tmp_path / "out"))
    second = bundle_files(render(payload, tmp_path / "out"))
    for name in ("diagram.svg", "diagram.png", "view.json", "diagnostics.json", "model.json"):
        assert first[name] == second[name], name
    one, two = json.loads(first["manifest.json"]), json.loads(second["manifest.json"])
    assert one.pop("bundle_id") != two.pop("bundle_id")
    assert one == two


def test_the_normalized_graph_is_stable_across_runs_and_hosts(tmp_path: Path) -> None:
    parsed = Architecture.model_validate(load("providers/aws.json"))
    first = map_view(parsed, parsed.views[0], "strict", LIMITS).model_dump(mode="json")
    second = map_view(parsed, parsed.views[0], "strict", LIMITS).model_dump(mode="json")
    assert first == second
    assert str(ROOT) not in json.dumps(first)


def test_console_script_renders_from_stdin_and_reports_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "out"
    payload = (FIXTURES / "core-valid.json").read_bytes()
    result = subprocess.run(
        ["cloud-diagrams", "render", "--output", str(output)],
        input=payload,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0 and not result.stderr
    report = json.loads(result.stdout)
    assert report["rendered"] is True and report["pending_checks"] == []
    for artifact in report["artifacts"]:
        path = Path(artifact["path"])
        assert path.is_file() and path.stat().st_size == artifact["bytes"]
    assert sorted(item["name"] for item in report["artifacts"]) == BUNDLE_FILES
    assert not [name for name in tree(output) if name.startswith(".")]


def test_console_script_exit_codes(tmp_path: Path) -> None:
    def run(payload: bytes, *arguments: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["cloud-diagrams", "render", *arguments], input=payload, capture_output=True, timeout=60
        )

    output = str(tmp_path / "out")
    good = (FIXTURES / "core-valid.json").read_bytes()
    invalid = run(b"{}", "--output", output)
    assert invalid.returncode == 2 and json.loads(invalid.stdout)["rendered"] is False
    too_large = run(encode(large_model(LIMITS.view_entities + 1, 0)), "--output", output)
    assert too_large.returncode == 2
    assert [d["code"] for d in json.loads(too_large.stdout)["diagnostics"]] == [
        "RENDER_VIEW_TOO_LARGE"
    ]
    assert run(good).returncode == 64
    assert run(good, "--output", output, "--mode", "nope").returncode == 64
    missing_view = run(good, "--output", output, "--view", "absent")
    assert missing_view.returncode == 2
    assert "VIEW_NOT_FOUND" in {d["code"] for d in json.loads(missing_view.stdout)["diagnostics"]}
    target = tmp_path / "a-file"
    target.write_text("")
    failed = run(good, "--output", str(target))
    assert failed.returncode == 4
    assert [d["code"] for d in json.loads(failed.stdout)["diagnostics"]] == [
        "RENDER_OUTPUT_PATH_UNSAFE"
    ]


def test_capabilities_describe_the_renderer() -> None:
    report = capabilities()
    assert "render" in report["commands"]  # type: ignore[operator]
    assert report["render_available"] is True
    assert report["pending_checks"] == []
    details = report["render"]
    assert isinstance(details, dict)
    assert details["formats"] == ["svg", "png"] and details["host_blockers"] == []
    assert details["bundle"] == BUNDLE_FILES


def test_validation_alone_still_leaves_rendering_pending() -> None:
    from cloud_architecture_diagrams.validation import validate_json

    result = validate_json((FIXTURES / "core-valid.json").read_bytes())
    assert result.pending_checks == ["render"]


def test_validation_and_discovery_do_not_import_the_drawing_library() -> None:
    # The CLI answers these without touching Graphviz or loading the icon package.
    code = (
        "import sys, json;"
        "from cloud_architecture_diagrams import cli;"
        "print(json.dumps(sorted(m for m in sys.modules if m.split('.')[0] in"
        " ('diagrams', 'graphviz'))))"
    )
    from sys import executable

    output = subprocess.check_output([executable, "-c", code])
    assert json.loads(output) == []


def test_every_render_code_is_exercised_by_a_test() -> None:
    sources = "".join(
        (ROOT / "tests" / name).read_text()
        for name in ("test_render_smoke.py", "test_render_security.py")
    )
    missing = [code for code in MESSAGES if f'"{code}"' not in sources]
    assert not missing, missing


def test_literal_keeps_markup_out_of_dot() -> None:
    assert str(literal(["a&b", 'c"d', "e\\N"])) == 'a&amp;b\\nc"d\\ne\\\\N'


def test_font_license_notices_ship_with_the_fonts() -> None:
    package = ROOT / "src/cloud_architecture_diagrams"
    for font in catalog().manifest.fonts:
        assert (package / font.license_path).read_text().startswith("Copyright")
