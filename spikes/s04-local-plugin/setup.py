"""Install a private native Python environment; Graphviz is a system prerequisite."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.sax.saxutils import escape
sys.dont_write_bytecode = True
from common import ROOT, VERSION, STATE, RUNTIME, OUTPUT, supported_host, executable, fingerprint, digest, output_store, environment


def main():
    supported_host()
    store = output_store()
    store.close()
    uv = executable('uv')
    binaries = {name: {'path': executable(name)} for name in ['dot', 'fc-match']}
    binaries['sandbox-exec'] = {'path': '/usr/bin/sandbox-exec'}
    for binary in binaries.values():
        binary['sha256'] = digest(binary['path'])
    sys.path.insert(0, str(ROOT / 'runtime'))
    from artifact_store import directory_fd
    for path in [STATE.parent, RUNTIME, RUNTIME / 'fonts', RUNTIME / 'cache', RUNTIME / 'tmp']:
        os.close(directory_fd(path, create=True))
    venv = RUNTIME / 'venv'
    python = str(venv / 'bin/python')
    if not Path(python).exists():
        subprocess.run([uv, '--system-certs', 'venv', '--python', '3.13', str(venv)], check=True, stdout=sys.stderr)
    subprocess.run([uv, '--system-certs', 'pip', 'sync', '--python', python, '--require-hashes', str(ROOT / 'runtime/requirements.lock')], check=True, stdout=sys.stderr)
    for font in json.loads((ROOT / 'assets/fonts/sources.json').read_text())['fonts']:
        source = ROOT / 'assets/fonts' / font['filename']
        if digest(source) != font['sha256']:
            raise RuntimeError('Bundled font integrity failure')
        shutil.copyfile(source, RUNTIME / 'fonts' / font['filename'])
    config = '<fontconfig><dir>' + escape(str(RUNTIME / 'fonts')) + '</dir><cachedir>' + escape(str(RUNTIME / 'cache')) + '</cachedir></fontconfig>\n'
    (RUNTIME / 'fonts.conf').write_text(config)
    state = {'kind': 'native', 'version': VERSION, 'source_sha256': fingerprint(), 'python': python,
             'binaries': binaries, 'output_root': str(OUTPUT), 'fontconfig_sha256': digest(RUNTIME / 'fonts.conf')}
    env = environment(state)
    state['graphviz_version'] = subprocess.check_output([binaries['dot']['path'], '-V'], env=env, stderr=subprocess.STDOUT, text=True).strip()
    for family in ['Noto Sans', 'Noto Sans Thai']:
        match = subprocess.check_output([binaries['fc-match']['path'], '-f', '%{file}', family], env=env, text=True).strip()
        if Path(match).parent != RUNTIME / 'fonts':
            raise RuntimeError('Font resolution escaped the private font directory')
    probe = subprocess.check_output(['/usr/bin/sandbox-exec', '-f', str(ROOT / 'runtime/network.sb'), python, '-c',
        'import socket;s=socket.socket();print(s.connect_ex(("127.0.0.1",9)));s.close()'], env=env, text=True).strip()
    if probe != '1':
        raise RuntimeError('Native renderer network-denial probe failed')
    state['renderer_network_probe_errno'] = int(probe)
    with tempfile.NamedTemporaryFile('w', dir=STATE.parent, delete=False) as stream:
        json.dump(state, stream, indent=2)
        stream.write('\n')
        temporary = stream.name
    os.replace(temporary, STATE)
    print(json.dumps({'installed': True, **state, 'state_file': str(STATE)}))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
