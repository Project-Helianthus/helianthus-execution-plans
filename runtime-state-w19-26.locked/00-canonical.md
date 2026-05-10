# Runtime State File — /data/runtime_state.json

State: `draft` (will become `locked` post-validator)
Slug: `runtime-state-w19-26`
Started: `2026-05-10`
Planner: `Codex gpt-5.5 high (6 adversarial rounds, ready_to_lock=true at R6)`
Consultant: `Claude consultant subagent (mandatory web research per AGENTS.md §8.4) — GO with 3 MUST-FIX patches integrated into v3..v5`

## Summary

Add a persistent runtime state file at `/data/runtime_state.json` (HA add-on
persistent volume) consolidating gateway-owned daemon state across restarts.
v1 namespaces: `meta` (instance_guid + write metadata) and `ebus.{self,
known_bus_members[]}` (cached admitted source + observed device cache for
startup acceleration via directed `07 04` re-validation).

Sole writer is the gateway. The HA add-on reads `meta.instance_guid` once at
startup and passes it via the existing `-instance-guid` flag (locked
rediscovery contract). The add-on no longer writes the legacy
`/data/instance_guid` file.

The cache is **observation persistence, never assumption**. At startup,
cached known bus members are re-identified via directed `07 04` against each
cached address; non-responders are dropped immediately. This accelerates the
existing passive-first discovery pipeline without ever asserting the presence
of a device that did not respond this session.

## Lifecycle note

This plan is the v1 of runtime daemon state for Helianthus. Future plugin
namespaces (`gree.*`, `eebus.*`, `ebus.proxy_clients[]`) reuse the schema
versioning, atomicity contract, and add-on-vs-gateway ownership boundary
established here. v2 surface exposure (GraphQL/MCP identity-source field) and
v2 features (stale-verified pruning, stable schema URL, USB hot-disconnect
live test) are explicitly out of v1 scope.

## Objective

Provide a single, gateway-owned, JSON-formatted, atomically-written runtime
state file under `/data/runtime_state.json` that:

1. Carries the canonical Helianthus instance identity (`meta.instance_guid`)
   while preserving the locked rediscovery-plan invariants (add-on owns
   generation; HA `config_entry.unique_id == instanceGuid`; identity stable
   across restarts).
2. Caches the most recent successful Joiner result (`ebus.self.last_admitted_source`,
   `last_admitted_at`, `selection_method`, `companion_target`) to use as a HINT for
   subsequent Joiner sessions. The cache never bypasses SourceAddressSelector validation.
3. Caches observed bus members (`ebus.known_bus_members[]`) for startup
   acceleration via bounded directed `07 04` re-validation. Cache is wiped
   per-startup of any non-responder; verified responders' confidence is
   refreshed in cache.
4. Establishes a plugin-namespaced schema (`ebus.*`) with two-tier
   versioning (`schema_version` top-level + `<plugin>.schema_version`)
   permitting future namespaces to coexist without cross-plugin coupling.

## Scope

In scope (v1):

- Plan + back-ref amendment in
  `instance-identity-rediscovery.maintenance/00-canonical.md` (per
  `feedback_deprecation_enrichment.md`: extend, do not rewrite).
- Normative schema documentation + JSON Schema artifact
  (`runtime_state.schema.json`) in `helianthus-docs-ebus`.
- JSON Schema validation step in docs-ebus CI using
  `santhosh-tekuri/jsonschema/cmd/jv` (Go-native; same module the daemon
  could link if it ever runtime-validates).
- Gateway loader, persister, eager `meta.instance_guid` first-second
  persist, 15-min jittered ticker, shutdown hook, `SourceAddressSelection.Source`
  change subscriber.
- Gateway: cached `ebus.self.last_admitted_source` becomes a hint to the
  Joiner's bid selection (locked startup-admission plan invariant: Joiner
  always validates; cache never bypasses warmup).
- Gateway: post-SourceAddressSelector warmup directed `07 04` revalidation of cached
  known_bus_members[] via `helianthus-ebusreg.ScanDirected`, bounded to 32
  probes per cycle, ordered by `last_seen_at` DESC.
- HA add-on: AD09b read precedence; AD09a deploy-error guardrail
  (legacy-detected-without-runtime-state → exit 1 + marker file +
  `HELIANTHUS_MIGRATION_REQUIRED` log token); AD27 `-instance-guid-source`
  flag (compat-first: gateway accepts bare `-instance-guid` as
  `cli-override` with deprecation warning).
- Atomic + crash-safe writes (single serialized writer; temp in target
  dir; fsync(temp) required; fsync(parent_dir) best-effort with
  ENOTSUP/EINVAL/EPERM/ENOSYS swallowed; EXDEV treated as write failure
  preserving old file).
- Transport-gate: 88-case dry-run baseline at M0A and re-verify at M8.

Out of scope (v2 deferred):

- GraphQL / MCP surface for identity-source provenance.
- Stale-verified pruning (cached entries that were verified once but stop
  responding without a gateway restart).
- Stable schema URL for external `$ref`.
- USB hot-disconnect live test fixture.
- Hard rejection of bare `-instance-guid` (compat-first in v1; rejection
  in v2 once add-on rollout cycle is confirmed).
- Persistence of identity-source under `meta.instance_guid_source`.
- Other plugin namespaces (`gree.*`, `eebus.*`, `ebus.proxy_clients[]`).
- Register-value caching, Prometheus-metric persistence (operator
  rejected after debate).

## Decision matrix

The full decision matrix (AD01–AD27) is documented in
`11-decision-matrix.md`. The following are highlights with cross-plan
references.

- **AD01–AD03** (cache-as-observation, `07 04` re-validation, NM/passive
  delegation): Cache only accelerates; never asserts presence. Aligns with
  `address-table-registry-w19-26.maintenance` AD05 (positive ACK only) and
  `startup-admission-discovery-w17-26.maintenance` (passive-first evidence).
- **AD04** plugin namespace `ebus.*`: future plugins reuse schema
  scaffolding without cross-plugin coupling.
- **AD05** JSON Draft 2020-12; validator
  `santhosh-tekuri/jsonschema/cmd/jv` (drops AJV-CLI per consultant MF-3).
- **AD07** sole writer = gateway: add-on never writes runtime_state.json.
  Add-on still owns instance_guid generation per locked rediscovery plan.
- **AD08** eager first-second `meta.instance_guid` persist: closes
  crash-before-first-periodic-persist window.
- **AD09 / AD09a / AD09b**: hard manual migration policy with deploy-error
  guardrail. No legacy read-fallback in code per operator decision. Add-on
  emits `HELIANTHUS_MIGRATION_REQUIRED` token + marker file + exit 1 (NOT
  78; consultant MF-1 found exit 78 collides with Docker convention noise).
- **AD13** atomic writes: temp file in target dir from start (eliminates
  EXDEV in normal operation); fsync(temp) required; fsync(parent_dir)
  best-effort. EXDEV treated as write failure preserving old file (no
  non-atomic fallback path; consultant + Codex R5 A2).
- **AD14** write cadence: shutdown + 15-min jittered ticker (±30s) + on
  `SourceAddressSelection.Source` change. Jitter avoids synchronized fsync storms
  across multi-instance HA installs.
- **AD15 / AD16**: `confidence` and `last_source` enums for cached
  members. Persisted enums exclude `cached` and `directed_07_04_no_reply`
  per Codex R1 A6 (load-time provenance preserves original source; no-reply
  drives immediate eviction, never persists).
- **AD20** transport-gate REQUIRED (changed from R1 not_required after
  Codex R1 A3): M5 directed-revalidation alters startup bus behavior.
- **AD22** JSON Schema strict types Draft 2020-12; UUIDv4 regex enforced;
  identity object OPTIONAL regardless of confidence value (decoupled per
  consultant SF-1 / Codex R2 A2: confidence reflects address-presence
  verification only; identity completeness is orthogonal).
- **AD24** `ebus.self` is HISTORICAL HINT ONLY: current admitted source
  is exclusively current-session `SourceAddressSelection.Source` after validation.
  No surface (GraphQL/MCP/metrics) reports cached value as "current"
  pre-validation.
- **AD27** compat-first v1: gateway accepts bare `-instance-guid` as
  `cli-override` with deprecation log; hard rejection deferred to v2 to
  avoid cross-repo rollout hazard (Codex R5 A1).

## Schema (v1)

```json
{
  "schema_version": 1,
  "meta": {
    "instance_guid": "8a3f2b9e-4d7c-4f1a-9b5e-2c1f3e7a9d5b",
    "written_at": "2026-05-10T19:42:11Z",
    "gateway_build": "1.2.3-abc123",
    "addon_version": "0.4.7"
  },
  "ebus": {
    "schema_version": 1,
    "self": {
      "last_admitted_source": 247,
      "last_admitted_at": "2026-05-10T19:38:55Z",
      "selection_method": "source_selection_warmup",
      "companion_target": 252
    },
    "known_bus_members": [
      {
        "addr": 8,
        "companion_addr": 13,
        "identity": {
          "manufacturer": "Vaillant",
          "device_id": "BAI00",
          "sn": "0x21000567"
        },
        "last_seen_at": "2026-05-10T19:39:55Z",
        "last_source": "passive_observed",
        "confidence": "verified"
      }
    ]
  }
}
```

The `runtime_state.schema.json` artifact in `helianthus-docs-ebus`
(M0_DOC_GATE) is the normative validator. It is referenced by docs-ebus CI
via `santhosh-tekuri/jsonschema/cmd/jv` and validates the example payload
plus negative fixtures (out-of-range addr, invalid UUIDv4, missing required
`meta.instance_guid`).

## Phase milestones

`M0_PLAN_LOCK → M0_DOC_GATE → M0A_TRANSPORT_BASELINE → M1_TDD_RED_GATEWAY (parallel
M1_TDD_RED_ADDON) → M2_GATEWAY_LOADER → M3_GATEWAY_PERSISTER → M4_JOINER_HINT →
M5_ADDRESS_TABLE_REVALIDATE → M6_HA_ADDON_MIGRATION → M7_LIVE_VALIDATION →
M8_TRANSPORT_VERIFY`

Detailed milestone scope, blocks, and acceptance criteria: see
`12-milestones.md`.

## Falsifiability gate

After M5 + M6 merge + live deploy:

**Positive (P1–P6):**

- **P1** Instance identity stable across gateway restart: `runtime_state.json[meta][instance_guid]` matches HA `config_entry.unique_id` (no regen).
- **P2** Cached known_bus_members for `{0x08, 0x15, 0x26}` are re-identified via directed `07 04` within 5s of SourceAddressSelector warmup completion.
- **P3** Phantom address (operator manually plants `0x99` in cache) is dropped from cache after first failed `07 04` (no_reply outcome → immediate eviction + telemetry; no persisted no-reply state per AD23).
- **P4** Manual JSON corruption results in gateway start with empty cache + `runtime_state.json.corrupt-<ISO8601>` rename, no crash.
- **P5** 88-case transport matrix vs M0A baseline shows 0 unexpected fail/xpass deltas.
- **P6** Fault-injection test: kill -9 gateway during persister write under simulated fsync-EINVAL → next start has fully old or fully new content; never partial. Test uses FS-abstraction layer (no LD_PRELOAD; mockable in unit tests).

**Negative (N1–N4):**

- **N1** Cache cannot promote `unidentified` to `verified` without a live `07 04` reply within session.
- **N2** Gateway never modifies `meta.instance_guid` after the eager first-second persist; only the add-on (next start) can change it via flag.
- **N3** Per-plugin schema_version mismatch (e.g., `ebus.schema_version=99`) does NOT crash gateway; the namespace is ignored, others load.
- **N4** AD09a halt is mandatory when legacy `/data/instance_guid` is present without runtime_state.json migration; add-on does NOT silently regenerate identity.

Detail: `13-acceptance-falsifiability-cross-plan.md`.

## Cross-plan integration

This plan extends locked plans rather than rewriting them, per
`feedback_deprecation_enrichment.md`:

- `instance-identity-rediscovery.maintenance/00-canonical.md` receives a
  one-paragraph back-ref amendment (AD21) documenting the file-path move
  (`/data/instance_guid → /data/runtime_state.json[meta][instance_guid]`)
  and clarifying that the locked-plan invariants survive (add-on owns
  generation; HA `config_entry.unique_id == instanceGuid`; active GraphQL
  verification on rebind). Mismatch resolution: runtime_state authority
  wins, legacy is post-migration audit artifact only.
- `address-table-registry-w19-26.maintenance` is consumed but not
  modified: cached known_bus_members are seeded into the address-table
  inserter at `confidence=cached` (lower than `passive_observed`); first
  passive observation OR directed `07 04` confirms promote to `verified`.
- `startup-admission-discovery-w17-26.maintenance` is consumed but not
  modified: cached `ebus.self.last_admitted_source` is a hint to the
  Joiner; Joiner always validates per locked invariant; M5 directed
  revalidation uses `helianthus-ebusreg.ScanDirected` (locked API).
- `ebus-good-citizen-network-management.maintenance` is consumed: M5
  startup burst is bounded startup-window activity (≤32 probes, ~2.7s
  estimated), not steady-state NM cycle-time monitoring. NM cycle-time
  monitoring begins AFTER M5 burst completes.

## References

- Codex adversarial planning thread: 6 rounds (R1..R6), gpt-5.5 high
  reasoning, threadId `019e1235-62fd-7521-b551-eee8f7b6a94d`.
- Claude consultant validation: GO recommendation with 3 MUST-FIX patches
  (MF-1 exit-code semantics, MF-2 fsync portability + EXDEV, MF-3 schema
  validator pin). All integrated into v3..v5.
- Operator decisions captured: no legacy read-fallback (manual deploy
  step); JSON over TOML; runtime_state name (vs runtime_config); single-
  writer-after-start (now sole-writer = gateway); no metrics/data
  persistence; AD09b case (4) mismatch → runtime wins.
- Locked plans referenced: `instance-identity-rediscovery.maintenance`,
  `address-table-registry-w19-26.maintenance`,
  `startup-admission-discovery-w17-26.maintenance`,
  `ebus-good-citizen-network-management.maintenance`.
- Operator-feedback policy:
  `feedback_deprecation_enrichment.md` (extend locked plans, do not
  rewrite).
- HA add-on `/data/` persistence convention: HA developer docs +
  reference impls (Mosquitto, ESPHome, Z2M).
- Schema validator: `santhosh-tekuri/jsonschema/cmd/jv` (Go-native,
  Draft 2020-12 native).
