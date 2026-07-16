# Stage 3-F Gate 5 Documentation-Integrity Correction

> **Status:** CORRECTION V2 DEFINED — repository-only fast-forward repair
> **Failed commit retained:** `71ded3869f38ed59118435f119a35591aee29f75`
> **Restoration source:** `1e7797218473463bc85f6413c49080301eda2ad7`, tree `a3a1cb90f12b20ab47203b4f6b47d8a9694b0e04`

The first Gate 5 transaction passed its marker-oriented verifiers but replaced six established production documents with fixture-shortened copies. The result removed 1,017 lines overall, reduced `README.md` from 498 lines to 32, and reduced the collaboration workflow from 293 lines to 14. Independent post-push diff inspection therefore rejected the commit as the accepted final Stage 3-F documentation state.

The correction is a fast-forward commit. It does not erase or rewrite the failed commit. It restores the exact Gate 4 parent versions of the six affected documents, applies only bounded final Gate 5 status edits, preserves the new Gate 5 authority/evidence files, and strengthens verification with minimum line counts and long-lived section sentinels.

The correction performs no target execution, uv invocation, network publication, external networking, cache mutation, installation, or history rewrite.


## Correction v1 false-negative

The first documentation-correction wrapper result `69bfe223c5fb4f0dec42cf5b99ac35d346be9aaddb7438b82ce59e1d38af494a` made no repository mutation. Its only failed check treated pre-existing ignored bytecode anywhere in the working tree as newly created residue. Correction v2 captures the preflight bytecode inventory and rejects only new residue; standalone verification falls back to rejecting tracked bytecode.
