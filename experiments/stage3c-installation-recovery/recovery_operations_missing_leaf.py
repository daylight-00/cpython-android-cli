#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import recovery_operations as frozen
from recovery_common import actual_kind

uninstall = frozen.uninstall


def install(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Run the frozen installer with a narrow missing-leaf repair correction.

    A registered non-directory that is absent is still planned as ``repair`` by
    the frozen planner.  Before the frozen executor records that repair as a
    ``replaced`` mutation, rewrite only that absent-path intent to ``created``
    and skip the immediately following backup move.  Existing mismatches retain
    the original ``replaced`` semantics.
    """

    original_add_intent = frozen.add_intent
    original_durable_move = frozen.durable_move
    missing_sources: set[str] = set()

    def corrected_add_intent(
        transaction: Path,
        journal: dict[str, Any],
        record: dict[str, Any],
        crash: Any,
    ) -> int:
        if record.get("kind") == "replaced" and isinstance(record.get("path"), str):
            root = transaction.parents[2]
            path = root / "prefix" / record["path"]
            if actual_kind(path) == "absent":
                missing_sources.add(str(path))
                return original_add_intent(
                    transaction,
                    journal,
                    {"kind": "created", "path": record["path"]},
                    crash,
                )
        return original_add_intent(transaction, journal, record, crash)

    def corrected_durable_move(source: Path, destination: Path, *, label: str) -> None:
        source_text = str(source)
        if label == "install-leaf-backup" and source_text in missing_sources:
            if actual_kind(source) != "absent":
                raise RuntimeError(f"missing-leaf repair source unexpectedly appeared: {source}")
            missing_sources.remove(source_text)
            return
        original_durable_move(source, destination, label=label)

    frozen.add_intent = corrected_add_intent
    frozen.durable_move = corrected_durable_move
    try:
        return frozen.install(*args, **kwargs)
    finally:
        frozen.add_intent = original_add_intent
        frozen.durable_move = original_durable_move
