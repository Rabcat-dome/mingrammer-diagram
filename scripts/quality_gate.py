"""Run every implemented lane; any failure/timeout/missing tool fails aggregate."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    python = sys.executable
    commands = {
        "docs-contract": [python, "scripts/repository_checks.py", "docs"],
        "secrets": [python, "scripts/repository_checks.py", "secrets"],
        "lint": [python, "-m", "ruff", "check", "src", "scripts", "tests"],
        "format": [python, "-m", "ruff", "format", "--check", "src", "scripts", "tests"],
        "types": [python, "-m", "mypy"],
        "workflow": ["actionlint"],
        "schema-core": [
            python,
            "-m",
            "pytest",
            "--ignore=tests/test_claude_plugin.py",
            "--junitxml=reports/tests.xml",
            "-q",
        ],
        "claude-plugin": [
            python,
            "-m",
            "pytest",
            "tests/test_claude_plugin.py",
            "--junitxml=reports/claude-plugin-tests.xml",
            "-q",
        ],
        "package-build": [python, "-m", "build", "--no-isolation", "--outdir", "reports/dist"],
        "package-contents": [python, "scripts/repository_checks.py", "package"],
    }
    # A stale wheel must not stand in for a build that failed or changed version.
    shutil.rmtree(REPORTS / "dist", ignore_errors=True)
    results = []
    for name, command in commands.items():
        started = time.monotonic()
        log = REPORTS / (name + ".log")
        try:
            with log.open("w") as output:
                process = subprocess.run(
                    command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=180
                )
            status = "passed" if process.returncode == 0 else "failed"
        except (OSError, subprocess.TimeoutExpired):
            status = "failed"
            log.write_text("Required check could not execute or exceeded its timeout.\n")
        results.append(
            {"check": name, "status": status, "seconds": round(time.monotonic() - started, 3)}
        )
        print(f"{name}: {status}", flush=True)
    passed = all(result["status"] == "passed" for result in results)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    report = {
        "scope": "M1 core foundation and M7 Claude plugin package contract",
        "passed": passed,
        "checks": results,
        "commit": commit,
        "working_tree_dirty": dirty,
        "source_ref": None if dirty else commit,
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "source_digests": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for folder in [
                "src",
                "scripts",
                "tests",
                "schemas",
                ".github",
                ".claude-plugin",
                "plugins",
            ]
            for path in sorted((ROOT / folder).rglob("*"))
            if path.is_file() and path.suffix in {".py", ".json", ".yml", ".yaml"}
        },
        "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
        "runner_name": os.environ.get("RUNNER_NAME"),
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "deferred": {
            "catalog-license": "M2",
            "provider-semantics": "M2",
            "render-security": "M3",
            "render-smoke": "M3/M4",
            "visual-regression": "M4",
            "plugin-package": "M5",
            "claude-host-acceptance": "M7 (recorded manually; no Claude CLI or model call in CI)",
        },
        "review": "Recorded separately; no paid model API call in CI",
    }
    (REPORTS / "quality-gate.json").write_text(json.dumps(report, indent=2) + "\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a") as output:
            output.write(
                "## M1 quality gate\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n"
            )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
