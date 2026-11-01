"""Native script/MCP integration and output-root/resource regression checks."""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import signal
import shutil
import selectors
import time
from unittest.mock import patch
import zipfile
from mcp import Client, StdioServerParameters
from artifact_store import ArtifactStore, FILES, MAX_FILE
from execution import execute, POLICY, directory_bytes

HERE = Path(__file__).resolve().parent
VERSION = '0.1.0-alpha.3'
NAME = 'cloud-architecture-diagrams'
INSTALLED = Path.home() / '.codex/plugins/cache/mingrammer-local' / NAME / VERSION
ARCHIVE = HERE / 'output' / (NAME + '-' + VERSION + '.zip')
LABELS = ['Client', 'Application \u0e23\u0e30\u0e1a\u0e1a', 'Database \u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25']


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def bundle(report):
    assert report['node_count'] == 3 and report['edge_count'] == 2
    assert len(report['host_paths']) == 5
    for name, path in report['host_paths'].items():
        data = Path(path).read_bytes()
        if name != 'manifest.json':
            assert len(data) == report['files'][name]['bytes']
            assert checksum(data) == report['files'][name]['sha256']
    manifest = json.loads(Path(report['host_paths']['manifest.json']).read_text())
    assert manifest == report
    assert report['runtime']['system'] == 'Darwin'
    assert report['runtime']['plugin_version'] == VERSION
    assert report['runtime']['packages']['diagrams'] == '0.25.1'
    return report


async def mcp_check(root):
    async with Client(StdioServerParameters(command=sys.executable, args=['-B', str(root / 'scripts/launch.py')], cwd=root)) as client:
        tools = (await client.list_tools()).tools
        assert {t.name for t in tools} == {'get_runtime_info', 'render_fixture', 'read_fixture_artifact'}
        info = await client.call_tool('get_runtime_info', {})
        assert not info.is_error and info.structured_content['plugin_version'] == VERSION
        result = await client.call_tool('render_fixture', {'request': {'labels': LABELS}})
        assert not result.is_error, result
        report = bundle(result.structured_content)
        image = next(c for c in result.content if c.type == 'image')
        assert base64.b64decode(image.data) == Path(report['host_paths']['diagram.png']).read_bytes()
        for name, path in report['host_paths'].items():
            read = await client.call_tool('read_fixture_artifact', {'bundle_id': report['bundle_id'], 'filename': name})
            assert not read.is_error
            assert base64.b64decode(read.content[0].resource.blob) == Path(path).read_bytes()
        negatives = [{'labels': ['one']}, {'labels': ['x' * 257, 'b', 'c']}, {'labels': ['a\nb', 'b', 'c']}, {'labels': LABELS, 'code': 'forbidden'}]
        for request in negatives:
            bad = await client.call_tool('render_fixture', {'request': request})
            assert bad.is_error
        bad = await client.call_tool('read_fixture_artifact', {'bundle_id': '../etc', 'filename': 'source.json'})
        assert bad.is_error
        return {'root': str(root), 'tools': sorted(t.name for t in tools), 'bundle': report,
                'artifact_reads_and_hashes': 'passed', 'negative_cases': ['label_count', 'label_length', 'control_label', 'code_field', 'artifact_traversal']}


def path_regressions():
    passed = []
    with tempfile.TemporaryDirectory(prefix='s04-native-path-') as raw:
        base = Path(raw).resolve()
        outside = base / 'outside'; outside.mkdir(mode=0o700)
        alias = base / 'alias'; alias.symlink_to(outside, target_is_directory=True)
        for path, name in [(alias, 'existing_root_symlink'), (alias / 'child', 'ancestor_symlink')]:
            try:
                ArtifactStore(path)
            except (OSError, ValueError):
                passed.append(name)
            else:
                raise AssertionError(name + ' accepted')
        assert not (outside / 'child').exists()
        root = base / 'approved'; store = ArtifactStore(root)
        try:
            identifier = 'a' * 32; folder = root / identifier; folder.mkdir(mode=0o700)
            secret = outside / 'private.txt'; secret.write_text('outside sentinel')
            target = folder / 'source.json'; target.symlink_to(secret)
            try:
                store.read(identifier, 'source.json')
            except (OSError, ValueError):passed.append('artifact_symlink')
            else:raise AssertionError('symlink file read')
            target.unlink(); os.mkfifo(target)
            try:
                store.read(identifier, 'source.json')
            except (OSError, ValueError):passed.append('non_regular_artifact')
            else:raise AssertionError('FIFO accepted')
            target.unlink()
            with target.open('wb') as stream:stream.truncate(MAX_FILE + 1)
            try:
                store.read(identifier, 'source.json')
            except ValueError:passed.append('artifact_size')
            else:raise AssertionError('oversize accepted')
            root.rename(base / 'original'); root.mkdir(mode=0o700)
            try:
                store.check_root()
            except ValueError:passed.append('root_replacement')
            else:raise AssertionError('replaced root accepted')
        finally:store.close()
        store = ArtifactStore(base / 'atomic')
        try:
            source = base / 'source'; source.mkdir(mode=0o700)
            report = {'files': {}}
            for name in FILES - {'manifest.json'}:
                data = name.encode(); (source / name).write_bytes(data)
                report['files'][name] = {'bytes': len(data), 'sha256': checksum(data)}
            report['files']['source.json']['sha256'] = 'wrong'
            try:store.publish('b' * 32, source, report)
            except ValueError:passed.append('failed_bundle_atomic_cleanup')
            else:raise AssertionError('corrupt bundle published')
            assert list(store.root.iterdir()) == []
        finally:store.close()
    return passed


def resource_regressions():
    passed = []
    with tempfile.TemporaryDirectory(prefix='s04-native-limits-') as raw:
        scratch = Path(raw).resolve()
        cases = [('S04_RENDER_TIMEOUT', 'import time;time.sleep(5)', {'wall_seconds': .2}),
                 ('S04_MEMORY_LIMIT', 'import time;x=bytearray(32*1024*1024);time.sleep(5)', {'memory_bytes': 8 * 1024 ** 2}),
                 ('S04_TEMPORARY_LIMIT', 'import pathlib,time,sys;pathlib.Path(sys.argv[1]).write_bytes(b"x"*(2*1024*1024));time.sleep(5)', {'temporary_bytes': 1024 ** 2}),
                 ('S04_RENDER_TIMEOUT', 'import subprocess,sys,pathlib;p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(5)"]);pathlib.Path(sys.argv[1]).write_text(str(p.pid))', {'wall_seconds': .2})]
        for expected, code, overrides in cases:
            command = [sys.executable, '-c', code, str(scratch / 'file.bin')]
            try:execute(command, b'{}', os.environ.copy(), scratch, {**POLICY, **overrides})
            except ValueError as error:
                assert str(error) == expected, str(error)
                passed.append(expected)
            else:raise AssertionError(expected + ' not enforced')
        child = (scratch / 'file.bin').read_text()
        status = subprocess.run(['/bin/ps', '-o', 'stat=', '-p', child], capture_output=True, text=True)
        assert not status.stdout.strip() or status.stdout.strip().startswith('Z'), 'descendant survived timeout'
        passed[-1] = 'S04_RENDER_TIMEOUT_with_exited_parent_and_live_descendant'
    return passed


def shutdown_regressions():
    state = json.loads((Path.home() / '.local/share/cloud-architecture-diagrams' / (VERSION + '.json')).read_text())
    sys.path.insert(0, str(INSTALLED / 'scripts'))
    from common import environment
    passed = []
    helper = r"""
import json,os,pathlib,signal,subprocess,sys,threading,time
import execution,local_server
marker=pathlib.Path(sys.argv[1]);mode=sys.argv[2]
real_popen=subprocess.Popen
if mode=='spawn':
    def during_spawn(*args,**kwargs):
        process=real_popen(*args,**kwargs)
        marker.write_text(json.dumps({'pid':process.pid,'scratch':kwargs['env']['TEST_SCRATCH']}))
        os.kill(os.getpid(),signal.SIGTERM)
        return process
    execution.subprocess.Popen=during_spawn

def slow(command,payload,env,scratch):
    env={**env,'TEST_SCRATCH':scratch}
    program='import json,os,pathlib,sys,time;pathlib.Path(sys.argv[1]).write_text(json.dumps({"pid":os.getpid(),"scratch":sys.argv[2]}));time.sleep(30)'
    return execution.execute([sys.executable,'-c',program,str(marker),scratch],payload,env,scratch)
local_server.execute=slow

def work():
    local_server.render_fixture(local_server.FixtureRequest(labels=['a','b','c']))
if mode in ('mcp','eof'):
    local_server.serve()
elif mode=='thread':
    threading.Thread(target=work,daemon=True).start()
    while True:time.sleep(.1)
else:work()
"""
    with tempfile.TemporaryDirectory(prefix='s04-shutdown-') as raw:
        base = Path(raw).resolve()
        for mode, signum in [('main', signal.SIGTERM), ('thread', signal.SIGTERM), ('thread', signal.SIGINT), ('spawn', signal.SIGTERM), ('mcp', signal.SIGTERM), ('eof', None)]:
            marker = base / (mode + '-' + str(signum) + '.json')
            env = environment(state); env['PYTHONPATH'] = str(INSTALLED / 'runtime')
            process = subprocess.Popen([state['python'], '-B', '-c', helper, str(marker), mode], env=env,
                                       stdin=subprocess.PIPE if mode in ('mcp','eof') else subprocess.DEVNULL,
                                       stdout=subprocess.PIPE if mode in ('mcp','eof') else subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, start_new_session=True)
            record = None
            try:
                if mode in ('mcp','eof'):
                    from mcp.client.session import LATEST_HANDSHAKE_VERSION
                    def send(message):
                        process.stdin.write((json.dumps(message)+'\n').encode());process.stdin.flush()
                    send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':LATEST_HANDSHAKE_VERSION,'capabilities':{},'clientInfo':{'name':'s04-shutdown-check','version':'1'}}})
                    with selectors.DefaultSelector() as selector:
                        selector.register(process.stdout,selectors.EVENT_READ)
                        assert selector.select(timeout=10), 'MCP initialize timed out'
                        response=json.loads(process.stdout.readline());assert response.get('id')==1 and 'result' in response,response
                    send({'jsonrpc':'2.0','method':'notifications/initialized'})
                    send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':'render_fixture','arguments':{'request':{'labels':['a','b','c']}}}})
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    try:record = json.loads(marker.read_text());break
                    except (OSError,ValueError):
                        if process.poll() is not None:break
                        time.sleep(.02)
                assert record is not None, ('helper did not start controlled worker', mode, process.poll())
                if mode=='eof':process.stdin.close()
                elif mode != 'spawn':process.send_signal(signum)
                assert process.wait(timeout=8) == (0 if mode=='eof' else 128 + signum), ('wrong shutdown status', mode, process.returncode)
                status = subprocess.run(['/bin/ps','-o','stat=','-p',str(record['pid'])],capture_output=True,text=True)
                assert not status.stdout.strip() or status.stdout.strip().startswith('Z'), ('renderer survived', mode)
                assert not Path(record['scratch']).exists(), ('scratch survived', mode)
                passed.append(mode + ':' + ('EOF' if signum is None else signal.Signals(signum).name))
            finally:
                if record:
                    try:os.killpg(record['pid'],signal.SIGKILL)
                    except ProcessLookupError:pass
                    scratch = Path(record['scratch'])
                    expected = Path(state['python']).parents[2] / 'tmp'
                    if scratch.parent == expected and scratch.name.startswith('request-'):
                        shutil.rmtree(scratch,ignore_errors=True)
                if process.poll() is None:
                    process.kill();process.wait(timeout=5)
    return passed


def deleted_file_regression():
    with tempfile.TemporaryDirectory(prefix='s04-snapshot-') as raw:
        root=Path(raw).resolve();transient=root/'removed';transient.write_bytes(b'x')
        survivor=root/'retained';survivor.write_bytes(b'abc')
        transient.unlink()
        # The file existed when enumerated and disappeared before lstat.
        with patch.object(Path,'rglob',return_value=iter([transient,survivor])):
            assert directory_bytes(root)==3
    return 'deleted intermediate ignored; retained file still counted'


async def main():
    paths = path_regressions(); resources = resource_regressions()
    shutdown = shutdown_regressions(); deleted = deleted_file_regression()
    with tempfile.TemporaryDirectory(prefix='s04-no-docker-') as raw:
        folder = Path(raw); marker = folder / 'called'
        fake = folder / 'docker'; fake.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\nexit 99\n'); fake.chmod(0o700)
        environment = os.environ.copy(); environment['PATH'] = str(folder) + os.pathsep + environment['PATH']
        environment['DOCKER_HOST'] = 'tcp://unused.invalid:2375'
        result = subprocess.run([sys.executable, '-B', str(INSTALLED / 'scripts/render.py')], input=json.dumps({'labels': LABELS}).encode(), env=environment, capture_output=True, check=True)
        direct = bundle(json.loads(result.stdout)); assert not marker.exists()
        too_large = subprocess.run([sys.executable, '-B', str(INSTALLED / 'scripts/render.py')], input=b'x' * (1024 ** 2 + 1), env=environment, capture_output=True)
        assert too_large.returncode == 2 and b'S04_INPUT_LIMIT' in too_large.stderr
    oversize = subprocess.run([sys.executable,'-B',str(INSTALLED/'scripts/launch.py')], input=b'x'*(1024**2+1), capture_output=True,timeout=10)
    assert oversize.returncode==1, 'MCP frame limit not enforced'
    installed = await mcp_check(INSTALLED)
    with tempfile.TemporaryDirectory(prefix='S04 native relocated ') as raw:
        with zipfile.ZipFile(ARCHIVE) as z:z.extractall(raw)
        relocated = await mcp_check(Path(raw) / NAME)
    proof = {'recorded_at': datetime.now(ZoneInfo('Asia/Bangkok')).isoformat(), 'plugin_version': VERSION, 'scope': 'native macOS S04 pilot',
             'direct_script': direct, 'docker_invocation': 'not_used; failing Docker shim and remote DOCKER_HOST did not affect render',
             'installed_mcp': installed, 'relocated_zip_mcp': relocated, 'path_regressions': paths,
             'resource_regressions': resources, 'shutdown_regressions': shutdown, 'deleted_file_regression': deleted, 'cli_input_limit': 'passed', 'mcp_frame_limit': 'passed',
             'archive': {'path': str(ARCHIVE), 'sha256': checksum(ARCHIVE.read_bytes())},
             'actual_chatgpt_work_mode': 'not_tested', 'independent_native_source_review': 'pending', 'second_physical_machine': 'not_tested'}
    target = HERE / 'output/native-proof.json'; target.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps({'passed': True, 'proof': str(target), 'png': direct['host_paths']['diagram.png'], 'path_regressions': len(paths), 'resource_regressions': len(resources)}))


if __name__ == '__main__':
    asyncio.run(main())
