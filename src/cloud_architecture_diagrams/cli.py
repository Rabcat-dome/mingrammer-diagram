"""Data-only CLI. JSON results on stdout; no payloads or raw exception dumps."""

import argparse
import json
import sys
from typing import NoReturn

from . import __version__
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
        "commands": ["schema", "capabilities", "validate"],
        "validation_scope": "core_only",
        "pending_checks": ["catalog", "provider_rules", "render"],
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
    args = parser.parse_args()
    if args.command == "schema":
        report: object = Architecture.model_json_schema()
    elif args.command == "capabilities":
        report = capabilities()
    else:
        result = validate_json(
            sys.stdin.buffer.read(MAX_INPUT_BYTES + 1), mode=args.mode, view_id=args.view
        )
        # A rejected key can be non-ASCII, and the host's locale must not be able to break JSON.
        sys.stdout.buffer.write(result.model_dump_json().encode() + b"\n")
        return 0 if result.valid else 2
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return 0
