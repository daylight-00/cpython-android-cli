# Stage 3-E Gate 2 Isolated Dual-Version Census Result

> **Status:** TARGET EVIDENCE ACCEPTED BY EXTERNAL RE-AUDIT — ORIGINAL VERIFIER FALSE-NEGATIVE PRESERVED
> **Repository input:** `af930acdcbd5054733bfaa480d1eb18ecdc557bb`, tree `c0bb501656b82b4a43f94548e6080e993dabf974`
> **Target:** Termux on Android arm64
> **uv:** `0.11.28 (aarch64-linux-android)`

## Accepted archive

```text
work ID       20260716-stage3e-gate2-isolated-dual-version-census-v2
archive       3fe68808e2a770f93a6cfe2feba2517b9ac7a42be04c22349fd1c6f375b6cac2
size          46759 bytes
safe members  173
self-index    168/168 exact
Drive file    1dMOGFamGmybm6qPx_BNR0eAhJvMzeprZ
```

External audit:

```text
checks        117/117 PASS
audit sha256  5813305c22528354e6af686330e8f635db2b90a8a7a48ed5ed3c9ad4d1a4fb4d
```

## Correction lineage

v1 stopped before any install because two `set -u` variable-expansion defects existed in the wrapper. It has no target result authority.

v2 executed the complete target census. Its original verifier reported six errors, all caused by invalid verifier assumptions:

1. the catalog-list preflight observed ambient Termux Python instead of listing custom downloadable rows; both exact custom-key installs succeeded and therefore prove catalog acceptance;
2. minor and unspecified finds returned `cpython-3.14-linux-aarch64-none`, while the verifier required an exact-key path; the installed list maps this alias to the 3.14.6 key in both orders;
3. verification ran before `snapshots/after.txt` was created; both archived snapshots exist and are byte-identical.

The original archive and its FAIL marker remain immutable. Acceptance is layered through the external audit.

## Accepted observations

Both installation orders complete:

```text
3.14.5 -> 3.14.6
3.14.6 -> 3.14.5
```

For both orders:

- exact installs and side-by-side installed listing pass;
- installed listing is ordered 3.14.6 then 3.14.5;
- exact find, direct launch, and uv venv launch pass for both versions;
- both interpreters retain `SOABI=cpython-314-aarch64-linux-android` and `MULTIARCH=aarch64-linux-android`;
- exact reinstall reports already installed and preserves complete path/type/mode/content/symlink manifests;
- `3.14` and unspecified find return the same minor alias mapped to 3.14.6;
- removal of the first-installed version preserves exact discovery and launch of the peer;
- final removal yields `[]` and expected return code 2 for both exact finds;
- repository, remote, real managed directory, `$PREFIX/bin`, shell files, registry, journal, and product inputs remain unchanged.

## Claim boundary

This accepts an isolated offline census. It does not accept a persistent root, uv's default managed directory, catalog publication, network distribution, global links, shell integration, upgrade/downgrade, crash recovery, power-loss durability, third-product compatibility, or general upstream uv Android support.
