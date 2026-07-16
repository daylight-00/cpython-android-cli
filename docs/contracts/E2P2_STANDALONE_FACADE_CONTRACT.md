# E2-P2 Standalone Build/Package/Verify Façade Contract

> **Status:** Gate 1 frozen — repository implementation
> **Façade contract version:** 1
> **Artifact contract:** E2-P1 version 1

## Stable command

```text
components/standalone/bin/cpython-android-standalone
```

The command is the public repository entry point for standalone production. Callers must not depend on the experiment paths behind it.

## Operations

### `plan`

Resolves the selected operation, inputs, outputs, and pinned internal commands without executing them. Contract or predecessor-entry-point drift fails before an operation can run.

### `build`

`build` is a Linux-workstation operation. Version 1 delegates to the frozen Stage 3-B producer chain:

```text
experiments/stage3b-upstream-replay/prepare-replay.sh
experiments/stage3b-upstream-replay/run-replay.sh
experiments/stage3b-product-promotion/promote-replay-package.sh
scripts/build/build-launcher.sh
```

The façade does not duplicate these scripts. It pins their Git blob identities, checks their completion markers, verifies the canonical output set, and writes:

```text
results/workstation/epoch2-standalone/build-receipt.json
```

The receipt records exact output size and SHA-256 without making generated paths part of product identity.

### `package`

`package` consumes only:

```text
work/workstation/stage3b-promoted-cpython/prefix
out/<target>/<profile>/bin/python3.14
tracked product lock
repository commit and tree
explicit strip and zstd tools
```

It creates the E2-P1 `install_only_stripped` envelope under:

```text
dist/<target>/<profile>/standalone
```

Transformation rules:

- use one `python/` archive root;
- overlay the canonical launcher and `python3`/`python` symlinks;
- retain runtime and development surfaces;
- exclude CPython tests, `__phello__`, unsupported Tk/IDLE/turtle sources, bytecode residue, build workspaces, and detached debug symbols;
- strip ELF files with one recorded tool and `--strip-unneeded`;
- serialize twice and require byte-identical `pax-tar+zstd` output;
- generate E2-P1 artifact, manifest, provenance, qualification, license, checksum, and release-index sidecars;
- leave qualification `not-qualified` and all selectability fields false.

The package implementation must not invoke the installer or mutate the promoted source prefix.

### `verify`

```text
verify --scope repository
verify --scope envelope --release-dir <directory>
```

Repository scope verifies the façade contract, pinned predecessor entry points, regression tests, E2-P1 preservation, Epoch 1 control-plane preservation, documentation, and tracked authority.

Envelope scope independently verifies archive safety, normalized headers, exact manifest fidelity, metadata linkage, checksum coverage, noncanonical Termux/uv mappings, excluded paths, stripping provenance, and unselectable qualification state.

Target runtime qualification is deliberately absent from façade contract version 1 and belongs to E2-P3.

## Host roles

`build` and `package` require `PROJECT_ROLE=workstation`. Repository and envelope verification are host-independent when Python, Git, zstd, and the required fixture compiler are available.

## Compatibility and evolution

The stable command and operation names are version-1 interfaces. Internal script paths may change only with an explicit contract update and independent verification. Adding target verification requires a new accepted scope rather than silently broadening `verify --scope envelope`.

## Claim boundary

Gate 1 freezes the repository façade implementation and synthetic deterministic package behavior. It does not claim that the real producer has run through the façade or that any emitted product is executable, qualified, selectable, publishable, or installer-ready.
