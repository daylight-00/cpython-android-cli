# Stage 2-A: Bootstrap Strategy Comparison

> **Status:** Complete.
> **Outcome:** self re-exec selected for refinement in Stage 2-B.

Stage 2-A compared three strategies for reducing the external Stage 1-B runtime contract.

## Variants

### S2-E: setenv-only control

The launcher self-locates and updates `LD_LIBRARY_PATH` in the process environment without re-exec or a linker-update API.

Observed result:

```text
current process native imports: FAIL
subprocess inheriting prepared environment: PASS
```

This established that changing the environment was useful for future processes but did not repair native dependency loading in the already-running process.

### S2-U: bionic linker update experiment

The launcher attempted to resolve `android_update_LD_LIBRARY_PATH` dynamically and update the running process linker search path.

Observed result on the tested target:

```text
symbol resolution through RTLD_DEFAULT: unavailable
```

The project does not use this strategy.

### S2-R: self re-exec

The launcher:

1. self-locates,
2. prepares `LD_LIBRARY_PATH`,
3. configures `SSL_CERT_FILE`,
4. re-execs the actual executable with the original `argv`,
5. enters the B0 PyConfig frontend.

Observed result:

```text
native stdlib: PASS
HTTPS: PASS
subprocess: PASS
uv venv: PASS
venv native imports: PASS
uv run: PASS
```

S2-R won the comparison and was refined into the R2 fixed-point design in Stage 2-B.

## Historical note

The build and comparison scripts in this directory preserve the original experiment. Some scripts contain the original `~/tmp/260703` and `~/tmp/260704` path assumptions. They are retained as experimental provenance, not as the current Stage 2-C workflow.
