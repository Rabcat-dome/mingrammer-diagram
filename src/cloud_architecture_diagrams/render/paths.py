"""Descriptor-anchored file access, so a swapped symbolic link cannot redirect a read or write."""

import os
import signal
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
INTERRUPTS = {signal.SIGTERM, signal.SIGINT, signal.SIGHUP}


@contextmanager
def signals_deferred() -> Iterator[None]:
    """Hold interrupts while a process starts or a cleanup runs, so neither stops halfway."""
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, INTERRUPTS)
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def open_directory(path: Path, *, create: bool = False) -> int:
    """Open a directory, refusing `..` and a symbolic link at every level."""
    descriptor = os.open(path.anchor, DIRECTORY)
    try:
        for component in path.parts[1:]:
            if component == "..":
                raise ValueError("relative traversal")
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(component, DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def read_regular(directory: int, name: str, limit: int) -> bytes:
    """Read one regular file; an oversize file raises OverflowError rather than truncating."""
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("not a regular file")
        if info.st_size > limit:
            raise OverflowError
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise OverflowError
    return data


def write_new(directory: int, name: str, data: bytes) -> None:
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
