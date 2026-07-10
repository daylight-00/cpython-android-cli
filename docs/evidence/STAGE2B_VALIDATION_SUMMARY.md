# Stage 2-B Main Validation Summary

> **Status:** Selected evidence
> **Stage:** 2-B
> **Result:** PASS

## Purpose

This summary freezes the decision-bearing results of the final R2 main validation. Raw bulk results remain outside the tracked repository; the historical harness is preserved under `experiments/stage2b-conditional-reexec/`.

## Profiles

```text
clean
  LD_LIBRARY_PATH unset
  SSL_CERT_FILE unset

ready
  correct <prefix>/lib present
  correct CA bundle present

wrong-ld
  unrelated loader path present
  valid CA present

wrong-ca
  correct loader path present
  SSL_CERT_FILE points to missing file

duplicate
  required <prefix>/lib duplicated
  valid CA present
```

## Final profile results

```text
PROFILE_RESULT[clean]=PASS
PROFILE_RESULT[ready]=PASS
PROFILE_RESULT[wrong-ld]=PASS
PROFILE_RESULT[wrong-ca]=PASS
PROFILE_RESULT[duplicate]=PASS
```

## Clean profile

Observed logical state:

```text
LD_LIBRARY_PATH:
  exactly <runtime-prefix>/lib

SSL_CERT_FILE:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

sys.prefix:
  runtime prefix

sys.base_prefix:
  runtime prefix

HTTPS:
  200

sys.platform:
  android

sysconfig platform:
  android-24-arm64_v8a
```

Expected and observed debug action sequence:

```text
reexec
direct
```

## Ready profile

Expected and observed debug action sequence:

```text
direct
```

No bootstrap re-exec was necessary when the required native path was already a component of `LD_LIBRARY_PATH`.

## Wrong loader path

The required runtime libdir was prepended while preserving the unrelated existing component.

Logical result:

```text
<runtime-prefix>/lib:<wrong-path>
```

Native imports and HTTPS passed after repair.

## Wrong CA path

The loader environment was already ready, so no re-exec was required for CA repair.

The nonexistent CA path was replaced with:

```text
/data/data/com.termux/files/usr/etc/tls/cert.pem
```

HTTPS returned status 200.

## Duplicate loader path

Input contained the required runtime libdir twice.

The final path contained one exact required component.

This validated duplicate normalization without requiring re-exec when the required component was already present at process start.

## Unrelated working directory

Result:

```text
UNRELATED_CWD_RC=0
```

The launcher did not depend on the process current working directory for runtime-prefix discovery.

## External symlink invocation

Result:

```text
SYMLINK_RC=0
```

The runtime prefix remained correct because discovery used the actual executable location rather than the symlink text or working directory.

## Subprocess re-entry

Result:

```text
SUBPROCESS_RC=0
```

Logical action sequence:

```text
parent:
  reexec
  direct

child via sys.executable:
  direct
```

Combined:

```text
reexec
direct
direct
```

The child inherited the prepared loader environment and avoided redundant bootstrap re-exec.

## uv venv

Result:

```text
UV_VENV_RC=0
```

The selected R2 interpreter was accepted by uv with Python downloads disabled.

## Clean venv launch

Result:

```text
VENV_CLEAN_RC=0
```

Observed identity:

```text
sys.executable:
  <venv>/bin/python

sys.prefix:
  <venv>

sys.base_prefix:
  <Stage-2-B runtime prefix>

sys.prefix != sys.base_prefix:
  true
```

Native imports succeeded.

## uv run

Result:

```text
UV_RUN_RC=0
```

The uv ephemeral environment used the Stage 2-B runtime as `sys.base_prefix`.

## Frozen interpretation

The Stage 2-B main validation established, on the tested target:

```text
R2 environment fixed point                    PASS
single top-level bootstrap re-exec             PASS
ready-process direct entry                     PASS
child redundant re-exec avoidance              PASS
native stdlib imports                          PASS
HTTPS                                           PASS
wrong loader state repair                      PASS
wrong CA state repair                          PASS
duplicate required path normalization          PASS
unrelated cwd                                  PASS
external symlink invocation                    PASS
subprocess re-entry                            PASS
uv venv                                        PASS
clean venv launch                              PASS
venv identity                                  PASS
uv run                                         PASS
```

This summary is evidence for `docs/stages/STAGE2_FINAL.md`.
