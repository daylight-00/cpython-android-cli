# E2-P2 Termux-native CPython 3.14.6 producer authority

> **Status:** FROZEN — exact Termux-native producer and standalone three-artifact authority

## Decision

E2-P2 accepts a new CPython 3.14.6 producer authority executed directly on the canonical Termux device. This authority is distinct from the frozen Stage 3-B Linux-workstation producer and from the frozen Gate 4A CPython 3.14.5 second product.

The authority does not itself rebind the E2-P2 façade. Producer binding remains a separate repository transaction.

## Frozen product identity

- CPython: `3.14.6`
- source commit: `c63aec69bd59c55314c06c23f4c22c03de76fe45`
- target: `aarch64-linux-android`
- canonical host: `aarch64-unknown-linux-android`
- Android API: `24`
- NDK release: `27.3.13750724`
- producer host class: `termux-native-android-bionic-aarch64`
- SOABI: `cpython-314-aarch64-linux-android`
- upstream package SHA-256: `517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7`
- replay-prefix snapshot SHA-256: `3081a1b150473ff6d6896589a2898cb38baf831e0f811af2bd0447c29b36bb89`
- launcher SHA-256: `bcaf6dd6eb6b156f202ef7c59056f9b0c3f2b9a4ed687f38cf7970f46d40c1bc`

## Frozen artifact set

```text
runtime-base
  archive SHA-256   7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03
  manifest SHA-256  c8e182282605eeda874805a4c4b1847a82c24252443c59770337e2c0379739ca
  owned paths       714

development-addon
  archive SHA-256   73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f
  manifest SHA-256  d0dc69fc03552117e1f0d19df09c3230d6eb0436f50595274e8dde60f983e2ce
  owned paths       454
  structural refs   2

test-addon
  archive SHA-256   5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03
  manifest SHA-256  a2d90bc30139337f4d3106a0a5a21f6ade3208cb307e0b46d9f25ced57af4697
  owned paths       1788
  structural refs   2
```

The `2,956` owned paths are disjoint. Four structural parent entries are non-owning namespace references. Unsupported GUI source remains excluded until an Android/Termux Tk backend authority exists.

## Accepted producer method

The authority freezes these bounded host-execution methods:

1. implicit `subprocess.run(shell=True)` calls are routed through Termux bash by an ephemeral adapter;
2. six build-Python cache negatives require exact source mappings;
3. `ac_cv_func_setpwent=no` is the sole historically proven inert cache entry;
4. lld PT_TLS alignment is changed only in an ephemeral overlay;
5. the installed NDK and reacquired source authority remain unchanged;
6. clean dependency, source, build, output, materialization, and validation roots are used.

## Accepted validation

```text
setpwent preflight correction      25/25
clean replay verifier              10/10 after canonical adjudication
canonical identity adjudication    24/24 + 10/10
materialization core               25/25
materialization adjudication       23/23 + 12/12
standalone candidate               10/10
standalone verifier                41/41
standalone invariant closure       21/21
repository façade verifier         24/24 before and after closure
custom-NDK provenance audit         49/49 before and after closure
external freeze audit              23/23
```

Standalone acceptance includes both addon orders, HTTPS, timezone data, subprocess identity, stdlib and uv virtual environments, native extension and ELF closure, whole-prefix relocation, same-version repair, preserve-and-report ownership, PREPARED/APPLYING/COMMITTED recovery, lock exclusion, and complete teardown.

## Forbidden substitutions

The following remain forbidden:

- relabeling the Stage 3-B Linux producer as Termux-produced;
- carrying CPython 3.14.5 source, OpenSSL 3.0.20, package, or runtime identities into this product;
- mutating the installed custom NDK or committing the ephemeral lld overlay;
- treating matching NDK release numbers as matching compiler bytes;
- changing façade producer binding implicitly as part of this freeze;
- claiming E2-P1 envelope qualification, selection, publication, upgrade, downgrade, migration, or transition behavior.

## Next gate

```text
frozen producer authority
  -> explicit façade producer-binding transition
  -> real façade build/package execution
  -> independent E2-P1 envelope review
```
