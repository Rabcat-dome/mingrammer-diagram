"""Run every implemented lane; any failure/timeout/missing tool fails aggregate."""

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from repository_checks import source_digests

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
# A test lane passes only when it really ran tests, so an empty selection cannot look green.
TEST_LANES = {
    "schema-core": "tests.xml",
    "catalog-license": "catalog-license-tests.xml",
    "provider-semantics": "provider-semantics-tests.xml",
    "claude-plugin": "claude-plugin-tests.xml",
}


def executed_tests(name: str) -> int | None:
    report = TEST_LANES.get(name)
    if report is None or not (REPORTS / report).exists():
        return None
    root = ET.parse(REPORTS / report).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    return sum(int(suite.get("tests", 0)) - int(suite.get("skipped", 0)) for suite in suites)


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
            "--ignore=tests/test_catalog_license.py",
            "--ignore=tests/test_provider_semantics.py",
            "--junitxml=reports/tests.xml",
            "-q",
        ],
        "catalog-license": [python, "scripts/catalog_checks.py"],
        "provider-semantics": [
            python,
            "-m",
            "pytest",
            "tests/test_provider_semantics.py",
            "--junitxml=reports/provider-semantics-tests.xml",
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
    for stale in TEST_LANES.values():
        (REPORTS / stale).unlink(missing_ok=True)
    (REPORTS / "catalog-license.json").unlink(missing_ok=True)
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
        tests = executed_tests(name)
        if name in TEST_LANES and not tests:
            status = "failed"
        results.append(
            {
                "check": name,
                "status": status,
                "seconds": round(time.monotonic() - started, 3),
                **({} if tests is None else {"tests": tests}),
            }
        )
        print(f"{name}: {status}", flush=True)
    passed = all(result["status"] == "passed" for result in results)
    catalog_report = REPORTS / "catalog-license.json"
    release_blockers = (
        json.loads(catalog_report.read_text())["release_blockers"]
        if catalog_report.exists()
        else None
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    report = {
        "scope": "M1 core, M2 catalogs and semantics, and M7 Claude plugin package contract",
        "passed": passed,
        "checks": results,
        # A passing gate does not clear these; they block packaging and release until resolved.
        "release_blockers": release_blockers,
        "commit": commit,
        "working_tree_dirty": dirty,
        "source_ref": None if dirty else commit,
        "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "source_digests": source_digests(),
        "github_actions": os.environ.get("GITHUB_ACTIONS") == "true",
        "runner_name": os.environ.get("RUNNER_NAME"),
        "python": platform.python_version(),
        "system": platform.system(),
        "machine": platform.machine(),
        "deferred": {
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
            output.write("## Quality gate\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
