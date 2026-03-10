# Common Firmware Rewrite 06: Revised Milestones T0 + M0-M9

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: All prior chunks (01-05). T0 produces testing foundation docs that gate M0+. M0 resolves hardware unknowns from Chunks 02-04. M1 produces adversarial matrix and harness from Chunks 02-03. M2-M9 implement per-family firmware against contracts in Chunks 02-05 and test gates in Chunk 03. Decision 9 (testing gates implementation) from Chunk 01 enforces test-before-code at every milestone.

Scope: T0 (new testing-first reframing milestone) plus M0-M9 (tightened from v1.0 with additional deliverables enforcing testing-first philosophy, observability from day zero, and proof-gated feature progression).

Idempotence contract: Reapplying this chunk must not create duplicate milestone definitions, conflicting deliverable lists, or ambiguous gate criteria.

Falsifiability gate: A review fails this chunk if any milestone lacks explicit deliverables, if gate criteria are not falsifiable, if dependency ordering has cycles, if any new deliverable lacks an explicit blocking relationship, or if T0 timeboxing is not quantified.

Coverage: Section 13 (Revised Milestone Plan).

---

## T0: Testing-First Reframing (NEW)

**Duration: 1-2 weeks. No dependencies. Timeboxed: 3 weeks maximum (escalate if exceeded).**

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

**Fails review if:** Any document is missing, any document uses vague acceptance language, or T0 exceeds 3-week timebox without escalation.

---

## M0: Hardware Truth + Protocol Baseline + Instrumentation — TIGHTENED

**Duration: 2-4 weeks. Depends on T0.**

v1.0 M0 deliverables PRESERVED (M0-D01 through M0-D07: pin validation, RE reports, protocol doc updates, adversarial matrix v0). Added:

| ID | Added deliverable |
|----|------------------|
| M0-D08 | Reference capture set (ebusd-esp ENH/ENS recordings) |
| M0-D09 | `firmware/hil-rig-spec.md` per available family |
| M0-D10 | RE characterisation test results (RE-* from Section 6J) |
| M0-D11 | `firmware/reverse-engineering-test-catalog.md` |
| M0-D12 | `firmware/family-capability-profile-v5-c6.md` (draft) |
| M0-D13 | `firmware/family-capability-profile-v3x.md` (draft) |
| M0-D14 | `firmware/family-capability-profile-esera.md` (draft) |

**Gate:** v1.0 gate PRESERVED (all unknowns resolved with evidence, pin assignments confirmed) + RE characterisation tests executed + reference captures recorded + HIL rig spec per available family.

**Fails review if:** Any v1.0 gate criterion fails, any RE characterisation test not executed, reference captures missing, or HIL rig spec absent for any available family.

---

## M1: Adversarial Matrix + Harness + Eligibility — TIGHTENED

**Duration: 2-3 weeks. Depends on M0.**

v1.0 M1 deliverables PRESERVED (M1-D01 through M1-D11: contract docs, HAL docs, harness stubs, adversarial matrix). Added:

| ID | Added deliverable |
|----|------------------|
| M1-D12 | Feature eligibility matrix finalised with M0 RE results |
| M1-D13 | `firmware/fault-injection-plan.md` |
| M1-D14 | Harness stub code (MUST compile) |
| M1-D15 | Adversarial matrix v1 with byte-level expected outputs |
| M1-D16 | SPEC-* tests running against Go oracle |
| M1-D17 | PARSE-* tests running against Go oracle |

**Gate:** v1.0 gate PRESERVED (all docs exist, harness stubs compile, adversarial matrix covers Section 9A vectors) + feature eligibility matrix finalised + SPEC-* and PARSE-* tests running and passing against Go oracle.

**Fails review if:** Any v1.0 gate criterion fails, feature eligibility matrix has unresolved entries, harness stubs do not compile, or SPEC-*/PARSE-* tests not running.

---

## M2: Per-Family Proofs + Skeletons + Hooks — TIGHTENED

**Duration: 2-3 weeks per family. Depends on M1.**

v1.0 M2 deliverables PRESERVED (M2-D01 through M2-D06: build system, minimal UART/USB, LED blink, INFO 0x00, memory map, pinout). Added:

| ID | Added deliverable |
|----|------------------|
| M2-D07 | P-MEMORY proof: linker map, no malloc |
| M2-D08 | P-TIMING proof: first ISR latency oscilloscope measurement |
| M2-D09 | Mandatory counter struct compiled into skeleton |
| M2-D10 | Timing measurement GPIO wired and tested |
| M2-D11 | Memory analysis toolchain documented |
| M2-D12 | tinyebus C library port if Tier B: ENH parser compiles on target |

**Gate:** v1.0 gate PRESERVED (skeleton builds, flashes, boots, responds to INFO 0x00, memory map shows static allocations) + P-MEMORY proof document + P-TIMING first measurement + mandatory counters compiled into skeleton + timing GPIO functional.

**Fails review if:** Any v1.0 gate criterion fails, P-MEMORY proof shows dynamic allocation, ISR latency measurement not recorded, mandatory counter struct not compiled, or timing GPIO not functional.

---

## M3: ENH/ENS/STD Implementation — TIGHTENED

**Duration: 3-4 weeks per family. Depends on M2.**

v1.0 M3 deliverables PRESERVED (M3-D01 through M3-D08: complete ENH command set, INFO responses, arbitration, parser reset, errors, RECEIVED streaming, harness PASS, T01-T04 PASS). Added:

- Mandatory observability counters operational from M3 (Decision 10).
- SPEC-* and PARSE-* tests running against C firmware (not just Go oracle).
- STD parity test (where STD supported).
- OBS-* self-tests for mandatory counters.
- P-TIMING oscilloscope evidence (SYN-to-TX within family budget).

**Gate:** v1.0 gate PRESERVED (ENH harness V01-V12 PASS, T01-T04 PASS, oscilloscope SYN-to-TX evidence) + mandatory counters pass OBS-* self-tests + STD parity PASS (where applicable) + SPEC-*/PARSE-* pass on C firmware.

**Fails review if:** Any v1.0 gate criterion fails, mandatory counters not operational, OBS-* self-tests fail, or STD parity fails (where STD is offered).

---

## M4: Network + Reconnect — PRESERVED + test-gated

**Duration: 2-3 weeks per family. Depends on M3.**

v1.0 M4 deliverables PRESERVED (M4-D01 through M4-D07: TCP server, session lifecycle, idle timeout, reconnect handling, UDP-PLAIN optional, T09-T24 PASS, reconnect storm PASS). Added:

- SESS-RECONNECT-STORM (1000 cycles) must pass.
- FAULT-ETH-LINKFLAP (ESERA), FAULT-WIFI-DEGRADE (v5/C6) must pass.

**Gate:** v1.0 gate PRESERVED (T09-T24 PASS, reconnect storm PASS, zero resource growth after 1000 cycles) + fault-injection network tests pass.

**Fails review if:** Any v1.0 gate criterion fails, or any network fault-injection test does not recover cleanly.

---

## M5: Multi-Client — PRESERVED + proof-gated

**Duration: 2-4 weeks. Depends on M4. v3.x EXEMPT.**

v1.0 M5 deliverables PRESERVED (M5-D01 through M5-D05: compute proof, session manager, arbitration scheduler, T25-T88 PASS, fairness test PASS). Added:

- P-NON-INTERFERENCE proof: multi-client does not degrade single-client timing.

**Gate:** v1.0 gate PRESERVED (compute proof accepted, T25-T88 PASS 64/64, fairness 10% tolerance) + P-NON-INTERFERENCE proof accepted.

**Fails review if:** Any v1.0 gate criterion fails, or P-NON-INTERFERENCE proof shows timing degradation.

---

## M6: Full Harness Integration — PRESERVED

**Duration: 2-3 weeks. Depends on M3 (all families).**

v1.0 M6 deliverables PRESERVED (M6-D01 through M6-D06: complete ENH harness, topology runner integration, per-family smoke matrix automated, local CI, documentation). No changes from v1.0.

**Gate:** Full smoke matrix PASS for all families at applicable test levels.

**Fails review if:** Any automated test requires manual intervention, report format is not machine-readable, or CI script does not exist.

---

## M7: Soak + Hardening — TIGHTENED

**Duration: 3-6 weeks. Depends on M6.**

v1.0 M7 deliverables PRESERVED (M7-D01 through M7-D06: 72h soak, stuck TX/RX recovery, extended reconnect storm, watchdog recovery, bus fault injection, resource proof). Added:

- All FAULT-* tests pass (Section 6I — full fault-injection sweep).
- All OBS-* self-tests pass (Section 6L — observability validation).
- All XFAM-* parity tests pass (Section 6K — cross-family consistency).
- P-DETERMINISM proof: static analysis confirms no unbounded allocation, WCET bounded.
- Stress variant mandatory coverage pass (Section 11C items 1-4).

**Gate:** v1.0 gate PRESERVED (all soak/stress PASS, resource proof accepted) + all FAULT-*/OBS-*/XFAM-* pass + P-DETERMINISM proof accepted + mandatory stress variant coverage.

**Fails review if:** Any v1.0 gate criterion fails, any FAULT-* test does not recover, any OBS-* self-test fails, any XFAM-* parity test shows divergence, or P-DETERMINISM proof identifies unbounded allocation.

---

## M8: tinyebus Augmentation — REPLACED (proof-gated)

**Duration: 2-4 weeks. Depends on M5 for eligible families.**

v1.0 M8 deliverables are REPLACED. Each tinyebus augmentation feature (F13, F17-F19) requires its own proof chain:

1. P-MEMORY: feature fits within remaining memory budget.
2. P-NON-INTERFERENCE: feature does not degrade arbitration or protocol timing.
3. P-SOAK: 72h soak with augmentation active shows no regression.

**Gate:** Compute proof accepted per augmentation feature + soak PASS with augmentation active.

**Fails review if:** Any augmentation degrades arbitration latency, soak test shows regression, or memory budget exceeded.

---

## M9: Release — PRESERVED

**Duration: 1-2 weeks. Depends on M7 (and M8 if pursued).**

v1.0 M9 deliverables PRESERVED (M9-D01 through M9-D08: versioning, release packaging, rollback docs, OTA optional, doc-gate finalized, CHANGELOG, release template, tinyebus README). Release-gate tests (Section 6M) are the formal exit criterion.

**Gate:** All doc-gate PASS (Section 14) + at least one release candidate per family with all release-gate tests (Section 6M) green.

**Fails review if:** Any doc-gate entry is missing, release candidate has failing release-gate tests, or rollback procedure is untested.
