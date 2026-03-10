# Common Firmware Rewrite 03: Common Behavioural Contract + Test Taxonomy

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: Chunks 01-02. The behavioural contract defines what the test taxonomy validates. The feature eligibility matrix (Chunk 02) determines which tests apply per family. Proof classes (Chunk 01 Section 1C) are referenced throughout the taxonomy.

Scope: Common behavioural contract (transport surface matrix, ENH framing with test traceability, ENS semantics, STD raw serial parity, UDP-PLAIN) and the full test taxonomy (13 categories: SPEC, PARSE, XPORT, TIME, ARB, SESS, RES, SOAK, FAULT, RE, XFAM, OBS, release-gate).

Idempotence contract: Reapplying this chunk must not create duplicate test vectors, conflicting acceptance criteria, or ambiguous test-to-proof-class mappings.

Falsifiability gate: A review fails this chunk if any test category lacks explicit pass/fail criteria, if any harness vector lacks expected output, if the release-gate checklist has gaps relative to the taxonomy, or if any ENH invariant lacks a corresponding test reference.

Coverage: Section 5 (Common Behavioural Contract); Section 6 (Test Taxonomy).

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
