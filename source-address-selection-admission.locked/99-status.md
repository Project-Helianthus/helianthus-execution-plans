# Status

State: `locked`

Current milestone: `M7_LIVE_ROLLOUT_AND_COEXISTENCE_EVIDENCE`

This plan was created on `2026-05-03` after live-bus investigation showed
that source `0xF7` could be selected but fail active probing, while explicit
source `0x71` worked. The same discussion identified `0xFF` rejection via
`companion-target-overflows-byte` as a protocol bug: companion target derivation
must wrap to `0x04`.

## Planner Input

Primary planning pass: `Codex gpt-5.5 high`

The planner recommended:

- `SourceAddressSelector` / `SourceAddressSelection` terminology;
- separate standard source description from p0..p4 `SourceAddressPriorityIndex`;
- default `HelianthusGatewayDefaultPolicy` p4, then p3, then p1, then p0;
- explicit address as validate-only;
- docs own the source-address table; ebusgo implements static constants/defines
  and tests reference the docs directly;
- gateway owns startup admission, active-probe FSM, quarantine, and persistence;
- ebusreg remains admission-agnostic.

## Open Review Items

- Confirm operator acceptance of the additive M3 -> HA M6 -> removal M4
  sequencing before promotion to `.locked`.
- During M3 implementation, append any newly discovered public field to the
  migration matrix without removing the locked rows.

## Accepted Corrections

- `SourceAddressStandardDescription` is independent from p0..p4
  `SourceAddressPriorityIndex`; free-use and recommended-for are separate
  fields.
- Priority-only gateway startup selection filters
  `HelianthusGatewayDefaultPolicy`; it does not search all standard
  descriptions at that priority.
- `ExplicitAddress + StandardDescription/Priority` is a configuration error in
  the first implementation.
- No JSON/YAML generated source-address artifact is used; this is static
  protocol data implemented once in code and referenced to docs.
- The public API migration is intentionally breaking: old camelCase/legacy
  admission names are removed and snake_case remains.
- The five adversarial reviews all returned `BLOCK`; accepted fixes include
  docs-owned source table, active-probe FSM, persistence only after active
  success, occupancy unknown/stale model, HA degraded handling, and public
  snake_case migration.
- A second adversarial round also returned `BLOCK`; accepted fixes include
  passive-only selector semantics, known-address evidence input, bounded
  `AdmissionProbeTarget`, metadata mismatch handling for `source_addr.last`,
  gateway-safe standard-description allowlist, HA-before-public-removal
  sequencing, M3 transport/cold-boot gates, explicit `0x71` success evidence,
  eBUSd stopped-state protection, rollout/rollback runbook evidence, and an
  enumerable public API migration matrix.
- A third adversarial round returned `BLOCK`; accepted fixes include four-mode
  naming, exact docs hash procedure, additive M3 schema, HA tests against M3
  PR-head artifacts, M4-only old-field rejection, RED-before-implementation
  matrix, transport baseline timing, explicit `0x71` success tests, exact
  gateway-safe description constants, previous-source order semantics, positive
  `observed_free` provenance, and executable rollback/recovery requirements.
- A fourth adversarial round returned `BLOCK`; accepted fixes include local
  official-spec citations and table hash, M1 superseding all current join-era
  docs, `priority_index`/`arbitration_nibble` terminology, `07 04` active-probe
  allowlist, degraded zero-eBUS-traffic semantics including NM and invoke paths,
  M3a MCP/artifact before M3b GraphQL parity, `rpc.invoke` source authority
  migration, expanded public CLI/add-on/GraphQL/expvar inventory, split
  T01..T88 vs no-eBUSd admission evidence, proxy-listener guard proof, M3
  recovery surfaces before binary override, and stricter coexistence ordering.
- A fifth adversarial round returned `BLOCK`; accepted fixes include preserving
  official blank `0x07` recommended-for semantics, citing the official
  arbitration priority-class section, making `helianthus-ha-addon` a real M2a
  target before gateway runtime validation, splitting M3a/M3b/M6/M4
  dependencies topologically, specifying bus-reaching `params.source`
  authority for MCP/GraphQL/HA, separating current GraphQL camelCase fields from
  the new snake_case source-selection surface, adding a complete expvar rename
  inventory, requiring actual parent-SHA RED artifacts, and distinguishing
  `source_selection_active_capable` from `passive_observe_first_capable`.
- A sixth adversarial round returned `BLOCK`; accepted fixes include
  tests-only RED artifacts with selected-test-count and failure-string proof,
  clean-tree parent/baseline artifacts, explicit official-spec root or
  non-self-ratifying fixture for docs CI, locked transport expected-failure
  inventory, M3 evidence runbook before merge, active-probe target validation,
  no-passive pre-probe eligibility, PX01..PX12 adjunct evidence for
  proxy/coexistence runs, `official_description_summary` terminology, official
  arbitration rank tests, NM `07 FE` vs `07 FF` reconciliation, corrected
  GraphQL admission inventory, `daemon_status.initiator_address` source-status
  coverage, removal of hidden/fallback `0x31` write authority, M6 merge only
  after M3b merge, SAS-specific transport evidence validator, and M2a
  add-on/gateway compatibility tests.
- A seventh adversarial round returned `BLOCK`; accepted fixes include removing
  documented lab topology as an automatic active-probe target source, anchoring
  PX01..PX12 evidence to the adapter-proxy case set and report schema, adding
  mutation-canary docs RED proof, strengthening RED commit/test selection
  mechanics, defining the transport expected-failure JSON schema/hash and SAS
  validator command, requiring an independent bus-boundary transcript, adding a
  committed M3 runbook template, adding machine-readable `topology_nodes` with
  doc/transport gates, changing M4 dependencies to wait for HA merge, adding an
  M4 add-on cleanup lane, making M7 wait for M5 satisfied, fixing GraphQL root
  path to `busSummary`, covering snake_case mutation aliases, and specifying
  old/new/unknown gateway behavior for add-on exact `source_addr`.
- An eighth adversarial round returned `BLOCK` only on runtime/evidence
  precision after spec/API/lockability review passed; accepted fixes include
  promoting the independent bus-boundary transcript into canonical M3 blockers,
  replacing the docs checker direct-script RED row with a pytest mutation
  canary and JSON report, and closing the expected-failure inventory schema with
  exact top-level shape, ordered `T01`..`T88` cases, allowed values, no extra
  keys, and canonical JSON hashing.
- A ninth focused evidence review returned `BLOCK`; accepted fixes include
  copying the detailed evidence/test-gate contract into canonical source of
  truth and requiring non-empty `expected_failure_reason` if and only if a
  transport case is `xfail`.
- A final API/source-authority concern found that bus-reaching GraphQL mutation
  aliases beyond config writes could still bypass admitted source authority.
  Accepted fixes make the admitted source the only normal gateway-owned source
  authority for MCP, GraphQL, semantic writer, scheduler, poller, and HA-driven
  paths; the only non-admitted source override is a user-explicit,
  transport-specific MCP diagnostic request that is audited, single-request,
  non-persistent, and outside normal operation.
- A focused gateway/reg source-authority review returned `BLOCK`; accepted
  fixes add explicit M3 coverage for Vaillant B503 dispatcher/bridge, NM
  runtime `FF00`/`FF02` emits, and Portal explorer. Portal explorer is treated
  as normal gateway-owned operation, not an override surface; only
  transport-specific MCP diagnostics may carry a one-request explicit source.
- Operator clarification distinguished the Python `helianthus-vrc-explorer`
  application from Portal explorer. Portal explorer remains admitted-source-only
  on the gateway active path. External adaptermux/proxy clients such as the
  Python `helianthus-vrc-explorer` application and ebusd may use their own
  per-session source over ENS/ENH/TCP proxy surfaces, and that source choice
  must not update or bypass gateway admitted source authority.
- A full re-review evidence pass returned `BLOCK`; accepted fixes add
  parent-SHA RED rows for the transport-specific MCP one-request source
  override and B503 GraphQL bridge, plus mandatory coexistence evidence that
  runs the Python `helianthus-vrc-explorer` application as an external proxy
  client and proves its per-session source does not mutate gateway admitted
  source.
- Runtime/transport R2 found that PX01..PX12 was overclaimed as
  source-authority proof. Accepted fixes demote PX to adjunct wire-semantics
  evidence only and add mandatory `SAS-SRC-01..02` coexistence source-isolation
  cases enforced by the SAS evidence validator.
- Runtime/transport R4 noted current hard-coded source paths in gateway/add-on
  code. Accepted clarifications classify those as known implementation defects
  that are valid only as parent-SHA RED evidence before M3/M2a and merge
  blockers afterward, and require a gateway-side SAS evidence validator that
  gates `SAS-SRC` artifacts separately from generic transport/PX gates.

## Blockers

No planning blockers remain.

M7 still requires post-merge rollout/rollback evidence on the live HA runtime.

## Execution Progress

Updated: `2026-05-06`

Completed and merged:

- M0 / SAS-00: plan locked in `helianthus-execution-plans`.
- M1 / SAS-01: source-address docs and protocol table merged in
  `helianthus-docs-ebus`.
- M2 / SAS-02: source-address selection API and `0xFF -> 0x04` companion fix
  merged in `helianthus-ebusgo`.
- M2a / SAS-02A: add-on wrapper source-config migration merged in
  `helianthus-ha-addon`.
- M3a/M3b / SAS-03A/SAS-03B: gateway active-probed source-selection admission,
  MCP/artifact contract, and GraphQL parity merged in `helianthus-ebusgateway`.
- M6 / SAS-04: HA integration degraded/empty-payload guard and new admission
  schema consumption merged in `helianthus-ha-integration`.
- M4 / SAS-05: gateway public API cleanup merged as
  `3efe87abfc1a8a850139c3b268ea71df8a5e5c3a`.
- M4 / SAS-06: ebusgo public selector cleanup gate merged as
  `51c57f4325aee38e09175a5a457cc58462a4bf7e`.
- M4 / SAS-07: docs public migration cleanup merged as
  `457378b15d6eedf5412b3f968841f012a55f924c`.
- M4 / SAS-08: HA legacy admission dependency proof merged as
  `b90f9b16e7f257d24b16a49ef001221743f27424`.
- M4 / SAS-08A: add-on source config cleanup proof merged as
  `1c4988103ff402adffd11643733bb3a73a6d7007`.
- M5 / SAS-09: ebusreg no-op boundary proof captured in
  `92-ebusreg-noop-boundary-proof.md`; no ebusreg PR was opened and abandoned
  PR129 was not reused.

Review/CI state at M4 closure:

- All M4 PR review threads were addressed and resolved.
- Gateway, docs, add-on, ebusgo, and HA GitHub checks were green at merge.
- Fresh Codex review comments on gateway, docs, and add-on reported no major
  issues after the final fixes.

Next:

- M7 / SAS-10: capture live rollout/rollback evidence and coexistence/proxy
  guard state against the merged `main` heads.
