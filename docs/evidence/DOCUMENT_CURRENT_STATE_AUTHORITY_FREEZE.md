# Document current-state authority freeze

> **Status:** frozen PASS
> **Authority SHA-256:** `77345393b51d1f7807f77884990838598d2520c6dca3426107c580a1fcb041b6`
> **Predecessor:** `7248859ff5c24990f6cc06ad696a21b2d2793202` / `3a85792eec9c8e78e4955aa1a227e737d9c4c509`

Phase 2 establishes `docs/current/STATE.json` as the sole temporal writer and separates immediate documentation control work from the research program gate held ready.

## Accepted result

```text
tracked Markdown/JSON registry  425/425
current source count            1
render targets                  4/4 deterministic
legacy live bindings            24/24 exact grandfathered baseline
new live/generated bindings     0
negative fixtures               10/10
fixture repository              staged index only; no commit
fixture cleanup                 non-authoritative
Phase 1 authority               18/18 preserved
E2-P3 frozen paths              10/10 byte-preserved
E2-P3 secondary freeze          28/28 verified
```

Historical E2-P3 authority is protected by exact predecessor byte comparison. The recursive historical verifier chain is not replayed in a temporary clone. Negative fixtures are built in one single staged-index fixture repository, restored before every case; ignored runtime trees and temporary-directory cleanup cannot alter the authority verdict.

The state records documentation lifecycle Phase 3 as the immediate repository action and preserves E2-R1 / UT-0 as the program action to resume afterward.

## Claim boundary

No product bytes, experiment result, selectability, publication authorization, Epoch 3 selection, historical evidence, or physical document path is changed by this authority.
