# Stage 3-C Phase 4: Installation Contract

> **Status:** ACTIVE — target evidence pending
> **Input:** frozen Phase 3 archives

## Question

```text
Can frozen archives deterministically produce an installed ownership registry,
collision matrix, transaction ordering, and uninstall policy before any target
filesystem is changed?
```

## Run

```sh
bash experiments/stage3c-installation-contract/run-installation-contract.sh
```

## Frozen input

```text
runtime-base archive
  2ba7c309b1700926dc423eb4305a9eba1a53c023a11617e490b151be71e49743

development-addon archive
  f77ea24c92fdd982cd32e172b2d38134f1d785b1f106d1bfe36a9bffa9cc8eea

test-addon archive
  02a1fad1af5528a4e910f0eb3370f4a2696da4f78067586e8b62f2a10fb4c9b1
```

The workflow copies the accepted Phase 3 archives, build indexes, verification results, manifests, manifest index, and product lock into a self-contained input directory.

## Registry model

```text
owned path records          2956
structural references          4
shared namespace
  lib
  lib/python3.14
```

Only `OWNED_PAYLOAD` is registered. `STRUCTURAL_PARENT` remains non-owning. Archive envelope metadata is not copied into the installed payload prefix.

## State layout

```text
<installation-root>/
  prefix/
  .cpython-android-cli/
    registry.json
    lock
    transactions/
```

## Policy outputs

```text
installed-owned-paths.tsv
structural-paths.tsv
collision-policy.tsv
operation-order.tsv
contract-summary.tsv
registry-template.json
installation-contract.json
contract-index.json
```

The collision matrix contains 17 exact rules. The operation model contains 12 install steps and 10 uninstall steps.

## Safety direction

```text
unowned regular file or symlink at a required leaf path
  conflict

existing compatible directory for an owned directory path
  reuse and register only the directory path
  preserve all descendants

existing compatible structural directory
  create or reuse without ownership

required directory occupied by non-directory
  conflict

matching same-version reinstall
  no-op

registered same-owner mismatch
  replacement requires backup

locally modified path during uninstall
  preserve and report

owned directory
  remove only when empty

structural parent and unowned descendant
  preserve
```

Exact directory ownership never implies descendant ownership. This preserves unowned sentinels while allowing a later install to reuse the retained directory.

## Validation

```text
contract derivation       54 checks
independent verifier      59 checks
input tree mutation        PASS required
```

Expected markers:

```text
STAGE3C_PHASE4_INSTALLATION_CONTRACT_DERIVATION=PASS
INSTALLATION_CONTRACT_ACCEPTED_INPUTS=PASS
INSTALLATION_CONTRACT_DERIVATION=54/54 PASS
INSTALLATION_CONTRACT_VERIFICATION=59/59 PASS
INSTALLATION_CONTRACT_OWNED_PATHS=2956 PASS
INSTALLATION_CONTRACT_STRUCTURAL_REFERENCES=4 PASS
INSTALLATION_CONTRACT_INPUT_MUTATION_CHECK=PASS
STAGE3C_PHASE4_INSTALLATION_CONTRACT=PASS
```

## Results

```text
results/termux/stage3c-phase4-installation-contract/
```

## Upload

```sh
RESULTS="$PWD/results/termux/stage3c-phase4-installation-contract"
ARCHIVE="$HOME/Downloads/stage3c-phase4-installation-contract-results-$(date +%Y%m%d-%H%M%S).tgz"

tar czf "$ARCHIVE" "$RESULTS"
printf 'upload: %s\n' "$ARCHIVE"
```

The bundle contains the three frozen Phase 3 archives and is expected to be larger than earlier contract-only evidence.

## Claim boundary

A PASS proves deterministic policy and registry representation. It does not mutate a target or prove rollback, recovery, concurrency, upgrade, downgrade, or installed runtime behavior.
