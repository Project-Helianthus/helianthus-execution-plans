# Proxy v0.6.99 Chunk 10: Foundations — Invariant, Decision Matrix, Doc-Gate

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: None. This chunk defines the measurement-only invariant, the
locked decision matrix `AD01..AD10`, and the doc-gate / transport-gate
classification the rest of the plan imports.

Scope: The bit-identical contract over named proxy paths, the resolution of
every AD entry, and the per-milestone doc-gate trigger table. Out of scope:
concrete milestone deliverables (those live in chunks 11–15).

Idempotence contract: Declarative-only. Reapplying this chunk must not add a
second invariant, relax the bit-identical scope, or silently re-open a
resolved AD entry.

Falsifiability gate: A review fails this chunk if it permits a behavior
change to any §1 path, treats `AD07`/`AD08` as still-open, omits a milestone
from the doc-gate table, or claims transport-gate is triggered when no
milestone modifies wire framing/registers/transport selection.

Coverage: §0 Summary; §1 Central Invariant; §2 AD01..AD10; §3 Doc-Gate
Classification; §9 Looking Ahead (reference only).

## Why v0.6.99 Exists

v0.6.99 is a **measurement-only release**. It lands synthetic and stress-test
infrastructure on the current `adaptermux` design **before** any v0.7.0
behavior change. The sole deliverable is reproducible golden SLO baselines.
Without it, every v0.7.0 claim (WFQ fairness, admission control, deadline
propagation, T2/T3 portability) is hand-waving. Adversarial review (Codex
gpt-5.5) named "deterministic bus simulator + golden SLO profiles" as the
highest-leverage missing item in the program; v0.6.99 ships that artifact.

## Central Invariant — Measurement-Only

Across milestones M0..M10, the following proxy code paths MUST remain
**bit-identical** to the `v0.6.5` tag:

- `internal/proxy/**`
- `internal/scheduler/**`
- `internal/session/**`
- `internal/southbound/**`
- `internal/northbound/**`
- `internal/adapterproxy/**`
- `internal/sourcepolicy/**`
- `internal/emulation/**` (existing files only; new sub-packages permitted)
- `internal/domain/**`
- `internal/compat/**`

`scripts/check_bit_identical.sh` (installed in M0) verifies SHA256 sums of
these paths against the `v0.6.5` tag on every PR. PRs touching them must
`git revert` or escalate.

Permitted writes during v0.6.99:

| Path                                | Purpose                                       |
|-------------------------------------|-----------------------------------------------|
| `internal/admin/http.go`            | pprof + expvar registration only (AD07).      |
| `internal/emulation/bussim/`        | New sub-package — bus simulator.              |
| `cmd/proxy-bench/`                  | New binary — scenario runner.                 |
| `test/bench/**`                     | New harness — clients, metrics, scenarios.    |
| `scripts/ci_local.sh`               | Append smoke run.                             |
| `scripts/check_bit_identical.sh`    | New CI gate.                                  |
| `scripts/run-bench-soak.sh`         | New on-demand soak runner.                    |
| `docs/bench-spec.md`                | New doc.                                      |
| `baselines/v0.6.99/*.yaml`          | Golden SLO profiles (M9 only).                |

## Decision Matrix

| ID    | Decision                                                                      | Resolution                                                                                                                                                                            |
|-------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AD01  | bussim speaks ENH/ENS framing over TCP (not raw eBUS bytes).                  | RESOLVED. Proxy southbound is TCP-to-PIC; bussim emulates PIC side.                                                                                                                  |
| AD02  | Fairness is wire-time, NOT request count.                                     | RESOLVED. B509 scan equals dozens of point reads; request-count fairness is a known anti-pattern (per Codex adversarial review).                                                     |
| AD03  | Workloads MUST be bit-deterministic given a seed.                             | RESOLVED. Every workload accepts `seed uint64`.                                                                                                                                       |
| AD04  | 24h soak (S12) is on-demand, not in CI.                                       | RESOLVED. M10 ships `scripts/run-bench-soak.sh`; CI runs only S1+S2 smoke (<90s).                                                                                                    |
| AD05  | `bench-spec.md` lives in proxy repo by default.                               | RESOLVED. Per-milestone doc-gate table below decides docs-ebus companion case-by-case.                                                                                                |
| AD06  | v0.6.99 baselines are immutable once committed.                               | RESOLVED. v0.7.0 cannot regenerate without operator approval.                                                                                                                         |
| AD07  | Mux-internals source (goroutines, mutex profile, GC pauses, heap).            | RESOLVED (operator, 2026-05-11): **always-on pprof in `internal/admin/http.go`**. internal/admin/ is observation-layer and NOT in §1 bit-identical list.                              |
| AD08  | Pcap source for S13.                                                          | RESOLVED (operator, 2026-05-11): **synthetic mandatory + live best-effort**. M2 ships golden synthetic fixtures (lock-blocking). M8 attempts live capture; if unavailable, ship with note. |
| AD09  | Release anchor: branch off `v0.6.5` tag.                                      | RESOLVED. If `v0.6.5` not yet tagged when M0 starts, M0 blocks; escalates after 72h.                                                                                                  |
| AD10  | WFQ / admission / token-bucket are v0.7.0 design items.                       | RESOLVED. v0.6.99 measures the CURRENT FIFO behavior (including S4 greedy and S11 overflow); v0.7.0 improves it.                                                                      |

## Doc-Gate Classification per Milestone

| Milestone | Trigger | Doc artifact |
|-----------|---------|--------------|
| M0  | None | None |
| M1  | RE knowledge: device table encodes Vaillant device-ID semantics. | `docs-ebus` companion PR documenting bussim/devices.go device table. |
| M2  | None (fixture format internal). | `docs/bench-spec.md § fidelity-fixtures` (proxy-local). |
| M3  | Public contract for v0.7.0 measurement. | `docs/bench-spec.md § schema` (proxy-local). |
| M4  | None | `docs/bench-spec.md § runner` (CLI usage). |
| M5  | None | `docs/bench-spec.md § scenarios`. |
| M6  | None | `docs/bench-spec.md § failure-injection`. |
| M7  | None | `docs/bench-spec.md § reports`. |
| M8  | Conditional: live pcap topology → docs-ebus note. | `docs/bench-spec.md § replay`; conditional docs-ebus. |
| M9  | None | `baselines/v0.6.99/README.md`. |
| M10 | None | `scripts/README.md` updates. |

## Transport-Gate

**NOT triggered** for any milestone in v0.6.99. No milestone modifies wire
protocol, framing, register semantics, or transport-selection logic. `bussim`
consumes the existing ENH/ENS framing spec; it does not introduce new framing.

If a future amendment to this plan adds wire-protocol changes (e.g., a new
ENH variant), it MUST re-classify and re-lock with transport-gate=triggered.

## Looking Ahead (reference)

When v0.7.0 starts (separate plan), it branches off the `v0.6.99` tag, runs
the harness on every milestone PR, and diff-gates against
`baselines/v0.6.99/*.yaml`. The bus simulator becomes the foundation for
"bench-as-product" (Codex review item) — extractable when API stabilizes.
