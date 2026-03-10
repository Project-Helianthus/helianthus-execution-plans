# Common eBUS Adapter Firmware Rewrite — Testing-First Revision

Revision: `v2.0-testing-first`
Date: `2026-03-10`
Status: `Pre-adversarial (testing-first reframe from v1.0-initial; requires Codex xhigh convergence)`
Baseline: `v1.0-initial SHA256 f54db55bc64c2a894343515bc2e3aead5da6f92569ebe56809a7997d6369f63e`

---

## Summary

This plan defines a **common behavioural specification** for eBUS adapter firmware that produces identical externally-observable results across three hardware families, within each family's proven compute limits. The specification yields firmware images for:

- **v5 / C6:** ESP32-C3 (v5) and ESP32-C6 (C6) adapters, SDK: ESP-IDF, language: C.
- **v3.x (3.1 class):** PIC-based adapters with USB/RPi/Wi-Fi/Ethernet host variants.
- **ESERA legacy:** Ethernet couplers (WIZnet-derived, W7500P class).

**Testing-first revision key changes from v1.0-initial:**

| Aspect | v1.0-initial | v2.0-testing-first | Change class |
|--------|-------------|-------------------|-------------|
| Testing | Late validation (M6-M7) | Design input from T0 | **replaced** |
| tinyebus | Optional M8 augmentation | Common behavioural basis | **replaced** |
| Feature decisions | Generic MUST/MAY | Per-family eligibility matrix with proof gates | **replaced** |
| Observability | Mentioned in passing | Deterministic contract from day zero | **replaced** |
| C6 extras | Same as v5 (pre-decided) | Behind family-specific proof gates | **tightened** |
| Milestones | M0-M9 linear | T0 + M0-M9 with test-before-code enforcement | **replaced** |
| Behavioural contract | Preserved | Preserved + test traceability | **tightened** |
| Per-family HALs | Preserved | Preserved + tinyebus tier annotation | **tightened** |
| Multi-client policy | Preserved | Preserved | **preserved** |
| Security/safety | Preserved | Preserved | **preserved** |
| Doc-gate | 15 entries | 30+ entries (testing docs added) | **expanded** |

The plan separates a **common behavioural contract** — defined by tinyebus-derived protocol oracles and test vectors — from **per-family hardware adaptation layers**. All firmware images MUST pass the same ENH/ENS compatibility harness and integrate with the Helianthus T01..T88 topology runner as the acceptance artefact.

---

## 1. Testing-First Philosophy and Scope Derivation

### 1A. Core Principle

**No feature exists until a test defines it; no implementation starts until the test scaffolding for it exists.**

Every firmware feature begins as a hypothesis:
- "This MCU can achieve SYN-to-TX latency < 50us" is a hypothesis until an oscilloscope measurement proves it.
- "This family can support 2 concurrent ENH sessions" is a hypothesis until a RAM proof + latency proof + fairness proof + soak proof pass.
- "tinyebus shared logic fits in PIC RAM" is a hypothesis until a compile-time memory map proves it.

Hypotheses become one of:
- **mandatory** — test defines it, proof confirms it, lock commits it.
- **optional-if-proven** — test defines it, proof is pending, implementation is gated.
- **forbidden-until-proven** — hypothesis has plausible failure mode, test defines the disproof condition, implementation is blocked.
- **permanently out-of-scope** — hypothesis is disproven or the feature violates a safety/determinism invariant for the family.

### 1B. Scope Derivation from Tests

The feature set for each hardware family is *derived* from its test results, not assumed:

1. Hardware characterisation tests (M0) determine what the MCU *can* do.
2. Protocol specification tests (T0/M1) determine what the firmware *must* do.
3. The intersection — filtered through determinism and safety constraints — determines what the firmware *will* do on that family.
4. Anything outside the intersection is either optional-if-proven (with a proof gate) or out-of-scope.

### 1C. Proof Classes

| Class | What it proves | Method | When required |
|-------|---------------|--------|---------------|
| P-TIMING | ISR latency, arbitration timing, SYN-to-TX | Oscilloscope / logic analyser on HIL rig | Before any arbitration code is locked (M2) |
| P-MEMORY | Static allocation fits, no dynamic paths, stack budgets | Compile-time linker map + static analysis | Before any implementation starts (M2) |
| P-PARITY | Byte-for-byte match with reference firmware | Compatibility harness (DUT vs reference capture) | Before any protocol feature is locked (M3) |
| P-RESOURCE | Queue capacities, ring overflow, bounded counters | Compile-time analysis + soak test | Before multi-client or observability features (M5) |
| P-FAIRNESS | Multi-client arbitration, bounded starvation | Statistical test over N rounds | Before multi-client is enabled (M5) |
| P-NON-INTERFERENCE | Feature X does not degrade timing path Y | Before+after timing measurement with feature enabled | Before any optional feature (M5+) |
| P-DETERMINISM | No unbounded growth, no hidden allocation, WCET bounded | Static analysis + 72h soak | Before release (M7) |
| P-SOAK | Long-run stability under traffic | 72h continuous operation | Before release (M7) |

### 1D. Lock Criteria

A feature or decision is LOCKED when:
1. The relevant proof class has been executed and passed.
2. An adversarial review has attempted to invalidate the proof.
3. The proof artefact is machine-checkable or has a reproducible measurement procedure.
4. The lock is recorded in the feature eligibility matrix with a proof reference.

### 1E. De-Scope Criteria

A feature is DE-SCOPED for a family when any of:
1. P-MEMORY proof shows it cannot fit.
2. P-TIMING proof shows it degrades arbitration below eBUS timing requirements.
3. P-NON-INTERFERENCE proof shows it interferes with a mandatory feature.
4. Hardware RE (M0) reveals the MCU cannot support the feature's prerequisites.
5. 72h soak shows non-deterministic behaviour with the feature enabled.

De-scoping is permanent for a given hardware revision. Re-scoping requires a new proof chain.

### 1F. Required Instrumentation Before Code Starts

Before any family's M2 (skeleton) begins, the following MUST exist:

| Instrument | Purpose | Deliverable |
|-----------|---------|-------------|
| HIL rig spec | Physical test setup for the family | `firmware/hil-rig-spec.md` |
| Timing measurement GPIO | Oscilloscope-observable test point | Pin identified in HAL doc |
| Reference capture set | ebusd-esp ENH captures for harness | Recorded binary files |
| Harness stub | Stimulus generator + comparator skeleton | Compiling code in test repo |
| Memory analysis toolchain | Linker map parser, stack analyser | Script or tool documented |
| Observability counter struct | Static memory layout for mandatory counters | Header/source file |

---

## 2. Adversarially Locked Decisions

### Decision 1: tinyebus as Common Behavioural Basis — REPLACED

**Replaces v1.0 Decision 1 (ESP-IDF C only) and v1.0 Section 7 (tinyebus optional augmentation).**

**Lock:** tinyebus is the common behavioural basis for all implementations. This means:

- tinyebus-defined protocol state machines (STD, ENH, ENS) are the **specification oracle**.
- tinyebus-defined observability primitives (counters, event markers) are the **minimum contract**.
- tinyebus Go test vectors are the **compliance reference**.
- Per-family implementations MUST match tinyebus-defined behaviour but MAY use family-specific code.

**This does NOT mean:**
- tinyebus Go code runs on firmware targets (it does not — firmware is C, PIC ASM, or ARM C).
- All families share a single codebase (they do not — each family has its own HAL and build).
- tinyebus runtime features (TCP server, query API) are mandatory (they are not — they are gated per family).

**Per-family tinyebus tier — see Section 3 for full adjudication:**
- v5/C6: Tier B (shared logic layer via C port) + Tier C optional-if-proven (runtime augmentation)
- v3.x PIC: Tier A (spec/oracle only — too resource-constrained for shared library)
- ESERA: Tier B (shared logic layer via C port) + Tier C conditional (runtime augmentation)

**Failure modes survived:**
- "tinyebus Go code can't run on MCUs" — Correct. The Go code is the *oracle*. Firmware is C. Behavioural parity is proven by the compatibility harness, not by code sharing.
- "Porting tinyebus to C creates drift" — Drift is detected by the compatibility harness (P-PARITY proofs). The Go oracle and the C implementation must produce identical outputs for identical inputs.
- "tinyebus emulation framework is not a protocol implementation" — Correct. The emulation framework (VR90, VR_71 targets) tests *device emulation*, not *adapter firmware*. The adapter firmware spec is derived from tinyebus bus/hal interfaces and the ENH protocol docs.

### Decision 2: Language/SDK Per Family — SPLIT from v1.0 Decision 1

**Lock:**
- v5/C6: C using ESP-IDF. **(preserved)**
- v3.x PIC: C or PIC ASM, toolchain determined by M0 RE. **(preserved)**
- ESERA W7500P: C using ARM GCC + W7500P SDK. **(preserved)**

**Rationale:** Each family requires ISR-level control for eBUS arbitration timing. No garbage-collected or interpreted language is acceptable on any firmware target.

### Decision 3: PIC RE before M2 — PRESERVED

**Lock:** v3.x implementation MUST NOT begin coding (M2) until M0 produces: (a) exact PIC part number, (b) exact pinout schematic, (c) exact timer peripheral mapping for arbitration, (d) bootloader entry protocol for ebus PIC Loader.

### Decision 4: ESERA clean-room replacement — PRESERVED

**Lock:** ESERA coupler firmware MUST be a clean-room replacement, NOT a modification of existing proprietary firmware.

### Decision 5: Single-client default, multi-client only with compute proof — PRESERVED

**Lock:** All families MUST default to single-client mode. Multi-client MUST NOT be enabled without per-family P-MEMORY + P-TIMING + P-FAIRNESS + P-SOAK proofs.

### Decision 6: ENH canonical, STD and ENS derive from it — TIGHTENED

**Lock:** ENH framing (helianthus-docs-ebus/protocols/enh.md) is the canonical protocol. ENS differs only by serial baud. STD (raw eBUS serial) is the unframed baseline. All compliance testing uses ENH as primary reference, with STD and ENS parity validated separately.

**Tightening from v1.0:** STD (raw serial) is now explicitly tested for parity, not just "MAY be offered." On families where STD is supported, it MUST pass byte-stream parity tests against ENH-derived reference captures.

### Decision 7: No dynamic memory allocation — PRESERVED

**Lock:** All firmware MUST use only static allocation. No `malloc`/`free`/`heap_caps_malloc` in application code.

### Decision 8: Port 9999 default — PRESERVED

**Lock:** TCP ENH default port MUST be 9999.

### Decision 9: Testing gates implementation — NEW

**Lock:** No implementation milestone (M2+) may begin for any family until:
1. The test harness stubs for that milestone's deliverables exist and compile.
2. The required measurement hooks (GPIO test points, memory analysis toolchain) are documented.
3. The feature eligibility matrix entry for every feature in that milestone shows either "mandatory" with proof class identified, or "gated" with experiment defined.

**Failure modes survived:**
- "This slows down development" — It prevents rework. A timing proof failure at M7 that invalidates an M3 design choice costs more than front-loading the measurement infrastructure.
- "Harness stubs are busy-work" — Harness stubs define the *acceptance contract* for the implementation. Writing the stub first forces the developer to understand what "done" means before writing code.

### Decision 10: Observability from day zero — NEW

**Lock:** Every firmware image MUST implement the mandatory observability counters (Section 7A) from the first functional milestone (M3). Observability is not a late-phase add-on; it is a design input that constrains memory budget and timing budget from the start.

**Failure modes survived:**
- "Observability steals arbitration budget" — The timing impact budget (Section 7F) limits observability overhead to < 5us per event, which is < 1.2% of one eBUS bit-time. This is enforced by P-NON-INTERFERENCE proofs.
- "Counters waste RAM on PIC" — The mandatory counter set requires < 64 bytes (Section 7G). Even PIC18 with 2KB RAM can afford this.

### Decision 11: C6 extras behind proof gates — NEW

**Lock:** ESP32-C6 MUST NOT receive any capability beyond the v5 baseline unless a family-specific proof chain demonstrates:
1. P-MEMORY: the extra feature fits within C6 memory budget after all baseline features.
2. P-TIMING: the extra feature does not degrade arbitration latency.
3. P-NON-INTERFERENCE: the extra feature does not interfere with baseline operation.
4. P-SOAK: 72h soak with the extra feature enabled shows no regression.

C6 extras that are candidates (but NOT pre-decided):
- Wi-Fi 6 specific optimisations
- BLE 5.3 commissioning interface
- Additional concurrent TCP sessions beyond v5 baseline
- Richer tinyebus runtime augmentation (wire-log, query API)

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

---

## 5. Common Behavioural Contract

**Status: PRESERVED from v1.0 with test traceability added.** Every subsection now references the test vector or proof class that validates it.

### 5A. Transport Surface Matrix

| Surface | Protocol | Direction | Required | Families | Validated by |
|---------|----------|-----------|----------|----------|-------------|
| USB serial (CDC ACM / USB-UART) | ENH or ENS | Bidirectional | M (where USB exists) | v5/C6, v3.x | P-PARITY over USB |
| UART-on-header (GPIO) | ENH or ENS | Bidirectional | M (where header exists) | v5/C6, v3.x RPi | P-PARITY over UART |
| TCP (port 9999 default) | ENH | Bidirectional | M (where IP exists) | v5/C6, v3.x module, ESERA | P-PARITY over TCP |
| Raw serial (STD) | Raw eBUS bytes | Bidirectional | M (where serial exists) | v5/C6, v3.x | P-PARITY byte-stream |
| UDP-PLAIN | Raw eBUS bytes | Bidirectional | P | v5/C6, ESERA | P-PARITY + P-RESOURCE |

### 5B. ENH Framing Contract

**Status: PRESERVED in full from v1.0 Section 2B.** All subsections (encoding, command IDs, INIT/RESETTED, SEND, START/STARTED/FAILED, INFO, errors, received byte streaming) are unchanged. Refer to v1.0 Section 2B for complete specification.

Key invariants retained verbatim:
- Encoding: `byte1 & 0xC0 == 0xC0`, `byte2 & 0xC0 == 0x80`. Violation triggers ERROR_HOST.
- INIT triggers RESETTED within 100ms. Hardware reset triggers unsolicited RESETTED.
- Parser reset after STARTED and FAILED.
- Arbitration: SYN-to-TX within one bit-time (~417us).
- INFO serialised: concurrent INFO triggers ERROR_HOST. Timeout 500ms triggers ERROR_EBUS.
- RX streaming: all bus bytes forwarded, SYN included, overflow triggers drop + counter.

**Test traceability added:**

| Invariant | Harness vector | Proof class |
|-----------|---------------|-------------|
| INIT then RESETTED | V01 | P-PARITY |
| INFO 0x00-0x07 | V02 | P-PARITY |
| Unknown INFO yields length 0 | V03 | P-PARITY |
| START then STARTED | V04 | P-PARITY + P-TIMING |
| START then FAILED | V05 | P-PARITY |
| START 0xAA cancel | V06 | P-PARITY |
| SEND during transaction | V07 | P-PARITY |
| SEND outside transaction | V08 | P-PARITY |
| Parser reset after arb | V09 | P-PARITY |
| Rapid INIT cycle | V10 | P-SOAK |
| INFO during INFO | V11 | P-PARITY |
| Framing error | V12 | P-PARITY |
| SYN-to-TX timing | T-ARB-01 | P-TIMING |
| RX drop counter | OBS-01 | P-RESOURCE |

### 5C. ENS Semantics — PRESERVED

ENS = ENH with 115200 baud serial (vs 9600). Over TCP/UDP: identical. Both transmit source byte during START. Host MUST NOT include source byte for either.

### 5D. STD (Raw Serial) Semantics — TIGHTENED

**v1.0 called this "optional." v2.0 makes it mandatory where serial exists, with parity testing.**

STD carries unframed eBUS bytes. No INIT/RESETTED, no START/STARTED/FAILED, no INFO. The host handles all framing, CRC, and arbitration timing.

**Parity requirement (new):** When STD is offered on a transport, the raw byte stream MUST be bit-for-bit identical to the RECEIVED byte stream in ENH mode. Specifically: if the adapter is receiving eBUS bytes and forwarding them via both ENH (as RECEIVED frames) and STD (as raw bytes) simultaneously, the extracted data bytes MUST match.

**Validated by:** P-PARITY byte-stream comparison (harness captures ENH RECEIVED stream and STD stream simultaneously, extracts data bytes, diffs).

### 5E. UDP-PLAIN — PRESERVED

Multi-client correctness MUST be above the adapter unless firmware implements explicit arbitration owner layer.

---

## 6. Test Taxonomy

### 6A. Specification Tests

**Purpose:** Verify that the firmware implements the protocol specification correctly, independent of hardware.

| Test ID | Description | Input | Expected output | Tool |
|---------|-------------|-------|----------------|------|
| SPEC-ENH-ENCODE-* | ENH encoding for all 256 data values x all command IDs | Data byte + command | Encoded 2-byte pair | Unit test (C or Go) |
| SPEC-ENH-DECODE-* | ENH decoding for all valid encoded pairs | Encoded pair | Data byte + command | Unit test |
| SPEC-ENH-DECODE-INVALID | Decoding of all invalid encoded pairs | Invalid pair | Error / ERROR_HOST | Unit test |
| SPEC-INFO-LEN-* | INFO response length for each ID (0x00-0x07) | INFO request | Correct length + payload | Unit test |
| SPEC-LIFECYCLE-* | INIT/RESETTED state machine transitions | State + event | Next state + output | Unit test |
| SPEC-ARB-SM-* | Arbitration state machine (idle/waiting/won/lost) | State + bus event | Next state + output | Unit test |

**Execution:** These tests run against the tinyebus Go oracle AND the C firmware port. Both MUST produce identical results.

### 6B. Framing / Protocol Parser Tests

| Test ID | Description |
|---------|-------------|
| PARSE-VALID-SHORT | All valid short-form bytes (0x00-0x7F) |
| PARSE-VALID-ENCODED | All valid encoded pairs |
| PARSE-INVALID-BYTE2 | byte1 valid (0xC0+), byte2 invalid (not 0x80-0xBF) |
| PARSE-TRUNCATED | byte1 without byte2 (stream ends mid-pair) |
| PARSE-RESYNC | Invalid pair followed by valid pair (parser must resync) |
| PARSE-RESET-AFTER-ARB | Parser state after STARTED/FAILED must be clean |
| PARSE-INTERLEAVED | Short-form bytes interleaved with encoded pairs |
| PARSE-TCP-FRAG | Encoded pair split across TCP segments |
| PARSE-TCP-COALESCE | Multiple frames coalesced in one TCP segment |

### 6C. Transport Tests

| Test ID | Transport | Validates |
|---------|-----------|----------|
| XPORT-USB-ENH | USB CDC ACM | ENH round-trip over USB |
| XPORT-USB-ENS | USB CDC ACM | ENS round-trip over USB |
| XPORT-UART-ENH | GPIO UART | ENH round-trip over UART |
| XPORT-UART-ENS | GPIO UART | ENS round-trip over UART |
| XPORT-TCP-ENH | Wi-Fi/Eth TCP | ENH round-trip over TCP |
| XPORT-UDP-PLAIN | Wi-Fi/Eth UDP | Raw byte round-trip over UDP |
| XPORT-STD-SERIAL | Raw serial | Byte-stream parity vs ENH RECEIVED |

### 6D. Timing Tests

| Test ID | Measurement | Method | Acceptance |
|---------|------------|--------|------------|
| TIME-SYN-TO-TX | SYN detection to TX start | Oscilloscope on GPIO test point | < 50us (v5/C6), < 200us (PIC), < 100us (ESERA) |
| TIME-ISR-LATENCY | UART RX ISR entry latency | Logic analyser: RX pin edge to ISR toggle | < 10us (v5/C6), < 5us (ESERA) |
| TIME-ARB-TOTAL | Full arbitration cycle | START command to STARTED/FAILED response | < 2ms |
| TIME-INIT-RESETTED | INIT to RESETTED latency | Protocol capture | < 100ms |
| TIME-INFO-COMPLETE | INFO request to final response byte | Protocol capture | < 500ms |
| TIME-OBS-OVERHEAD | Observability counter increment cost | Before/after GPIO toggle around counter update | < 5us |

### 6E. Arbitration Tests

| Test ID | Scenario | Expected |
|---------|----------|----------|
| ARB-WIN-CLEAN | Solo initiator, bus idle | STARTED with correct address |
| ARB-LOSE-HIGHER | Two initiators, DUT has higher address | FAILED with winner address |
| ARB-LOSE-LOWER | Two initiators, DUT has lower address | STARTED (DUT wins) |
| ARB-CANCEL | START 0xAA during pending arbitration | Return to idle, no STARTED/FAILED |
| ARB-NO-SYN | Bus stuck (no SYN within 200ms) | ERROR_EBUS 0x01 |
| ARB-RAPID | 100 START requests in 10 seconds | All produce STARTED or FAILED, no stuck state |
| ARB-PARSER-RESET | Verify parser clean after each arbitration | No corruption in subsequent commands |

### 6F. Concurrency / Session Tests

| Test ID | Scenario | Expected |
|---------|----------|----------|
| SESS-CONNECT-DISCONNECT | TCP connect then INIT then traffic then disconnect | Clean teardown, resources freed |
| SESS-IDLE-TIMEOUT | No traffic for timeout period | Session destroyed |
| SESS-RECONNECT-STORM | 1000 connect/disconnect in 60s | No leak (session count, fd count) |
| SESS-MULTI-FAIR | N clients, 1000 arbitration rounds | Each within 10% of 1000/N |
| SESS-MULTI-STARVE | N clients, one heavy | No client starved > 2*N rounds |
| SESS-MULTI-OVERFLOW | Queue full, new START | ERROR_HOST |

### 6G. Resource-Bound Proofs

| Proof ID | What | Method |
|----------|------|--------|
| RES-LINKER-MAP | All allocations are static | Parse linker map, reject any .bss/.data growth across commits |
| RES-STACK-BUDGET | Stack depth per task/ISR | Static analysis or call-graph analyser |
| RES-QUEUE-CAP | All queues have compile-time fixed capacity | Code review + grep for malloc/calloc/realloc |
| RES-RING-OVERFLOW | Ring buffer overflow is drop-oldest + counter | Unit test: fill ring, write one more, verify drop count |
| RES-COUNTER-BOUND | Counters use wrapping arithmetic | Code review: all counters are uint32 with wrapping |
| RES-SESSION-MAX | Maximum session count is compile-time constant | Code review + multi-client test at max+1 sessions |

### 6H. Soak / Stress Tests

| Test ID | Duration | Traffic | Acceptance |
|---------|----------|---------|------------|
| SOAK-72H | 72 hours | Mixed INIT/INFO/START/SEND | No timeout, no ERROR_EBUS, no watchdog reset, memory stable |
| SOAK-168H | 168 hours | Light traffic + periodic INFO | Same as 72h (optional, for release candidates) |
| STRESS-RECONNECT-10K | ~10 min | 10000 TCP connect/disconnect | Zero leak |
| STRESS-ARB-STORM | 1 hour | Continuous START at maximum rate | Fair distribution, no stuck state |
| STRESS-MIXED | 24 hours | Random mix of all command types | No error, counters consistent |
| STRESS-MULTI-SOAK | 72 hours | N clients, mixed traffic | Fairness maintained, no session leak |

### 6I. Fault-Injection Tests

| Test ID | Fault | Expected |
|---------|-------|----------|
| FAULT-RX-DISCONNECT | Disconnect eBUS RX mid-transaction | Timeout < 200ms, ERROR_EBUS, return to idle |
| FAULT-TX-SHORT | Short TX to ground momentarily | Stuck-TX watchdog < 15ms, bus released |
| FAULT-BUS-NOISE | Inject random bytes on bus | Parser handles gracefully, no crash |
| FAULT-POWER-BROWNOUT | Supply voltage dip | Watchdog reset then unsolicited RESETTED |
| FAULT-POWER-CYCLE | Full power off/on | Clean boot then RESETTED on INIT |
| FAULT-ETH-LINKFLAP | Ethernet link down/up (ESERA) | TCP sessions close cleanly, reconnect works |
| FAULT-WIFI-DEGRADE | Wi-Fi signal degradation (v5/C6) | TCP may timeout, no firmware crash |
| FAULT-USB-DISCONNECT | USB cable removed (v5/C6, v3.x) | Session cleanup, no crash |
| FAULT-HOST-INVALID-ENH | Invalid encoded byte pairs | ERROR_HOST, parser resyncs |
| FAULT-HOST-INFO-INTERLEAVE | INFO request during active INFO | ERROR_HOST |
| FAULT-HOST-START-STORM | 1000 START requests with no SYN | All produce ERROR_EBUS (bus timeout), no stuck |
| FAULT-HOST-OVERSIZED | > 256 SEND bytes without SYN | Adapter handles gracefully |
| FAULT-HOST-PARTIAL-CMD | TCP disconnect mid-encoded-pair | Parser reset on disconnect, no state leak |
| FAULT-HOST-FUZZ | 24h random byte sequences to ENH transport | No crash, no stuck state, parser always resyncs |

### 6J. Reverse-Engineering Characterisation Tests

| Test ID | Target | Measures |
|---------|--------|----------|
| RE-PIC-PARTID | v3.x PIC | Device ID via ICSP |
| RE-PIC-TIMER | v3.x PIC | Timer resolution and ISR latency |
| RE-PIC-RAM | v3.x PIC | Available RAM after bootloader reservation |
| RE-ESERA-MCU | ESERA | Chip ID via SWD |
| RE-ESERA-PHY | ESERA | eBUS PHY circuit trace (NAND-gate logic) |
| RE-ESERA-FLASH | ESERA | Flash layout dump |
| RE-ESERA-PROTO | ESERA | Existing protocol packet capture |
| RE-V5-PINS | v5 | PCB trace confirming GPIO7/GPIO10 |
| RE-C6-PINS | C6 | PCB trace confirming GPIO14/GPIO15 |
| RE-PHY-THRESHOLD | All | eBUS comparator threshold measurement |
| RE-PHY-INVERSION | All | Bus polarity vs UART polarity validation |

### 6K. Cross-Family Parity Tests

| Test ID | Comparison | Method |
|---------|-----------|--------|
| XFAM-ENH-PARITY | v5 vs C6 vs ESERA (vs v3.x where applicable) | Same stimulus same response (byte-level diff) |
| XFAM-INFO-PARITY | All families | INFO 0x00-0x07 response format identical (except family-specific content) |
| XFAM-ARB-PARITY | All families | Same arbitration scenario same STARTED/FAILED sequence |
| XFAM-ERROR-PARITY | All families | Same fault condition same error code |
| XFAM-STREAM-PARITY | All families | Same bus traffic same RECEIVED byte sequence |

### 6L. Observability Self-Tests

| Test ID | Counter | Validation |
|---------|---------|-----------|
| OBS-RX-COUNT | rx_bytes | Count bytes received in harness, compare to counter |
| OBS-TX-COUNT | tx_bytes | Count bytes sent in harness, compare to counter |
| OBS-DROP-COUNT | rx_drops | Force overflow, compare drop count to expected |
| OBS-ARB-COUNT | arb_started + arb_failed | Count arbitration outcomes in harness, compare |
| OBS-ERR-COUNT | errors_ebus + errors_host | Inject known faults, compare to counter |
| OBS-RESET-COUNT | resets | Trigger known number of resets, compare |
| OBS-MONOTONIC | All counters | Verify counters never decrease (wrapping uint32 is OK) |
| OBS-WIRELOG-BOUND | Wire-log ring (if present) | Fill ring beyond capacity, verify oldest dropped, size stable |
| OBS-WIRELOG-NONINTERFERENCE | Wire-log ring (if present) | TIME-OBS-OVERHEAD with wire-log enabled vs disabled |

### 6M. Release-Gate Tests

A release candidate PASSES only if ALL of the following are green:
1. All SPEC-* tests pass.
2. All PARSE-* tests pass.
3. All XPORT-* tests pass for the family's supported transports.
4. P-PARITY harness vectors V01-V12 pass.
5. T01-T04 topology runner pass (direct adapter).
6. T09-T24 pass (proxy single-client, if TCP supported).
7. T25-T88 pass (proxy dual-client, if multi-client enabled).
8. SOAK-72H pass.
9. All FAULT-* tests pass.
10. All OBS-* self-tests pass.
11. RES-LINKER-MAP confirms no dynamic allocation.
12. RES-STACK-BUDGET is within 80% of available stack.
13. All XFAM-* parity tests pass.

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

---

## 9. Multi-Client Policy — PRESERVED

All content from v1.0 Section 6 (policy matrix, compute proof template, multi-client arbitration, session lifecycle, determinism constraint) is unchanged.

---

## 10. Security and Safety — PRESERVED

All content from v1.0 Section 8 (bus safety, electrical safety, network safety, watchdog policy) is unchanged. Safety constraints are now validated by fault-injection tests (Section 6I).

---

## 11. Stress-Test Variant Matrix

### 11A. Axes

| Axis | Symbol | Values |
|------|--------|--------|
| Hardware family | `F` | v5, c6, v3x-usb, v3x-uart, v3x-wifi, v3x-eth, esera |
| Transport mode | `X` | usb-enh, usb-ens, uart-enh, uart-ens, tcp-enh, udp-plain, std-serial |
| Protocol mode | `P` | std, enh, ens |
| Session topology | `S` | single, proxy-single, proxy-dual, multi-direct-2, multi-direct-4 |
| Traffic profile | `T` | idle, light, moderate, heavy, burst, arb-storm, info-flood |
| Bus condition | `B` | normal, noisy, rx-disconnect, tx-short, intermittent, no-syn |
| Power condition | `W` | nominal, brownout, power-cycle, hot-reconnect |
| Network condition | `N` | nominal, latency-50ms, loss-1pct, link-flap, na |
| Lifecycle | `L` | fresh, 1h, 24h, 72h, 168h |
| Observability mode | `O` | off, counters-only, wirelog, full |
| tinyebus mode | `Y` | oracle-only, shared-lib, augmented, na |
| Duration profile | `D` | short-1m, medium-1h, long-24h, soak-72h, soak-168h |
| Instrumentation | `I` | minimal, hooks, full-debug |

### 11B. Variant ID Scheme

Format: `{F}-{X}-{P}-{S}-{T}-{B}-{W}-{N}-{L}-{O}-{Y}-{D}-{I}`

Examples:
- `v5-tcp_enh-enh-single-heavy-normal-nominal-nominal-72h-counters-sharedlib-soak72h-hooks`
- `esera-tcp_enh-enh-proxy_dual-arb_storm-normal-nominal-link_flap-24h-full-sharedlib-long24h-hooks`
- `v3x_usb-usb_enh-enh-single-moderate-normal-nominal-na-1h-counters-oracle-medium1h-minimal`

### 11C. Coverage Requirements

Full cross-product is infeasible (~10^7 combinations). Coverage-guided selection:

**Mandatory (every release candidate):**
1. One SOAK-72H per family on primary transport.
2. Transport sweep: all supported transports per family, 1h each.
3. Multi-client fairness: v5 + ESERA, proxy-dual, arb-storm, 1h.
4. Fault injection sweep: all families, each fault condition, 1m each.

**Optional (hardening):**
5. C6 max stress: multi-direct-4, heavy, 168h, full obs, augmented.
6. ESERA network stress: multi-direct-2, link-flap, 24h.

---

## 12. Testing Drives Feature Set — Decision Framework

### 12A. Rules

| Rule | Statement |
|------|-----------|
| R01 | No feature without acceptance artefact |
| R02 | No protocol feature without P-PARITY harness vector |
| R03 | No timing-critical feature without P-TIMING measurement |
| R04 | No multi-client without P-MEMORY + P-FAIRNESS + P-SOAK |
| R05 | No tinyebus runtime component without P-NON-INTERFERENCE |
| R06 | No observability endpoint without P-MEMORY proof |
| R07 | No protocol alias without P-PARITY byte-level test |
| R08 | No optional feature on weak MCU without P-MEMORY + P-TIMING |
| R09 | No feature promotion from MAY to MUST without all proof classes passing |
| R10 | No C6 extra without Decision 11 proof chain |

### 12B. Proof Chain Per Feature Class

**Protocol (F01-F06):** Hypothesis then SPEC test then PARSE test then XPORT test then P-PARITY harness then Lock.

**Transport (F07-F10):** Hypothesis then XPORT test then P-PARITY over transport then P-RESOURCE then Lock.

**Session (F11-F12):** Hypothesis then SESS test then P-SOAK (single) or full proof chain (multi) then Lock.

**Observability (F13-F16, F24-F25):** Hypothesis then P-MEMORY then OBS self-test then P-NON-INTERFERENCE then Lock.

**tinyebus augmentation (F17-F19):** Hypothesis then P-MEMORY then P-NON-INTERFERENCE then P-SOAK then Lock.

---

## 13. Revised Milestone Plan

### T0: Testing-First Reframing (NEW)

**Duration: 1-2 weeks. No dependencies.**

**Deliverables:**

| ID | Deliverable | Blocks |
|----|------------|--------|
| T0-D01 | `firmware/testing-first-principles.md` | M0+ |
| T0-D02 | `firmware/feature-eligibility-matrix.md` (draft) | M1 |
| T0-D03 | `firmware/stress-variant-taxonomy.md` | M6 |
| T0-D04 | `firmware/observability-contract.md` | M3 |
| T0-D05 | `firmware/resource-proof-method.md` | M2 |
| T0-D06 | `firmware/non-interference-proof-template.md` | M5 |
| T0-D07 | Compatibility harness architecture document | M1 |
| T0-D08 | Test taxonomy document | M1 |

**Gate:** All documents exist and pass review. NO hardware work starts until T0 done.

### M0: Hardware Truth + Protocol Baseline + Instrumentation — TIGHTENED

**Duration: 2-4 weeks. Depends on T0.**

v1.0 deliverables PRESERVED (RE reports, protocol doc updates). Added:

| ID | Added deliverable |
|----|------------------|
| M0-D08 | Reference capture set (ebusd-esp ENH/ENS recordings) |
| M0-D09 | `firmware/hil-rig-spec.md` per available family |
| M0-D10 | RE characterisation test results (RE-* from 6J) |
| M0-D11 | `firmware/reverse-engineering-test-catalog.md` |
| M0-D12 | `firmware/family-capability-profile-v5-c6.md` (draft) |
| M0-D13 | `firmware/family-capability-profile-v3x.md` (draft) |
| M0-D14 | `firmware/family-capability-profile-esera.md` (draft) |

### M1: Adversarial Matrix + Harness + Eligibility — TIGHTENED

**Duration: 2-3 weeks. Depends on M0.**

v1.0 deliverables PRESERVED. Added:

| ID | Added deliverable |
|----|------------------|
| M1-D12 | Feature eligibility matrix finalised with M0 RE results |
| M1-D13 | `firmware/fault-injection-plan.md` |
| M1-D14 | Harness stub code (MUST compile) |
| M1-D15 | Adversarial matrix v1 with byte-level expected outputs |
| M1-D16 | SPEC-* tests running against Go oracle |
| M1-D17 | PARSE-* tests running against Go oracle |

### M2: Per-Family Proofs + Skeletons + Hooks — TIGHTENED

**Duration: 2-3 weeks per family. Depends on M1.**

v1.0 deliverables PRESERVED. Added:

| ID | Added deliverable |
|----|------------------|
| M2-D07 | P-MEMORY proof: linker map, no malloc |
| M2-D08 | P-TIMING proof: first ISR latency oscilloscope measurement |
| M2-D09 | Mandatory counter struct compiled into skeleton |
| M2-D10 | Timing measurement GPIO wired and tested |
| M2-D11 | Memory analysis toolchain documented |
| M2-D12 | tinyebus C library port if Tier B: ENH parser compiles on target |

### M3: ENH/ENS/STD Implementation — TIGHTENED

**Duration: 3-4 weeks per family. Depends on M2.**

v1.0 deliverables PRESERVED. Added: mandatory obs counters from M3, SPEC/PARSE tests against C firmware, STD parity test, OBS self-tests, P-TIMING oscilloscope evidence.

### M4: Network + Reconnect — PRESERVED + test-gated

Depends on M3. Added: SESS-RECONNECT-STORM and FAULT-*-LINKFLAP must pass.

### M5: Multi-Client — PRESERVED + proof-gated

Depends on M4. v3.x EXEMPT. Added: P-NON-INTERFERENCE proof.

### M6: Full Harness Integration — PRESERVED

Depends on M3 (all families).

### M7: Soak + Hardening — TIGHTENED

Depends on M6. Added: all FAULT-* pass, all OBS-* pass, XFAM-* parity pass, P-DETERMINISM proof, stress variant mandatory coverage pass.

### M8: tinyebus Augmentation — REPLACED (proof-gated)

Depends on M5 for eligible families. Each augmentation feature requires its own proof chain.

### M9: Release — PRESERVED

Depends on M7. Release-gate tests (Section 6M) are the formal exit criterion.

---

## 14. Mega Doc-Gate List

### 14A. Testing Foundation Docs (T0 gate — blocks M0+)

| Document | Assumed path | Milestone |
|----------|-------------|-----------|
| Testing-first principles | `firmware/testing-first-principles.md` | T0 |
| Feature eligibility matrix | `firmware/feature-eligibility-matrix.md` | T0 draft, M1 final |
| Stress variant taxonomy | `firmware/stress-variant-taxonomy.md` | T0 |
| Observability contract | `firmware/observability-contract.md` | T0 |
| Resource proof method | `firmware/resource-proof-method.md` | T0 |
| Non-interference proof template | `firmware/non-interference-proof-template.md` | T0 |
| Compatibility harness architecture | `firmware/enh-compatibility-harness.md` | T0 |
| Test taxonomy | `firmware/test-taxonomy.md` | T0 |

### 14B. Hardware and Protocol Docs (M0 gate — blocks M1)

| Document | Assumed path | Milestone |
|----------|-------------|-----------|
| ENH protocol (update) | `protocols/enh.md` | M0 |
| ENS protocol (update) | `protocols/ens.md` | M0 |
| UDP-PLAIN protocol (update) | `protocols/udp-plain.md` | M0 |
| HIL rig spec | `firmware/hil-rig-spec.md` | M0 |
| RE test catalog | `firmware/reverse-engineering-test-catalog.md` | M0 |
| M0 hardware RE report | `firmware/m0-hardware-re-report.md` | M0 |
| Family profile: v5/C6 | `firmware/family-capability-profile-v5-c6.md` | M0 draft, M1 final |
| Family profile: v3.x | `firmware/family-capability-profile-v3x.md` | M0 draft, M1 final |
| Family profile: ESERA | `firmware/family-capability-profile-esera.md` | M0 draft, M1 final |

### 14C. Contract and Policy Docs (M1 gate — blocks M2)

| Document | Assumed path | Milestone |
|----------|-------------|-----------|
| Common behavioural contract | `firmware/common-behavioural-contract.md` | M1 |
| HAL: v5/C6 | `firmware/hal-v5-c6.md` | M1 |
| HAL: v3.x | `firmware/hal-v3x.md` | M1 |
| HAL: ESERA | `firmware/hal-esera.md` | M1 |
| Multi-client policy | `firmware/multi-client-policy.md` | M1 |
| Security/safety | `firmware/security-safety.md` | M1 |
| Fault injection plan | `firmware/fault-injection-plan.md` | M1 |

### 14D. Implementation Docs (M2+ gates)

| Document | Repo (assumed) | Milestone |
|----------|---------------|-----------|
| Build instructions | per-family `docs/build.md` | M2 |
| Pinout reference | per-family `docs/pinout.md` | M2 |
| Memory map | per-family `docs/memory-map.md` | M2 |
| Topology runner integration | `helianthus-ebusgateway` docs | M6 |
| Adapter endpoint config | `helianthus-ebus-adapter-proxy` docs | M4 |
| CHANGELOG | per-family repo | M9 |

**Note:** All paths are assumptions. Repo structure MUST be confirmed before T0 lock.

**Total doc-gate entries: 30.**

---

## 15. Adversarial Self-Attack

### Attack 1: Overcommitting tinyebus on weak devices

**Risk:** Requiring tinyebus-derived behaviour on PIC with 2KB RAM may force cuts or introduce compliance gaps.

**Why plausible:** PIC RAM budget is estimated. If PIC16 with 512B RAM, even 48B counters is ~10% of memory.

**Evidence to defeat:** M0 RE (RE-PIC-PARTID + RE-PIC-RAM) showing actual RAM. If < 1KB, mandatory counter set must be reduced or PIC de-scoped from counter compliance.

**Gate:** Feature eligibility update after M0 RE.

### Attack 2: Confusing behavioural compatibility with shared code

**Risk:** "tinyebus as common base" interpreted as "must use C port" on PIC where hand-optimised ASM is better.

**Why plausible:** Plan uses both "shared logic layer" and "spec/oracle" language.

**Evidence to defeat:** Feature eligibility matrix explicitly states tinyebus tier per family. P-PARITY validates behaviour, not code.

**Gate:** M1 matrix must state: "Tier A compliance is proven by P-PARITY harness, not code inspection."

### Attack 3: Observability stealing arbitration budget

**Risk:** 12 counter increments per byte could add 12-24us on PIC at 4MHz.

**Why plausible:** PIC: 4-8 cycles per 32-bit increment = 1-2us each. 12 increments = 12-24us.

**Evidence to defeat:** TIME-OBS-OVERHEAD measurement on each family. If > 5us, counters deferred to non-ISR context.

**Gate:** M2 P-TIMING must include measurement with counters active.

### Attack 4: Multi-client specified too early for weak hardware

**Risk:** Multi-client MAY-IF-PROVEN for v5/C6/ESERA requires four proofs. May be dead weight.

**Why plausible:** Proof obligations are expensive. Adapter-proxy already provides multi-client.

**Evidence to defeat:** Multi-client is optional. M5 is not on critical path. Single-client + proxy is proven topology.

**Gate:** M5 explicitly optional. Release candidates may ship without M5.

### Attack 5: Assuming hardware parity without proving analogue differences

**Risk:** "Comparator + open-drain" assumed for all families. ESERA NAND-gate conditioning may differ.

**Why plausible:** ESERA uses signal conditioning not present on v5/C6.

**Evidence to defeat:** RE-ESERA-PHY and RE-PHY-THRESHOLD measurements.

**Gate:** M0 RE. ESERA PHY must be fully traced before M2.

### Attack 6: Protocol aliases silently diverging

**Risk:** ESERA port 5000 alias could have undocumented quirks.

**Why plausible:** Legacy format may not be fully RE'd.

**Evidence to defeat:** P-PARITY test for alias: recorded original traffic vs replacement.

**Gate:** F23 is SHOULD, not MUST. Alias only if P-PARITY passes.

### Attack 7: Under-specifying malformed input

**Risk:** Behavioural contract covers known error paths but not arbitrary malformed sequences.

**Why plausible:** Input space is infinite.

**Evidence to defeat:** FAULT-HOST-FUZZ: 24h random input, no crash.

**Gate:** FAULT-HOST-FUZZ added to M7 release-gate.

### Attack 8: Hidden runtime allocation in ESP-IDF lwIP

**Risk:** lwIP uses malloc internally for PCBs and segments.

**Why plausible:** lwIP default config uses dynamic allocation.

**Evidence to defeat:** ESP-IDF allows LWIP_MEMPOOL static pools. P-MEMORY must verify config.

**Gate:** M2 P-MEMORY must include lwIP config review.

### Attack 9: Test coverage mistaken for timing proof

**Risk:** P-PARITY validates bytes, not timing. Firmware could pass all P-PARITY tests with > 417us arb latency.

**Why plausible:** Software tests cannot prove real-time compliance.

**Evidence to defeat:** P-TIMING is separate from P-PARITY. TIME-SYN-TO-TX requires oscilloscope.

**Gate:** M3 gate requires oscilloscope evidence. P-PARITY alone is insufficient.

### Attack 10: Testing-first approach too heavyweight

**Risk:** T0 + 30 doc-gates + 8 proof classes before firmware code may paralyse project.

**Why plausible:** Firmware is often empirical.

**Evidence to defeat:** T0 delay is ~2 weeks. Prevented rework from M7 timing failure is 4-8 weeks. Net positive.

**Gate:** T0 timeboxed to 3 weeks. Escalate if exceeded.

---

## 16. Assumptions, Defaults, Out of Scope

### 16A. Assumptions — EXPANDED

| ID | Assumption | Invalidation trigger | Version |
|----|-----------|---------------------|---------|
| A1 | v5 pins: RX=GPIO7, TX=GPIO10 | PCB trace differs | v1.0 |
| A2 | C6 pins: RX=GPIO14, TX=GPIO15 | PCB trace differs | v1.0 |
| A3 | eBUS PHY: comparator + open-drain all families | Schematic differs | v1.0 |
| A4 | v3.x PIC has suitable hardware timer | Datasheet shows none | v1.0 |
| A5 | ESERA MCU is W7500P or derivative | Chip markings differ | v1.0 |
| A6 | W7500P SWD accessible on PCB | No SWD pads | v1.0 |
| A7 | ebusd-esp available as reference | Unavailable | v1.0 |
| A8 | Topology runner supports pluggable endpoints | Requires code changes | v1.0 |
| A9 | tinyebus Go oracle can generate C-portable test vectors | Go needs export format | v2.0 |
| A10 | ESP-IDF lwIP can use static pools | lwIP docs must confirm | v2.0 |
| A11 | Mandatory counters (48B) fit on smallest PIC | PIC RAM may be < 1KB | v2.0 |
| A12 | Doc paths in Section 14 match repo structure | Must confirm before lock | v2.0 |

### 16B. Defaults — PRESERVED

All defaults unchanged from v1.0.

### 16C. Out of Scope — PRESERVED + expanded

All v1.0 out-of-scope items unchanged. Added:
- MQTT or any nonessential network service (F20 = MUST-NOT).
- BLE commissioning (future plan, not firmware rewrite scope).
