# Stage 3-D Scope: Consumer Integration

> **Status:** ACTIVE — Gate 1 scope and authority design frozen
> **Input:** frozen Stage 3-C Gate 4E exact two-product transition authority
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv using the installed interpreter as a system Python
> **Optional research:** uv-managed-Python-style integration, explicitly deferred

## 1. Stage question

> How should the frozen installed CPython products be exposed to uv and ordinary Termux consumers without misrepresenting Android as a supported upstream Linux managed-Python distribution or reopening the runtime, archive, ownership, and transition contracts?

Stage 3-D consumes the exact CPython 3.14.5 and 3.14.6 products and the four frozen installed topologies:

```text
runtime-base
runtime-base + development-addon
runtime-base + test-addon
runtime-base + development-addon + test-addon
```

The first integration authority is the **system-Python path**. uv defines every Python installation that uv did not install itself as a system Python, including installations managed by other tools. The already-frozen explicit absolute interpreter path remains the canonical control.

## 2. Why managed-Python integration is not the first gate

Current upstream uv documentation describes managed CPython distributions as bundled downloadable distributions for macOS, Linux, and Windows, sourced from `python-build-standalone`. Android is not listed in uv's platform-support tiers. Therefore this project must not make an Android archive look like an upstream Linux uv-managed distribution merely by copying files into `UV_PYTHON_INSTALL_DIR` or imitating a directory name.

The first gates observe and define supported system-Python discovery behavior. Managed-Python feasibility is a separate optional research boundary after system integration is frozen.

Primary upstream references, reviewed 2026-07-15:

```text
https://docs.astral.sh/uv/concepts/python-versions/
https://docs.astral.sh/uv/reference/policies/platforms/
```

## 3. Frozen Gate 1 decisions

```text
canonical baseline
  explicit absolute interpreter path

primary integration model
  uv system Python

D1 mutations
  none outside isolated temporary fixtures

network/download policy
  automatic Python downloads disabled
  no managed download may satisfy a system-integration scenario

accepted discovery surfaces for census
  executable path
  executable name
  install directory
  PATH names python, python3, python3.14
  version and implementation requests
  .python-version
  project requires-python
  uv python find
  uv venv / uv run / uv sync

product coverage
  CPython 3.14.5 and 3.14.6

installed-topology coverage
  all four frozen topologies

transition coverage
  discovery before and after both frozen transition directions

managed-Python status
  deferred research, not an accepted integration mode
```

## 4. Gate sequence

```text
Gate 1  scope and consumer authority design             FROZEN
Gate 2  read-only Termux consumer discovery census      pending
Gate 3  system-Python integration contract              pending
Gate 4  target implementation and validation            pending
Gate 5  independent consumer-integration freeze         pending
Gate 6  optional managed-Python feasibility research    deferred
```

Gate 2 must observe actual uv behavior before Gate 3 chooses any names, links, configuration, or installer integration.

## 5. Gate 2 evidence requirements

The census must record exact identities for:

```text
uv executable, version, package/source origin
Termux package environment and PATH
installed product and topology
interpreter path, mode, inode, and symlink chain
uv request and preference flags
UV_PYTHON_INSTALL_DIR and relevant config environment
stdout, stderr, exit code
selected interpreter realpath
queried Python implementation/version/platform metadata
repository and installation pre/post state
```

Each scenario must be isolated. It may create temporary project directories and virtual environments, but it must not alter global shell files, `$PREFIX/bin`, uv's managed installation directory, canonical product archives, the installed ownership registry, or the transition journal.

## 6. Gate 2 matrix

The tracked matrix contains 64 scenarios:

```text
explicit-path controls          8
natural discovery              32
project selection               8
precedence and negative        12
transition continuity           4
                               --
total                          64
```

All requests run with Python downloads disabled. Scenarios that study managed precedence may use inert decoys only; they do not register or install an Android managed distribution.

## 7. Non-reopening rules

Stage 3-D must not silently change:

```text
launcher and PyConfig architecture
runtime archive bytes or manifests
artifact ownership and addon dependencies
registry schema 1
transaction journal schema 2
Gate 4 transition behavior
host CA and tzdata policies
canonical source/build provenance
```

Any required change to those authorities is a new explicit intervention, not consumer integration.

## 8. Explicitly unaccepted claims

Gate 1 does not prove:

```text
natural discovery on Termux
safe global python/python3 links
uv-managed Android distribution support
uv python install/upgrade/uninstall support
custom download mirrors or provider metadata
third-product support
multi-ABI or multi-API support
consumer behavior outside the exact tested uv build
```

## 9. Gate 1 records

```text
experiments/stage3d-consumer-integration/GATE1_CONSUMER_AUTHORITY_DESIGN.md
experiments/stage3d-consumer-integration/gate1-consumer-authority.json
experiments/stage3d-consumer-integration/gate2-consumer-discovery-matrix.json
experiments/stage3d-consumer-integration/verify-gate1-consumer-authority-design.py
```
