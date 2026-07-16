# Epoch 1 Closure

> **Status:** FROZEN predecessor
> **Final accepted repository commit:** `e1de252740a96c40f3d587269136235a2c84ea16`
> **Final stage:** Stage 3-F through Gate 5 with documentation-integrity correction

## Purpose of the closure

Epoch 1 began as an investigation of whether an upstream CPython Android build could behave as a practical Termux command-line interpreter. It ended with a reproducible, evidence-driven product and lifecycle system spanning two CPython versions, uv consumption, project-owned managed installation, and retained publication/acquisition authority.

Epoch 2 does not replace or reinterpret this evidence. It changes the product decomposition built on top of it.

## Completed authority

```text
runtime
  R2 conditional self re-exec + B0 PyConfig discovery
  whole-prefix relocation
  native extension and DT_NEEDED closure
  HTTPS, timezone, subprocess, venv, and uv workflows

producer and products
  reproducible CPython Android source/toolchain/dependency reconstruction
  independently frozen CPython 3.14.5 and 3.14.6 products
  exact archives, manifests, product locks, and provenance

installer and lifecycle
  ownership registry and preserve-and-report policy
  transactional install, recovery, repair, and uninstall
  addon dependency rules and final teardown
  66-scenario bidirectional upgrade/downgrade authority

consumers and distribution
  uv explicit system-Python workflows
  bounded uv managed-Python feasibility
  local, offline, exact-key, project-owned managed-Python root
  immutable publication snapshot and fail-closed acquisition cache
  retained actual-byte target validation and independent freeze
```

## Deliberately unclaimed

Epoch 1 did not accept:

- a public production download service, DNS/TLS origin policy, signatures, mirrors, or release promotion;
- built-in upstream uv Android managed-Python catalog support;
- arbitrary third-product compatibility or general schema migration;
- a generic glibc-style Android Linux distribution;
- Android app embedding as the primary product;
- a separately branded and independently released standalone repository.

## Handoff to Epoch 2

Epoch 2 inherits every frozen behavior and claim boundary. It may package, expose, and reorganize responsibilities only when each transformation preserves or explicitly revalidates:

```text
runtime and subprocess identity
native closure and extension surface
CA and timezone boundaries
uv and venv behavior
whole-prefix relocation
archive and manifest identity
ownership and dependency policy
transaction, recovery, residual, and transition semantics
publication and acquisition identity
```

## Historical preservation

Existing `docs/stages/`, `docs/evidence/`, `docs/handoff/`, and `experiments/` paths remain in place. Failed and superseded attempts remain evidence. Epoch 2 adds navigation and component boundaries instead of rewriting Epoch 1 history.
