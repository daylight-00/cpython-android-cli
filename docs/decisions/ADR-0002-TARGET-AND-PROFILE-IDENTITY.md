# ADR-0002: Separate Target, ABI, Libc, API, and Execution Profile

- **Status:** Accepted
- **Date:** 2026-07-16

## Context

Names such as `arm64-termux`, `arm64-bionic`, and `bionic-linux` mix CPU architecture, Android platform identity, libc implementation, and user-space profile.

## Decision

Use the following independent identities:

```text
target triple      aarch64-linux-android
Android ABI        arm64-v8a
minimum API        android24 initially
libc/runtime       bionic
execution profile  termux-cli
```

Artifact filenames may include target and API. Metadata records all fields. `termux-cli` is a profile and must not replace the platform target.

## Consequences

- The core product remains recognizable as Android rather than a fictional Bionic Linux distribution.
- Termux-specific adaptation can evolve without creating a false Termux ELF ABI.
- Future x86_64 or other Android profiles fit the same schema.
- Python wheel platform tags remain a separate compatibility identity, such as `android_24_arm64_v8a`.
