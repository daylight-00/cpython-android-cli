# E2-R1/UT-6 Evidence Freeze

```text
authority            experiments/epoch2-upstream-thin-platform-portability/platform-portability-authority.json
authority sha        b21eddfee574343772d0875a7b6f26aa7b5dd494ccf0a5f1be9b8c09201276f4
direct API           36
direct page size     4096
runtime cases        5/7 direct PASS/complete
runtime ELF          81
wheel ELF            1
public claims        3
withheld claims      10
minimum API claimed  False
runtime 16K tested   False
audit                 64/64 PASS
```

Accepted: exact current-target runtime evidence and static final-ELF 16 KiB compatibility.

Withheld: minimum API, untested page-size runtime, non-Termux, ADB, root, emulator, other ABI, broad device/version, and unselected pip/uv claims.
