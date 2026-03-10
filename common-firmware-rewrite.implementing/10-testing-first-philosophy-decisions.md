# Common Firmware Rewrite 01: Testing-First Philosophy + Adversarially Locked Decisions

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: None. This chunk defines the foundational testing-first philosophy and locked decisions that all subsequent chunks depend on.

Scope: Testing-first philosophy (core principle, scope derivation, proof classes, lock/de-scope criteria, required instrumentation) and all 11 adversarially locked decisions (including 3 new decisions in v2.0).

Idempotence contract: Reapplying this chunk must not create conflicting proof class definitions, duplicate lock criteria, or ambiguous decision states.

Falsifiability gate: A review fails this chunk if any proof class lacks a concrete method, if any lock criterion lacks a machine-checkable or reproducible measurement procedure, if any decision lacks explicit failure modes survived, or if scope derivation is circular.

Coverage: Summary; Section 1 (Testing-First Philosophy); Section 2 (Adversarially Locked Decisions).

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
