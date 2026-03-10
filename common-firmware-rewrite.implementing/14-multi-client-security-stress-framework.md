# Common Firmware Rewrite 05: Multi-Client + Security + Stress Matrix + Testing Framework

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: Chunks 01-04. Decision 5 (single-client default) and Decision 7 (no dynamic allocation) from Chunk 01 constrain multi-client policy. Per-family memory budgets from v1.0 HALs and Chunk 04 determine multi-client eligibility. The test taxonomy (Chunk 03) provides the test IDs referenced in the stress matrix. Proof classes (Chunk 01 Section 1C) gate every rule in the testing framework.

Scope: Multi-client policy (preserved from v1.0), security and safety constraints (preserved from v1.0), stress-test variant matrix (13 axes, variant ID scheme, coverage requirements), and testing-drives-feature-set decision framework (10 rules, proof chain per feature class).

Idempotence contract: Reapplying this chunk must not create conflicting multi-client policies, duplicate stress axes, or ambiguous testing-framework rules.

Falsifiability gate: A review fails this chunk if any stress axis lacks enumerated values, if the variant ID scheme is ambiguous, if any testing-framework rule lacks a concrete proof class reference, if coverage requirements are not quantified, or if the multi-client or security sections contradict their v1.0 originals.

Coverage: Section 9 (Multi-Client Policy); Section 10 (Security/Safety); Section 11 (Stress-Test Variant Matrix); Section 12 (Testing Drives Feature Set Framework).

---

## 9. Multi-Client Policy — PRESERVED

All content from v1.0 Section 6 (policy matrix, compute proof template, multi-client arbitration, session lifecycle, determinism constraint) is unchanged.

**Summary of preserved content:**

- **Policy matrix:** v5/C6 USB = single only; v5/C6 TCP = single default, configurable to N with proof; v3.x = single only (use proxy); ESERA TCP = single default, configurable to N with proof.
- **Compute proof template:** RAM proof (N × per_session_bytes + safety margin ≥ 10% total RAM), latency proof (N × dispatch_us + ISR_us < 417us), fairness proof (max_starve ≤ 2*N, round-robin).
- **Arbitration:** Serialised on bus, deterministic scheduling, queue capacity = N, full queue → ERROR_HOST.
- **Session lifecycle:** TCP connect → session, INIT → active, disconnect → destroyed + cancelled, idle timeout configurable (default 300s, 0=disabled).
- **Determinism:** Every queue compile-time fixed, every buffer compile-time fixed, overflow behaviour explicit, no unbounded memory growth, WCET-analysable.

---

## 10. Security and Safety — PRESERVED

All content from v1.0 Section 8 (bus safety, electrical safety, network safety, watchdog policy) is unchanged. Safety constraints are now validated by fault-injection tests (Section 6I).

**Summary of preserved content:**

- **Bus safety:** No TX without SEND/START. Stuck-TX watchdog ≤ 15ms. Crash/reset → TX high-impedance. Power-on → TX high-impedance until INIT.
- **Electrical safety:** Galvanic isolation or voltage limiting. GPIO within absolute maximum ratings. TX open-drain only.
- **Network safety:** TCP on configurable interface (default 0.0.0.0). No auth M0-M7. Debug endpoints not in production. OTA requires signature.
- **Watchdog:** Hardware watchdog ≤ 10s. Main task feeds every iteration. Hung → reset → unsolicited RESETTED. Timeout compile-time configurable (1s-30s).

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

**Protocol (F01-F06):** Hypothesis → SPEC test → PARSE test → XPORT test → P-PARITY harness → Lock.

**Transport (F07-F10):** Hypothesis → XPORT test → P-PARITY over transport → P-RESOURCE → Lock.

**Session (F11-F12):** Hypothesis → SESS test → P-SOAK (single) or full proof chain (multi) → Lock.

**Observability (F13-F16, F24-F25):** Hypothesis → P-MEMORY → OBS self-test → P-NON-INTERFERENCE → Lock.

**tinyebus augmentation (F17-F19):** Hypothesis → P-MEMORY → P-NON-INTERFERENCE → P-SOAK → Lock.
