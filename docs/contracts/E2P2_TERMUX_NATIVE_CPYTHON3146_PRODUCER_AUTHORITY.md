# E2-P2 Termux-native CPython 3.14.6 producer authority

## Decision

E2-P2 may acquire a new CPython 3.14.6 producer authority on the canonical
Termux device rather than requiring the unavailable historical Linux producer.

The new authority is distinct from:

- the frozen Stage 3-B Linux-workstation producer;
- the frozen Gate 4A CPython 3.14.5 second product;
- the E2-P2 façade and its current producer binding.

## Pinned product identity

- CPython: `3.14.6`
- source commit: `c63aec69bd59c55314c06c23f4c22c03de76fe45`
- target: `aarch64-linux-android`
- Android API: `24`
- NDK release: `27.3.13750724`
- producer host class: `termux-native-android-bionic-aarch64`

## Permitted reuse from the CPython 3.14.5 authority

Only host-execution methods may be reused:

1. an ephemeral Python launcher that routes implicit `shell=True` calls through
   Termux bash;
2. bounded build-Python configure-cache adaptation, including the retained
   `setpwent` inert cache entry described below;
3. an ephemeral lld PT_TLS alignment overlay;
4. clean isolated roots and full command/result capture;
5. Android runtime validation before freezing.

## Legacy build-Python cache model

The initial negative cache profile contains seven functions. Six functions
(`fexecve`, `getloadavg`, `getlogin_r`, `getpwent`, `pthread_getname_np`, and
`sem_clockwait`) must have exact `configure` cache-variable and
`pyconfig.h.in` macro mappings.

`setpwent` is the sole exception. The retained CPython 3.14.5 A3 successful
replay proves that passing `ac_cv_func_setpwent=no` records `no` in the build
Python config log, emits no `HAVE_SETPWENT` definition, and allows the complete
build and target replay to succeed. It is therefore an inert build-Python cache
entry, not a claim that CPython exposes a `HAVE_SETPWENT` mapping.

Any new dynamically discovered function still requires both exact source
mappings before it may be added.

## Forbidden substitutions

The following are forbidden:

- setting `PROJECT_ROLE=workstation` merely to bypass role enforcement;
- calling the Termux compiler the historical Victor Linux compiler;
- carrying the CPython 3.14.5 source, OpenSSL, package, or runtime identities
  into the 3.14.6 product;
- relabeling the frozen Stage 3-B artifacts as Termux-produced;
- changing the façade producer binding before the new producer is independently
  built, materialized, validated, and frozen.

## Gate sequence

```text
opening and preflight
  -> clean upstream 3.14.6 replay
  -> three-artifact materialization
  -> standalone Termux validation
  -> independent freeze
  -> explicit façade producer-binding transition
  -> E2-P2 Gate 2
```

This document authorizes only the first line until its evidence is accepted.
