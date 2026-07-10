# Stage 3-A: Runtime Closure Census

> **Status:** FROZEN
> **Parent scope:** `docs/stages/STAGE3_SCOPE.md`
> **Final synthesis:** `docs/stages/STAGE3A_FINAL.md`
> **Input architecture:** frozen Stage 2 R2 + B0 runtime

## Question

> What exactly is the runtime closure of the frozen Stage 2 interpreter, and which native, host, metadata, and data-source boundaries are internal, Android-provided, Termux-provided, or external?

## Principle

Stage 3-A was observational first.

The experiment did not begin by:

```text
patching ELF files
rewriting RUNPATH
removing runtime files
installing packages into the frozen runtime prefix
changing launcher behavior
```

It inspected the already-validated Stage 2-C assembled runtime and introduced negative controls and non-mutating consumer-environment probes where needed.

## Input

Default runtime prefix:

```text
work/termux/stage2c/runtime/prefix
```

Default result root:

```text
results/termux/stage3a-runtime-closure/
```

## Experiment phases

### 1. Complete runtime and ELF inventory

```text
inventory-runtime.sh
inventory-runtime.py
```

Outputs include:

```text
files.tsv
symlinks.tsv
elf-objects.tsv
elf-needed.tsv
python-runtime.json
closure-classification.tsv
unresolved.tsv
errors.tsv
summary.json
mutation-check.txt
```

Observed:

```text
file entries             3280
ELF objects                 81
DT_NEEDED edges            329
unresolved edges              0
mutation check            PASS
```

### 2. Closure aggregation and Android SONAME loadability

```text
analyze-closure.py
probe-system-sonames.py
analyze-and-probe.sh
```

Observed:

```text
9 unique needed SONAMEs
  4 RUNTIME_INTERNAL
  5 ANDROID_SYSTEM

5/5 Android-system SONAME loadability probes PASS
```

### 3. Extension import sweep

```text
probe-extension-imports.py
probe-extension-imports.sh
```

Observed:

```text
67 candidates
67 PASS
0 FAIL
```

The probe discovered the active extension directory from runtime state instead of trusting stale `DESTSHARED` metadata.

### 4. Sysconfig path census and classification

```text
probe-sysconfig-paths.py
probe-sysconfig-paths.sh
analyze-sysconfig-paths.py
analyze-sysconfig-paths.sh
triage-sysconfig-paths.py
triage-sysconfig-paths.sh
classify-missing-sysconfig-paths.py
classify-missing-sysconfig-paths.sh
```

Extractor v2 result:

```text
absolute path records                 179
BUILD_PREFIX_RESIDUE                   25
OTHER_ABSOLUTE                         97
RUNTIME_PREFIX                         56
ANDROID_SYSTEM                          1
```

Missing OTHER path classification:

```text
91 records
27 unique paths
UNKNOWN=0
```

Categories:

```text
BUILD_WORKSPACE_RESIDUE
TOOLCHAIN_RESIDUE
USER_SCHEME_DESTINATION
HOST_BUILD_TOOL_RESIDUE
TZDATA_SEARCH_PATH_METADATA
```

### 5. Timezone-data boundary

```text
probe-zoneinfo-boundary.py
probe-zoneinfo-boundary.sh
probe-zoneinfo-with-tzdata.py
probe-zoneinfo-with-uv-tzdata.sh
```

Observed:

```text
base default TZPATH            FAIL
base tzdata fallback           FAIL: package absent
Termux zoneinfo path           FAIL: path absent
uv ephemeral tzdata fallback   PASS
```

### 6. CA trust boundary

```text
probe-ca-boundary.py
probe-ca-boundary.sh
```

Observed:

```text
clean_default          PASS
explicit_termux_ca     PASS
missing_file_repair    PASS
existing_empty_file    FAIL
```

The final interpretation is path-level CA repair, not trust-store content validation.

### 7. Representative runtime audit

```text
probe-runtime-audit-boundary.py
probe-runtime-audit-boundary.sh
```

Exact observed path and special-event rows were reviewed and classified.

No exact observed row remained semantically unknown.

The probe is not a complete syscall trace.

### 8. Final production reconfirmation

Canonical smoke:

```text
bash scripts/test/smoke-termux.sh
```

Observed:

```text
STAGE2C_SMOKE=PASS
```

Production relocation:

```text
reconfirm-production-relocation.sh
```

Observed:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

## Frozen result

```text
STAGE3A=FROZEN
```

Authoritative synthesis:

```text
docs/stages/STAGE3A_FINAL.md
```

Selected evidence:

```text
docs/evidence/STAGE3A_CLOSURE_PHASE1_SUMMARY.md
docs/evidence/STAGE3A_EXTENSION_IMPORT_SUMMARY.md
docs/evidence/STAGE3A_SYSCONFIG_PATH_CENSUS_SUMMARY.md
docs/evidence/STAGE3A_SYSCONFIG_PATH_ANALYSIS_SUMMARY.md
docs/evidence/STAGE3A_SYSCONFIG_MISSING_PATH_CLASSIFICATION.md
docs/evidence/STAGE3A_SYSCONFIG_CLASSIFIER_RESULT.md
docs/evidence/STAGE3A_ZONEINFO_BOUNDARY_SUMMARY.md
docs/evidence/STAGE3A_TZDATA_FALLBACK_SUMMARY.md
docs/evidence/STAGE3A_CA_BOUNDARY_SUMMARY.md
docs/evidence/STAGE3A_RUNTIME_AUDIT_BOUNDARY_SUMMARY.md
docs/evidence/STAGE3A_RUNTIME_AUDIT_EXACT_ROW_REVIEW.md
docs/evidence/STAGE3A_FINAL_RECONFIRMATION_SUMMARY.md
```

## Handoff

The next active sub-stage is:

```text
Stage 3-B
Reproducible build-input promotion
```

See:

```text
docs/stages/STAGE3B_SCOPE.md
```
