# Status

State: `maintenance`

## Current Position

- All non-deferred milestones (M0-M7, M9) are complete and merged on `main`.
- M8 remains intentionally deferred, tracked in `common-firmware-rewrite.locked`.
- M9 exhausted on the explicit optional-rollout no-op path: `ISSUE-HA-01` is
  linked to `Project-Helianthus/helianthus-ha-integration#170`, closed on
  2026-03-29 after confirming the HA integration remains a semantic GraphQL
  consumer with parity guardrails and does not need a new observe-first
  diagnostics surface for this plan closure.
- Parent issue `Project-Helianthus/helianthus-ebusgateway#400` is closed as
  the completed `GW-15` proof/default-flip-preparation gate.
- `ISSUE-GW-16` is closed as the canonical non-promotion/default-state
  decision: record-only remains the canonical default.
- `ISSUE-DOC-11` is merged/closed on docs `main`, freezing the bounded P03
  proof scope as family-scoped evidence only.
- Original M0 docs-canonicalization backlog fully merged (DOC-01 through DOC-04).
- Tiny parallel lane (ISSUE-TE-01/TE-02) re-homed to `common-firmware-rewrite.locked`.

## Closure Note

Plan transitioned to `.maintenance` on 2026-03-29. Status file updated
2026-04-11 to reflect the canonical maintenance state.

Key outcomes:
- Observe-first bus observability pipeline fully operational
- Bounded P03 proof artifacts: canonical proof with fail-closed gates
- Family-scoped promotion eligibility proven (proxy-single-client/required/ens)
- Record-only default preserved (broader promotion overreaches proven scope)
- Cross-plane skew, warmup behavior, rollback execution all proven
- Wire-derived timing reference comparator verdict passing

Deferred items:
- M8: deferred to `common-firmware-rewrite.locked`
- ISSUE-DOC-12: deferred tail item (tinyebus documentation follows firmware-rewrite)
- ISSUE-TE-01/TE-02: re-homed to `common-firmware-rewrite.locked`

## Blockers

None. All non-deferred milestones complete.

## Next Actions

None. Plan is in maintenance. Deferred items tracked in their respective plans.
