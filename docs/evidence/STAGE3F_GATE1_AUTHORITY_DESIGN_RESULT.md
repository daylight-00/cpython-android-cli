# Stage 3-F Gate 1 Publication and Acquisition Authority Design Result

> **Status:** FROZEN — repository-only authority design
> **Input:** Stage 3-E Gate 5 commit `6419e107e4aa8400ebd3d98f3583999075b8b935`, tree `e16edd99bfadf2135d0b632ddef4d292c0d80ea6`
> **Active next:** Gate 2 deterministic immutable-publication snapshot contract and fixture census

## Result

Gate 1 separates immutable product identity, catalog rows, publication snapshots, endpoint locators, transport observations, acquisition candidates, verified caches, and installation roots. It defines a fail-closed transition from untrusted candidate bytes to a content-addressed verified cache and preserves the Stage 3-E installation authority unchanged.

```text
exact-key redefinition                    forbidden
URL/filename/endpoint as product identity forbidden
candidate promotion before size/hash      forbidden
failed acquisition mutates installed root false
verified cache key                         artifact SHA-256
publication snapshot                       canonical immutable metadata
mutable endpoint                           pointer to immutable snapshot only
```

## Repository validation

This is class R. Acceptance requires:

```text
exact Stage 3-E base and clean Termux checkout
new bounded Stage 3-F branch
project-control fixture suite PASS
project-control verifier PASS
git diff --check PASS
exact changed-path inventory
canonical Signed-off-by commit
normal push and remote readback
clean post-state
```

No target rerun or independent target audit is required because Gate 1 makes no target claim.

## Selected Gate 2

Gate 2 will locally implement the canonical publication-snapshot schema and verifier for the frozen 3.14.5 and 3.14.6 exact keys. It must include success, expected-negative, and incomplete fixtures and prove deterministic output. It opens no socket and performs no uv or target execution.

## Not accepted

Network publication, endpoint availability, DNS/TLS/origin authenticity, signatures, redirects, mirrors, automatic acquisition, uv default-root use, global links, installation changes, upgrades, recovery, concurrency, durability, third products, and upstream uv Android support remain unaccepted.
