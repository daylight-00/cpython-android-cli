# Stage 3-F Gate 3 Loopback Transport and Acquisition Result

> **Status:** FROZEN — local loopback behavior verified
> **Input:** Gate 2 commit `82c21757e08b040fb7167c90e60fa48af323efb0`, tree `ba85ac5bf09bdfc2aac7482077535ac2942cbc38`

## Result

The bounded publisher and acquisition engine pass 31/31 local checks. The publisher binds only to `127.0.0.1`; the client rejects non-loopback locators and redirects, verifies the exact Gate 2 snapshot, receives synthetic artifacts into isolated candidates, and promotes only exact size/hash matches to an exclusive content-addressed cache path.

```text
success checks           12/12
expected-negative checks 14/14
incomplete checks         5/5
failed checks             []
public network            none
uv invocation             none
Android target            none
real CPython artifacts    none
installation              none
cache mutation            isolated fixture paths only
```

A repeat acquisition is a cache no-op without another request. A failed transfer removes its candidate and preserves previously verified cache objects. A mismatched object already occupying a content-addressed path is not replaced.

## Claim boundary

This result accepts local loopback implementation behavior only. It does not accept public hosting, actual CPython artifact transport, Termux target behavior, uv acquisition, installation, origin trust, concurrent writers, crash recovery, or durability.

## Next

Gate 4 is a bounded Termux target validation using actual frozen archive bytes, loopback-only HTTP, and an isolated cache. It remains forbidden to invoke uv, execute unverified products, or mutate the Stage 3-E managed root.
