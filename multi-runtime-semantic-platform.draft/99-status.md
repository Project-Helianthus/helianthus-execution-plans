# Status

State: `draft`
Started: `2026-04-12`
Last revised: `2026-07-08`
Current milestone: `M1 - Documentation Grounding`
Baseline: `Gateway 0.4.0`

## Current Position

This draft records the owner-approved direction for Helianthus as a
multi-runtime semantic platform and the adversarially refined raw-first eeBUS
VR940f execution path. M0 is accepted; the plan remains `.draft/` until M1
platform documentation grounding is accepted and the lock step can run.

## Completed In This Draft

- Standard plan directory created.
- Gateway `0.4.0` named as the direct eBUS baseline.
- Platform taxonomy captured.
- eBUS base/profile split captured.
- eeBUS raw-first VR940f track rewritten around `helianthus-eebusreg`,
  `enbility/eebus-go v0.7.0`, runtime feasibility gates, trust hardening, and
  deterministic read-only MCP.
- Model routing updated to use only `GPT-5.3-Codex-Spark`, `gpt-5.4-mini`,
  and `GPT-5.5` medium/high/xhigh lanes.
- `helianthus-docs-eebus` added as the eeBUS-native protocol documentation
  repo, with cross-protocol platform contracts kept under
  `helianthus-docs-ebus/docs/platform/`.
- Issue and milestone maps updated for M0 through M9 with M8.5 leaf-promotion
  lock.
- Machine-readable M0 issue matrix added in `92-m0-issue-matrix.yaml`.
- `eebus-transport-gate v0` added in `93-eebus-transport-gate-v0.md`.
- Ready-to-file M0 issue bodies added under `issues/` for MSP-00A, MSP-00B,
  and MSP-00C.
- GitHub issues filed for MSP-00A, MSP-00B, and MSP-00C in
  `Project-Helianthus/helianthus-execution-plans`.
- PR #35 merged in `Project-Helianthus/helianthus-execution-plans` for the M0
  control-plane plan update at
  `2860d742e2682fbc42d1a5d98906031a0ff3e45d`; MSP-00A/MSP-00B/MSP-00C issues
  #33/#32/#34 are closed.
- Local M1 docs bootstrap completed in `helianthus-docs-ebus` and
  `helianthus-docs-eebus`; evidence recorded in
  `94-m1-docs-bootstrap-evidence.md`.
- GitHub issue #333 and draft PR #334 opened in
  `Project-Helianthus/helianthus-docs-ebus` for MSP-01A.
- Public repository `Project-Helianthus/helianthus-docs-eebus` created and
  seeded at commit `d15353296605e057a7fe5e0a11e4e066cdfb405c`; MSP-01B and
  MSP-01C issues filed as #1 and #2, then closed against the bootstrap commit.
- M2 repo bootstrap gap closed in the plan with MSP-020 before MSP-02A; this
  makes `helianthus-eebusreg` creation an explicit serialized issue with CI
  and public boundary gates.
- Public repository `Project-Helianthus/helianthus-eebusreg` created and
  seeded at commit `6c4fa77435db48f5cdecfb6b2d586ae0b22d8837`; MSP-020 filed
  as issue #1 and closed against the bootstrap commit.
- Six-agent adversarial gate review run against PR #35, PR #334, and
  `helianthus-eebusreg`; the seventh requested agent was blocked by thread
  limit.
- Bootstrap hardening PR #3 merged in `helianthus-eebusreg` to remove
  premature public runtime/raw identity/pairing/evidence contracts and allow
  future `internal/...` facade package names.
- `helianthus-docs-ebus` PR #334 updated to explicitly include MSP-020 before
  raw identity/snapshot/evidence drafts.
- `helianthus-docs-eebus` PR #3 merged to make the VR940f promotion note
  summary-only and link canonical platform ownership.
- MSP-02A issue body prepared locally as `prepared-not-filed`; it is explicitly
  blocked until docs-ebus #334 merges.

## Not Yet Done

- Merge the MSP-01A docs platform PR after formal approval.
- File concrete GitHub issues for MSP-02A and later M2 rows from the M0
  matrix after predecessor gates are accepted.
- Attach gateway `0.4.0` baseline evidence bundle.
- Run implementation-time gates for `eebus-go`, HA networking, VR940f lab
  smoke, trust store, MCP contract, evidence recorder, and leaf promotion.
- Promote to `.locked/`.

## Operational Notes

- M0 seed artifacts are accepted and merged.
- Runtime implementation must not start before MSP-01A establishes the platform
  docs ownership gate through merged docs-ebus #334.
- Durable protocol knowledge remains canonical in `helianthus-docs-ebus`.
- `helianthus-docs-eebus` is the eeBUS-native workbench/docs repo and must
  cross-seed publishable durable conclusions back to `helianthus-docs-ebus`.
- Cross-protocol platform contracts remain in
  `helianthus-docs-ebus/docs/platform/` until a future docs-platform split.
- Existing dirty files in other plan directories are unrelated and must remain
  untouched by this draft commit.
