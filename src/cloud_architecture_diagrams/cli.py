"""Data-only CLI. JSON results on stdout; no payloads or raw exception dumps."""

import argparse
import json
import sys
from typing import NoReturn

from . import __version__
from .catalog import MAX_RESULTS, catalog
from .models import MAX_DEPTH, MAX_ENTITIES, MAX_INPUT_BYTES, Architecture
from .validation import validate_json


class Parser(argparse.ArgumentParser):
    """Exit 2 means an invalid model, so usage errors take the conventional EX_USAGE instead."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(64, f"{self.prog}: error: {message}\n")


def capabilities() -> dict[str, object]:
    return {
        "package_version": __version__,
        "schema_version": "1.0.0",
        "catalog_version": catalog().version,
        "commands": ["schema", "capabilities", "validate", "catalog"],
        "validation_scope": "core_catalog_provider",
        "pending_checks": ["render"],
        "release_blockers": catalog().release_blockers(),
        "render_available": False,
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


def main() -> int:
    parser = Parser(prog="cloud-diagrams")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("schema", help="Print the versioned JSON Schema")
    sub.add_parser("capabilities", help="Print implemented capabilities and pending layers")
    validate = sub.add_parser("validate", help="Validate bounded UTF-8 JSON from stdin")
    validate.add_argument("--mode", choices=["strict", "lenient"], default="strict")
    validate.add_argument("--view", default=None)
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
