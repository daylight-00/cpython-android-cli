# Stage 3-B Phase 5 Promoted Boundary Equivalence

> **Status:** Selected target evidence
> **Execution host:** Termux on Android arm64
> **Candidate:** `work/termux/stage3b-promoted-runtime/prefix`
> **Frozen control:** `work/termux/stage2c/runtime/prefix`
> **Result:** PASS

## Purpose

This document records the corrected CA trust and timezone-data boundary comparison between the promoted Stage 3-B runtime and the frozen Stage 2-C runtime.

The comparison was run only after two probe-contract defects were repaired:

```text
CA fresh-process child
  old: python -I -S -c ...
  new: python -I -B -S -c ...

zoneinfo fresh-process child
  old: python -I -c ...
       while testing PYTHONTZPATH
  new: sanitized Python environment
       + python -B -P -s -c ...
```

The corrected zoneinfo child records the actual `PYTHONTZPATH` value, `zoneinfo.TZPATH`, interpreter isolation flags, first-party `tzdata` visibility, and per-key results.

## Command

```sh
rm -rf \
  results/termux/stage3b-promoted-boundaries

bash \
  experiments/stage3b-target-validation/validate-promoted-boundaries.sh
```

## Machine verdict

The combined verifier reported:

```text
schema_version       1
check_count         28
failed_checks       []
missing_outputs     []
parse_errors        {}
pass                true
```

All six component workflows exited with status `0`:

```text
candidate  ca-boundary          0
candidate  zoneinfo-boundary    0
candidate  uv-tzdata-fallback   0
frozen     ca-boundary          0
frozen     zoneinfo-boundary    0
frozen     uv-tzdata-fallback   0
```

## CA trust contract

The candidate and frozen control produced the same four-scenario matrix.

```text
clean_default
  resolved SSL_CERT_FILE     Termux CA
  HTTPS                      PASS 200

explicit_termux_ca
  resolved SSL_CERT_FILE     Termux CA
  HTTPS                      PASS 200

missing_file_repair
  resolved SSL_CERT_FILE     Termux CA
  HTTPS                      PASS 200

existing_empty_file
  resolved SSL_CERT_FILE     empty regular-file control
  HTTPS                      FAIL as expected
  return code                4
```

The tested Termux CA file existed at:

```text
/data/data/com.termux/files/usr/etc/tls/cert.pem
```

Machine checks:

```text
candidate_ca_contract       true
frozen_ca_contract          true
ca_semantic_equivalence     true
```

Conclusion:

> The promoted launcher preserves the frozen path-level CA policy: unset or missing `SSL_CERT_FILE` is repaired to the Termux CA bundle, an explicit usable Termux CA path is preserved, and an existing regular but unusable file is also preserved rather than semantically replaced.

## Corrected direct-zoneinfo scenarios

The child contract was observed exactly as designed:

```text
child arguments
  -B -P -s -c

flags
  dont_write_bytecode = true
  isolated            = 0
  no_user_site         = 1
  safe_path            = true
```

### Default scenario

Observed input:

```text
PYTHONTZPATH unset
```

Observed `zoneinfo.TZPATH`:

```text
/usr/share/zoneinfo
/usr/lib/zoneinfo
/usr/share/lib/zoneinfo
/etc/zoneinfo
```

All four paths were absent. The first-party `tzdata` package was not visible.

```text
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

### Package-only scenario

Observed input:

```text
PYTHONTZPATH=""
```

Observed:

```text
zoneinfo.TZPATH      []
tzdata visible       false
UTC                  FAIL
Asia/Seoul           FAIL
America/New_York     FAIL
```

This corrected run now establishes that the empty environment value was actually consumed and produced package-only lookup.

The failure means only that the base runtime does not include the first-party `tzdata` package.

### Explicit Termux-path scenario

Observed input:

```text
PYTHONTZPATH=/data/data/com.termux/files/usr/share/zoneinfo
```

Observed `zoneinfo.TZPATH`:

```text
/data/data/com.termux/files/usr/share/zoneinfo
```

The path did not exist on the tested host and all representative keys failed.

This corrected run establishes that the explicit path was actually delivered to the child. It does not claim that no Termux package can ever provide that directory.

## Zoneinfo equivalence

Candidate and frozen runtime matched for:

```text
child argument contract
interpreter flags
actual PYTHONTZPATH delivery
zoneinfo.TZPATH
host-path existence state
tzdata visibility
representative key results
```

Machine checks:

```text
zone_child_contract             true
zone_semantic_equivalence       true
candidate_zone_input_*          true
frozen_zone_input_*             true
candidate_zone_flags_*          true
frozen_zone_flags_*             true
```

Conclusion:

> The promoted runtime preserves the frozen base-runtime timezone-data boundary on the tested Termux host. Neither base runtime has a usable built-in or host TZif source in the tested state.

## First-party tzdata fallback

The uv ephemeral fallback supplied:

```text
tzdata 2026.3
PYTHONTZPATH=""
```

For both candidate and frozen runtime:

```text
tzdata visible          true
zoneinfo.TZPATH         []
UTC                     PASS
Asia/Seoul              PASS
America/New_York        PASS
all_keys_pass           true
```

The uv environment preserved the expected base runtime identity:

```text
candidate uv sys.base_prefix
  work/termux/stage3b-promoted-runtime/prefix

frozen uv sys.base_prefix
  work/termux/stage2c/runtime/prefix
```

Machine checks:

```text
candidate_uv_tzdata_pass          true
frozen_uv_tzdata_pass             true
uv_tzdata_semantic_equivalence    true
candidate_uv_base_prefix          true
frozen_uv_base_prefix             true
```

Conclusion:

> The first-party Python `tzdata` fallback solves the tested `zoneinfo` data gap for both runtime products without installing data into either base prefix.

## Mutation controls

Both runtime fingerprints remained unchanged across all CA, direct-zoneinfo, and uv-tzdata workflows.

```text
candidate_runtime_not_mutated    true
frozen_runtime_not_mutated       true
```

This closes the validation-hygiene risk found during the earlier closure probe incident.

## Final markers

```text
CA_BOUNDARY_EQUIVALENCE=PASS
ZONEINFO_BOUNDARY_EQUIVALENCE=PASS
TZDATA_FALLBACK_EQUIVALENCE=PASS
CANDIDATE_RUNTIME_MUTATION_CHECK=PASS
FROZEN_RUNTIME_MUTATION_CHECK=PASS
STAGE3B_PROMOTED_BOUNDARIES=PASS
```

## Claim boundary

The result proves equivalence on the tested Termux/Android host state. It does not choose the later distribution policy for CA or timezone data.

Still deferred to Stage 3-C:

```text
whether a CA bundle is bundled or host-integrated
whether tzdata is bundled, declared, or host-integrated
version/update policy for data packages
cross-device and cross-Android-version portability
```

## Conclusion

Gate 3 is closed:

```text
promoted CA boundary equivalence          PASS
corrected direct-zoneinfo equivalence     PASS
first-party tzdata fallback equivalence   PASS
candidate mutation control                PASS
frozen mutation control                   PASS
machine-readable combined verdict         PASS
```

The remaining Phase 5 gate is production-shape whole-prefix relocation of the promoted runtime.
