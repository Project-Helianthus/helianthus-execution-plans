# Acceptance, Falsifiability, Cross-Plan Integration — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f1129d0c442d3b2704f6f7e7eed2042c05df3f83e21ad57ccebdd6884f42241d`

Depends on: [10-architecture-overview.md](./10-architecture-overview.md), [11-decision-matrix.md](./11-decision-matrix.md), [12-milestones.md](./12-milestones.md).

Scope: Falsifiability gate (P1..P6 + N1..N4), cross-plan amendments and integration boundaries, deferred-to-v2 list.

Idempotence contract: Falsifiability assertions are append-only with explicit revision. P/N assertions cannot be silently dropped — removal requires canonical revision (v1.1) and chunk SHA256 re-pin. Cross-plan amendments listed here MUST match the actual `feedback_deprecation_enrichment.md`-style back-references appended to locked plan canonicals during M0_PLAN_LOCK.

Falsifiability gate: Live HA validation (M7) checks every P1..P6 positive and N1..N4 negative assertion. The plan FAILS to ship if any P assertion is false post-deploy or any N assertion is violated. Rollback procedure is documented per assertion.

Coverage: Full falsifiability gate + cross-plan integration matrix + v2-deferred items.

## Falsifiability gate — positive assertions (P1..P6)

After M5 + M6 merge + live deploy:

### P1 — Instance identity stable across restart

- **Procedure:** Restart gateway. Compare `runtime_state.json[meta][instance_guid]` to HA `config_entry.unique_id` for the Helianthus integration.
- **Expected:** Identical (no regen).

### P2 — Cached members re-identified within 5s of Joiner warmup completion

- **Procedure:** With cached `known_bus_members[]` containing `{0x08, 0x15, 0x26}` (BAI00, BASV2, VR_71), restart gateway. Observe time from Joiner warmup completion (log) to all three appearing as `confidence=verified, last_source=directed_07_04` in registry / GraphQL `devices`.
- **Expected:** ≤ 5 seconds.
- **Telemetry:** `ebus_runtime_state_revalidate_total{outcome="responder"}` increments by ≥3.

### P3 — Phantom address dropped after first failed `07 04`

- **Procedure:** Operator manually plants `0x99` (a known-non-existent address) in `runtime_state.json[ebus][known_bus_members][]` with `confidence=verified, last_source=directed_07_04`. Restart gateway.
- **Expected:** After M5 burst, `0x99` is absent from registry and from runtime_state.json; `ebus_runtime_state_revalidate_total{outcome="no_reply"}` increments by 1; no persisted no-reply state per AD23.

### P4 — Manual JSON corruption does not crash gateway

- **Procedure:** Operator corrupts `runtime_state.json` (e.g., truncates mid-file). Restart gateway.
- **Expected:** Gateway starts with empty cache; `runtime_state.json.corrupt-<ISO8601>` rename present; no panic / no abnormal exit; error log emitted with reason.
- **Note:** Add-on `AD09a` halt is M6 acceptance, separate from gateway P4. Add-on detects corrupt runtime + valid legacy as case (5) → AD09a halt; gateway P4 covers the gateway-side load-and-quarantine path.

### P5 — Transport matrix shows 0 diffs vs M0A baseline

- **Procedure:** Run 88-case transport-matrix dry-run on post-M5 main. Diff against `transport-matrix-baseline-runtime-state-w19-26.json` (captured at M0A).
- **Expected:** 0 unexpected fail/xpass deltas.

### P6 — Crash-during-write preserves old-or-new content

- **Procedure:** Fault-injection test (per consultant MF-2): kill -9 gateway during persister write under simulated `fsync(parent_dir)` returning EINVAL. Test uses FS-abstraction layer (no LD_PRELOAD; mockable in unit tests).
- **Expected:** Next start has fully old or fully new content; never partial. `helianthus_runtime_state_write_total{reason}` reflects the failure mode.
- **Live HA validation note:** records observed `/data` mount type (overlayfs / ext4-loopback / virtiofs / tmpfs) and parent-fsync support flag — informational, not pass/fail.

## Falsifiability gate — negative assertions (N1..N4)

### N1 — Cache cannot promote unidentified to verified without live `07 04` reply

- **Procedure:** With a cached entry at `confidence=unidentified`, restart gateway. Observe registry/GraphQL during M5 burst.
- **Expected:** No promotion to `verified` unless `07 04` reply observed in current session. (`corroborated` promotion via passive observation is permitted per AD15 but is a separate state.)

### N2 — Gateway never modifies `meta.instance_guid` after eager first-second persist

- **Procedure:** With known `meta.instance_guid=GUID-A` written via eager persist, induce a write trigger (15-min ticker / shutdown). Examine the rewritten file.
- **Expected:** `meta.instance_guid` unchanged. Only the add-on (next start) can change it via `-instance-guid` flag.

### N3 — Per-plugin schema_version mismatch ignored, gateway starts

- **Procedure:** Operator manually sets `runtime_state.json[ebus][schema_version] = 99`. Restart gateway.
- **Expected:** Gateway starts; `ebus.*` namespace ignored (cache empty); other namespaces (currently only `meta` in v1) load normally; warning log emitted with namespace name + observed/expected schema version.

### N4 — AD09a halt is mandatory; no silent regen

- **Procedure:** Operator deliberately skips manual migration: keeps `/data/instance_guid` (legacy) but does NOT create runtime_state.json. Restart add-on.
- **Expected:** Add-on emits `HELIANTHUS_MIGRATION_REQUIRED` log token; writes `/data/.helianthus_migration_required` marker; exits with code 1; gateway does NOT start; no new `instance_guid` generated. Default-tested via temp-fixture unit test (M1_TDD_RED_ADDON case 2).

## Cross-plan integration matrix

This plan extends locked plans rather than rewriting them, per
`feedback_deprecation_enrichment.md`.

### `instance-identity-rediscovery.maintenance` (consumed + amended via back-ref)

- **Amendment scope:** One paragraph appended to `00-canonical.md` documenting the file-path migration (`/data/instance_guid → /data/runtime_state.json[meta][instance_guid]`). Documented in AD21.
- **Invariants preserved:**
  - Add-on still owns `instance_guid` GENERATION.
  - HA `config_entry.unique_id == instanceGuid`.
  - Active GraphQL verification on rebind.
- **New invariant (AD09b case 4):** runtime_state authority wins on legacy/runtime mismatch; legacy is post-migration audit artifact only. Operator-confirmed decision.
- **M0_PLAN_LOCK action:** Append back-ref paragraph during plan lock; verify `validate_plans_repo.sh` accepts the rediscovery canonical edit.

### `address-table-registry-w19-26.maintenance` (consumed; not modified)

- **Integration:** Cached `known_bus_members` are seeded into the address-table inserter at startup. Cached entries enter the inserter at confidence equivalent to their persisted `confidence` (verified / corroborated / unidentified) but pre-validation are flagged as not-yet-current-session.
- **First passive observation OR directed `07 04`** in current session promotes confidence per address-table AD05 (positive ACK only) and AD06 (SN denylist).
- **No conflict** with address-table's `[256]*AddressSlot` storage primitive: cache is a secondary view that re-populates the registry on startup; the registry remains the in-memory authority during the session.

### `startup-admission-discovery-w17-26.maintenance` (consumed; not modified)

- **Integration:** Cached `ebus.self.last_join_initiator` is a HINT to the Joiner's bid-selection logic (M4). Joiner ALWAYS validates per locked invariant; cache never bypasses warmup.
- **AD24 enforcement:** Pre-validation, no surface (loader, GraphQL, MCP, metrics) reports cached `last_join_initiator` as the current admitted source. Current admitted source = current-session `JoinResult.Initiator` after validation.
- **M5 directed revalidation** uses `helianthus-ebusreg.ScanDirected` (locked API from startup-admission). M5 burst is bounded startup-window activity (cap=32, ~2.7s) — not steady-state polling.

### `ebus-good-citizen-network-management.maintenance` (consumed; cross-plan note in AD20)

- **Integration:** M5 startup burst is bounded startup-window activity, NOT steady-state NM cycle-time monitoring. NM cycle-time monitoring (per the good-citizen plan) starts AFTER M5 burst completes.
- **Cap=32 rationale:** documented in `12-milestones.md::M5` to confirm the burst is within the good-citizen plan's startup-window allowance.

## Out of v1 (deferred to v2)

- **GraphQL/MCP surface for identity-source provenance** — Codex R4 A1: violates MCP-first invariant if added directly as GraphQL. v2 will add MCP-first surface then GraphQL.
- **Stale-verified pruning** — consultant SF-2: cached entries that were verified once but stop responding without a gateway restart will not auto-prune in v1. v2 may add `last_verified_at` field + periodic in-session re-validation.
- **Stable schema URL for external `$ref`** — consultant NH-1: would benefit external tooling but not in v1 critical path.
- **USB hot-disconnect live test fixture** — consultant NH-5: requires hardware fixture; defer.
- **Hard rejection of bare `-instance-guid` flag** — Codex R5 A1: v1 is compat-first per AD27 to avoid cross-repo rollout hazard. v2 ships hard rejection once add-on rollout cycle is confirmed complete.
- **Persistence of identity-source under `meta.instance_guid_source`** — Codex R5 A2: v1 keeps identity-source as startup metric/log only; v2 may add persistence under `meta.*` (NOT `ebus.self`).
- **Other plugin namespaces (`gree.*`, `eebus.*`, `ebus.proxy_clients[]`)** — out of v1 scope by design.
- **Register-value caching, Prometheus-metric persistence** — operator-rejected after debate; documented in conversation history. Will not be added in any future version unless operator changes position.

## Rollback procedure

If any P1..P6 fails or any N1..N4 is violated post-deploy at M7:

1. Revert M5 PR (gateway directed revalidation) — closes the directed `07 04` burst risk.
2. Revert M4 PR (Joiner hint) — restores Joiner default policy.
3. Revert M3 PR (persister) — gateway no longer writes runtime_state.json (file may exist from prior runs; gateway treats it as input only).
4. Revert M2 PR (loader) — gateway ignores runtime_state.json entirely.
5. Revert M6 PR (add-on migration) — add-on resumes legacy `/data/instance_guid` write semantics.
6. M0_DOC_GATE PR may remain (no runtime impact).
7. M0_PLAN_LOCK back-ref amendment in rediscovery canonical may remain (documents the attempted migration; does not affect runtime).

The rollback decision MUST be made from the failed assertion log + a brief
incident note appended to `99-status.md`.
