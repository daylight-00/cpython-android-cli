#!/usr/bin/env python3
"""Verify Gate 3 loopback transport, fail-closed acquisition, and cache promotion."""
from __future__ import annotations

import sys
sys.dont_write_bytecode = True

import copy
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from loopback_acquisition import (
    AcquisitionError,
    CacheConflictError,
    LoopbackFixtureServer,
    PolicyError,
    Route,
    TransportError,
    VerificationError,
    acquire_to_verified_cache,
    content_addressed_path,
    fetch_and_verify_snapshot,
    sha256_bytes,
)

ROOT = Path(__file__).resolve().parent
SNAPSHOT_PATH = ROOT / "gate2-publication-snapshot.json"
SNAPSHOT_FILE_SHA256 = "c942b9863e33c2edf7d628780bfeef0957b427fb12259ba49e708cb4858c52bc"
SNAPSHOT_BODY_SHA256 = "a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c"
SNAPSHOT_FILE_SIZE = 2328

PAYLOAD_A = (b"HW-T stage3f gate3 synthetic artifact A\n" * 7) + bytes(range(64))
PAYLOAD_B = (b"HW-T stage3f gate3 synthetic artifact B\n" * 11) + bytes(reversed(range(64)))
PAYLOAD_C = b"HW-T stage3f gate3 synthetic artifact C cache-conflict\n" * 3


def descriptor(name: str, payload: bytes, snapshot: str = SNAPSHOT_BODY_SHA256) -> dict[str, Any]:
    return {"key": name, "size": len(payload), "sha256": sha256_bytes(payload), "snapshot_sha256": snapshot}


def expect_failure(fn: Callable[[], Any], cls: type[BaseException], contains: str) -> bool:
    try:
        fn()
    except cls as exc:
        return contains in str(exc)
    except Exception:
        return False
    return False


def canonical_document_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def run_success_scenario(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot_bytes = SNAPSHOT_PATH.read_bytes()
    a = descriptor("fixture-a", PAYLOAD_A)
    b = descriptor("fixture-b", PAYLOAD_B)
    routes = {
        "/snapshot.json": Route(snapshot_bytes),
        "/artifact/a": Route(PAYLOAD_A),
        "/artifact/b": Route(PAYLOAD_B),
    }
    cache = root / "cache"
    with LoopbackFixtureServer(routes) as server:
        document, snapshot_observation = fetch_and_verify_snapshot(
            server.base_url + "/snapshot.json",
            expected_file_size=SNAPSHOT_FILE_SIZE,
            expected_file_sha256=SNAPSHOT_FILE_SHA256,
            expected_body_sha256=SNAPSHOT_BODY_SHA256,
        )
        result_a = acquire_to_verified_cache(
            a,
            url=server.base_url + "/artifact/a",
            bound_snapshot_sha256=SNAPSHOT_BODY_SHA256,
            cache_root=cache,
        )
        before_repeat = list(server.requests)
        repeat_a = acquire_to_verified_cache(
            a,
            url=server.base_url + "/artifact/a",
            bound_snapshot_sha256=SNAPSHOT_BODY_SHA256,
            cache_root=cache,
        )
        after_repeat = list(server.requests)
        result_b = acquire_to_verified_cache(
            b,
            url=server.base_url + "/artifact/b",
            bound_snapshot_sha256=SNAPSHOT_BODY_SHA256,
            cache_root=cache,
        )
        files = sorted(p for p in cache.rglob("*") if p.is_file())
        normalized = {
            "snapshot_sha256": document["snapshot_sha256"],
            "snapshot_observed_sha256": snapshot_observation["observed_sha256"],
            "a_status": result_a["status"],
            "a_repeat_status": repeat_a["status"],
            "b_status": result_b["status"],
            "a_digest": hashlib.sha256(content_addressed_path(cache, a["sha256"]).read_bytes()).hexdigest(),
            "b_digest": hashlib.sha256(content_addressed_path(cache, b["sha256"]).read_bytes()).hexdigest(),
            "file_count": len(files),
            "requests": [Path(item).name for item in server.requests],
        }
        details = {
            "document": document,
            "snapshot_observation": snapshot_observation,
            "result_a": result_a,
            "repeat_a": repeat_a,
            "result_b": result_b,
            "before_repeat": before_repeat,
            "after_repeat": after_repeat,
            "cache": cache,
            "files": files,
            "descriptor_a": a,
            "descriptor_b": b,
        }
        return normalized, details


def main() -> int:
    checks: dict[str, bool] = {}
    negative: dict[str, bool] = {}
    incomplete: dict[str, bool] = {}

    with tempfile.TemporaryDirectory() as td:
        first_root = Path(td) / "first"
        second_root = Path(td) / "second"
        first, details = run_success_scenario(first_root)
        second, _ = run_success_scenario(second_root)
        a = details["descriptor_a"]
        b = details["descriptor_b"]
        cache: Path = details["cache"]
        a_path = content_addressed_path(cache, a["sha256"])
        b_path = content_addressed_path(cache, b["sha256"])

        checks["snapshot-fetch-exact"] = details["document"]["snapshot_sha256"] == SNAPSHOT_BODY_SHA256
        checks["snapshot-file-observation"] = details["snapshot_observation"]["observed_sha256"] == SNAPSHOT_FILE_SHA256
        checks["artifact-a-promoted"] = details["result_a"]["status"] == "promoted" and details["result_a"]["network_used"] is True
        checks["artifact-b-promoted"] = details["result_b"]["status"] == "promoted" and details["result_b"]["network_used"] is True
        checks["repeat-cache-hit"] = details["repeat_a"]["status"] == "cache-hit" and details["repeat_a"]["network_used"] is False
        checks["repeat-no-request"] = details["before_repeat"] == details["after_repeat"]
        checks["content-addressed-layout"] = a_path.name == a["sha256"] and a_path.parent.name == a["sha256"][:2]
        checks["cache-bytes-exact"] = a_path.read_bytes() == PAYLOAD_A and b_path.read_bytes() == PAYLOAD_B
        checks["cache-object-count"] = len(details["files"]) == 2
        checks["candidate-cleanup"] = not (cache / ".candidates").exists()
        checks["installation-remains-forbidden"] = all(result["installation_permitted"] is False for result in (details["result_a"], details["repeat_a"], details["result_b"]))
        checks["deterministic-repeat"] = first == second

        snapshot_bytes = SNAPSHOT_PATH.read_bytes()
        wrong_a = bytes([PAYLOAD_A[0] ^ 1]) + PAYLOAD_A[1:]
        altered_document = json.loads(snapshot_bytes.decode("utf-8"))
        altered_document["snapshot_sha256"] = "f" * 64
        altered_snapshot = canonical_document_bytes(altered_document)
        routes = {
            "/snapshot.json": Route(snapshot_bytes),
            "/snapshot-bad-file.json": Route(bytes([snapshot_bytes[0] ^ 1]) + snapshot_bytes[1:]),
            "/snapshot-bad-body.json": Route(altered_snapshot),
            "/artifact/a": Route(PAYLOAD_A),
            "/artifact/a-wrong": Route(wrong_a),
            "/artifact/a-truncated": Route(PAYLOAD_A[:-5], declared_length=len(PAYLOAD_A)),
            "/artifact/a-oversized": Route(PAYLOAD_A + b"X"),
            "/redirect": Route(b"", status=302, headers={"Location": "/artifact/a"}),
            "/artifact/b-wrong": Route(bytes([PAYLOAD_B[0] ^ 1]) + PAYLOAD_B[1:]),
            "/artifact/c": Route(PAYLOAD_C),
        }
        isolated = Path(td) / "negative-cache"
        with LoopbackFixtureServer(routes) as server:
            request_count = len(server.requests)
            negative["non-loopback-host"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url="http://example.com:80/a", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                PolicyError,
                "non-loopback-host",
            ) and len(server.requests) == request_count
            negative["https-scheme"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url.replace("http://", "https://") + "/artifact/a", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                PolicyError,
                "scheme-not-http",
            )
            negative["query-forbidden"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/artifact/a?x=1", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                PolicyError,
                "query-or-fragment-forbidden",
            )
            negative["redirect-rejected"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/redirect", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "http-status:302",
            )
            negative["missing-route"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/missing", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "http-status:404",
            )
            negative["candidate-hash-mismatch"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/artifact/a-wrong", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                VerificationError,
                "candidate-sha256-mismatch",
            )
            wrong_size = dict(a); wrong_size["size"] = a["size"] + 1
            negative["candidate-size-mismatch"] = expect_failure(
                lambda: acquire_to_verified_cache(wrong_size, url=server.base_url + "/artifact/a", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "content-length-mismatch",
            )
            negative["truncated-response"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/artifact/a-truncated", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "read",
            ) or expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/artifact/a-truncated", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "body-size-mismatch",
            )
            negative["oversized-response"] = expect_failure(
                lambda: acquire_to_verified_cache(a, url=server.base_url + "/artifact/a-oversized", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                TransportError,
                "content-length-mismatch",
            )
            negative["snapshot-file-digest"] = expect_failure(
                lambda: fetch_and_verify_snapshot(
                    server.base_url + "/snapshot-bad-file.json",
                    expected_file_size=SNAPSHOT_FILE_SIZE,
                    expected_file_sha256=SNAPSHOT_FILE_SHA256,
                    expected_body_sha256=SNAPSHOT_BODY_SHA256,
                ),
                VerificationError,
                "snapshot-file-sha256-mismatch",
            )
            negative["snapshot-body-digest"] = expect_failure(
                lambda: fetch_and_verify_snapshot(
                    server.base_url + "/snapshot-bad-body.json",
                    expected_file_size=len(altered_snapshot),
                    expected_file_sha256=sha256_bytes(altered_snapshot),
                    expected_body_sha256=SNAPSHOT_BODY_SHA256,
                ),
                VerificationError,
                "snapshot-contract-invalid",
            ) or expect_failure(
                lambda: fetch_and_verify_snapshot(
                    server.base_url + "/snapshot-bad-body.json",
                    expected_file_size=len(altered_snapshot),
                    expected_file_sha256=sha256_bytes(altered_snapshot),
                    expected_body_sha256=SNAPSHOT_BODY_SHA256,
                ),
                VerificationError,
                "snapshot-body-sha256-mismatch",
            )
            wrong_binding = dict(b); wrong_binding["snapshot_sha256"] = "e" * 64
            before_binding = len(server.requests)
            negative["snapshot-binding-mismatch"] = expect_failure(
                lambda: acquire_to_verified_cache(wrong_binding, url=server.base_url + "/artifact/b-wrong", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=isolated),
                VerificationError,
                "snapshot-binding-mismatch",
            ) and len(server.requests) == before_binding

            preserved = isolated / "preserved"
            good_a = acquire_to_verified_cache(a, url=server.base_url + "/artifact/a", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=preserved)
            before_bytes = content_addressed_path(preserved, a["sha256"]).read_bytes()
            failure_b = expect_failure(
                lambda: acquire_to_verified_cache(b, url=server.base_url + "/artifact/b-wrong", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=preserved),
                VerificationError,
                "candidate-sha256-mismatch",
            )
            negative["verified-cache-preserved-after-failure"] = good_a["status"] == "promoted" and failure_b and content_addressed_path(preserved, a["sha256"]).read_bytes() == before_bytes

            c = descriptor("fixture-c", PAYLOAD_C)
            conflict_root = isolated / "conflict"
            conflict_path = content_addressed_path(conflict_root, c["sha256"])
            conflict_path.parent.mkdir(parents=True, exist_ok=True)
            conflict_path.write_bytes(b"not-the-expected-object")
            conflict_before = conflict_path.read_bytes()
            before_conflict_requests = len(server.requests)
            negative["cache-conflict-no-overwrite"] = expect_failure(
                lambda: acquire_to_verified_cache(c, url=server.base_url + "/artifact/c", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=conflict_root),
                CacheConflictError,
                "existing-content-addressed-object-mismatch",
            ) and conflict_path.read_bytes() == conflict_before and len(server.requests) == before_conflict_requests

        base = descriptor("incomplete", b"x")
        for field in ("key", "size", "sha256", "snapshot_sha256"):
            value = dict(base); value.pop(field)
            incomplete[f"missing-{field}"] = expect_failure(
                lambda value=value: acquire_to_verified_cache(value, url="http://127.0.0.1:1/x", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=Path(td) / "incomplete"),
                PolicyError,
                "descriptor-missing",
            )
        incomplete["missing-url"] = expect_failure(
            lambda: acquire_to_verified_cache(base, url="", bound_snapshot_sha256=SNAPSHOT_BODY_SHA256, cache_root=Path(td) / "incomplete"),
            PolicyError,
            "locator-missing",
        )

    failed = sorted(
        [name for name, passed in checks.items() if not passed]
        + [f"negative:{name}" for name, passed in negative.items() if not passed]
        + [f"incomplete:{name}" for name, passed in incomplete.items() if not passed]
    )
    result = {
        "schema_version": 1,
        "verification_kind": "stage3f-gate3-loopback-transport-acquisition",
        "pass": not failed,
        "check_count": len(checks) + len(negative) + len(incomplete),
        "pass_count": sum(checks.values()) + sum(negative.values()) + sum(incomplete.values()),
        "failed_checks": failed,
        "checks": dict(sorted(checks.items())),
        "expected_negative": dict(sorted(negative.items())),
        "incomplete": dict(sorted(incomplete.items())),
        "snapshot_sha256": SNAPSHOT_BODY_SHA256,
        "publisher_binding": "127.0.0.1-ephemeral-port-only",
        "cache_policy": "isolated-content-addressed-no-replacement",
        "claim_boundary": "Loopback-only synthetic transport and isolated cache behavior. No public endpoint, uv invocation, Android target, CPython artifact acquisition, installation, or durability claim.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
