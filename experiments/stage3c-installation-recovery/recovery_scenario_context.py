from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from recovery_scenario_support import canonical_json_bytes, read_json


class ScenarioContext:
    def __init__(self, gate2: Path, engine: Path, work: Path, output: Path):
        self.gate2 = gate2
        self.contract = gate2 / "input/contract"
        self.engine = engine
        self.work = work
        self.output = output
        self.checks: dict[str, bool] = {}
        self.sequence = 0

    def check(self, name: str, value: bool) -> None:
        self.checks[name] = bool(value)

    def save(self, name: str, value: dict[str, Any]) -> dict[str, Any]:
        self.sequence += 1
        path = self.output / f"{self.sequence:02d}-{name}.json"
        path.write_bytes(canonical_json_bytes(value))
        return value

    def run_engine(
        self,
        name: str,
        root: Path,
        operation: str,
        *,
        artifact: str | None = None,
        extra: list[str] | None = None,
        expect_rc: int | None = 0,
    ) -> tuple[dict[str, Any], subprocess.CompletedProcess[str]]:
        self.sequence += 1
        result_path = self.output / f"{self.sequence:02d}-{name}.json"
        command = [
            sys.executable,
            str(self.engine),
            "--installation-root",
            str(root),
            "--operation",
            operation,
            "--output",
            str(result_path),
        ]
        if operation in {"install", "uninstall"}:
            command.extend(["--contract-results", str(self.contract)])
            crash_requested = bool(extra) and any(item.startswith("--crash-") for item in extra)
            if not crash_requested:
                command.append("--fast-success")
        if artifact is not None:
            command.extend(["--artifact", artifact])
        if extra:
            command.extend(extra)
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result_path.exists():
            result = read_json(result_path)
        else:
            result = {
                "operation": operation,
                "artifact": artifact,
                "process_exit": completed.returncode,
                "output_absent": True,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            result_path.write_bytes(canonical_json_bytes(result))
        if expect_rc is not None:
            result["expected_returncode_match"] = completed.returncode == expect_rc
            result_path.write_bytes(canonical_json_bytes(result))
        return result, completed
