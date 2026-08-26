# Implementation Milestones

Canonical-SHA256: `0675509fd10408c4102f15b108f8152e1fd985293f14f7f870b3bc4176bab720`

Depends on: `10-terminology-and-api-contract.md`

Scope: Cross-repo sequencing for `helianthus-docs-ebus`,
`helianthus-ebusgo`, `helianthus-ebusgateway`, `helianthus-ha-addon`,
`helianthus-ebusreg`, and `helianthus-ha-integration`.

Idempotence contract: Each milestone is independently repeatable. Re-running a
milestone after merge must not create duplicate docs, resurrect old public
names, or create a second source-selection path.

Falsifiability gate: A reviewer can reject this chunk if any milestone requires
gateway to duplicate candidate policy, conflates standard source description
with priority, requires ebusreg to know admission semantics, or allows gateway
to continue active startup probes with a source that already failed validation.

Coverage: Milestone order, repository responsibilities, merge blockers,
doc-gate, transport-gate, HA degraded-state gate, and cleanup.

Universal PR gate: every milestone PR includes repo-local CI evidence at PR
head: command, commit SHA, artifact/log path, and `Local-CI: pass@<sha>` or
the repository's accepted equivalent.

## M0 - Plan Draft And Lock

Primary repo: `helianthus-execution-plans`

Deliverables:

- create this execution plan;
- run adversarial review;
- promote to `.locked` only after review convergence and operator approval.

Acceptance:

- plan contains `plan.yaml`, canonical, split index, issue map, milestone map,
  and status;
- target repos and merge order are explicit;
- doc-gate and transport-gate are marked required.

## M1 - Docs Source Address Selection

Primary repo: `helianthus-docs-ebus`

Deliverables:

- add or update startup admission architecture docs with source address
  selection terminology;
- freeze the standard source-address table, priority-index mapping,
  arbitration-nibble mapping, and all 25 companion mappings in Markdown;
- give the source-address table anchor `#ebus-source-address-table-v1`, table
  version `ebus-source-address-table/v1`, and SHA-256 hash over normalized
  Markdown table bytes for ebusgo tests; current normalized table hash is
  `e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103`;
- cite `docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:28-60`,
  `docs/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:69-77`,
  `docs/Spec_Prot_12_V1_3_1_E.en.md:178-184`,
  `docs/Spec_Prot_12_V1_3_1_E.en.md:254-256`,
  `docs/Spec_Prot_12_V1_3_1_E.en.md:320-349`,
  `docs/SRC/Spec_Prot_12_V1_3_1_E.md:320-349`, and
  `docs/Spec_Prot_12_V1_3_1_E.en.md:471-478`;
- add docs CI that checks every frozen source-address row against those local
  official spec excerpts before ebusgo tests can consume the table. The checker
  has an explicit spec-root contract:
  `HELIANTHUS_OFFICIAL_SPEC_DIR=/Users/razvan/Desktop/Helianthus\ Project/docs ./scripts/check_source_address_table_against_official_specs.py`;
- the docs CI artifact records SHA-256 values for every official spec file it
  reads. If repo-only CI cannot access the workspace-level `docs/` directory,
  M1 must commit a non-self-ratifying excerpt fixture with source file hashes,
  line provenance, and exact excerpt text, then compare the docs table to that
  fixture;
- split official description summaries from canonical enum descriptions:
  `official_description_summary` is compared against the local spec fixture,
  while `canonical_description` is the enum consumed by ebusgo;
- document and test official arbitration rank separately from gateway policy:
  p0 / `0x0` outranks p1 / `0x1`, then p2 / `0x3`, p3 / `0x7`, and p4 / `0xF`;
  lower source bytes win within otherwise equal contention, and p4 must never be
  called higher bus priority;
- document that standard source description and `SourceAddressPriorityIndex` are
  separate;
- document free-use and recommended-for separately from exact standard
  description;
- document `HelianthusGatewayDefaultPolicy` as a Helianthus policy, not a
  standard source description;
- document explicit validate-only mode;
- document `0xFF -> 0x04` and `0xF7 -> 0xFC` companion modulo behavior;
- replace stale docs that exclude `0xFF` as a source due to NACK-byte context;
- document gateway / ebusgo / ebusreg responsibility boundaries;
- update or explicitly supersede all current normative join/admission docs before
  M2 merges: `architecture/startup-admission-and-discovery.md`,
  `architecture/nm-participant-policy.md`, `architecture/decisions.md`,
  `architecture/nm-model.md`, `architecture/nm-discovery.md`,
  `protocols/ebus-services/ebus-overview.md`, and
  `architecture/ebus_standard/10-rpc-source-113.md`;
- add a docs/CI check that current normative NM docs distinguish `0x07/0xFE`
  inquiry from `0x07/0xFF` sign-of-life;
- amend startup admission docs so addressed `0x07/0x04` is the only initial
  pre-discovery source-validation probe, is `read_only_bus_load`, is budgeted,
  and does not permit broadcasts, `0x0F`, NM, mutating services, memory writes,
  full-range probes, or `system_nm_runtime` bypasses;
- replace `JoinResult`/configured fallback as NM local address-pair authority
  with `active_probe_passed` `SourceAddressSelection`;
- define `DEGRADED_SOURCE_SELECTION` as no Helianthus-originated eBUS traffic,
  including scan, semantic polling, MCP/GraphQL bus invoke, NM broadcast,
  `0x07/0xFF`, and companion responder activity.

Acceptance:

- docs contain a normative source-address table with standard source
  description and priority as separate columns;
- docs contain the exact `HelianthusGatewayDefaultPolicy` order;
- docs state that explicit address bypasses candidate search but not
  active validation;
- docs state that ebusreg remains admission-agnostic;
- docs no longer present the old join-era contracts as normative current
  behavior outside explicit historical/migration notes.

## M2 - ebusgo Selection API

Primary repo: `helianthus-ebusgo`

Deliverables:

- replace `JoinBus`, `JoinConfig`, `JoinResult`, and `NewJoiner` with the
  source-selection API in `protocol`;
- implement default, constrained, and explicit validate-only modes;
- implement the docs-owned source-address table as static constants/defines;
- add tests that reference the exact docs anchor/version/hash rather than
  importing a generated JSON/YAML artifact;
- compute companion target with byte modulo arithmetic;
- replace overflow rejection with companion occupancy validation;
- add known-address evidence input for current observation, topology, cache,
  stale-known devices, and companion provenance;
- implement `unknown`, `observed_free`, `observed_occupied`, and
  `stale_known_device` occupancy states;
- remove gateway-startup force selection from the API;
- add typed config/validation/no-available-source/bus-observation errors;
- preserve or migrate existing observation metrics;
- add table tests for ordering, constrained policy, explicit address,
  priority filtering, occupancy state, and companion validation.

Sequencing note:

- this is a breaking API change in `helianthus-ebusgo`;
- gateway migration in M3 updates to the new dependency/API before merge.
- M5 may run any time after M2 as an opportunistic boundary proof.

Acceptance:

- `0xFF` can validate with companion `0x04` when `0x04` is unoccupied;
- `0xFF` is withheld or rejected when `0x04` is occupied, unknown, or
  stale-known device;
- explicit `0x71` ignores persisted `0xF7` in selector behavior;
- default ordering matches exact `HelianthusGatewayDefaultPolicy`;
- constrained policy cannot escape its requested source description;
- priority filter cannot introduce a source description that was not requested;
- free-use recommendation rows are not returned as preallocated
  heating-regulator or combustion-controller description rows;
- source table tests compare `official_description_summary` to the local spec
  fixture and consume `canonical_description` for API enums;
- official arbitration rank tests prove p0 outranks p1, p1 outranks p2, p2
  outranks p3, p3 outranks p4, and lower source byte wins within equal
  contention. These tests are distinct from Helianthus default candidate order.
- explicit address combined with source description or priority is rejected as a config
  error.

## M2a - HA Add-On Wrapper Source-Config Migration

Primary repo: `helianthus-ha-addon`

Deliverables:

- stop add-on wrapper-side raw source reuse from `source_addr_state_file`;
- stop add-on wrapper-side raw source persistence before gateway validation;
- keep leftover `/data/source_addr.last` only as rollback/migration input, never
  as active source authority;
- map `source_addr=auto` to gateway default source-selection policy;
- map exact `source_addr` values by gateway capability: old gateways continue
  to receive legacy `-source-addr` after wrapper-side raw persistence is
  disabled; M3a+ gateways receive explicit validate-only intent; unknown
  gateway capability either fails closed or uses the old-gateway legacy arg path
  without claiming validate-only;
- update add-on README, `config.json`, run script, and tests;
- document rollback with leftover legacy state files.
- forbid new gateway-only CLI/config flags unless version-gated and tested
  against old, new, and unknown gateway capabilities.

Sequencing:

- M2a must merge before M3a binary override or runtime validation. The gateway
  cannot own metadata persistence if the add-on wrapper can still rewrite or
  promote a raw source byte first.

Acceptance:

- add-on restart with `source_addr=auto` and legacy `/data/source_addr.last` does
  not pass that raw byte as active source config;
- add-on exact `source_addr` passes explicit validate-only intent to M3a+
  gateway, and old gateway receives only the legacy `-source-addr` path with no
  wrapper-side raw persistence;
- add-on never rewrites `source_addr_state_file` during startup admission;
- rollback notes preserve old files without letting them override new gateway
  metadata persistence.
- compatibility tests cover new add-on + old gateway, old add-on + new gateway,
  and new add-on + M3a gateway.

## M3 - Gateway Admission Migration

Primary repo: `helianthus-ebusgateway`

Deliverables:

- replace `protocol.NewJoiner(...).Join(...)` call sites with
  `protocol.NewSourceAddressSelector(...).Select(...)`;
- rename the passive observation adapter to source-selection vocabulary;
- update admission artifacts, logs, schemas, expvars, and tests to snake_case
  source-selection vocabulary as additive public fields where old consumers
  still need them until M4;
- stage public surfaces as MCP-first:
  - M3a freezes MCP status and raw admission artifact contracts;
  - M3b adds GraphQL parity from the frozen M3a contract;
  - M6 consumes only M3b GraphQL parity artifacts pinned by commit SHA;
- produce generated GraphQL parity schema artifacts for HA:
  `docs/schemas/source-selection-admission.graphql` and
  `docs/schemas/source-selection-admission.schema.json`;
- produce the complete public API migration matrix before implementation;
- freeze public source-parameter semantics for bus-reaching calls:
  - normal gateway-owned operations use the admitted source after
    `active_probe_passed`;
  - MCP `params.source` and GraphQL `invoke.params.source` are optional
    redundant diagnostic inputs for normal operations, not source authority;
  - missing source uses the admitted source;
  - a value matching the admitted source is accepted only as redundant
    diagnostic input;
  - a nonmatching value is rejected for normal operations;
  - degraded/untrusted admission fails closed;
  - only transport-specific diagnostic MCP requests may use an explicit
    non-admitted user source, and only for one audited, non-persistent request
    that does not change the admitted source;
- migrate every gateway-owned bus-reaching path away from fixed `0x71`,
  fallback `0x31`, or caller-selected normal source authority: MCP invoke,
  GraphQL invoke, Portal explorer, Vaillant B503 dispatcher/bridge, NM runtime
  `FF00`/`FF02` emits, semantic writers, scheduler/time-program writers, poller
  writes, HA write call sites, and gateway-owned GraphQL mutation alias
  families;
- treat current fixed-source code paths as known implementation defects, not as
  accepted runtime behavior. The M3/M2a PRs must convert them into parent-SHA
  RED artifacts and then remove or gate them before merge;
- migrate public GraphQL bus-reaching mutations `setCircuitConfig`,
  `setSystemConfig`, `setZoneConfig`, `setBoilerConfig`,
  `setZoneTimeProgram`, `setDhwTimeProgram`, and snake_case aliases away from
  hidden `mutationSourceAddr=0x31` or any other independent source authority;
  mutations use the admitted source after `active_probe_passed` or fail closed;
- migrate Portal explorer source handling: remove/reject request/query/default
  source overrides, use admitted source after `active_probe_passed`, and fail
  closed before admission or while degraded. Portal is not a transport-specific
  MCP diagnostic override surface;
- preserve adaptermux/proxy external-client source independence: the gateway
  active path uses only admitted source on its own adaptermux session, while
  external ENS/ENH/TCP proxy sessions such as the Python
  `helianthus-vrc-explorer` application and ebusd may use their own source
  address on their own session. External proxy client source choice must not
  update or bypass gateway admitted source authority;
- implement gateway-owned active admission probe FSM:
  `observe -> select -> active probe -> persist/scan on success OR
  quarantine/exclude/reselect on failure`;
- model transport capability as two flags:
  `source_selection_active_capable` and `passive_observe_first_capable`;
- for adapter-direct ENH/ENS, prove that active-capable does not imply
  passive-observe-first-capable. Without configured or current bounded probe
  targets, gateway must degrade with zero eBUS traffic rather than inventing a
  target from transport capability alone;
- implement bounded `AdmissionProbeTarget` selection and degrade with no scan
  when no bounded target exists;
- validate every `AdmissionProbeTarget`: reject broadcast `0xFE`, SYN `0xAA`,
  ESC `0xA9`, initiator-pattern destinations, selected source, selected
  companion, and any target without configured/current positive target
  provenance;
- define pre-probe eligibility for `passive_observe_first_capable=false`:
  known occupied or stale-known source/companion rejects the candidate without
  probing; unknown source/companion may be tentatively probed only with
  operator-exclusive reservation or configured/current bounded target; otherwise
  gateway degrades with zero eBUS traffic;
- retry at most eight candidates per boot, one read-only directed active probe
  per candidate;
- enter `DEGRADED_SOURCE_SELECTION` with no Helianthus-originated eBUS traffic
  if all candidates fail or no bounded target exists;
- commit source persistence only after active probe success, with metadata key
  scoped by instance, transport, adapter/proxy identity, policy fingerprint,
  companion, schema version, and validation type;
- ignore legacy raw `source_addr.last` and any metadata-mismatched persisted
  source until a current active-probe success writes a new metadata record;
- ensure operator explicit source configuration maps to explicit
  validate-only mode.
- ensure gateway startup cannot select non-default standard descriptions merely
  because a priority was requested.
- require adapter-direct ENS live evidence, explicit `0x71` active-probe
  success, cold boot/power-cycle evidence, and before/after transport matrix
  evidence before the M3 gateway PR can merge.
- capture the full T01..T88 baseline at the parent SHA before M3 code edits,
  then rerun the matrix at PR head with per-case expected eBUSd state from the
  matrix; do not require eBUSd-stopped proof for cases whose definition includes
  ebusd/proxy.
- capture a separate no-eBUSd adapter-direct admission submatrix with eBUSd and
  reconnectable proxy listeners disabled or mechanically guarded for the full
  evidence window.
- implement a SAS-specific transport evidence validator in gateway CI before
  M3a can merge. It verifies parent/PR SHA metadata, clean-tree baseline
  artifacts, per-case eBUSd/proxy state, capability flags, the no-eBUSd
  submatrix, and locked expected-failure inventory.
- lock the parent-SHA expected-failure inventory and hash before PR-head matrix
  validation; PR-head validation rejects any unlisted xfail and all xpass unless
  an operator override artifact names the case and reason.
- include `PX01..PX12` adjunct evidence for any proxy/coexistence run, or mark
  the proxy listener checks as observational only with no proxy-semantics claim.
  PX evidence is wire-semantics evidence only and must not be used as proof of
  gateway admitted-source immutability.
- add `SAS-SRC-01..02` source-authority coexistence cases and make the SAS
  evidence validator fail coexistence claims unless the applicable cases pass:
  `SAS-SRC-01` for a generic external ENS/ENH/TCP proxy session with
  non-admitted source, and `SAS-SRC-02` for the Python
  `helianthus-vrc-explorer` application when compatibility is claimed. Each
  case captures before/after gateway source-selection snapshot, adaptermux
  session/source snapshot, and independent bus-boundary transcript.
- implement the SAS evidence validator as a required gateway-side gate
  (`go run ./cmd/sas-evidence-validator --manifest artifacts/sas/m3/manifest.json`
  or wrapper equivalent). Existing `scripts/transport_gate.sh` and adapter-proxy
  PX validation are insufficient by themselves and cannot authorize coexistence
  source-authority claims.
- use temporary addon binary override for pre-merge lab validation; this is not
  production rollout.
- include an M3 evidence runbook before merge, not only in M7. The runbook lists
  exact commands and artifact paths for eBUSd stopped proof, proxy listener
  absence/guard, adaptermux external-session count zero, binary override deploy,
  admission artifact capture, GraphQL snapshots, explicit `0x71` validation,
  and rollback.
- implement minimal operator recovery surfaces before any M3 binary override:
  status, clear-persistence, clear-quarantine, re-admit, explicit-source
  validate, and rollback.
- test that rollback with leftover new source-selection persistence does not
  brick old gateway/new HA or new gateway/old HA pairings.
- block production live deployment and public legacy/camelCase removal until
  M6 HA migration tests are green against the M3b GraphQL parity schema artifact.

Gateway remains responsible for:

- startup admission state;
- transport admission dispatch;
- operator override semantics;
- source exclusion after active-probe failure;
- retry limits, quarantine, persistence, and degraded state;
- GraphQL/MCP observability surfaces.

Acceptance:

- adapter-direct ENS default startup no longer marks `0xF7` active and then
  continues scanning after active-probe timeout;
- direct ENH/ENS startup with no passive occupancy snapshot and no configured or
  current bounded probe target enters `DEGRADED_SOURCE_SELECTION` without eBUS
  traffic;
- direct ENH/ENS startup with a configured/current bounded probe target may run
  only the first-implementation directed `0x07/0x04` probe;
- active-probe target validation rejects broadcast, SYN, ESC, initiator-pattern
  destinations, selected source, selected companion, and targets without
  configured/current positive target provenance;
- explicit `0x71` validates and is used when available;
- explicit `0x71` active-probe success scans with source `0x71`, records
  companion `0x76`, emits `explicit_validate_only`, and does not persist the
  explicit source by default;
- persisted last-known source cannot override explicit configuration;
- artifact path names use `source_selection`, not legacy join strings.
- raw admission artifact includes selected source, companion, rejected
  candidates, quarantined sources, active probe transcript, persistence
  decision, and final state.
- default `0xF7` timeout has two proofs: next candidate success uses the new
  source for scan, and all candidates failing enters degraded state with no
  Helianthus-originated eBUS traffic.
- failed `0xF7`, withheld `0xFF`, and degraded admission cannot emit NM `FF 00`,
  NM `FF 02`, `07 FF`, MCP/GraphQL bus invoke, or companion responses.
- full transport matrix and no-eBUSd admission submatrix have no unexpected
  failures before merge.

## M4 - Public API And Legacy Terminology Removal

Primary repos: `helianthus-ebusgo`, `helianthus-ebusgateway`,
`helianthus-docs-ebus`, `helianthus-ha-integration`

Deliverables:

- remove public camelCase/legacy admission/status names only after M6 HA tests
  are green against the new source-selection schema;
- reject old fields/enums only in M4 schema tests, not in M3;
- rename or explicitly account for every current gateway expvar key:
  `startup_admission_degraded_total`, `startup_admission_state`,
  `startup_admission_override_active`,
  `startup_admission_warmup_events_seen`,
  `startup_admission_warmup_cycles_total`,
  `startup_admission_override_bypass_total`,
  `startup_admission_override_conflict_detected`,
  `startup_admission_degraded_escalated`,
  `startup_admission_degraded_since_ms`,
  `startup_admission_consecutive_rejoin_failures`, and
  `startup_admission_degraded_cumulative_ms`;
- verify old aliases and public camelCase/legacy names are removed after
  gateway and downstream consumers are migrated;
- rename files and tests where useful;
- update schema docs and log assertions;
- add an executable terminology gate with regex, allowlist, red/green test, and
  historical execution-plan exclusion.
- require local CI evidence for each touched repo at PR head.

Acceptance:

- active code and current docs contain no legacy source-selection API names;
- exceptions are limited to historical execution-plan references and migration
  notes;
- no public API exposes both old camelCase/legacy names and new snake_case
  names after M4; snake_case is the only public surface for this admission
  model.
- gateway expvar snapshot tests show all old `startup_admission_*` admission
  keys are absent and all corresponding `startup_source_selection_*` keys are
  present, unless a retained key has a row-specific rationale in this plan and a
  green retention test.
- GraphQL snake_case-only applies to admission/status fields; unrelated
  GraphQL camelCase fields are out of scope for this plan.

## M5 - ebusreg No-Op Boundary Proof

Primary repo: `helianthus-ebusreg`

Deliverables:

- confirm `Scan` and `ScanDirected` remain source-byte consumers only;
- add a boundary test only if it can protect against future admission leakage
  without introducing selection concepts into ebusreg.

Acceptance:

- ebusreg imports no source-selection API;
- ebusreg behavior is unchanged for scan target filtering and pacing.

## M6 - HA Diagnostics And Empty-Payload Guard

Primary repo: `helianthus-ha-integration`

Deliverables:

- develop against M3b GraphQL parity schema artifacts and a gateway test fixture
  pinned by commit SHA; M6 does not require M3 production rollout;
- add HA repair issue or diagnostic entity when gateway admission is degraded;
- suppress stale cleanup when gateway reports degraded admission or
  healthy-looking empty inventory;
- migrate HA integration to snake_case admission/status fields with no
  camelCase compatibility dependency;
- query the exact `bus_admission.source_selection` schema and create repair
  codes `schema_incompatible`, `admission_degraded`, and
  `empty_inventory_untrusted`;
- run admission preflight before stale cleanup, persist `admission_trusted`, and
  clear repairs only after source-selection status is healthy;
- add tests for `devices=[]`, `zones=[]`, `dhw=null`, and degraded admission.

Acceptance:

- HA does not silently present a successful integration with no useful
  entities after source admission failure;
- existing entities are not removed solely because gateway inventory is empty
  during degraded startup.
- HA marks entities unavailable during degraded admission and resumes cleanup
  only after two consecutive healthy non-empty coordinator refreshes or
  explicit operator acknowledgement.
- all HA write paths remove fixed `0x31` fallbacks: climate, water heater, zone
  schedule helper, and DHW schedule helper.

## M7 - Live Rollout And Coexistence Evidence

Primary repo: `helianthus-execution-plans`

Deliverables:

- run local CI for all touched repos;
- record the live HA rollout and rollback runbook evidence artifact;
- reference the M3 evidence bundle by commit SHA; do not require the live bus to
  naturally reproduce pre-fix `0xF7` failure after merge unless a controlled
  reset or fixture path is documented;
- snapshot gateway config, source-selection persistence, HA entity state, and
  eBUSd state before deployment;
- deploy with the approved addon binary override or release path, verify
  GraphQL/HA, then document rollback of binary/config/persistence and HA entity
  state;
- include exact deploy/rollback commands, backup paths, persistence
  restore/clear steps, HA repair/entity-state cleanup, and version-pair rollback
  matrix;
- keep eBUSd stopped for baseline evidence and prove stopped state before and
  after the run;
- prove proxy listener disabled/guarded state before/during/after baseline:
  addon config, listening sockets, `127.0.0.1:8888` absence where applicable,
  adapter upstream single-owner state, and adaptermux external-session count
  zero;
- run gateway plus eBUSd/proxy client reconnect only as an operator-approved
  coexistence sub-run with written approval, max ten-minute runtime, exact
  topology, external clients started before re-admission or forced re-admission
  after they connect, external source+companion marked occupied, selected
  gateway source+companion proven disjoint, allowed read-only traffic, abort on
  same source/companion even without collision, collision abort threshold of one,
  pre/post state, and restore-to-stopped proof.
- when the coexistence sub-run claims Python `helianthus-vrc-explorer`
  compatibility, run that application as an external proxy client with an
  explicit per-session source. Capture the command line, client transcript,
  bus-boundary capture, adaptermux session/source snapshot, gateway
  `bus_admission.source_selection` snapshot before and after, and proof that
  the client source did not update admitted source. Record these artifacts in
  `artifacts/sas/m3/RUNBOOK.md` and `artifacts/sas/m3/manifest.json`.

Acceptance:

- GraphQL bus admission surface reports source-selection outcome clearly;
- evidence bundle includes commit SHA, config, eBUSd state, raw admission
  artifact, selected source, rejected candidates, active probe target/opcode,
  timeout/success logs, GraphQL snapshots, and HA state;
- live evidence covers `0xF7` quarantine/retry/degraded path;
- live evidence covers explicit `0x71` validate-only success.
- operator recovery commands/surfaces exist for status, clear-persistence,
  clear-quarantine, re-admit, explicit-source validate, and rollback.

## Merge Order

1. `helianthus-execution-plans`
2. `helianthus-docs-ebus`
3. `helianthus-ebusgo`
4. `helianthus-ha-addon` wrapper source-config migration
5. `helianthus-ebusgateway` M3a MCP/artifact admission migration
6. `helianthus-ebusgateway` M3b GraphQL parity
7. `helianthus-ha-integration` M6 diagnostics and empty-payload guard
8. `helianthus-ebusgateway` / docs / HA / ebusgo coordinated M4 public API and
   terminology removal, only after HA is green against the M3b schema
9. `helianthus-ebusreg` boundary proof, if a PR is needed; this may run any time
   after M2 and is not blocked by M4
10. `helianthus-execution-plans` M7 live rollout/coexistence evidence artifact

The docs PR may run in parallel with ebusgo development, but docs must be
merged before ebusgo API merges because the source-address table is normative.
M3a waits for M2 and M2a. The HA PR may develop in parallel with M3 using the
M3b PR-head GraphQL parity schema artifact, but it may merge only after M3b has
merged. Public schema removal and production rollout wait for HA tests.
