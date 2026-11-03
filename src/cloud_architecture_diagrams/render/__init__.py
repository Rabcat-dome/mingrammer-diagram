"""Controlled rendering (M3): validate, map one view, run Graphviz bounded, check, then publish."""

import hashlib
import json
import os
import platform
import secrets
from importlib import metadata
from typing import Any
from xml.sax.saxutils import escape

from pydantic import BaseModel, Field

from .. import __version__
from ..catalog import catalog
from ..diagnostics import Diagnostic, ValidationResult
from ..models import Architecture, View
from ..validation import Mode, validate_model
from .bundle import OutputRoot
from .checks import (
    check_content,
    check_png,
    check_svg,
    check_undistorted,
    finalize_svg,
    png_scale,
)
from .draw import build_dot
from .errors import MESSAGES, REQUEST_CODES, RenderFailure, diagnostic
from .execution import ENGINE_LOG, ISOLATION, Engine, check_fonts_used, find_engine, run_engine
from .graph import RenderGraph, map_view
from .icons import VerifiedIcon, verified_fonts, verified_icons
from .limits import LIMITS, Limits
from .paths import read_regular, write_new

MEDIA_TYPES = {
    "diagram.svg": "image/svg+xml",
    "diagram.png": "image/png",
    "model.json": "application/json",
    "view.json": "application/json",
    "diagnostics.json": "application/json",
    "manifest.json": "application/json",
}
BUNDLE_FILES = sorted(MEDIA_TYPES)


class Artifact(BaseModel):
    name: str
    path: str
    bytes: int
    sha256: str
    media_type: str


class RenderResult(ValidationResult):
    """Success only ever follows a published bundle, so `rendered` alone can be trusted."""

    rendered: bool = False
    bundle_id: str | None = None
    bundle_path: str | None = None
    artifacts: list[Artifact] = Field(default_factory=list)
    rights: dict[str, Any] | None = None


def exit_status(result: RenderResult) -> int:
    """0 published; 2 the model or view cannot be drawn as asked; 4 this render failed."""
    if result.rendered:
        return 0
    failures = {
        item.code
        for item in result.diagnostics
        if item.severity == "error" and item.code in MESSAGES
    }
    return 4 if failures - REQUEST_CODES else 2


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()


def rights_report(graph: RenderGraph) -> dict[str, Any]:
    """FR-052: terms travel with the output, and only what this image really uses is listed."""
    data = catalog()
    packs = [data.packs[identifier] for identifier in graph.packs()]
    private = [pack for pack in packs if pack.status == "private_use_only"]
    return {
        "private_use_only": bool(private),
        "distribution_limit": (
            "Private personal use only under D-018. Rights are not cleared, and O-002 keeps "
            "public distribution blocked. Do not publish this bundle or share it outside "
            "private use."
            if private
            else None
        ),
        "blockers": sorted({pack.blocker for pack in private if pack.blocker}),
        "packs": [
            {
                "id": pack.id,
                "status": pack.status,
                "distribution": pack.distribution,
                "license": pack.license,
                "rights_basis": pack.rights_basis,
                "source_version": pack.source_version,
                "attribution": pack.attribution,
                "conditions": list(pack.conditions),
            }
            for pack in packs
        ],
    }


def _write_request(
    directory: int, request: str, dot: str, icons: dict[str, VerifiedIcon], limits: Limits
) -> list[dict[str, str]]:
    """Graphviz reads only this directory, so the sandbox can refuse everything else."""
    for name in ("icons", "fonts", "cache", "tmp"):
        os.mkdir(name, mode=0o700, dir_fd=directory)
    write_new(directory, "graph.dot", dot.encode("utf-8"))
    fonts = []
    fonts_directory = os.open("fonts", os.O_RDONLY, dir_fd=directory)
    icons_directory = os.open("icons", os.O_RDONLY, dir_fd=directory)
    try:
        for font, data in verified_fonts(limits):
            write_new(fonts_directory, os.path.basename(font.path), data)
            fonts.append(
                {
                    "family": font.family,
                    "version": font.version,
                    "sha256": font.sha256,
                    "license": font.license,
                }
            )
        for icon in icons.values():
            try:
                write_new(icons_directory, icon.file_name, icon.data)
            except FileExistsError:
                pass  # Types can share one icon, and the digest names the bytes.
    finally:
        os.close(fonts_directory)
        os.close(icons_directory)
    config = (
        f"<fontconfig><dir>{escape(request)}/fonts</dir>"
        f"<cachedir>{escape(request)}/cache</cachedir></fontconfig>\n"
    )
    write_new(directory, "fonts.conf", config.encode("utf-8"))
    return fonts


def _read_output(directory: int, name: str, limits: Limits) -> bytes:
    try:
        return read_regular(directory, name, limits.file_bytes)
    except OverflowError as error:
        raise RenderFailure("RENDER_ARTIFACT_LIMIT", f"/{name}") from error
    except (OSError, ValueError) as error:
        raise RenderFailure("RENDER_OUTPUT_MISSING", f"/{name}") from error


def _manifest(
    bundle_id: str,
    payload: bytes,
    view: View,
    graph: RenderGraph,
    validation: ValidationResult,
    engine: Engine,
    fonts: list[dict[str, str]],
    icons: dict[str, VerifiedIcon],
    size: tuple[int, int],
    scale: float,
    files: dict[str, bytes],
    limits: Limits,
) -> dict[str, Any]:
    """FR-047. No timestamps or host paths, so the same input stays comparable across machines."""
    packs = catalog().packs
    return {
        "manifest_version": "1.1.0",
        "status": "complete",
        "bundle_id": bundle_id,
        "package_version": __version__,
        "schema_version": validation.schema_version,
        "catalog_version": catalog().version,
        "validation": {
            "mode": validation.mode,
            "scope": validation.validation_scope,
            "draft": validation.draft,
            "generic_fallbacks": [item.model_dump(mode="json") for item in graph.fallbacks],
        },
        "input": {"sha256": _digest(payload), "bytes": len(payload)},
        "view": {
            "id": view.id,
            "title": view.title,
            "grouping": view.grouping,
            "direction": view.direction,
            "style": view.style,
            "legend": view.legend,
        },
        "engine": {
            "graphviz": engine.version,
            "diagrams": metadata.version("diagrams"),
            "python_graphviz": metadata.version("graphviz"),
            "python": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "isolation": ISOLATION,
        "limits": limits.report(),
        "fonts": fonts,
        "assets": sorted(
            (
                {
                    "source": icon.source,
                    "reference": icon.reference,
                    "pack": icon.pack,
                    "sha256": icon.sha256,
                    "source_version": packs[icon.pack].source_version,
                }
                for icon in icons.values()
            ),
            key=lambda item: item["reference"],
        ),
        "rights": rights_report(graph),
        "png": {"width": size[0], "height": size[1], "scale": scale},
        "artifacts": {
            name: {"bytes": len(data), "sha256": _digest(data), "media_type": MEDIA_TYPES[name]}
            for name, data in sorted(files.items())
        },
    }


def _draw(
    payload: bytes,
    model: Architecture,
    view: View,
    graph: RenderGraph,
    validation: ValidationResult,
    root: OutputRoot,
    engine: Engine,
    limits: Limits,
) -> tuple[str, dict[str, bytes], list[Diagnostic]]:
    icons = verified_icons(graph, limits)
    dot = build_dot(graph, icons)
    with root.request() as (directory, request):
        fonts = _write_request(directory, request, dot, icons, limits)
        run_engine(engine, request, limits)
        check_fonts_used(_read_output(directory, ENGINE_LOG, limits), request)
        raw_svg = _read_output(directory, "diagram.svg", limits)
        png = _read_output(directory, "diagram.png", limits)
    size = check_png(png, limits)
    svg = finalize_svg(raw_svg, icons, limits)
    tree = check_svg(svg, {icon.sha256 for icon in icons.values()})
    check_undistorted(tree)
    check_content(tree, graph, icons)
    scale = png_scale(tree, size, limits)
    if scale < 1:
        warning = diagnostic("RENDER_PNG_SCALED", "/png", severity="warning")
        validation = validation.model_copy(
            update={"diagnostics": [*validation.diagnostics, warning]}
        )
    files = {
        "diagram.svg": svg,
        "diagram.png": png,
        "model.json": payload,
        "view.json": _json(
            {
                "view": view.model_dump(mode="json"),
                "excluded_ids": validation.excluded_ids,
                "graph": graph.model_dump(mode="json"),
            }
        ),
        "diagnostics.json": _json(
            {
                "mode": validation.mode,
                "draft": validation.draft,
                "validation_scope": validation.validation_scope,
                "diagnostics": [item.model_dump(mode="json") for item in validation.diagnostics],
            }
        ),
    }
    bundle_id = f"{model.metadata.id}--{view.id}--{secrets.token_hex(8)}"
    manifest = _manifest(
        bundle_id,
        payload,
        view,
        graph,
        validation,
        engine,
        fonts,
        icons,
        size,
        scale,
        files,
        limits,
    )
    return bundle_id, files | {"manifest.json": _json(manifest)}, validation.diagnostics


def render_model(
    payload: bytes,
    output: str,
    *,
    mode: Mode = "strict",
    view_id: str | None = None,
    limits: Limits = LIMITS,
) -> RenderResult:
    """Validation is unconditional: without a validated model there is nothing to draw."""
    result = RenderResult(valid=False, mode=mode, draft=mode == "lenient")
    try:
        validation, model = validate_model(payload, mode=mode, view_id=view_id)
        result = RenderResult(**validation.model_dump())
        if model is None:
            return result
        view = next(item for item in model.views if item.id == validation.selected_view)
        graph = map_view(model, view, mode, limits)
        result.diagnostics = [
            *validation.diagnostics,
            *(
                diagnostic(
                    "RENDER_GENERIC_FALLBACK", "/views", fallback.entity_id, severity="warning"
                )
                for fallback in graph.fallbacks
            ),
        ]
        validation = validation.model_copy(update={"diagnostics": result.diagnostics})
        engine = find_engine()
        with OutputRoot(output) as root:
            bundle_id, files, diagnostics = _draw(
                payload, model, view, graph, validation, root, engine, limits
            )
            path = root.publish(bundle_id, files)
    except RenderFailure as failure:
        result.diagnostics = [*result.diagnostics, failure.diagnostic()]
        return result
    result.rendered = True
    result.diagnostics = diagnostics
    result.pending_checks = []
    result.bundle_id = bundle_id
    result.bundle_path = str(path)
    result.rights = rights_report(graph)
    result.artifacts = [
        Artifact(
            name=name,
            path=str(path / name),
            bytes=len(data),
            sha256=_digest(data),
            media_type=MEDIA_TYPES[name],
        )
        for name, data in sorted(files.items())
    ]
    return result
