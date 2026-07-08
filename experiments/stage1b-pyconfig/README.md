# Stage 1-B: PyConfig Frontend Comparison

> **Status:** Complete and frozen.
> **Selected variant:** B0 / PyConfig auto-discovery.
> **Historical workspace:** the original experiment was run under `~/tmp/260704/stage1b`.

This directory preserves the Stage 1-B comparison that replaced the Stage 1-A `Py_BytesMain` frontend with explicit PyConfig initialization while keeping the Stage 1-A runtime contract unchanged.

## Variants

- `stage1a`: frozen `Py_BytesMain` baseline.
- `b0-auto`: `PyConfig` initialization without overriding `config.home`.
- `b1-home`: the same flow with `config.home` supplied from `CPYTHON_HOME`.

The comparison covered CLI execution modes, common CLI flags, `sys.orig_argv`, `sys.path`, `PYTHONPATH`, subprocess re-entry, exit codes, native stdlib imports, HTTPS, uv venv, venv identity, uv pip, and uv run.

Both B0 and B1 passed the tested functional surface. B1's wrong-home negative control failed hard during startup, proving that explicit `config.home` introduced a real additional dependency. B0 passed without that dependency and was selected.

## Frozen decision

```text
selected:
  B0 / PyConfig auto-discovery

initialization:
  PyConfig_InitPythonConfig
  PyConfig_SetBytesArgv
  Py_InitializeFromConfig
  PyConfig_Clear
  Py_RunMain

not selected:
  B1 / explicit config.home
```

See `docs/stages/STAGE1B_PYCONFIG.md` for the frozen stage document.

## Reproduction note

The scripts in this directory are historical experiment artifacts and some still contain the original date-based workspace assumptions. Stage 2-C introduces the canonical repo-wide workflow under `src/`, `scripts/`, `config/`, and `out/`; the Stage 1-B scripts are retained for experiment provenance rather than as the current project entry point.
