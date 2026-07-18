# E2-P3 Real Termux Archive Qualification Authority Freeze

## Scope

This authority freezes one archive-only `termux-real` qualification of the exact E2-P2 private envelope. It does not rebuild, repackage, mutate, select, or publish the product.

## Input identity

```text
repository commit              2a60dfa977e6f14e34203f876dcb1cafaf83f15c
repository tree                acd6c00d96e3831aabc23a80508489c3a2e4eb7c
envelope archive               66c2a39b7164701d3a14cff538be298abcf30c696150f6abf7785e212c1b4727
release index                  64825d3afabbda7c90992debfb11e771baeff5514f2b6e6d13584dc7ac6fcf85
private authority index        5fd8c03b53bcb749cfa221277e75f16b2392e6cec3a184b716f98e24d84fe0b5
contract result                ec38ed8bb5b42dbcd32c106ae6887433e59e17b0cb9573491761443683b85caf
harness correction result      938466af2d5dc58e1551a1ef4a66cab38b85d847f06e4dde3214335f3f432a1b
failed 33/35 result             0864173ef3b6b735ef3168b26aed6c5052296289a7c0771cb05754318fb63a79
```

## Accepted target result

```text
profile                         termux-real
host                            real Android / Termux / aarch64
Android API                     36
qualification                   35/35
result verifier                 19/19
independent review              38/38
repository before/after         unchanged
blockers                        0
```

Observed product facts include 81 ELF objects, 329 `DT_NEEDED` edges, 67/67 extension imports, HTTPS status 200, offline pip installation, explicit-interpreter uv workflows, relocated venv behavior, `android_24_arm64_v8a` wheel tags, and no product mutation.

## Frozen evidence coordinates

```text
result archive
  20260718-e2p3-real-termux-archive-qualification-v2-results.tar.zst
  size    68447
  SHA-256 b92b041b78b21e0a3b402e54a15e008008db13320a264284d604f39046907e0b
  Drive file ID 1V91v9v0jELPbnH42w10-FNKzQMMsVjl6

target authority
  gdrive:HW-T/cpython-android-cli/authorities/e2p3/qualifications/termux-native-cpython3146/termux-real-v1
  Drive folder ID 1zKPFqqcGF-Y8HzblRZBl_aFweKoSsdMb
  index SHA-256 9fbd2ce1f9c288bcdb92b19c0fffce24086671d40b2cce658f524935ad473ab1
```

The result archive has one safe `run/` root, 113 members, no absolute/traversal/duplicate/link/special members, and a self-excluding index that exactly covers 96 files. The live Drive authority index is byte-identical to the archived source and readback indexes; its `SHA256SUMS` exactly enumerates the 24 indexed children other than itself and the sums file.

## Claim boundary

The individual real-Termux profile is qualified and frozen. It remains `selectable=false`. Emulator qualification, combined target acceptance, qualification metadata finalization, publication, installer conversion, transition behavior, and the planned post-E2-P3 Epoch 2 scope redesign are not claimed here.
