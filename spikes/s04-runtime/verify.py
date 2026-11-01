"""Reproduce the local S04 container and authenticated loopback MCP checks."""

import base64
import datetime
import hashlib
import http.client
import json
import os
from pathlib import Path
import secrets
import socket
import statistics
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "output"
IMAGE = subprocess.check_output(["docker", "image", "inspect", "mingrammer-s04:local", "--format", "{{.Id}}"], text=True).strip()
LIMITS = ["--memory", "1g", "--memory-swap", "1g", "--cpus", "1", "--pids-limit", "64",
          "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
          "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m,mode=1777"]
LABELS = ["Client", "Application \u0e41\u0e2d\u0e1b\u0e1e\u0e25\u0e34\u0e40\u0e04\u0e0a\u0e31\u0e19", "Database \u0e10\u0e32\u0e19\u0e02\u0e49\u0e2d\u0e21\u0e39\u0e25"]


def docker_worker(payload=None, args=(), code=None):
    name = "mingrammer-s04-check-" + secrets.token_hex(6)
    cmd = ["docker", "run", "--rm", "--pull", "never", "--name", name, "--network", "none", *LIMITS]
    if code:
        cmd += ["--entrypoint", "python", IMAGE, "-c", code]
    else:
        cmd += ["-i", IMAGE, *args]
    try:
        return subprocess.run(cmd, input=json.dumps(payload) if payload is not None else "",
                              capture_output=True, text=True, timeout=65)
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
        raise


def get(url, token=None):
    headers = {"Authorization": "Bearer " + token} if token else {}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as response:
            data = response.read(16 * 1024 * 1024 + 1)
            assert len(data) <= 16 * 1024 * 1024
            return response.status, data
    except urllib.error.HTTPError as error:
        return error.code, error.read(4096)


def main():
    OUTPUT.mkdir(exist_ok=True)
    info_result = docker_worker(args=["info"])
    assert info_result.returncode == 0, info_result.stderr
    info = json.loads(info_result.stdout)
    assert info["uid"] == 10001 and info["cgroups"]["memory.max"] == "1073741824"
    assert info["cgroups"]["memory.swap.max"] == "0" and info["cgroups"]["pids.max"] == "64"
    assert info["cgroups"]["cpu.max"] == "100000 100000"
    for font in info["fonts"]:
        assert font["name_records"]["1"] == font["requested_family"]
        assert "SIL Open Font License" in font["name_records"]["13"]
    isolation = docker_worker(code="import pathlib,os,json; print(json.dumps({'interfaces':{p.name:(p/'flags').read_text().strip() for p in pathlib.Path('/sys/class/net').iterdir() if p.is_dir()},'ipv4_routes':pathlib.Path('/proc/net/route').read_text().splitlines()[1:],'tmp_bytes':os.statvfs('/tmp').f_blocks*os.statvfs('/tmp').f_frsize}))")
    assert isolation.returncode == 0
    isolation_info = json.loads(isolation.stdout)
    assert isolation_info["tmp_bytes"] == 268435456 and not isolation_info["ipv4_routes"]
    assert all(name == "lo" or not (int(flags, 16) & 1)
               for name, flags in isolation_info["interfaces"].items()), isolation_info
    negative = []
    for name, payload, expected in [
        ("executable_field", {"python": "raise SystemExit('must never execute')"}, "S04_INVALID_FIELDS"),
        ("oversized_label", {"labels": ["a" * 257, "b", "c"]}, "S04_LABEL_LIMIT"),
        ("control_label", {"labels": ["a\x00", "b", "c"]}, "S04_LABEL_CONTROL"),
        ("oversized_graph", {"node_count": 201}, "S04_INVALID_SIZE"),
        ("oversized_body", {"labels": ["a" * (1024 * 1024), "b", "c"]}, "S04_INPUT_LIMIT"),
    ]:
        result = docker_worker(payload)
        assert result.returncode == 2 and json.loads(result.stdout)["error"] == expected
        negative.append(name)
    benchmarks = []
    for count in (3, 30, 100, 200):
        trials = []
        for _ in range(3):
            result = docker_worker({"node_count": count, "labels": LABELS})
            assert result.returncode == 0, result.stderr
            value = json.loads(result.stdout)
            assert value["node_count"] == count and value["edge_count"] == count - 1
            trials.append(value)
        benchmarks.append({"nodes": count, "edges": count - 1, "trials": trials,
                           "median_seconds": statistics.median(r["elapsed_seconds"] for r in trials)})

    token = secrets.token_urlsafe(32)
    environment = os.environ.copy()
    environment["S04_TOKEN"] = token
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    environment["S04_ARTIFACT_ORIGIN"] = origin
    name = "mingrammer-s04-http-" + secrets.token_hex(6)
    start = ["docker", "run", "--rm", "--pull", "never", "-d", "--name", name, *LIMITS,
             "--publish", f"127.0.0.1:{port}:8000", "--env", "S04_TOKEN", "--env", "S04_ARTIFACT_ORIGIN",
             "--entrypoint", "python", IMAGE, "/app/server.py"]
    subprocess.run(start, env=environment, capture_output=True, text=True, check=True)
    try:
        for _ in range(50):
            try:
                status, _ = get(origin + "/mcp")
                if status == 401:
                    break
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                pass
            time.sleep(0.2)
        else:
            raise RuntimeError("S04 loopback server did not become ready")
        assert get(origin + "/mcp", "wrong-token")[0] == 401
        # Read the early response before uploading a rejected body. Sending the
        # full body with urllib races the server's deliberate connection close.
        oversized = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
        try:
            oversized.putrequest("POST", "/mcp")
            oversized.putheader("Authorization", "Bearer " + token)
            oversized.putheader("Content-Type", "application/json")
            oversized.putheader("Content-Length", str(1024 * 1024 + 1))
            oversized.endheaders()
            response = oversized.getresponse()
            assert response.status == 413, response.status
            response.read(4096)
        finally:
            oversized.close()
        client_source = '''import asyncio,json,os,httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
async def main():
    async with httpx2.AsyncClient(headers={"Authorization":"Bearer "+os.environ["S04_TOKEN"]}) as http:
        async with Client(streamable_http_client("http://127.0.0.1:8000/mcp",http_client=http)) as client:
            tools=await client.list_tools()
            result=await client.call_tool("render_fixture",{"labels":LABELS})
            assert not result.is_error
            invalid=await client.call_tool("render_fixture",{"labels":["x"*257,"b","c"]})
            assert invalid.is_error
            literal=await client.call_tool("render_fixture",{"labels":["<script>alert(1)</script>","safe","database"]})
            assert not literal.is_error
            print(json.dumps({"tools":[t.name for t in tools.tools],"result":result.model_dump(mode="json",by_alias=True),"literal":literal.structured_content,"invalid_rejected":invalid.is_error}))
asyncio.run(main())
'''.replace("LABELS", repr(LABELS))
        client = subprocess.run(["docker", "exec", "-i", "--env", "S04_TOKEN", name, "python", "-"],
                                input=client_source, env=environment, capture_output=True, text=True, timeout=60)
        if client.returncode:
            raise RuntimeError("Local MCP client failed: " + client.stderr.replace(token, "[REDACTED]")[-3000:])
        result = json.loads(client.stdout)
        assert set(result["tools"]) == {"runtime_info_tool", "render_fixture"}
        body = result["result"]["structuredContent"]
        for filename, url in body["artifact_urls"].items():
            assert url.startswith(origin + "/artifacts/")
            assert get(url)[0] == 401
            status, data = get(url, token)
            assert status == 200
            if filename in body["files"]:
                assert hashlib.sha256(data).hexdigest() == body["files"][filename]["sha256"]
            (OUTPUT / filename).write_bytes(data)
        svg = ET.fromstring((OUTPUT / "diagram.svg").read_bytes())
        texts = [element.text or "" for element in svg.iter() if element.tag.endswith("}text")]
        assert all(label in texts for label in LABELS)
        image = next(x for x in result["result"]["content"] if x["type"] == "image")
        assert base64.b64decode(image["data"]) == (OUTPUT / "diagram.png").read_bytes()
        literal_url = result["literal"]["artifact_urls"]["diagram.svg"]
        literal_svg = ET.fromstring(get(literal_url, token)[1])
        assert not any(e.tag.endswith("}script") for e in literal_svg.iter())
        assert any(e.text == "<script>alert(1)</script>" for e in literal_svg.iter())
        assert get(origin + "/artifacts/" + body["request_id"] + "/..%2fserver.py", token)[0] == 404
        inspect = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
        host = inspect["HostConfig"]
        assert host["ReadonlyRootfs"] and host["Memory"] == 1073741824 and host["PidsLimit"] == 64
        proof = {"session": "S04", "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 "scope": "Local Docker/SDK HTTP proof, not an actual Work call or deployment",
                 "image_id": IMAGE, "runtime": info, "isolation_probe": isolation_info,
                 "negative_cases": negative + ["missing_auth", "wrong_auth", "http_body_limit", "literal_script_text", "artifact_traversal"],
                 "benchmarks": benchmarks, "mcp_tools": result["tools"],
                 "http_proof": {"authenticated_render": True, "invalid_tool_input_rejected": result["invalid_rejected"],
                                "png_image_matches_download": True, "artifact_hashes_verified": True,
                                "transport": "SDK Streamable HTTP on container loopback; authenticated host GET downloads"},
                 "sample": body, "container_readonly": host["ReadonlyRootfs"],
                 "actual_work_invocation": "pending", "remote_authentication": "pending", "hosting": "not_provisioned"}
        # Do not persist the token, raw SDK image/base64 result or Docker environment.
        proof["sample"].pop("artifact_urls")
        proof["sample"].pop("request_id")
        (OUTPUT / "proof.json").write_text(json.dumps(proof, indent=2, ensure_ascii=True) + "\n")
        print(json.dumps({"runtime": info["packages"], "benchmarks": [{"nodes": b["nodes"], "median_seconds": b["median_seconds"]} for b in benchmarks], "http_proof": proof["http_proof"], "output": str(OUTPUT)}, indent=2))
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, check=True)


if __name__ == "__main__":
    main()
