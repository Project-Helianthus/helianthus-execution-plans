# Status

This active guide is a planning artifact, not live issue, review, CI, release or
hardware status. The 4 September 2026 inventory is a dated baseline. Inspect current
remote state in the owning repository before implementation.

The companion only checks the declared 0.7 package IDs, owner allowlist,
dependencies, priority ordering and Markdown mirror. It is local and read-only.
0.8 packages and execution order live exclusively in the future 0.8 guide.

## Decision record

- 24 October 2026, operator decision: all Huawei implementations are Release 0.7.
  Evidence comes from bounded read-only captures on the operator's sites; raw
  captures stay private and only sanitized, synthetic re-creations reach any
  repository. The clean-room rule is unchanged, and writes and controls stay out of
  scope. The [canonical guide](./00-canonical.md) holds the decision text and the
  [issue map](./90-issue-map.md) lists tickets H01 to H12. This line is scheduling
  metadata and carries no runtime state.
