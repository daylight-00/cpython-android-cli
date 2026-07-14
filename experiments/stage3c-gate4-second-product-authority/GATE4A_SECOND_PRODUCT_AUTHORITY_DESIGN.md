# Stage 3-C Phase 5 Gate 4A: Second-Product Authority Acquisition Design

> **Status:** FROZEN PASS — A1-A6 complete
> **Selected second product:** CPython 3.14.5 / android24 / aarch64
> **First-product authority:** CPython 3.14.6 / android24 / aarch64, frozen through Gate 3D
> **Target:** Termux on Android arm64

## Authority question

> Can a genuine second complete product be reproduced, split into the frozen three-artifact ownership model, validated independently on Termux, and frozen with byte-exact evidence before any upgrade or downgrade policy is designed?

Gate 4A is an authority-acquisition gate, not a transition gate. It consumes the frozen first-product architecture and lifecycle semantics without reopening them.

## Selected second product

The second product is the immediate stable predecessor of the first product:

```text
first product
  CPython 3.14.6
  tag v3.14.6
  commit c63aec69bd59c55314c06c23f4c22c03de76fe45

second product
  CPython 3.14.5
  tag v3.14.5
  commit 5607950ef232dad16d75c0cf53101d9649d89115

target held constant
  aarch64-linux-android
  Android API 24
  NDK 27.3.13750724
```

This is a real cross-version boundary while keeping the CPython minor line, Android target, API floor, and NDK constant. It avoids conflating transition behavior with a major/minor ABI change.

## Reference identities versus project authority

Official Python.org source and Android package hashes are preserved as references:

```text
Python-3.14.5.tar.xz
  sha256 7e32597b99e5d9a39abed35de4693fa169df3e5850d4c334337ffd6a19a36db6

python-3.14.5-aarch64-linux-android.tar.gz
  sha256 f008321abf837fcaec569df143283ece0e764b18d8c75763200160553f906af1
```

The official Android package is not the project product authority. The project must independently replay the exact upstream Android producer, then materialize its own runtime-base, development-addon, and test-addon artifacts under the frozen ownership contract.

## Source-native producer boundary

The exact upstream source blobs are inputs:

```text
Android/android.py
  git blob ec4d28bbaad84d4db730678a5d627c4703bbb401

Android/android-env.sh
  git blob 5859c0eac4a88fb552c495d46b77422ac5cdc2f0
```

The dependency set must come from that exact `Android/android.py`:

```text
bzip2   1.0.8-3
libffi  3.4.4-3
openssl 3.0.20-0
sqlite  3.50.4-0
xz      5.4.6-1
zstd    1.5.7-2
```

The OpenSSL input is a real producer delta: v3.14.5 declares OpenSSL 3.0.20-0, while the frozen v3.14.6 producer declares OpenSSL 3.5.7-0. Therefore the second product cannot be obtained by editing a version string or relabeling first-product bytes.

Every dependency asset, including apparently unchanged releases, must be freshly downloaded or independently read back and verified against an exact URL, size, SHA-256, and archive inventory before replay. Reuse of a first-product cached asset is allowed only after byte identity is independently verified.

## Six-stage acquisition sequence

```text
A1  selection and repository design          DESIGN FROZEN
A2  exact input and toolchain capture         FROZEN PASS
A3  clean upstream Android replay             FROZEN PASS
A4  three-artifact materialization            FROZEN PASS — 26/26 adjudication
A5  standalone Termux validation              FROZEN PASS — 34/34 independent audit
A6  independent archive audit and freeze      FROZEN PASS — 28/28 external audit
```

### A2 — exact input capture

Capture:

```text
v3.14.5 tag and commit reachability
source archive and clean worktree identities
Android/android.py and android-env.sh SHA-256
all six dependency asset URLs, sizes, SHA-256, and member inventories
Android SDK and NDK identities
compiler, linker, make, host Python, and relevant host tool versions
```

No product archive is claimed by input capture.


#### A2a accepted progress

The immutable remote-input sub-witness is accepted:

```text
result archive sha256  e9c9ed69098017017b3cbf70e8237c040ede26d378f6530043cc5ff4e7469caf
root result-index      5d87e7727aef99b793ac8ddacf5e9d77f96701caf2377094013753edcda17fbe
external audit         81/81 PASS
```

The A2a collector's original 44/49 FAIL is retained and classified as a schema-comparison false negative. A scoped authority decision accepts A2b through the exact preserved custom-r27d Android/aarch64 binary asset and ephemeral linker overlay. A2 is complete. No product archive is claimed by A2.

### A3 — upstream replay

Replay from an isolated clean worktree and empty build/output roots. Preserve raw commands, stdout, stderr, and real process return codes for dependency unpack, build-Python, target configure/build/install, and packaging.

No first-product payload may be copied into the second candidate. The candidate must identify itself as Python 3.14.5 and `aarch64-linux-android` through runtime and sysconfig probes.

### A4 — three-artifact materialization

Derive complete and independently owned:

```text
runtime-base archive + manifest
development-addon archive + manifest
test-addon archive + manifest
second-product lock
manifest index
ownership registry template
```

Reconstructing the three artifacts must reproduce the complete replay prefix under the accepted exclusion policy with no unexplained drift. Artifact ownership must remain disjoint while using the frozen registry and journal schema.

### A5 — standalone Termux validation

Use fresh inode-separated roots and validate the second product independently:

```text
CLI and PyConfig behavior
native stdlib closure
HTTPS trust and timezone integration
subprocess and venv behavior
uv explicit-interpreter workflow
whole-prefix relocation
independent addon installation/removal
same-version reinstall and repair boundaries
preserve-and-report ownership
recovery and lock exclusion
complete final teardown
```

A5 must not execute upgrade or downgrade operations.

Accepted A5 evidence is the exact corrected v2 result archive `851026d08d18dcef03b30d7ccf3f437a8712ba5cbdecde5e9d4478ba996ecc76`: candidate 10/10 PASS, archived verifier 41/41 PASS, and independent A6 input audit 34/34 PASS. The preserved v1 FAIL remains evidence of two harness false negatives.

### A6 — independent freeze

A complete pass-or-fail `.tar.zst` result archive must include raw logs, real return codes, canonical JSON, complete indexes, and archive safety evidence. Independent audit recomputes artifact and manifest identities, product lock, ownership counts, native closure, runtime behavior, and claim boundaries.

The accepted A6 archive is `4565b69e78c618f58fda59f928c086bbcf1cd02cfb28252f419e42e8cbc266aa`: 40/40 indexed files, candidate 18/18 PASS, archived verifier 18/18 PASS, and external audit 28/28 PASS. A6 declares the exact CPython 3.14.5 second product frozen.

## Forbidden shortcuts

```text
manual version-string editing
copying and relabeling first-product payload
using the official Android package as project product authority
reusing the first product lock as the second product lock
starting mixed-version or transition scenarios before A6 freeze
```

## Transition boundary

Gate 4A is complete, so upgrade/downgrade policy design may now begin. This authority still does not freeze:

```text
whole-product versus artifact-by-artifact transition order
mixed-product addon compatibility
collision or residual policy across versions
product-lock replacement semantics
bidirectional transition journal behavior
upgrade or downgrade recovery
post-transition behavior acceptance
scenario count
```

## Machine authority

```text
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-input.json
experiments/stage3c-gate4-second-product-authority/gate4a-second-product-authority-matrix.json
experiments/stage3c-gate4-second-product-authority/gate4a-a4-materialization-authority.json
experiments/stage3c-gate4-second-product-authority/gate4a-a5-standalone-authority.json
experiments/stage3c-gate4-second-product-authority/gate4a-a6-external-audit.json
experiments/stage3c-gate4-second-product-authority/gate4a-a6-second-product-authority.json
```

## Claim boundary

Gate 4A A6 PASS proves that the repository acquired and independently froze a genuine v3.14.5 source-native three-artifact product with exact archives, manifests, product lock, ownership, target behavior, recovery behavior, and evidence lineage.

It does not prove compatibility, upgrade, downgrade, migration, cross-version collision policy, transition recovery, or post-transition behavior.

## Scoped A2b producer-host exception

The original workstation topology remains historical design authority and the frozen first-product provenance is unchanged. For Gate 4A second-product acquisition only, A2b through A4 may execute on the accepted Termux-native producer host. The authority is binary-defined and does not claim custom-NDK source rebuild reproducibility. See `gate4a-a2b-termux-native-toolchain-authority.json`.
