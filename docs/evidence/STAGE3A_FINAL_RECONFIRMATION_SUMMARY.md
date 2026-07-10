# Stage 3-A Final Reconfirmation Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** PASS

## Purpose

This summary records the final acceptance-condition reconfirmation performed after the Stage 3-A closure, metadata, non-ELF boundary, and audit tooling had been introduced.

The two final gates were:

```text
1. canonical production-shape Stage 2-C smoke
2. production-shape whole-prefix relocation reconfirmation
```

## Canonical smoke reconfirmation

Command:

```text
bash scripts/test/smoke-termux.sh
```

Observed base runtime:

```text
sys.executable:
  work/termux/stage2c/runtime/prefix/bin/python

sys.prefix:
  work/termux/stage2c/runtime/prefix

sys.base_prefix:
  work/termux/stage2c/runtime/prefix

LD_LIBRARY_PATH:
  work/termux/stage2c/runtime/prefix/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

HTTPS:
  200
```

Fresh uv venv:

```text
sys.prefix:
  results/termux/stage2c/venv

sys.base_prefix:
  work/termux/stage2c/runtime/prefix
```

Fresh uv run:

```text
anyio import PASS
sys.prefix = uv ephemeral environment
sys.base_prefix = frozen Stage 2-C runtime prefix
```

Final marker:

```text
STAGE2C_SMOKE=PASS
```

## Production-shape relocation reconfirmation

The Stage 3-A relocation harness used the canonical assembled runtime:

```text
work/termux/stage2c/runtime/prefix
```

and tested:

```text
canonical runtime
    -> copy to location A
    -> validate A
    -> move whole prefix A -> B
    -> validate B
```

### Location A

Observed:

```text
base runtime identity                     PASS
active sysconfig paths rooted at A        PASS
HTTPS 200                                 PASS
child interpreter identity rooted at A    PASS
fresh uv venv                             PASS
fresh venv base_prefix = A                PASS
uv run                                    PASS
uv run base_prefix = A                    PASS
```

Marker:

```text
LOCATION_RECONFIRM[A]=PASS
```

### Location B after A -> B move

Observed:

```text
base runtime identity                     PASS
active sysconfig paths rooted at B        PASS
HTTPS 200                                 PASS
child interpreter identity rooted at B    PASS
fresh uv venv                             PASS
fresh venv base_prefix = B                PASS
uv run                                    PASS
uv run base_prefix = B                    PASS
```

Marker:

```text
LOCATION_RECONFIRM[B]=PASS
```

## Stale A-prefix assertions

At location B the harness directly asserted absence of the old A prefix from:

```text
sys.prefix
sys.base_prefix
sys.path
active sysconfig.get_paths() values
child interpreter identity
fresh venv base_prefix and import paths
uv run base_prefix and import paths
```

Final markers:

```text
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

## uv hardlink warning

uv emitted its known warning that hardlinks were unavailable across the tested cache/target filesystem arrangement and fell back to copying.

Observed:

```text
package installation completed
venv validation completed
uv run completed
```

Frozen interpretation:

> The warning affects link-mode performance characteristics, not the functional result of the tested workflows.

## Acceptance conclusion

The final Stage 3-A acceptance gates passed:

```text
Stage 2-C smoke on inventoried runtime                 PASS
whole-prefix production-shape relocation reconfirm    PASS
fresh uv venv at A                                     PASS
fresh uv venv at B                                     PASS
uv run at A                                            PASS
uv run at B                                            PASS
stale A runtime-path assertions                        PASS
```

This evidence closes the final validation gap required before Stage 3-A freeze review.
