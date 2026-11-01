"""Native host helpers. No Docker dependency or network listener."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / 'plugin.json').read_text())['version']
STATE = Path.home() / '.local/share/cloud-architecture-diagrams' / (VERSION + '.json')
RUNTIME = STATE.parent / 'runtime' / VERSION
OUTPUT = Path.home() / 'Documents/CloudArchitectureDiagrams'


def supported_host():
    if sys.platform != 'darwin':
        raise RuntimeError('The S04 native pilot is verified on macOS only; other OS setup remains pending')


def executable(name):
    for value in [shutil.which(name), '/opt/homebrew/bin/' + name, '/usr/local/bin/' + name]:
        if value and Path(value).is_file() and os.access(value, os.X_OK):
            return str(Path(value).resolve())
    raise RuntimeError('Missing ' + name + '. Install uv and Graphviz (macOS: brew install uv graphviz), then run setup.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint():
    paths = sorted(p for folder in ['runtime', 'assets/fonts'] for p in (ROOT / folder).iterdir() if p.is_file())
    values = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def output_store():
    supported_host()
    sys.path.insert(0, str(ROOT / 'runtime'))
    from artifact_store import ArtifactStore
    try:
        return ArtifactStore(OUTPUT)
    except (OSError, ValueError) as error:
        raise RuntimeError('Output root must be a private real directory; symlink components are rejected: ' + str(OUTPUT)) from error


def environment(state):
    bins = [str(Path(state['python']).parent), *sorted({str(Path(p['path']).parent) for p in state['binaries'].values()}), '/usr/bin', '/bin']
    return {'PATH': os.pathsep.join(bins), 'HOME': str(RUNTIME), 'LANG': 'en_US.UTF-8',
            'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUNBUFFERED': '1',
            'FONTCONFIG_FILE': str(RUNTIME / 'fonts.conf'), 'TMPDIR': str(RUNTIME / 'tmp'),
            'CLOUD_DIAGRAM_RUNTIME_DIR': str(RUNTIME), 'CLOUD_DIAGRAM_HOST_OUTPUT_ROOT': str(OUTPUT),
            'CLOUD_DIAGRAM_PLUGIN_VERSION': VERSION}


def preflight():
    supported_host()
    store = output_store()
    store.close()
    try:
        state = json.loads(STATE.read_text())
        if state['version'] != VERSION or state['source_sha256'] != fingerprint() or state['kind'] != 'native':
            raise ValueError('source/version differs')
        if not Path(state['python']).is_file():
            raise ValueError('virtual environment missing')
        for binary in state['binaries'].values():
            if digest(binary['path']) != binary['sha256']:
                raise ValueError('system binary changed')
        fonts = json.loads((ROOT / 'assets/fonts/sources.json').read_text())['fonts']
        for font in fonts:
            if digest(RUNTIME / 'fonts' / font['filename']) != font['sha256']:
                raise ValueError('font changed')
        if digest(RUNTIME / 'fonts.conf') != state['fontconfig_sha256']:
            raise ValueError('font configuration changed')
        return state
    except (OSError, ValueError, KeyError) as error:
        raise RuntimeError('Native runtime setup/preflight failed; run ' + shlex.join([sys.executable, str(ROOT / 'scripts/setup.py')])) from error
