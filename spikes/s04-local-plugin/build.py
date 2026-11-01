"""Build one self-contained experimental plugin; no account upload or install."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NAME = "cloud-architecture-diagrams"
VERSION = "0.1.0-alpha.1"
OUTPUT = HERE / "output"
PACKAGE = OUTPUT / NAME
OUTPUT.mkdir(exist_ok=True)
if PACKAGE.exists():
    shutil.rmtree(PACKAGE)
for name in ["scripts", "runtime", "skills/cloud-architecture-runtime", ".codex-plugin"]:
    (PACKAGE / name).mkdir(parents=True, exist_ok=True)
interface = {"displayName": "Cloud Architecture Diagrams (S04)", "shortDescription": "Local runtime pilot",
             "longDescription": "Experimental local runtime with a versioned installer, preflight and three-node SVG/PNG fixture. Provider catalogs and production architecture rendering are later milestones.",
             "developerName": "Visarut", "category": "Productivity", "capabilities": ["Read", "Write"],
             "defaultPrompt": "Check the local runtime and render the S04 three-node fixture."}
manifest = {"$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "name": NAME, "version": VERSION,
            "description": "Experimental local architecture diagram runtime for S04.", "author": {"name": "Visarut"},
            "extensions": {"com.openai": {"requires_local_executor": True, "interface": interface}}}
mcp = {"$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json", "mcpServers": {
    "architecture-runtime": {"type": "stdio", "command": "python3", "args": ["${PLUGIN_ROOT}/scripts/launch.py"], "cwd": "${PLUGIN_ROOT}"}}}
def save(name, value):
    (PACKAGE / name).write_text(json.dumps(value, indent=2) + "\n")
save("plugin.json", manifest)
save("mcp.json", mcp)
save(".mcp.json", {"mcpServers": mcp["mcpServers"]})
save(".codex-plugin/plugin.json", {"name": NAME, "version": VERSION, "description": manifest["description"],
      "author": manifest["author"], "skills": "./skills/", "mcpServers": "./.mcp.json",
      "requires_local_executor": True, "interface": interface})
(PACKAGE / "README.md").write_text('''# Cloud Architecture Diagrams: S04 local pilot

Version: 0.1.0-alpha.1. Experimental three-node runtime proof, not the complete provider renderer.

Requires a local-execution desktop host, Python 3.10+ on the host, and a running Linux Docker engine. macOS ARM64 is the tested host; other host systems remain unverified. No model API key, public rendering service or central server is required.

After installing/extracting this plugin, run `python3 scripts/setup.py` from its root. This downloads public dependencies and builds a versioned local renderer image. Repeat on each machine. Keep Docker running. The MCP entrypoint is `python3 scripts/launch.py`; the host resolves `${PLUGIN_ROOT}` in mcp.json. No dependencies are installed during MCP startup.

Call get_runtime_info, then render_fixture with exactly three literal labels. Tools return a PNG and local paths to SVG, PNG, DOT, request JSON and manifest under `~/Documents/CloudArchitectureDiagrams`. Outputs remain until the user removes them; this pilot has no automatic retention cleanup. read_fixture_artifact reads only those bundle files.

Rendering runs without network access, with one CPU, 1 GiB memory/no swap, 64 PIDs, read-only root, dropped capabilities and a 256 MiB temporary filesystem. Only the designated output folder is bound from the host. Setup needs network access. Re-run setup for a changed runtime source/version; missing dependencies fail with a setup instruction.

Provider service catalogs, architecture JSON semantics, detailed Kubernetes, icon clearance, polished installation/upgrade/removal and cross-machine release acceptance are later milestones. SVG uses font-family references rather than embedded fonts; PNG is the current visual check. Actual Work chat preview/export and independent Astra review remain separate acceptance evidence. Source licenses/notices and fully frozen transitive OS dependencies need release packaging work.
''')
for name in ["common.py", "setup.py", "launch.py"]:
    shutil.copyfile(HERE / name, PACKAGE / "scripts" / name)
shutil.copyfile(HERE / "local_server.py", PACKAGE / "runtime/local_server.py")
for name in ["render_fixture.py", "requirements.lock"]:
    shutil.copyfile(REPO / "spikes/s04-runtime" / name, PACKAGE / "runtime" / name)
(PACKAGE / "runtime/Dockerfile").write_text('''FROM python:3.13-alpine3.22@sha256:e81548ac35b07a3bd4805f275107592ef458b1e893c0e04d45aedaa19416cca5
RUN apk add --no-cache graphviz=12.2.1-r0 fontconfig=2.15.0-r3 font-noto=2025.05.01-r0 font-noto-thai=2025.05.01-r0
WORKDIR /app
COPY requirements.lock .
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY render_fixture.py local_server.py ./
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/tmp
USER 10001:10001
ENTRYPOINT ["python", "/app/local_server.py"]
''')
(PACKAGE / "skills/cloud-architecture-runtime/SKILL.md").write_text('''---
name: cloud-architecture-runtime
description: Use to preflight the experimental local architecture renderer and produce the S04 three-node SVG/PNG fixture.
---

This is an S04 pilot, not the five-environment release renderer. It provides local runtime verification and a synthetic three-node fixture only.

Call get_runtime_info first. If runtime setup is missing, resolve the plugin root two directories above this file and run its scripts/setup.py with Python 3. It builds the local container once; a running Linux Docker engine is required. Do not install into another plugin's cache or send data to a public rendering service.

Call render_fixture with exactly three literal labels. Use read_fixture_artifact for exported SVG/PNG/JSON/manifest data. The returned host_paths are confined to the local CloudArchitectureDiagrams output directory; inspect them and attach the verified PNG/SVG using the host's normal local-file mechanisms. Do not claim successful Work preview/download until observed there.

Never execute user-authored Python, arbitrary Graphviz attributes or paths. Do not fabricate provider catalog support. Record startup/tool/label/artifact failures accurately. Rendering runs in a network-disabled local container; plugin install/build can download public dependencies.
''')
archive = OUTPUT / (NAME + "-" + VERSION + ".zip")
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(PACKAGE.rglob("*")):
        if p.is_file():
            z.write(p, NAME + "/" + str(p.relative_to(PACKAGE)))
with zipfile.ZipFile(archive) as z:
    assert len({p.split("/")[0] for p in z.namelist()}) == 1
    for p in z.namelist():
        assert ".." not in Path(p).parts
        if p.endswith(".json"):
            json.loads(z.read(p))
assert len(interface["shortDescription"]) <= 30
print(json.dumps({"package": str(PACKAGE), "archive": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(), "files": len([p for p in PACKAGE.rglob('*') if p.is_file()])}))
