#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    rows: list[dict[str, object]] = []
    for path in sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()
        observed = path.lstat()
        mode = f"{stat.S_IMODE(observed.st_mode):04o}"
        if path.is_symlink():
            rows.append(
                {
                    "path": relative,
                    "type": "symlink",
                    "mode": mode,
                    "target": os.readlink(path),
                }
            )
        elif path.is_dir():
            rows.append({"path": relative, "type": "directory", "mode": mode})
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(
                {
                    "path": relative,
                    "type": "regular",
                    "mode": mode,
                    "size": observed.st_size,
                    "sha256": digest,
                }
            )
        else:
            rows.append({"path": relative, "type": "special", "mode": mode})

    canonical = "\n".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"))
        for row in rows
    ).encode("utf-8")
    result = {
        "schema_version": 1,
        "pass": all(row["type"] != "special" for row in rows),
        "entry_count": len(rows),
        "regular_count": sum(row["type"] == "regular" for row in rows),
        "directory_count": sum(row["type"] == "directory" for row in rows),
        "symlink_count": sum(row["type"] == "symlink" for row in rows),
        "special_paths": [
            row["path"] for row in rows if row["type"] == "special"
        ],
        "fingerprint": hashlib.sha256(canonical).hexdigest(),
        "root": str(root),
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
