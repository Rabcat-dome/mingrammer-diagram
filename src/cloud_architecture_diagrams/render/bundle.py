"""The output root and atomic bundle publication (NFR-003, NFR-010)."""

import fcntl
import hashlib
import os
import secrets
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .errors import RenderFailure
from .paths import DIRECTORY, open_directory, read_regular, signals_deferred, write_new

UNSAFE = "RENDER_OUTPUT_PATH_UNSAFE"


def _canonical(descriptor: int, fallback: str) -> str:
    # The sandbox compares real paths, and macOS accepts other spellings of a real directory.
    command = getattr(fcntl, "F_GETPATH", None)
    if command is None:
        return fallback
    return os.fsdecode(fcntl.fcntl(descriptor, command, bytes(1024)).split(b"\0", 1)[0])


class OutputRoot:
    """A real directory owned by this user that others cannot write to, held by descriptor."""

    def __init__(self, path: str) -> None:
        # absolute() keeps `..`, which open_directory then refuses instead of resolving lexically.
        self.path = Path(path).absolute()
        self.fd = -1
        try:
            self.fd = open_directory(self.path, create=True)
            info = os.fstat(self.fd)
        except (OSError, ValueError) as error:
            self.close()
            raise RenderFailure(UNSAFE, "/output") from error
        if info.st_uid != os.getuid() or info.st_mode & 0o022:
            self.close()
            raise RenderFailure(UNSAFE, "/output")
        self.identity = (info.st_dev, info.st_ino)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> "OutputRoot":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def check_unchanged(self) -> None:
        try:
            other = open_directory(self.path)
        except (OSError, ValueError) as error:
            raise RenderFailure("RENDER_OUTPUT_ROOT_CHANGED", "/output") from error
        try:
            info = os.fstat(other)
        finally:
            os.close(other)
        if (info.st_dev, info.st_ino) != self.identity:
            raise RenderFailure("RENDER_OUTPUT_ROOT_CHANGED", "/output")

    @contextmanager
    def request(self) -> Iterator[tuple[int, str]]:
        """A private scratch directory that is always removed, whatever ends the render."""
        name = f".request-{secrets.token_hex(16)}"
        descriptor = -1
        try:
            os.mkdir(name, mode=0o700, dir_fd=self.fd)
            descriptor = os.open(name, DIRECTORY, dir_fd=self.fd)
            yield descriptor, _canonical(descriptor, str(self.path / name))
        except OSError as error:
            raise RenderFailure("RENDER_OUTPUT_WRITE_FAILED", "/output") from error
        finally:
            with signals_deferred():
                if descriptor >= 0:
                    os.close(descriptor)
                shutil.rmtree(name, dir_fd=self.fd, ignore_errors=True)

    def publish(self, name: str, files: dict[str, bytes]) -> Path:
        """Readers see a complete bundle or none: the rename comes after every file checks out."""
        self.check_unchanged()
        stage = f".{name}.part"
        descriptor = -1
        published = False
        try:
            os.mkdir(stage, mode=0o700, dir_fd=self.fd)
            descriptor = os.open(stage, DIRECTORY, dir_fd=self.fd)
            for filename, data in files.items():
                write_new(descriptor, filename, data)
            for filename, data in files.items():
                stored = read_regular(descriptor, filename, len(data))
                if hashlib.sha256(stored).digest() != hashlib.sha256(data).digest():
                    raise RenderFailure("RENDER_CONTENT_MISSING", "/bundle")
            os.fsync(descriptor)
            self.check_unchanged()
            try:
                os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise RenderFailure("RENDER_BUNDLE_COLLISION", "/bundle")
            os.rename(stage, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
            # Until the rename is durable a failure must still take the bundle away, because the
            # caller hears that nothing was published, and a retry would otherwise collide.
            stage = name
            os.fsync(self.fd)
            published = True
        except (OSError, OverflowError, ValueError) as error:
            raise RenderFailure("RENDER_OUTPUT_WRITE_FAILED", "/output") from error
        finally:
            with signals_deferred():
                if descriptor >= 0:
                    os.close(descriptor)
                if not published:
                    shutil.rmtree(stage, dir_fd=self.fd, ignore_errors=True)
        return self.path / name
