# Milestones — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f1129d0c442d3b2704f6f7e7eed2042c05df3f83e21ad57ccebdd6884f42241d`

Depends on: [11-decision-matrix.md](./11-decision-matrix.md), [13-acceptance-falsifiability-cross-plan.md](./13-acceptance-falsifiability-cross-plan.md).

Scope: All v1 milestones (M0_PLAN_LOCK..M8_TRANSPORT_VERIFY) with depends_on graph, repo assignment, scope, and acceptance criteria.

Idempotence contract: Each milestone has a stable identifier. Acceptance criteria are append-only with explicit revision; if a criterion is dropped or relaxed, plan canonical revises (v1.1) and chunk SHA256 re-pins. Milestone completion is asserted by linking the merged PR(s) in `99-status.md` per cruise-state-sync skill.

Falsifiability gate: Reviewer rejects a milestone PR if (a) acceptance is not satisfied; (b) the PR diff exceeds the documented scope without an amendment commit; (c) cross-plan invariants are violated (verified via `review-execution-plans` skill on plan-side PRs).

Coverage: 12 milestones in DAG order: M0_PLAN_LOCK → M0_DOC_GATE → M0A_TRANSPORT_BASELINE → (M1_TDD_RED_GATEWAY ∥ M1_TDD_RED_ADDON) → M2_GATEWAY_LOADER → M3_GATEWAY_PERSISTER → M4_JOINER_HINT → M5_ADDRESS_TABLE_REVALIDATE → M6_HA_ADDON_MIGRATION → M7_LIVE_VALIDATION → M8_TRANSPORT_VERIFY.

## M0_PLAN_LOCK

- **Repo:** `helianthus-execution-plans`
- **Scope:** Lock `runtime-state-w19-26` plan (chunks pass validator, SHA256 sync, 5 required headers, token caps). Append back-ref paragraph to `instance-identity-rediscovery.maintenance/00-canonical.md` documenting file-path migration (AD21).
- **Blocks:** M0_DOC_GATE
- **Acceptance:**
  - `validate_plans_repo.sh` green.
  - Back-ref present in rediscovery canonical.
  - Meta-issue created in `helianthus-execution-plans` and pinned with cruise-state-sync v1 comment.
  - Plan dir renamed `.draft → .locked`.

## M0_DOC_GATE

- **Repo:** `helianthus-docs-ebus`
- **Scope:** Normative schema doc ("Runtime State File") + JSON Schema artifact (`runtime_state.schema.json`) covering `meta` + `ebus.{self, known_bus_members[]}` v1 namespaces. Documents AD13 atomicity contract, AD09a/b add-on lifecycle, AD24 hint-vs-source-of-truth invariant. Cross-link from `instance-identity-rediscovery` doc section. Adds `make validate-schemas` target (using `santhosh-tekuri/jsonschema/cmd/jv`) wired into docs-ebus CI workflow. Validates the example payload AND ≥3 negative fixtures (out-of-range addr, invalid UUIDv4, missing required `meta.instance_guid`). 00-canonical doc-side notes the rationale for confidence/identity decoupling (per consultant NH-2).
- **Depends on:** M0_PLAN_LOCK
- **Blocks:** M1_TDD_RED_GATEWAY, M1_TDD_RED_ADDON, M2_GATEWAY_LOADER, M3_GATEWAY_PERSISTER, M4_JOINER_HINT, M5_ADDRESS_TABLE_REVALIDATE, M6_HA_ADDON_MIGRATION
- **Acceptance:**
  - Schema doc merged on docs-ebus main.
  - JSON Schema validates the example payload.
  - ≥3 negative fixtures validate as expected (rejected with appropriate error).
  - `make validate-schemas` green; CI step wired and runs on docs-ebus PRs.

## M0A_TRANSPORT_BASELINE

- **Repo:** `helianthus-ebusgateway`
- **Scope:** Capture 88-case transport-matrix index for current gateway main as baseline before any runtime-state code lands.
- **Acceptance:** `transport-matrix-baseline-runtime-state-w19-26.json` committed to gateway repo.

## M1_TDD_RED_GATEWAY

- **Repo:** `helianthus-ebusgateway`
- **Scope:** RED tests (per cruise-tdd-gate skill) for:
  - **Loader:** missing → empty; corrupt → quarantine + empty; per-plugin schema_version mismatch ignored.
  - **Persister:** atomic temp+rename, fsync semantics (temp required + parent best-effort with ENOTSUP/EINVAL/EPERM/ENOSYS swallowed), deterministic key order.
  - **Eager identity persist:** `meta.instance_guid` written within 1s of receiving `-instance-guid` flag (AD08).
  - **15-min jittered ticker** (AD14).
  - **EXDEV path:** test asserts old file preservation + temp unlink + `rename_exdev` metric increment + no partial state on disk (consultant MF-2 / Codex R5 A2).
  - **Concurrent write serialization:** simulated rename failure; disk-full failure path.
  - **P6 fault-injection** (consultant MF-2): kill -9 mid-write under simulated fsync-EINVAL via FS-abstraction layer (no LD_PRELOAD).
- **Depends on:** M0_DOC_GATE
- **Blocks:** M2_GATEWAY_LOADER, M3_GATEWAY_PERSISTER
- **Acceptance:** Tests committed and FAILING (RED) on a feature branch.

## M1_TDD_RED_ADDON

- **Repo:** `helianthus-ha-addon`
- **Scope:** RED tests for:
  - AD09b read precedence (5 cases, all using temp `/data` fixture per consultant SF-1):
    1. runtime_state valid → use it.
    2. legacy-only → AD09a halt.
    3. both absent → generate fresh + `HELIANTHUS_FRESH_IDENTITY` warn.
    4. mismatch → runtime wins, log warn.
    5. corrupt runtime + valid legacy → AD09a halt.
  - AD09a halt semantics: marker file `/data/.helianthus_migration_required` created with correct content; structured banner log line with `HELIANTHUS_MIGRATION_REQUIRED` token; exit code 1 (NOT 78).
  - AD27 `-instance-guid-source` flag pass-through (4 cases: `runtime_state`, `legacy_migrated`, `generated`, `cli-override`).
  - AD26 ENOENT retry logic: 3 attempts × 100ms backoff before falling through to AD09b precedence.
- **Depends on:** M0_DOC_GATE
- **Blocks:** M6_HA_ADDON_MIGRATION
- **Acceptance:** Tests RED on a feature branch.

## M2_GATEWAY_LOADER

- **Repo:** `helianthus-ebusgateway`
- **Scope:** Loader implementation: parses `meta` + `ebus`, exposes `RuntimeState` accessor type. Failure modes per AD11. Eager `meta.instance_guid` persist on receipt of `-instance-guid` flag (AD08). Loaded `known_bus_members` preserve original `last_source` (no `cached` synthetic value per AD16). Accepts bare `-instance-guid` as `cli-override` per AD27 with deprecation log + `helianthus_runtime_state_identity_source_total{source="cli-override"}` increment.
- **Depends on:** M1_TDD_RED_GATEWAY
- **Acceptance:** M1 RED tests pass GREEN.

## M3_GATEWAY_PERSISTER

- **Repo:** `helianthus-ebusgateway`
- **Scope:** Periodic + shutdown + on-event persister per AD13 crash-safety contract:
  - Single serialized writer.
  - Temp file in target dir; fsync(temp) required; fsync(parent_dir) best-effort.
  - EXDEV → write failure preserving old file + `rename_exdev` metric (no fallback path).
  - Retry on transient failure.
  - Metric `helianthus_runtime_state_write_total{reason}` (single metric, label values per consultant NH-3).
  - `known_bus_members[]` populated from address-table runtime events.
- **Depends on:** M2_GATEWAY_LOADER
- **Acceptance:**
  - M1 persister tests GREEN.
  - Live test shows file rewritten after 15 min and on graceful shutdown.
  - fsync verified via FS-abstraction unit tests (no strace dependency per consultant MF-2).
  - Live HA validation records observed `/data` mount type (overlayfs / ext4-loopback / virtiofs / tmpfs); informational, not pass/fail.

## M4_JOINER_HINT

- **Repo:** `helianthus-ebusgateway`
- **Scope:** Cached `ebus.self.last_join_initiator` becomes a HINT to the Joiner's bid-selection logic on direct transports. Joiner ALWAYS validates per locked `startup-admission-discovery-w17-26.maintenance` invariant; cache never bypasses warmup. On `JoinResult` success, write back to `ebus.self`. AD24 invariant test: pre-Joiner-validation, GraphQL `gatewayIdentity` and metric `helianthus_admitted_source` MUST report "not yet admitted" (or equivalent), NEVER the cached value.
- **Depends on:** M3_GATEWAY_PERSISTER
- **Acceptance:**
  - Joiner test: cache → hint → validate → accept (record back) succeeds.
  - Joiner test: cache → hint → reject → fall back to default policy (no cache mutation).
  - AD24 invariant test: pre-validation surfaces report not-yet-admitted, never the cached `last_join_initiator`.

## M5_ADDRESS_TABLE_REVALIDATE

- **Repo:** `helianthus-ebusgateway`
- **Scope:** After Joiner warmup completes (or NMNormal entry per `ebus-good-citizen-network-management.maintenance`), gateway issues directed `07 04` against cached `known_bus_members[*].addr` via `helianthus-ebusreg.ScanDirected`. Constraints:
  - **(a)** Skip members already passively re-observed during warmup.
  - **(b)** Bounded concurrency inherited from startup-admission rate limits.
  - **(c)** Cap = 32 startup probes per cycle (configurable internal const). **Cap rationale:** `07 04` directed probe is ~5-byte request + ~16-byte reply ≈ 21 bytes per round-trip; eBUS bus rate ~250 bytes/s under contention → ~84ms wall-clock per probe (conservative; ebusd defaults `--receivetimeout=25ms`, typical Vaillant slave responses single-digit ms; 84ms accounts for arbitration retries at 2400 baud); cap=32 → ~2.7s peak burst, well under Joiner warmup tail latency. Plan accepts that this estimate may be revised downward post-implementation if logic-analyzer measurement shows lower (consultant SF-3).
  - **(d)** No-reply outcome → AD23 immediate eviction + `ebus_runtime_state_revalidate_total{outcome="no_reply"}` telemetry.
  - **(e)** Responder → confidence=verified, last_source=directed_07_04, identity refreshed via address-table inserter normal path.
  - **Ordering:** cached members sorted by `last_seen_at` DESC (most recently active first), tie-break by `addr` ASC.
  - **Postponement:** members beyond cap=32 stay cached at unchanged confidence; revalidation resumes them in the NEXT 15-min cycle.
- **Depends on:** M4_JOINER_HINT
- **Acceptance:**
  - Live HA: cached BAI00/BASV2/VR_71 re-identified within 5s of Joiner warmup completion.
  - Counter `ebus_runtime_state_revalidate_total{outcome=responder|no_reply|skipped_passive_refresh}` increments correctly.
  - Synthetic test with 64 cached members confirms cap behavior: first 32 by `last_seen_at` probed; remaining 32 untouched but cached; next cycle probes them.
  - T01..T88 dry-run vs M0A baseline shows 0 unexpected fail/xpass deltas (transport-gate compliance per AD20).

## M6_HA_ADDON_MIGRATION

- **Repo:** `helianthus-ha-addon`
- **Scope:** Add-on implements AD09b precedence + AD09a deploy-error guardrail. Reads `meta.instance_guid` and passes via `-instance-guid` flag. STOPS writing `/data/instance_guid` (legacy file untouched on disk; preserved for audit). Passes `-instance-guid-source=<source>` per AD27 well-formed contract. AD26 ENOENT retries integrated.
- **Depends on:** M2_GATEWAY_LOADER, M1_TDD_RED_ADDON
- **Acceptance:**
  - Live HA preserves `instance_guid` across restart.
  - Legacy file no longer written by add-on (existence on disk preserved as audit only).
  - AD09a halt observed when migration is deliberately skipped (negative test):
    - **Default:** temp-fixture unit test (5 cases per M1_TDD_RED_ADDON; per consultant SF-7).
    - **Optional live test on operator's HA:** documented backup of `/data/runtime_state.json` and `/data/instance_guid` to `/tmp/migration-test-backup-<ISO8601>/`; trigger halt by removing `meta.instance_guid` from runtime_state.json; observe Supervisor logs contain AD09a message + exit code 1 + marker file present; restore backups; verify add-on starts successfully + gateway boots normally. Documented in M6 PR body.
  - Supervisor restart-loop CPU-budget test: exit-1 halt loop must not exceed N% CPU during restart-loop window (consultant MF-1 acceptance).

## M7_LIVE_VALIDATION

- **Repo:** `helianthus-ebusgateway` (live deploy)
- **Scope:** Operator deploys to live HA at 192.168.100.4. Verifies P1..P6 positive + N1..N4 negative (see `13-acceptance-falsifiability-cross-plan.md`). Includes corrupt-file injection test and AD09a halt test (with backup/restore precondition per M6).
- **Depends on:** M5_ADDRESS_TABLE_REVALIDATE, M6_HA_ADDON_MIGRATION
- **Acceptance:** All 6 positive + 4 negative assertions pass.

## M8_TRANSPORT_VERIFY

- **Repo:** `helianthus-ebusgateway`
- **Scope:** 88-case transport-matrix dry-run vs M0A baseline post-merge. AD20 transport-gate fulfillment.
- **Depends on:** M5_ADDRESS_TABLE_REVALIDATE
- **Acceptance:** 0 unexpected fail/xpass deltas.

## DAG summary

```
M0_PLAN_LOCK
   └── M0_DOC_GATE
         ├── M0A_TRANSPORT_BASELINE (parallel)
         ├── M1_TDD_RED_GATEWAY
         │     └── M2_GATEWAY_LOADER
         │           └── M3_GATEWAY_PERSISTER
         │                 └── M4_JOINER_HINT
         │                       └── M5_ADDRESS_TABLE_REVALIDATE
         │                             ├── M7_LIVE_VALIDATION
         │                             └── M8_TRANSPORT_VERIFY
         └── M1_TDD_RED_ADDON
               └── M6_HA_ADDON_MIGRATION
                     └── M7_LIVE_VALIDATION (joins gateway lane)
```

M5/M6 fan in to M7. M7 is the final acceptance gate; M8 confirms no transport regression.
