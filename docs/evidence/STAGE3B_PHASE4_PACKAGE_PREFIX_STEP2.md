# Stage 3-B Phase 4.1 Package-Prefix Comparison: Step 2

> **Status:** PASS — structural successor confirmed, differences pending classification
> **Final marker:** `STAGE3B_PACKAGE_PREFIX_COMPARISON=PASS`

## Comparison objects

```text
historical prefix
    versus
replay upstream package prefix/
```

The archive was read directly. It was not extracted into or over either input prefix.

Historical-prefix mutation check:

```text
PASS
```

## Structural result

| Metric | Historical prefix | Replay package prefix |
|---|---:|---:|
| entries | 3155 | 3151 |
| directories | 216 | 215 |
| files | 2934 | 2933 |
| symlinks | 5 | 3 |
| ELF objects | 81 | 80 |
| file bytes | 79336714 | 79338271 |

Exact path comparison:

```text
common exact       3077
common different     74
only historical       4
only package            0
```

## Launcher contract

```text
Python.h          byte-identical
pyconfig.h        byte-identical
libpython3.14.so  present in both, byte-different
```

Packaged replay library hash:

```text
f7d1a53e32186eb304ce1192f408994b557fe78e6e05c0c0c4d0934998b894a9
```

The packaged hash differs from the unstripped composite-prefix hash because upstream packaging strips shared objects by default.

## Interpretation

The absence of package-only paths is important:

> The clean upstream package does not introduce a new product surface relative to the historical prefix.

The four historical-only paths and 74 content differences still require exact classification. Likely producer-host or packaging effects are hypotheses, not conclusions.

Byte equality is not required in advance because the historical and replay producer hosts differ. Acceptance instead requires:

```text
path-role classification
ELF identity and dependency-surface comparison
launcher consumer validation
runtime behavior validation in later phases
```

No historical-only path is removed from the promoted contract until its role is known.
