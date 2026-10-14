# Release phases

Canonical-SHA256: `d7f28882f3b117c568b95c25fbf5a5d44638f465e90d67a1a700c7788b380730`
Depends on: [13-surface-targets.md](./13-surface-targets.md).
Scope: 0.7 seams and ordered 0.8 moves.
Idempotence contract: Re-reading creates no work; fixtures preserve outputs; lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the node.
Coverage: Canonical section 4; 90 and 91 maps.

## 4. Phased delivery

### 0.7 — seams, not full family extraction

1. Retain G4/#1024 semantic hub behavior and characterization-first discipline. Hub then three kernel owners; inventory is unmerged G4 PR #1028 head. Require merged #1024; no live CI claim. Reconcile merged contract/deviations before G5.
2. G5 drivers/durable ebus.primary lifecycle: O6/D5 default PR 0a gateway-owned semhub hooks export/restore complete accepted record incl. control transitions, no SemReg change (Cx 5; issue Cx 9 with/without O2 PR 0b). O6 alternative: external SemReg snapshot-restore API replaces PR 0a; issue Cx 8. PR 0b A2 succession only for O2 new epoch (Cx 5; public docs before/with it); PR 1 goldens/registration/store/service/eBUS/write-ahead record/replay/restoration test (Cx 8); PR 2 kernel boundary/tools (Cx 4). O7/90. Keep v1/direction fixtures without hooks, eBUS-only controls, S1–S6/D1–D6, shell-first startup, lifecycle-only bridge and recovery boundaries; no family extraction, thermal cutover or full public lifecycle API.
3. Four scoped managed-runtime adapters: SunSpec TCP, Growatt RTU, eeBUS, Tesla (G5 follow-ups, Cx 7 each). They transfer start/close ownership to registration, not whole protocols. A retained-only Tesla adapter reports its actual resource; it does not invent a live writer. No managed placeholder accepts nonfunctional controls.
4. G6 generic registry becomes **driver composition**: needs G5; named M items gate compositions, native providers/qualification stay in drivers. Compose only profiles admitted by M/C evidence; represent blocked families truthfully. G7 CAN and G7b Tesla outcome producer retain their prerequisites; publication/native operations are not granted by registration.
5. DM-RAW/#1021 follows DM-G5 and satisfied R-G2C. eBUS owns raw identity/promotion/traffic/specimen stores and provenance via contributed read views. G2’s site smoke is a dispatch-time overlap constraint on the same raw 07 04 identification evidence, not a prerequisite. No bytes move to SemReg or a universal raw schema; wider eBUS extraction waits for 0.8.

No other family moves into driver ownership packages in 0.7. G8–G19 integration, configuration, consumers and rename retain accepted outcomes, scope and closure gates; only their seams change. Provider/sidecar IDs remain unfiled.

G8 uses eBUS-owned thermal projections and keeps D4/HA parity. G9a migrates eeBUS inbound with candidate/unknown; G9b freezes only after STD-01. G10 infrastructure keeps native mapping ownership. G11 public/downward contracts wait for G5 and G6 registry; G12 waits for G7b. G13 Portal consumes contributions; G14/#999–1002 remains primary config/listener work, with P1 and Matter contracts first. G15/G15b metrics remain integrated/BOM acceptance, G16 native mux work remains eBUS, G17a/b retain eeBUS owner/STD-01 checkpoints. G18 rename remains sequential after INT-10/11/12/13/15, and G19 waits for docs naming migration. A7 exact-BOM, Daybreak and physical acceptance are unchanged.

### 0.8 — family moves in measured order

Accepted 0.7/INT-21 is the external start prerequisite; coordinate the existing locked 0.8 declarative guide's DRIVER-EXTRACTION-01/INT-18 so there is one work program. Prioritize **CAN → Modbus → eeBUS → eBUS**. Coupling counts, not extraction estimates; overlapping mixed files are not summed:

| Family order | GW source files/lines; tests | Risk/cost rationale and bounded split |
|---|---|---|
| CAN | 2 / 285; 9 tests | Smallest gateway footprint; transport missing from supplied scope is a prerequisite, not low-risk proof. Start with ownership/transport boundary reconciliation, then move DTO/composition surfaces after G7. Cx 4 + 5. |
| Modbus | 32 / 7,950; 246 tests | Three existing semantic publishers and distinct TCP/RTU/retained lifetimes. Move construction/acquisition first, then MCP/GraphQL/Portal/setup/state/metrics and legacy minters; preserve all provider dispositions. Cx 7 + 6. |
| eeBUS | 87 / 27,095; 382 tests | Trust, listener/client slots, raw mutations, participation and cross-native capture make extraction risk higher. Separate native runtime/trust/evidence from overlays/contributions/setup. Cx 8 + 7. |
| eBUS | 111 / 70,048; 1,865 tests | Largest and deepest host coupling: default Gateway/MCP/GraphQL, scans/passive/cache/B503/mux, state and gates. Split transport/admission/evidence, polling/qualification/state, public/setup/metrics contributions, then remove mandatory eBUS host construction. Cx 8 + 8 + 8 + 6. |

Counts and anchors are [inventory](./reference-inventory.md) §6 (`GW mcp/growatt_bms_v104_v1.go:1`, `internal/modbusadapter/adapter.go:122`, `cmd/gateway/eebus_runtime_adapter.go:350`, `gateway.go:22`). Native trees stay separately owned (eBUS transport 13,074 lines and registry 10,099; Modbus transport 17,376 and registry 20,392; eeBUS native 44,153; CAN registry 1,359). Re-estimate from exact manifests; test counts do not prove effort/coverage. Respect one issue per owning repo and serial repository integration; priority order may pause for unavailable evidence but a Board change must record any reordering.

DM-HOOKS completes typed MCP/GraphQL/Portal/setup/state/metrics contributions with hook fixtures per direction, without native switches. A no-eBUS fixture must boot shell, config, M2M, semantic exporter and another driver. Family acceptance covers all applicable section 3 surfaces, not just family-named files. Compile native modules separately from host; package names are implementation choices, not repository mandates.
