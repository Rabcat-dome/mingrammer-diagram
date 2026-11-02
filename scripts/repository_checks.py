"""Portable documentation/traceability, narrow credential-pattern and wheel-content checks."""

import hashlib
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    )
    return sorted({ROOT / path.decode() for path in output.split(b"\0") if path})


def anchors(text: str) -> set[str]:
    counts: Counter[str] = Counter()
    result: set[str] = set()
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and re.match(r"^#{1,6} ", line):
            base = re.sub(r"[^\w\- ]", "", line.lstrip("# ").lower()).replace(" ", "-")
            result.add(base if counts[base] == 0 else f"{base}-{counts[base]}")
            counts[base] += 1
    return result


def documentation() -> list[str]:
    errors: list[str] = []
    tracked = files()
    documents = [path for path in tracked if path.suffix == ".md"]
    requirements = (ROOT / "doc/requirements/requirements.md").read_text()
    milestones = (ROOT / "doc/project-management/milestones.md").read_text()
    decisions = (ROOT / "doc/project-management/decisions.md").read_text()
    definitions: set[str] = set()
    for text, pattern in [
        (requirements, r"^\| ((?:FR|NFR)-\d+) \|"),
        (requirements, r"^\| (T-\d+)\b"),
        (milestones, r"^\| (M\d+-\d+) \|"),
        (decisions, r"^\| ([DPO]-\d+) \|"),
    ]:
        ids = re.findall(pattern, text, re.MULTILINE)
        if not ids or len(ids) != len(set(ids)):
            errors.append("Missing or duplicate traceability definitions")
        definitions.update(ids)
    for path in documents:
        text = path.read_text(encoding="utf-8")
        name = str(path.relative_to(ROOT))
        if not text.endswith("\n") or re.search(r"[\u0e00-\u0e7f]", text):
            errors.append(f"{name}: require English Markdown and final newline")
        if sum(line.startswith("```") for line in text.splitlines()) % 2:
            errors.append(f"{name}: unbalanced fenced blocks")
        for identifier in re.findall(r"\b(?:FR-\d+|NFR-\d+|T-\d+|M\d+-\d+|[DPO]-\d+)\b", text):
            if identifier not in definitions:
                errors.append(f"{name}: undefined traceability ID {identifier}")
        for raw in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = urlsplit(raw.strip("<>"))
            if target.scheme:
                continue
            destination = (path.parent / unquote(target.path)).resolve() if target.path else path
            if Path(unquote(target.path)).is_absolute() or not destination.is_relative_to(ROOT):
                errors.append(f"{name}: local documentation link must stay inside the repository")
            elif not destination.exists():
                errors.append(f"{name}: missing local link")
            elif target.fragment and (
                destination.suffix != ".md"
                or unquote(target.fragment) not in anchors(destination.read_text())
            ):
                errors.append(f"{name}: missing Markdown anchor")
        for raw in re.findall(r"```json\n(.*?)\n```", text, re.DOTALL):
            try:
                json.loads(raw)
            except ValueError:
                errors.append(f"{name}: invalid fenced JSON")
    for path in tracked:
        if path.suffix == ".json":
            try:
                value = json.loads(path.read_text())
                if isinstance(value, dict):
                    for source, expected in value.get("source_digests", {}).items():
                        source_path = (
                            "spikes/s04-runtime/" + source
                            if path.name == "S04-runtime-proof.json"
                            else source
                        )
                        if ref := value.get("source_ref"):
                            content = subprocess.check_output(
                                ["git", "show", f"{ref}:{source_path}"],
                                cwd=ROOT,
                                stderr=subprocess.DEVNULL,
                            )
                        else:
                            content = (ROOT / source_path).read_bytes()
                        if hashlib.sha256(content).hexdigest() != expected:
                            errors.append(f"{path.name}: source proof hash mismatch")
            except (ValueError, OSError, subprocess.CalledProcessError):
                errors.append(f"{path.name}: invalid JSON or inaccessible source proof")
    return errors


def credentials() -> list[str]:
    # Deliberately narrow: not an entropy scanner, history scan or security audit.
    pattern = re.compile(
        r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,}|sk-[A-Za-z0-9_-]{32,}"
        r"|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    )
    errors = []
    for path in files():
        if path.suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".toml", ".lock"}:
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            errors.append(f"{path.relative_to(ROOT)}: possible credential pattern (value withheld)")
    return errors


def package() -> list[str]:
    # A build can exit 0 and still ship no code, so compare the wheel with its source tree.
    source = ROOT / "src"
    expected = {
        str(path.relative_to(source))
        for path in source.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }
    wheels = sorted((ROOT / "reports/dist").glob("*.whl"))
    if len(wheels) != 1:
        return [f"reports/dist: expected one wheel, found {len(wheels)}"]
    with zipfile.ZipFile(wheels[0]) as wheel:
        shipped = {name for name in wheel.namelist() if ".dist-info/" not in name}
    return [f"{wheels[0].name}: differs from src: {name}" for name in sorted(expected ^ shipped)]


def main() -> int:
    check = sys.argv[1] if len(sys.argv) == 2 else "docs"
    errors = (
        documentation()
        if check == "docs"
        else credentials()
        if check == "secrets"
        else package()
        if check == "package"
        else ["Unknown check"]
    )
    for error in errors:
        print(error)
    print(json.dumps({"check": check, "passed": not errors, "errors": len(errors)}))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
