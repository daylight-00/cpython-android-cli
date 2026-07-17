#!/usr/bin/env python3
"""Run an exact upstream Python script while forcing shell=True through Termux bash.

Only subprocess.run calls with shell=True and no explicit executable are adapted.
All non-shell subprocess calls and the upstream source file remain unchanged.
"""
from __future__ import annotations

import os
import pathlib
import runpy
import subprocess
import sys


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: android-shell-adapter.py /path/to/android.py [args...]")
    script = pathlib.Path(sys.argv[1]).resolve()
    shell = pathlib.Path(os.environ.get("A3_ANDROID_SHELL", "/data/data/com.termux/files/usr/bin/bash")).resolve()
    if not script.is_file():
        raise SystemExit(f"upstream script missing: {script}")
    if not shell.is_file() or not os.access(shell, os.X_OK):
        raise SystemExit(f"adapted shell missing or not executable: {shell}")

    real_run = subprocess.run

    def adapted_run(*popenargs, **kwargs):
        if kwargs.get("shell") is True and kwargs.get("executable") is None:
            kwargs["executable"] = str(shell)
        return real_run(*popenargs, **kwargs)

    subprocess.run = adapted_run
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
