# Common Firmware Rewrite 04: Deterministic Observability Contract + Per-Family HALs

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: Chunks 01-03. Decision 10 (observability from day zero) and Decision 7 (no dynamic allocation) from Chunk 01 constrain the observability contract. The test taxonomy (Chunk 03, Section 6L: OBS-* self-tests) validates the observability counters. Per-family memory budgets from v1.0 HALs determine what observability features are affordable per family.

Scope: Deterministic observability contract (mandatory counters, optional counters, event markers, ring buffers, retention rules, timing impact budget, memory budget, query surfaces, forbidden items) and per-family HAL additions (tinyebus tier annotations for v5/C6, v3.x PIC, ESERA).

Idempotence contract: Reapplying this chunk must not create conflicting counter definitions, duplicate memory budget entries, or ambiguous timing impact thresholds.

Falsifiability gate: A review fails this chunk if any mandatory counter lacks explicit type and semantics, if the timing impact budget is not quantified in microseconds, if the memory budget exceeds PIC18 2KB RAM for the mandatory-only configuration, if any forbidden item uses vague justification, or if per-family tinyebus tier annotations contradict the adjudication in Chunk 02.

Coverage: Section 7 (Deterministic Observability Contract); Section 8 (Per-Family Hardware Adaptation Layers).

---

## 7. Deterministic Observability Contract

### 7A. Mandatory Counters (ALL Families)

These counters MUST be implemented from the first functional milestone (M3) and MUST NOT be conditional.

| Counter | Type | Semantics | Reset behaviour |
|---------|------|-----------|----------------|
| `rx_bytes` | uint32 wrapping | Total eBUS bytes received from bus | Cleared on firmware reset |
| `tx_bytes` | uint32 wrapping | Total bytes transmitted to bus | Cleared on firmware reset |
| `rx_frames_enh` | uint32 wrapping | ENH frames received from host | Cleared on firmware reset |
| `tx_frames_enh` | uint32 wrapping | ENH frames sent to host | Cleared on firmware reset |
| `rx_drops` | uint32 wrapping | Bytes dropped due to RX buffer overflow | Cleared on firmware reset |
| `arb_started` | uint32 wrapping | Successful arbitrations (STARTED sent) | Cleared on firmware reset |
| `arb_failed` | uint32 wrapping | Failed arbitrations (FAILED sent) | Cleared on firmware reset |
| `errors_ebus` | uint32 wrapping | ERROR_EBUS events sent | Cleared on firmware reset |
| `errors_host` | uint32 wrapping | ERROR_HOST events sent | Cleared on firmware reset |
| `resets` | uint32 wrapping | Hardware/watchdog resets since first boot | Persisted if config persistence available (F22) |
| `info_queries` | uint32 wrapping | INFO requests received | Cleared on firmware reset |
| `sessions_total` | uint32 wrapping | TCP sessions created (0 on non-TCP) | Cleared on firmware reset |

**Total: 12 counters x 4 bytes = 48 bytes.** Fits on every family.

### 7B. Optional Counters (SHOULD on Capable Families)

| Counter | Type | Semantics | Families |
|---------|------|-----------|----------|
| `arb_latency_max_us` | uint32 | Maximum SYN-to-TX latency observed (us) | v5/C6, ESERA |
| `arb_latency_min_us` | uint32 | Minimum SYN-to-TX latency observed | v5/C6, ESERA |
| `bus_idle_ms` | uint32 | Time since last bus activity (ms) | v5/C6, ESERA |
| `syn_count` | uint32 wrapping | SYN (0xAA) bytes received | v5/C6, ESERA |
| `session_active` | uint8 | Currently active TCP sessions | v5/C6, ESERA |
| `uptime_seconds` | uint32 wrapping | Seconds since last reset | v5/C6, ESERA |

**Total: 21 additional bytes.** Requires P-MEMORY + P-NON-INTERFERENCE.

### 7C. Mandatory Event Markers

| Event | When fired | Observable via |
|-------|-----------|---------------|
| RESET | Firmware boots after any reset | INFO 0x06 + unsolicited RESETTED |
| OVERFLOW | RX buffer drops a byte | `rx_drops` counter increment |
| ERROR | Any ERROR_EBUS or ERROR_HOST sent | counter increment |
| SESSION_START | TCP session accepted | `sessions_total` counter increment |
| SESSION_END | TCP session closed | `session_active` decrement (if optional counters enabled) |

### 7D. Ring Buffers

| Buffer | Mandatory? | Size | Overflow |
|--------|-----------|------|----------|
| Wire-log ring | MAY-IF-PROVEN (F13) | 64 entries x 38B = 2432B (compile-time) | Drop oldest entry |

### 7E. Retention and Overflow Rules

- All counters use wrapping uint32 arithmetic. No counter may cause an error or reset on overflow.
- Wire-log ring uses circular overwrite (drop oldest).
- No counter or buffer writes to flash during normal operation (flash wear prohibition).

### 7F. Timing Impact Budget

| Operation | Budget | Enforcement |
|-----------|--------|-------------|
| Single counter increment | < 1us | Code review (atomic word write) |
| Wire-log entry write | < 5us | P-NON-INTERFERENCE measurement |
| Total observability overhead per eBUS byte | < 5us | TIME-OBS-OVERHEAD test |
| Maximum observability impact on arbitration | < 5us (1.2% of bit-time) | P-NON-INTERFERENCE: arb latency with/without obs |

### 7G. Memory Budget

| Component | Budget | Families |
|-----------|--------|----------|
| Mandatory counters | 48 bytes | ALL |
| Optional counters | 21 bytes | v5/C6, ESERA |
| Wire-log ring (if enabled) | 2432 bytes | v5/C6, ESERA (P-MEMORY) |
| Total (mandatory only) | 48 bytes | ALL |
| Total (full observability) | 2501 bytes | v5/C6, ESERA |

### 7H. Query Surfaces

| Surface | Protocol | Families | Mandatory? |
|---------|----------|----------|-----------|
| INFO extension (new ID 0x08 or via existing) | ENH INFO | ALL | S |
| HTTP /metrics endpoint | HTTP GET | v5/C6, ESERA (if TCP + P-MEMORY) | P |
| Wire-log query | HTTP GET or TCP command | v5/C6, ESERA (if wire-log proven) | P |

### 7I. What MUST NOT Exist

| Forbidden | Why |
|-----------|-----|
| Flash writes for logging | Flash wear, non-deterministic write latency |
| Filesystem on device | Dynamic allocation, unbounded growth |
| Unbounded counters | Wrapping uint32 is sufficient |
| Feedback from counters to protocol SM | Observability is write-only from protocol perspective |
| Observability that blocks eBUS ISR | ISR must never wait on observability |
| Heap allocation for obs buffers | All buffers are statically allocated |
| Network-triggered obs that could DoS | Query endpoints must be rate-limited or non-blocking |

---

## 8. Per-Family Hardware Adaptation Layers

**Status: PRESERVED from v1.0 Sections 3-5 with tinyebus tier annotations.** All MCU specs, pin assignments, USB identity, PHY assumptions, clock/timer sources, worst-case latency analyses, stack choices, memory budgets, constraints, and test hooks from v1.0 are retained. Refer to v1.0 for the complete HAL text.

**Key additions per family:**

### 8A. v5 / C6 — tinyebus Tier B + C optional

Memory budget addition: mandatory obs 48B, optional obs 21B, wire-log 2432B, tinyebus C library ~2KB flash + ~256B RAM. Total obs overhead ~2.5KB RAM.

### 8B. v3.x PIC — tinyebus Tier A (possibly B after M0)

tinyebus tier depends on M0 RE: PIC18 with 2KB = Tier A only. PIC24 with 8KB+ = MAY Tier B. Mandatory counters (48B) MUST fit on any PIC.

### 8C. ESERA W7500P — tinyebus Tier B + C conditional

Memory: ~32KB application RAM after Ethernet buffers (~16KB). tinyebus C library + mandatory obs fit. Wire-log and query engine require P-MEMORY proofs.
