# Milestone Map

| Milestone | Scope | Primary repos | Depends on | Status |
| --- | --- | --- | --- | --- |
| `T0` | testing-first reframing, proof templates, oracle export, and harness architecture | `helianthus-docs-ebus`, `helianthus-tinyebus` | none | active |
| `M0` | hardware truth, protocol baseline, reference captures, HIL specs, and family capability drafts | `helianthus-docs-ebus`, `helianthus-tinyebus` | `T0` | queued |
| `M1` | adversarial matrix, compile-clean harness stubs, and finalised contract docs | `helianthus-docs-ebus`, `helianthus-tinyebus` | `M0` | queued |
| `M2` | per-family proofs, skeletons, timing hooks, memory proofs, and Tier-B compilation gates | `helianthus-tinyebus`, `helianthus-ebusgo` | `M1` | queued |
| `M3` | ENH, ENS, and STD implementation with mandatory observability from day zero | `helianthus-tinyebus`, `helianthus-docs-ebus` | `M2` | queued |
| `M4` | network lifecycle, reconnect handling, and fault-tested transport behaviour | `helianthus-tinyebus`, `helianthus-ebus-adapter-proxy` | `M3` | queued |
| `M5` | optional multi-client proofs and enablement for eligible families only | `helianthus-tinyebus`, `helianthus-ebus-adapter-proxy` | `M4` | optional |
| `M6` | full harness integration and topology runner validation | `helianthus-ebusgateway`, `helianthus-ha-addon`, `helianthus-tinyebus` | `M3` | queued |
| `M7` | soak, hardening, determinism, observability, and cross-family parity gates | `helianthus-tinyebus`, `helianthus-docs-ebus` | `M6` | queued |
| `M8` | proof-gated tinyebus augmentation for eligible families | `helianthus-tinyebus` | `M5` | optional |
| `M9` | release candidates, rollback readiness, final doc-gate closure, and release artifacts | `helianthus-tinyebus`, `helianthus-docs-ebus`, `helianthus-ha-addon` | `M7` and `M8` if pursued | queued |

## Ordering Rules

- The default order is `T0 -> M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9`.
- `T0` is mandatory and timeboxed; no hardware or implementation milestone starts before it completes.
- `M0` tracks may execute in parallel across families once `T0` is locked.
- `M2`, `M3`, and `M4` may parallelize per family after their prerequisite milestone is complete.
- `M5` and `M8` are optional proof-gated lanes and may remain intentionally unopened for ineligible families.
- Locked decisions in [00-canonical.md](./00-canonical.md) override shorthand in this file if drift appears.
