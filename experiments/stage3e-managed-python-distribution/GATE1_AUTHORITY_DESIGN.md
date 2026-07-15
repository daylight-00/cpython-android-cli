# Stage 3-E Gate 1: Managed-Python Distribution Authority Design

> **Status:** DESIGN FROZEN
> **Claim:** the next target gate is an isolated offline dual-version managed-Python boundary census

## Why a new stage is required

Stage 3-D Gate 6 answered a feasibility question under deliberately disposable conditions. Product distribution introduces different authorities: publication, persistent paths, multi-version selection, lifecycle policy, recovery, and coexistence with the accepted system-Python surface. Those claims cannot be inferred from a single-product isolated PASS.

Stage 3-E therefore begins from the exact Gate 6 authority and does not modify it.

## Frozen input

```text
Stage 3-D Gate 6 freeze commit
  c4f0333db196b7bf0e074b9556d566e0d33c91aa

Stage 3-D Gate 6 freeze tree
  593695ee66270cb9f496df10bef624717ba7fc98

Gate 6 authority blob
  92f1fb56f237661d9eeba934ad02f8c275f5c1cb

uv
  0.11.28 (aarch64-linux-android)
  f624c48a72b2e2e307043f339eb3ff6dbdfa0207be2053d2e5bc071709289495
```

## Productization authorities

Stage 3-E separates these questions:

```text
catalog
  exact keys, metadata, publication, and update authority

artifact transport
  immutable archive identity, location, availability, and mirror policy

installation
  persistent root, executable exposure, permissions, and coexistence

selection
  exact, minor, unspecified, project, and active-environment precedence

lifecycle
  install, exact reinstall, uninstall, upgrade, downgrade, recovery, and residue

compatibility
  system-Python contract, existing Termux Python, and future product versions
```

## Selected Gate 2

Gate 2 is an isolated dual-version boundary census. It uses one custom local catalog containing:

```text
cpython-3.14.5-linux-aarch64-none
cpython-3.14.6-linux-aarch64-none
```

The census covers both install orders and records:

```text
catalog recognition
side-by-side installation
installed list ordering
exact-version discovery
minor-version and unspecified discovery
interpreter identity and direct launch
uv venv creation and launch
exact reinstall/no-op identity
uninstall of one version while the peer remains
final empty-state expected negative
```

All state is disposable and isolated. Network access remains disabled. Explicit install commands alone may use `UV_PYTHON_DOWNLOADS=manual`; all other commands use `never`.

## Invariants

Gate 2 must prove before/after identity for:

```text
repository and remote branch
Stage 3-D authorities
canonical CPython 3.14.5 and 3.14.6 products
real uv managed-Python directory
$PREFIX/bin
shell startup files
project registry and journal state
```

## Decision outputs expected from Gate 2

Gate 2 must determine, without yet selecting a production design:

```text
whether both products are accepted by one catalog
whether exact keys coexist without collision
how minor and unspecified requests resolve
whether install order changes selection
whether removal of one product preserves the other
whether both installed trees retain Android identity
which behaviors require an explicit Gate 3 policy
```

## Not proved

Gate 1 does not prove any dual-version result, persistent installation path, catalog publication mechanism, network mirror, global executable exposure, upgrade/recovery policy, third-product compatibility, or upstream uv Android support.
