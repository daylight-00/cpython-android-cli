# E2-P2 Standalone Build/Package/Verify Façade Contract

> **Status:** frozen — real execution authority accepted; E2-P3 qualification next
> **Façade contract version:** 1
> **Producer binding version:** 1
> **Execution authority version:** 1
> **Artifact contract:** E2-P1 version 1

## Stable command

```text
components/standalone/bin/cpython-android-standalone
```

The stable command and operation names remain unchanged. Internal producer paths are hidden behind the contract.

## Frozen producer binding

The façade is explicitly bound to the frozen Termux-native CPython 3.14.6 authority recorded by:

```text
experiments/epoch2-termux-native-cpython3146-producer/producer-authority.json
components/standalone/contracts/termux-native-cpython3146-producer-binding-v1.json
```

The private authority storage is:

```text
gdrive:HW-T/cpython-android-cli/authorities/e2p2/producers/termux-native-cpython3146/frozen-product-v1
```

This is internal producer authority storage, not a public release, selectable catalog, or publication claim.

## Frozen execution authority

The exact bound façade execution is recorded by:

```text
experiments/epoch2-termux-native-cpython3146-facade-execution/execution-authority.json
```

The private unqualified envelope authority is:

```text
gdrive:HW-T/cpython-android-cli/authorities/e2p2/envelopes/termux-native-cpython3146/install-only-stripped-v1
```

```text
execution input commit   863dccbb31acf4ffe32dd0e26630dd861f96d992
envelope archive         66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727
release index            64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85
private authority index  5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5
```

Canonical and replay package executions are byte-identical across all eight envelope files. This execution authority is accepted only as a real unqualified E2-P1 envelope plus static review.

## Operations

### `plan`

Resolves the selected operation, exact authority inputs, outputs, and internal command without execution. Contract or tracked-input drift fails closed.

### `build`

`build` is now a `termux` host-role operation. It acquires and verifies the frozen authority index, exact artifact archives, manifests, and product lock. It then reconstructs the package input from:

```text
runtime-base + development-addon
```

The `test-addon` remains preserved in the authority and output artifact set but is not included in the E2-P1 package input.

The build step is:

```text
experiments/epoch2-termux-native-cpython3146-facade-binding/materialize-frozen-producer.sh
```

It writes the exact selected prefix under:

```text
work/termux/e2p2-termux-native-cpython3146-facade/prefix
```

and records:

```text
work/termux/e2p2-termux-native-cpython3146-facade/producer-binding.json
results/termux/epoch2-standalone/build-receipt.json
```

Materialization validates archive safety, exact archive and manifest identities, disjoint ownership, structural-parent references, complete path coverage, file modes, regular-file SHA-256 values, symlink targets, launcher identity, and absence of extra paths.

### `package`

`package` is a `termux` host-role operation. It consumes only:

```text
work/termux/e2p2-termux-native-cpython3146-facade/prefix
out/<target>/<profile>/bin/python3.14
tracked Termux-native product lock
repository commit and tree
explicit strip and zstd tools
```

It creates an unqualified E2-P1 `install_only_stripped` envelope under:

```text
dist/<target>/<profile>/standalone
```

The package implementation records the selected producer authority and three-artifact identities in provenance. It does not invoke the installer or mutate the materialized prefix.

### `verify`

```text
verify --scope repository
verify --scope envelope --release-dir <directory>
```

Repository scope uses the current execution-authority verifier. It preserves the producer-binding verifier, historical Gate 1 verifier, and custom-NDK audit as immutable predecessor authorities, requiring only their exact adjudicated current-state failure sets. Envelope scope remains the independent E2-P1 static verifier.

## Host roles

`build` and `package` require `PROJECT_ROLE=termux`. Repository and envelope verification remain host-independent when their declared tools and fixtures are available.

## Compatibility and evolution

Contract version 1 retains the stable command and operation names. The execution freeze changes only current repository authority and verifier routing; build/package behavior and the producer binding remain unchanged. The frozen envelope must be consumed by E2-P3 rather than silently regenerated or promoted.

## Claim boundary

This authority accepts the real stable `build` and `package` executions, deterministic canonical/replay assembly, the complete unqualified E2-P1 envelope, and independent static review. The product is not target-qualified, selectable, publishable, or installer-ready; installer conversion and transition behavior remain separate later gates.
