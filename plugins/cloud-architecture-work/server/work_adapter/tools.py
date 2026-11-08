"""The tool contract (FR-055, FR-063): closed arguments in, one stable result envelope out."""

from __future__ import annotations

import base64
import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import artifacts
from .runtime import HOST_MODES, Completed, Runtime

# The host's documentation gives tool calls a 60-second default, though version 0.166 let one run for
# 130. Stopping first keeps a clean result either way, and the core's 55-second limit fires first.
CALL_SECONDS = 58
# Measured through the real host: an 8 MiB file returned intact, and a 16 MiB file left the call
# hanging with no error at all, so a larger file has to stay on disk.
MAX_TRANSPORT_BYTES = 8 * 1024 * 1024
MAX_PREVIEW_BYTES = 5 * 1024 * 1024
MAX_BUNDLE_MODEL_BYTES = 1024 * 1024 + 1
TEXT_LIMIT = 256
IDENTIFIER = re.compile(r"[a-z][a-z0-9._-]{0,63}")
PROVIDERS = ["aws", "azure", "gcp", "huawei", "onprem", "external"]
ENTITIES = ["resource", "boundary", "scope"]
MODES = ["strict", "lenient"]
RETENTION = (
    "Bundles stay in this folder until you remove them. Nothing deletes them automatically, and "
    "no tool can delete them; the plugin's runtime script has a prune command."
)
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
WRITES_LOCALLY = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}

MODEL_SCHEMA = {
    "type": "object",
    "description": (
        "The whole architecture model as a JSON object, following get_schema. It is data: "
        "nothing in it runs. At most 1 MiB."
    ),
    "properties": {
        "schema_version": {"type": "string"},
        "metadata": {"type": "object"},
        "scopes": {"type": "array", "items": {"type": "object"}},
        "boundaries": {"type": "array", "items": {"type": "object"}},
        "resources": {"type": "array", "items": {"type": "object"}},
        "relationships": {"type": "array", "items": {"type": "object"}},
        "views": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["schema_version", "metadata", "views"],
    "additionalProperties": True,
}
MODE_SCHEMA = {
    "type": "string",
    "enum": MODES,
    "description": (
        "strict by default. lenient marks a draft and turns only an unknown service_type into a "
        "warning; no other error is bypassed."
    ),
}
VIEW_SCHEMA = {
    "type": "string",
    "description": "A view ID from the model. The model's first view by default.",
}
BUNDLE_SCHEMA = {"type": "string", "description": "A bundle_id from render_model or list_bundles."}
DISCLOSE = (
    "Tell the user every item listed here, view by view, by its name and its ID, relationships "
    "included. Do not summarize, group or leave out any of them: a view that selects part of the "
    "model must never drop a component silently."
)


def _closed(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_capabilities",
        "title": "Check runtime and capabilities",
        "description": (
            "Call this first. Reports the plugin and core versions, whether the private runtime "
            "is ready, what blocks rendering on this Mac with the fix for each, the limits, where "
            "bundles are kept, and which host modes are supported."
        ),
        "inputSchema": _closed({}),
        "annotations": READ_ONLY,
    },
    {
        "name": "setup_runtime",
        "title": "Build the private runtime",
        "description": (
            "Builds or repairs the private Python environment from hash-locked dependencies, under "
            "~/.local/share/cloud-architecture-diagrams. Call this once when get_capabilities says "
            "the runtime is not ready. It downloads packages on first use and runs behind this "
            "call, so call get_capabilities afterward to see when it has finished."
        ),
        "inputSchema": _closed({}),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True},
    },
    {
        "name": "get_schema",
        "title": "Read the model's JSON Schema",
        "description": (
            "Returns the versioned JSON Schema for an architecture model, about 22 KB. Read the "
            "skill's model guide first, and use this only when the guide is not enough."
        ),
        "inputSchema": _closed({}),
        "annotations": READ_ONLY,
    },
    {
        "name": "search_catalog",
        "title": "Search provider and Kubernetes types",
        "description": (
            "Finds exact service_type IDs, each with its one taxonomy ID and placement rule. "
            "Results are bounded, so narrow the search rather than paging. Never guess an ID."
        ),
        "inputSchema": _closed(
            {
                "provider": {"type": "string", "enum": PROVIDERS},
                "entity": {"type": "string", "enum": ENTITIES},
                "taxonomy": {"type": "string", "description": "One taxonomy ID."},
                "query": {
                    "type": "string",
                    "description": "Text in the type ID, display name or native ID.",
                },
                "type_id": {"type": "string", "description": "One exact type ID."},
                "kubernetes": {
                    "type": "boolean",
                    "description": "Only types that map to Kubernetes kinds.",
                },
                "list_taxonomy": {
                    "type": "boolean",
                    "description": "Return the taxonomy IDs instead of types.",
                },
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            }
        ),
        "annotations": READ_ONLY,
    },
    {
        "name": "validate_model",
        "title": "Validate an architecture model",
        "description": (
            "Checks structure, IDs, references, cycles, views, Kubernetes context, catalog types "
            "and provider placement rules. Draws nothing. Fix each error by its code and remedy; "
            "do not delete a requested component to make this pass. When a view leaves part of "
            "the model out, disclose lists each item by name and ID for the user."
        ),
        "inputSchema": _closed(
            {"model": MODEL_SCHEMA, "mode": MODE_SCHEMA, "view": VIEW_SCHEMA}, ["model"]
        ),
        "annotations": READ_ONLY,
    },
    {
        "name": "render_model",
        "title": "Draw one view to a bundle",
        "description": (
            "Validates, then draws one view to SVG and PNG with the controlled Graphviz renderer "
            "and publishes a new bundle on this Mac. Pass model, or bundle_id to draw another view "
            "of a model already rendered without sending it again. Run one render at a time. "
            "The result lists every file's path and checksum and includes the PNG as a preview. "
            "When the drawn view leaves part of the model out, disclose lists each item by name "
            "and ID for the user."
        ),
        "inputSchema": _closed(
            {
                "model": MODEL_SCHEMA,
                "bundle_id": BUNDLE_SCHEMA,
                "mode": MODE_SCHEMA,
                "view": VIEW_SCHEMA,
            }
        ),
        "annotations": WRITES_LOCALLY,
    },
    {
        "name": "read_artifact",
        "title": "Read one file from a bundle",
        "description": (
            "Returns one bundle file by its fixed name. Use it for model.json when editing an "
            "earlier model, and for the PNG. A file's path is already in the render result, so "
            "you rarely need this for diagram.svg, which is large."
        ),
        "inputSchema": _closed(
            {
                "bundle_id": BUNDLE_SCHEMA,
                "file": {"type": "string", "enum": sorted(artifacts.MEDIA_TYPES)},
            },
            ["bundle_id", "file"],
        ),
        "annotations": READ_ONLY,
    },
    {
        "name": "list_bundles",
        "title": "List recent bundles",
        "description": "Lists published bundles, newest first, with each one's view and limits.",
        "inputSchema": _closed(
            {"limit": {"type": "integer", "minimum": 1, "maximum": artifacts.MAX_LISTED}}
        ),
        "annotations": READ_ONLY,
    },
]


@dataclass
class Outcome:
    """`body` becomes the JSON text every result starts with, so any host can read it."""

    body: dict[str, Any]
    extra_content: list[dict[str, Any]] = field(default_factory=list)

    @property
    def is_error(self) -> bool:
        return bool(self.body.get("status") != "ok")

    def result(self) -> dict[str, Any]:
        # No structuredContent: a host may send only that to the model and drop the image with it.
        text = json.dumps(self.body, ensure_ascii=False, indent=1)
        return {
            "content": [{"type": "text", "text": text}, *self.extra_content],
            "isError": self.is_error,
        }


def success(result: Any, **extra: Any) -> Outcome:
    return Outcome({"status": "ok", **extra, "result": result})


def failure(status: str, code: str, message: str, remedy: str, **extra: Any) -> Outcome:
    return Outcome({"status": status, "code": code, "message": message, "remedy": remedy, **extra})


def invalid(message: str) -> Outcome:
    return failure(
        "invalid_arguments",
        "INVALID_ARGUMENTS",
        message,
        "Correct the arguments to match this tool's input schema, then call it again.",
    )


def _first_error(report: dict[str, Any]) -> dict[str, Any]:
    for item in report.get("diagnostics", []):
        if item.get("severity") == "error":
            return dict(item)
    return {}


def _listed(model: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = model.get(key)
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _disclosure(payload: bytes, report: dict[str, Any], views: list[Any]) -> dict[str, Any]:
    """Name what each view leaves out (FR-025), so a chat tells the user rather than summarizing.

    Work chats on 2026-11-07 and 2026-11-08 explained or skipped excluded IDs in their own words.
    """
    exclusions = report.get("view_exclusions")
    if not isinstance(exclusions, dict):
        return {}
    partial = [
        (view, exclusions[view])
        for view in views
        if isinstance(view, str) and isinstance(exclusions.get(view), list) and exclusions[view]
    ]
    if not partial:
        return {}
    try:
        model = json.loads(payload)
    except ValueError:
        model = None
    if not isinstance(model, dict):
        model = {}
    names = {
        entity.get("id"): entity.get("name")
        for key in ("scopes", "boundaries", "resources")
        for entity in _listed(model, key)
    }
    edges = {edge.get("id"): edge for edge in _listed(model, "relationships")}

    def item(identifier: Any) -> dict[str, Any]:
        if identifier in names:
            return {"id": identifier, "name": names[identifier]}
        edge = edges.get(identifier)
        if edge is None:
            return {"id": identifier}
        source = names.get(edge.get("source_ref"), edge.get("source_ref"))
        target = names.get(edge.get("target_ref"), edge.get("target_ref"))
        described = {"id": identifier, "relationship": f"{source} -> {target}"}
        if edge.get("label"):
            described["label"] = edge["label"]
        return described

    return {
        "disclose": {
            "instruction": DISCLOSE,
            "views": [
                {"view": view, "left_out": [item(identifier) for identifier in identifiers]}
                for view, identifiers in partial
            ],
        }
    }


def _encode_model(model: Any) -> bytes | Outcome:
    if not isinstance(model, dict):
        return invalid("model must be a JSON object, not a string or a list.")
    try:
        # A string the host passed through unpaired reaches the core as invalid UTF-8, which it refuses.
        return json.dumps(model, ensure_ascii=False, allow_nan=False).encode(
            "utf-8", "surrogatepass"
        )
    except (ValueError, RecursionError):
        return failure(
            "validation_failed",
            "MODEL_NOT_SERIALIZABLE",
            "The model holds a value that JSON cannot carry, or it is nested too deeply.",
            "Use plain JSON values, and nest no deeper than 64 levels.",
        )


def _checked_view(arguments: dict[str, Any]) -> list[str] | Outcome:
    view = arguments.get("view")
    if view is None:
        return []
    if not isinstance(view, str) or not IDENTIFIER.fullmatch(view):
        return invalid("view must be a view ID from the model.")
    return ["--view=" + view]


def _checked_mode(arguments: dict[str, Any]) -> list[str] | Outcome:
    mode = arguments.get("mode", "strict")
    if mode not in MODES:
        return invalid("mode must be strict or lenient.")
    return ["--mode=" + str(mode)]


class Toolbox:
    """Maps tool calls onto one core subcommand each, and core outcomes onto result statuses."""

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.render_gate = threading.Lock()
        self.handlers = {
            "get_capabilities": self.get_capabilities,
            "setup_runtime": self.setup_runtime,
            "get_schema": self.get_schema,
            "search_catalog": self.search_catalog,
            "validate_model": self.validate_model,
            "render_model": self.render_model,
            "read_artifact": self.read_artifact,
            "list_bundles": self.list_bundles,
        }
        self.allowed = {tool["name"]: set(tool["inputSchema"]["properties"]) for tool in TOOLS}

    def call(self, name: str, arguments: Any, token: Any) -> Outcome:
        handler = self.handlers.get(name)
        if handler is None:
            return invalid("There is no such tool.")
        arguments = {} if arguments is None else arguments
        if not isinstance(arguments, dict):
            return invalid("Arguments must be a JSON object.")
        if set(arguments) - self.allowed[name]:
            return invalid("An argument this tool does not take was supplied.")
        return handler(arguments, token)

    def _not_ready(self) -> Outcome | None:
        if not self.runtime.installed_files_present():
            return failure(
                "runtime_unavailable",
                "PLUGIN_UPDATED",
                "This chat's tool process belongs to a plugin version that is no longer installed.",
                "Open a new chat, or restart the ChatGPT app, so that the current version loads.",
            )
        state = self.runtime.state()
        if state["state"] == "ready":
            return None
        if state["state"] == "installing":
            return failure(
                "runtime_unavailable",
                "RUNTIME_INSTALLING",
                "The private runtime is still being built.",
                "Wait, then check get_capabilities until runtime.state is ready.",
            )
        if state["state"] == "failed":
            return failure(
                "runtime_unavailable",
                state["failure"].get("code", "RUNTIME_SETUP_FAILED"),
                state["failure"].get("message", "Setup failed."),
                state["failure"].get("remedy", "Call setup_runtime again."),
            )
        return failure(
            "runtime_unavailable",
            "RUNTIME_NOT_READY",
            "The private runtime has not been built on this Mac yet.",
            "Call setup_runtime, then check get_capabilities until runtime.state is ready.",
        )

    def _run(self, arguments: list[str], payload: bytes | None, token: Any) -> Completed | Outcome:
        blocked = self._not_ready()
        if blocked is not None:
            return blocked
        try:
            return self.runtime.run_core(arguments, payload, CALL_SECONDS, token)
        except OSError:
            return failure(
                "runtime_failure",
                "CORE_NOT_STARTED",
                "The private runtime could not be started.",
                "Call setup_runtime to repair it, then try again.",
            )

    @staticmethod
    def _timeout() -> Outcome:
        return failure(
            "timeout",
            "CALL_TIMEOUT",
            "The call exceeded its time limit and was stopped. Nothing was published.",
            "Split the view into smaller views, then try again.",
        )

    def _report(self, done: Completed) -> dict[str, Any] | Outcome:
        """A status the core does not document means a crash, never a result about the model."""
        if done.timed_out:
            return self._timeout()
        if done.cancelled:
            return failure(
                "runtime_failure",
                "CALL_CANCELLED",
                "The call was cancelled and stopped.",
                "Call it again if it is still needed.",
            )
        if done.status not in (0, 2, 4):
            return failure(
                "runtime_failure",
                "CORE_CRASHED",
                "The core stopped unexpectedly and reported no result.",
                "Call setup_runtime to repair the runtime, then try again.",
            )
        try:
            report = json.loads(done.stdout)
        except ValueError:
            report = None
        if not isinstance(report, dict):
            return failure(
                "runtime_failure",
                "CORE_CRASHED",
                "The core reported a result that could not be read.",
                "Call setup_runtime to repair the runtime, then try again.",
            )
        return report

    def _failed_core_call(self, done: Completed, report: dict[str, Any]) -> Outcome:
        first = _first_error(report)
        code = str(first.get("code", "CORE_FAILED"))
        if done.status == 2:
            status = "validation_failed"
        elif code == "RENDER_TIMEOUT":
            status = "timeout"
        else:
            status = "runtime_failure"
        return failure(
            status,
            code,
            str(first.get("message", "The core reported a failure.")),
            str(first.get("remedy", "Read the diagnostics in result.")),
            result=report,
        )

    # Tools.
    def get_capabilities(self, _arguments: dict[str, Any], token: Any) -> Outcome:
        runtime = self.runtime
        if not runtime.installed_files_present():
            blocked = self._not_ready()
            assert blocked is not None
            return blocked
        preflight = runtime.preflight()
        blockers = list(preflight["blockers"])
        state = runtime.state()
        core: dict[str, Any] | None = None
        if state["state"] == "ready":
            done = self._run(["capabilities"], None, token)
            if isinstance(done, Completed):
                report = self._report(done)
                core = report if isinstance(report, dict) else None
        if core is None:
            # The same answer a tool would give, so that installing never reads as "call setup".
            blocked = self._not_ready()
            blockers.append(
                {key: str(blocked.body[key]) for key in ("code", "message", "remedy")}
                if blocked
                else {
                    "code": "CORE_CRASHED",
                    "message": "The core did not report its capabilities.",
                    "remedy": "Call setup_runtime to repair the runtime, then check again.",
                }
            )
        ready = core is not None and bool(core.get("render_available")) and not blockers
        return success(
            {
                "plugin": {"name": runtime.manifest["name"], "version": runtime.version},
                "core_version": runtime.core_version(),
                "runtime": {key: value for key, value in state.items() if key != "lock_sha256"},
                # The host asks before a tool that reaches the network, and a user can decline it.
                "setup_command": runtime.setup_command(),
                "render_available": ready,
                "blockers": blockers,
                "checks": preflight["checks"],
                "server_python": preflight["server_python"],
                "artifacts": {
                    "root": str(runtime.output),
                    "bundles": artifacts.count_bundles(runtime.output),
                    "retention": RETENTION,
                    "transport_limit_bytes": MAX_TRANSPORT_BYTES,
                },
                "host_modes": HOST_MODES,
                "core": core,
            }
        )

    def setup_runtime(self, _arguments: dict[str, Any], _token: Any) -> Outcome:
        if not self.runtime.installed_files_present():
            blocked = self._not_ready()
            assert blocked is not None
            return blocked
        started = self.runtime.start_setup()
        return success(
            {
                "started": started,
                "next": "Check get_capabilities until runtime.state is ready or failed.",
            }
        )

    def get_schema(self, _arguments: dict[str, Any], token: Any) -> Outcome:
        done = self._run(["schema"], None, token)
        if isinstance(done, Outcome):
            return done
        report = self._report(done)
        return report if isinstance(report, Outcome) else success(report)

    def search_catalog(self, arguments: dict[str, Any], token: Any) -> Outcome:
        command = ["catalog"]
        for key, option, allowed in (
            ("provider", "--provider", PROVIDERS),
            ("entity", "--entity", ENTITIES),
        ):
            if key in arguments:
                if arguments[key] not in allowed:
                    return invalid(f"{key} must be one of: {', '.join(allowed)}.")
                command.append(f"{option}={arguments[key]}")
        for key, option in (
            ("taxonomy", "--taxonomy"),
            ("query", "--query"),
            ("type_id", "--type"),
        ):
            if key in arguments:
                value = arguments[key]
                # A control character or an unpaired surrogate cannot pass as a process argument.
                if not isinstance(value, str) or len(value) > TEXT_LIMIT or not value.isprintable():
                    return invalid(f"{key} must be text of at most {TEXT_LIMIT} characters.")
                # The joined form keeps a value starting with a dash from reading as an option.
                command.append(f"{option}={value}")
        for key, option in (("kubernetes", "--kubernetes"), ("list_taxonomy", "--taxonomy-list")):
            if key in arguments:
                if not isinstance(arguments[key], bool):
                    return invalid(f"{key} must be true or false.")
                if arguments[key]:
                    command.append(option)
        if "limit" in arguments:
            limit = arguments["limit"]
            if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
                return invalid("limit must be a whole number from 1 to 200.")
            command.append(f"--limit={limit}")
        done = self._run(command, None, token)
        if isinstance(done, Outcome):
            return done
        report = self._report(done)
        return report if isinstance(report, Outcome) else success(report)

    def validate_model(self, arguments: dict[str, Any], token: Any) -> Outcome:
        if "model" not in arguments:
            return invalid("model is required.")
        mode = _checked_mode(arguments)
        view = _checked_view(arguments)
        for checked in (mode, view):
            if isinstance(checked, Outcome):
                return checked
        assert isinstance(mode, list) and isinstance(view, list)
        payload = _encode_model(arguments["model"])
        if isinstance(payload, Outcome):
            return payload
        done = self._run(["validate", *mode, *view], payload, token)
        if isinstance(done, Outcome):
            return done
        report = self._report(done)
        if isinstance(report, Outcome):
            return report
        if done.status != 0:
            return self._failed_core_call(done, report)
        exclusions = report.get("view_exclusions")
        views = list(exclusions) if isinstance(exclusions, dict) else []
        return success(report, **_disclosure(payload, report, views))

    def _render_payload(self, arguments: dict[str, Any]) -> bytes | Outcome:
        if ("model" in arguments) == ("bundle_id" in arguments):
            return invalid("Pass exactly one of model and bundle_id.")
        if "model" in arguments:
            return _encode_model(arguments["model"])
        bundle_id = arguments["bundle_id"]
        if not isinstance(bundle_id, str):
            return invalid("bundle_id must be text.")
        try:
            return artifacts.read_file(
                self.runtime.output, bundle_id, "model.json", MAX_BUNDLE_MODEL_BYTES
            )
        except artifacts.ArtifactError as error:
            return self._artifact_failure(error.code)

    def render_model(self, arguments: dict[str, Any], token: Any) -> Outcome:
        mode = _checked_mode(arguments)
        view = _checked_view(arguments)
        for checked in (mode, view):
            if isinstance(checked, Outcome):
                return checked
        assert isinstance(mode, list) and isinstance(view, list)
        payload = self._render_payload(arguments)
        if isinstance(payload, Outcome):
            return payload
        if not self.render_gate.acquire(blocking=False):
            return failure(
                "busy",
                "RENDER_BUSY",
                "Another render is still running in this chat's tool process.",
                "Render one view at a time, and call this again when that one has finished.",
            )
        try:
            command = ["render", "--output=" + str(self.runtime.output), *mode, *view]
            done = self._run(command, payload, token)
        finally:
            self.render_gate.release()
        if isinstance(done, Outcome):
            return done
        report = self._report(done)
        if isinstance(report, Outcome):
            return report
        if done.status != 0 or report.get("rendered") is not True:
            return self._failed_core_call(done, report)
        # Only the drawn view: another view's exclusions belong to its own render.
        return self._published(report, _disclosure(payload, report, [report.get("selected_view")]))

    def _published(self, report: dict[str, Any], disclosed: dict[str, Any]) -> Outcome:
        bundle_id = str(report.get("bundle_id"))
        try:
            artifacts.verify_published(self.runtime.output, bundle_id, report.get("artifacts", []))
            png = artifacts.read_file(self.runtime.output, bundle_id, "diagram.png")
        except (artifacts.ArtifactError, KeyError, TypeError) as error:
            code = (
                error.code if isinstance(error, artifacts.ArtifactError) else "ARTIFACT_INTEGRITY"
            )
            return self._artifact_failure(code, result=report)
        if len(png) > MAX_PREVIEW_BYTES:
            return success(report, preview="omitted: open diagram.png by its path", **disclosed)
        image = {
            "type": "image",
            "data": base64.b64encode(png).decode("ascii"),
            "mimeType": "image/png",
        }
        return Outcome(success(report, preview="diagram.png follows", **disclosed).body, [image])

    @staticmethod
    def _artifact_failure(code: str, **extra: Any) -> Outcome:
        messages = {
            "ARTIFACT_NAME_REFUSED": (
                "That is not a bundle_id this plugin issues, or not a file a bundle holds.",
                "Use a bundle_id from render_model or list_bundles, and a listed file name.",
            ),
            "ARTIFACT_NOT_FOUND": (
                "That bundle or file does not exist any more.",
                "Check list_bundles, and render the view again if it was removed.",
            ),
            "ARTIFACT_UNSAFE": (
                "The bundle is not an ordinary folder of ordinary files, so it was not read.",
                "Render the view again into a new bundle; do not link or move files into one.",
            ),
            "ARTIFACT_TOO_LARGE": (
                "The file exceeds the limit on reading a bundle file.",
                "Open it by its path on this Mac, or split the view into smaller views.",
            ),
            "ARTIFACT_INCOMPLETE": (
                "The bundle does not hold every file it should, so it does not count as a result.",
                "Render the view again.",
            ),
            "ARTIFACT_INTEGRITY": (
                "A bundle file does not match the checksum the renderer recorded.",
                "Render the view again, and do not use the changed file.",
            ),
        }
        message, remedy = messages[code]
        return failure("artifact_unavailable", code, message, remedy, **extra)

    def read_artifact(self, arguments: dict[str, Any], _token: Any) -> Outcome:
        bundle_id = arguments.get("bundle_id")
        name = arguments.get("file")
        if not isinstance(bundle_id, str) or not isinstance(name, str):
            return invalid("bundle_id and file are both required.")
        try:
            data = artifacts.read_file(
                self.runtime.output, bundle_id, name, limit=MAX_TRANSPORT_BYTES
            )
        except artifacts.ArtifactError as error:
            if error.code == "ARTIFACT_TOO_LARGE":
                return self._artifact_failure(
                    error.code, path=str(self.runtime.output / bundle_id / name)
                )
            return self._artifact_failure(error.code)
        media_type = artifacts.MEDIA_TYPES[name]
        body = success(
            {
                "bundle_id": bundle_id,
                "file": name,
                "path": str(self.runtime.output / bundle_id / name),
                "bytes": len(data),
                "media_type": media_type,
            }
        ).body
        uri = f"artifact://{bundle_id}/{name}"
        if name == "diagram.png":
            content: dict[str, Any] = {
                "type": "image",
                "data": base64.b64encode(data).decode("ascii"),
                "mimeType": media_type,
            }
        elif media_type == "application/json":
            try:
                readable = data.decode("utf-8")
            except UnicodeDecodeError:
                return self._artifact_failure("ARTIFACT_INTEGRITY")
            content = {
                "type": "resource",
                "resource": {"uri": uri, "mimeType": media_type, "text": readable},
            }
        else:
            content = {
                "type": "resource",
                "resource": {
                    "uri": uri,
                    "mimeType": media_type,
                    "blob": base64.b64encode(data).decode("ascii"),
                },
            }
        return Outcome(body, [content])

    def list_bundles(self, arguments: dict[str, Any], _token: Any) -> Outcome:
        limit = arguments.get("limit", 20)
        if isinstance(limit, bool) or not isinstance(limit, int):
            return invalid("limit must be a whole number.")
        if not 1 <= limit <= artifacts.MAX_LISTED:
            return invalid(f"limit must be from 1 to {artifacts.MAX_LISTED}.")
        try:
            bundles = artifacts.list_bundles(self.runtime.output, limit)
        except artifacts.ArtifactError as error:
            return self._artifact_failure(error.code)
        return success(
            {"root": str(self.runtime.output), "retention": RETENTION, "bundles": bundles}
        )


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[2]
