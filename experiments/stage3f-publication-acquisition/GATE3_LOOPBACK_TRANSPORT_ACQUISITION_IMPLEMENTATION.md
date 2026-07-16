# Stage 3-F Gate 3: Loopback Transport and Acquisition Implementation

> **Status:** IMPLEMENTATION FROZEN — local loopback behavior verified
> **Class:** L, local behavior
> **Input:** Gate 2 commit `82c21757e08b040fb7167c90e60fa48af323efb0`, tree `ba85ac5bf09bdfc2aac7482077535ac2942cbc38`
> **Snapshot:** `a00027a81956ef175bf537eff3a92286e26c1120fa536d0a8ad6a096a1760f8c`

## Boundary

Gate 3 implements the first transport and cache transition without opening any public publication surface. A Python standard-library fixture publisher binds only to `127.0.0.1` on an ephemeral port. The acquisition client rejects every non-loopback host, HTTPS locator, query, fragment, unsafe path, and redirect before accepting bytes as evidence.

```text
immutable Gate 2 snapshot
  -> exact loopback response capture
  -> canonical snapshot and digest verification
  -> untrusted artifact candidate
  -> exact Content-Length
  -> exact observed size
  -> exact observed SHA-256
  -> exact snapshot binding
  -> exclusive content-addressed cache promotion
```

A content-addressed path is never replaced. An already valid object is an exact cache hit; an existing mismatched object is a conflict and remains untouched. Failed and partial candidates are removed. Installation remains forbidden.

## Synthetic fixture surface

The implementation is generic, but Gate 3 exercises it with deterministic small fixture bytes rather than the real CPython archives:

```text
fixture-a  344 bytes  c40fe3e0affea04d95a55601be476f46aa74561c4108e80f1dfcf4a010316cf9
fixture-b  504 bytes  5a09b2f32ae9d2cc5b90f48ae24f69fb518bbadb675a90331e78e72241ee5f75
fixture-c  165 bytes  f060b4c69b634a36ab1247d6fc5160776d58792d6168cf2593b6c44f7f07559a
```

These fixture identities are not CPython product identities and cannot be used as publication rows.

## Verified matrix

The verifier passes 31/31 checks:

```text
success                 12
expected negative       14
incomplete               5
```

Accepted local behavior includes exact snapshot fetch, two independent promotions, content-addressed layout, repeat cache no-op, no repeat request, candidate cleanup, deterministic repeat, redirect rejection, public-host rejection, wrong size/hash rejection, truncated and oversized response rejection, snapshot digest rejection, snapshot-binding rejection, cache-conflict no-overwrite, and preservation of an existing verified object after another acquisition fails.

## Gate 4 selected boundary

Gate 4 moves the same policy to the real Termux host and actual frozen CPython archive bytes, still through loopback-only HTTP and an isolated cache. It must not invoke uv, execute a product before verification, install into the Stage 3-E root, or use a public endpoint.

## Not proved

Public availability, DNS/TLS/origin authenticity, signatures, redirects or mirrors in production, automatic uv acquisition, installation, resumable transfer, cache garbage collection, concurrent writers, crash or power-loss durability, third products, and upstream uv Android support remain unaccepted.
