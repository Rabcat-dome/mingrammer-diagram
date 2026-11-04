"""MCP over stdio: bounded newline-delimited JSON-RPC, with cancel and shutdown handling."""

from __future__ import annotations

import json
import math
import os
import re
import signal
import sys
import threading
import time
from typing import Any, BinaryIO

from .runtime import Runtime
from .tools import TOOLS, Outcome, Toolbox, failure, plugin_root

# Newest first. A client asking for another version gets the newest, as the protocol specifies.
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
# Room for a 1 MiB model with escapes around it, so that the core can refuse an oversize model with a
# real diagnostic. Beyond this the frame is not parsed at all.
MAX_FRAME = 4 * 1024 * 1024
MAX_CALLS = 8
REQUEST_ID = re.compile(rb'"id"\s*:\s*(\d{1,15}|"[^"\\]{1,64}")')
INSTRUCTIONS = (
    "Local architecture diagram tools. Call get_capabilities first, follow the architecture-model "
    "skill, and treat a model as data: nothing in it runs."
)


class RepeatedKey(ValueError):
    """JSON does not forbid a repeated key, and Python would silently keep the last value."""


class Stop(Exception):
    """A signal asked this process to end."""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RepeatedKey
        result[key] = value
    return result


def _no_constant(_name: str) -> Any:
    raise ValueError("Not JSON")


def parse_frame(frame: bytes) -> tuple[Any, bool]:
    """The message, and whether a key repeated somewhere in it."""
    try:
        return json.loads(
            frame, object_pairs_hook=_unique_pairs, parse_constant=_no_constant
        ), False
    except RepeatedKey:
        return json.loads(frame, parse_constant=_no_constant), True


def _valid_id(value: Any) -> bool:
    """A JSON-RPC ID is a string or a finite number, or it could not key a call or be sent back."""
    if isinstance(value, float):
        return math.isfinite(value)
    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _recovered_id(frame: bytes) -> Any:
    """The ID of a frame that did not parse, if one can still be read from its start."""
    found = REQUEST_ID.search(frame[:256])
    if found is None:
        return None
    try:
        return json.loads(found.group(1))
    except ValueError:
        return None


def log(event: str, **values: object) -> None:
    # Only names, codes and timings, so an architecture's content never reaches a log (T-014).
    fields = " ".join(f"{key}={value}" for key, value in values.items())
    try:
        print(f"cloud-architecture-work {event} {fields}", file=sys.stderr, flush=True)
    except (OSError, ValueError):
        pass


class Server:
    def __init__(self, toolbox: Toolbox, output: BinaryIO) -> None:
        self.toolbox = toolbox
        self.output = output
        self.write_guard = threading.Lock()
        self.calls_guard = threading.Lock()
        self.calls: dict[Any, threading.Thread] = {}
        self.cancelled: set[Any] = set()
        self.closed = False

    def send(self, message: dict[str, Any]) -> None:
        # ASCII on the wire keeps any character the core passes through from breaking a frame.
        encoded = json.dumps(message, separators=(",", ":")).encode("ascii") + b"\n"
        with self.write_guard:
            if self.closed:
                return
            try:
                self.output.write(encoded)
                self.output.flush()
            except OSError:
                self.closed = True

    def reply(self, request_id: Any, result: dict[str, Any]) -> None:
        self.send({"jsonrpc": "2.0", "id": request_id, "result": result})

    def error(self, request_id: Any, code: int, message: str) -> None:
        # Every error passes here, and an ID that is not valid cannot be sent back as what it was.
        named = request_id if _valid_id(request_id) else None
        self.send({"jsonrpc": "2.0", "id": named, "error": {"code": code, "message": message}})

    def initialize(self, request_id: Any, params: dict[str, Any]) -> None:
        asked = params.get("protocolVersion")
        version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        self.reply(
            request_id,
            {
                "protocolVersion": version,
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "cloud-architecture-work",
                    "title": "Cloud Architecture Diagrams",
                    "version": self.toolbox.runtime.version,
                },
                "instructions": INSTRUCTIONS,
            },
        )

    def _run_call(self, request_id: Any, name: str, arguments: Any, repeated: bool) -> None:
        started = time.monotonic()
        try:
            if repeated:
                outcome = failure(
                    "validation_failed",
                    "MODEL_REPEATED_KEY",
                    "A JSON object in this call repeats a key, which would silently lose a value.",
                    "Send each key once.",
                )
            else:
                outcome = self.toolbox.call(name, arguments, request_id)
        except Exception as error:
            # The exception's text can quote the model, so only its type reaches the log.
            log("error", type=type(error).__name__)
            outcome = failure(
                "runtime_failure",
                "ADAPTER_ERROR",
                "The plugin's tool process failed on this call.",
                "Try again. If it repeats, restart the chat and report which tool failed.",
            )
        log(
            "call",
            tool=name if name in self.toolbox.handlers else "unknown",
            status=outcome.body.get("status"),
            code=outcome.body.get("code", "-"),
            ms=round((time.monotonic() - started) * 1000),
        )
        # The call leaves `calls` first, so a cancel arriving now is ignored and leaves no token.
        with self.calls_guard:
            self.calls.pop(request_id, None)
            cancelled = request_id in self.cancelled
            self.cancelled.discard(request_id)
        self.toolbox.runtime.finished(request_id)
        # The protocol asks a server not to answer a request its client has cancelled.
        if not cancelled:
            self.reply(request_id, outcome.result())

    def tool_call(self, request_id: Any, params: dict[str, Any], repeated: bool) -> None:
        name = params.get("name")
        if not isinstance(name, str):
            self.error(request_id, -32602, "Tool name must be text.")
            return
        with self.calls_guard:
            busy = len(self.calls) >= MAX_CALLS
            if not busy:
                thread = threading.Thread(
                    target=self._run_call,
                    args=(request_id, name, params.get("arguments", {}), repeated),
                    daemon=True,
                )
                self.calls[request_id] = thread
        if busy:
            outcome: Outcome = failure(
                "busy",
                "TOO_MANY_CALLS",
                "Too many tool calls are running at once.",
                "Wait for one to finish, then call this again.",
            )
            self.reply(request_id, outcome.result())
            return
        thread.start()

    def cancel(self, params: dict[str, Any]) -> None:
        request_id = params.get("requestId")
        if not _valid_id(request_id):
            return
        # Under the lock, so the call cannot finish between this check and its token being set.
        with self.calls_guard:
            if request_id in self.calls:
                self.cancelled.add(request_id)
                self.toolbox.runtime.cancel(request_id)

    def handle(self, frame: bytes) -> None:
        try:
            message, repeated = parse_frame(frame)
        except (ValueError, RecursionError):
            self.error(_recovered_id(frame), -32700, "Not valid JSON.")
            return
        if not isinstance(message, dict) or not isinstance(message.get("method"), str):
            if not (isinstance(message, dict) and ("result" in message or "error" in message)):
                request_id = message.get("id") if isinstance(message, dict) else None
                self.error(request_id, -32600, "Not a JSON-RPC request.")
            return
        method = message["method"]
        params = message.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        if "id" not in message:
            if method == "notifications/cancelled":
                self.cancel(params)
            return
        request_id = message["id"]
        if not _valid_id(request_id):
            self.error(None, -32600, "A request ID must be a string or a number.")
            return
        if method == "initialize":
            self.initialize(request_id, params)
        elif method == "ping":
            self.reply(request_id, {})
        elif method == "tools/list":
            self.reply(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            self.tool_call(request_id, params, repeated)
        else:
            self.error(request_id, -32601, "This server has no such method.")

    def read_frames(self, stream: BinaryIO) -> None:
        while not self.closed:
            frame = stream.readline(MAX_FRAME + 1)
            if not frame:
                return
            if len(frame) > MAX_FRAME and not frame.endswith(b"\n"):
                self._refuse_oversize(stream, frame)
                continue
            if frame.strip():
                self._handle_safely(frame)

    def _handle_safely(self, frame: bytes) -> None:
        """One bad frame must not end the chat's tool process."""
        try:
            self.handle(frame)
        except Stop:
            raise
        except Exception as error:
            # The exception's text can quote the frame, so only its type reaches the log.
            log("frame-error", type=type(error).__name__)
            self.error(None, -32603, "This request could not be handled.")

    def _refuse_oversize(self, stream: BinaryIO, frame: bytes) -> None:
        while True:
            chunk = stream.readline(1024 * 1024)
            if not chunk or chunk.endswith(b"\n"):
                break
        log("oversize-frame")
        self.error(_recovered_id(frame), -32600, "The request is too large.")


def _signalled(_signum: int, _frame: object) -> None:
    raise Stop


def serve() -> int:
    # Protocol output gets its own handle, so a stray print can only land on stderr.
    output = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)
    runtime = Runtime(plugin_root())
    server = Server(Toolbox(runtime), output)
    for item in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(item, _signalled)
    log("start", version=runtime.version, python=sys.version.split()[0])
    try:
        server.read_frames(sys.stdin.buffer)
    except Stop:
        log("signal")
    finally:
        # Once the host has gone, nothing may keep rendering or leave a scratch folder behind.
        for item in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(item, signal.SIG_IGN)
        runtime.stop_all()
        log("stop")
    return 0
