#!/usr/bin/env python3
"""Bounded loopback publication and acquisition support for Stage 3-F Gate 3.

The implementation accepts only explicit HTTP URLs on 127.0.0.1, rejects
redirects, receives bytes into an untrusted candidate, verifies exact size and
SHA-256, and promotes to an isolated content-addressed cache without replacing
an existing object. It does not install or execute a product.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import shutil
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from publication_snapshot import canonical_bytes, verify_snapshot_document


class AcquisitionError(RuntimeError):
    """Base class for bounded acquisition failures."""


class PolicyError(AcquisitionError):
    """The requested locator or descriptor violates Gate 3 policy."""


class TransportError(AcquisitionError):
    """The loopback response could not be received exactly."""


class VerificationError(AcquisitionError):
    """Received bytes do not match their expected immutable identity."""


class CacheConflictError(AcquisitionError):
    """A non-matching object already occupies the content-addressed path."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_loopback_url(url: str) -> urllib.parse.SplitResult:
    if not isinstance(url, str) or not url:
        raise PolicyError("locator-missing")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "http":
        raise PolicyError("scheme-not-http")
    if parsed.username is not None or parsed.password is not None:
        raise PolicyError("userinfo-forbidden")
    if parsed.hostname != "127.0.0.1":
        raise PolicyError("non-loopback-host")
    if parsed.port is None:
        raise PolicyError("explicit-port-required")
    if parsed.query or parsed.fragment:
        raise PolicyError("query-or-fragment-forbidden")
    decoded_path = urllib.parse.unquote(parsed.path)
    if not decoded_path.startswith("/") or any(part == ".." for part in decoded_path.split("/")):
        raise PolicyError("unsafe-path")
    return parsed


def validate_descriptor(descriptor: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(descriptor, Mapping):
        raise PolicyError("descriptor-not-object")
    required = {"key", "size", "sha256", "snapshot_sha256"}
    missing = sorted(required - set(descriptor))
    if missing:
        raise PolicyError("descriptor-missing:" + ",".join(missing))
    key = descriptor["key"]
    size = descriptor["size"]
    digest = descriptor["sha256"]
    snapshot = descriptor["snapshot_sha256"]
    if not isinstance(key, str) or not key:
        raise PolicyError("descriptor-key")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise PolicyError("descriptor-size")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise PolicyError("descriptor-sha256")
    if not isinstance(snapshot, str) or len(snapshot) != 64 or any(c not in "0123456789abcdef" for c in snapshot):
        raise PolicyError("descriptor-snapshot-sha256")
    return {"key": key, "size": size, "sha256": digest, "snapshot_sha256": snapshot}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_NoRedirect())


def _response_content_length(headers: Any) -> int:
    value = headers.get("Content-Length")
    if value is None:
        raise TransportError("content-length-missing")
    try:
        length = int(value)
    except (TypeError, ValueError) as exc:
        raise TransportError("content-length-invalid") from exc
    if length < 0:
        raise TransportError("content-length-negative")
    return length


def fetch_exact_bytes(url: str, *, expected_size: int, timeout: float = 5.0) -> tuple[bytes, dict[str, Any]]:
    validate_loopback_url(url)
    request = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "Connection": "close"})
    try:
        with _opener().open(request, timeout=timeout) as response:
            status = int(response.getcode())
            if status != 200:
                raise TransportError(f"http-status:{status}")
            declared = _response_content_length(response.headers)
            if declared != expected_size:
                raise TransportError(f"content-length-mismatch:{declared}:{expected_size}")
            try:
                body = response.read(expected_size + 1)
            except http.client.IncompleteRead as exc:
                raise TransportError(f"incomplete-read:{len(exc.partial)}:{expected_size}") from exc
    except urllib.error.HTTPError as exc:
        raise TransportError(f"http-status:{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise TransportError(f"url-error:{exc.reason}") from exc
    if len(body) != expected_size:
        raise TransportError(f"body-size-mismatch:{len(body)}:{expected_size}")
    return body, {
        "status": 200,
        "declared_size": declared,
        "observed_size": len(body),
        "observed_sha256": sha256_bytes(body),
        "url": url,
    }


def fetch_and_verify_snapshot(
    url: str,
    *,
    expected_file_size: int,
    expected_file_sha256: str,
    expected_body_sha256: str,
    timeout: float = 5.0,
) -> tuple[dict[str, Any], dict[str, Any]]:
    body, observation = fetch_exact_bytes(url, expected_size=expected_file_size, timeout=timeout)
    if sha256_bytes(body) != expected_file_sha256:
        raise VerificationError("snapshot-file-sha256-mismatch")
    try:
        document = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("snapshot-json-invalid") from exc
    if not isinstance(document, dict):
        raise VerificationError("snapshot-not-object")
    if canonical_bytes(document) != body:
        raise VerificationError("snapshot-not-canonical")
    verification = verify_snapshot_document(document)
    if not verification["pass"]:
        raise VerificationError("snapshot-contract-invalid:" + ",".join(verification["error_codes"]))
    if document.get("snapshot_sha256") != expected_body_sha256:
        raise VerificationError("snapshot-body-sha256-mismatch")
    observation["snapshot_sha256"] = expected_body_sha256
    return document, observation


def content_addressed_path(cache_root: Path, digest: str) -> Path:
    return cache_root / "sha256" / digest[:2] / digest


def _verify_cache_object(path: Path, *, expected_size: int, expected_sha256: str) -> bool:
    return path.is_file() and path.stat().st_size == expected_size and sha256_file(path) == expected_sha256


def acquire_to_verified_cache(
    descriptor: Mapping[str, Any],
    *,
    url: str,
    bound_snapshot_sha256: str,
    cache_root: Path,
    timeout: float = 5.0,
) -> dict[str, Any]:
    desc = validate_descriptor(descriptor)
    validate_loopback_url(url)
    if bound_snapshot_sha256 != desc["snapshot_sha256"]:
        raise VerificationError("snapshot-binding-mismatch")
    cache_root = cache_root.resolve()
    final_path = content_addressed_path(cache_root, desc["sha256"])
    if final_path.exists():
        if _verify_cache_object(final_path, expected_size=desc["size"], expected_sha256=desc["sha256"]):
            return {
                "status": "cache-hit",
                "key": desc["key"],
                "cache_path": str(final_path),
                "size": desc["size"],
                "sha256": desc["sha256"],
                "network_used": False,
                "installation_permitted": False,
            }
        raise CacheConflictError("existing-content-addressed-object-mismatch")

    candidates = cache_root / ".candidates"
    candidates.mkdir(parents=True, exist_ok=True)
    candidate = candidates / f"{desc['sha256']}.{uuid.uuid4().hex}.partial"
    try:
        body, observation = fetch_exact_bytes(url, expected_size=desc["size"], timeout=timeout)
        candidate.write_bytes(body)
        with candidate.open("rb") as stream:
            os.fsync(stream.fileno())
        observed_size = candidate.stat().st_size
        observed_sha256 = sha256_file(candidate)
        if observed_size != desc["size"]:
            raise VerificationError("candidate-size-mismatch")
        if observed_sha256 != desc["sha256"]:
            raise VerificationError("candidate-sha256-mismatch")
        final_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(final_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if _verify_cache_object(final_path, expected_size=desc["size"], expected_sha256=desc["sha256"]):
                return {
                    "status": "cache-race-hit",
                    "key": desc["key"],
                    "cache_path": str(final_path),
                    "size": desc["size"],
                    "sha256": desc["sha256"],
                    "network_used": True,
                    "installation_permitted": False,
                    "transport": observation,
                }
            raise CacheConflictError("raced-content-addressed-object-mismatch")
        try:
            with os.fdopen(fd, "wb") as out, candidate.open("rb") as source:
                shutil.copyfileobj(source, out, length=1024 * 1024)
                out.flush()
                os.fsync(out.fileno())
            if not _verify_cache_object(final_path, expected_size=desc["size"], expected_sha256=desc["sha256"]):
                final_path.unlink(missing_ok=True)
                raise VerificationError("promoted-cache-verification-failed")
        except Exception:
            final_path.unlink(missing_ok=True)
            raise
        return {
            "status": "promoted",
            "key": desc["key"],
            "cache_path": str(final_path),
            "size": observed_size,
            "sha256": observed_sha256,
            "network_used": True,
            "installation_permitted": False,
            "transport": observation,
        }
    finally:
        candidate.unlink(missing_ok=True)
        try:
            candidates.rmdir()
        except OSError:
            pass


@dataclass(frozen=True)
class Route:
    body: bytes = b""
    status: int = 200
    headers: Mapping[str, str] = field(default_factory=dict)
    declared_length: int | None = None


class LoopbackFixtureServer:
    """Small deterministic publisher bound only to 127.0.0.1 for fixtures."""

    def __init__(self, routes: Mapping[str, Route]):
        self.routes = dict(routes)
        self.requests: list[str] = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:  # noqa: N802
                owner.requests.append(self.path)
                route = owner.routes.get(self.path)
                if route is None:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    return
                self.send_response(route.status)
                for key, value in route.headers.items():
                    self.send_header(key, value)
                if "Content-Length" not in route.headers:
                    length = len(route.body) if route.declared_length is None else route.declared_length
                    self.send_header("Content-Length", str(length))
                self.send_header("Connection", "close")
                self.end_headers()
                if route.body:
                    self.wfile.write(route.body)
                    self.wfile.flush()
                self.close_connection = True

            def log_message(self, format: str, *args: Any) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="stage3f-gate3-loopback", daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._server.server_address[:2]
        return f"http://{host}:{port}"

    def __enter__(self) -> "LoopbackFixtureServer":
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)
