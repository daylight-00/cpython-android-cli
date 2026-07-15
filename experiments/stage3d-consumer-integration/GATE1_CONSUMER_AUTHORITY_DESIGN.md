# Stage 3-D Gate 1: Consumer Authority Design

> **Status:** DESIGN FROZEN
> **Claim:** the next target gate is a read-only uv system-Python discovery census over the exact frozen products and topologies

## Authority boundary

The project already proves that an explicit absolute interpreter path works with uv workflows. Gate 1 keeps that path as the control and asks whether less explicit system-Python discovery surfaces are stable enough to become an integration contract.

uv terminology matters:

```text
managed Python
  installed by uv

system Python
  every other discovered Python installation
```

The project products are system Pythons unless and until a separate managed-provider authority is proved. Their Android target must not be relabeled as an upstream Linux distribution.

## Selected first target gate

Gate 2 is observational and non-mutating. It runs 64 bounded scenarios across:

```text
products
  CPython 3.14.5
  CPython 3.14.6

topologies
  runtime-only
  runtime+development
  runtime+test
  full

selection families
  explicit path controls
  natural discovery
  project selection
  precedence and negative controls
  transition continuity
```

The census records what uv actually selects. It does not decide that a successful accidental discovery is a supported product contract.

## System-first decision

System-Python integration is selected first because:

1. explicit interpreter paths are already part of the frozen runtime evidence;
2. uv officially supports path, executable-name, install-directory, PATH, version, and project requests for system interpreters;
3. downloads can be disabled, preventing an unsupported managed fallback from hiding discovery failure;
4. uv's managed CPython distribution model is tied to its bundled downloadable distributions, while Android is outside the documented platform tiers;
5. observing before installing links or provider metadata preserves the non-reopening rule.

## Mutation boundary

Allowed:

```text
isolated temporary directories
temporary PATH overlays containing links inside the fixture
temporary .python-version and pyproject.toml files
temporary venvs and uv caches
read-only inspection of installed product and registry state
frozen upgrade/downgrade transitions inside a disposable installation fixture
```

Forbidden:

```text
writing `$PREFIX/bin/python*`
editing shell startup files
placing product bytes in uv's managed installation directory
running uv python install/upgrade/uninstall against the project product
patching uv
changing canonical installation registry or product manifests
network fallback for Python acquisition
using proot, root, Shizuku, or Docker
```

## Decision outputs expected from Gate 2

Gate 2 must produce evidence, not a final integration choice. Gate 3 will decide among these possible surfaces only after the census:

```text
explicit absolute path only
product-prefix executable names
opt-in PATH shim directory
installer-created versioned link
project-local .python-version guidance
configuration-only system preference
no natural-discovery integration
```

Global unversioned links and managed-Python emulation require independent justification and are not default candidates.

## Frozen provenance

```text
Gate 4E commit
  68b67dcc3b65872e1034c487747d3fcd1ad5a319

Gate 4E tree
  2115f6fa3b923c9fcf21a1b8343cb6149afb6cc7

Gate 4D v1
  ef24baca1f01d3e106825fb99e537d68ba0beffa9cd4e92577e43bd35421e77c

Gate 4D corrective v2
  98ab810732dd2eb35bff9180dcb8fa1ec872eb09103d58670edb481cc9e3e5b2

final Gate 4 matrix
  66/66 PASS
```

## Not proved

This design does not prove any Termux discovery result, link policy, managed-Python compatibility, provider metadata, or target integration behavior.
