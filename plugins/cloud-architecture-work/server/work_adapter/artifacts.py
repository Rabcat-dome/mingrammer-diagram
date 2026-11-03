"""Scoped access to published bundles: fixed names, no symbolic links, descriptors throughout."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEDIA_TYPES = {
    "diagram.png": "image/png",
    "diagram.svg": "image/svg+xml",
    "model.json": "application/json",
    "view.json": "application/json",
    "diagnostics.json": "application/json",
    "manifest.json": "application/json",
}
# The core names a bundle `<metadata id>--<view id>--<16 hex>`, and its IDs cannot start with a dot.
BUNDLE = re.compile(r"[a-z][a-z0-9._-]{0,63}--[a-z][a-z0-9._-]{0,63}--[0-9a-f]{16}")
SCRATCH = re.compile(r"\.(request-[0-9a-f]{32}|[a-z][a-z0-9._-]*--[0-9a-f]{16}\.part)")
DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
# The core's own limit on one file. Anything larger is not something the core published.
MAX_FILE = 16 * 1024 * 1024
MAX_MANIFEST = 1024 * 1024
MAX_LISTED = 100


class ArtifactError(Exception):
    """`code` is a stable name; the message stays with the caller, so nothing here leaks a path."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def open_root(path: Path) -> int:
    """Open the root without following a symbolic link at any level."""
    descriptor = os.open(path.anchor, DIRECTORY)
    try:
        for component in path.parts[1:]:
            child = os.open(component, DIRECTORY, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _read(directory: int, name: str, limit: int) -> bytes:
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ArtifactError("ARTIFACT_UNSAFE")
        if info.st_size > limit:
            raise ArtifactError("ARTIFACT_TOO_LARGE")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ArtifactError("ARTIFACT_TOO_LARGE")
    return data


def read_file(root: Path, bundle_id: str, name: str, limit: int = MAX_FILE) -> bytes:
    if not BUNDLE.fullmatch(bundle_id) or name not in MEDIA_TYPES:
        raise ArtifactError("ARTIFACT_NAME_REFUSED")
    try:
        directory = open_root(root)
        try:
            bundle = os.open(bundle_id, DIRECTORY, dir_fd=directory)
            try:
                return _read(bundle, name, limit)
            finally:
                os.close(bundle)
        finally:
            os.close(directory)
    except FileNotFoundError as error:
        raise ArtifactError("ARTIFACT_NOT_FOUND") from error
    except OSError as error:
        raise ArtifactError("ARTIFACT_UNSAFE") from error


def verify_published(root: Path, bundle_id: str, artifacts: list[dict[str, Any]]) -> None:
    """FR-043: a bundle counts only if every file the core listed reads back as it reported."""
    if {item.get("name") for item in artifacts} != set(MEDIA_TYPES):
        raise ArtifactError("ARTIFACT_INCOMPLETE")
    for item in artifacts:
        data = read_file(root, bundle_id, str(item["name"]))
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ArtifactError("ARTIFACT_INTEGRITY")


def _names(directory: int) -> list[str]:
    return [name for name in os.listdir(directory) if BUNDLE.fullmatch(name)]


def count_bundles(root: Path) -> int:
    try:
        directory = open_root(root)
    except OSError:
        return 0
    try:
        return len(_names(directory))
    finally:
        os.close(directory)


def _summary(directory: int, name: str, modified: float) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "bundle_id": name,
        "created": datetime.fromtimestamp(modified, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        bundle = os.open(name, DIRECTORY, dir_fd=directory)
        try:
            manifest = json.loads(_read(bundle, "manifest.json", MAX_MANIFEST))
        finally:
            os.close(bundle)
        view = manifest.get("view", {})
        entry.update(
            view_id=view.get("id"),
            view_title=view.get("title"),
            draft=manifest.get("validation", {}).get("draft"),
            private_use_only=manifest.get("rights", {}).get("private_use_only"),
        )
    except (ArtifactError, OSError, ValueError, AttributeError):
        entry["manifest_readable"] = False
    return entry


def _open_for_listing(root: Path) -> int | None:
    """None when there is nothing yet; a root that cannot be used must not read as empty."""
    try:
        return open_root(root)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise ArtifactError("ARTIFACT_UNSAFE") from error


def list_bundles(root: Path, limit: int) -> list[dict[str, Any]]:
    """Newest first. A listing reads only each bundle's manifest, and never a model."""
    directory = _open_for_listing(root)
    if directory is None:
        return []
    try:
        found = []
        for name in _names(directory):
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                found.append((info.st_mtime, name))
        found.sort(reverse=True)
        return [_summary(directory, name, modified) for modified, name in found[:limit]]
    finally:
        os.close(directory)


def _remove_tree(parent: int, name: str) -> None:
    """By descriptor, so a link cannot redirect it. shutil.rmtree takes dir_fd only from 3.11."""
    folder = os.open(name, DIRECTORY, dir_fd=parent)
    try:
        for entry in os.listdir(folder):
            info = os.stat(entry, dir_fd=folder, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                _remove_tree(folder, entry)
            else:
                os.unlink(entry, dir_fd=folder)
    finally:
        os.close(folder)
    os.rmdir(name, dir_fd=parent)


def prune(root: Path, older_than_days: float, *, apply: bool) -> dict[str, Any]:
    """Remove old bundles on request. A model has no tool for this, so only the owner can do it."""
    cutoff = time.time() - older_than_days * 86400
    directory = _open_for_listing(root)
    if directory is None:
        return {"removed": [], "applied": apply}
    try:
        selected = []
        for name in os.listdir(directory):
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            # A killed render can leave scratch behind, which is safe to remove once it is an hour old.
            limit = time.time() - 3600 if SCRATCH.fullmatch(name) else cutoff
            eligible = BUNDLE.fullmatch(name) or SCRATCH.fullmatch(name)
            if eligible and stat.S_ISDIR(info.st_mode) and info.st_mtime < limit:
                selected.append(name)
        if apply:
            for name in selected:
                _remove_tree(directory, name)
        return {"removed": sorted(selected), "applied": apply}
    finally:
        os.close(directory)
