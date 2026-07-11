# Stage 3-B Phase 5 Promoted Relocation Fidelity Incident

> **Status:** Active diagnosis checkpoint
> **Execution host:** Termux on Android arm64
> **Functional relocation:** PASS at A and B
> **Source mutation controls:** PASS
> **Relocated-tree strict fingerprint:** FAIL

## Purpose

This document records the first promoted whole-prefix relocation run and preserves the exact claim boundary before any fix is selected.

The run used:

```text
source candidate
  work/termux/stage3b-promoted-runtime/prefix

location A
  work/termux/stage3b-promoted-relocation/location-a/prefix

location B
  work/termux/stage3b-promoted-relocation/location-b/prefix
```

## Functional result

Location A passed:

```text
runtime identity re-rooted at A
active sysconfig paths re-rooted at A
HTTPS 200
child interpreter identity re-rooted at A
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
```

Location B passed after the complete A prefix was moved to B:

```text
runtime identity re-rooted at B
active sysconfig paths re-rooted at B
HTTPS 200
child interpreter identity re-rooted at B
fresh uv venv PASS
venv base-prefix identity PASS
uv run PASS
uv run base-prefix identity PASS
old A prefix absent from active assertions
```

Observed markers:

```text
LOCATION_RECONFIRM[A]=PASS
LOCATION_RECONFIRM[B]=PASS
STALE_A_PREFIX_RUNTIME_ASSERTIONS=PASS
STAGE3A_PRODUCTION_RELOCATION_RECONFIRM=PASS
```

The uv hardlink warning was the already-reviewed fallback-to-copy performance warning. Both package installation and consumer validations completed.

## Machine verdict

The promoted verifier reported:

```text
check_count       16
passed checks     15
failed checks      1
missing_outputs   []
parse_errors      {}
```

Only this check failed:

```text
relocated_runtime_matches_source=false
```

All other checks passed, including:

```text
relocation_workflow_exit_zero
location A marker and path checks
location B marker and path checks
stale A-prefix marker
A absent after move
B present with executable Python
candidate source not mutated
frozen control not mutated
```

## Observed fingerprints

Canonical promoted candidate:

```text
before
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

after
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

pass=true
```

Frozen Stage 2-C control:

```text
before
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e

after
  5a14f213bbf069b844a799615ed2b87eb34b48b4251b0a48bf431337e929ce0e

pass=true
```

Relocated B versus canonical candidate:

```text
candidate source
  834f7aeb2e5266f027b6ee43dd77255079b2e01cf049dad56fda5ef39ce048b0

relocated B
  6d881c82e21eaf009aba70a9b68c867a2efa0b9ed14256c4e1cddf79a6246744

pass=false
```

## What this proves

The result proves:

```text
promoted runtime execution relocates successfully
consumer identities re-root at A and B
stale A runtime paths are absent from tested active state
canonical promoted candidate remained unchanged
frozen Stage 2-C control remained unchanged
strict metadata-sensitive source/B fingerprints differ
```

## What this does not yet prove

The result does not yet identify whether the source/B mismatch is:

```text
validation-induced added or removed paths
regular-file content mutation
regular-file metadata mutation
symlink change
directory mtime mutation
directory inode-size difference introduced by cp -a
another filesystem metadata effect
```

The prior fingerprint included `%s` for every entry, including directories. Directory `st_size` is filesystem allocation metadata and is not guaranteed to be reproducible in a copied tree even when paths and file contents are equivalent.

Therefore the failure must not yet be classified as either:

```text
product relocation defect
or
false-positive fingerprint contract defect
```

## Read-only diagnosis

The retained B tree must not be deleted before running:

```sh
CANDIDATE="$PWD/work/termux/stage3b-promoted-runtime/prefix"
RELOCATED="$PWD/work/termux/stage3b-promoted-relocation/location-b/prefix"
OUT="$PWD/results/termux/stage3b-promoted-relocation/fidelity-diagnosis"

rm -rf "$OUT"

"$CANDIDATE/bin/python" \
  -I -B -S \
  experiments/stage3b-target-validation/diagnose-promoted-relocation-fidelity.py \
  --source "$CANDIDATE" \
  --relocated "$RELOCATED" \
  --output-dir "$OUT"
```

The diagnostic produces:

```text
source-manifest.jsonl
relocated-manifest.jsonl
tree-delta.json
tree-delta.tsv
```

It reports two comparisons:

```text
strict
  reproduces the previous metadata-sensitive comparison
  includes directory st_size

portable
  ignores directory st_size
  requires path/type/mode/mtime equality
  requires regular-file size and SHA-256 equality
  requires symlink-target equality
```

## Decision rule

```text
portable_pass=true
  -> diagnose prior gate as fingerprint-contract false positive
  -> replace strict directory-size-sensitive fidelity contract
  -> rerun Gate 4 with corrected machine verifier

portable_pass=false
  -> inspect exact added/removed/changed paths and fields
  -> determine which validation step caused the delta
  -> repair validation mutation before rerun
```

## Current conclusion

Gate 4 functional relocation behavior passed, but Phase 5 remains open because the relocated-product fidelity mismatch has not yet been classified.

The next action is evidence extraction from the retained source and B trees, not product cleanup and not an acceptance-policy downgrade.
