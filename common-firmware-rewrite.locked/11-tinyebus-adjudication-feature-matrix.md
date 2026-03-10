# Common Firmware Rewrite 02: tinyebus Adjudication + Feature Eligibility Matrix

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: Chunk 01 (10-testing-first-philosophy-decisions.md). Decision 1 (tinyebus as common basis) defines the adjudication framework. Proof classes from Section 1C gate every feature.

Scope: tinyebus adjudication across five possible roles and four hardware families, minimal common subset, richer profile, drift safeguards, and the complete 25-feature eligibility matrix with proof requirements per feature class.

Idempotence contract: Reapplying this chunk must not create conflicting tinyebus tier assignments, duplicate feature entries, or ambiguous proof requirements.

Falsifiability gate: A review fails this chunk if any tinyebus role lacks a quantitative cost estimate, if any per-family adjudication uses vague language instead of MUST/SHOULD/MAY/MUST-NOT, if any feature in the eligibility matrix lacks a proof requirement, or if the minimal common subset exceeds PIC18 2KB RAM budget.

Coverage: Section 3 (tinyebus Adjudication); Section 4 (Feature Eligibility Matrix).

---

## 3. tinyebus Adjudication

### 3A. What "tinyebus as base" Means — Five Possible Roles

| Role | Description | Runtime cost | Proof needed |
|------|------------|-------------|-------------|
| **Protocol oracle** | tinyebus Go code defines correct ENH/ENS/STD behaviour; firmware must match | Zero (Go runs on test host only) | P-PARITY |
| **Shared state-machine library** | C port of tinyebus ENH/ENS parsers compiled into firmware | ~2KB flash, ~256B RAM | P-MEMORY |
| **Observability substrate** | tinyebus-defined counter structs and event markers compiled into firmware | ~64-256B RAM | P-MEMORY + P-NON-INTERFERENCE |
| **Local query engine** | On-device wire-log and register-read cache with query API | ~4-16KB RAM, ~8-32KB flash | P-MEMORY + P-NON-INTERFERENCE + P-SOAK |
| **Full runtime** | TCP server, HTTP endpoint, multiple concurrent features | ~32-64KB RAM, ~64-128KB flash | All proofs |

### 3B. Per-Family Adjudication

#### v5 (ESP32-C3, 400KB SRAM, 4MB flash)

| Role | Adjudication | Rationale |
|------|-------------|-----------|
| Protocol oracle | **MUST** | Go oracle runs on test host. Zero firmware cost. |
| Shared state-machine library | **SHOULD** (Tier B) | C port of ENH parser fits easily (~2KB flash, 256B RAM). Shared code reduces drift risk. Must pass P-MEMORY. |
| Observability substrate | **MUST** (mandatory counters) | 64B RAM for mandatory counters is negligible vs 400KB budget. Must pass P-NON-INTERFERENCE. |
| Local query engine | **MAY-IF-PROVEN** (Tier C) | 130KB SRAM headroom is likely sufficient. Requires P-MEMORY + P-NON-INTERFERENCE + P-SOAK. |
| Full runtime | **FORBIDDEN-UNTIL-PROVEN** | Wi-Fi + TCP + multi-client + query engine is aggressive for single-core 160MHz. Requires all proofs. |

#### C6 (ESP32-C6, 512KB SRAM, 4MB flash)

| Role | Adjudication | Rationale |
|------|-------------|-----------|
| Protocol oracle | **MUST** | Same as v5. |
| Shared state-machine library | **SHOULD** (Tier B) | Same as v5. |
| Observability substrate | **MUST** (mandatory counters) | Same as v5. |
| Local query engine | **MAY-IF-PROVEN** (Tier C) | 242KB headroom is generous. Same proofs as v5. |
| Full runtime | **MAY-IF-PROVEN** (Tier C) | Extra 112KB vs v5 makes this plausible. Requires all proofs + Decision 11 gates. |

#### v3.x PIC (2-8KB RAM, 32-128KB flash — estimates pending M0 RE)

| Role | Adjudication | Rationale |
|------|-------------|-----------|
| Protocol oracle | **MUST** | Go oracle runs on test host. Zero firmware cost. |
| Shared state-machine library | **UNKNOWN until M0 RE** | PIC RAM may be too small for C port of ENH parser. If PIC18 with 2KB RAM: likely **Tier A only**. If PIC24 with 8KB+: **MAY-IF-PROVEN (Tier B)**. |
| Observability substrate | **SHOULD** (mandatory counters only) | 48B for counters fits even in 2KB RAM. Optional counters gated on P-MEMORY after M0. |
| Local query engine | **MUST-NOT** | PIC cannot afford 4-16KB RAM for wire-log. |
| Full runtime | **MUST-NOT** | PIC cannot run TCP server or query API. |

#### ESERA W7500P (48KB RAM, 128KB flash)

| Role | Adjudication | Rationale |
|------|-------------|-----------|
| Protocol oracle | **MUST** | Go oracle runs on test host. Zero firmware cost. |
| Shared state-machine library | **SHOULD** (Tier B) | 32KB application RAM can afford C port. Must pass P-MEMORY. |
| Observability substrate | **MUST** (mandatory counters) | 48B for counters is trivial. |
| Local query engine | **MAY-IF-PROVEN** (Tier C) | ~16KB free after baseline is plausible but tight. Requires all proofs. |
| Full runtime | **FORBIDDEN-UNTIL-PROVEN** | 48KB total RAM with Ethernet buffers (~16KB) leaves limited headroom. |

### 3C. Minimal Common tinyebus-Derived Subset (ALL Families)

Every family MUST implement:
1. **Protocol oracle compliance:** firmware behaviour matches tinyebus Go test vectors (P-PARITY).
2. **Mandatory observability counters:** the counter struct from Section 7A, statically allocated, < 64 bytes.
3. **Error classification taxonomy:** error codes from Section 5B.7, matching tinyebus-defined enum values.
4. **INFO protocol responses:** INFO 0x00-0x07 with tinyebus-defined response formats.

This subset costs zero RAM on the oracle side and < 64 bytes on the firmware side. It is achievable on every family including PIC18 with 2KB RAM.

### 3D. Richer tinyebus-Enabled Profile (Stronger Targets Only)

Targets with > 16KB free RAM after baseline MAY implement:
1. **Shared C state-machine library:** tinyebus ENH parser, ENS baud adapter, STD framing — compiled into firmware.
2. **Extended observability:** optional counters, arbitration stats, wire-log ring buffer.
3. **Local query helpers:** bounded register-read cache, wire-log query endpoint.

Each feature requires its own proof chain. No feature is automatically included by virtue of being on a "stronger" target.

### 3E. Safeguards Against tinyebus Drift

| Risk | Mitigation |
|------|-----------|
| C port diverges from Go oracle | P-PARITY harness runs both Go oracle and C firmware against same stimulus; any byte-level difference fails the test |
| tinyebus Go repo changes break firmware compliance | Firmware CI pins tinyebus Go dependency to a tagged version; compliance harness runs on every firmware commit |
| Shared library grows beyond PIC budget | Compile-time size check in CI; library has `#ifdef TINYEBUS_MINIMAL` for counter-only mode |
| Observability counters introduce hidden coupling | Counters are write-only from ISR/task perspective; query is read-only via INFO or debug endpoint; no feedback path into protocol state machine |
| Optional features on C6 create protocol drift | Optional features MUST NOT alter ENH/ENS wire behaviour; they are observability or management features only |

---

## 4. Feature Eligibility Matrix

### 4A. Matrix

Legend: **M** = MUST, **S** = SHOULD, **P** = MAY-IF-PROVEN, **X** = MUST-NOT, **?** = UNKNOWN until experiment

| # | Feature | v5 | C6 | v3.x PIC | ESERA | Proof required |
|---|---------|----|----|----------|-------|---------------|
| F01 | STD (raw eBUS serial) | M | M | M | P | P-PARITY (byte-stream vs ENH reference) |
| F02 | ENH framing | M | M | M | M | P-PARITY (harness V01-V12) |
| F03 | ENS framing | M | M | M | M | P-PARITY (baud-only difference validated) |
| F04 | Unsolicited RESETTED | M | M | M | M | P-PARITY (reset then RESETTED verified) |
| F05 | INFO set (0x00-0x07) | M | M | M | M | P-PARITY (all IDs, all lengths) |
| F06 | Byte-stream parity | M | M | M | M | P-PARITY (continuous RX matches reference) |
| F07 | Direct USB transport | M | M | M (CP2102) | X | P-PARITY over USB |
| F08 | UART-header transport | M | M | M (RPi) | X | P-PARITY over UART |
| F09 | TCP transport (ENH) | M (Wi-Fi) | M (Wi-Fi) | ? (module) | M | P-PARITY over TCP + P-RESOURCE |
| F10 | UDP-PLAIN | P | P | X | P | P-PARITY + P-RESOURCE |
| F11 | Single-client mode | M | M | M | M | P-SOAK |
| F12 | Bounded multi-client | P | P | X | P | P-MEMORY + P-TIMING + P-FAIRNESS + P-SOAK |
| F13 | Wire-log observability | S | S | P | P | P-MEMORY + P-NON-INTERFERENCE |
| F14 | Reset cause reporting | M | M | ? | M | P-PARITY (INFO 0x06) |
| F15 | Drop counters | M | M | M | M | P-RESOURCE (counter never overflows) |
| F16 | Arbitration stats | S | S | P | S | P-NON-INTERFERENCE |
| F17 | Local tinyebus readonly helpers | P | P | X | P | P-MEMORY + P-NON-INTERFERENCE + P-SOAK |
| F18 | Local tinyebus active query | P | P | X | X | All proofs |
| F19 | HTTP observability endpoint | P | P | X | P | P-MEMORY + P-NON-INTERFERENCE + P-SOAK |
| F20 | MQTT or nonessential network | X | X | X | X | Permanently out of scope |
| F21 | OTA firmware update | P | P | X (PIC Loader) | X (SWD) | P-MEMORY + P-NON-INTERFERENCE |
| F22 | Configuration persistence | S (NVS) | S (NVS) | ? | S (flash) | P-MEMORY |
| F23 | Legacy compatibility alias | N/A | N/A | N/A | S (port 5000) | P-PARITY (alias matches legacy byte format) |
| F24 | Mandatory observability counters | M | M | M | M | P-MEMORY (< 64B) |
| F25 | Optional observability counters | S | S | P | S | P-MEMORY + P-NON-INTERFERENCE |

### 4B. Proof Requirements Per Feature Class

| Feature class | Required proofs | Gate milestone |
|--------------|----------------|---------------|
| Protocol (F01-F06) | P-PARITY | M3 |
| Transport (F07-F10) | P-PARITY + P-RESOURCE | M3 (serial), M4 (network) |
| Session (F11-F12) | P-SOAK (single), all four (multi) | M4 (single), M5 (multi) |
| Observability (F13-F16, F24-F25) | P-MEMORY + P-NON-INTERFERENCE | M3 (mandatory), M5 (optional) |
| tinyebus augmentation (F17-F19) | P-MEMORY + P-NON-INTERFERENCE + P-SOAK | M8 |
| Infrastructure (F20-F23) | Per-feature | M9 |
