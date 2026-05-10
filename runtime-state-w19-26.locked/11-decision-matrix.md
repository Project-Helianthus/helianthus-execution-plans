# Decision Matrix — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `9bd219258d7f447eab7398d3953c9bcc99bacc14979e6529a3448e2a08d23a8f`

Depends on: [10-architecture-overview.md](./10-architecture-overview.md), [12-milestones.md](./12-milestones.md), [13-acceptance-falsifiability-cross-plan.md](./13-acceptance-falsifiability-cross-plan.md).

Scope: AD01..AD27 — every architectural decision driving v1 implementation. Each AD names its source (operator decision / Codex round / consultant patch / cross-plan) so future review can trace provenance.

Idempotence contract: Every AD has a stable identifier. Editing an AD body is permitted only if the canonical and chunk SHA256 are re-pinned together. Adding ADxx (xx > 27) is permitted; removing or renumbering ADs requires a new canonical revision (v1.1).

Falsifiability gate: A milestone PR fails review if its acceptance does not satisfy the AD it claims. Reviewer cross-references AD↔milestone in `12-milestones.md` and flags any acceptance that drops or contradicts an AD without an explicit amendment commit.

Coverage: Full decision matrix.

## Schema and storage

- **AD01** Cache is observation persistence, never assumption. Static seed table model rejected by operator.
- **AD02** Startup re-identification via directed `07 04` against cached members; non-responders dropped (no carry-forward stale presence).
- **AD03** NM bits + passive observation handle joiners; cache only ACCELERATES what those mechanisms already do.
- **AD04** Plugin namespace `ebus.*`; future namespaces (`gree.*`, `eebus.*`, `ebus.proxy_clients[]`) deferred to v2.
- **AD05** Format = JSON, pretty-printed, deterministic key order. JSON Schema artifact ships alongside (`runtime_state.schema.json`). Validator pinned to `santhosh-tekuri/jsonschema/cmd/jv` (Go-native; same module the daemon could link if it ever runtime-validates). Per consultant MF-3: drops AJV-CLI to avoid Draft 2020-12 + format:uuid plugin pitfalls.
- **AD06** Path = `/data/runtime_state.json` (HA add-on writable persistent volume).

## Ownership and writers

- **AD07** Sole writer = gateway. Add-on never writes the file post-v1. Add-on still owns instance_guid GENERATION per locked rediscovery plan.
- **AD08** Gateway eagerly persists `meta.instance_guid` within first second of receiving `-instance-guid` flag (closes crash-before-first-periodic-persist window).

## Migration policy

- **AD09** Migration immediate; no read-fallback in code (operator-locked decision: "I'm the only user and we can manually migrate my guid during the deployment process"). Operator manually copies legacy `/data/instance_guid` value into `runtime_state.json[meta][instance_guid]` at deploy time. Add-on stops writing legacy file.

- **AD09a** **Deploy-error detector / guardrail.** At add-on startup, if (legacy `/data/instance_guid` is present AND parses as valid UUIDv4) AND (runtime_state.json absent OR `meta.instance_guid` absent or invalid), the add-on:
  1. Emits ONE structured banner log line with stable token `HELIANTHUS_MIGRATION_REQUIRED` and the actionable message: "Migration step missing: copy /data/instance_guid value into /data/runtime_state.json under meta.instance_guid, then restart".
  2. Writes a marker file `/data/.helianthus_migration_required` containing the same instructions in plaintext (operator-readable when inspecting `/data/`).
  3. Exits with code **1** (NOT sysexits-78 EX_CONFIG, per consultant MF-1: exit 78 collides with Docker convention noise — Elasticsearch vm.max_map_count, PHP-FPM init — and HA Supervisor doesn't differentiate non-zero exits anyway).
  4. HA Supervisor's restart-loop policy (Docker `restart=unless-stopped` + exponential backoff) handles cadence; no add-on-side rate limit needed.

  Add-on does NOT auto-recover from this state, does NOT generate a new instance_guid, and does NOT start the gateway in a degraded mode.

- **AD09b** **Add-on read precedence:**
  1. `runtime_state.json` valid + `meta.instance_guid` valid UUIDv4 → use it.
  2. Legacy file present + runtime_state.json invalid/absent → AD09a halt.
  3. Both files absent → generate fresh uuid4 (first-ever install path); emit `HELIANTHUS_FRESH_IDENTITY` warn log per AD25.
  4. Mismatch (runtime_state has GUID-A, legacy has GUID-B): runtime_state wins per operator decision; log warning. Legacy is post-migration audit artifact only.
  5. Corrupt runtime_state.json with valid legacy → AD09a halt (no silent fallback to legacy).

## Out-of-scope persistence

- **AD10** No Prometheus/metrics persistence. No register-value caching. Operator rejected after debate; rationale documented in conversation history (Prometheus reset-on-restart is contractual; persisting gauges produces stale-current-data lies; persisting counters provides no useful improvement over `process_start_time_seconds`).
- **AD11** Cache invalidation = manual subentry deletion (operator edits JSON). No implicit invalidation logic. Gateway never blocks startup on cache state. Failure modes: missing → empty start + log; corrupt → rename to `.corrupt-<ISO8601>` + empty start + log.

## Schema versioning

- **AD12** Schema versioning two-tier: top-level `schema_version` int + per-plugin `<plugin>.schema_version` int. Plugin mismatch = ignore that namespace, NEVER fail startup. Other namespaces still load.

## Crash-safety contract

- **AD13** **Atomic + crash-safe writes.**
  - Single serialized writer (mutex-guarded goroutine OR channel-serialized writes) — no concurrent writer interleaving.
  - Marshal full state to temp file **in target directory** (`/data/`) from start — eliminates EXDEV path under normal operation.
  - `fsync(temp)` REQUIRED.
  - `rename(temp → final)`.
  - `fsync(parent_dir)` BEST-EFFORT: swallow ENOTSUP, EINVAL, EPERM, ENOSYS (overlayfs / non-POSIX FS / stripped Alpine kernels); log at debug level + emit `helianthus_runtime_state_write_total{reason="parent_fsync_unsupported"}` (single metric, label values per consultant NH-3).
  - On `rename` returning EXDEV (precondition violation — should not happen since temp is in same directory; indicates filesystem misconfiguration): treat as write failure, OLD FILE REMAINS AUTHORITATIVE, unlink the orphan temp, emit `helianthus_runtime_state_write_total{reason="rename_exdev"}`, retry on next trigger. **NO non-atomic fallback path** (per Codex R5 A2 — write+fsync+unlink is not atomic and would violate AD13's "last-valid file preserved by rename atomicity" contract).
  - On marshal/write/rename other failures: keep in-memory state authoritative, emit `helianthus_runtime_state_write_total{reason="marshal|write|rename|fsync_temp"}`, retry on next trigger.

## Cadence

- **AD14** Write cadence: **shutdown** + **15-min jittered ticker** (±30s; jitter avoids synchronized fsync storms across multi-instance HA installs on shared NAS storage; per consultant NH-4) + on **`SourceAddressSelection.Source` change**. Tunable via internal const, not exposed to operator config in v1.

## Cache enums

- **AD15** `confidence` enum (persisted): `verified` | `corroborated` | `unidentified`. Reflects ADDRESS PRESENCE verification only (verified = directed `07 04` reply this session OR ≥2 corroborating passive samples; corroborated = single passive observation; unidentified = seen but no protocol-level reply). Identity completeness is orthogonal (per AD22).
- **AD16** `last_source` enum (persisted): `passive_observed` | `directed_07_04` | `nm_event`. **Excludes** `cached` (load-time provenance preserves original source) and `directed_07_04_no_reply` (no-reply members are dropped immediately, never persisted; per Codex R1 A6).
- **AD17** `selection_method` enum (persisted): `source_selection_warmup` | `override` | `explicit_validate_only` | `ebusd-tcp-fallback`.

## Capacity

- **AD18** Member cap 256 (one per eBUS address). No LRU; pruning via startup re-validation. With operator's bus typically <10 members, the cap is a defensive ceiling not a routine constraint.

## Gates

- **AD19** Doc-gate REQUIRED. Schema doc + JSON Schema artifact in `helianthus-docs-ebus`, MERGED before any gateway/addon code merges.
- **AD20** Transport-gate REQUIRED (changed from R1 not_required after Codex R1 A3). M5 directed-revalidation alters startup bus behavior; M0A baseline + M8 dry-run mandatory. Note: M5 startup burst is **bounded startup-window activity** (≤32 probes, ~2.7s estimated; cap rationale in `12-milestones.md::M5`), not steady-state NM cycle-time monitoring. NM cycle-time monitoring (per `ebus-good-citizen-network-management.maintenance`) starts AFTER M5 burst completes.

## Cross-plan integration

- **AD21** Plan amendment via back-reference to `instance-identity-rediscovery.maintenance/00-canonical.md` per `feedback_deprecation_enrichment.md`: extend, do not rewrite. Locked rediscovery plan invariants (add-on owns instance_guid generation; HA `config_entry.unique_id == instanceGuid`; active GraphQL verification on rebind) survive untouched. Mismatch resolution (AD09b case 4): runtime_state wins; legacy is post-migration audit artifact.

## Schema strict types

- **AD22** **JSON Schema strict types** using Draft 2020-12 (`$schema: "https://json-schema.org/draft/2020-12/schema"`).
  - `addr`, `companion_addr`: integers in `[0, 255]`.
  - `companion_addr` nullable when no valid companion exists per `address-table-w19-26.maintenance` AD03 bit-pattern rule.
  - `instance_guid` REQUIRED regex `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$` (lowercase UUIDv4). NEVER rely on `format: uuid` alone (would require AJV `ajv-formats` plugin; we use `jv` which doesn't have format-validation hangups but the regex is the explicit authority).
  - `identity` object OPTIONAL **regardless of confidence value** (decoupled per consultant SF-1 / Codex R2 A2).
  - `identity.{manufacturer, device_id, sn}` opaque strings when identity is non-null. No format enforcement on `sn` (manufacturer-specific encoding).
  - **Removed oneOf coupling** between confidence and identity: confidence reflects address-presence verification only; identity completeness is orthogonal.

## No-reply telemetry

- **AD23** No persistent no-reply telemetry. `directed_07_04_no_reply` outcomes during M5 revalidation increment `ebus_runtime_state_revalidate_total{outcome="no_reply"}` and trigger immediate cache eviction. No "tombstone" or "tried-but-failed" persisted state.

## Hint vs source-of-truth

- **AD24** `runtime_state.ebus.self` is **HISTORICAL HINT ONLY**. The current admitted source is exclusively the in-memory `SourceAddressSelection.Source` from the current session, AFTER SourceAddressSelector validation succeeds. No surface (loader, GraphQL, MCP, metrics) may expose `runtime_state.ebus.self` as the current admitted source until the current session's SourceAddressSelector validation passes. M4 includes a test asserting that pre-validation cached initiator is NOT reported as current/admitted via any surface.

## Fresh-identity diagnostics

- **AD25** On AD09b case (3) "both files absent, fresh uuid4 generated", add-on emits ONE structured warn log line with stable token `HELIANTHUS_FRESH_IDENTITY` and the actionable message ("Fresh instance_guid generated; if you have a prior HA integration entry for Helianthus, re-pair manually"). Metric `helianthus_runtime_state_identity_source_total{source}` increments once per startup. v1 does NOT persist identity-source in runtime_state.json or in `ebus.self.selection_method` (those are eBUS-domain semantics, not identity-domain — per Codex R5 A2). Persistence of identity-source under `meta.instance_guid_source` and v2-side surface exposure (GraphQL/MCP) deferred to v2 to preserve MCP-first invariant (per Codex R4 A1).

## Add-on read robustness

- **AD26** Add-on read path tolerates ENOENT on `/data/runtime_state.json` `open()` with bounded retries (3 attempts, 100ms backoff between) before falling through to AD09b precedence. Closes the gateway-write-vs-addon-read concurrent-window edge case during startup (gateway eagerly persists in first second; add-on may have already attempted to read).

## Add-on→gateway flag contract

- **AD27** **Compatibility-first v1**.
  - Add-on passes `-instance-guid-source=<source>` flag where source ∈ `{runtime_state, legacy_migrated, generated, cli-override}` (well-formed contract going forward).
  - Gateway accepts bare `-instance-guid` (without `-instance-guid-source`) as if `source=cli-override`, logs ONE deprecation warning ("--instance-guid-source flag missing; treating as cli-override; required in future release"), increments `helianthus_runtime_state_identity_source_total{source="cli-override"}`.
  - **No rejection in v1.** Hard rejection of bare `-instance-guid` deferred to v2 (post-operator-confirms-deploy-cycle-complete).
  - This avoids cross-repo rollout hazard: gateway can land first; add-on update can follow without breaking add-on startup (per Codex R5 A1).
