# Stage 3-A: Runtime Closure Census

> **Status:** ACTIVE
> **Parent scope:** `docs/stages/STAGE3_SCOPE.md`
> **Input architecture:** frozen Stage 2 R2 + B0 runtime

## Question

> What exactly is the runtime closure of the frozen Stage 2 interpreter, and which native dependencies are internal, Android-provided, Termux-provided, or unresolved?

## Principle

The first Stage 3 experiment is observational.

It must not:

```text
patch ELF files
rewrite RUNPATH
move runtime files
remove files
install packages into the runtime prefix
change launcher behavior
```

It should inspect the already-validated Stage 2-C assembled runtime.

## Input

Default runtime prefix:

```text
work/termux/stage2c/runtime/prefix
```

Default output:

```text
results/termux/stage3a-runtime-closure/
```

## Run

From the repository root on Termux:

```sh
bash experiments/stage3a-runtime-closure/inventory-runtime.sh
```

Override paths when needed:

```sh
RUNTIME_PREFIX=/path/to/prefix \
OUTPUT_DIR=/path/to/results \
bash experiments/stage3a-runtime-closure/inventory-runtime.sh
```

## Outputs

```text
files.tsv
  complete runtime-prefix file inventory

symlinks.tsv
  symlink paths and targets

elf-objects.tsv
  per-ELF identity and dynamic metadata

elf-needed.tsv
  one row per DT_NEEDED edge

python-runtime.json
  Python runtime identity and selected sysconfig values

closure-classification.tsv
  initial provider classification for each DT_NEEDED edge

unresolved.tsv
  DT_NEEDED edges with no identified provider

errors.tsv
  inspection tool failures, if any

summary.json
  counts and classification totals

mutation-check.txt
  before/after runtime tree fingerprints
```

## Initial classification model

```text
RUNTIME_INTERNAL
  provider identified inside runtime prefix

ANDROID_SYSTEM
  candidate provider file identified under Android system/APEX library roots

TERMUX_HOST_INTEGRATION
  candidate provider identified under the Termux prefix library tree

UNRESOLVED
  no provider identified by the initial census
```

The initial census is a provider inventory, not a proof of Android linker-namespace accessibility. A later Stage 3-A step must validate questionable provider edges against actual load behavior where necessary.

## Non-mutation requirement

The harness computes a content-oriented runtime tree fingerprint before and after inventory.

Expected:

```text
MUTATION_CHECK=PASS
```

The runtime Python is invoked with bytecode writes disabled and an external pycache location.

## Acceptance

Stage 3-A is not complete merely because the script runs.

Completion requires review of:

```text
all runtime files
all ELF objects
all DT_NEEDED edges
all UNRESOLVED edges
all TERMUX_HOST_INTEGRATION edges
all ANDROID_SYSTEM classifications that require namespace validation
Python runtime identity
Stage 2-C smoke after census
whole-prefix relocation after census tooling
```
