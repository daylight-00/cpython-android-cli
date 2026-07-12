# Stage 3-C Phase 5 Gate 3B Preserve-and-Report Product Acceptance Result

> **Status:** FROZEN PASS
> **Target:** Termux on Android arm64
> **Accepted evidence:** complete independently inspected historical TGZ

## Archive identity and safety

```text
archive
  stage3c-phase5-gate3b-preservation-acceptance-results-20260713-024946.tgz

sha256
  0be850523ddc9b0fcb652d47f4414d0772dea1d8767f23490c3655576683270b

size
  24,857,211 bytes

members
  323

regular files / directories
  290 / 33

unsafe paths / links / special entries
  0 / 0 / 0
```

The accepted `.tgz` is immutable historical evidence. It was inspected byte-exact and was not recompressed or renamed as a replacement.

## Result-index authority

```text
root result-index sha256
  f3e0bd34c61f5b1e0960d002175478b112641fa71f0e914ec712e6c514e52fe9

root indexed files
  289/289 exact

missing / extra indexed regular files
  0 / 0

hash / size / mode / type mismatches
  0 / 0 / 0 / 0
```

## Verification authority

```text
scenario checks
  29/29 PASS

independent verifier
  62/62 PASS

happy reinstall
  4/4 PASS

happy uninstall
  4/4 PASS

crash recovery
  12/12 PASS

scenario runner return code
  0

independent verifier return code
  0

workflow return code
  0

wrapper return code
  0
```

The independent verifier also confirmed canonical generated JSON, exact copied Gate 3B0 authority, exact raw process cross-checks, 20 inode-separated scenario roots, and the explicit product claim boundary.

## Happy-path acceptance

Registered mismatches were repaired with `noop 713 / repair 1`, mutation count 2, exact registry preservation, clean verification, and zero transaction residue. Unowned sentinels remained unchanged with `noop 714`, mutation count 0, exact registry preservation, clean verification, and zero transaction residue.

All four uninstall scenarios transitioned the registry from one artifact and 714 owned rows to zero artifacts and zero rows, preserved only the contract-approved modified leaf or unowned sentinel plus required non-empty ancestor directories, verified against the empty registry, and left zero transaction residue.

## Crash-recovery acceptance

```text
PREPARED
  4/4, process rc 90

late APPLYING
  4/4, process rc 93

COMMITTED
  4/4, process rc 92
```

For PREPARED and late APPLYING, recovery returned `ROLLED_BACK`, restored the prior registry and complete registered state, retained the original modification or sentinel, and a second recovery returned `NOOP_ROLLED_BACK` without state change.

Modified-owned pre-commit states intentionally retained exactly one bad registered leaf:

```text
regular
  lib/python3.14/LICENSE.txt

symlink
  bin/python

engine verifier
  bad_paths exactly the modified leaf / rc 44
```

Unowned-sentinel pre-commit states verified cleanly with rc 0. COMMITTED recovery returned `FINALIZED_COMMIT`, retained the accepted residual, removed the transaction, left an empty registry, and verified cleanly with rc 0; the second recovery was a no-op with transaction count zero.

## Frozen policy result

Gate 3B accepts the existing preserve-and-report contract for runtime-base reinstall, uninstall, and crash recovery. It does not alter journal, registry, manifest, archive, dependency, or upgrade policy.

## Claim boundary

This PASS proves runtime-base preserve-and-report behavior across eight happy scenarios and twelve accepted crash-recovery scenarios.

It does not prove addon lifecycle or dependency enforcement, final multi-artifact or runtime-base uninstall, upgrade, or downgrade. Those remain Gate 3C, Gate 3D, and Gate 4 boundaries respectively.
