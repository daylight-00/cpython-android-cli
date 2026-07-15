# Stage 3-D Gate 6 Managed-Python Feasibility Result

> **Status:** BOUNDED FEASIBILITY ACCEPTED — NOT PRODUCTION MANAGED-PYTHON ACCEPTANCE
> **Repository input:** `9d70ea1d3468ed02fa9684f61609c2cb5caf4ebc`, tree `fade17abba57b38f99c87368efc96b4e0aaa930a`
> **Target:** Termux on Android arm64
> **uv:** `0.11.28 (aarch64-linux-android)`

## Research question

Can an exact frozen HW-T Android CPython product participate in uv's managed-Python machinery without patching uv, changing the built-in catalog, registering into the real user managed directory, creating global links, or weakening the frozen system-Python consumer contract?

For the exact CPython 3.14.5 runtime-only product and fully isolated local-file conditions, the answer is yes.

## Gate 6-A — read-only catalog census

```text
work ID             20260715-stage3d-gate6a-managed-python-readonly-census-v1
result sha256       fa582b372b81feed68b76ee64bf304d364f9280b10a5569da6cb6fd9f9d43694
result size         4883
safe members        53
self-index          48/48 exact
Drive file          1DM9MSX42zXAcLFUQRanmKyGN0RTCGUc9
```

The built-in current-platform CPython 3.14 list is empty on the tested host. The all-platform list contains Linux aarch64 GNU and musl entries but no `linux-aarch64-none` entry. Setting `UV_LIBC` to `none`, `gnu`, or `musl` does not produce a current-platform candidate. A custom downloads JSON entry named `cpython-3.14.5-linux-aarch64-none` is listed both with all-platform output and as a current-platform candidate. Empty isolated managed discovery returns the expected failure.

The census itself completed before two wrapper transport defects were encountered: deletion of an active current working directory and rclone execution under an isolated HOME. The retained evidence was recovered and uploaded without rerunning the census. These defects do not change the catalog observation.

## Gate 6-B — isolated managed install rehearsal

The first v1 rehearsal is retained as a valid policy-preflight negative:

```text
result sha256  a42d61f70537ea836c7b92d406864dffa77c37478782fda4fd2e6250128d36cd
result size    2083
classification explicit local install blocked by UV_PYTHON_DOWNLOADS=never
```

The corrected v2 result is accepted:

```text
work ID             20260715-stage3d-gate6b-isolated-managed-install-rehearsal-v2
result sha256       73ef934e3a2346546c79032a80a4a791ac55f4858a02100301afd33f9bc8fa03
result size         5756
safe members        35
self-index          30/30 exact
Drive file          1NUQHqlQZ5xsQBVJRCmrTCmnxmpwtouf_
```

v2 uses `UV_PYTHON_DOWNLOADS=manual` only for the explicit install command. The catalog and archive are local `file://` inputs, all commands are offline, the install/cache/data paths are disposable and isolated, and global executable links are disabled with `--no-bin`.

Observed installed identity:

```text
key       cpython-3.14.5-linux-aarch64-none
version   3.14.5
SOABI     cpython-314-aarch64-linux-android
MULTIARCH aarch64-linux-android
platform  android-24-arm64_v8a
```

Installation, managed discovery, direct interpreter launch, uv virtual-environment creation, and virtual-environment launch all pass.

## Gate 6-C — isolated lifecycle

```text
work ID             20260715-stage3d-gate6c-isolated-managed-lifecycle-v1
result sha256       a0e15ef45171af409df27fb2265bb7afed7c1631176ebe6e563be04725fd72d6
result size         32769
safe members        39
self-index          34/34 exact
Drive file          1l9tiuQgzwFHeRWPejen3rcHpfbF79Nd-
```

The first exact install succeeds. A second exact install reports that the same key is already installed, and complete before/after manifests are byte-identical for path, entry type, mode, content hash, and symlink target. Managed discovery and direct launch remain exact. `uv python uninstall 3.14.5` removes the installation, the installed-only list becomes `[]`, and managed-only find returns code 2 with no interpreter found, as expected.

## Frozen feasibility contract

```text
catalog key             cpython-3.14.5-linux-aarch64-none
archive transport       local file://
explicit install policy UV_PYTHON_DOWNLOADS=manual
other command policy    UV_PYTHON_DOWNLOADS=never
network                  offline
install/cache/data       isolated disposable paths
global bin links         disabled
uv patch                 none
```

Repository state, the real uv managed-install directory, `$PREFIX/bin`, shell startup files, and canonical product inputs are byte-identical before and after each accepted experiment.

## Claim boundary

Gate 6 proves feasibility, not productization. It does not claim built-in uv Android catalog support, automatic or network downloads, a published production catalog, persistent user managed installation, global interpreter links, shell integration, CPython 3.14.6 or multi-version managed behavior, upgrade/downgrade policy, third-product compatibility, or general upstream uv Android platform support.
