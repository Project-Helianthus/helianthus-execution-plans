# 10 — Scope, Problem, Out-of-Scope, Normative Anchors

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `345445f1cedfc21e6c35d6e0f21513979fbf7ff3a520978932f0dd82e65c1b3d`

Depends on: None. This chunk establishes the problem statement, scope,
hard out-of-scope guards, and the frozen normative anchors.

Scope: Observed adapter-direct ENS scan storm; two-layer root cause
(unvalidated `ScanSource` + `DefaultScanTargets` full-range fall-
through); startup ordering inversion in `cmd/gateway/main.go`; list of
in-scope items (JoinBus adapter, startup ordering flip, evidence
pipeline, degraded-mode surfaces, operator override, full-range retry
guard, ebusreg directed scan API, doc-gate companion, transport-gate
matrix); list of hard-out-of-scope items; frozen normative anchors.

Idempotence contract: Declarative-only. Reapplying this chunk must not
broaden the in-scope list, erase any hard out-of-scope item, weaken
the frozen normative anchors, or reintroduce a full-range fall-through
on non-ebusd-tcp transports. The 0.5%/2% NM-class budget numbers and
the ebusd-tcp-only sanctioned retry policy remain frozen.

Falsifiability gate: Review fails this chunk if it (a) denies that the
root cause has two layers that must be fixed jointly, (b) permits
active frames before a valid `JoinResult` on join-capable direct
transports without operator override, (c) reintroduces `DefaultScanTargets`
fall-through on adapter-direct transports, (d) removes any normative
anchor from the frozen list, or (e) relaxes a hard-out-of-scope item.

Coverage: Summary; Scope; Out of Scope (hard guard); Normative Anchors
(frozen) from the canonical plan.

## Summary

Under `cfg.ScanOnStart=true` on adapter-direct ENS @ 192.168.100.2,
observed over a 60s window: `scan_07_04=58`, `echo_only_timeout=61`,
`candidate_no_parse=12`, `writePrefix` contaminated by concurrent
B524/B509 passive traffic, and adapter heap/signal instability under
sustained initiator bursts. `-scan=false` → all zero.

Root cause splits cleanly in two:

- **Admission layer**: gateway issues active frames using a static
  configured `ScanSource` (default `0xF0`, or `0xF7` when proxy-auto-
  resolved). The source is never validated against the live bus — no
  address-pair authority, no companion-target occupancy check, no
  observe-first warmup. `config.go:152-160` and `startup_scan.go:216
  (proxyObserveFirstStartupSource)` are not `JoinResult`s.
- **Discovery layer**: `cmd/gateway/startup_scan.go:554` invokes
  `registry.Scan(..., nil)` which falls through to
  `scan.go:181-188 DefaultScanTargets()` and probes `0x01..0xFD` with
  `07 04`.

`cmd/gateway/main.go` starts the discovery scan (line 192) BEFORE the
passive transaction reconstructor (lines 235-239). This inversion
must flip for Joiner wiring to have a frame source to listen on.

Fixing the discovery layer alone still leaves the admission layer:
probes from an unvalidated source can still collide and conflict with
companion targets even if target selection is narrow. Both layers must
be remediated together. This plan combines ISSUE-GW-JOIN-01 (Joiner
admission from the parent plan
`ebus-good-citizen-network-management.maintenance`) with scan
remediation, because active probing without validated admission is the
original defect.

On join-capable direct transports (ENH, ENS, UDP-plain, TCP-plain) the
gateway wires a `JoinBus` adapter subscribed to
`PassiveTransactionReconstructor`, runs a `protocol.NewJoiner` warmup
(default `JoinConfig`: 5s warmup, inquiry disabled, persist-last-good
enabled), and only after a successful `JoinResult` does it emit any
Helianthus-originated active frames, using `JoinResult.Initiator` as
source. Discovery replaces the full-range scan with a passive-first
evidence pipeline: suspects are promoted from reconstructor events and
confirmed by directed `07 04` probes through a new
`helianthus-ebusreg` directed scan API. `ebusd-tcp` does NOT run
`Joiner`; it continues to use the configured `ScanSource` as
admission-fallback per `nm-participant-policy.md:38-48`.

## Scope

In scope:

- **JoinBus adapter** for ENH, ENS, UDP-plain, TCP-plain; subscribes
  only to `PassiveTransactionReconstructor.Subscribe(...)`. Forwards
  only allowed `PassiveClassifiedEvent.Kind`s (broadcast/master-only/
  i2i = request-only; initiator/target-with-response = request then
  inferred response). Abandoned transactions and discontinuity events
  are NOT forwarded. `InquiryExistence` returns explicit sentinel when
  `InquiryEnabled=false`. Uses `protocol.NewJoiner` with default
  `JoinConfig`.
- **Startup ordering flip** on join-capable direct transports:
  INIT/INFO → reconstructor + JoinBus subscribe → Joiner 5s warmup →
  on success, active source = `JoinResult.Initiator` and
  `CompanionTarget` recorded → directed probes against promoted
  suspects → semantic polling enabled last. On Joiner-fail without
  override, `probe_count=0` and active semantic polling `count=0`
  while unsuccessful.
- **Evidence pipeline** (passive-first with bounded directed
  confirmation): promotion on ≥2 observations OR any single strong
  evidence; directed `07 04` via the new
  `helianthus-ebusreg` directed scan API; evidence buffer
  `max_entries=128` LRU + baseline-topology protection; rejoin
  backoff aligned with ebusgo `defaultRejoinBackoffBase=5s` /
  `defaultRejoinBackoffMax=60s`, exponential, capped.
- **Degraded-mode surfaces**: log lines, expvars (including
  escalation counters and a 15-min rolling cumulative accumulator),
  and additive `bus_admission` field in the
  `ebus.v1.bus_observability` envelope with a 30s state-stability
  window.
- **Operator override**: `StartupSource.Override` with opt-in
  `Override.Validate` sub-flag. Soft short-circuit semantics (AD09).
  Config-only persistence; no auto-lift.
- **Full-range retry guard**: sanctioned retry remains ebusd-tcp
  only; non-ebusd-tcp disabled by default, gated behind diagnostic
  flag + ≥1 Vaillant root candidate in evidence buffer.
- **`helianthus-ebusreg` directed scan API**: new
  `ScanDirected`/`ScanOptions{Mode,Targets}` requiring explicit
  non-empty targets; existing `Scan(ctx, bus, reg, source, nil)`
  unchanged.
- **Doc-gate companion** in `helianthus-docs-ebus`: new "Startup
  Admission + Discovery Pipeline" section cross-linked from
  `nm-model.md`, `nm-discovery.md`, and `nm-participant-policy.md`
  §Local Address-Pair Authority. Ratifies discovery-class burst
  budget. Documents the admission-artifact JSON schema (AD23).
- **Transport-gate matrix** over ENH, ENS, ebusd-tcp, UDP-plain,
  TCP-plain with explicit rows for "Join wired?" and "Static-source
  fallback?".

## Out of Scope (hard guard)

Verbatim from operator intent. Any PR touching these items fails
preflight:

- FF 00/01/02 emission
- 07 FF, 07 FE active
- NM state machine (NMInit → NMReset → NMNormal)
- Responder-lane 07 04 response, FF 03-06
- Peer NM interrogation
- ebusd-tcp path behavior changes beyond preserving static-source
  admission-fallback
- Semantic polling refactor
- Passive transaction reconstructor refactor
- Firmware / adapter-proxy changes
- HA integration changes beyond additive `bus_observability` fields

## Normative Anchors (frozen; do not re-debate)

- `helianthus-docs-ebus/architecture/nm-model.md` (L36-52, L132-218)
- `helianthus-docs-ebus/architecture/nm-discovery.md` (L39-196)
- `helianthus-docs-ebus/architecture/nm-participant-policy.md`:
  §"Local Address-Pair Authority" (L18-59) —
  `JoinResult` is preferred source; configured policy is fallback
  only on transports where join is unavailable (notably ebusd-tcp).
  §"Transport Capability Matrix" (L192-214) — ENH, ENS, UDP-plain,
  TCP-plain are join-capable; ebusd-tcp is explicit configured-
  fallback.
  §"Bus-Load Policy" (L216-247) — 0.5%/2% frozen for NM-class.
  §"Cycle-Time Policy, Timer-Reset Event Sources" (L287-307) —
  decode faults and discontinuity events do not reset timers /
  produce evidence (analogous rule for Joiner admission).
- `helianthus-docs-ebus/architecture/b524-semantic-root-discovery.md`
  (L68-78) — sanctioned bounded full-range retry is ebusd-tcp-
  specific (narrowed/preloaded inventory).
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/10-evidence-decisions-and-wire-behaviour.md`
  (L88-111).
- `helianthus-execution-plans/ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md`
  (L149: ISSUE-GW-JOIN-01).
- `helianthus-docs-ebus/protocols/ebus-services/ebus-overview.md`
  (L52-62 join strategy; L88-131 transaction flow; L114-116 target
  response address inference).
- `helianthus-ebusgo/protocol/join.go`
  (L29, L42-47, L129-199, L264-353, L401-415).
- `helianthus-ebusgateway/passive_transaction_reconstructor.go`
  (L24-31 event kinds; L76-82 `PassiveClassifiedEvent` shape with
  `HasResponse`, `Request`, `Response`).

## Bus-Load Math (provisional, ratified in M0)

2400 baud × 8/10 useful bits = **240 wire bytes/s**.

- NM-class sustained: 0.5% = 1.2 B/s (frozen, out of scope to alter)
- NM-class burst: 2.0% = 4.8 B/s (frozen)
- Discovery-class startup burst: 2.0% over 60s startup window (NEW;
  ratified in M0 doc-gate). `probe_count ≤ 15` satisfies this at
  ~5 B/s (2.08% rounds to 2.0% per operator ruling).
- Discovery-class post-startup: 1 probe per 15s steady-state
  (enforced by rate limiter).

Full `07 04` transaction on the wire: 18-22 bytes (request + ACK +
response + ACK + SYN, before escape expansion).

## Parent-plan Relationship

This plan is the narrow-scope execution of ISSUE-GW-JOIN-01 from
`ebus-good-citizen-network-management.maintenance`. Per
`feedback_deprecation_enrichment.md`, the parent is treated as an
enrichment source: its normative artifacts remain authoritative where
they apply; this plan does not rewrite them. M0-scope authors the
plan-lock commit in `helianthus-execution-plans` that adds a one-line
back-reference under ISSUE-GW-JOIN-01 in the parent's
`11-runtime-discovery-and-policy.md` pointing to this plan's
directory. Parent plan state stays `.maintenance`.
