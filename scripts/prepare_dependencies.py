#!/usr/bin/env python3
"""Verify the vendored, pinned dependency trees without network access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "dependencies" / "manifest.json").read_text())


def tree_hash(directory: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = sorted(path for path in directory.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(directory).as_posix().encode()
        data = path.read_bytes()
        digest.update(relative + b"\0" + str(len(data)).encode() + b"\0" + data)
    return digest.hexdigest(), len(files)


for name, expected in MANIFEST["dependencies"].items():
    directory = ROOT / "lib" / name
    if not directory.is_dir():
        raise RuntimeError(f"vendored dependency missing: {name}")
    if any(path.name in {".git", ".gitmodules"} for path in directory.rglob("*")):
        raise RuntimeError(f"Git metadata remains in vendored dependency: {name}")
    actual_hash, actual_files = tree_hash(directory)
    if actual_hash != expected["tree_sha256"] or actual_files != expected["files"]:
        raise RuntimeError(f"vendored dependency tree differs: {name}")

print("pinned vendored dependency sources verified")
