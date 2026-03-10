# Common Firmware Rewrite 08: Adversarial Self-Attack + Assumptions/Defaults/Out of Scope

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: All prior chunks (01-07). Attacks reference tinyebus adjudication (Chunk 02), observability contract (Chunk 04), multi-client policy (Chunk 05), milestones (Chunk 06), and doc-gate (Chunk 07). Assumptions table covers hardware pins (Chunks 02-04), protocol references, and v2.0-specific additions (tinyebus Go oracle, lwIP static pools, counter budget).

Scope: Adversarial self-attack section (10 attacks on the plan itself with risk, plausibility, evidence to defeat, and gate criteria) and assumptions/defaults/out-of-scope tables (expanded from v1.0 with 4 new assumptions).

Idempotence contract: Reapplying this chunk must not create duplicate attacks, conflicting assumption IDs, or ambiguous out-of-scope boundary definitions.

Falsifiability gate: A review fails this chunk if any attack lacks a concrete gate criterion, if any assumption lacks an invalidation trigger, if any out-of-scope item overlaps with in-scope requirements, or if any attack references a section that does not exist in the canonical plan.

Coverage: Section 15 (Adversarial Self-Attack); Section 16 (Assumptions, Defaults, Out of Scope).

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

All defaults unchanged from v1.0:

| Parameter | Default | Configurable | Range |
|-----------|---------|-------------|-------|
| TCP ENH port | 9999 | Yes | 1024-65535 |
| ENH serial baud | 9600 | No | Fixed |
| ENS serial baud | 115200 | No | Fixed |
| Telemetry poll | 30s | Yes | 10s-300s |
| Idle timeout | 300s | Yes | 0-3600s |
| Arb delay | Per INFO 0x02 | Via INFO | 0-630us (10us steps) |
| Watchdog | 10s | Compile-time | 1s-30s |
| Max sessions | 1 | Compile-time | 1-8 |
| eBUS RX ring | 2048 bytes | Compile-time | 512-8192 |
| ENH TX buffer | 128 bytes | Compile-time | 64-512 |
| Wire-log ring | 64 entries | Compile-time | 16-256 |

### 16C. Out of Scope — PRESERVED + expanded

All v1.0 out-of-scope items unchanged:
- ebusd-esp firmware modification (this plan creates replacement firmware).
- eBUS protocol stack (framing, CRC, transactions) — handled by ebusgo.
- Home Assistant integration changes — firmware is transparent to HA.
- Matter bridge — future milestone.
- BLE transport — not an eBUS transport.
- Cloud connectivity — local network only.
- Custom PCB design — targets existing hardware.
- ebusd ASCII command protocol on adapter — ENH/ENS only.

Added:
- MQTT or any nonessential network service (F20 = MUST-NOT).
- BLE commissioning (future plan, not firmware rewrite scope).
