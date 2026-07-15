# Stage 3-E Gate 4 Project-Owned Persistent-Root Result

> **Status:** ACCEPTED — corrected v2 target result and independent freeze audit
> **Target:** Termux on Android arm64
> **uv:** `0.11.28 (aarch64-linux-android)`
> **Repository input:** `0b9ba82428f3ee15486fe689a5a8dd267ae399fe`, tree `6136a1a08b860b0572d768ce64ab3d357b783783`

## Accepted result identity

```text
work id              20260716-stage3e-gate4-project-owned-persistent-root-v2
archive sha256       4553c5aae0ef3a34979a1678112b01dcdebe7087ba370aea69c44dcbce4fe112
archive size         54299
safe archive members 191
self-index            186/186 exact
target verifier       37/37 PASS
independent audit     74/74 PASS
independent audit sha 794f124b5b00e30b00e26121f01e06fee9e49b7f1c1ac29bdcd775b28c85981a
```

The tested root was:

```text
$HOME/.local/share/hw-t/cpython-managed/gate4-validation-v2
```

It was explicitly supplied as the install directory. The real uv managed directory, `$PREFIX/bin`, shell startup files, repository, registry, journal, and frozen products remained unchanged.

## Accepted lifecycle

The target result proves:

```text
install CPython 3.14.5 and 3.14.6 side by side
exact discovery and launch for both products
fresh-session re-entry after deleting the first session HOME and cache
uv virtual-environment creation and launch for both products
move the complete managed root and continue exact discovery and launch
move the root back without manifest drift
reject a corrupt 3.14.7 local archive
preserve both existing products after that failed operation
create a full backup
restore with archived permissions preserved
verify candidate path/type/mode/content/link identity before replacement
atomically replace the live root
re-discover and launch both products after rollback
remove 3.14.5 while preserving 3.14.6
reinstall and launch exact 3.14.5
uninstall both products
observe an empty managed list and expected-negative exact finds
remove the validation root and restore the pre-existing parent state
```

## Correction lineage

The preserved v1 archive `009114528a72d504659ab30a8a4659add6099ede0a3553f3edc7105786f761cf` passed 36/37. Backup extraction without permission preservation applied umask and narrowed modes (`0711 -> 0700`, `0666 -> 0600`). Strict candidate comparison detected this before atomic replacement. The live root therefore remained intact, and peer lifecycle, teardown, and global invariants still passed.

The v2 rerun did not relax identity. It changed extraction to preserve archived permissions, then passed both candidate and post-swap strict manifest comparisons.

## Claim boundary

This result accepts one explicit project-owned persistent root using local immutable catalog and artifact inputs. It does not accept uv's default managed directory, network publication, automatic downloads, global links, shell integration, upgrades, downgrades, crash recovery, concurrent writers, power-loss durability, third products, or upstream uv Android support.
