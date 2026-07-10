# Stage 3-A CA Trust Boundary Summary

> **Status:** Selected evidence
> **Stage:** 3-A
> **Result:** Host trust integration confirmed; launcher policy limitation identified

## Purpose

This summary records the Stage 3-A CA trust-source boundary probe for the frozen Stage 2 runtime.

The probe separated four states:

```text
clean launcher environment
explicit correct Termux CA path
missing SSL_CERT_FILE path
existing regular but unusable CA file
```

The HTTPS target was:

```text
https://pypi.org/simple/
```

## Result matrix

```text
clean_default          PASS  HTTPS 200
explicit_termux_ca     PASS  HTTPS 200
missing_file_repair    PASS  HTTPS 200
existing_empty_file    FAIL  certificate verification error
```

The Termux CA file existed at:

```text
/data/data/com.termux/files/usr/etc/tls/cert.pem
```

## Clean launcher environment

Input state:

```text
SSL_CERT_FILE unset
SSL_CERT_DIR unset
```

Observed inside Python:

```text
SSL_CERT_FILE=/data/data/com.termux/files/usr/etc/tls/cert.pem
HTTPS status=200
```

Frozen interpretation:

> The launcher discovered and exported the Termux CA bundle before Python HTTPS use.

`clean_default` in this probe means a clean input environment to the launcher. It does not mean OpenSSL operated without launcher CA integration.

## Explicit Termux CA

Input:

```text
SSL_CERT_FILE=/data/data/com.termux/files/usr/etc/tls/cert.pem
```

Observed:

```text
same SSL_CERT_FILE preserved
HTTPS status=200
```

Frozen interpretation:

> An existing regular-file CA path supplied by the caller is preserved, and the tested Termux CA bundle is usable for HTTPS verification.

## Missing-file repair

Input:

```text
SSL_CERT_FILE=<nonexistent path>
```

Observed:

```text
SSL_CERT_FILE repaired to:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

HTTPS status=200
```

Frozen interpretation:

> A nonexistent `SSL_CERT_FILE` path is rejected by the launcher's regular-file existence check and replaced by the discovered Termux CA bundle.

## Existing empty file control

Input:

```text
SSL_CERT_FILE=<existing zero-byte regular file>
```

Observed:

```text
SSL_CERT_FILE preserved as the empty file
HTTPS FAIL
SSLCertVerificationError
unable to get local issuer certificate
```

Frozen interpretation:

> The launcher checks whether an existing `SSL_CERT_FILE` points to a regular file. It does not validate that the file contains a usable trust store.

This is a policy boundary, not a contradiction in the probe:

```text
path existence acceptance
    !=
trust-store semantic validation
```

## OpenSSL/Python metadata observation

With the Termux CA environment active, `ssl.get_default_verify_paths()` reported:

```text
cafile:
  /data/data/com.termux/files/usr/etc/tls/cert.pem

openssl_cafile:
  /usr/local/ssl/cert.pem

openssl_capath:
  /usr/local/ssl/certs

openssl_cafile_env:
  SSL_CERT_FILE

openssl_capath_env:
  SSL_CERT_DIR
```

The active resolved cafile followed `SSL_CERT_FILE`; the hard-coded OpenSSL build paths remained `/usr/local/...` metadata.

## Architecture consequence

The tested CA trust contract is:

```text
caller supplies existing regular SSL_CERT_FILE
    -> preserve caller choice

caller supplies missing path
    -> discover/repair to Termux CA

caller leaves path unset
    -> discover Termux CA

caller supplies existing but semantically unusable file
    -> preserve caller choice
    -> HTTPS may fail
```

The launcher therefore performs path-level repair, not CA-content validation.

## Documentation correction consequence

Any earlier project wording that says the launcher preserves a "valid `SSL_CERT_FILE`" is stronger than the implementation and should be interpreted as:

> preserve an existing `SSL_CERT_FILE` that points to a regular file.

Stage 3-A adds the empty-file negative control that distinguishes filesystem validity from trust-store usability.

## Distribution implication

CA trust is a confirmed host-integration boundary in the tested Stage 2/3-A runtime:

```text
base runtime archive
    does not currently carry its own selected CA bundle contract

launcher
    discovers Termux host CA bundle when caller path is absent or missing

HTTPS
    succeeds with the tested Termux CA bundle
```

Later Stage 3 distribution design may compare:

```text
host CA integration
bundled CA data
Python package CA data
platform trust API integration
```

but Stage 3-A does not choose among those designs.
