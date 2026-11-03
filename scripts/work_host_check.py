"""Install the built plugin into a throwaway host profile and run its tools through the real engine.

This drives the app-server inside the ChatGPT app, with no model, no account and no change to the
owner's profile. It proves install, discovery, the tool contract and retrieval on this machine. It
does not prove the Work user interface, which only the owner can check.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from build_work_plugin import MARKETPLACE, PLUGIN, build

ROOT = Path(__file__).resolve().parents[1]
CODEX = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex"
SERVER = "cloud-architecture"
TOOLS = {
    "get_capabilities",
    "setup_runtime",
    "get_schema",
    "search_catalog",
    "validate_model",
    "render_model",
    "read_artifact",
    "list_bundles",
}
BUNDLE_FILES = {
    "diagram.png",
    "diagram.svg",
    "model.json",
    "view.json",
    "diagnostics.json",
    "manifest.json",
}
SETUP_SECONDS = 600


class AppServer:
    """Just enough of the host's own client protocol to reach a plugin's tools without a model."""

    def __init__(self, codex: str, environment: dict[str, str], cwd: Path) -> None:
        self.process = subprocess.Popen(
            [codex, "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=environment,
            cwd=cwd,
        )
        self.replies: dict[int, dict[str, Any]] = {}
        self.sequence = 0
        threading.Thread(target=self._read, daemon=True).start()
        self.request(
            "initialize",
            {
                "clientInfo": {"name": "s09-check", "version": "1"},
                "capabilities": {"experimentalApi": True},
            },
        )
        self._write({"method": "initialized"})

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            message = json.loads(line)
            if "id" in message and "method" not in message:
                self.replies[message["id"]] = message

    def _write(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method: str, params: dict[str, Any], seconds: float = 120) -> Any:
        self.sequence += 1
        number = self.sequence
        self._write({"id": number, "method": method, "params": params})
        deadline = time.monotonic() + seconds
        while number not in self.replies:
            if time.monotonic() > deadline:
                raise TimeoutError(method)
            time.sleep(0.02)
        reply = self.replies.pop(number)
        if "error" in reply:
            raise RuntimeError(f"{method}: {reply['error']}")
        return reply["result"]

    def close(self) -> None:
        self.process.terminate()
        self.process.wait(timeout=20)


class StandInModel(ThreadingHTTPServer):
    """Plays a scripted model over the host's Responses API, and keeps every request it receives.

    It shows what the host really tells and returns to a model, with no account and no model. It
    says nothing about how a real model reads the skill.
    """

    def __init__(self, steps: list[str]) -> None:
        super().__init__(("127.0.0.1", 0), _StandInHandler)
        self.steps = steps
        self.requests: list[dict[str, Any]] = []

    def outputs(self, step: int) -> list[dict[str, Any]]:
        """What the host returned for one `exec` step, from the request that followed it."""
        items = [
            item
            for item in self.requests[step + 1]["input"]
            if item.get("type") == "custom_tool_call_output"
        ]
        output: list[dict[str, Any]] = items[-1]["output"]
        return output

    def text_of(self, step: int) -> str:
        return "\n".join(item.get("text", "") for item in self.outputs(step))


class _StandInHandler(BaseHTTPRequestHandler):
    server: StandInModel

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _event(self, event: dict[str, Any]) -> None:
        self.wfile.write(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode())
        self.wfile.flush()

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))))
        turn = len(self.server.requests)
        self.server.requests.append(body)
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        identifier = f"resp_{turn}"
        self._event({"type": "response.created", "response": {"id": identifier}})
        item: dict[str, Any]
        if turn < len(self.server.steps):
            item = {
                "type": "custom_tool_call",
                "id": f"ctc_{turn}",
                "call_id": f"call_{turn}",
                "name": "exec",
                "input": self.server.steps[turn],
            }
        else:
            item = {
                "type": "message",
                "id": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "done"}],
            }
        self._event({"type": "response.output_item.done", "item": item})
        usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
        self._event({"type": "response.completed", "response": {"id": identifier, "usage": usage}})


def model_path(
    codex: str, environment: dict[str, str], work: Path, check: Check, model: dict[str, Any]
) -> None:
    """Run the tools the way the host's own agent does: from JavaScript, under normalized names."""
    prefix = f"tools.mcp__{SERVER.replace('-', '_')}__"
    steps = [
        "text(JSON.stringify(ALL_TOOLS.map(t => t.name)));",
        f"text(JSON.stringify(await {prefix}setup_runtime({{}})));",
        f"const model = {json.dumps(model, ensure_ascii=False)};\n"
        'store("model", model);\n'
        f"const r = await {prefix}render_model({{model}});\n"
        "const body = JSON.parse(r.content[0].text);\n"
        "text(JSON.stringify({status: body.status, isError: r.isError, bundle: body.result.bundle_id}));\n"
        "image(r.content[1]);",
        f'const r = await {prefix}validate_model({{model: {{metadata: {{id: "x"}}}}}});\n'
        "const body = JSON.parse(r.content[0].text);\n"
        "text(JSON.stringify({status: body.status, code: body.code, isError: r.isError}));",
        f'const r = await {prefix}validate_model({{model: load("model")}});\n'
        "text(JSON.parse(r.content[0].text).status);",
    ]
    stand_in = StandInModel(steps)
    threading.Thread(target=stand_in.serve_forever, daemon=True).start()
    provider = (
        'model_providers.stand_in={name="stand-in",'
        f'base_url="http://127.0.0.1:{stand_in.server_address[1]}/v1",'
        'wire_api="responses",requires_openai_auth=false}'
    )
    try:
        done = subprocess.run(
            [
                codex,
                "exec",
                "--skip-git-repo-check",
                "--json",
                "-s",
                "read-only",
                "-c",
                provider,
                "-c",
                'model_provider="stand_in"',
                "-c",
                'model="gpt-6.1-sol"',
                "Draw a diagram",
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            env=environment,
            cwd=work,
            timeout=180,
            check=False,
        )
    finally:
        stand_in.shutdown()
    check.record(
        "the host's agent completes a turn against the stand-in model",
        done.returncode == 0 and len(stand_in.requests) == len(steps) + 1,
        requests=len(stand_in.requests),
    )
    first = json.dumps(stand_in.requests[0], ensure_ascii=False)
    check.record(
        "the skill reaches the model's first request",
        f"{PLUGIN}:architecture-model:" in first and "cloud-architecture-work" in first,
    )
    names = json.loads(stand_in.outputs(0)[-1]["text"])
    wanted = {f"mcp__{SERVER.replace('-', '_')}__{name}" for name in TOOLS}
    check.record(
        "every tool is callable from exec under the name the skill gives",
        wanted <= set(names),
        names=sorted(name for name in names if "cloud_architecture" in name),
    )
    check.record(
        "the host asks before setup_runtime, because it reaches the network",
        "requires approval" in stand_in.text_of(1),
        answer=stand_in.text_of(1)[-160:],
    )
    kinds = [item.get("type") for item in stand_in.outputs(2)]
    check.record(
        "a forwarded image reaches the model as an image",
        "input_image" in kinds and '"status":"ok"' in stand_in.text_of(2),
        output=kinds,
    )
    check.record(
        "a failed call reaches the model with its status and isError",
        '"status":"validation_failed"' in stand_in.text_of(3)
        and '"isError":true' in stand_in.text_of(3),
        answer=stand_in.text_of(3)[-160:],
    )
    check.record(
        "a stored model survives between exec calls, so it is written once",
        stand_in.text_of(4).rstrip().endswith("ok"),
    )


class Check:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(self, name: str, passed: bool, **detail: Any) -> None:
        self.results.append({"check": name, "passed": bool(passed), **detail})
        print(f"{'pass' if passed else 'FAIL'}  {name}", flush=True)

    @property
    def passed(self) -> bool:
        return all(item["passed"] for item in self.results)


def tree_digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }


def body_of(result: dict[str, Any]) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(result["content"][0]["text"])
    return value


def run(codex: str, work: Path, check: Check) -> None:
    home = work / "home"
    profile = work / "codex-home"
    home.mkdir()
    profile.mkdir()
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "CODEX_HOME": str(profile),
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
        "USER": os.environ.get("USER", ""),
    }
    report = build(work / "release")
    version = report["version"]

    def cli(*arguments: str) -> Any:
        return json.loads(
            subprocess.check_output([codex, *arguments], env=environment, cwd=work, text=True)
        )

    cli("plugin", "marketplace", "add", report["marketplace_root"], "--json")
    installed = cli("plugin", "add", f"{PLUGIN}@{MARKETPLACE}", "--json")
    cache = Path(installed["installedPath"])
    built = tree_digests(Path(report["marketplace_root"]) / "plugins" / PLUGIN)
    cached = tree_digests(cache)
    check.record(
        "install keeps every built file, byte for byte",
        all(cached.get(name) == digest for name, digest in built.items()),
        version=installed["version"],
        files=len(built),
        extra_in_cache=sorted(set(cached) - set(built)),
    )
    check.record("installed version is the stamped version", installed["version"] == version)
    check.record(
        "install holds no symbolic links",
        not [path for path in cache.rglob("*") if path.is_symlink()],
    )

    prompt = subprocess.check_output(
        [codex, "debug", "prompt-input", "hello"], env=environment, cwd=work, text=True
    )
    line = f"{PLUGIN}:architecture-model:"
    check.record("skill is offered in the model-visible prompt", line in prompt)

    host = AppServer(codex, environment, work)
    try:
        listed = host.request("plugin/list", {})
        entries = [
            plugin
            for market in listed["marketplaces"]
            for plugin in market["plugins"]
            if plugin["id"] == f"{PLUGIN}@{MARKETPLACE}"
        ]
        check.record(
            "marketplace lists the plugin as installed and enabled",
            len(entries) == 1 and entries[0]["installed"] and entries[0]["enabled"],
            display_name=entries[0]["interface"]["displayName"] if entries else None,
        )
        status = host.request("mcpServerStatus/list", {}, seconds=60)["data"]
        server = next((item for item in status if item["name"] == SERVER), None)
        check.record(
            "host discovers exactly the expected tools",
            server is not None and set(server["tools"]) == TOOLS,
            tools=sorted(server["tools"]) if server else None,
            server_version=server["serverInfo"]["version"] if server else None,
        )
        thread = host.request("thread/start", {"cwd": str(work)})["thread"]["id"]

        def tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
            result: dict[str, Any] = host.request(
                "mcpServer/tool/call",
                {"threadId": thread, "server": SERVER, "tool": name, "arguments": arguments or {}},
            )
            return result

        before = body_of(tool("get_capabilities"))["result"]
        check.record(
            "a fresh machine reports not_installed and the version",
            before["runtime"]["state"] == "not_installed"
            and before["plugin"]["version"] == version,
            checks=before["checks"],
            server_python=before["server_python"],
        )
        fixtures = ROOT / "tests/fixtures"
        valid = json.loads((fixtures / "core-valid.json").read_text())
        early = tool("validate_model", {"model": valid})
        check.record(
            "a call before setup is runtime_unavailable, not a result about the model",
            early.get("isError") is True and body_of(early)["code"] == "RUNTIME_NOT_READY",
        )
        started = time.monotonic()
        tool("setup_runtime")
        state = before
        while time.monotonic() - started < SETUP_SECONDS:
            state = body_of(tool("get_capabilities"))["result"]
            if state["runtime"]["state"] in ("ready", "failed"):
                break
            time.sleep(2)
        check.record(
            "first setup from an empty uv cache finishes and can render",
            state["runtime"]["state"] == "ready" and state["render_available"] is True,
            seconds=round(time.monotonic() - started, 1),
            runtime=state["runtime"],
            blockers=state["blockers"],
        )

        search = body_of(tool("search_catalog", {"provider": "aws", "query": "load balancer"}))
        check.record(
            "catalog search answers", search["status"] == "ok" and search["result"]["records"]
        )
        schema = body_of(tool("get_schema"))
        check.record(
            "schema discovery answers",
            schema["status"] == "ok" and "properties" in schema["result"],
        )

        broken = json.loads(json.dumps(valid))
        broken["views"][0]["entity_refs"] = ["does-not-exist"]
        refused = tool("validate_model", {"model": broken})
        refused_body = body_of(refused)
        check.record(
            "invalid input is validation_failed with a stable code",
            refused.get("isError") is True and refused_body["status"] == "validation_failed",
            code=refused_body.get("code"),
        )

        reference = json.loads((fixtures / "references/aws-three-tier.json").read_text())
        started = time.monotonic()
        drawn = tool("render_model", {"model": reference})
        drawn_body = body_of(drawn)
        result = drawn_body["result"]
        kinds = [item["type"] for item in drawn["content"]]
        check.record(
            "render publishes a bundle with an inline PNG",
            drawn_body["status"] == "ok" and result["rendered"] and "image" in kinds,
            seconds=round(time.monotonic() - started, 2),
            bundle_id=result["bundle_id"],
            content=kinds,
            png_bytes=next(a["bytes"] for a in result["artifacts"] if a["name"] == "diagram.png"),
        )
        bundle_id = result["bundle_id"]
        retrieved = {}
        for item in result["artifacts"]:
            answer = tool("read_artifact", {"bundle_id": bundle_id, "file": item["name"]})
            body = body_of(answer)
            on_disk = Path(item["path"]).read_bytes()
            content = answer["content"][1]
            if content["type"] == "image":
                data = base64.b64decode(content["data"])
            elif "text" in content["resource"]:
                data = content["resource"]["text"].encode()
            else:
                data = base64.b64decode(content["resource"]["blob"])
            retrieved[item["name"]] = (
                body["status"] == "ok"
                and hashlib.sha256(data).hexdigest() == item["sha256"]
                and hashlib.sha256(on_disk).hexdigest() == item["sha256"]
            )
        check.record(
            "all six files come back through the host and match their checksums",
            set(retrieved) == BUNDLE_FILES and all(retrieved.values()),
            files=retrieved,
        )

        views = [view["id"] for view in reference["views"]]
        other = tool("render_model", {"bundle_id": bundle_id, "view": views[-1]})
        check.record(
            "another view renders from the earlier bundle without resending the model",
            body_of(other)["status"] == "ok"
            and body_of(other)["result"]["selected_view"] == views[-1],
            views=views,
        )

        source = json.loads(
            tool("read_artifact", {"bundle_id": bundle_id, "file": "model.json"})["content"][1][
                "resource"
            ]["text"]
        )
        identifiers = {item["id"] for key in ("resources", "relationships") for item in source[key]}
        edited = json.loads(json.dumps(source))
        target = source["resources"][0]
        s3 = body_of(tool("search_catalog", {"type_id": "aws.storage.s3"}))["result"]["records"][0]
        s3_taxonomy = s3["taxonomy"]
        edited["resources"].append(
            {
                "id": "added-bucket",
                "name": "Added bucket",
                "provider": "aws",
                "service_type": "aws.storage.s3",
                "taxonomy": s3_taxonomy,
            }
        )
        edited["relationships"].append(
            {
                "id": "added-link",
                "kind": "traffic",
                "source_ref": target["id"],
                "target_ref": "added-bucket",
            }
        )
        edited["views"][0]["entity_refs"].append("added-bucket")
        edited["views"][0]["relationship_refs"].append("added-link")
        again = tool("render_model", {"model": edited})
        again_body = body_of(again)
        new_source = (
            json.loads(
                Path(
                    next(
                        a["path"]
                        for a in again_body["result"]["artifacts"]
                        if a["name"] == "model.json"
                    )
                ).read_text()
            )
            if again_body["status"] == "ok"
            else None
        )
        kept = (
            identifiers
            <= {item["id"] for key in ("resources", "relationships") for item in new_source[key]}
            if new_source
            else False
        )
        old_unchanged = hashlib.sha256(
            Path(
                next(a["path"] for a in result["artifacts"] if a["name"] == "model.json")
            ).read_bytes()
        ).hexdigest() == next(a["sha256"] for a in result["artifacts"] if a["name"] == "model.json")
        check.record(
            "an edit keeps every ID, returns the updated source, and leaves the old bundle alone",
            again_body["status"] == "ok" and kept and old_unchanged,
            code=again_body.get("code"),
            diagnostics=[d["code"] for d in again_body.get("result", {}).get("diagnostics", [])][
                :8
            ],
        )

        kubernetes = json.loads((fixtures / "kubernetes-valid.json").read_text())
        kube_views = {}
        for view in kubernetes["views"]:
            answer = body_of(tool("render_model", {"model": kubernetes, "view": view["id"]}))
            kube_views[view["id"]] = answer["status"]
        check.record(
            "every Kubernetes view renders",
            all(value == "ok" for value in kube_views.values()) and len(kube_views) >= 2,
            views=kube_views,
        )

        thai = json.loads(json.dumps(valid))
        thai["metadata"]["title"] = "สถาปัตยกรรมทดสอบ"
        thai["resources"][0]["name"] = "แอปพลิเคชันหลัก"
        thai_answer = body_of(tool("render_model", {"model": thai}))
        thai_ok = thai_answer["status"] == "ok"
        stored = (
            Path(
                next(
                    a["path"]
                    for a in thai_answer["result"]["artifacts"]
                    if a["name"] == "model.json"
                )
            ).read_text()
            if thai_ok
            else ""
        )
        check.record(
            "a Thai model renders and keeps its text", thai_ok and "แอปพลิเคชันหลัก" in stored
        )

        for label, arguments, expected in (
            (
                "traversal",
                {"bundle_id": "../../secret--a--0123456789abcdef", "file": "model.json"},
                "ARTIFACT_NAME_REFUSED",
            ),
            (
                "missing bundle",
                {"bundle_id": "nothing--here--0123456789abcdef", "file": "model.json"},
                "ARTIFACT_NOT_FOUND",
            ),
            (
                "unlisted file",
                {"bundle_id": bundle_id, "file": "../manifest.json"},
                "ARTIFACT_NAME_REFUSED",
            ),
        ):
            answer = tool("read_artifact", arguments)
            check.record(
                f"artifact scope refuses {label}",
                answer.get("isError") is True and body_of(answer)["code"] == expected,
            )
        listing = body_of(tool("list_bundles", {"limit": 5}))["result"]
        check.record(
            "bundles can be listed", len(listing["bundles"]) == 5, retention=listing["retention"]
        )
        check.record(
            "the output root and each bundle are private",
            os.stat(listing["root"]).st_mode & 0o077 == 0
            and all(
                os.stat(Path(listing["root"]) / item["bundle_id"]).st_mode & 0o077 == 0
                for item in listing["bundles"]
            ),
            root=listing["root"].replace(str(work), "<work>"),
        )
    finally:
        host.close()

    model_path(codex, environment, work, check, valid)

    runtime_script = cache / "scripts/runtime.py"
    runtime_data = home / ".local/share/cloud-architecture-diagrams/work-plugin"
    subprocess.run(
        ["python3", "-I", "-B", str(runtime_script), "remove"],
        env=environment,
        check=True,
        capture_output=True,
    )
    check.record("the runtime script removes the private runtime", not runtime_data.exists())
    bundles_left = home / "Documents/CloudArchitectureDiagrams/work"
    check.record("removing the runtime keeps bundles", any(bundles_left.iterdir()))
    cli("plugin", "remove", f"{PLUGIN}@{MARKETPLACE}", "--json")
    cli("plugin", "marketplace", "remove", MARKETPLACE, "--json")
    check.record(
        "uninstall leaves no install and no config entry",
        not cache.exists() and PLUGIN not in (profile / "config.toml").read_text(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=CODEX)
    parser.add_argument("--proof", type=Path, help="Write the results here as JSON")
    args = parser.parse_args()
    version = subprocess.check_output([args.codex, "--version"], text=True).strip()
    check = Check()
    # The host resolves real paths, and the core refuses a symbolic link in an output path.
    work = Path(tempfile.mkdtemp(prefix="s09-host-")).resolve()
    try:
        run(args.codex, work, check)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    proof = {
        "scope": (
            "The host's own engine and client, with a throwaway profile and no model or account. "
            "This is not the Work user interface."
        ),
        "host": version,
        "passed": check.passed,
        "checks": check.results,
    }
    if args.proof:
        args.proof.write_text(json.dumps(proof, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"passed": check.passed, "checks": len(check.results)}))
    return 0 if check.passed else 1


if __name__ == "__main__":
    sys.exit(main())
