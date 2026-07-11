# Stage 3-B Phase 3: Dependency Product Promotion

This experiment captures immutable identities for the exact dependency archives consumed by the frozen Phase 2 replay.

Run:

```sh
bash experiments/stage3b-dependency-promotion/capture-current-inputs.sh
```

Expected marker:

```text
STAGE3B_DEPENDENCY_INPUT_CAPTURE=PASS
```

The operation is read-only with respect to the cache and replay products. It writes only:

```text
results/workstation/stage3b-dependency-promotion/dependency-input-manifest.json
```

After review, stable identity fields can be promoted into a tracked manifest. Machine-local cache paths remain evidence and must not become canonical consumer paths.

## Promoted verification

The stable fields from the first capture are tracked at:

```text
config/dependencies/android-source-deps-aarch64-linux-android.lock.json
```

Recapture the current cache and compare it field-by-field:

```sh
bash experiments/stage3b-dependency-promotion/verify-promoted-inputs.sh
```

Expected marker:

```text
STAGE3B_DEPENDENCY_INPUT_VERIFY=PASS
```

Low-level evidence and product-boundary interpretation:

```text
docs/evidence/STAGE3B_PHASE3_DEPENDENCY_CAPTURE.md
```
