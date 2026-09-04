# Retained product acceptance from historical trackers

These are traceability inputs, not proof of a current defect and not a revival of the old workflow. Read current implementation and owning contracts first. Keep historical IDs and evidence; repair or explicitly disposition the remaining behavior. Protocol addresses and timing values below identify historical controlled scenarios, not universal defaults for every installation. Current repository applicability governs conformance gates.

Offline completion of each LEGACY item means reconciliation plus repository-local corrective/proof work is complete. It does not include live release acceptance; the remaining named P/N/live rows are owned by INT-20 and block INT-21. Thus INT-16/INT-17 can consume offline readiness without waiting on a hardware gate that itself requires the release candidate. No completion label may hide an unresolved physical/evidence gap.


The following is the minimum acceptance to carry forward. It preserves product assertions, not the old locked-plan hashes, workflow state, mandatory multiround process, or automatic post-merge actions.

### `LEGACY-PERSIST` — execution-plans #27

Historical tracker state at the pinned planning revision (reconcile against current code): implementation milestones M0-M6 and M8 are recorded merged; `M7_LIVE_VALIDATION` remains nonterminal. Source: `runtime-state-w19-26.implementing/99-status.md` at execution-plans HEAD `e6f77819d58e25a830e79848b40747cd10d07a3b`.

Retain these invariants in the owning gateway/add-on/docs issues:

- Path is `/data/runtime_state.json`; the gateway is sole writer. The add-on retains instance-GUID generation ownership and passes it to the gateway.
- Writes are serialized and atomic: temp file in `/data`, `fsync(temp)`, rename, best-effort parent fsync; EXDEV or another failure leaves the old file authoritative and has no non-atomic fallback.
- Migration has no silent legacy fallback. Valid runtime state wins a mismatch. Valid legacy plus absent/invalid runtime state emits `HELIANTHUS_MIGRATION_REQUIRED`, writes `/data/.helianthus_migration_required`, exits 1, does not start the gateway, and does not generate a new GUID. Both files absent is the explicit fresh-install path.
- Missing/corrupt state cannot crash the gateway; corrupt state is quarantined as `.corrupt-<ISO8601>`. A mismatched plugin schema version disables only that namespace.
- Cache is evidence, not presence authority. Current-session source admission and device verification require current evidence. No register-value or Prometheus-value persistence is introduced.

Exact P/N checklist from `runtime-state-w19-26.implementing/13-acceptance-falsifiability-cross-plan.md`:

| ID | Retained assertion |
|---|---|
| P1 | After gateway restart, `runtime_state.json.meta.instance_guid` equals the HA integration `config_entry.unique_id`; no regeneration. |
| P2 | Cached `0x08`, `0x15`, and `0x26` become `verified` with `last_source=directed_07_04` within 5 seconds after SourceAddressSelector warmup; responder metric increases by at least 3. |
| P3 | A planted cached phantom `0x99` is removed after the first failed `07 04`, is absent from registry and persisted state, and increments the no-reply metric once. |
| P4 | Truncated/corrupt runtime JSON causes quarantine plus empty-cache startup, an error log, and no panic/abnormal gateway exit. The add-on's corrupt-runtime plus valid-legacy case still follows N4. |
| P5 | T01..T88 post-change transport topology has zero unexpected fail and zero unexpected xpass deltas from its baseline. |
| P6 | Killing the gateway during a write leaves a wholly old or wholly new file, never partial content; the write-reason metric records the fault. |
| N1 | Cached `unidentified` cannot become `verified` without a current-session `07 04` reply; separately evidenced passive corroboration remains a distinct state. |
| N2 | Later write triggers never change `meta.instance_guid` after its eager first-second persist. |
| N3 | `ebus.schema_version=99` is ignored per namespace; gateway startup and other namespaces continue with a warning. |
| N4 | Skipped manual migration yields the stable token, marker, exit 1, no gateway start, and no generated replacement GUID. |

Mapping: provider-local and fault-injection tests plus P5 block `INT-16/INT-17`; operator-run/live assertions are named rows in `INT-20`; all P/N results or an explicit scope-specific Board waiver block `INT-21`. Keep #27 open until that mapping and evidence exist.

### `LEGACY-IDENTITY` — execution-plans #23

Historical tracker state at the pinned planning revision (reconcile against current code): most Phase A/C work is merged, but Phase-A live acceptance is not complete. `TAP_SYN_FIX` is not started; the status records passive tap delimiter loss, false source classifications, and blocked `0xF1` detection. Phase B remains deferred. Source: `address-table-registry-w19-26.maintenance/99-status.md` at the same exact execution-plans HEAD.

Exact Phase-A P/N checklist from `address-table-registry-w19-26.maintenance/13-acceptance-criteria-and-falsifiability.md`:

| ID | Retained assertion |
|---|---|
| P1 | With static seeds off, passive `0xF1` observations produce companion `0xF6` as `passive_observed/corroborated` only after the required second corroboration. |
| P2 | With static seeds on, `0x04` appears as `static_seed/candidate`. |
| P3 | With static seeds on, `0xEC` appears as `static_seed/candidate`. |
| P4 | Existing `0x08`, `0x15`, and `0x26` devices remain `identity_confirmed`; no regression. |
| P5 | Bus admission remains active with selected source `0x7F`, companion target `0x84`, and successful active-probe outcome. |
| P6 | T01..T88 has zero unexpected fail/xpass deltas; infra-blocked cases retain the declared reason. |
| N1 | NACK-only traffic for nonexistent `0x99` does not insert a device. |
| N2 | Broadcast bytes `0xFE`/`0xFF` do not become device slots merely from destination class. |
| N3 | ACK-position byte `0xFF` does not insert unless separately evidenced as a frame-start source/destination. |
| N4 | Gateway self source `0x7F` is not inserted as a device. |
| N5 | One corroboration cannot insert companion `0xF6`; the second qualifying observation after the window must insert it. |

Also retain HA compatibility: existing entity identities remain stable; candidate-derived entities are intentionally filtered or clearly tagged; HA does not crash or create arbitrary/spurious entities.

The successor must disposition the remaining work explicitly:

1. `TAP_SYN_FIX`: preserve SYN delimiters between passive frames; eliminate mid-frame false-source classification; recover `0xF1` observation; add negative controls for false addresses; rerun the exact Phase-A P/N and transport criteria.
2. Phase B M6: merge slots only on a complete matching manufacturer/device-ID/serial triple; deny at least serials `0`, `0xFFFFFFFF`, and `0x7FFFFFFF`; merge `0x15` and `0xEC` in the positive case; refuse zero/partial identity; promote a seeded candidate only after qualified identity evidence.
3. Phase B M7: make address-table insertion/merge events the EvidenceBuffer source; remove the direct passive-frame path; keep any legacy kill switch bounded to one release; prove identical visible behavior and T01..T88 parity.

Mapping: `TAP_SYN_FIX`/Phase-B provider and integration work must have repository-owned issues; their offline evidence blocks `INT-17`, live assertions are rows in `INT-20`, and unresolved criteria block `INT-21`. Reconcile the remaining Phase-B requirements against current code and the current Board scope. Do not silently drop accepted behavior or automatically revive previously deferred implementation mechanisms; preserve any explicit prior deferral until it is superseded by the current semantic/driver design or a Board decision. Keep #23 open until the successor records that disposition.

### `LEGACY-MUX` — execution-plans #30

Historical tracker state at the pinned planning revision (reconcile against current code): `M4_NO_GO`; no rollback, waiver, or corrective plan selected. The historical correction only forwards the first unexpected master-class byte before any echo match so the existing collision classifier can retry. It does not relax arbitrary bytes, later positions, missing later echoes, or response-phase interleaving.

Minimum corrective-successor acceptance:

- Preserve or deliberately replace the narrow predicate: pending echo, zero matched bytes, first write byte, unexpected master-class symbol. The byte must reach the existing collision classifier; do not drop it or broaden the bypass to later/noise bytes.
- Add deterministic positive and negative tests for first-byte arbitration loss and separate tests/disposition for later missing echo and response-interleaving modes.
- Retain the historical 500 contention events/hour floor when reproducing that exact qualification claim; a quieter window cannot be relabelled as its GO. First inspect the current implementation and published contract. If the new acceptance uses a different controlled contention method, document how it covers the old failure mode and distinguish the new result from historical qualification; do not infer a waiver.
- Preserve the original observable targets: all 12 B524-backed MCP planes non-null within 60 seconds of add-on startup; `discoverB524Root` resolves `0x15` within 60 seconds of request start; `round9_absorb_entered_total` slope is 0/min over 90 minutes; post-grant ACK rate is at most 10/hour; collision rate is at most 1.5 times the recorded baseline (historically about 825/hour).
- Rerun applicable race/unit/integration tests and T01..T88 with no unexpected fail/xpass; verify the exact gateway/add-on package/BOM used for the live result.
- If the selected outcome is rollback, prove restoration against the same deterministic and live criteria. If it is waiver, record the exact unqualified mode, affected products, operational limit, expiry/revisit condition, and explicit Board decision.

Mapping: selected disposition and offline evidence block `INT-16/INT-17`; live qualification belongs in `INT-20`; any code/package change after Daybreak requires fresh exact-HEAD review and affected revalidation before `INT-21`.
