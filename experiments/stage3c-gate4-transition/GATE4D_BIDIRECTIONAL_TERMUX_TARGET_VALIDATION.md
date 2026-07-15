# Stage 3-C Phase 5 Gate 4D: Bidirectional Termux Target Validation

> **Status:** ACCEPTED — final adjudication 66/66 PASS
> **Products:** exact frozen CPython 3.14.5 and 3.14.6 authorities
> **Freeze:** Gate 4E independent archive and repository freeze

Gate 4D preserves the initial complete target run and a corrective focused retest. The initial FAIL is not replaced; it supplies 55 unaffected PASS scenarios and raw evidence for 11 harness false negatives.

```text
v1  ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c  493427 bytes  1223/1223
v2  98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2  720554 bytes  529/529
```

H01-H08 were rerun with explicit uv-provided tzdata and native development-extension compile/import where installed. C11-C12 were replayed from preserved before/after state because source-only removal does not create the originally required collision path. A04 was derived after corrected happy and collision groups passed. The remaining 55 rows retain v1 provenance.

```text
preflight 14/14  happy 8/8  collision 12/12
recovery 24/24   locking 2/2 audit 6/6
total 66/66
```

Accepted behavior is exact to both directions and the four frozen topologies, including registry/payload identity, source-only removal, sentinel preservation, transaction cleanup, preflight, collision, locking, crash recovery, CLI/base runtime, extensions, timezone, venv, uv, and relocation. No third product, registry migration, arbitrary mixed-product repair, or consumer integration is accepted.
