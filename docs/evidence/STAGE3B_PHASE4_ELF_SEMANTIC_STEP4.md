# Stage 3-B Phase 4.1 Regenerated Surface Comparison: Step 4

> **Status:** PASS — native semantic surface preserved
> **Final marker:** `STAGE3B_REGENERATED_SURFACE_COMPARE=PASS`

## ELF result

```text
changed ELF objects       69
semantic matches          69
semantic mismatches        0
```

Every regenerated CPython ELF object matched at:

```text
ELF class
data encoding
object type
machine
flags
DT_NEEDED
DT_SONAME
DT_RPATH
DT_RUNPATH
normalized defined dynamic symbols
normalized undefined dynamic symbols
```

The comparison intentionally ignored byte-layout properties such as build ID, section offsets, symbol addresses, and debug content.

## Interpretation

The exact 69-object set is:

```text
libpython shared objects      2
extension modules            67
```

Therefore:

> The Linux replay regenerated a byte-different CPython native surface with the same observed loader contract and dynamic-symbol consumer surface as the historical product.

This is stronger than treating the byte differences as expected without measurement.

It is not yet a target-side import or behavioral claim. Phase 5 must still run closure and extension probes on Termux.

## Remaining five non-ELF differences

```text
lib/python3.14/_sysconfig_vars__android_aarch64-linux-android.json
lib/python3.14/_sysconfigdata__android_aarch64-linux-android.py
lib/python3.14/build-details.json
lib/python3.14/config-3.14-aarch64-linux-android/Makefile
lib/python3.14/config-3.14-aarch64-linux-android/config.c
```

All five belong to the installed build/development metadata surface.

They are not silently ignored. The next capture compares their structured keys, generated values, and producer-path deltas.

## Current boundary conclusion

The package successor model now has:

```text
3077 exact entries
69 regenerated native entries with semantic equality
5 build/development metadata entries pending delta classification
0 package-only paths
4 historical-only assembly paths already classified
```
