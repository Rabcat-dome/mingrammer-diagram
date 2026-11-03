"""M4-04 and NFR-007: measure render time and where the limits bind, on views of real icons.

Cold is a new CLI process per run. Warm is a further run in one process that has already rendered.
With a few runs, p95 is close to the slowest run, so read it as that. This sets no release threshold.
"""

import argparse
import json
import math
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from render_helpers import codes, encode, icon_chain, icon_model, manifest_of, render, svg_root  # noqa: E402
from visual_helpers import engine_version  # noqa: E402

from cloud_architecture_diagrams import __version__  # noqa: E402
from cloud_architecture_diagrams.catalog import catalog  # noqa: E402
from cloud_architecture_diagrams.render import exit_status  # noqa: E402
from cloud_architecture_diagrams.render.limits import LIMITS  # noqa: E402

BENCHMARKS = [("small", 30, 50), ("medium", 100, 150), ("large", 150, 225), ("upper", 197, 300)]
SCAN = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 197]


def nearest_rank(values: list[float], share: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(share * len(ordered)) - 1)]


def summary(values: list[float]) -> dict[str, Any]:
    return {
        "runs": [round(item, 3) for item in values],
        "p50": round(statistics.median(values), 3),
        "p95": round(nearest_rank(values, 0.95), 3),
    }


def outcome(model: dict[str, Any], output: Path) -> dict[str, Any]:
    result = render(model, output)
    found: dict[str, Any] = {"exit": exit_status(result), "codes": codes(result)}
    if result.rendered:
        root = svg_root(result)
        width = float(root.get("width", "0").removesuffix("pt")) * 96 / 72
        height = float(root.get("height", "0").removesuffix("pt")) * 96 / 72
        found |= {
            "full_size": [round(width), round(height)],
            "full_megapixels": round(width * height / 1e6, 1),
            "png": manifest_of(result)["png"],
            "warnings": sorted(
                {item.code for item in result.diagnostics if item.severity == "warning"}
            ),
        }
        for artifact in result.artifacts:
            if artifact.name in {"diagram.png", "diagram.svg"}:
                found[f"{artifact.name}_bytes"] = artifact.bytes
    return found


def measure(runs: int, scratch: Path) -> dict[str, Any]:
    benchmarks = []
    for name, entities, relationships in BENCHMARKS:
        model = icon_model(entities, relationships)
        payload = encode(model)
        cold = []
        for _ in range(runs):
            started = time.perf_counter()
            subprocess.run(
                [
                    "uv",
                    "run",
                    "--frozen",
                    "cloud-diagrams",
                    "render",
                    "--output",
                    str(scratch / name),
                ],
                input=payload,
                cwd=ROOT,
                capture_output=True,
                timeout=180,
                check=False,
            )
            cold.append(time.perf_counter() - started)
        render(model, scratch / name)
        warm = []
        for _ in range(runs):
            started = time.perf_counter()
            result = render(model, scratch / name)
            warm.append(time.perf_counter() - started)
            assert result.rendered or codes(result)
        benchmarks.append(
            {
                "name": name,
                "entities": entities,
                "relationships": relationships,
                "outcome": outcome(model, scratch / name),
                "cold_seconds": summary(cold),
                "warm_seconds": summary(warm),
            }
        )
    labeled = [
        {"entities": size, "relationships": round(size * 1.5)}
        | outcome(icon_model(size, round(size * 1.5)), scratch / "scan")
        for size in SCAN
    ]
    line = [{"entities": size} | outcome(icon_chain(size), scratch / "scan") for size in SCAN]
    over_entities = icon_model(LIMITS.view_entities + 1, 0)
    over_relationships = icon_model(100, LIMITS.view_relationships + 1)
    return {
        "package": __version__,
        "catalog": catalog().version,
        "engine": engine_version(),
        "python": platform.python_version(),
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "macos": platform.mac_ver()[0],
        "cpu": subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "memory_gib": round(
            int(
                subprocess.run(
                    ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=True
                ).stdout
            )
            / 2**30
        ),
        "limits": LIMITS.report(),
        "benchmarks": benchmarks,
        "labeled_scan": labeled,
        "line_scan": line,
        "rejections": {
            "over_entities": outcome(over_entities, scratch / "over"),
            "over_relationships": outcome(over_relationships, scratch / "over"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=7)
    arguments = parser.parse_args()
    # The renderer refuses a root with a symbolic link in its path, as $TMPDIR has on macOS.
    scratch = Path(tempfile.mkdtemp(dir=ROOT / "reports"))
    try:
        report = measure(arguments.runs, scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    arguments.output.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
