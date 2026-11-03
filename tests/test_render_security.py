"""M3 render-security lane: T-009, FR-045, NFR-002, NFR-003, NFR-006, NFR-009 and NFR-010."""

import base64
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
import zlib
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from render_helpers import (
    FIXTURES,
    amplified_model,
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

import cloud_architecture_diagrams.catalog as catalog_module
import cloud_architecture_diagrams.render as renderer
from cloud_architecture_diagrams.catalog import catalog
from cloud_architecture_diagrams.models import MAX_INPUT_BYTES, Architecture
from cloud_architecture_diagrams.render import checks, execution, icons
from cloud_architecture_diagrams.render.bundle import OutputRoot
from cloud_architecture_diagrams.render.draw import build_dot
from cloud_architecture_diagrams.render.errors import RenderFailure
from cloud_architecture_diagrams.render.execution import (
    Engine,
    engine_environment,
    find_engine,
    host_blockers,
    limited,
    run_bounded,
    sandboxed,
)
from cloud_architecture_diagrams.render.graph import GraphIcon, Mapper, map_view
from cloud_architecture_diagrams.render.icons import PNG_SIGNATURE, verified_icon, verified_icons
from cloud_architecture_diagrams.render.limits import LIMITS, Limits

GOOD = (FIXTURES / "core-valid.json").read_bytes()
HOSTILE_TEXT = [
    '<TABLE><TR><TD><IMG SRC="/etc/passwd"/></TD></TR></TABLE>',
    "<b>bold</b>",
    '"]; injected [image="/etc/passwd"]; x [label="',
    '\\"]; injected [label=\\"',
    "\\N \\G \\E \\T \\H \\L \\l \\r \\n",
    "trailing backslash \\",
    "</text><script>alert(1)</script><text>",
    '"><svg onload="alert(1)">',
    '<image xlink:href="http://attacker.test/x.png"/>',
    "&lt;script&gt; &#60;script&#62; &amp; R&D; &unknown;",
    "javascript:alert(1) https://attacker.test/x file:///etc/passwd",
    "__import__('os').system('touch marker')",
    "${HOME} $(touch marker) `touch marker`",
    "subgraph cluster_x { a -> b } // /* comment",
    "]]> <!-- <!DOCTYPE x [<!ENTITY y 'z'>]> <?xml-stylesheet href='x'?>",
    "url(#x) style=fill:url(http://attacker.test)",
    "‮​ RTL and zero-width",
]


def fail_if_called(*_: object, **__: object) -> None:
    raise AssertionError("invalid input reached the renderer")


@pytest.fixture
def forbid_rendering(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("find_engine", "map_view", "build_dot", "OutputRoot", "verified_icons"):
        monkeypatch.setattr(renderer, name, fail_if_called)


def hostile_everywhere(text: str) -> dict[str, Any]:
    model = single_resource_model(text)
    model["metadata"] |= {"title": text, "environment": text}
    model["resources"].append(
        {
            "id": "other",
            "name": text,
            "provider": "external",
            "service_type": "external.system.other",
            "taxonomy": "external.entity",
        }
    )
    model["boundaries"] = [
        {"id": "zone", "name": text, "provider": "external", "kind": "security_zone"}
    ]
    model["relationships"] = [
        {
            "id": "link",
            "source_ref": "app",
            "target_ref": "other",
            "kind": "traffic",
            "label": text,
            "protocol": text,
            "purpose": text,
            "security": text,
        }
    ]
    model["views"] = [
        {
            "id": "main",
            "title": text,
            "entity_refs": ["app", "other", "zone"],
            "relationship_refs": ["link"],
        }
    ]
    return model


@pytest.mark.parametrize("text", HOSTILE_TEXT)
def test_hostile_text_stays_literal_text(
    text: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    model = hostile_everywhere(text)
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    root = svg_root(result)
    element = by_id(root)
    squeezed = "".join(text.split())
    for identifier in ("node:app", "node:other", "group:zone", "edge:link", "graph:root"):
        assert squeezed in joined_text(element[identifier]), identifier
    # Only the elements the graph asked for exist, with no attribute a label could have added.
    names = {item.tag.rpartition("}")[2] for item in root.iter()}
    assert names <= {"svg", "g", "title", "polygon", "path", "ellipse", "text"}
    assert not list(root.iter(f"{{{checks.SVG}}}image"))
    expected = {"graph:root", "node:app", "node:other", "group:zone", "edge:link"}
    assert expected <= {item.get("id") for item in root.iter()}
    assert not (tmp_path / "marker").exists()
    assert not any("injected" == item.get("id") for item in root.iter())


@pytest.mark.parametrize("text", HOSTILE_TEXT)
def test_hostile_text_cannot_add_to_the_dot_source(text: str) -> None:
    model = hostile_everywhere(text)
    parsed = Architecture.model_validate(model)
    graph = map_view(parsed, parsed.views[0], "strict", LIMITS)
    dot = build_dot(graph, verified_icons(graph, LIMITS))
    # An HTML string would reach Graphviz unquoted, so no label may be written as one.
    assert "label=<" not in dot
    # Graphviz itself reads it back: whatever the label says, the structure is only what was drawn.
    parsed_dot = json.loads(
        subprocess.run(
            [find_engine().path, "-Tjson0"],
            input=dot.encode(),
            capture_output=True,
            timeout=30,
            check=True,
        ).stdout
    )
    assert {item["name"] for item in parsed_dot["objects"]} == {
        "app",
        "other",
        "_anchor.zone",
        "_legend.traffic.a",
        "_legend.traffic.b",
        "cluster__provider.external",
        "cluster_zone",
        "cluster__legend",
    }
    assert len(parsed_dot["edges"]) == 2
    for item in [*parsed_dot["objects"], *parsed_dot["edges"]]:
        assert not {"image", "shapefile", "URL", "href", "tooltip", "imagepath"} & set(item)


def test_a_model_cannot_name_an_image_for_the_engine(tmp_path: Path) -> None:
    parsed = Architecture.model_validate(load("providers/aws.json"))
    graph = map_view(parsed, parsed.views[0], "strict", LIMITS)
    dot = build_dot(graph, verified_icons(graph, LIMITS))
    images = [part.split('"')[1] for part in dot.split("image=")[1:]]
    assert images and all(
        image.startswith("icons/") and image.endswith(".png") and len(image) == 74
        for image in images
    )
    assert "http" not in " ".join(images) and "/etc" not in dot


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m["resources"][0].update(image="http://attacker.test/x.png"),
        lambda m: m["resources"][0].update(icon="/etc/passwd"),
        lambda m: m["resources"][0].update(url="https://attacker.test"),
        lambda m: m["resources"][0].update(graph_attr={"URL": "https://attacker.test"}),
        lambda m: m["resources"][0].update(properties={"image": "/etc/passwd"}),
        lambda m: m["resources"][0].update(service_type="diagrams.aws.compute.EC2"),
        lambda m: m["resources"][0].update(service_type="../../etc/passwd"),
        lambda m: m["resources"][0].update(service_type="https://attacker.test/icon"),
        lambda m: m["resources"][0].update(id="../../evil"),
        lambda m: m["resources"][0].update(provider="kubernetes"),
        lambda m: m["metadata"].update(id="../../evil"),
        lambda m: m["metadata"].update(id="a/b"),
        lambda m: m["views"][0].update(id="../../evil"),
        lambda m: m["views"][0].update(direction="RL"),
        lambda m: m["views"][0].update(style="custom"),
        lambda m: m["views"][0].update(grouping="anything"),
        lambda m: m["views"][0].update(legend="yes"),
        lambda m: m["views"][0].update(graph_attr={"size": "9999"}),
        lambda m: m["views"][0].update(exec="print(1)"),
        lambda m: m.update(python="import os"),
        lambda m: m.update(schema_version="2.0.0"),
        lambda m: m["resources"][0].update(name="line\nbreak"),
        lambda m: m["resources"][0].update(name="x" * 257),
    ],
)
@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_invalid_input_cannot_reach_the_renderer(
    mutate: Callable[[dict[str, Any]], Any],
    mode: Any,
    tmp_path: Path,
    forbid_rendering: None,
) -> None:
    model = single_resource_model()
    mutate(model)
    output = tmp_path / "out"
    result = render(model, output, mode=mode)
    assert not result.rendered and not result.valid and codes(result)
    assert renderer.exit_status(result) == 2 and not output.exists()


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not json",
        b"\xff\xfe",
        b"[]",
        b'{"schema_version":"1.0.0","schema_version":"1.0.0"}',
        b'{"schema_version":"1.0.0","x":NaN}',
        b"[" * 100 + b"]" * 100,
        b" " * (MAX_INPUT_BYTES + 1),
    ],
)
@pytest.mark.parametrize("mode", ["strict", "lenient"])
def test_malformed_input_never_creates_output(
    payload: bytes, mode: Any, tmp_path: Path, forbid_rendering: None
) -> None:
    output = tmp_path / "out"
    result = render(payload, output, mode=mode)
    assert not result.rendered and not result.valid and codes(result)
    assert not output.exists() and renderer.exit_status(result) == 2


@pytest.mark.parametrize("view", ["../../etc/passwd", "absent", ""])
def test_an_undeclared_view_cannot_become_a_path(
    view: str, tmp_path: Path, forbid_rendering: None
) -> None:
    output = tmp_path / "out"
    result = render(GOOD, output, view=view)
    assert not result.rendered and "VIEW_NOT_FOUND" in codes(result)
    assert not output.exists()


@pytest.mark.parametrize("service_type", ["os.system", "subprocess.popen", "builtins.eval"])
def test_a_module_path_as_a_type_is_only_ever_an_unknown_type(
    service_type: str, tmp_path: Path
) -> None:
    # These fit the identifier pattern, so they must end at the catalog lookup, not at an import.
    model = single_resource_model()
    model["resources"][0]["service_type"] = service_type
    strict = render(model, tmp_path / "strict")
    assert "CATALOG_TYPE_UNKNOWN" in codes(strict) and not (tmp_path / "strict").exists()
    lenient = render(model, tmp_path / "lenient", mode="lenient")
    assert lenient.rendered, codes(lenient)
    [asset] = manifest_of(lenient)["assets"]
    assert asset["reference"] == catalog().fallback.class_path


def test_catalog_class_paths_stay_data_a_model_cannot_supply() -> None:
    fields = json.dumps(Architecture.model_json_schema())
    for forbidden in ("class_path", '"image"', '"asset"', '"icon"', "graph_attr", "node_attr"):
        assert forbidden not in fields


def test_a_symlinked_output_root_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target)
    result = render(GOOD, link)
    assert codes(result) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert renderer.exit_status(result) == 4 and not list(target.iterdir())


def test_a_symlinked_ancestor_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "elsewhere"
    target.mkdir(mode=0o700)
    (tmp_path / "link").symlink_to(target)
    result = render(GOOD, tmp_path / "link/nested/out")
    assert codes(result) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert not list(target.iterdir())


def test_a_dangling_symlink_cannot_be_created_through(tmp_path: Path) -> None:
    (tmp_path / "link").symlink_to(tmp_path / "missing")
    result = render(GOOD, tmp_path / "link")
    assert codes(result) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert not (tmp_path / "missing").exists()


def test_parent_traversal_is_rejected_not_resolved(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    result = render(GOOD, Path(f"{tmp_path}/a/../b"))
    assert codes(result) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert not (tmp_path / "b").exists()


@pytest.mark.parametrize("mode", [0o777, 0o775, 0o757, 0o1777])
def test_an_output_root_others_can_write_is_rejected(mode: int, tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir()
    output.chmod(mode)
    assert codes(render(GOOD, output)) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert not list(output.iterdir())


def test_a_file_cannot_be_an_output_root(tmp_path: Path) -> None:
    path = tmp_path / "file"
    path.write_text("keep")
    assert codes(render(GOOD, path)) == ["RENDER_OUTPUT_PATH_UNSAFE"]
    assert path.read_text() == "keep"


def test_an_unusual_output_path_still_works(tmp_path: Path) -> None:
    # None of these characters may alter the sandbox profile or the font configuration.
    output = tmp_path / 'my "out" (v1) & co:=$HOME <x>'
    result = render(GOOD, output)
    assert result.rendered, codes(result)
    assert Path(result.artifacts[0].path).is_file()


def test_an_existing_private_root_is_reused_and_others_left_alone(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir(mode=0o755)
    (output / "keep.txt").write_text("keep")
    first = render(GOOD, output)
    second = render(GOOD, output)
    assert first.rendered and second.rendered and first.bundle_id != second.bundle_id
    assert (output / "keep.txt").read_text() == "keep"
    assert Path(first.artifacts[0].path).is_file()


def test_bundle_files_are_private_to_the_owner(tmp_path: Path) -> None:
    result = render(GOOD, tmp_path / "out")
    assert result.bundle_path
    assert stat.S_IMODE(os.stat(result.bundle_path).st_mode) == 0o700
    for artifact in result.artifacts:
        assert stat.S_IMODE(os.stat(artifact.path).st_mode) == 0o600


def test_a_bundle_collision_fails_and_keeps_the_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("secrets.token_hex", lambda _: "0" * 16)
    output = tmp_path / "out"
    first = render(GOOD, output)
    assert first.rendered
    before = bundle_files(first)
    second = render(GOOD, output)
    assert not second.rendered and codes(second) == ["RENDER_BUNDLE_COLLISION"]
    assert bundle_files(first) == before
    assert not [name for name in tree(output) if name.startswith(".")]


def output_engine(
    monkeypatch: pytest.MonkeyPatch,
    svg: Callable[[bytes], bytes] = lambda raw: raw,
    png: Callable[[bytes], bytes] = lambda raw: raw,
) -> None:
    """Keep the real engine, then alter what it wrote, as a compromised engine could."""
    real = execution.run_engine

    def run(engine: Engine, request: str, limits: Limits) -> None:
        real(engine, request, limits)
        svg_path, png_path = Path(request, "diagram.svg"), Path(request, "diagram.png")
        svg_path.write_bytes(svg(svg_path.read_bytes()))
        png_path.write_bytes(png(png_path.read_bytes()))

    monkeypatch.setattr(renderer, "run_engine", run)


SVG_TAIL = b"</svg>"


def inserting(markup: bytes) -> Callable[[bytes], bytes]:
    return lambda raw: raw.replace(SVG_TAIL, markup + SVG_TAIL)


@pytest.mark.parametrize(
    "alter",
    [
        inserting(b"<script>alert(1)</script>"),
        inserting(b'<g onload="alert(1)"/>'),
        inserting(b'<g onclick="alert(1)"/>'),
        inserting(b"<foreignObject><body/></foreignObject>"),
        inserting(b'<a xlink:href="javascript:alert(1)"><text>x</text></a>'),
        inserting(b'<a xlink:href="https://attacker.test"><text>x</text></a>'),
        inserting(b'<image xlink:href="https://attacker.test/x.png" width="1" height="1"/>'),
        inserting(b'<image xlink:href="file:///etc/passwd" width="1" height="1"/>'),
        inserting(b'<image xlink:href="/etc/passwd" width="1" height="1"/>'),
        inserting(b'<image xlink:href="data:image/svg+xml;base64,PHN2Zy8+" width="1" height="1"/>'),
        inserting(b'<image xlink:href="icons/' + b"0" * 64 + b'.png" width="1" height="1"/>'),
        inserting(b'<use xlink:href="https://attacker.test/x.svg#y"/>'),
        inserting(b"<style>*{fill:url(https://attacker.test)}</style>"),
        inserting(b'<g style="fill:url(https://attacker.test)"/>'),
        inserting(b'<path fill="url(https://attacker.test)" d="M0,0"/>'),
        inserting(b'<animate attributeName="href" to="javascript:alert(1)"/>'),
        inserting(b'<set attributeName="href" to="javascript:alert(1)"/>'),
        inserting(b'<g xmlns:x="urn:x" x:y="z"/>'),
        lambda raw: b'<?xml-stylesheet href="https://attacker.test/x.css"?>\n' + raw,
        lambda raw: raw.replace(b"<svg", b'<!DOCTYPE svg [<!ENTITY a "b">]><svg', 1),
        lambda raw: raw.replace(b"<svg", b'<!DOCTYPE x SYSTEM "http://attacker.test/x"><svg', 1),
        lambda raw: raw.replace(b"</g>\n</svg>", b"", 1),
        lambda raw: b"not svg at all",
        lambda raw: b"<html xmlns='http://www.w3.org/1999/xhtml'/>",
        lambda raw: raw.replace(b'id="graph:root"', b'id="graph:root" onload="x"', 1),
        lambda raw: raw.replace(b'id="node:app"', b'id="graph:root"', 1),
    ],
    ids=lambda item: None,
)
def test_an_unsafe_svg_blocks_the_bundle(
    alter: Callable[[bytes], bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_engine(monkeypatch, svg=alter)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert not result.rendered and not result.artifacts
    assert codes(result) == ["RENDER_SVG_UNSAFE"], codes(result)
    assert tree(output) == []


@pytest.mark.parametrize(
    "alter",
    [
        lambda raw: raw.replace(b'id="node:app"', b'id="node:gone"', 1),
        lambda raw: raw.replace(b'id="group:subnet"', b'id="group:gone"', 1),
        lambda raw: raw.replace(b">Application</text>", b">Changed</text>", 1),
        lambda raw: raw.replace(b"Core contract example", b"Changed", 1),
        lambda raw: raw.replace(
            b'preserveAspectRatio="xMinYMin meet"', b'preserveAspectRatio="none"', 1
        ),
        lambda raw: raw.replace(b"rotate(0)", b"rotate(90)", 1),
        lambda raw: raw.replace(b"scale(1 1)", b"scale(-1 1)", 1),
    ],
)
def test_a_lost_or_distorted_element_blocks_the_bundle(
    alter: Callable[[bytes], bytes], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_engine(monkeypatch, svg=alter)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_CONTENT_MISSING"], codes(result)
    assert tree(output) == []


def test_a_lost_icon_blocks_the_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # An unreadable image only makes Graphviz warn, and exit 0 would otherwise report success.
    def strip(raw: bytes) -> bytes:
        start = raw.index(b"<image")
        return raw[:start] + raw[raw.index(b"/>", start) + 2 :]

    output_engine(monkeypatch, svg=strip)
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_CONTENT_MISSING"]
    assert tree(output) == []


@pytest.mark.parametrize(
    ("alter", "code"),
    [
        (lambda raw: raw[: len(raw) // 2], "RENDER_PNG_INVALID"),
        (lambda raw: raw[:-1], "RENDER_PNG_INVALID"),
        (lambda raw: raw + b"extra", "RENDER_PNG_INVALID"),
        (lambda raw: b"not a png", "RENDER_PNG_INVALID"),
        (lambda raw: raw[:40] + bytes([raw[40] ^ 255]) + raw[41:], "RENDER_PNG_INVALID"),
        (
            lambda raw: raw[:16] + (70000).to_bytes(4) + (70000).to_bytes(4) + raw[24:],
            "RENDER_PIXEL_LIMIT",
        ),
        (
            lambda raw: raw[:16] + (0).to_bytes(4) + raw[20:],
            "RENDER_PNG_INVALID",
        ),
    ],
)
def test_an_invalid_png_blocks_the_bundle(
    alter: Callable[[bytes], bytes], code: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_engine(monkeypatch, png=alter)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == [code]
    assert renderer.exit_status(result) == (2 if code == "RENDER_PIXEL_LIMIT" else 4)
    assert tree(output) == []


def rebuilt_png(width: int, height: int) -> bytes:
    """A structurally valid PNG of any size, as a compromised engine could write."""

    def chunk(kind: bytes, body: bytes) -> bytes:
        return len(body).to_bytes(4) + kind + body + zlib.crc32(kind + body).to_bytes(4)

    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", b"x") + chunk(b"IEND", b"")


def resized(resize: Callable[[int, int], tuple[int, int]]) -> Callable[[bytes], bytes]:
    return lambda raw: rebuilt_png(*resize(*struct.unpack(">II", raw[16:24])))


@pytest.mark.parametrize(
    "resize",
    [
        lambda width, height: (width * 2, height * 2),
        lambda width, height: (width, height // 2),
        lambda width, height: (width * 2, height),
    ],
)
def test_a_png_of_another_shape_blocks_the_bundle(
    resize: Callable[[int, int], tuple[int, int]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_engine(monkeypatch, png=resized(resize))
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_PNG_INVALID"]
    assert renderer.exit_status(result) == 4 and tree(output) == []


def test_a_uniformly_smaller_png_is_disclosed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_engine(monkeypatch, png=resized(lambda width, height: (width // 2, height // 2)))
    result = render(GOOD, tmp_path / "out")
    assert result.rendered, codes(result)
    assert manifest_of(result)["png"]["scale"] == pytest.approx(0.5, abs=0.05)
    assert [item.severity for item in result.diagnostics if item.code == "RENDER_PNG_SCALED"] == [
        "warning"
    ]


@pytest.mark.parametrize("tall", [True, False])
def test_png_scale_accepts_every_shrink_cairo_writes(tall: bool) -> None:
    # Cairo scales by the longer side and truncates the other to an integer, so the shorter side's
    # ratio runs low and must not set the scale.
    unlimited = replace(LIMITS, pixels=10**12)
    for long_points in range(24_600, 60_000, 97):
        for short_points in (120, 355, 747, 1000):
            ratio = 32767 / (long_points * 96 / 72)
            sides = (long_points, short_points) if tall else (short_points, long_points)
            root = ET.Element("svg", {"height": f"{sides[0]}pt", "width": f"{sides[1]}pt"})
            short = int(short_points * 96 / 72 * ratio)
            size = (short, 32767) if tall else (32767, short)
            assert checks.png_scale(root, size, unlimited) == pytest.approx(ratio, abs=0.001)


def test_the_pixel_limit_applies_before_a_png_is_shrunk(tmp_path: Path) -> None:
    # This PNG is about 9 Mpx after Cairo shrinks it, so only the full-size check can refuse it.
    output = tmp_path / "out"
    result = render(icon_model(197, 0), output, limits=replace(LIMITS, pixels=20_000_000))
    assert codes(result) == ["RENDER_PIXEL_LIMIT"]
    assert renderer.exit_status(result) == 2 and tree(output) == []


@pytest.mark.parametrize("size", [b'width="100%"', b'width="0pt"'])
def test_an_svg_without_a_usable_size_blocks_the_bundle(
    size: bytes, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def alter(raw: bytes) -> bytes:
        changed, count = re.subn(rb'(?<=<svg )width="[^"]*"', size, raw, count=1)
        assert count == 1
        return changed

    output_engine(monkeypatch, svg=alter)
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_SVG_UNSAFE"]
    assert tree(output) == []


def test_an_in_bound_view_over_the_pixel_limit_asks_for_a_split(tmp_path: Path) -> None:
    # The real engine and real icons, with a lower limit so that a new layout cannot change this.
    output = tmp_path / "out"
    result = render(icon_model(20, 30), output, limits=replace(LIMITS, pixels=100_000))
    assert codes(result) == ["RENDER_PIXEL_LIMIT"]
    assert renderer.exit_status(result) == 2 and tree(output) == []
    failure = next(item for item in result.diagnostics if item.code == "RENDER_PIXEL_LIMIT")
    assert "Split" in (failure.remedy or "")


def test_output_links_and_missing_files_block_the_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = tmp_path / "secret.svg"
    secret.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
    real = execution.run_engine

    def link(engine: Engine, request: str, limits: Limits) -> None:
        real(engine, request, limits)
        Path(request, "diagram.svg").unlink()
        Path(request, "diagram.svg").symlink_to(secret)

    monkeypatch.setattr(renderer, "run_engine", link)
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_OUTPUT_MISSING"]
    assert tree(output) == []

    def missing(engine: Engine, request: str, limits: Limits) -> None:
        real(engine, request, limits)
        Path(request, "diagram.png").unlink()

    monkeypatch.setattr(renderer, "run_engine", missing)
    assert codes(render(GOOD, output)) == ["RENDER_OUTPUT_MISSING"]
    assert tree(output) == []


def test_an_oversize_output_blocks_the_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = execution.run_engine

    def grow(engine: Engine, request: str, limits: Limits) -> None:
        real(engine, request, limits)
        Path(request, "diagram.png").write_bytes(b"x" * (limits.file_bytes + 1))

    monkeypatch.setattr(renderer, "run_engine", grow)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_ARTIFACT_LIMIT"]
    assert renderer.exit_status(result) == 2 and tree(output) == []


def test_a_root_replaced_during_rendering_gets_no_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out"
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    real = execution.run_engine

    def swap(engine: Engine, request: str, limits: Limits) -> None:
        real(engine, request, limits)
        output.rename(tmp_path / "moved")
        output.symlink_to(outside)

    monkeypatch.setattr(renderer, "run_engine", swap)
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_OUTPUT_ROOT_CHANGED"]
    assert not list(outside.iterdir())


def test_failure_after_writing_leaves_no_stage_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out"
    root = OutputRoot(str(output))
    real_rename = os.rename

    def refuse(*_: object, **__: object) -> None:
        raise OSError("disk trouble")

    monkeypatch.setattr(os, "rename", refuse)
    with pytest.raises(RenderFailure) as caught:
        root.publish("bundle", {"a.txt": b"a"})
    assert caught.value.code == "RENDER_OUTPUT_WRITE_FAILED"
    monkeypatch.setattr(os, "rename", real_rename)
    root.close()
    assert tree(output) == []


@pytest.mark.parametrize(
    "path",
    [
        "../../../../etc/passwd",
        "/etc/passwd",
        "https://attacker.test/x.png",
        "assets/../../../etc/passwd",
        "assets/huawei/../../catalog_data/rules.json",
    ],
)
def test_a_tampered_asset_path_is_refused(path: str, monkeypatch: pytest.MonkeyPatch) -> None:
    data = catalog()
    asset = data.assets["huawei-ecs"]
    file = asset.derived.png.model_copy(update={"path": path})
    tampered = asset.model_copy(update={"derived": asset.derived.model_copy(update={"png": file})})
    monkeypatch.setitem(data.assets, asset.id, tampered)
    icon = GraphIcon(source="custom_asset", reference=asset.id, pack=asset.pack)
    with pytest.raises(RenderFailure) as caught:
        verified_icon(icon, LIMITS)
    assert caught.value.code == "RENDER_ASSET_UNSAFE"


def test_a_tampered_asset_digest_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    data = catalog()
    asset = data.assets["huawei-ecs"]
    file = asset.derived.png.model_copy(update={"sha256": "0" * 64})
    tampered = asset.model_copy(update={"derived": asset.derived.model_copy(update={"png": file})})
    monkeypatch.setitem(data.assets, asset.id, tampered)
    icon = GraphIcon(source="custom_asset", reference=asset.id, pack=asset.pack)
    with pytest.raises(RenderFailure) as caught:
        verified_icon(icon, LIMITS)
    assert caught.value.code == "RENDER_ASSET_UNSAFE"


@pytest.mark.parametrize(
    "reference",
    [
        "os.system",
        "subprocess.Popen",
        "builtins.eval",
        "diagrams.aws.compute.NotAClass",
        "diagrams.Diagram",
        "diagrams.custom.Custom",
    ],
)
def test_a_class_outside_the_lock_is_never_imported(
    reference: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_import(_: str) -> None:
        raise AssertionError("imported a class the lock does not list")

    monkeypatch.setattr("importlib.import_module", no_import)
    icon = GraphIcon(source="native_class", reference=reference, pack="diagrams-generic")
    with pytest.raises(RenderFailure) as caught:
        verified_icon(icon, LIMITS)
    assert caught.value.code == "RENDER_ASSET_UNSAFE"


def test_a_blocked_or_unknown_pack_is_refused() -> None:
    for pack in ("huawei-cloud-icons", "no-such-pack"):
        icon = GraphIcon(source="custom_asset", reference="huawei-ecs", pack=pack)
        with pytest.raises(RenderFailure) as caught:
            verified_icon(icon, LIMITS)
        assert caught.value.code == "RENDER_ASSET_UNSAFE"


def test_an_asset_replaced_by_a_link_or_changed_on_disk_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "package"
    shutil.copytree(catalog_module.PACKAGE / "assets", package / "assets")
    monkeypatch.setattr(icons, "PACKAGE", package)
    asset = catalog().assets["huawei-ecs"]
    icon = GraphIcon(source="custom_asset", reference=asset.id, pack=asset.pack)
    assert verified_icon(icon, LIMITS).data
    target = package / asset.derived.png.path
    target.write_bytes(target.read_bytes() + b"x")
    with pytest.raises(RenderFailure):
        verified_icon(icon, LIMITS)
    good = catalog_module.PACKAGE / asset.derived.png.path
    target.unlink()
    target.symlink_to(good)
    with pytest.raises(RenderFailure):
        verified_icon(icon, LIMITS)
    target.unlink()
    (package / "assets/huawei").rename(package / "assets/moved")
    (package / "assets/huawei").symlink_to(package / "assets/moved")
    shutil.copyfile(good, package / "assets/moved" / target.name)
    with pytest.raises(RenderFailure):
        verified_icon(icon, LIMITS)


def test_a_changed_font_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    package = tmp_path / "package"
    shutil.copytree(catalog_module.PACKAGE / "assets", package / "assets")
    monkeypatch.setattr(icons, "PACKAGE", package)
    (package / catalog().manifest.fonts[0].path).write_bytes(b"not a font")
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_ASSET_UNSAFE"]
    assert tree(output) == []


def test_view_size_limits_reject_with_a_split_suggestion(tmp_path: Path) -> None:
    for entities, relationships in [
        (LIMITS.view_entities + 1, 0),
        (2, LIMITS.view_relationships + 1),
    ]:
        output = tmp_path / "out"
        result = render(large_model(entities, relationships), output)
        assert codes(result) == ["RENDER_VIEW_TOO_LARGE"]
        assert "Split" in next(d.remedy for d in result.diagnostics if d.severity == "error")
        assert renderer.exit_status(result) == 2 and not output.exists()


def chain_model(depth: int) -> dict[str, Any]:
    model = single_resource_model()
    model["boundaries"] = [
        {
            "id": f"b{index}",
            "name": f"Level {index}",
            "provider": "external",
            "kind": "environment",
            **({"parent_ref": f"b{index - 1}"} if index else {}),
        }
        for index in range(depth)
    ]
    model["views"][0]["entity_refs"] = [f"b{index}" for index in range(depth)]
    return model


def test_deep_nesting_is_rejected_before_graphviz(tmp_path: Path, forbid_engine: None) -> None:
    output = tmp_path / "out"
    result = render(chain_model(LIMITS.group_depth + 1), output)
    assert codes(result) == ["RENDER_GROUP_DEPTH_LIMIT"] and not output.exists()


@pytest.fixture
def forbid_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(renderer, "find_engine", fail_if_called)


def test_nesting_at_the_limit_renders(tmp_path: Path) -> None:
    result = render(chain_model(LIMITS.group_depth - 1), tmp_path / "out")
    assert result.rendered, codes(result)


def test_memberships_that_only_loop_across_dimensions_terminate(tmp_path: Path) -> None:
    # Each dimension is acyclic alone, so validation passes, and only the mapper can catch this.
    model = single_resource_model()
    model["boundaries"] = [
        {
            "id": "a",
            "name": "A",
            "provider": "external",
            "kind": "environment",
            "parent_ref": "b",
        },
        {
            "id": "b",
            "name": "B",
            "provider": "external",
            "kind": "environment",
            "relations": [{"kind": "deployment_member_of", "target_ref": "a"}],
        },
    ]
    model["views"][0]["entity_refs"] = ["a", "b", "app"]
    result = render(model, tmp_path / "out")
    assert result.rendered, codes(result)
    groups = {group["id"]: group for group in graph_of(result)["groups"]}
    assert groups["a"]["parent"] == "b"
    assert groups["b"]["parent"] == "_provider.external"
    # The dropped direction stays stated rather than vanishing with the nesting.
    assert "deployment:A" in joined_text(by_id(svg_root(result))["group:b"])


def test_a_strict_mapper_refuses_an_unresolved_type() -> None:
    # Validation stops this first; the mapper still has no route from it to a drawing.
    model = single_resource_model()
    model["resources"][0]["service_type"] = "external.system.madeup"
    parsed = Architecture.model_validate(model)
    with pytest.raises(RenderFailure) as caught:
        Mapper(parsed, parsed.views[0], "strict", LIMITS).build()
    assert caught.value.code == "RENDER_TYPE_UNRESOLVED"


def test_text_xml_cannot_hold_fails_closed(tmp_path: Path) -> None:
    # The schema allows these noncharacters, Graphviz writes them, and XML forbids them.
    output = tmp_path / "out"
    result = render(single_resource_model("bad￾ text"), output)
    assert codes(result) == ["RENDER_SVG_UNSAFE"]
    assert tree(output) == []


def test_only_literal_and_controlled_values_reach_engine_environment(tmp_path: Path) -> None:
    assert set(engine_environment(str(tmp_path))) == {
        "PATH",
        "HOME",
        "TMPDIR",
        "LANG",
        "FONTCONFIG_FILE",
        "PANGOCAIRO_BACKEND",
    }


def test_the_engine_really_uses_the_bundled_fonts(tmp_path: Path) -> None:
    # Graphviz reports the font file it resolved, which the manifest's claim must match.
    request = tmp_path / "request"
    (request / "fonts").mkdir(parents=True)
    (request / "cache").mkdir()
    for font in catalog().manifest.fonts:
        shutil.copyfile(
            catalog_module.PACKAGE / font.path, request / "fonts" / Path(font.path).name
        )
    (request / "fonts.conf").write_text(
        f"<fontconfig><dir>{request}/fonts</dir><cachedir>{request}/cache</cachedir></fontconfig>"
    )
    (request / "t.dot").write_text(
        'digraph { node [fontname="Noto Sans"]; a [label="Latin สถาปัตยกรรม"] }\n'
    )
    result = subprocess.run(
        [find_engine().path, "-v", "-Tsvg", "-o", "t.svg", "t.dot"],
        cwd=request,
        capture_output=True,
        env=engine_environment(str(request)),
        timeout=30,
        check=True,
    )
    assert f"{request}/fonts/NotoSans-Regular.ttf".encode() in result.stderr
    assert b"CoreText" not in result.stderr


def test_a_render_that_skipped_the_bundled_fonts_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Real Graphviz, without the variable: on macOS it then falls back to a system font.
    real = execution.engine_environment

    def without_backend(request: str) -> dict[str, str]:
        return {key: value for key, value in real(request).items() if key != "PANGOCAIRO_BACKEND"}

    monkeypatch.setattr(execution, "engine_environment", without_backend)
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_FONT_UNAVAILABLE"]
    assert tree(output) == []


def test_hostile_environment_does_not_reach_the_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    planted = tmp_path / "planted"
    planted.mkdir()
    for name, value in {
        "GVBINDIR": str(planted),
        "FONTCONFIG_FILE": str(planted / "fonts.conf"),
        "FONTCONFIG_PATH": str(planted),
        "DYLD_INSERT_LIBRARIES": str(planted / "x.dylib"),
        "SERVER_NAME": "x",
        "GV_FILE_PATH": str(planted),
        "TMPDIR": str(planted),
    }.items():
        monkeypatch.setenv(name, value)
    result = render(GOOD, tmp_path / "out")
    assert result.rendered, codes(result)
    assert not list(planted.iterdir())


def test_a_relative_path_entry_cannot_supply_the_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "dot"
    fake.write_text("#!/bin/sh\ntouch marker\n")
    fake.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", f".:{os.environ['PATH']}")
    assert Path(find_engine().path) != fake.resolve()
    assert not (tmp_path / "marker").exists()


def test_missing_graphviz_fails_closed_with_a_remedy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(execution, "_dot_path", lambda: None)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_ENGINE_UNAVAILABLE"] and not output.exists()
    assert renderer.exit_status(result) == 4
    assert result.valid is True and result.pending_checks == ["render"]
    assert "brew install graphviz" in result.diagnostics[-1].remedy
    assert host_blockers() == ["graphviz_missing"]


def test_a_dot_that_will_not_report_a_version_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(execution, "_dot_path", lambda: "/bin/echo")
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_ENGINE_UNAVAILABLE"]
    assert not output.exists()


def test_a_host_without_the_sandbox_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Rendering without isolation would be a silent downgrade, so it does not render at all.
    monkeypatch.setattr(execution, "SANDBOX", str(tmp_path / "missing"))
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_ISOLATION_UNAVAILABLE"] and not output.exists()
    assert "sandbox_unavailable" in host_blockers()


# /bin/sh on macOS is a small launcher that starts another shell, which the profile would deny.
SHELL = "/bin/bash"


def probe(
    tmp_path: Path, *command: str, home: Path | None = None
) -> subprocess.CompletedProcess[bytes]:
    """Run a command under the renderer's real profile, as the engine runs."""
    request = tmp_path / "request"
    request.mkdir(exist_ok=True)
    return subprocess.run(
        sandboxed(
            list(command), str(request.resolve()), str((home or tmp_path / "home").resolve())
        ),
        cwd=request,
        capture_output=True,
        env={"PATH": "/usr/bin:/bin"},
        timeout=30,
        check=False,
    )


def test_sandbox_denies_network_while_the_same_command_can_connect(tmp_path: Path) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        listener.settimeout(5)
        port = str(listener.getsockname()[1])
        accepted: list[bool] = []

        def accept() -> None:
            try:
                connection, _ = listener.accept()
                connection.close()
                accepted.append(True)
            except TimeoutError:
                accepted.append(False)

        waiter = threading.Thread(target=accept)
        waiter.start()
        control = subprocess.run(
            ["/usr/bin/nc", "-z", "-G", "2", "127.0.0.1", port], capture_output=True, timeout=10
        )
        waiter.join()
        assert control.returncode == 0 and accepted == [True]
        denied = probe(tmp_path, "/usr/bin/nc", "-v", "-z", "-G", "2", "127.0.0.1", port)
        assert denied.returncode != 0
        assert b"not permitted" in denied.stderr.lower()


def test_sandbox_confines_writes_to_the_request_directory(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    result = probe(tmp_path, SHELL, "-c", f'echo x > "{outside}"; echo y > inside.txt')
    assert not outside.exists()
    # The write that is allowed proves the shell really ran, so the denial above means something.
    assert (tmp_path / "request/inside.txt").read_text() == "y\n"
    assert b"not permitted" in result.stderr.lower()


def test_sandbox_denies_reading_the_home_directory(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    secret = home / "secret.txt"
    secret.write_text("secret value")
    (tmp_path / "request").mkdir()
    (tmp_path / "request/allowed.txt").write_text("allowed value")
    result = probe(
        tmp_path,
        SHELL,
        "-c",
        f'read line < allowed.txt; echo "$line"; read other < "{secret}"; echo "got $other"',
        home=home,
    )
    assert b"allowed value" in result.stdout
    assert b"secret value" not in result.stdout
    assert b"not permitted" in result.stderr.lower()


def test_sandbox_denies_starting_other_programs(tmp_path: Path) -> None:
    forked = probe(tmp_path, SHELL, "-c", "echo alive; /usr/bin/touch forked")
    assert b"alive" in forked.stdout
    assert not (tmp_path / "request/forked").exists()
    replaced = probe(tmp_path, SHELL, "-c", "echo alive; exec /usr/bin/touch replaced")
    assert b"alive" in replaced.stdout and replaced.returncode != 0
    assert not (tmp_path / "request/replaced").exists()


def test_real_engine_cannot_read_an_image_from_the_home_directory(tmp_path: Path) -> None:
    # A direct hit on the second wall: even an image attribute reaching DOT finds nothing.
    home = tmp_path / "home"
    home.mkdir()
    icon = home / "private.png"
    icon.write_bytes(
        (catalog_module.PACKAGE / catalog().assets["huawei-ecs"].derived.png.path).read_bytes()
    )
    engine = find_engine()
    request = tmp_path / "request"
    request.mkdir()
    (request / "t.dot").write_text(f'digraph {{ a [shape=none image="{icon}"] }}\n')
    result = probe(tmp_path, engine.path, "-Tsvg", "-o", "t.svg", "t.dot", home=home)
    written = (request / "t.svg").read_text() if (request / "t.svg").exists() else ""
    assert result.returncode != 0 or "<image" not in written


def test_real_engine_reads_what_the_request_directory_holds(tmp_path: Path) -> None:
    # The control for the test above: without it, a broken profile would pass as a safe one.
    engine = find_engine()
    request = tmp_path / "request"
    request.mkdir()
    shutil.copyfile(
        catalog_module.PACKAGE / catalog().assets["huawei-ecs"].derived.png.path,
        request / "icon.png",
    )
    (request / "t.dot").write_text('digraph { a [shape=none image="icon.png"] }\n')
    result = probe(tmp_path, engine.path, "-Tsvg", "-o", "t.svg", "t.dot")
    assert result.returncode == 0 and "<image" in (request / "t.svg").read_text()


def spawned_pids(path: Path) -> list[int]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if path.exists() and (text := path.read_text()).endswith("\n"):
            return [int(item) for item in text.split()]
        time.sleep(0.02)
    raise AssertionError("the child did not start")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A zombie still answers until its parent reaps it, and it can no longer do anything.
    state = subprocess.run(
        ["/bin/ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def test_timeout_kills_the_whole_process_group(tmp_path: Path) -> None:
    script = 'sleep 300 & echo "$$ $!" > pids; wait\n'
    limits = replace(LIMITS, wall_seconds=0.5)
    with pytest.raises(RenderFailure) as caught:
        run_bounded(["/bin/sh", "-c", script], str(tmp_path), {}, limits, str(tmp_path))
    assert caught.value.code == "RENDER_TIMEOUT"
    for pid in spawned_pids(tmp_path / "pids"):
        assert not alive(pid), pid


def test_a_child_left_behind_by_a_finished_leader_is_killed(tmp_path: Path) -> None:
    script = 'sleep 300 & echo "$!" > pids; exit 0\n'
    run_bounded(["/bin/sh", "-c", script], str(tmp_path), {}, LIMITS, str(tmp_path))
    [pid] = spawned_pids(tmp_path / "pids")
    time.sleep(0.1)
    assert not alive(pid)


def test_real_engine_timeout_cleans_up_and_publishes_nothing(tmp_path: Path) -> None:
    output = tmp_path / "out"
    # The first check comes after one sampling interval, well before Graphviz can finish.
    limits = replace(LIMITS, wall_seconds=0.01, sampling_seconds=0.01)
    result = render(large_model(150, 280), output, limits=limits)
    assert codes(result) == ["RENDER_TIMEOUT"]
    assert renderer.exit_status(result) == 4 and tree(output) == []


def test_label_amplification_stays_bounded(tmp_path: Path) -> None:
    output = tmp_path / "out"
    limits = replace(LIMITS, wall_seconds=3)
    started = time.monotonic()
    result = render(amplified_model(), output, limits=limits)
    assert time.monotonic() - started < 30
    assert not result.rendered and codes(result)[0].startswith("RENDER_")
    assert renderer.exit_status(result) == 4 and tree(output) == []


def test_memory_limit_stops_the_engine(tmp_path: Path) -> None:
    code = "import time; x = b'x' * (256 * 1024 * 1024); time.sleep(60)"
    limits = replace(LIMITS, memory_bytes=64 * 1024 * 1024, wall_seconds=30)
    with pytest.raises(RenderFailure) as caught:
        run_bounded([sys.executable, "-c", code], str(tmp_path), {}, limits, str(tmp_path))
    assert caught.value.code == "RENDER_MEMORY_LIMIT"


def test_temporary_storage_limit_stops_the_engine(tmp_path: Path) -> None:
    code = (
        "import itertools\n"
        "for i in itertools.count():\n"
        "    open(f'part{i}', 'wb').write(b'x' * 65536)\n"
    )
    limits = replace(LIMITS, temporary_bytes=1024 * 1024, wall_seconds=30)
    with pytest.raises(RenderFailure) as caught:
        run_bounded([sys.executable, "-c", code], str(tmp_path), {}, limits, str(tmp_path))
    assert caught.value.code == "RENDER_TEMPORARY_LIMIT"


def test_cpu_limit_stops_a_busy_engine(tmp_path: Path) -> None:
    command = limited([sys.executable, "-c", "while True: pass"], replace(LIMITS, cpu_seconds=1))
    limits = replace(LIMITS, wall_seconds=30)
    started = time.monotonic()
    with pytest.raises(RenderFailure) as caught:
        run_bounded(command, str(tmp_path), {}, limits, str(tmp_path))
    assert caught.value.code == "RENDER_ENGINE_FAILED"
    assert time.monotonic() - started < 15


def test_file_size_limit_stops_a_runaway_write(tmp_path: Path) -> None:
    code = "open('big', 'wb').write(b'x' * (4 * 1024 * 1024))"
    command = limited([sys.executable, "-c", code], replace(LIMITS, file_bytes=1024 * 1024))
    with pytest.raises(RenderFailure) as caught:
        run_bounded(command, str(tmp_path), {}, LIMITS, str(tmp_path))
    assert caught.value.code == "RENDER_ENGINE_FAILED"
    assert (tmp_path / "big").stat().st_size <= 1024 * 1024


def test_engine_failure_is_reported_and_cleaned_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(_engine: Engine, request: str, limits: Limits) -> None:
        run_bounded(["/usr/bin/false"], request, {}, limits, request)

    monkeypatch.setattr(renderer, "run_engine", broken)
    output = tmp_path / "out"
    result = render(GOOD, output)
    assert codes(result) == ["RENDER_ENGINE_FAILED"]
    assert result.valid and tree(output) == []


def test_engine_with_no_output_is_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def only_a_log(_engine: Engine, request: str, _limits: Limits) -> None:
        Path(request, execution.ENGINE_LOG).write_bytes(
            f"fontname: x resolved to: y {request}/fonts/z\n".encode()
        )

    monkeypatch.setattr(renderer, "run_engine", only_a_log)
    output = tmp_path / "out"
    assert codes(render(GOOD, output)) == ["RENDER_OUTPUT_MISSING"]
    assert tree(output) == []


def test_sigterm_stops_graphviz_and_removes_every_temporary_file(tmp_path: Path) -> None:
    output = tmp_path / "out"
    process = subprocess.Popen(
        ["cloud-diagrams", "render", "--output", str(output)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin
    # A view this size keeps Graphviz busy for seconds, so the signal cannot arrive too late.
    process.stdin.write(encode(amplified_model()))
    process.stdin.close()
    process.stdin = None
    deadline = time.monotonic() + 30
    scratch: list[str] = []
    while time.monotonic() < deadline and not scratch:
        scratch = (
            [name for name in tree(output) if name.endswith("graph.dot")] if output.exists() else []
        )
        time.sleep(0.01)
    assert scratch, "the render never reached Graphviz"
    process.send_signal(signal.SIGTERM)
    stdout, _ = process.communicate(timeout=20)
    assert process.returncode == 4
    report = json.loads(stdout)
    assert report["rendered"] is False
    assert [d["code"] for d in report["diagnostics"] if d["severity"] == "error"] == [
        "RENDER_INTERRUPTED"
    ]
    assert tree(output) == []
    running = subprocess.run(
        ["/usr/bin/pgrep", "-f", str(output)], capture_output=True, text=True, check=False
    ).stdout
    assert not running.strip()


def test_real_engine_run_uses_only_the_request_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []
    real = execution.run_bounded

    def record(
        command: list[str],
        cwd: str,
        environment: dict[str, str],
        limits: Limits,
        scratch: str,
        stderr: int,
    ) -> None:
        seen.append(command)
        assert cwd == scratch == environment["HOME"]
        assert environment["FONTCONFIG_FILE"].startswith(cwd)
        real(command, cwd, environment, limits, scratch, stderr)

    monkeypatch.setattr(execution, "run_bounded", record)
    result = render(GOOD, tmp_path / "out")
    assert result.rendered, codes(result)
    [command] = seen
    assert command[1:3] == ["-I", "-S"]
    assert execution.SANDBOX in command
    assert command[-1] == "graph.dot"
    assert "-Tsvg" in command and "-Tpng" in command


def test_no_label_or_host_path_appears_in_a_failure_report(tmp_path: Path) -> None:
    # NFR-005 keeps rejected values out of diagnostics, and a failed render is no exception.
    secret = "SECRET-LABEL-VALUE"
    model = single_resource_model(secret + "￾")
    result = render(model, tmp_path / "out")
    assert not result.rendered
    assert secret not in result.model_dump_json()
    assert str(tmp_path) not in result.model_dump_json()


def test_secret_markers_show_no_payload(tmp_path: Path) -> None:
    result = render((FIXTURES / "kubernetes-valid.json").read_bytes(), tmp_path / "out")
    assert result.rendered
    node = by_id(svg_root(result))["node:secret"]
    assert texts(node) == ["secret", "Secret"]


def test_svg_embeds_only_verified_icon_bytes(tmp_path: Path) -> None:
    result = render((FIXTURES / "providers/huawei.json").read_bytes(), tmp_path / "out")
    digests = {asset["sha256"] for asset in manifest_of(result)["assets"]}
    for image in svg_root(result).iter(f"{{{checks.SVG}}}image"):
        data = base64.b64decode(image.get(checks.HREF, "").removeprefix(checks.DATA_PNG))
        assert hashlib.sha256(data).hexdigest() in digests


def test_bundle_is_complete_or_absent_when_publication_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "out"
    real = OutputRoot.publish

    def failing(self: OutputRoot, name: str, files: dict[str, bytes]) -> Path:
        partial = {key: value for key, value in files.items() if key != "manifest.json"}
        partial["model.json"] = None  # type: ignore[assignment]
        return real(self, name, partial)

    monkeypatch.setattr(OutputRoot, "publish", failing)
    with pytest.raises(TypeError):
        render(GOOD, output)
    assert tree(output) == []


def test_manifest_comes_last_and_only_on_success(tmp_path: Path) -> None:
    result = render(GOOD, tmp_path / "out")
    manifest = manifest_of(result)
    assert manifest["status"] == "complete"
    assert set(manifest["artifacts"]) == set(renderer.BUNDLE_FILES) - {"manifest.json"}
