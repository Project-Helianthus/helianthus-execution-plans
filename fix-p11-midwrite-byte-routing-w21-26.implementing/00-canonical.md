# fix-p11-midwrite-byte-routing-w21-26 — canonical plan

## Objective

Restore semantic-layer plane population on production HA host. Specifically: `discoverB524Root` must resolve `0x15` within 60 seconds of addon startup under normal Vaillant bus contention, and all 12 B524-driven semantic MCP planes must return non-null data within the same window.

## Problem statement

### Symptom

On 2026-05-21 ~18:10 the operator observed that production Prometheus stopped receiving B524 metric data. Investigation 2026-05-22 confirmed:

- MCP `ebus.v1.semantic.*.get` returned `data:null` for 7 of 12 planes (zones, circuits, dhw, radio_devices, solar, cylinders, schedules).
- Gateway log: `semantic_b524_root: gateway.discoverB524Root: no coherent responder among [0x15, 0x04, 0x08, 0x26, 0x36, 0xf6, 0xfc]` repeated every ~3 minutes.
- The 0x15 (BASV2/VRC controller) device entry in the device registry had `planes=[]` (empty) despite normal devices like 0x08 (BAI) having full plane sets.

On 2026-05-23 ~04:18Z (about 9 hours after addon restart) the semantic layer self-recovered — `semantic_b524_root_discovery address=0x15 probed=4` log line appeared and planes populated. The bug is therefore not "never works" but "takes hours to recover under contention".

### Two failure modes (confirmed via production logs)

**Mode A** — `writes=1 echoLike=0 nonEcho=22`. After adapter signals `StreamEventStarted data=0x7F` (gateway "wins" arbitration), the FIRST wire byte the gateway sees does not match its first expected echo; it is the leading byte of another initiator's frame (e.g., `0xF1` — Vaillant internal system-register-access initiator). The current P11 round-2 gate at `helianthus-ebusgateway/internal/adaptermux/mux.go:2315-2317` drops the foreign byte. `helianthus-ebusgo/protocol/bus.go`'s first-byte-after-arbitration classifier at `bus.go:1328-1378` never sees the byte, so cannot raise `ErrBusCollision`. Result: 2-second `active_read_timeout`, no retry, txn ends with `class=non_echo_invalid_frame`.

**Mode B** — `writes=11 echoLike=8 nonEcho=68 dur=2.1s`. The gateway writes a full 11-byte B524 request, 8 echoes match, but the LAST 3 bytes' echoes do not return. Either bytes 9–11 were lost on the wire (mid-frame collision), or the target's response phase interleaves with other initiator traffic (42 SYNs observed in 2 seconds = high contention). `bus.Send` waits for a response that never arrives coherently.

This plan addresses **Mode A only**. Mode B is deferred to a follow-up plan.

### Operator hint

> "Assuming arbitration wins is wrong. We screwed something up."

The hint maps exactly to the P11 round-2 gate's premise: once arbitration is "won", the code assumes nothing else can be on the wire. When that assumption fails — false arbitration win, adapter buffering, or a competing initiator with overlapping address — the filter blocks legitimate wire traffic from reaching the active sender.

## Root cause

`helianthus-ebusgateway/internal/adaptermux/mux.go:2315-2317` (commit `a35b51d1`, PR #606, landed 2026-05-10):

```go
activeExpects := m.gatewayTxnActive
if activeExpects && hadPendingEcho {
    // Mid-write: only the next expected echo passes.
    activeExpects = symbol == preMatchHead
}
```

This strict mid-write filter drops every wire byte that does not exactly match `preMatchHead`. Under sustained background contention from third-party initiators (low rate, ~0.6 c/s, but consistent), the gateway eventually wins arbitration and writes its first byte — but the wire shows another initiator's frame first. The gate suppresses all 22 bytes of the foreign frame, the gateway's `bus.Send.ReadByte` consumes nothing, the 2-second timeout fires, and `discoverB524Root` records this candidate as failed.

The retry loop (`bus.go:374-396`) handles `ErrBusCollision` correctly but never receives one, because the mux drops the foreign master-class byte before `bus.go`'s `isFirstByteAfterArbitration` classifier (`bus.go:1356-1361`) can see it.

## Fix direction

Refined Direction C — **event-driven first-byte arbitration revalidation**, with **forward-not-drop** semantics so the existing `bus.go` classifier engages.

At `mux.go:2315-2317`, when ALL of these hold:

- `hadPendingEcho == true`
- `m.gatewayEcho.matchCount() == 0`  (no echo has matched yet in this txn)
- `writeCount == 1`  (only the first byte has been written)
- `symbol != preMatchHead`  (wire byte does not match expected echo)
- `AddressClassOf(symbol) == AddressClassMaster`  (wire byte is an initiator-class address — i.e., a foreign master starting a frame)

Then FORWARD the byte to `activeCh` (do NOT drop). Set a `firstByteSuspectArbLoss` diagnostic flag on `activeTxnDiag`. Let `bus.go:1328-1378` classify the byte as `ErrBusCollision`. Let `sendWithRetries` (`bus.go:374-396`) consume the retry naturally with `collisionBackoffFloor` (50 ms) and `waitForSyn`.

For all OTHER wire-byte mismatches (mid-frame, after first echo matched, non-master-class noise): KEEP the strict P11 drop behaviour. P11 round-2's design intent is preserved AFTER ownership is validated by at least one echo.

### Why not the other directions

- **A (RECOVERY_ON_N_MISMATCH)**: would deliver foreign frame bytes into `bus.Send` as response data, reintroducing the `post_grant_ack` leak that P11 round-2 closed. No safe value of N exists (foreign frames can be 22+ bytes).
- **B (TIME_BASED_FALLBACK)**: same flaw as A, plus T is unpickable (at 2400 baud each wire byte is ~4.2 ms; T=100 ms is 24 bytes of latency; T=500 ms is past per-write timeout).
- **D (HYBRID)**: inherits both A's N-pick problem and the race between soft recovery and hard timeout — partial response is delivered then aborted.

Adversarial reviewers (Codex gpt-5.5 R1; fresh Claude Opus angry-tester R1 and R2) converged on refined Direction C.

## Outcome required

| ID | Outcome | Measurable predicate |
|---|---|---|
| O1 | Semantic planes populate fast | Within 60 s of addon startup, all 12 MCP `ebus.v1.semantic.*.get` planes return non-null `data`. Pre-fix observed: ~9 hours. |
| O2 | B524 root discovered fast | `semantic_b524_root_discovery address=0x15` log line within 60 s of `RequestStart(0x7F)` for session 0. Pre-fix observed: ~9 hours. |
| O3 | Round-9 invariant preserved | 90-min parallel `ebusd + ENS-direct` stress test: `helianthus_round9_absorb_entered_total` slope = 0/min. Pre-fix baseline: 0 entries. |
| O4 | P11 invariant preserved (bounded) | `ebus_active_echo_mismatch_subclass_total{subclass="post_grant_ack"}` rate post-fix ≤ **10 events/hour absolute**. Pre-fix baseline rate = 0 (counter never surfaced in 9 hours of runtime). Ratio-based bound is unusable because 2 × 0 = 0. |
| O5 | Contention amplification bounded | `ebus_errors_total{class="collision",phase="request",scope="active"}` rate post-fix ≤ 1.5 × pre-fix rate (~550/hr → ceiling ~825/hr). |

## Scope

### Affected repos

- `helianthus-ebusgateway` (PRIMARY) — `internal/adaptermux/mux.go`, `internal/adaptermux/echo_tracker.go`, `internal/adaptermux/diag.go`, test additions.
- `helianthus-ebusgo` — *no changes expected*. Existing `bus.go:1328-1378` first-byte-after-arbitration classifier already handles `ErrBusCollision`. If interface plumbing is needed during implementation, add to dependency graph as M3a.
- `helianthus-ha-addon` (FINAL) — version bump to `v0.6.27` with the merged gateway commit pinned.

### Out of scope

- Mode B (`writes=11 echoLike=8`) — deferred to a follow-up cruise plan.
- Re-architecting the arbitration protocol itself (the adapter's `StreamEventStarted`/`StreamEventFailed` contract is fixed).
- Changing the P11 design philosophy (filter mid-write is still right; this is a recovery path for false-positive cases).

## Milestones

| ID | Name | Repo | Description |
|---|---|---|---|
| M0 | DOC_GATE classification | helianthus-execution-plans + helianthus-docs-ebus | Required: docs-ebus entry on "first-byte arbitration revalidation" semantic. Transport-gate: REQUIRED (per Codex A3 — this IS transport byte-routing change). |
| M1 | TDD red tests | helianthus-ebusgateway | 4 unit tests; all FAIL on current main, all PASS post-fix. |
| M2 | TRANSPORT_GATE baseline | helianthus-ebusgateway | Capture pre-fix `post_grant_ack` rate, round-9 rate, semantic-plane null rate (baseline already captured 2026-05-23, see SUMMARY.md). |
| M3a | echoTracker accessors | helianthus-ebusgateway | Add `matchCount()`, `writeCount()` methods to gateway-private `echoTracker`. |
| M3b | mux.go forward-not-drop | helianthus-ebusgateway | Implement the refined Direction C predicate at `mux.go:2315-2317`. |
| M3c | activeTxnDiag flag | helianthus-ebusgateway | `firstByteSuspectArbLoss` diagnostic + log line. |
| M4 | Live verification | HA host .4 | Plane-population gate + stress test + post_grant_ack regression bound + collision-rate bound. |
| M5 | Addon bump | helianthus-ha-addon | `v0.6.27` with `EBUSGATEWAY_VERSION` pin updated to merge commit. CHANGELOG entry. |

## Decision matrix (post-adversarial — LOCKED)

| ID | Decision | Outcome |
|---|---|---|
| AD01 | Fix direction | Refined Direction C: event-driven first-byte arbitration revalidation; forward-not-drop master-class first mismatch. |
| AD02 | Predicate scope | `hadPendingEcho && matchCount==0 && writeCount==1 && AddressClassOf(symbol)==AddressClassMaster && symbol!=preMatchHead`. |
| AD03 | Where the abort signal originates | Mux forwards byte to activeCh; `bus.go:1328-1378` raises `ErrBusCollision`; `sendWithRetries` retries. |
| AD04 | Test 1 assertion shape | Assert `ErrBusCollision` returned within 200 ms, NOT raw byte delivery. |
| AD05 | post_grant_ack regression bound | ≤ 10 events/hour absolute (pre-fix baseline = 0; ratio-based 2× would degenerate to 0). |
| AD06 | Mode B scope | OUT of this plan; separate task for follow-up. Bundling would create race conditions. |
| AD07 | Cross-repo PR ordering | PR1 ebusgo (conditional, likely SKIPPED) → PR2 gateway → PR3 addon. Each PR independently mergeable. |
| AD08 | Transport-gate classification | REQUIRED (not N/A). Touches active transport byte-routing per Codex A3. |
| AD09 | matchEcho mismatch branch reuse | DO NOT reuse — would clear `expectedStructural` and undo round-2 cascade fix. |
| AD10 | Non-ENH (plain) transport coverage | Plan must verify behaviour under plain transport's escape lead `0xA9` / `0x01` pair. |

## Falsifiability gate

A successful fix MUST satisfy ALL outcomes O1..O5 simultaneously during M4 verification on HA host `.4` with `v8_classifier_mode=enforce` and `transport=ens`. Any single failure rolls back the deploy and re-enters M3 with the failure mode documented as new evidence.

## Idempotence contract

The plan is idempotent at the repository state level: re-running M3 against an already-locked plan is a no-op (the predicate is either already present or not); re-running M4 verification with the same gateway commit yields the same pass/fail decision modulo non-deterministic bus contention noise (which the O4/O5 bounds account for).

## Dependencies

| From | To | Reason |
|---|---|---|
| M1 | M3 | TDD strict — tests must fail on current main before fix lands. |
| M2 | M4 | Pre-fix baseline numbers feed M4's regression bounds. |
| M3a | M3b | echoTracker accessors are called from the new gate predicate. |
| M3b | M3c | Diagnostic flag is set inside the new predicate branch. |
| M3 | M4 | Implementation must merge before live verification. |
| M4 | M5 | Live verification must pass before addon ships. |

No cycles. No orphan deps. No cross-repo dep without coordination note.

## Coverage

- All four open questions from DRAFT_PLAN_v0 answered by Codex R1 and fresh-Opus R1.
- All five Codex attacks (A1–A5) addressed via AD05, AD06, AD08, M1 test design.
- All eight fresh-Opus attacks (A1–A8) addressed via AD09, baseline capture, Mode A/B split.
- All six fresh-Opus missed diagnostics (D1–D6) folded into root cause analysis and AD02 predicate refinement.
- Both adversaries agree on direction and predicate shape; no R3 needed.

