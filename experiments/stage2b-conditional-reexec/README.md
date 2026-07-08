# Stage 2-B: Conditional Re-exec and Relocation

> **Status:** Complete.
> **Result:** PASS.
> **Selected design:** R2 conditional self re-exec.

Stage 2-B refined the Stage 2-A self-reexec strategy into a fixed-point launcher that avoids redundant re-exec in prepared subprocesses.

## R2 policy

```text
discover /proc/self/exe
        |
derive prefix/lib
        |
is prefix/lib already an LD_LIBRARY_PATH component?
        |
        +-- no
        |    normalize environment
        |    configure CA
        |    execv(actual executable, original argv)
        |
        +-- yes
             normalize duplicate required entries
             repair/discover CA if needed
             run B0 PyConfig directly
```

This gives:

- clean top-level launch: one re-exec,
- inherited subprocess with the correct loader environment: zero re-execs,
- wrong or missing required native path: repair and one re-exec,
- wrong or nonexistent CA path: repair without re-exec when the loader path is already ready,
- duplicate required path components: normalized to one occurrence.

## Main validation result

The final validator covered:

- `clean`,
- `ready`,
- `wrong-ld`,
- `wrong-ca`,
- `duplicate`,
- unrelated working directory,
- external symlink invocation,
- subprocess re-entry,
- uv venv,
- clean launch through the venv interpreter,
- venv identity,
- uv run.

All tested areas passed.

The canonical validator in this directory is:

```sh
./stage2b-validate.sh
```

## Relocation result

`stage2b-relocation.sh` validated the runtime at location A, moved the whole prefix to location B, and repeated:

- native imports,
- HTTPS,
- subprocess re-entry,
- uv venv creation,
- clean venv launch,
- uv run.

All tests passed at both locations.

The validated claim is:

> The tested runtime prefix can be relocated as a unit, and R2 re-derives its native runtime path from the actual executable location.

The test did **not** prove that an external venv created before moving its base runtime remains usable after that base-runtime move.

## Historical workspace note

The original experiment was run under `~/tmp/260704/stage2b`. The historical build and preparation scripts retain parts of that path model. Stage 2-C provides the current repo-wide build, sync, assembly, and smoke workflows.
