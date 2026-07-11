# Stage 3-C Phase 1 Component Policy Result

> **Status:** PASS — isolated materialization active
> **Input contract:** 27/27
> **Policy selector:** 18/18
> **Independent verifier:** 34/34
> **Source mutation:** PASS

## Accepted identities

```text
source entries
  3155

role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

component manifest
  91088a013722ad35910f049bfc45b2e61607423d833c23038c1d9645497b7b84

source before/after fingerprint
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c
```

```text
failed_checks      []
missing_inputs     []
missing_outputs    []
parse_errors       {}
pass               true
```

## Complete component partition

```text
component                  entries     regular bytes     ELF     links
RUNTIME_BASE                   710        38,625,987       81         3
RUNTIME_METADATA                 3           119,958        0         0
DEVELOPMENT                    449         4,737,164        0         2
DEVELOPMENT_METADATA             5           236,211        0         0
OPTIONAL_TEST_SUITE           1785        33,476,596        0         0
OPTIONAL_TEST_DEMO               3               194        0         0
UNSUPPORTED_GUI_SOURCE         199         2,139,349        0         0
LICENSE                          1            13,804        0         0
```

The partition is complete and non-overlapping:

```text
component entry sum      3155
component byte sum       79,349,263
ELF sum                      81
symlink sum                   5
```

All 81 ELF entries remain in `RUNTIME_BASE`.

## Candidate artifact composition

```text
runtime-base
  RUNTIME_BASE + RUNTIME_METADATA + LICENSE
  714 entries
  38,759,749 regular-file bytes

development-addon
  DEVELOPMENT + DEVELOPMENT_METADATA
  454 entries
  4,973,375 regular-file bytes

test-addon
  OPTIONAL_TEST_SUITE + OPTIONAL_TEST_DEMO
  1788 entries
  33,476,790 regular-file bytes

unsupported-gui-source
  UNSUPPORTED_GUI_SOURCE
  199 entries
  2,139,349 regular-file bytes
  not distributed until a working _tkinter/Tcl/Tk backend exists
```

## Exact metadata ownership

Runtime metadata:

```text
lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
lib/python3.14/build-details.json
```

Development metadata:

```text
lib/python3.14/config-3.14-aarch64-linux-android/Makefile
lib/python3.14/config-3.14-aarch64-linux-android/Setup
lib/python3.14/config-3.14-aarch64-linux-android/Setup.local
lib/python3.14/config-3.14-aarch64-linux-android/config.c
lib/python3.14/config-3.14-aarch64-linux-android/python-config.py
```

## Unsupported GUI ownership

```text
lib/python3.14/tkinter/
lib/python3.14/idlelib/
lib/python3.14/turtledemo/
lib/python3.14/turtle.py
lib/python3.14/turtle.cfg, if present
```

The policy intentionally moves `turtle.py` out of its original descriptive runtime role because the target semantic probe proved that it cannot import without `_tkinter`.

## Independent verification

The 34-check verifier independently established:

```text
source and output path sets equal
source fields preserved
component mapping re-derived exactly
component path-list files exact
component summaries exact
component and artifact manifest hashes exact
runtime and development anchors present
runtime/development metadata sets exact
test roots exact
unsupported GUI source contains turtle and no ELF
runtime artifact composition exact
unsupported GUI disposition non-distributed
```

## Source mutation control

```text
before
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

after
  5465a389496e0f7810866ef4b8786d1f3d283b96116ff4da72b881c1a3ec3e6c

before entries   3155
after entries    3155
pass             true
```

## Next isolated variants

The policy now permits four disposable, exact-path trees:

```text
runtime-base
  714 entries

runtime-development
  runtime-base + development-addon
  1168 entries

runtime-test
  runtime-base + test-addon
  2502 entries

runtime-supported
  runtime-base + development-addon + test-addon
  2956 entries
```

No unsupported GUI source is copied into these variants.

The first isolated validation gate requires:

```text
exact selected path/type/mode/mtime/hash/symlink fidelity
all 81 ELF entries retained
runtime-base production smoke including HTTPS and uv/venv
variant-specific positive and negative import matrix
development-addon native C extension compile and import
test-addon representative CPython regression test
all variant fingerprints unchanged after validation
canonical source fingerprint unchanged
```

## Claim boundary

Proved:

```text
every canonical path has exactly one candidate component
artifact composition is complete and non-overlapping
unsupported GUI source is explicitly excluded
canonical source was not modified
```

Not proved:

```text
materialized variants preserve exact product fidelity
runtime-base production behavior passes
native development works after addon composition
test addon executes successfully
runtime-base preserves native closure and relocation
```

Those claims belong to isolated-copy validation. The canonical promoted tree remains frozen.
