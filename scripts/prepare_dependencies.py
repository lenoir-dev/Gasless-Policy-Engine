
#!/usr/bin/env python3
"""Verify pinned vendored dependencies against committed source files."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads(
    (ROOT / "dependencies" / "manifest.json").read_text()
)


def git_files(directory: Path, *options: str) -> list[Path]:
    relative_dir = directory.relative_to(ROOT).as_posix()

    output = subprocess.check_output(
        ["git", "ls-files", "-z", *options, "--", relative_dir],
        cwd=ROOT,
    )

    return sorted(
        ROOT / os.fsdecode(name)
        for name in output.split(b"\0")
        if name
    )


def tree_hash(directory: Path) -> tuple[str, int]:
    digest = hashlib.sha256()

    # Hash only committed source files, not generated build outputs.
    files = git_files(directory, "--cached")

    if not files:
        raise RuntimeError(
            f"no tracked dependency files: {directory.name}"
        )

    for path in files:
        if not path.is_file():
            raise RuntimeError(
                f"tracked dependency file missing: "
                f"{path.relative_to(ROOT)}"
            )

        relative = path.relative_to(directory).as_posix().encode()
        data = path.read_bytes()

        digest.update(
            relative
            + b"\0"
            + str(len(data)).encode()
            + b"\0"
            + data
        )

    return digest.hexdigest(), len(files)


for name, expected in MANIFEST["dependencies"].items():
    directory = ROOT / "lib" / name

    if not directory.is_dir():
        raise RuntimeError(
            f"vendored dependency missing: {name}"
        )

    # Nested Git metadata is not allowed in vendored dependencies.
    if any(
        path.name in {".git", ".gitmodules"}
        for path in directory.rglob("*")
    ):
        raise RuntimeError(
            f"Git metadata remains in vendored dependency: {name}"
        )

    # Reject unexpected source files, but respect .gitignore
    # for legitimate generated outputs such as node_modules.
    unexpected = git_files(
        directory, "--others", "--exclude-standard"
    )

    if unexpected:
        names = [
            str(path.relative_to(ROOT))
            for path in unexpected[:10]
        ]
        raise RuntimeError(
            f"unexpected untracked dependency files in {name}: "
            + ", ".join(names)
        )

    actual_hash, actual_files = tree_hash(directory)

    if (
        actual_hash != expected["tree_sha256"]
        or actual_files != expected["files"]
    ):
        raise RuntimeError(
            f"vendored dependency tree differs: {name}; "
            f"expected {expected['files']} files, "
            f"got {actual_files}"
        )

    print(
        f"{name}: verified {actual_files} committed files",
        flush=True,
    )

print("pinned vendored dependency sources verified")
