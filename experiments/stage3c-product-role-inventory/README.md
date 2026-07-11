# Stage 3-C Phase 1: Promoted Product Role Inventory

> **Status:** MECHANICAL INVENTORY PASS — semantic decomposition active
> **Input:** frozen Stage 3-B promoted runtime
> **First gate:** complete semantic role classification with `UNKNOWN=0`

## Question

> Which exact paths in the frozen promoted product are runtime, development, metadata, license, or optional/debug surfaces before an archive split is selected?

## Frozen input

```text
work/termux/stage3b-promoted-runtime/prefix
```

```text
entry count      3155
ELF objects        81
symlinks             5
```

## Step 1: complete role inventory — PASS

Run:

```sh
bash \
  experiments/stage3c-product-role-inventory/run-role-inventory.sh
```

Observed:

```text
UNKNOWN                              0
machine verifier                 43/43
source mutation control           PASS
role manifest
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f
```

Role counts:

```text
RUNTIME               711
DEVELOPMENT           449
METADATA                8
LICENSE                 1
DEBUG_OR_OPTIONAL    1986
```

Regular-file bytes:

```text
RUNTIME             38,775,506
DEBUG_OR_OPTIONAL   35,466,620
DEVELOPMENT          4,737,164
METADATA               356,169
LICENSE                  13,804
```

The mechanical gate is closed. The optional bucket remains a policy-review input because its size is close to the runtime payload and it combines tests, demos, GUI modules, and other optional trees.

First-result evidence:

```text
docs/evidence/STAGE3C_PHASE1_ROLE_INVENTORY_FIRST_RESULT.md
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

`UNKNOWN` is a review state, not a distributable role.

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

Observed mixed directories:

```text
lib
lib/python3.14
lib/python3.14/config-3.14-aarch64-linux-android
```

## Step 2: exact role decomposition — ACTIVE

Run after the accepted Step 1 evidence exists:

```sh
bash \
  experiments/stage3c-product-role-inventory/analyze-role-inventory.sh
```

The runner first requires the accepted verifier result:

```text
pass=true
check_count=43
failed_checks=[]
missing_outputs=[]
parse_errors={}
```

It then verifies the frozen inventory identity:

```text
manifest SHA-256
  092ea87eed2a3c800053a0ef480abd8ef836bda8a8890549ce84370eae6e2a0f

entries / ELF / symlinks
  3155 / 81 / 5
```

Outputs added beside the original evidence:

```text
role-overview.tsv
role-by-rule.tsv
role-by-type.tsv
role-by-top-level.tsv
python-subtree-summary.tsv
optional-component-summary.tsv
optional-root-summary.tsv
development-surface-summary.tsv
runtime-surface-summary.tsv
selected-boundary-rows.tsv
largest-regular-files.tsv
role-review.json
role-review.log
```

The decomposition must sum exactly back to the accepted role counts and regular-file bytes. It does not change the original role inventory or the promoted product.

Expected marker:

```text
ROLE_INVENTORY_ACCEPTED_EVIDENCE=PASS
STAGE3C_PHASE1_ROLE_DECOMPOSITION=PASS
```

## Step 1 outputs

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

The classifier, verifier, and decomposition analyzer run under the promoted interpreter as:

```text
python -I -B -S
```

No bytecode may be written into the candidate.

## First-gate markers

```text
STAGE3C_PRODUCT_ROLE_CLASSIFIER=PASS
PRODUCT_ROLE_UNKNOWN_ZERO=PASS
PRODUCT_ROLE_MUTATION_CHECK=PASS
STAGE3C_PHASE1_ROLE_INVENTORY=PASS
```

A future changed inventory is retained as new evidence. Do not add broad fallback rules merely to force `UNKNOWN=0`, and do not treat `DEBUG_OR_OPTIONAL` as wholesale removable before exact component review.
