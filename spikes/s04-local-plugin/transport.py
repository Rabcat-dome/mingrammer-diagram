"""Cancelable, bounded POSIX stdio streams for the pinned MCP 2.3 adapter."""
import os
import anyio
from mcp.server.stdio import stdio_server
from execution import stop_requests

MAX_FRAME = 1024 * 1024


class Lines:
    def __init__(self, descriptor):
        self.descriptor = descriptor
        self.buffer = bytearray()

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            index = self.buffer.find(b'\n')
            if index >= 0:
                if index > MAX_FRAME:
                    stop_requests(1)
                    raise ValueError('S04_MCP_FRAME_LIMIT')
                line = bytes(self.buffer[:index + 1])
                del self.buffer[:index + 1]
                return line.decode('utf-8', errors='replace')
            if len(self.buffer) > MAX_FRAME:
                stop_requests(1)
                raise ValueError('S04_MCP_FRAME_LIMIT')
            await anyio.wait_readable(self.descriptor)
            try:
                chunk = os.read(self.descriptor, 65536)
            except BlockingIOError:
                continue
            if not chunk:
                # EOF cancels outstanding tools before task-group drain.
                stop_requests(0)
                raise StopAsyncIteration
            self.buffer.extend(chunk)


class Output:
    def __init__(self, descriptor):
        self.descriptor = descriptor

    async def write(self, text):
        data = memoryview(text.encode('utf-8'))
        while data:
            await anyio.wait_writable(self.descriptor)
            try:
                count = os.write(self.descriptor, data[:65536])
            except BlockingIOError:
                continue
            data = data[count:]

    async def flush(self):
        pass


async def run_stdio(server):
    flags = {fd: os.get_blocking(fd) for fd in (0, 1)}
    try:
        for fd in flags:
            os.set_blocking(fd, False)
        async with stdio_server(Lines(0), Output(1)) as (read, write):
            # Same pinned SDK dispatch as MCPServer.run_stdio_async, with
            # explicit streams to avoid uncancelable thread-based pipe reads.
            lowlevel = server._lowlevel_server
            await lowlevel.run(read, write, lowlevel.create_initialization_options())
    finally:
        for fd, blocking in flags.items():
            os.set_blocking(fd, blocking)
