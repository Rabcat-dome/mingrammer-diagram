"""Data-only CLI. JSON results on stdout; no payloads or raw exception dumps."""

import argparse
import json
import signal
import sys
from types import FrameType
from typing import NoReturn

from . import __version__
from .catalog import MAX_RESULTS, catalog
from .models import MAX_DEPTH, MAX_ENTITIES, MAX_INPUT_BYTES, Architecture
from .render import BUNDLE_FILES, exit_status, render_model
from .render.errors import RenderFailure
from .render.execution import host_blockers
from .render.limits import LIMITS
from .render.paths import INTERRUPTS
from .validation import Mode, validate_json


class Parser(argparse.ArgumentParser):
    """Exit 2 means an invalid model, so usage errors take the conventional EX_USAGE instead."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(64, f"{self.prog}: error: {message}\n")


def capabilities() -> dict[str, object]:
    blockers = host_blockers()
    return {
        "package_version": __version__,
        "schema_version": "1.0.0",
        "catalog_version": catalog().version,
        "commands": ["schema", "capabilities", "validate", "catalog", "render"],
        "validation_scope": "core_catalog_provider",
        "pending_checks": [],
        "release_blockers": catalog().release_blockers(),
        # This host's readiness rather than the code's: `render` fails closed without either.
        "render_available": not blockers,
        "render": {
            "formats": ["svg", "png"],
            "host_blockers": blockers,
            "requires": {"graphviz": "dot on PATH", "isolation": "macOS sandbox-exec"},
            "bundle": BUNDLE_FILES,
            "limits": LIMITS.report(),
        },
        "docker_required": False,
        "model_api_required": False,
        "limits": {
            "input_bytes": MAX_INPUT_BYTES,
            "json_depth": MAX_DEPTH,
            "entities": MAX_ENTITIES,
            "relationships": 4000,
            "views": 32,
            "diagnostic_errors": 100,
        },
    }


def _interrupt(_signum: int, _frame: FrameType | None) -> None:
    # The exception unwinds through the renderer's cleanup, which a second signal must not cut off.
    for item in INTERRUPTS:
        signal.signal(item, signal.SIG_IGN)
    raise RenderFailure("RENDER_INTERRUPTED")


def _render(output: str, mode: Mode, view: str | None) -> int:
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    previous = {item: signal.signal(item, _interrupt) for item in INTERRUPTS}
    try:
        result = render_model(payload, output, mode=mode, view_id=view)
    finally:
        for item, handler in previous.items():
            signal.signal(item, handler)
    sys.stdout.buffer.write(result.model_dump_json().encode() + b"\n")
    return exit_status(result)


def main() -> int:
    parser = Parser(prog="cloud-diagrams")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema", help="Print the versioned JSON Schema")
    sub.add_parser("capabilities", help="Print implemented capabilities and pending layers")
    validate = sub.add_parser("validate", help="Validate bounded UTF-8 JSON from stdin")
    validate.add_argument("--mode", choices=["strict", "lenient"], default="strict")
    validate.add_argument("--view", default=None)
    render = sub.add_parser(
        "render", help="Validate JSON from stdin, then draw one view to a bundle"
    )
    render.add_argument(
        "--output", required=True, help="Output root: a real, private directory, no symlinks"
    )
    render.add_argument("--mode", choices=["strict", "lenient"], default="strict")
    render.add_argument("--view", default=None, help="View ID; the model's first view by default")
    types = sub.add_parser("catalog", help="Search provider and Kubernetes types (bounded)")
    types.add_argument(
        "--provider", choices=["aws", "azure", "gcp", "huawei", "onprem", "external"]
    )
    types.add_argument("--taxonomy", default=None)
    types.add_argument("--entity", choices=["resource", "boundary", "scope"])
    types.add_argument("--query", default=None, help="Text in the ID, display name or native ID")
    types.add_argument("--type", dest="type_id", default=None, help="One exact type ID")
    types.add_argument("--kubernetes", action="store_true", help="Only Kubernetes-mapped types")
    types.add_argument("--taxonomy-list", action="store_true", help="List the taxonomy IDs instead")
    types.add_argument("--limit", type=int, default=50, help=f"At most {MAX_RESULTS}")
    args = parser.parse_args()
    if args.command == "render":
        return _render(args.output, args.mode, args.view)
    if args.command == "schema":
        report: object = Architecture.model_json_schema()
    elif args.command == "capabilities":
        report = capabilities()
    elif args.command == "catalog":
        report = (
            {
                "catalog_version": catalog().version,
                "taxonomy": [entry.model_dump() for entry in catalog().taxonomy],
            }
            if args.taxonomy_list
            else catalog().search(
                provider=args.provider,
                taxonomy=args.taxonomy,
                entity=args.entity,
                query=args.query,
                type_id=args.type_id,
                kubernetes=args.kubernetes,
                limit=args.limit,
            )
        )
    else:
        result = validate_json(
            sys.stdin.buffer.read(MAX_INPUT_BYTES + 1), mode=args.mode, view_id=args.view
        )
        # A rejected key can be non-ASCII, and the host's locale must not be able to break JSON.
        sys.stdout.buffer.write(result.model_dump_json().encode() + b"\n")
        return 0 if result.valid else 2
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0
