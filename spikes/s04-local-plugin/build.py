"""Build a self-contained native plugin; no Docker, upload or installation."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NAME = 'cloud-architecture-diagrams'
VERSION = '0.1.0-alpha.2'
OUTPUT = HERE / 'output'
PACKAGE = OUTPUT / NAME
OUTPUT.mkdir(exist_ok=True)
if PACKAGE.exists():
    shutil.rmtree(PACKAGE)
for name in ['scripts', 'runtime', 'assets/fonts', 'skills/cloud-architecture-runtime', '.codex-plugin']:
    (PACKAGE / name).mkdir(parents=True, exist_ok=True)
interface = {'displayName': 'Cloud Architecture Diagrams (S04)', 'shortDescription': 'Native local runtime pilot',
    'longDescription': 'Experimental local Python/Graphviz runtime with setup, preflight, stdio tools and direct script execution. No Docker or central server required. Three-node S04 fixture only.',
    'developerName': 'Visarut', 'category': 'Productivity', 'capabilities': ['Read', 'Write'],
    'defaultPrompt': 'Check the native local runtime and render the S04 three-node fixture.'}
manifest = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json', 'name': NAME, 'version': VERSION,
    'description': 'Experimental native local architecture diagram runtime for S04.', 'author': {'name': 'Visarut'},
    'extensions': {'com.openai': {'requires_local_executor': True, 'interface': interface}}}
mcp = {'$schema': 'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json', 'mcpServers': {
    'architecture-runtime': {'type': 'stdio', 'command': 'python3', 'args': ['-B', '${PLUGIN_ROOT}/scripts/launch.py'], 'cwd': '${PLUGIN_ROOT}'}}}

def save(name, value):
    (PACKAGE / name).write_text(json.dumps(value, indent=2) + '\n')

save('plugin.json', manifest)
save('mcp.json', mcp)
save('.mcp.json', {'mcpServers': mcp['mcpServers']})
save('.codex-plugin/plugin.json', {'name': NAME, 'version': VERSION, 'description': manifest['description'],
    'author': manifest['author'], 'skills': './skills/', 'mcpServers': './.mcp.json',
    'requires_local_executor': True, 'interface': interface})
for name in ['common.py', 'setup.py', 'launch.py', 'render.py']:
    shutil.copyfile(HERE / name, PACKAGE / 'scripts' / name)
for name in ['local_server.py', 'artifact_store.py', 'execution.py', 'native_worker.py', 'cli.py']:
    shutil.copyfile(HERE / name, PACKAGE / 'runtime' / name)
for name in ['render_fixture.py', 'requirements.lock']:
    shutil.copyfile(REPO / 'spikes/s04-runtime' / name, PACKAGE / 'runtime' / name)
(PACKAGE / 'runtime/network.sb').write_text('(version 1)\n(allow default)\n(deny network*)\n')
for path in sorted((HERE / 'assets/fonts').iterdir()):
    if path.is_file():
        shutil.copyfile(path, PACKAGE / 'assets/fonts' / path.name)
fonts = json.loads((PACKAGE / 'assets/fonts/sources.json').read_text())['fonts']
for font in fonts:
    assert hashlib.sha256((PACKAGE / 'assets/fonts' / font['filename']).read_bytes()).hexdigest() == font['sha256']
    assert (PACKAGE / 'assets/fonts' / font['license']).is_file()
(PACKAGE / 'README.md').write_text('''# Cloud Architecture Diagrams: native S04 pilot

Version: 0.1.0-alpha.2. Fixed three-node feasibility fixture; the full cloud/Kubernetes renderer is later work.

No Docker or central server is required. The plugin runs controlled local Python scripts and native Graphviz. MCP stdio is an optional host interface to the same code; it starts a local helper process without opening an HTTP/listening port. A direct script command is also provided.

The tested host is macOS ARM64. Install Python 3.10+, uv and Graphviz (for example, brew install uv graphviz), then run python3 scripts/setup.py from the installed plugin root. Setup creates a private Python 3.13 virtual environment under ~/.local/share/cloud-architecture-diagrams, installs hash-locked dependencies and uses the bundled Noto Sans/Thai fonts and OFL notices. Setup downloads dependencies; rendering performs no download. Native Graphviz is a host prerequisite, and its actual executable/version/hash is recorded and checked. Other OS paths remain unverified.

Run python3 scripts/render.py with a JSON object on stdin, for example {"labels":["Client","Application","Database"]}. The command returns paths/checksums for SVG, PNG, source JSON, DOT and manifest under ~/Documents/CloudArchitectureDiagrams. No MCP client is needed for this command. Through MCP, call get_runtime_info, render_fixture with {"request":{"labels":["Client","Application","Database"]}}, then read_fixture_artifact for the five exported files.

Output directories must be real, private and owned by the current user. Symlink directory components and symlink artifact files are rejected; descriptor-relative access anchors artifacts to the approved directory. Outputs persist until user removal. The renderer and descendants have network denied by the tested macOS sandbox-exec profile. CPU/file limits and a wall timeout are enforced; process-group RSS and scratch bytes are sampled, not kernel hard quotas or Docker isolation. Read runtime_info limits and the project evidence before relying on production isolation. Windows/Linux and future macOS sandbox availability remain separate validation work.

SVG uses font-family references; cross-machine SVG appearance, actual ChatGPT Work mode/UI download and second-machine acceptance remain unverified. This prototype is not a product release, and its new native source requires a fresh independent review.
''')
(PACKAGE / 'skills/cloud-architecture-runtime/SKILL.md').write_text('''---
name: cloud-architecture-runtime
description: Use to preflight the native local Python and Graphviz renderer and produce the S04 three-node SVG/PNG fixture without Docker.
---

This is a native S04 feasibility pilot. It has no provider service catalog or full architecture/Kubernetes semantics yet.

Call get_runtime_info first. If setup is missing, use the installed plugin root's scripts/setup.py. It installs a private Python environment; native Graphviz and uv are prerequisites. No Docker, central server, renderer token or model API key is required. Do not install into another plugin or edit the plugin cache.

Use render_fixture with request.labels containing exactly three literal strings, then read_fixture_artifact for SVG/PNG/JSON/DOT/manifest. Alternatively execute the fixed scripts/render.py with a JSON object containing labels on stdin; this uses the same validated renderer without an MCP client. Never generate or execute user-authored Python or arbitrary Graphviz options.

Inspect the returned PNG and verified file paths before attaching outputs. Record the actual host/mode; a successful Codex Desktop call does not prove a different Work mode. Do not claim visible preview/download without observed evidence. Native resource limits differ from the historical container prototype; report the actual runtime policy.
''')
archive = OUTPUT / (NAME + '-' + VERSION + '.zip')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in sorted(PACKAGE.rglob('*')):
        if p.is_file():
            z.write(p, NAME + '/' + str(p.relative_to(PACKAGE)))
with zipfile.ZipFile(archive) as z:
    assert len({n.split('/')[0] for n in z.namelist()}) == 1
    for n in z.namelist():
        assert '..' not in Path(n).parts
        if n.endswith('.json'):
            json.loads(z.read(n))
assert len(interface['shortDescription']) <= 30
print(json.dumps({'package': str(PACKAGE), 'archive': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'files': len([p for p in PACKAGE.rglob('*') if p.is_file()])}))
