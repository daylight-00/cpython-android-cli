# Collaboration and Transport

## Responsibility split

The project owner operates the authoritative Termux/device environment, runs target wrappers, controls final scope, pushes from the authoritative checkout, and provides the minimum bridge between device and Drive.

The assistant inspects exact state, implements bounded changes in isolation, creates one-command packages and independent verifiers, audits complete PASS-or-FAIL archives, preserves claim boundaries, publishes/retrieves Drive packages, and prepares successor handoffs.

Do not ask the owner to inspect large logs, edit many files, or run loosely coupled commands when one wrapper can do the work.

## Drive topology

```text
gdrive:HW-T/cpython-android-cli/
  exchange/agent-to-user/<WORK_ID>/
  exchange/user-to-agent/<WORK_ID>/
  handoff/<HANDOFF_ID>/
  backup/<BACKUP_ID>/
```

`gdrive:` is an rclone remote. Use `rclone copyto` or `rclone copy`; plain filesystem `rsync` does not address it. Corrected packages use a new explicit suffix such as `-v2` or `-recovery`.

## Package classes

1. **Work package:** one `.tar.zst`, one safe root, one wrapper, manifest, hashes, and all bounded inputs. It uploads a complete PASS-or-FAIL result.
2. **Mandatory handoff:** the successor starts here. It carries orientation, current coordinates, immediate task, stable operation snapshots, and repository documentation patch when needed.
3. **Miscellaneous backup:** only non-redundant session-local reconstruction material.

When a prior work package is unexecuted or a result exists but is intentionally left unaudited, create only the mandatory handoff and optional backup. Reference the exact pending object instead of duplicating it.

## Archive rules

- New archives use `.tar.zst`; historical accepted `.tgz` remains byte-exact.
- Require one root, no absolute/traversal/duplicate/unexpected-link/special members.
- Use a self-excluding result index when an archive contains its own index.
- Record final SHA-256 and size outside the archive; an archive cannot reliably contain its own final hash.

## Repository rules

- The assistant does not mutate the owner's authoritative checkout directly.
- Use exact local Git for edits, patches, bundles, and validation.
- Patch for narrow linear change; partial bundle for selected topology; full bundle for reconstruction/history rewrite/rollback.
- Cross-session content identity is the Git tree when commit metadata can vary.
- Future author and committer: `daylight-00 <hwjang00@snu.ac.kr>` unless explicitly changed.

## Connector constraints

- Group related files into one archive to reduce connector latency and ambiguity.
- Resolve same-named or duplicate folders by parent, ID, creation time, and direct-child listing.
- After upload, perform raw-byte readback and compare size/SHA when possible.
- Binary downloads may be mounted with `.bin`; content identity, not suffix, is authority.
- Local upload paths must be anywhere under `/mnt/data`.
- A new chat may block local-path rewrite on the first assistant turn. Do not repeatedly retry in that turn; expose the artifact and retry on a later turn.
- Do not embed mutable post-upload claims such as “not uploaded” inside an immutable handoff archive. Record intended destination in the archive and the actual upload/readback receipt externally.
