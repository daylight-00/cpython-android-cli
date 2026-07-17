# E2-P2 Termux-native CPython 3.14.6 producer

> **Status:** FROZEN producer authority

This experiment records the exact CPython 3.14.6 Android product rebuilt directly in Termux under the bounded custom-NDK r27d authority.

It is a new authority. It does not rename the frozen Stage 3-B Linux producer, and it does not treat matching NDK release numbers as matching compiler bytes.

## Frozen lineage

```text
source commit                    c63aec69bd59c55314c06c23f4c22c03de76fe45
setpwent correction              25/25
clean replay                     accepted after canonical-host adjudication
materialization                  25/25 + 23/23 adjudication
standalone validation            10/10 + 41/41
invariant closure                21/21
façade verifier closure          24/24 before and after
custom-NDK audit closure         49/49 before and after
```

## Frozen artifacts

```text
runtime-base        7119e97cb43fb19ef4dce3eec145bb867b8070b9f8b7772c74a5885f4fe53c03
development-addon   73dc90a8ead6c58d040a2fc31386f1c00ff38ce84fd4507229e8e9bc18902b6f
test-addon          5bb4c1a45a2c04031c8c8c1a0be05fc02ad4653f21492b63559039105be5ce03
```

The complete machine-readable authority is [`producer-authority.json`](producer-authority.json). The external freeze audit is [`producer-authority-external-audit.json`](producer-authority-external-audit.json).

## Boundary

The producer and standalone three-artifact set are frozen. The E2-P2 façade still has its previous producer binding. Rebinding, real E2-P1 envelope production, qualification, selection, and publication are later independent transactions.
