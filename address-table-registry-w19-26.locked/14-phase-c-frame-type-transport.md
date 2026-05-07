# Phase C — Frame-Type-Aware Transport (Amendment)

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

Depends on: `00-canonical.md` decision matrix AD01..AD23 (current lock), Phase
A milestones M0..M5 merged, Phase A.5 runtime wire-up + A.6 src insertion + A.7
canonical-table API + A.8 forensic logging + A.9 abandon counters + M6/M6.1
identity-merge merged. Predecessor PRs `helianthus-ebusgateway#560` + `#562` +
`#564` + `#565` + `#566` + `#567` + `#568` + `#569` + `#570` + `#571` + `#572`
+ `#573` + `#574`, `helianthus-ebusgo#148` + `#149`, `helianthus-ebusreg#131`
+ `#132` + `#133`. Live-validation evidence collected in
`helianthus-docs-ebus/architecture/atr/07-live-validation-acceptance.md`. New
docs anchor: `helianthus-docs-ebus/architecture/ebus_standard/12-address-table.md`
(rename + 256-byte taxonomy + frame-type contract + validator contract).

Scope: amend the locked plan with Phase C, which introduces a frame-type-aware
transport contract across `helianthus-ebusgo`, `helianthus-ebus-adapter-proxy`,
and `helianthus-ebusgateway`. Phase C closes two operator-confirmed regressions
that surfaced after live deployment of Phase A + A.5..A.9 + M6/M6.1:

- (a) `entry.Address()` returned the initiator (e.g. `0x03`) instead of the
  target slave (e.g. `0x08`) when the registry aliased a master/slave pair.
  Semantic writes that picked `entry.Address()` then addressed the wrong byte
  on the wire.
- (b) The transport `Send(src, dst, bytes...)` API had no notion of frame
  type. Any caller could emit M2S, M2M, or M2BC bytes regardless of whether
  `dst`'s address class was consistent with the chosen application-layer
  service.

Operator-chosen fix: **additive**. `protocol.Frame` gains an optional
`FrameType` field and a `Frame.Validate() error` method; `Bus.Send` calls
`Frame.Validate()` at the top of its body. The `RawTransport.Send`
interface signature is unchanged — no cross-repo breaking-change cascade.
Callsites that know their frame type set `Frame.FrameType`; sites that
do not rely on the existing `FrameTypeForTarget(dst)` fallback in
`helianthus-ebusgo/protocol/protocol.go`.

Idempotence contract: each amendment decision (AD24..AD30 below) is the
authoritative resolution; re-issuing a milestone prompt MUST yield the same
scope. Phase C amends the locked plan; it does not re-canonicalize. The
`00-canonical.md` SHA stays at
`eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`. Future
changes to this chunk REQUIRE a canonical-hash bump; Phase C amendments after
this chunk go in `15-...md`, not by editing this file.

Falsifiability gate: M-C8_LIVE_VALIDATION is the integration falsifier. After
Phase C deploy, the gateway MUST emit `ErrInvalidFrameAddress` whenever a
caller passes a frame-type-incompatible (`src`, `dst`) pair, AND the BAI ecoTEC
M2S writes MUST address the target slave `0x08` (not the aliased initiator
`0x03`) on the wire. Pre-Phase-C reproduction traces (operator pcap) MUST
become impossible by construction post-Phase-C. Per-milestone falsifiability
is enumerated below.

Coverage: this chunk covers Phase C only. Phase A milestones live in
`11-milestones-phase-a.md`. Phase B (deferred) lives in
`12-milestones-phase-b.md`. Phase A live-validation acceptance lives in
`13-acceptance-criteria-and-falsifiability.md`. The doc-side normative anchor
for the address taxonomy and frame-type contract lives at
`helianthus-docs-ebus/architecture/ebus_standard/12-address-table.md`. The
Phase C rollback runbook lives at
`helianthus-execution-plans/runbooks/phase-c-rollback.md`.

## Decision matrix (Phase C extension)

- **AD24** — Frame-type validation lives on `Frame`, not on the transport
  interface. `protocol.Frame` gains optional `FrameType FrameType` (zero
  value falls back to `FrameTypeForTarget(Frame.Target)`).
  `Frame.Validate() error` runs the validator contract from
  `12-address-table.md`. `Bus.Send` MUST call `frame.Validate()` first;
  return the error before any byte writes. `RawTransport.Send(ctx, src,
  dst byte, payload ...) error` is **unchanged**. Adapter-proxy, ebusreg,
  and ebusgateway only update callsites to populate `Frame.FrameType`
  (or leave zero). **Additive, non-breaking** cross-repo change.

- **AD25** — 4-class address taxonomy. The lower-layer `protocol.AddressClass`
  enum has exactly four values: `Master`, `Slave`, `Broadcast`, `Reserved`.
  Tier (p0..p4), free-use, and device role recommendations remain in the v1
  source-address table; they do NOT appear in `AddressClass`. Pinned mapping
  rules per byte (per `12-address-table.md` 256-byte taxonomy section, with
  spec line cites): `0xAA`/`0xA9` Reserved (`Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md`
  lines 224-225, `Spec_Prot_12_V1_3_1_E.en.md` §5.1 lines 250-252); `0xFE`
  Broadcast (Anhang line 305); 25 spec masters Master (Anhang lines 34-58);
  everything else Slave (228 bytes, by elimination). The "228 vs 203"
  question is resolved in `12-address-table.md` § "Reconciliation with
  Anhang slave enumeration": 203 = Anhang's enumerated `Slave NNN` rows,
  228 = the protocol-class total (203 enumerated + 25 reserved-companion
  slots). The validator uses 228. `AddressClassReserved` MUST be the zero
  value of the enum so uninitialized fields fail closed.

- **AD26** — Validator semantics. `Frame.Validate() error` returns
  `ErrInvalidFrameAddress` iff (with `ft` resolved as `Frame.FrameType`
  if non-zero else `FrameTypeForTarget(Frame.Target)`): `ft ==
  FrameTypeUnknown` after fallback OR `Source == Target` OR per-frame-type
  class mismatch (M2S: src not Master or dst not Slave; M2M: both must
  be Master; M2BC: src must be Master and `dst == 0xFE`) OR caller-vs-
  central mismatch (`Frame.FrameType` non-zero AND
  `Frame.FrameType != FrameTypeForTarget(Frame.Target)`). Otherwise nil.
  Pure: no state, no logging, no metrics. `Bus.Send` emits audit logs.

- **AD27** — `FrameType` enum unification. `protocol.FrameType` is the
  single source of truth across emitter, parser-side reconstructor, and
  validator. Renames: `FrameTypeInitiatorTarget`→`FrameTypeM2S`,
  `FrameTypeInitiatorInitiator`→`FrameTypeM2M`,
  `FrameTypeBroadcast`→`FrameTypeM2BC`; `FrameTypeUnknown` stays zero.
  Renames land in ebusgo first with `// Deprecated:` aliases for one
  release cycle. Because AD24 dropped the `RawTransport.Send` signature
  change, each repo can take the rename PR independently — no atomic
  three-repo coordination required.

- **AD28** — Per-API-site explicit frame-type declaration reconciled with
  `FrameTypeForTarget`. Each semantic API site (B524, B509, B503,
  B5xx-Vaillant, 0704, B516, NM 0xFF, etc.) declares its frame type per
  its application-layer spec when constructing the `Frame`. The validator
  (AD26 clause 6) cross-checks the declared `Frame.FrameType` against
  `FrameTypeForTarget(Frame.Target)` and rejects on mismatch. No central
  inference table at the call layer; `FrameTypeForTarget` is consulted
  only as consistency check and zero-value fallback. Mapping is **per
  spec line, per NM-service**, NOT per command-code prefix — the
  runtime-target-branching service `03h 10h` (Spec_Prot_7 §3.1.6,
  lines 497, 518, 525) is the canonical reason: the spec table itself
  splits the response by `target == master` vs `target == slave`.

- **AD29** — Defense in depth, not bus-rejection. Per `12-address-table.md`
  operator-declared exception, the eBUS wire does NOT enforce sender class
  by frame type. Phase C enforcement is gateway-side discipline, refusing
  ill-typed frames at the `Bus.Send` boundary BEFORE arbitration. Failures
  are logged and counted, not silently swallowed. The transport gate (M-C8 +
  M-C9) verifies that no Phase C change alters the wire byte stream of
  well-typed callers (zero byte deltas).

- **AD30** — `entry.Address()` REMOVAL at M-C6. The ambiguity that
  triggered Phase C is closed by AD24 + M-C6's
  `entry.AddressByRole(role registry.SlotRole)`, which returns the
  matching `BusFace` address (e.g. `SlotRoleSlave` returns `0x08`
  for the BAI alias). Preferred over `AddressForFrameType(ft)`
  because it leverages existing `BusFace.Role` machinery
  (`address_slot.go` lines 5-11, 41-47), keeps the registry
  protocol-agnostic, and maps caller intent ("I want the slave-side
  byte") cleanly to `SlotRole`. M2S writers ask `SlotRoleSlave`;
  M2M asks `SlotRoleMaster`. **`entry.Address()` is REMOVED at
  M-C6 merge** — operator-pinned, no deprecation window. M-C6
  enumerates all callers via `git grep`, migrates each in the same
  PR; CI build break = caller missed.

## Phase C milestone list

```text
M-C0_DOC_SPEC →
M-C0A_TRANSPORT_BASELINE →
M-C0B_TDD_GATE (4 repos staged) →
M-C1_ADDRESS_CLASS →
M-C2_FRAMETYPE_UNIFY →
M-C3_FRAME_VALIDATE →
M-C4_VALIDATOR →
M-C5_BUS_SEND_ENFORCE →
M-C6_REGISTRY_HELPERS →
M-C7_SEMANTIC_API_ENRICH →
M-C8_LIVE_VALIDATION →
M-C9_TRANSPORT_VERIFY →
M-C10_DOC_EVIDENCE
```

## M-C0_DOC_SPEC — Doc-gate canonical specification

- Repo: `helianthus-docs-ebus`
- Complexity: 4
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: REQUIRED (this IS the Phase C doc-gate milestone)
- Scope:
  - Rename `architecture/ebus_standard/12-source-address-table.md` →
    `12-address-table.md` (preserve v1 table block byte-for-byte; v1 hash
    `e78954...` unchanged).
  - Add 256-byte address taxonomy section with `AddressClass` 4-class enum,
    classification algorithm, pinned cases (with `Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md`
    line cites), and the "Reconciliation with Anhang slave enumeration"
    sub-section that resolves 228 vs 203.
  - Add frame-type addressing contract section with:
    - M2S/M2M/M2BC table with Spec_Prot_12 §4 line cites.
    - `Frame.FrameType` field semantics + `FrameTypeForTarget` fallback.
    - Self-addressing rule and sender constraint scope.
    - Per-application-layer-service frame-type table (covering 03h 04h..
      03h 08h, 03h 10h, 08h 00h..04h, FEh 01h, FFh 00h..06h with line
      cites).
    - Service 03h 10h runtime-target branching call-out.
  - Add validator contract section with `Frame.Validate() error` signature,
    rejection clauses (1–6 including the caller-vs-central mismatch
    clause), and test surface.
  - Add taxonomy-and-contract hash contract section with the operator-
    runnable `awk | sed | shasum` snippet.
  - Ship companion script `helianthus-docs-ebus/scripts/check_address_table_taxonomy_hash.sh`
    that mirrors the shape of the existing
    `scripts/check_source_address_table_against_official_specs.py`. The
    script extracts the three sections (256-Byte Address Taxonomy →
    Validator Contract) and recomputes the hash; CI runs it and fails on
    drift.
  - Update `architecture/ebus_standard/README.md` index pointer.
  - Cross-link `architecture/atr/03-ack-nack-insertion-rules.md` for `0xFF`
    dual-meaning context.
- Acceptance: doc-gate companion check passes; v1 hash unchanged; new
  taxonomy-and-contract hash recorded once review board freezes the text;
  `check_address_table_taxonomy_hash.sh` runs green; review-bot APPROVE on
  docs-ebus PR; cross-link from this chunk resolves.

## M-C0A_TRANSPORT_BASELINE — Transport matrix pre-change baseline

- Repo: `helianthus-ebusgateway`
- Complexity: 3
- Routing: Codex
- Transport-gate: required-baseline
- Doc-gate: not-required
- Scope: capture T01..T88 transport matrix snapshot pre-Phase-C; record as
  `transport-matrix-phase-c-baseline-w19-26.json` in PR. Include byte-stream
  fingerprints for every defined M2S/M2M/M2BC representative frame so M-C9
  can verify zero wire-level deltas for well-typed callers. Include a
  concrete BAI 0x03↔0x08 regression fixture under
  `testdata/regression_aliased_write_to_initiator/` (golden bytes captured
  pre-Phase-C demonstrating the wrong-target write, plus a `.expected.txt`
  describing the post-Phase-C callsite behavior: same payload but `Target`
  byte flipped from `0x03` to `0x08`).
- Acceptance: matrix output checksum recorded; baseline artifact merged into
  the gateway repo at `matrix/phase-c-baseline-w19-26.json`; regression
  fixture committed; ready for M-C9 diff.

## M-C0B_TDD_GATE — Per-repo RED test commits

- Repos: `helianthus-ebusgo`, `helianthus-ebus-adapter-proxy`,
  `helianthus-ebusreg`, `helianthus-ebusgateway` — staged per AD15-style
  ordering: ebusgo first (foundation), then adapter-proxy + ebusreg (each
  independently consume), then gateway (consumer).
- Complexity: 3 per repo
- Routing: Codex per-repo
- Per-repo RED scope:
  - **ebusgo**: `TestAddressClass_{AllBytes,PinnedCases}`,
    `TestFrameType_RenameMapping`, `TestFrame_Validate_{PinnedCases,
    ZeroFrameType_FallsBackToFrameTypeForTarget,
    DeclaredVsCentral_Mismatch_Rejects}` (clause 6 from AD26).
    Pinned bytes: `0x00, 0xFF, 0x04, 0x05, 0x08, 0x15, 0x26, 0xEC,
    0xF6, 0xA9, 0xAA, 0xFE`.
  - **adapter-proxy**: `TestProxyForwardsFrameWith{Explicit,Zero}FrameType`
    (propagate `Frame.FrameType` byte-for-byte; proxy MUST NOT validate —
    only Bus.Send does).
  - **ebusreg**: `TestDeviceEntry_AddressByRole_{SlotRoleSlave_Returns_Slave,
    SlotRoleMaster_Returns_Master, SlotRoleUnknown_ReturnsFalse,
    NoFaceForRole_ReturnsFalse}` (operator-pinned BAI `0x03↔0x08` case
    returns `0x08`); `TestEntryAddress_RemovedAtCompile` —
    grep gate: zero references to `entry.Address()` in any *.go file
    after M-C6 merge.
  - **gateway**: `TestB524WriteAddressesSlaveOnAliasedEntry` (BAI
    regression); `TestB524ReadUsesM2S`; `TestB509ScanIDUsesM2S`;
    `TestBusSendRefuses{M2SWithSlaveSrc, M2BCWithNonFEDst,
    UnknownFrameTypeOnReservedTarget}`; `TestBusSendAuditLogsRejection`;
    `TestActivePassiveDeduplicator_DoesNotPropagateParserFrameTypeIntoBusSend`
    (P2-1 negative gate; backed by CI `git grep` + AST check — see M-C7).
- Acceptance: each test fails with the SAME error class expected post-impl
  (compile-error, panic, or `accessor not implemented`); cruise-dev-supervise
  observes each per-repo RED commit hash before approving impl.

## M-C1_ADDRESS_CLASS — `AddressClass` enum + classifier

- Repo: `helianthus-ebusgo` (`protocol` package)
- Complexity: 3
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required (consumed M-C0)
- Scope:
  - Add `protocol.AddressClass` 4-value enum per AD25; zero value =
    `AddressClassReserved`.
  - Add `protocol.AddressClassOf(b byte) AddressClass` classifier per the
    256-byte mapping rules in `12-address-table.md`. Reuse existing
    `IsInitiatorCapableAddress` for Master detection — no duplication.
  - 256-case unit test covering exact partition; pinned cases enforced.
- Acceptance: M-C0B ebusgo `TestAddressClass_*` RED tests turn GREEN; existing
  test suite passes; allocation budget on hot path zero (`go test -bench` if
  applicable). No public API rename in this milestone (additive only).

## M-C2_FRAMETYPE_UNIFY — Single `FrameType` source of truth

- Repo: `helianthus-ebusgo` (`protocol` package)
- Complexity: 4
- Routing: Codex
- Transport-gate: not-required (no wire change yet; rename only)
- Doc-gate: not-required
- Scope:
  - Rename parser-internal enum values per AD27:
    `FrameTypeInitiatorTarget`→`FrameTypeM2S`,
    `FrameTypeInitiatorInitiator`→`FrameTypeM2M`,
    `FrameTypeBroadcast`→`FrameTypeM2BC`. Keep `FrameTypeUnknown` as zero.
  - Provide deprecation aliases for one release cycle (typed `const` with
    `// Deprecated:` doc comment) so downstream PRs in adapter-proxy +
    gateway can migrate non-atomically within the cross-repo window.
  - String marshalling of the enum updated to the new names.
- Acceptance: M-C0B ebusgo `TestFrameType_RenameMapping` RED tests turn
  GREEN; downstream gateway + adapter-proxy still compile against the
  deprecation aliases; reconstructor golden-fixture parity preserved.

## M-C3_FRAME_VALIDATE — `Frame.FrameType` field + `Frame.Validate()`

- Repo: `helianthus-ebusgo` (`protocol` package)
- Complexity: 4
- Routing: Codex
- Transport-gate: not-required (no wire change yet; method-only addition)
- Doc-gate: not-required (consumed M-C0)
- Scope:
  - Add optional `FrameType FrameType` field to `protocol.Frame`. Zero value
    preserves the existing `Frame.Type()` derivation behavior; non-zero
    values are honored as caller-declared.
  - Add `Frame.Validate() error` method that runs the AD26 contract
    (clauses 1–6) using the `protocol.AddressClass` classifier from
    M-C1. The body wraps the package-private helper
    `validateFrameAddressing(ft, src, dst byte) error` which is exposed
    to ebusgo's own tests but not to consumers.
  - Add `protocol.ErrInvalidFrameAddress` sentinel error.
  - This is **additive only**: `RawTransport.Send` interface signature is
    unchanged; existing callers that do not set `Frame.FrameType` continue
    to work via the `FrameTypeForTarget(Target)` fallback. No deprecation
    aliases are needed because nothing was renamed.
- Acceptance: M-C0B ebusgo `TestFrame_Validate_*` RED tests turn GREEN;
  existing reconstructor + emitter tests pass unchanged; benchmarks confirm
  pure-function inlining (zero allocations).

## M-C4_VALIDATOR — Pure-function exhaustive sweep

- Repo: `helianthus-ebusgo` (`protocol` package)
- Complexity: 3
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required
- Scope:
  - Sample test surface: `4 (FrameType including zero) × 256 × 256 = 262 144`
    cases; sample per `12-address-table.md` Test surface: boundary classes
    per `ft`, pinned accept/reject cases, reserved-byte rejections,
    `FrameTypeUnknown` rejection AFTER fallback (only when target is reserved),
    `src == dst` rejection, zero-FrameType fallback equivalence to
    `FrameTypeForTarget`, and the AD26 clause-6 caller-vs-central
    mismatch.
  - Microbenchmark: `BenchmarkFrameValidate_Hot` proves zero allocations
    and sub-100 ns/call on Apple M-class and RPi4.
- Acceptance: sampled exhaustive sweep passes; benchmarks meet target;
  CI publishes the bench numbers in PR body.

## M-C5_BUS_SEND_ENFORCE — Wire `Frame.Validate` into Bus.Send

- Repo: `helianthus-ebusgo` (Bus / EventBus emit path) and
  `helianthus-ebus-adapter-proxy` (proxy must propagate `ErrInvalidFrameAddress`
  unchanged from upstream)
- Complexity: 3
- Routing: Codex
- Transport-gate: REQUIRED
- Doc-gate: not-required
- Scope:
  - Modify `Bus.Send` (or its EventBus equivalent that is the gateway's
    actual emit boundary) to invoke `frame.Validate()` at the very top of
    its body. On non-nil error, return immediately without writing to the
    wire.
  - Emit a structured WARN log with `(ft, src, dst, callsite_pc)` and a
    Prometheus counter `ebus_transport_invalid_frame_address_total{ft,...}`
    on rejection (Bus.Send-side, not validator-side per AD26).
  - Pass-through behavior on accept: byte-stream identical to pre-Phase-C.
  - `helianthus-ebus-adapter-proxy`: confirm that the proxy's forwarding
    path does not strip `Frame.FrameType` and that an upstream
    `ErrInvalidFrameAddress` propagates back to the caller without being
    rewritten. NO new validator runs in the proxy — single-validator
    invariant.
- Acceptance: M-C0B gateway `TestBusSendRefuses*` RED tests turn GREEN;
  fuzz harness with 10 000 random `(ft, src, dst)` tuples shows reject
  rate matches validator semantics; Prometheus counter increments
  correctly; adapter-proxy compile-only changes verified by
  `TestProxyForwardsFrameWith*` tests.

## M-C6_REGISTRY_HELPERS — `DeviceEntry.AddressByRole`

- Repo: `helianthus-ebusreg`
- Complexity: 4
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: not-required (model already in `12-address-table.md` + ATR
  `01-address-table-model.md`)
- Scope:
  - Add `(d *deviceEntry) AddressByRole(role registry.SlotRole) (byte, bool)`.
    Iterates `d.Faces[]` and returns the first `BusFace` whose `Role`
    matches. The function does NOT take a `protocol.FrameType` — registry
    stays protocol-agnostic; caller maps its frame type to `SlotRole`
    locally (M2S writer asks `SlotRoleSlave`; M2M asks `SlotRoleMaster`).
  - **REMOVE `entry.Address()`** (operator-pinned, no deprecation
    window). Same PR enumerates all callers via
    `git grep -nE 'entry\.Address\(\)|\.Address\(\)' -- '*.go'`,
    migrates each to `AddressByRole(...)`, and deletes the method
    from `DeviceEntry` interface + `deviceEntry` impl + `*Entry`
    receiver. Build break = caller missed.
- Acceptance: M-C0B ebusreg `TestDeviceEntry_AddressByRole_*` turn
  GREEN; BAI `0x03↔0x08` alias returns `0x08` for `SlotRoleSlave`;
  `TestEntryAddress_RemovedAtCompile` turns GREEN (zero `entry.Address()`
  references in repo); MCP `devices` + GraphQL consumers compile + tests
  green.

## M-C7_SEMANTIC_API_ENRICH — Per-API-site frame-type declaration

- Repo: `helianthus-ebusgateway`
- Complexity: 6
- Routing: Claude (correctness-heavy; per-service spec audit)
- Transport-gate: REQUIRED
- Doc-gate: not-required (M-C0 covers the contract; this milestone is
  callsite work)
- Scope: every semantic API call site that constructs a `protocol.Frame`
  for `Bus.Send` declares its `FrameType` per its application-layer spec.
  Final enumeration locked at M-C7 pre-flight from `git grep` against
  post-M-C5 codebase; M-C0's per-service table is the authoritative
  reference (with spec line cites for each entry):
  - `b524.Read` / `b524.Write` → `FrameTypeM2S`.
  - `b524.RootDiscovery` → `FrameTypeM2S`.
  - `b509.ScanID` (0x09 / 0x29) → `FrameTypeM2S`.
  - `b503.*` Vaillant → `FrameTypeM2S` (operator-confirmed: B503 is
    always M2S per Vaillant application-layer convention).
  - `0704.scan` (Identification) → `FrameTypeM2S` (per Spec_Prot_7
    §3.3.5).
  - `b516.*` → `FrameTypeM2S` (operator-confirmed: same as b503).
  - **NM, Service 08h, Service 03h mappings**: per the per-service table
    in `helianthus-docs-ebus/architecture/ebus_standard/12-address-table.md`
    §"Per-application-layer-service frame-type mapping". Summary: NM
    `FFh 00h..02h` are M2BC (broadcast resets/failure); NM `FFh 03h..06h`
    are M2S (unicast interrogations of master-companion slaves); Service
    `08h 00h..03h` are M2BC; Service `08h 04h` is M2S. Service `03h 04h..08h`
    are M2S (single response form); Service `03h 10h` is the runtime-target
    branching exception below. The doc table carries Spec_Prot_7 line cites
    per row.
  - **Service 03h 10h runtime-target branching**: caller MUST set
    `Frame.FrameType` based on the runtime `Target` byte. M2S branch
    when `AddressClass(Target) == Slave`; M2M branch when
    `AddressClass(Target) == Master`. Validator's clause-6 cross-check
    is the load-bearing assertion. This is the only call site that
    legitimately reads `AddressClass(target)` to choose branch.
  - Startup source-selection-validation probe `0x07 / 0x04` →
    `FrameTypeM2S` (per `12-address-table.md` Startup Source-Selection
    Boundary).
  - Address-table inserter forensic test injections → mirror the frame
    type observed; never `FrameTypeUnknown` unless deliberately probing
    the reserved-target rejection path.
- Negative gates (CI lints in `gateway/internal/lints/`):
  - **G1 (P2-1)**: zero `Bus.Send.*FrameTypeUnknown` matches outside
    test files; AST-walk asserts no `*protocol.Frame.FrameType` from
    reconstructor output flows into `Bus.Send` in
    `active_passive_deduplicator.go`.
  - **G2 (P2-A)**: every `Bus.Send` callsite outside tests sets
    `Frame.FrameType` explicitly — zero-value-by-omission rejected
    (closes silent fallback foot-gun).
- Acceptance: every callsite passes a non-`FrameTypeUnknown` value;
  CI grep gate green; CI AST gate green; Prometheus
  `ebus_transport_invalid_frame_address_total` counter remains at zero
  during a 10-minute live soak with default polling; no behavior delta
  on golden-fixture replay.

## M-C8_LIVE_VALIDATION — Falsifiability gate, live HA deploy

- Repo: `helianthus-ebusgateway` (deploy + assertions)
- Complexity: 4
- Routing: Claude (live validation orchestration)
- Transport-gate: REQUIRED
- Doc-gate: not-required
- Scope: cross-compile + deploy gateway to HA (192.168.100.4) per existing
  flow. Run assertion suite (positive + negative split):
  - **Positive wire-level**:
    - **C-P1**: BAI ecoTEC M2S writes address `0x08` (pcap), NOT `0x03`.
      Operator pcap + M-C0A regression fixture turn negative.
    - **C-P3**: B524 read on BAI alias via
      `entry.AddressByRole(SlotRoleSlave)` addresses `0x08`.
    - **C-P7**: NETX3 M2S writes go to `0xF6` (paired) or `0x04`, not
      `0xF1`/`0xFF`. Both alias resolutions traced.
    - **C-P2**: NM `FFh 00h` emits with `dst == 0xFE` (M2BC, accepted);
      NM `FFh 03h` emits at master-companion slave (M2S, accepted).
  - **Positive synthetic harness** (deliberate-wrong-class injection):
    - **C-P4**: M2BC with `dst == 0x08` → `Bus.Send` returns
      `ErrInvalidFrameAddress`, counter increments.
    - **C-P5**: `Target == 0xAA` → fallback resolves to
      `FrameTypeUnknown`, rejected.
    - **C-P6**: `Source == Target` → rejected.
    - **C-P8**: explicit `FrameType = M2BC` but `Target = 0x08` →
      clause-6 mismatch, rejected.
  - **Negative soak**:
    - **C-N1**: 10-min live soak — strictly ZERO
      `ebus_transport_invalid_frame_address_total` increments
      (counter dump on PR; drift thresholds in
      `runbooks/phase-c-rollback.md` §1).
    - **C-N2**: Phase A registry behavior unchanged — same DeviceEntry
      count, same alias structure (BAI `0x03↔0x08`, BASV2 `0x10↔0x15`).
    - **C-N3**: `entry.Address()` removal verified — `git grep` returns
      zero matches; all migrated to `AddressByRole(SlotRoleSlave|Master)`.
- Acceptance: ALL C-P1..C-P8 pass; C-N1 + C-N2 + C-N3 hold; HA consumer
  compatibility unchanged (no entity churn); M-C8 PR carries pcap evidence
  for C-P1, C-P3, C-P7 plus counter dump for C-N1.

## M-C9_TRANSPORT_VERIFY — Transport-gate post-change verify

- Repo: `helianthus-ebusgateway`
- Complexity: 2
- Routing: Codex
- Transport-gate: REQUIRED (this IS the post-change verify)
- Doc-gate: not-required
- Scope: re-run T01..T88 transport matrix; diff vs M-C0A baseline; require
  zero unexpected fail/xpass deltas; require zero byte-stream deltas for
  every well-typed sender (the validator's accept path is byte-equivalent to
  pre-Phase-C). PR body carries the diff. Specifically include the
  M-C0A regression fixture replay: `testdata/regression_aliased_write_to_initiator/`
  golden bytes must produce the post-Phase-C `.expected.txt` output.
- Acceptance: zero unexpected fail/xpass deltas; cruise-merge-gate passes.

## M-C10_DOC_EVIDENCE — Post-merge evidence rollup

- Repo: `helianthus-docs-ebus`
- Complexity: 2
- Routing: Codex
- Transport-gate: not-required
- Doc-gate: REQUIRED (closes the loop opened in M-C0)
- Scope: append post-merge evidence to
  `architecture/atr/07-live-validation-acceptance.md`:
  - C-P1..C-P8 outcome with pcap artifact references.
  - C-N1 soak counter dump.
  - C-N2 registry diff.
  - C-N3 deprecation log evidence.
  - Transport-matrix M-C0A vs M-C9 diff.
  - Link to M-C8 PR + M-C9 PR + cruise-state meta-issue.
  - Confirm 256-byte taxonomy + frame-type-contract hash from M-C0
    matches the merged file's actual hash from
    `check_address_table_taxonomy_hash.sh`; cite both v1 hash and new
    hash.
- **Hash regression gate**: `check_address_table_taxonomy_hash.sh`
  recomputes the taxonomy block hash and hard-fails if it diverges
  from the pinned `316baf20ab0d0a64b36613bb8c7604d7570fecc01071daca94931029ae82ebec`
  in `12-address-table.md`. Any edit to taxonomy/frame-type/validator
  sections requires recompute + pin update in the same PR.
- Acceptance: cruise-doc-gate skill verifies M-C0 + M-C10 alignment;
  companion docs PR satisfies code-PR doc requirement; new taxonomy hash is
  recorded as the canonical post-merge value; placeholder absent from
  merged main.

## Phase C iteration vs merge dependencies

| Milestone | iteration_depends_on | merge_depends_on |
| --- | --- | --- |
| M-C0_DOC_SPEC | — | — |
| M-C0A_TRANSPORT_BASELINE | M-C0 | M-C0 |
| M-C0B_TDD_GATE/ebusgo | M-C0 | M-C0 |
| M-C0B_TDD_GATE/adapter-proxy | M-C0, M-C0B/ebusgo | M-C0, M-C0B/ebusgo |
| M-C0B_TDD_GATE/ebusreg | M-C0 | M-C0 |
| M-C0B_TDD_GATE/gateway | M-C0, M-C0B/{ebusgo, adapter-proxy, ebusreg} | M-C0, M-C0B/all |
| M-C1 | M-C0, M-C0B/ebusgo | M-C0, M-C0A, M-C0B/ebusgo |
| M-C2 | M-C0, M-C0B/ebusgo | M-C0, M-C0A, M-C1, M-C0B/ebusgo |
| M-C3 | M-C0, M-C1, M-C2, M-C0B/ebusgo | M-C0, M-C0A, M-C1, M-C2, M-C0B/ebusgo |
| M-C4 | M-C0, M-C1, M-C2, M-C3, M-C0B/ebusgo | M-C0, M-C0A, M-C1..M-C3, M-C0B/ebusgo |
| M-C5 | M-C0, M-C3, M-C4 | M-C0, M-C0A, M-C1..M-C4, M-C0B/all |
| M-C6 | M-C0, M-C0B/ebusreg | M-C0, M-C0B/ebusreg |
| M-C7 | M-C0, M-C5, M-C6 | M-C0, M-C0A, M-C1..M-C6, M-C0B/all |
| M-C8 | M-C0, M-C5, M-C6, M-C7 | all impl milestones |
| M-C9 | M-C0, M-C8 | M-C0, M-C0A, all impl milestones |
| M-C10 | M-C0, M-C8, M-C9 | M-C0, M-C0A, M-C8, M-C9 |

Routing summary: 11 of 13 Phase C milestones routed Codex (easy/medium dev).
2 Claude-routed (M-C7 per-API-site spec audit, M-C8 live validation
orchestration). Note: AD24's removal of the `RawTransport.Send` signature
change drops the previous M-C3 from Claude (cross-repo coordination) to
Codex (single-repo additive method).

Transport-gate REQUIRED for 4 milestones (M-C0A baseline, M-C5 enforcement,
M-C7 callsite-wide change, M-C9 verify). M-C8 also runs the matrix as part
of falsifiability.

Doc-gate REQUIRED for 2 milestones (M-C0, M-C10) — both in
`helianthus-docs-ebus`.

## Risk register (Phase C)

- **R-C1** AD24 made the change additive. Residual risk: downstream
  consumer pins old ebusgo lacking `Frame.FrameType`. Mitigation: M-C2
  deprecation aliases; ebusgo go.mod pin-bump in adapter-proxy + ebusreg
  + gateway is routine follow-up, not a blocker.
- **R-C2** M-C7 omits a callsite, producing runtime
  `ErrInvalidFrameAddress` on legitimate ops. Mitigation: CI grep gate
  (zero `Bus\.Send.*FrameTypeUnknown` outside tests) + AST gate vs
  active_passive_deduplicator; M-C8 live soak counter at zero.
- **R-C4** AD30 `entry.Address()` REMOVAL may surprise downstream
  consumer call sites (MCP, GraphQL). Mitigation: M-C6 enumerates
  all callers via `git grep`, migrates each to `AddressByRole(...)`
  in the same PR; CI build break = caller missed. No deprecation
  window — operator-pinned: removal happens at M-C6 merge.
- **R-C5** Validator hot-path overhead. Mitigation: M-C4 benchmark
  proves zero allocations + sub-100 ns/call on Apple M-class and RPi4.
- **R-C6** Service 03h 10h is the only case where caller `FrameType`
  can disagree with `FrameTypeForTarget`. Wrong declaration triggers
  both clause-6 and clause-3 rejections — intentional defense-in-depth.

## Rollback

If M-C8 falsifies (any C-P fails, or C-N1 counter increments under default
polling, or C-N2 shows registry drift), the runbook at
`helianthus-execution-plans/runbooks/phase-c-rollback.md` is the
authoritative procedure. Reverse-merge order, per-repo revert commands,
post-rollback verification, and the floor-for-next-attempt are captured
there. This chunk does not inline the rollback procedure to keep the
locked plan stable.

## Open questions

(All round-2 open questions resolved by operator pre-lock. None remain.)
