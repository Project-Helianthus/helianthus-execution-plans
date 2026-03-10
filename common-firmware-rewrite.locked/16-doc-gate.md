# Common Firmware Rewrite 07: Mega Doc-Gate List

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `117b40ab6c3df5cbc842ea7fbe228290fe861eca104c8ac209f09ea9132ab6cb`

Depends on: All prior chunks (01-06). T0 doc-gate entries come from Chunk 01 (testing-first philosophy). M0 doc-gate entries come from Chunks 02-04 (hardware RE, protocol). M1 doc-gate entries come from Chunks 02-05 (contracts, policies, harness). M2+ doc-gate entries come from Chunk 06 (milestones).

Scope: Complete mega doc-gate list organised into four categories: testing foundation docs (T0 gate), hardware and protocol docs (M0 gate), contract and policy docs (M1 gate), and implementation docs (M2+ gates). Total: 30 entries.

Idempotence contract: Reapplying this chunk must not create duplicate doc-gate entries or conflicting milestone assignments for the same document.

Falsifiability gate: A review fails this chunk if any doc-gate entry lacks an assumed path, if any entry lacks a milestone assignment, if the total count does not match 30, or if any entry referenced in prior chunks is missing from this list.

Coverage: Section 14 (Mega Doc-Gate List).

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
