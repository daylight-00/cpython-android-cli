# E2-P2 Termux-native CPython 3.14.6 producer authority freeze

## Decision

The exact Termux-native CPython 3.14.6 producer and its three-artifact standalone product are frozen as a new E2-P2 authority.

## Repository integration

```text
predecessor main        b5a2ca39d1250122312355dd3dbc6165b9409786
authority lineage head  62b2a935f04dc5c02f0a7676f9a0093682b1ec97
authority lineage tree  98d65c48bcce16022d8210bd9e2877df41f60ce1
topology                predecessor main is an exact ancestor by 41 commits
active branch policy    local main and origin/main only for new work
freeze commit parent    62b2a935f04dc5c02f0a7676f9a0093682b1ec97
```

Historical feature refs may remain as immutable references, but this transaction does not update them and future project work uses `main`.

## Product identity

```text
Python              3.14.6
source commit       c63aec69bd59c55314c06c23f4c22c03de76fe45
target              aarch64-linux-android
canonical host      aarch64-unknown-linux-android
Android API         24
NDK                 27.3.13750724
SOABI               cpython-314-aarch64-linux-android
package             517f4b0d113c4c1cf6931c230b6b517bee7a2b7f8b4f0f099a148260fa3ac8e7
prefix snapshot     3081a1b150473ff6d6896589a2898cb38baf831e0f811af2bd0447c29b36bb89
launcher            bcaf6dd6eb6b156f202ef7c59056f9b0c3f2b9a4ed687f38cf7970f46d40c1bc
```

## Frozen artifacts

| Artifact | Archive SHA-256 | Manifest SHA-256 | Owned paths |
|---|---|---|---:|
| runtime-base | `7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03` | `c8e182282605eeda874805a4c4b1847a82c24252443c59770337e2c0379739ca` | 714 |
| development-addon | `73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f` | `d0dc69fc03552117e1f0d19df09c3230d6eb0436f50595274e8dde60f983e2ce` | 454 |
| test-addon | `5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03` | `a2d90bc30139337f4d3106a0a5a21f6ade3208cb307e0b46d9f25ced57af4697` | 1788 |

## Evidence lineage

| Evidence | SHA-256 | Result |
|---|---|---|
| setpwent preflight correction | `63f18ae9b1fe5ea639c4a58bacad4ce3ada16c23a08adaf2ac5502c7e1a5e47e` | 25/25 |
| clean replay | `99dfc80c2b02d8745db984728c382df6c85bcb9a24980a2c0be2d02d50d764b4` | build/package complete; canonical-host false negative preserved |
| canonical identity adjudication | `fbfaf7b46b11ee6eed0c922587ac9440a0dcf907e274dd03a4e8552f7cef8ef6` | 24/24 + 10/10 |
| three-artifact materialization | `af7e45a9fbbb51d72ca6d696ac40e3c0504f6c8dd9b2b21feda759446802115b` | 25/25 core |
| materialization verifier adjudication | `0b9bbe5662880467def953c56aaf6a870cfff57d5e4ff2a284dd3707bf7e49a4` | 23/23 + 12/12 |
| standalone validation | `5c55d7b33dd7d85b9368d800d55e138fa2634e691fead279357eeedaf814bd94` | 10/10 + 41/41 |
| standalone invariant closure | `fc5f988e672a41cc13ee0189055d64701604aed5d39dcfd2613e07e3cb00f8ad` | 21/21; 24/24 ×2; 49/49 ×2 |

External freeze audit: **23/23 PASS**.

## Accepted behavior

- exact Python, target, canonical host, SOABI, OpenSSL, and SQLite identity;
- exact three-artifact composition in both addon orders;
- native extension import and ELF dependency closure;
- HTTPS, timezone, subprocess, stdlib venv, uv venv, and `uv run` behavior;
- whole-prefix relocation;
- reinstall no-op and repair;
- preserve-and-report ownership;
- PREPARED, APPLYING, and COMMITTED recovery;
- lock exclusion and complete teardown.

## Not accepted

- automatic façade producer rebinding;
- a real E2-P1 release envelope produced through the façade;
- E2-P3 qualification or selectability;
- publication;
- upgrade, downgrade, migration, mixed-version, collision, or transition behavior.
