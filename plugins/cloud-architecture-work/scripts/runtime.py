"""Set up, check, list, prune or remove this plugin's runtime from a terminal."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from work_adapter import artifacts  # noqa: E402
from work_adapter.runtime import HOST_MODES, Runtime  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight", help="Check this machine and the private runtime")
    sub.add_parser("setup", help="Build or repair the private runtime; downloads on first use")
    sub.add_parser("list", help="List recent bundles")
    prune = sub.add_parser("prune", help="Report old bundles, and remove them with --apply")
    prune.add_argument("--older-than-days", type=float, required=True)
    prune.add_argument("--apply", action="store_true", help="Really delete them")
    sub.add_parser("remove", help="Delete the private runtime; bundles are kept")
    args = parser.parse_args()

    runtime = Runtime(ROOT)
    try:
        return run(args, runtime)
    except artifacts.ArtifactError:
        print(
            json.dumps(
                {
                    "code": "OUTPUT_ROOT_UNAVAILABLE",
                    "message": f"{runtime.output} cannot be read safely, so nothing was done.",
                    "remedy": "Keep symbolic links out of its path, and let this process read it.",
                },
                indent=2,
            )
        )
        return 1


def run(args: argparse.Namespace, runtime: Runtime) -> int:
    report: object
    status = 0
    if args.command == "preflight":
        preflight = runtime.preflight()
        report = {
            "plugin_version": runtime.version,
            "core_version": runtime.core_version(),
            "runtime": runtime.state(),
            "host_modes": HOST_MODES,
            **preflight,
        }
        status = 1 if preflight["blockers"] or runtime.state()["state"] != "ready" else 0
    elif args.command == "setup":
        report = runtime.setup()
        status = 0 if report.get("ready") else 1
    elif args.command == "list":
        report = artifacts.list_bundles(runtime.output, artifacts.MAX_LISTED)
    elif args.command == "prune":
        report = artifacts.prune(runtime.output, args.older_than_days, apply=args.apply)
    else:
        report = runtime.remove()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
