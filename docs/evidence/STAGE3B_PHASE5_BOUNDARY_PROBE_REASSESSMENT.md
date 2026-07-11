# Stage 3-B Phase 5 Boundary Probe Reassessment

> **Status:** Probe-contract correction and next-gate design
> **Scope:** CA trust and timezone-data boundary validation
> **Result:** CA mutation control repaired; zoneinfo environment control reopened and repaired

## Trigger

After Gate 2 closure equivalence passed, the next planned Phase 5 gate was reuse of the Stage 3-A CA and timezone probes against the promoted candidate.

Before running those probes, their fresh-process contracts were reviewed in light of the earlier bytecode-mutation incident.

That review found two distinct issues.

## CA probe: bytecode-write risk

The CA child used:

```text
python -I -S -c ...
```

The shell wrapper supplied:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONPYCACHEPREFIX=<results>
```

Because `-I` ignores `PYTHON*` environment variables, the child could write bytecode into the tested runtime tree.

The CA semantics themselves remain valid because the variables under test are:

```text
SSL_CERT_FILE
SSL_CERT_DIR
```

They are not `PYTHON*` variables and are not suppressed by isolated mode.

Repair:

```text
python -I -B -S -c ...
```

This preserves isolated import behavior and makes the no-bytecode contract explicit.

## Zoneinfo probe: invalid environment-control contract

The zoneinfo child used:

```text
python -I -c ...
```

while the scenarios attempted to control:

```text
default
  PYTHONTZPATH unset

tzdata_only
  PYTHONTZPATH=""

termux_zoneinfo
  PYTHONTZPATH=$PREFIX/share/zoneinfo
```

This is internally contradictory.

CPython isolated mode implies environment isolation and ignores all `PYTHON*` variables. Therefore the child did not consume the `PYTHONTZPATH` scenario input.

The previous result still supports these observations:

```text
default runtime lookup failed
$PREFIX/share/zoneinfo was absent at the host filesystem check
uv-injected first-party tzdata fallback passed
```

However, these two direct scenario claims were not independently established by the old child process:

```text
PYTHONTZPATH="" forced package-only lookup
PYTHONTZPATH=$PREFIX/share/zoneinfo forced Termux-path lookup
```

They are reopened rather than silently rewritten.

## Corrected zoneinfo isolation model

The repaired probe cannot use `-I` or `-E`, because the variable under test is itself a `PYTHON*` variable.

Instead it uses:

```text
python -B -P -s -c ...
```

and constructs a sanitized child environment:

```text
remove all ambient PYTHON* variables
set PYTHONNOUSERSITE=1
apply only the scenario-specific PYTHONTZPATH value
```

Contract:

```text
-B
  prohibit .pyc writes explicitly

-P
  do not prepend a potentially unsafe current/script path

-s
  exclude user site-packages

no -I / no -E
  preserve the deliberate PYTHONTZPATH input
```

The child output now records:

```text
observed PYTHONTZPATH
zoneinfo.TZPATH
path existence
first-party tzdata visibility
interpreter flags
per-key results
```

This makes the scenario input itself machine-verifiable.

## uv tzdata fallback hardening

The uv fallback probe now exports:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONNOUSERSITE=1
PYTHONSAFEPATH=1
PYTHONTZPATH=""
UV_PYTHON_DOWNLOADS=never
```

The fallback remains an ephemeral consumer-environment test and does not install `tzdata` into either runtime prefix.

## Gate 3 comparison model

The new workflow runs the same corrected probes against:

```text
candidate
  work/termux/stage3b-promoted-runtime/prefix

frozen control
  work/termux/stage2c/runtime/prefix
```

under the same Termux host state.

It validates:

```text
CA contract against the frozen expected matrix
CA semantic equivalence between candidate and frozen runtime
correct zoneinfo child arguments
actual PYTHONTZPATH delivery in every scenario
zoneinfo semantic equivalence between candidate and frozen runtime
uv first-party tzdata fallback for both runtimes
uv base-prefix identity for both runtimes
candidate tree mutation control
frozen tree mutation control
```

Timezone host availability is not hard-coded from the earlier run. If the Termux host data state has changed, the relevant requirement is that the corrected input is observed and the promoted runtime remains semantically equivalent to the frozen control on the same host.

## Command

```sh
git pull --ff-only

rm -rf \
  results/termux/stage3b-promoted-boundaries

bash \
  experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

Expected final markers:

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

Primary machine-readable verdict:

```text
results/termux/stage3b-promoted-boundaries/promoted-boundary-verification.json
```

## Claim boundary

Before the target run, the current conclusion is limited to:

```text
probe defect identified
repair applied
comparison workflow implemented
real-device Gate 3 result pending
```

No CA or timezone equivalence PASS is claimed until the Termux workflow completes.
