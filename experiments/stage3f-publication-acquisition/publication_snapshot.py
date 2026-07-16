#!/usr/bin/env python3
"""Canonical Stage 3-F publication snapshot and candidate-observation checks."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SNAPSHOT_FORMAT = "hw-t-publication-snapshot-v1"
SCHEMA_VERSION = 1
STAGE3E_EVIDENCE_ARCHIVE_SHA256 = "3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2"
STAGE3E_GATE2_AUTHORITY_PATH = "experiments/stage3e-managed-python-distribution/gate2-isolated-dual-version-census-authority.json"
STAGE3E_GATE2_AUTHORITY_BLOB = "4d631ee6e2a4814e5936279c0a9f86b144473013"

FROZEN_ROWS: dict[str, dict[str, Any]] = {
    "cpython-3.14.5-linux-aarch64-none": {
        "version": "3.14.5",
        "artifact": {
            "size": 9761522,
            "sha256": "18832bb7982a679fcee067e2d33e106dac84307687b63803be105714596d422f",
        },
        "platform": {
            "implementation": "cpython",
            "os": "android",
            "arch": "aarch64",
            "catalog_platform": "linux-aarch64-none",
            "android_api": 24,
            "multiarch": "aarch64-linux-android",
            "soabi": "cpython-314-aarch64-linux-android",
        },
        "provenance": {
            "authority_path": STAGE3E_GATE2_AUTHORITY_PATH,
            "authority_blob": STAGE3E_GATE2_AUTHORITY_BLOB,
            "evidence_archive_sha256": STAGE3E_EVIDENCE_ARCHIVE_SHA256,
            "evidence_member": "research/derived-145.json",
            "evidence_member_sha256": "7b5d545a52965c965da8f50ba917e764b7dcc08c4a0277320a0827117618992c",
        },
    },
    "cpython-3.14.6-linux-aarch64-none": {
        "version": "3.14.6",
        "artifact": {
            "size": 11789074,
            "sha256": "9575edef24d84b2fce32c55093ab01cb8b2b1a41b521d2011653fae87b5bcb64",
        },
        "platform": {
            "implementation": "cpython",
            "os": "android",
            "arch": "aarch64",
            "catalog_platform": "linux-aarch64-none",
            "android_api": 24,
            "multiarch": "aarch64-linux-android",
            "soabi": "cpython-314-aarch64-linux-android",
        },
        "provenance": {
            "authority_path": STAGE3E_GATE2_AUTHORITY_PATH,
            "authority_blob": STAGE3E_GATE2_AUTHORITY_BLOB,
            "evidence_archive_sha256": STAGE3E_EVIDENCE_ARCHIVE_SHA256,
            "evidence_member": "research/derived-146.json",
            "evidence_member_sha256": "20e5ab521148a6a0bf1536a70f1c5b55eec8b3244343bf87e2b53f1d3d76b9e0",
        },
    },
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_snapshot_body() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for key in sorted(FROZEN_ROWS):
        frozen = copy.deepcopy(FROZEN_ROWS[key])
        digest = frozen["artifact"]["sha256"]
        rows.append(
            {
                "key": key,
                "version": frozen["version"],
                "platform": frozen["platform"],
                "artifact": frozen["artifact"],
                "locators": [
                    {
                        "kind": "snapshot-relative-content-addressed",
                        "value": f"artifacts/sha256/{digest}",
                    }
                ],
                "provenance": frozen["provenance"],
            }
        )
    return {
        "format": SNAPSHOT_FORMAT,
        "frozen_inputs": {
            "stage3e_freeze_commit": "6419e107e4aa8400ebd3d98f3583999075b8b935",
            "stage3e_freeze_tree": "e16edd99bfadf2135d0b632ddef4d292c0d80ea6",
            "stage3e_gate2_evidence_archive_sha256": STAGE3E_EVIDENCE_ARCHIVE_SHA256,
        },
        "rows": rows,
    }


def build_snapshot_document() -> dict[str, Any]:
    body = build_snapshot_body()
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot": body,
        "snapshot_sha256": sha256_bytes(canonical_bytes(body)),
    }


def _error(code: str, detail: str | None = None) -> dict[str, str]:
    v = {"code": code}
    if detail is not None:
        v["detail"] = detail
    return v


def verify_snapshot_document(document: Any) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not isinstance(document, dict):
        return {"pass": False, "errors": [_error("document-not-object")]}
    if set(document) != {"schema_version", "snapshot", "snapshot_sha256"}:
        errors.append(_error("document-fields"))
    if document.get("schema_version") != SCHEMA_VERSION:
        errors.append(_error("schema-version"))
    body = document.get("snapshot")
    supplied_digest = document.get("snapshot_sha256")
    if not isinstance(body, dict):
        errors.append(_error("snapshot-not-object"))
        body = {}
    if not isinstance(supplied_digest, str) or not _SHA256_RE.fullmatch(supplied_digest):
        errors.append(_error("snapshot-digest-missing-or-invalid"))
    else:
        actual_digest = sha256_bytes(canonical_bytes(body))
        if supplied_digest != actual_digest:
            errors.append(_error("snapshot-digest-mismatch"))
    if set(body) != {"format", "frozen_inputs", "rows"}:
        errors.append(_error("snapshot-fields"))
    if body.get("format") != SNAPSHOT_FORMAT:
        errors.append(_error("snapshot-format"))
    frozen_inputs = body.get("frozen_inputs")
    expected_inputs = build_snapshot_body()["frozen_inputs"]
    if frozen_inputs != expected_inputs:
        errors.append(_error("frozen-inputs"))
    rows = body.get("rows")
    if not isinstance(rows, list):
        errors.append(_error("rows-not-list"))
        rows = []
    keys = [row.get("key") for row in rows if isinstance(row, dict)]
    if len(keys) != len(rows):
        errors.append(_error("row-not-object"))
    if len(keys) != len(set(keys)):
        errors.append(_error("duplicate-key"))
    if keys != sorted(keys):
        errors.append(_error("row-order"))
    if keys != sorted(FROZEN_ROWS):
        errors.append(_error("exact-row-set"))
    expected_by_key = {row["key"]: row for row in build_snapshot_body()["rows"]}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        key = row.get("key")
        if set(row) != {"key", "version", "platform", "artifact", "locators", "provenance"}:
            errors.append(_error("row-fields", str(key or index)))
        artifact = row.get("artifact")
        if not isinstance(artifact, dict) or set(artifact) != {"size", "sha256"}:
            errors.append(_error("artifact-identity-missing", str(key or index)))
        else:
            if not isinstance(artifact.get("size"), int) or artifact["size"] <= 0:
                errors.append(_error("artifact-size", str(key or index)))
            if not isinstance(artifact.get("sha256"), str) or not _SHA256_RE.fullmatch(artifact["sha256"]):
                errors.append(_error("artifact-sha256", str(key or index)))
        locators = row.get("locators")
        if not isinstance(locators, list) or not locators:
            errors.append(_error("locator-list", str(key or index)))
        else:
            for locator in locators:
                if not isinstance(locator, dict) or set(locator) != {"kind", "value"}:
                    errors.append(_error("locator-shape", str(key or index)))
                    continue
                if any(field in locator for field in ("size", "sha256", "identity")):
                    errors.append(_error("locator-used-as-identity", str(key or index)))
        expected = expected_by_key.get(key)
        if expected is not None and row != expected:
            errors.append(_error("exact-key-redefined", str(key)))
    codes = [e["code"] for e in errors]
    return {
        "pass": not errors,
        "error_count": len(errors),
        "error_codes": codes,
        "errors": errors,
        "snapshot_sha256": supplied_digest if isinstance(supplied_digest, str) else None,
        "row_count": len(rows),
        "keys": keys,
    }


def verify_candidate_observation(
    document: Any,
    *,
    key: str,
    observed_size: int,
    observed_sha256: str,
    bound_snapshot_sha256: str,
) -> dict[str, Any]:
    snapshot_result = verify_snapshot_document(document)
    errors: list[str] = []
    if not snapshot_result["pass"]:
        errors.append("snapshot-invalid")
    if not isinstance(document, dict) or document.get("snapshot_sha256") != bound_snapshot_sha256:
        errors.append("snapshot-binding-mismatch")
    rows = {}
    if isinstance(document, dict) and isinstance(document.get("snapshot"), dict):
        raw_rows = document["snapshot"].get("rows", [])
        if isinstance(raw_rows, list):
            rows = {row.get("key"): row for row in raw_rows if isinstance(row, dict)}
    row = rows.get(key)
    if not isinstance(row, dict):
        errors.append("key-missing")
        artifact: dict[str, Any] = {}
    else:
        artifact = row.get("artifact") if isinstance(row.get("artifact"), dict) else {}
    if observed_size != artifact.get("size"):
        errors.append("candidate-size-mismatch")
    if observed_sha256 != artifact.get("sha256"):
        errors.append("candidate-sha256-mismatch")
    promotable = not errors
    return {
        "promotable": promotable,
        "errors": errors,
        "verified_cache_key": artifact.get("sha256") if promotable else None,
        "installation_permitted": False,
        "claim_boundary": "Gate 2 models candidate observation checks only; it performs no transport, cache mutation, or installation.",
    }


def load_document(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("snapshot document must be an object")
    return value
