# Gate 3 System-Python Integration Contract

> **Status:** CONTRACT FROZEN

## Canonical product selection

The supported exact selector is the absolute installed interpreter path:

```text
<installed-prefix>/bin/python
```

For `uv python find`, use system-only, download-disabled selection and verify the returned realpath and Python metadata. For `uv venv`, pass the same absolute interpreter with downloads and managed fallback disabled.

This contract is product-exact across CPython 3.14.5 and 3.14.6, all four frozen topologies, whole-prefix relocation, and both accepted transition directions. After transition, the path can stay the same but its exact product identity must be reprobed.

## Secondary and conditional forms

Install-directory requests and unique executable names are accepted only in a controlled system search environment. PATH `python3.14`, request `3.14`, `.python-version`, and `requires-python` are conditional compatibility selection surfaces, not patch-exact product selectors. They require exactly one eligible project product and explicit metadata verification.

An active virtual environment can outrank system discovery. `--system` is required when ambient virtual-environment selection is not intended. The first compatible system candidate can win PATH precedence, so two simultaneously exposed 3.14 products make a minor-version-only request non-deterministic with respect to patch identity.

## Deferred surfaces

Gate 2 did not execute `uv run` or `uv sync`; they are not accepted here. Global `python`/`python3` links, shell edits, unrestricted ambient PATH policy, uv-managed installation metadata, Android placement in `UV_PYTHON_INSTALL_DIR`, Python downloads, and uv patching remain prohibited or unaccepted.

## Gate 4 obligation

Gate 4 must validate 48 scenarios, including explicit `uv run` and `uv sync` candidates, transition continuity, bounded secondary discovery, precedence, download/managed-negative controls, and repository/product/global invariants. PASS and FAIL evidence must both be safely archived.
