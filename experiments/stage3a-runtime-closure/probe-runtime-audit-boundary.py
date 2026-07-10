#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import ctypes
import importlib.metadata
import json
import locale
import mimetypes
import multiprocessing
import os
from pathlib import Path
import platform
import socket
import sqlite3
import ssl
import sys
import sysconfig
import tempfile
import urllib.request
import zoneinfo
from collections import Counter
from typing import Any


def write_tsv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def decode_path(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return os.fsdecode(value)
    return None


def classify_path(
    path: str,
    *,
    runtime_prefix: Path,
    termux_prefix: Path,
    results_dir: Path,
    home: Path,
) -> str:
    if not os.path.isabs(path):
        return "RELATIVE_PATH"

    normalized = os.path.normpath(path)

    def under(root: Path) -> bool:
        root_s = str(root)
        return normalized == root_s or normalized.startswith(root_s + "/")

    if under(runtime_prefix):
        return "RUNTIME_PREFIX"
    if under(results_dir):
        return "RESULT_OUTPUT"
    if under(termux_prefix):
        if normalized.startswith(str(termux_prefix / "tmp") + "/"):
            return "TERMUX_TEMP"
        return "TERMUX_PREFIX"
    if normalized == "/proc" or normalized.startswith("/proc/"):
        return "PROCFS"
    if normalized == "/dev" or normalized.startswith("/dev/"):
        return "DEVFS"
    if any(
        normalized == root or normalized.startswith(root + "/")
        for root in ["/system", "/apex", "/vendor", "/product", "/odm"]
    ):
        return "ANDROID_SYSTEM"
    if normalized == str(home) or normalized.startswith(str(home) + "/"):
        return "HOME_STATE"
    if normalized == "/tmp" or normalized.startswith("/tmp/"):
        return "SYSTEM_TEMP"
    return "OTHER_ABSOLUTE"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-prefix", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    runtime_prefix = args.runtime_prefix.resolve()
    termux_prefix = args.termux_prefix.resolve()
    output_dir = args.output_dir.resolve()
    home = Path.home().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    events: list[dict[str, Any]] = []
    collecting = True

    path_events = {
        "open": 0,
        "os.listdir": 0,
        "os.scandir": 0,
        "os.chdir": 0,
    }

    def audit_hook(event: str, event_args: tuple[Any, ...]) -> None:
        nonlocal collecting
        if not collecting:
            return

        if event in path_events:
            index = path_events[event]
            if len(event_args) <= index:
                return
            path = decode_path(event_args[index])
            if path is None:
                return
            events.append(
                {
                    "event": event,
                    "subject": path,
                    "kind": "path",
                }
            )
            return

        if event == "subprocess.Popen":
            subject = repr(event_args[:2])
            events.append(
                {
                    "event": event,
                    "subject": subject,
                    "kind": "subprocess",
                }
            )
            return

        if event == "ctypes.dlopen":
            subject = repr(event_args[0] if event_args else None)
            events.append(
                {
                    "event": event,
                    "subject": subject,
                    "kind": "dlopen",
                }
            )
            return

        if event == "socket.connect":
            subject = repr(event_args[1] if len(event_args) > 1 else event_args)
            events.append(
                {
                    "event": event,
                    "subject": subject,
                    "kind": "network",
                }
            )

    sys.addaudithook(audit_hook)

    workload: dict[str, dict[str, Any]] = {}

    def run(name: str, func: Any) -> None:
        try:
            value = func()
        except Exception as exc:  # noqa: BLE001
            workload[name] = {
                "result": "FAIL",
                "error": repr(exc),
            }
        else:
            workload[name] = {
                "result": "PASS",
                "value": repr(value),
            }

    run("ssl_default_verify_paths", lambda: ssl.get_default_verify_paths()._asdict())
    run("https_pypi", lambda: urllib.request.urlopen("https://pypi.org/simple/", timeout=20).status)
    run("mimetypes_init", lambda: (mimetypes.init(), mimetypes.guess_type("x.json"))[1])
    run("locale_setlocale", lambda: locale.setlocale(locale.LC_CTYPE, ""))
    run("locale_preferred_encoding", lambda: locale.getpreferredencoding(False))
    run("tempdir", tempfile.gettempdir)
    run("sqlite_memory", lambda: sqlite3.connect(":memory:").execute("select 1").fetchone())
    run("ctypes_libc", lambda: ctypes.CDLL("libc.so")._name)
    run("multiprocessing_methods", multiprocessing.get_all_start_methods)
    run("platform", platform.platform)
    run("sysconfig_paths", sysconfig.get_paths)
    run("metadata_distribution_count", lambda: sum(1 for _ in importlib.metadata.distributions()))
    run("zoneinfo_UTC", lambda: repr(zoneinfo.ZoneInfo("UTC")))

    collecting = False

    path_rows: list[list[str]] = []
    special_rows: list[list[str]] = []
    class_counts: Counter[str] = Counter()
    unique_paths: dict[str, set[str]] = {}

    for item in events:
        if item["kind"] == "path":
            subject = str(item["subject"])
            classification = classify_path(
                subject,
                runtime_prefix=runtime_prefix,
                termux_prefix=termux_prefix,
                results_dir=output_dir,
                home=home,
            )
            class_counts[classification] += 1
            unique_paths.setdefault(classification, set()).add(subject)
            path_rows.append(
                [
                    str(item["event"]),
                    subject,
                    classification,
                    "yes" if os.path.exists(subject) else "no",
                ]
            )
        else:
            special_rows.append(
                [
                    str(item["event"]),
                    str(item["kind"]),
                    str(item["subject"]),
                ]
            )

    path_rows.sort(key=lambda row: (row[2], row[1], row[0]))
    special_rows.sort(key=lambda row: (row[1], row[0], row[2]))

    write_tsv(
        output_dir / "runtime-audit-path-events.tsv",
        ["event", "path", "classification", "exists_after_workload"],
        path_rows,
    )

    write_tsv(
        output_dir / "runtime-audit-special-events.tsv",
        ["event", "kind", "subject"],
        special_rows,
    )

    unique_rows: list[list[str]] = []
    for classification, paths in sorted(unique_paths.items()):
        for path in sorted(paths):
            unique_rows.append(
                [
                    classification,
                    path,
                    "yes" if os.path.exists(path) else "no",
                ]
            )

    write_tsv(
        output_dir / "runtime-audit-unique-paths.tsv",
        ["classification", "path", "exists_after_workload"],
        unique_rows,
    )

    summary = {
        "runtime_prefix": str(runtime_prefix),
        "termux_prefix": str(termux_prefix),
        "home": str(home),
        "workload": workload,
        "path_event_count": len(path_rows),
        "special_event_count": len(special_rows),
        "path_classification_record_counts": dict(sorted(class_counts.items())),
        "path_classification_unique_counts": {
            classification: len(paths)
            for classification, paths in sorted(unique_paths.items())
        },
    }

    with (output_dir / "runtime-audit-boundary-summary.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
