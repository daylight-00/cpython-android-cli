# Stage 2 CA Policy Clarification

> **Status:** Authoritative clarification
> **Applies to:** Frozen Stage 2 R2 launcher and Stage 2-C synthesis launcher
> **Evidence source:** Stage 3-A CA boundary probe

## Why this clarification exists

Some Stage 2 documents use shorthand such as:

```text
preserve valid SSL_CERT_FILE
```

Stage 3-A added a negative control using an existing zero-byte regular file and showed that this wording is stronger than the actual launcher implementation.

The launcher does not validate CA-bundle contents.

## Actual implementation contract

The frozen launcher policy is:

```text
existing SSL_CERT_FILE points to a regular file?
    yes -> preserve caller choice
    no  -> try $PREFIX/etc/tls/cert.pem
            |
            +-- regular file -> use it
            |
            +-- otherwise try fixed Termux fallback:
                /data/data/com.termux/files/usr/etc/tls/cert.pem
```

The regular-file check establishes filesystem existence and file type only.

It does not establish:

```text
PEM parseability
presence of CA certificates
suitability as a trust store
ability to verify a target certificate chain
```

## Stage 3-A control result

Observed:

```text
SSL_CERT_FILE unset
  -> launcher selects Termux CA
  -> HTTPS PASS

SSL_CERT_FILE = correct Termux CA
  -> preserved
  -> HTTPS PASS

SSL_CERT_FILE = nonexistent path
  -> launcher repairs to Termux CA
  -> HTTPS PASS

SSL_CERT_FILE = existing empty regular file
  -> preserved
  -> HTTPS FAIL
```

## Correct terminology

Use:

> preserve an existing `SSL_CERT_FILE` that points to a regular file

or, when discussing observed HTTPS success:

> preserve the tested usable Termux CA bundle

Do not use the implementation claim:

> launcher validates the existing CA bundle

because that behavior is not implemented or tested.

## Freeze status

This clarification does not reopen Stage 2 runtime architecture.

It narrows the wording of the CA policy to match:

```text
frozen launcher source
    +
Stage 2 observed repair behavior
    +
Stage 3-A empty-file negative control
```

A future Stage 3 distribution design may choose a stronger CA-content contract, but that would be a new distribution policy decision rather than a reinterpretation of frozen Stage 2 behavior.
