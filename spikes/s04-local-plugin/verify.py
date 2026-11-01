"""SDK integration checks of the installed cache and a relocated portable ZIP."""
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import zipfile
from mcp import Client, StdioServerParameters

HERE = Path(__file__).resolve().parent
NAME = "cloud-architecture-diagrams"
VERSION = "0.1.0-alpha.1"
INSTALLED = Path.home() / ".codex/plugins/cache/mingrammer-local" / NAME / VERSION
ARCHIVE = HERE / "output" / (NAME + "-" + VERSION + ".zip")
LABELS = ["Client", "Application \u0e23\u0e30\u0e1a\u0e1a", "Database \u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25"]


def containers():
    ids = subprocess.check_output(["docker", "ps", "-aq", "--filter", "name=cloud-diagrams-mcp-"], text=True).split()
    return set(ids)


async def check(root):
    started = time.monotonic()
    async with Client(StdioServerParameters(command=sys.executable, args=[str(root / "scripts/launch.py")], cwd=root)) as client:
        tools = (await client.list_tools()).tools
        assert {t.name for t in tools} == {"get_runtime_info", "render_fixture", "read_fixture_artifact"}
        info_result = await client.call_tool("get_runtime_info", {})
        assert not info_result.is_error
        info = info_result.structured_content
        # SDK wraps dict returns under result on some servers.
        if "result" in info:
            info = info["result"]
        assert info["uid"] != 0 and info["packages"]["diagrams"] == "0.25.1"
        assert info["cgroups"] == {"memory.max": "1073741824", "memory.swap.max": "0", "pids.max": "64", "cpu.max": "100000 100000"}
        result = await client.call_tool("render_fixture", {"request": {"labels": LABELS}})
        assert not result.is_error, result
        report = result.structured_content
        assert report["node_count"] == 3 and report["edge_count"] == 2
        files = report["host_paths"]
        assert len(files) == 5 and set(report["files"]) == set(files) - {"manifest.json"}
        for name, filename in files.items():
            path = Path(filename)
            assert path.is_file() and path.parent.name == report["bundle_id"]
            read = await client.call_tool("read_fixture_artifact", {"bundle_id": report["bundle_id"], "filename": name})
            assert not read.is_error
            contents = base64.b64decode(read.content[0].resource.blob)
            assert contents == path.read_bytes()
            if name in report["files"]:
                assert hashlib.sha256(contents).hexdigest() == report["files"][name]["sha256"]
        image = next(c for c in result.content if c.type == "image")
        assert base64.b64decode(image.data) == Path(files["diagram.png"]).read_bytes()
        for args in [{"labels": ["only one"]}, {"labels": ["x" * 257, "a", "b"]},
                     {"labels": ["a\nb", "c", "d"]}, {"labels": LABELS, "code": "print('forbidden')"}]:
            bad = await client.call_tool("render_fixture", {"request": args})
            assert bad.is_error
        traversal = await client.call_tool("read_fixture_artifact", {"bundle_id": "../etc", "filename": "source.json"})
        assert traversal.is_error
        live = containers()
        assert len(live) >= 1
        configs = json.loads(subprocess.check_output(["docker", "inspect", *live], text=True))
        matching = [c for c in configs if c["State"]["Running"] and c["Config"]["Env"] and "CLOUD_DIAGRAM_HOST_OUTPUT_ROOT=" + str(Path(files["source.json"]).parents[1]) in c["Config"]["Env"]]
        assert len(matching) == 1
        config = matching[0]
        hc = config["HostConfig"]
        assert hc["NetworkMode"] == "none" and hc["ReadonlyRootfs"] and hc["Privileged"] is False
        assert hc["CapDrop"] == ["ALL"] and hc["SecurityOpt"] == ["no-new-privileges"]
        assert len(hc["Mounts"]) == 1 and hc["Mounts"][0]["Target"] == "/output"
        assert hc["PortBindings"] == {}
        assert not any("TOKEN=" in e or "API_KEY=" in e for e in config["Config"]["Env"])
        probe = json.loads(subprocess.check_output(["docker", "exec", config["Id"], "python", "-c",
             'import json,os;print(json.dumps({"routes":open("/proc/net/route").read(),"tmp":os.statvfs("/tmp").f_frsize*os.statvfs("/tmp").f_blocks}))'], text=True))
        assert len(probe["routes"].splitlines()) == 1 and probe["tmp"] == 268435456
        return {"root": str(root), "runtime": info, "bundle": report, "tools": sorted(t.name for t in tools),
                "negative_cases": ["label_count", "label_length", "control_character", "code_field", "artifact_traversal"],
                "container_host_config": hc, "elapsed_including_startup_seconds": round(time.monotonic() - started, 3)}


async def main():
    before = containers()
    environment = os.environ.copy()
    environment.pop("DOCKER_CONTEXT", None)
    environment["DOCKER_HOST"] = "tcp://renderer.invalid:2375"
    rejected = subprocess.run([sys.executable, str(INSTALLED / "scripts/launch.py")], env=environment, capture_output=True, text=True)
    assert rejected.returncode == 1 and "local Docker socket" in rejected.stderr
    installed = await check(INSTALLED)
    with tempfile.TemporaryDirectory(prefix="S04 relocated plugin ") as directory:
        with zipfile.ZipFile(ARCHIVE) as z:
            z.extractall(directory)
        relocated = await check(Path(directory) / NAME)
    after = containers()
    assert before == after, (before, after)
    proof = {"date": "2026-11-01", "route": "D-013 per-machine local stdio plugin", "scope": "synthetic runtime pilot",
             "archive": {"path": str(ARCHIVE), "sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()},
             "installed_sdk": installed, "relocated_zip_sdk": relocated, "temporary_containers_remaining": len(after - before),
             "remote_docker_endpoint_rejected": True,
             "actual_work_chat": "not_tested", "second_physical_machine": "not_tested", "independent_astra_review": "not_performed"}
    path = HERE / "output/local-proof.json"
    path.write_text(json.dumps(proof, indent=2) + "\n")
    print(json.dumps({"passed": True, "proof": str(path), "preview": installed["bundle"]["host_paths"]["diagram.png"]}))


if __name__ == "__main__":
    asyncio.run(main())
