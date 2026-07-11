# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** ACTIVE — target execution pending
> **Input:** frozen Stage 3-B promoted runtime
> **Gate:** complete semantic role classification with `UNKNOWN=0`

## Question

> Which exact paths in the frozen promoted product are runtime, development, metadata, license, or optional/debug surfaces before an archive split is selected?

## Run

On Termux:

```sh
git pull --ff-only

bash \
  experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

Default input:

```text
work/termux/stage3b-promoted-runtime/prefix
```

Default output:

```text
results/termux/stage3c-phase1-role-inventory
```

The frozen Stage 3-B entry-count contract is `3155`. To deliberately inspect a changed candidate without asserting that contract, pass an explicit override and treat the result as new evidence rather than Stage 3-C acceptance:

```sh
EXPECTED_ENTRY_COUNT=<reviewed-count> \
  bash experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

## Roles

```text
RUNTIME
DEVELOPMENT
METADATA
LICENSE
DEBUG_OR_OPTIONAL
UNKNOWN
```

The first hard gate is:

```text
UNKNOWN=0
```

## Rule model

The classifier uses ordered, explicit rules. Important examples:

```text
ELF objects                          -> RUNTIME
bin/ entry points                    -> RUNTIME
Python stdlib and extension tree     -> RUNTIME
installed test/demo/GUI trees        -> DEBUG_OR_OPTIONAL
include/ headers                     -> DEVELOPMENT
static libraries                     -> DEVELOPMENT
pkg-config surfaces                  -> DEVELOPMENT
config development surface           -> DEVELOPMENT
sysconfig/build-details surfaces      -> METADATA
license/copying/notice paths          -> LICENSE
unmatched paths                       -> UNKNOWN
```

All rule identifiers and descriptions are emitted to `rules.tsv`.

## Directory model

Directories can contain more than one semantic role. Each directory records:

```text
role
  minimum archive-owner role

descendant_roles
  complete role set below the directory

mixed_directory
  true when descendant roles are mixed
```

This keeps shared directory ownership explicit without pretending all children have one role.

## Outputs

```text
product-role-inventory.tsv
unknown.tsv
mixed-directories.tsv
rules.tsv
role-summary.json
mutation-check.txt
classifier.log
verifier.log
verification.json
```

`product-role-inventory.tsv` includes:

```text
path
type
mode
size
mtime_ns
sha256
symlink_target
elf
role
rule_id
reason
descendant_roles
mixed_directory
```

## Non-mutation contract

The promoted tree is fingerprinted before and after the census using path, type, mode, size, mtime, regular-file SHA-256, and symlink target.

The classifier and verifier run under the promoted interpreter as:

```text
python -I -B -S
```

No bytecode may be written into the candidate.

## Independent verifier

The verifier checks 32 conditions, including:

```text
all required outputs exist and parse
inventory schema is exact
entry count is 3155
paths are unique
role and type counts match summary
UNKNOWN count is zero
all ELF entries are RUNTIME
no pycache/pyc paths exist
no unsupported special files exist
manifest SHA-256 recomputes
candidate before/after fingerprints match
required runtime/development anchors exist
classifier and verifier verdicts agree
```

Required anchors:

```text
bin/python3.14                     RUNTIME
bin/python                         RUNTIME
bin/python3                        RUNTIME
lib/libpython3.14.so               RUNTIME
include/python3.14/Python.h        DEVELOPMENT
include/python3.14/pyconfig.h      DEVELOPMENT
```

## Expected final markers

```text
STAGE3C_PRODUCT_ROLE_CLASSIFIER=PASS
PRODUCT_ROLE_UNKNOWN_ZERO=PASS
PRODUCT_ROLE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ROLE_INVENTORY=PASS
```

A failure is retained as evidence. Do not add broad fallback rules merely to force `UNKNOWN=0`; review exact unknown paths and assign a justified semantic rule.
