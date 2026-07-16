# Reference: uv Android Status

> **Reviewed:** 2026-07-16

## Primary sources

- Android target issue: https://github.com/astral-sh/uv/issues/14574
- Android development build CI: https://github.com/astral-sh/uv/pull/18333
- Termux dependency compatibility: https://github.com/astral-sh/uv/pull/18324
- Android file-lock behavior: https://github.com/astral-sh/uv/pull/18323
- Draft Android emulator integration: https://github.com/astral-sh/uv/pull/18302

## Observed boundary

uv has merged Android-oriented build and compatibility work and has a draft emulator integration test. The draft test downloads an official CPython Android package, adds a minimal native launcher, and exercises interpreter discovery, virtual environments, package installation, and `uv run`.

That work demonstrates Android Python consumption. It does not yet establish an official Android uv release binary channel or an Android managed-Python catalog equivalent to uv's mainstream platforms.

## Project relevance

Epoch 2 should produce the stable runtime contract that a future uv Android managed-Python entry could consume:

```text
immutable archive
versioned metadata
correct interpreter identity
relocation
venv and pip behavior
Android wheel tags
Termux target qualification
```

Until upstream support exists, the project keeps uv integration explicit, bounded, and downstream-owned.
