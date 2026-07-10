#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess


def run_scenario(
    python_bin: Path,
    env_overrides: dict[str, str | None],
) -> dict[str, object]:
    env = os.environ.copy()
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value

    code = r'''
import json
import os
import ssl
import urllib.request

result = {
    "ssl_cert_file_env": os.environ.get("SSL_CERT_FILE"),
    "ssl_cert_dir_env": os.environ.get("SSL_CERT_DIR"),
    "default_verify_paths": ssl.get_default_verify_paths()._asdict(),
}

try:
    with urllib.request.urlopen("https://pypi.org/simple/", timeout=20) as response:
        result["https_status"] = response.status
        result["https_result"] = "PASS"
except Exception as exc:
    result["https_result"] = "FAIL"
    result["https_error"] = repr(exc)

print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["https_result"] == "PASS" else 4)
'''

    proc = subprocess.run(
        [str(python_bin), "-I", "-S", "-c", code],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    parsed: dict[str, object] | None = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "parsed": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-bin", required=True, type=Path)
    parser.add_argument("--termux-prefix", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    python_bin = args.python_bin.resolve()
    termux_prefix = args.termux_prefix.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    termux_ca = termux_prefix / "etc" / "tls" / "cert.pem"
    missing_ca = output_dir / "missing-ca.pem"
    empty_ca = output_dir / "empty-ca.pem"
    if missing_ca.exists():
        missing_ca.unlink()
    empty_ca.write_bytes(b"")

    scenarios = {
        "clean_default": run_scenario(
            python_bin,
            {
                "SSL_CERT_FILE": None,
                "SSL_CERT_DIR": None,
            },
        ),
        "explicit_termux_ca": run_scenario(
            python_bin,
            {
                "SSL_CERT_FILE": str(termux_ca),
                "SSL_CERT_DIR": None,
            },
        ),
        "missing_file_repair": run_scenario(
            python_bin,
            {
                "SSL_CERT_FILE": str(missing_ca),
                "SSL_CERT_DIR": None,
            },
        ),
        "existing_empty_file": run_scenario(
            python_bin,
            {
                "SSL_CERT_FILE": str(empty_ca),
                "SSL_CERT_DIR": None,
            },
        ),
    }

    summary = {
        "termux_ca_path": str(termux_ca),
        "termux_ca_exists": termux_ca.is_file(),
        "empty_ca_path": str(empty_ca),
        "scenarios": scenarios,
    }

    with (output_dir / "ca-boundary-probe.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
