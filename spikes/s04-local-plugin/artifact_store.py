"""POSIX artifact directories anchored to file descriptors, without symlink traversal."""
import hashlib
import json
import os
from pathlib import Path
import re
import stat

FILES = {"diagram.png", "diagram.svg", "source.dot", "source.json", "manifest.json"}
MAX_FILE = 16 * 1024 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def directory_fd(path, create=False):
    path = Path(path).absolute()
    descriptor = os.open(path.anchor, DIRECTORY_FLAGS)
    try:
        for component in path.parts[1:]:
            if component in (".", ".."):
                raise ValueError("S04_UNSAFE_DIRECTORY")
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(component, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


class ArtifactStore:
    def __init__(self, root):
        self.root = Path(root).absolute()
        self.fd = directory_fd(self.root, create=True)
        info = os.fstat(self.fd)
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            self.close()
            raise ValueError("S04_OUTPUT_ROOT_MUST_BE_PRIVATE_AND_OWNED")

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def check_root(self):
        other = directory_fd(self.root)
        try:
            current, original = os.fstat(other), os.fstat(self.fd)
            if (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino):
                raise ValueError("S04_OUTPUT_ROOT_CHANGED")
        finally:
            os.close(other)

    def publish(self, identifier, source, report):
        if not re.fullmatch(r"[a-f0-9]{32}", identifier):
            raise ValueError("S04_INVALID_ARTIFACT")
        self.check_root()
        stage = "." + identifier + ".part"
        os.mkdir(stage, mode=0o700, dir_fd=self.fd)
        stage_fd = os.open(stage, DIRECTORY_FLAGS, dir_fd=self.fd)
        published = False
        try:
            for name in sorted(FILES - {"manifest.json"}):
                data = (source / name).read_bytes()
                expected = report["files"][name]
                if len(data) > MAX_FILE or len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
                    raise ValueError("S04_ARTIFACT_INTEGRITY")
                self._write(stage_fd, name, data)
            self._write(stage_fd, "manifest.json", (json.dumps(report, indent=2) + "\n").encode())
            self.check_root()
            try:
                os.stat(identifier, dir_fd=self.fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("S04_BUNDLE_COLLISION")
            os.rename(stage, identifier, src_dir_fd=self.fd, dst_dir_fd=self.fd)
            published = True
        finally:
            if not published:
                for name in os.listdir(stage_fd):
                    os.unlink(name, dir_fd=stage_fd)
            os.close(stage_fd)
            if not published:
                os.rmdir(stage, dir_fd=self.fd)

    @staticmethod
    def _write(descriptor, name, data):
        if len(data) > MAX_FILE:
            raise ValueError("S04_ARTIFACT_LIMIT")
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=descriptor)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)

    def read(self, identifier, name):
        if not re.fullmatch(r"[a-f0-9]{32}", identifier) or name not in FILES:
            raise ValueError("S04_INVALID_ARTIFACT")
        self.check_root()
        folder = os.open(identifier, DIRECTORY_FLAGS, dir_fd=self.fd)
        try:
            descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=folder)
            with os.fdopen(descriptor, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
                    raise ValueError("S04_ARTIFACT_LIMIT")
                data = stream.read(MAX_FILE + 1)
                if len(data) > MAX_FILE:
                    raise ValueError("S04_ARTIFACT_LIMIT")
                return data
        finally:
            os.close(folder)
