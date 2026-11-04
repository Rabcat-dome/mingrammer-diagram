"""T-010 and M6-01: reproduce the core at one commit from a new clone and a runtime that shares nothing.

It clones from GitHub, downloads its own Python and packages into a new folder with HOME and every
cache pointed there, builds the wheel, installs it from the hash-locked requirements, and renders
every reference view from outside the clone. Each result is compared with the baselines at that
commit. It runs on one machine, so it proves a clean runtime and not a second machine.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://github.com/Rabcat-dome/mingrammer-diagram.git"
PYTHON = "3.13.7"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_digest(root: Path) -> str:
    """What a proof depends on, so a later commit that changes none of it keeps the proof valid."""
    paths = [root / "uv.lock", root / "pyproject.toml", root / "tests/baselines/baselines.json"]
    paths += sorted(
        path
        for folder in ("src", "tests/fixtures/references")
        for path in (root / folder).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    state = hashlib.sha256()
    for path in paths:
        state.update(path.relative_to(root).as_posix().encode())
        state.update(path.read_bytes())
    return state.hexdigest()


def run(command: list[str], *, env: dict[str, str], cwd: Path, stdin: bytes | None = None) -> bytes:
    result = subprocess.run(
        command, env=env, cwd=cwd, input=stdin, capture_output=True, timeout=600, check=False
    )
    if result.returncode:
        raise SystemExit(f"{command[0]} failed: {result.stderr.decode()[-2000:]}")
    return result.stdout


def clean_environment(base: Path) -> dict[str, str]:
    home = base / "home"
    home.mkdir()
    # Graphviz and uv are the host tools T-010 lists, so only their folder stays on the path.
    return {
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
        "HOME": str(home),
        "UV_CACHE_DIR": str(base / "uv-cache"),
        "UV_PYTHON_INSTALL_DIR": str(base / "python"),
        "UV_PYTHON_PREFERENCE": "only-managed",
        "UV_NO_CONFIG": "1",
        "LANG": "en_US.UTF-8",
    }


def render_views(cli: Path, clone: Path, output: Path, env: dict[str, str]) -> list[dict[str, Any]]:
    record = json.loads((clone / "tests/baselines/baselines.json").read_text())
    results = []
    elsewhere = output.parent / "elsewhere"
    elsewhere.mkdir(exist_ok=True)
    for key, expected in sorted(record["views"].items()):
        scenario, view = key.split("--", 1)
        model = (clone / f"tests/fixtures/references/{scenario}.json").read_bytes()
        answer = json.loads(
            run(
                [str(cli), "render", "--output", str(output), "--view", view],
                env=env,
                cwd=elsewhere,
                stdin=model,
            )
        )
        bundle = Path(answer["bundle_path"])
        manifest = json.loads((bundle / "manifest.json").read_text())
        graph = json.loads((bundle / "view.json").read_text())["graph"]
        baseline = json.loads((clone / f"tests/baselines/{key}.graph.json").read_text())
        results.append(
            {
                "view": key,
                "rendered": answer["rendered"],
                "svg_matches": digest((bundle / "diagram.svg").read_bytes()) == expected["svg"],
                "png_matches": digest((bundle / "diagram.png").read_bytes()) == expected["png"],
                "graph_matches": graph == baseline,
                "model_matches": json.loads((bundle / "model.json").read_text())
                == json.loads(model),
                "manifest_versions": {
                    k: manifest[k]
                    for k in ("package_version", "catalog_version", "engine")
                    if k in manifest
                },
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Full commit SHA to reproduce")
    parser.add_argument("--output", required=True, type=Path, help="Where to write the proof")
    parser.add_argument("--expected-wheel", help="SHA-256 of the wheel this commit should build")
    arguments = parser.parse_args()
    if arguments.expected_wheel == "":
        parser.error("--expected-wheel is empty, so nothing would be compared")
    # The renderer refuses a root with a symbolic link in its path, as $TMPDIR has on macOS.
    base = ROOT / "reports/reproduction"
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True, mode=0o700)
    env = clean_environment(base)
    clone = base / "clone"
    # The clone alone uses the owner's Git credentials, since the repository is private.
    subprocess.run(["git", "clone", "--quiet", ORIGIN, str(clone)], check=True, timeout=300)
    subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", "--detach", arguments.commit],
        check=True,
        timeout=60,
    )
    run(["uv", "python", "install", PYTHON], env=env, cwd=base)
    python = run(["uv", "python", "find", PYTHON], env=env, cwd=base).decode().strip()

    # Route one: the lock, with no development tools.
    locked_env = env | {"UV_PROJECT_ENVIRONMENT": str(base / "locked")}
    run(["uv", "sync", "--locked", "--no-dev", "--python", PYTHON], env=locked_env, cwd=clone)
    locked = render_views(base / "locked/bin/cloud-diagrams", clone, base / "out-locked", env)

    # Route two: build the wheel with the locked build tools, and install only that.
    build_env = env | {"UV_PROJECT_ENVIRONMENT": str(base / "build")}
    run(["uv", "sync", "--locked", "--python", PYTHON], env=build_env, cwd=clone)
    run(
        [
            str(base / "build/bin/python"),
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(base / "dist"),
        ],
        env=env,
        cwd=clone,
    )
    wheels = sorted((base / "dist").glob("*.whl"))
    assert len(wheels) == 1, wheels
    requirements = base / "requirements.txt"
    requirements.write_bytes(
        run(
            [
                "uv",
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--format",
                "requirements-txt",
                "--python",
                PYTHON,
            ],
            env=locked_env,
            cwd=clone,
        )
    )
    run(["uv", "venv", "--python", PYTHON, str(base / "wheel")], env=env, cwd=base)
    target = str(base / "wheel/bin/python")
    run(
        ["uv", "pip", "install", "--python", target, "--require-hashes", "-r", str(requirements)],
        env=env,
        cwd=base,
    )
    run(
        ["uv", "pip", "install", "--python", target, "--no-deps", str(wheels[0])], env=env, cwd=base
    )
    installed = render_views(base / "wheel/bin/cloud-diagrams", clone, base / "out-wheel", env)

    capabilities = json.loads(
        run([str(base / "wheel/bin/cloud-diagrams"), "capabilities"], env=env, cwd=base)
    )
    wheel_digest = digest(wheels[0].read_bytes())
    packages = (
        run(["uv", "pip", "freeze", "--python", target], env=env, cwd=base).decode().splitlines()
    )
    checks = ("rendered", "svg_matches", "png_matches", "graph_matches", "model_matches")
    report = {
        "commit": arguments.commit,
        "source_digest": source_digest(clone),
        "system": f"{platform.system()} {platform.release()} {platform.machine()}",
        "python": python.replace(str(base), "<new folder>"),
        "python_version": run([python, "--version"], env=env, cwd=base).decode().strip(),
        "uv": run(["uv", "--version"], env=env, cwd=base).decode().strip(),
        "engine": subprocess.run(
            ["dot", "-V"], env=env, capture_output=True, text=True, check=True
        ).stderr.strip(),
        "core": capabilities["package_version"],
        "catalog": capabilities["catalog_version"],
        "wheel": wheels[0].name,
        "wheel_sha256": wheel_digest,
        "wheel_matches_expected": None
        if arguments.expected_wheel is None
        else wheel_digest == arguments.expected_wheel,
        "installed_packages": len(packages),
        "views": len(installed),
        "locked_route_all_match": all(all(item[key] for key in checks) for item in locked),
        "wheel_route_all_match": all(all(item[key] for key in checks) for item in installed),
        "routes_agree": locked == installed,
        "mismatches": [
            item["view"] for item in [*locked, *installed] if not all(item[key] for key in checks)
        ],
    }
    arguments.output.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if not report["mismatches"] and report["wheel_matches_expected"] is not False else 1


if __name__ == "__main__":
    os.umask(0o077)
    sys.exit(main())
