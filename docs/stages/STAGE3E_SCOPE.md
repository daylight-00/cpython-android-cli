# Stage 3-E Scope: Managed-Python Distribution

> **Status:** ACTIVE — Gate 3 contract frozen; Gate 4 next
> **Input:** frozen Stage 3-D Gate 6 feasibility plus accepted Stage 3-E Gate 2 dual-version census
> **Primary target:** Termux on Android arm64
> **Primary consumer:** uv managed-Python workflows for exact HW-T products

## Stage question

How should exact HW-T Android CPython products become a reproducible, persistent, multi-version managed-Python distribution without reopening frozen runtime, archive, ownership, transition, or system-Python authorities?

## Gate sequence

```text
Gate 1  authority and productization-boundary design    FROZEN
Gate 2  isolated dual-version boundary census           FROZEN — external re-audit 117/117
Gate 3  managed-Python distribution contract            FROZEN
Gate 4  target implementation and lifecycle validation  ACTIVE NEXT
Gate 5  independent distribution freeze                 pending
```

## Gate 2 authority

Gate 2 accepts one safe self-indexed target archive with 173 safe members and a 168/168 exact result index. The original target verifier is retained as a false-negative. External re-audit resolves only the invalid verifier assumptions and passes 117/117 without mutating the original result.

Accepted observations:

```text
both exact custom keys install in either order
side-by-side exact discovery and Android identity pass
uv venv creation and launch pass for both versions
exact reinstall is a byte/mode/link no-op for both versions
removing one version preserves the other
final uninstall produces an empty managed list and expected-negative finds
minor and unspecified selection choose the 3.14 alias mapped to 3.14.6
install order does not change installed-list order or selection
real/global/frozen state remains byte-identical
```

## Gate 3 contract

Exact patch-version requests are canonical.

Authoritative selectors:

```text
cpython-3.14.5-linux-aarch64-none + exact request 3.14.5
cpython-3.14.6-linux-aarch64-none + exact request 3.14.6
```

Conditional selectors:

```text
3.14        latest patch through uv minor alias; observed 3.14.6
unspecified latest eligible managed interpreter; observed 3.14.6
```

Conditional selectors must not be used when exact product identity is required. Catalog rows must bind immutable artifact hashes. Global links and shell integration are separate, currently forbidden authorities.

## Gate 4 selected boundary

Gate 4 first validates a project-owned persistent managed root with local immutable catalog/artifact inputs and explicit install directory. It must cover both versions, exact selection, venvs, idempotent reinstall, peer-preserving uninstall, final teardown, failed-operation preservation, and rollback.

Gate 4 does not yet authorize:

```text
uv default managed directory
network or automatic downloads
published mirrors or mutable catalog endpoints
$PREFIX/bin links or shell startup edits
power-loss durability
upgrade/downgrade or crash recovery claims
third-product or general upstream Android support
```
