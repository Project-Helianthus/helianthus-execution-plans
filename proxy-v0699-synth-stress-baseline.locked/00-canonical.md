# Proxy v0.6.99 — Synthetic & Stress-Test Baseline (Canonical)

Slug: `proxy-v0699-synth-stress-baseline`
Status: locked
Locked at: 2026-05-11
Source discussion: in-session synthesis from operator + Claude consultant + Codex adversarial review (threadIds 019e1851-f11d-7f33-b874-8304cbd613e7 and 019e185d-17d0-79e3-9685-e14190b17347)
Target repo: `helianthus-ebus-adapter-proxy` (single)
Knowledge repo: `helianthus-docs-ebus` (conditional; see §3 doc-gate)
Releases: branches off `v0.6.5` (in flight in a separate session); produces `v0.6.99` tag.

## 0. Summary

v0.6.99 is a **measurement-only release** that lands the synthetic test and stress-test infrastructure for the current `adaptermux` (adapter multiplexer) design **before** any v0.7.0 behavior change. Sole deliverable: reproducible, golden SLO baselines that v0.7.0 milestone PRs measure against — improvements proven, regressions caught.

Without this baseline, every v0.7.0 claim (fairness, admission control, deadline propagation, T2/T3 portability) is hand-waving. Adversarial review (Codex, gpt-5.5) identified "deterministic bus simulator + golden SLO profiles" as the highest-leverage missing item in the Helianthus proxy program; v0.6.99 delivers exactly that artifact.

## 1. Central Invariant — Measurement-Only

Across all milestones M0..M10, the following proxy code paths MUST remain **bit-identical** to the `v0.6.5` tag:

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

A CI check (`scripts/check_bit_identical.sh`) installed in M0 verifies these paths' SHA256 sums against the `v0.6.5` tag on every PR. PRs that change those paths must `git revert` or explicitly close the meta-issue with operator approval.

**Permitted writes**:
- `internal/admin/http.go` — pprof + expvar registration only (observation layer, not behaviorful). See AD07.
- `internal/emulation/bussim/` — new sub-package.
- `cmd/proxy-bench/` — new binary.
- `test/bench/**` — new test harness.
- `scripts/ci_local.sh`, `scripts/check_bit_identical.sh`, `scripts/run-bench-*.sh` — new or appended.
- `docs/bench-spec.md` — new doc.
- `baselines/v0.6.99/*.yaml` — golden SLO profiles (M9 only).

## 2. Decision Matrix

| ID | Decision | Resolution |
|----|----------|------------|
| AD01 | `bussim` speaks ENH/ENS framing over TCP, not raw eBUS bytes. | RESOLVED. The proxy's southbound transport is TCP-to-PIC; bussim emulates the PIC side. |
| AD02 | Fairness is measured in wire-time (microseconds of bus occupancy per client), NOT request count. | RESOLVED. A B509 scan equals dozens of point reads in wire-time; request-count fairness is a known anti-pattern. |
| AD03 | Workloads MUST be bit-deterministic given a seed. | RESOLVED. Every workload accepts a `seed uint64`; same seed reproduces same byte sequence. |
| AD04 | 24h soak (S12) is on-demand, not in CI. | RESOLVED. M10 ships `scripts/run-bench-soak.sh`; CI runs only S1+S2 smoke (<90s). |
| AD05 | `bench-spec.md` lives in proxy repo by default; docs-ebus companion required only if scripted device semantics introduce new reusable RE knowledge. | RESOLVED. See §3 doc-gate per-milestone classifier. |
| AD06 | v0.6.99 baselines are immutable once committed; v0.7.0 cannot regenerate without operator approval. | RESOLVED. Baselines are committed in M9 PR; v0.7.0 milestones diff against them. |
| AD07 | Mux-internals source (goroutine count, mutex profile, GC pauses, heap). | RESOLVED (operator, 2026-05-11): **Always-on pprof in `internal/admin/http.go`**. internal/admin/ is observation-layer (NOT in §1 bit-identical list); adding `net/http/pprof` + expvar there does not violate the measurement-only invariant. |
| AD08 | Pcap source for S13 simulator-fidelity-vs-real check. | RESOLVED (operator, 2026-05-11): **Synthetic mandatory + live best-effort**. M2 ships golden synthetic frame fixtures (lock-blocking). M8 attempts a live pcap from the 192.168.100.4 deploy; if operator cannot capture one by M8 PR time, M8 ships with synthetic-only and notes the realism gap. |
| AD09 | Release anchor: v0.6.99 branches off `v0.6.5` tag, recorded by SHA, enforced by `check_bit_identical.sh`. | RESOLVED. If `v0.6.5` is not yet tagged when M0 starts, M0 blocks until it is (or escalates to operator after 72h). |
| AD10 | Token-bucket / admission / WFQ — these are v0.7.0 design items. v0.6.99 measures their ABSENCE (current FIFO behavior). | RESOLVED. Baseline scenarios capture S4 greedy-client and S11 queue-overflow with the current code; v0.7.0 will improve them. |

## 3. Doc-Gate Classification (per-milestone)

Per AGENTS.md doc-gate rules, each milestone classifies its doc obligations:

| Milestone | Doc-gate trigger | Required doc artifact |
|-----------|------------------|------------------------|
| M0 release anchor | None (build/CI internal). | None. |
| M1 bussim package | RE knowledge: scripted device table encodes Vaillant device-ID semantics. | `docs-ebus` companion PR documenting the device table referenced by `bussim/devices.go`. Doc-gate classification: **RE-derived protocol knowledge**. |
| M2 simulator fidelity-min | None (internal fixture format). | `docs/bench-spec.md` § fidelity-fixtures (proxy-local). |
| M3 metric schema + SLO YAML | Public contract for v0.7.0 measurement. | `docs/bench-spec.md` § schema (proxy-local). Cross-product reference unnecessary. |
| M4 proxy-bench runner | None. | CLI usage in `docs/bench-spec.md` § runner. |
| M5 workload profiles + scenarios | None. | Scenario catalog in `docs/bench-spec.md` § scenarios. |
| M6 failure-injection | None. | Failure modes documented in `docs/bench-spec.md` § failure-injection. |
| M7 metrics collector + reporter | None. | Output format in `docs/bench-spec.md` § reports. |
| M8 pcap replay | If live capture is included: source-of-truth note in `docs-ebus` referencing the captured deployment topology. | `docs/bench-spec.md` § replay; conditional docs-ebus companion. |
| M9 baseline capture | None (data artifact only). | `baselines/v0.6.99/README.md` describing what the YAMLs represent. |
| M10 CI smoke + soak | None. | `scripts/README.md` updates. |

Transport-gate: **NOT triggered** for any milestone. No milestone modifies wire protocol, framing, register semantics, or transport selection logic. `bussim` consumes the existing ENH/ENS framing spec; it does not introduce new framing.

## 4. Architecture

```
┌────────────────┐    ┌──────────────────────────┐    ┌──────────────┐
│ Load Generator │ ─→ │  proxy (UNCHANGED v0.6.5)│ ─→ │ Bus Simulator│
│  (N clients)   │ ←─ │  + admin pprof (AD07)    │ ←─ │ (fake ENH)   │
└────────────────┘    └──────────────────────────┘    └──────────────┘
        ↓                        ↓                            ↓
        └────────── Metrics Collector (per-side) ─────────────┘
                              ↓
                    Scenario Runner + Reporter
                              ↓
                    JSON results + golden SLO YAML
```

### 4.1 Bus Simulator (`internal/emulation/bussim/`)

- Speaks ENH/ENS framing over TCP (same wire format the real PIC emits).
- Scripted eBUS device table: BAI00 (0x08), BASV2 (0x15), VR_71 (0x26), SOL00 (0xEC), NETX3 (0x04/0xF6) — matches live-deploy map.
- Per-device: programmable response latency (mean + jitter), content, error injection (NACK, malformed CRC, byte drop, stuck bus).
- **Wire-time ground truth**: every emitted/consumed symbol carries a monotonic timestamp. This is the SOLE source of truth for AD02 wire-time fairness.
- Replay mode (M8): ingests a recorded pcap or synthetic-fixture file and emits the same byte stream verbatim.

### 4.2 Client Load Generator (`test/bench/clients/`)

Spawns N virtual northbound clients against the proxy's existing client surface. Per-client workload profiles:

| Profile | Behavior |
|---------|----------|
| `pollLoop` | Periodic register reads (HA semantic poller analog). |
| `scanBurst` | B509/B524 scan storm (discovery tool analog). |
| `writeAfterRead` | Write-then-verify sequence. |
| `adHoc` | Randomized request mix (operator/ebusctl analog). |
| `greedy` | Unbounded request rate (admission-stress). |
| `slowConsumer` | Issues requests but ACKs responses with delay (backpressure). |

Each client tags every request `(clientID, profileTick, deadlineNs)` and records P50/P95/P99/P999 round-trip wall-clock.

### 4.3 Metrics Sources

| Layer | Source | Captured |
|-------|--------|----------|
| Per-client (north) | Load generator | Latency histograms, throughput, error rate, deadline-miss rate. |
| Wire (south) | bussim ground truth | Per-client wire-time, Jain fairness index, Gini, busload %, per-device tx count. |
| Mux internals | Proxy `/debug/pprof/*` (AD07) | Mutex profile, goroutine count, allocs/sec, GC pauses, heap RSS. |

Output: JSON per scenario; Markdown summary with ASCII histograms; YAML golden SLO profile per scenario for regression gating.

## 5. Test Scenarios

| ID  | Name                          | Clients | Busload  | Duration | Purpose                                    |
|-----|-------------------------------|---------|----------|----------|--------------------------------------------|
| S1  | single-client-baseline        | 1       | 10–60%   | 60s ×6   | Latency floor; per-busload curve           |
| S2  | identical-pollers-fairness    | 2,3,6   | 60%      | 5min     | Wire-time fairness on identical workloads  |
| S3  | mixed-workload                | 6       | 60%      | 5min     | poll+scan+writeAfterRead+adHoc mix         |
| S4  | one-greedy-five-fair          | 6       | overload | 5min     | Does greedy client starve fair clients?    |
| S5  | one-slow-consumer             | 6       | 60%      | 5min     | Backpressure semantics; queue growth       |
| S6  | scan-storm-during-polling     | 6       | overload | 5min     | Worst-case discovery + steady-state mix    |
| S7  | failure-injection-corrupt-crc | 3       | 30%      | 5min     | Per-client error isolation                 |
| S8  | failure-injection-stuck-bus   | 3       | n/a      | 60s ×3   | Recovery semantics; deadline propagation   |
| S9  | adapter-reconnect-storm       | 6       | 30%      | 5min     | bussim drops TCP and reconnects 5×/min     |
| S10 | client-reconnect-storm        | 6→0→6   | 30%      | 5min     | Client churn; goroutine-leak check         |
| S11 | queue-overflow                | 6       | overload | 5min     | What does current code do at saturation?   |
| S12 | soak-24h                      | 3       | 30%      | 24h      | Memory growth, goroutine leak, GC drift    |
| S13 | pcap-replay-realism           | n/a     | recorded | 1 capture| Synthetic-vs-real drift check (AD08)       |

## 6. Captured Metrics → v0.7.0 Mapping

Every captured metric maps to a specific v0.7.0 design item it lets us evaluate:

| Metric                                       | v0.7.0 item                              |
|----------------------------------------------|-----------------------------------------|
| Per-client P99 / P999 latency                | WFQ scheduler, deadline context         |
| Wire-time Jain fairness index across N       | WFQ scheduler                           |
| Per-client wait time at queue head           | Priority class taxonomy                 |
| Deadline-miss rate per client                | Deadline-propagating context            |
| 429/busy rate at overload                    | Admission control / token bucket        |
| Estimated vs ground-truth busload drift      | Predictive busload estimator            |
| Error-category distribution (S7/S8)          | Loss-mode taxonomy                      |
| Mutex contention profile under S3/S4         | Single-writer invariant; lock-free      |
| Goroutine count over S10                     | Goroutine leak guards                   |
| Heap growth over S12                         | Memory discipline; arena pools (T2)     |
| Cache-hit rate on identical reads            | Read-coalescing claim (refute/confirm)  |

## 7. Milestone Sequence

The order applies fixes from Codex R1 review (attack A1: metric schema must precede scenarios; attack A2: simulator fidelity-min must precede metric capture; attack A6: release anchor must come first).

| Milestone | Title | Deliverable summary |
|-----------|-------|---------------------|
| M0 | Release anchor | Wait for `v0.6.5` tag; commit `scripts/check_bit_identical.sh` listing the §1 paths; CI-enforce on every PR; add `//go:build` tag scaffolding for pprof admin extension. |
| M1 | bussim package | `internal/emulation/bussim/{framing,devices,inject}.go`; scripted device table; wire-time ground truth. Admin pprof registration in `internal/admin/http.go` (AD07). |
| M2 | Simulator fidelity-min | Golden synthetic frame fixtures + byte-diff replay harness; bussim must reproduce fixtures bit-exactly. |
| M3 | Metric schema + SLO YAML format | `test/bench/metrics/schema.go`; `docs/bench-spec.md` § schema; no scenarios yet. |
| M4 | proxy-bench runner + S1 | `cmd/proxy-bench/main.go`; loads YAML scenario; spins simulator+proxy+clients; S1 single-client-baseline only. |
| M5 | Workload profiles + multi-client scenarios | `test/bench/clients/{pollLoop,scanBurst,writeAfterRead,adHoc,greedy,slowConsumer}.go`; S2–S6. |
| M6 | Failure-injection primitives | bussim error injection wiring; S7–S11. |
| M7 | Metrics collector + reporter | Per-client / wire-side / pprof-side collectors; JSON+Markdown+YAML output. |
| M8 | pcap replay + S13 | `bussim/replay.go`; M2 synthetic fixture replayed AND live deploy pcap if available (AD08). |
| M9 | Baseline capture | Run S1–S11 + S13; commit `baselines/v0.6.99/*.yaml` with `tolerance` blocks. Operator review before merge. |
| M10 | CI smoke + soak runner | Append S1+S2 smoke (<90s) to `scripts/ci_local.sh`; add `scripts/run-bench-soak.sh` for S12. |

Each milestone is one PR per AGENTS.md `one-PR-per-repo` invariant; squash-merge.

## 8. Acceptance & Falsifiability

Per-milestone falsifiability gates are listed in the corresponding chunk file (10–15). The plan-level acceptance is:

1. After M9 merges, `baselines/v0.6.99/*.yaml` contains golden SLOs for S1..S11 (and S13 with realism note per AD08 outcome).
2. v0.6.99 tag is created against the head of M10's merge commit.
3. `scripts/check_bit_identical.sh` passes against `v0.6.5` for every PR in the sequence.
4. Smoke run in `ci_local.sh` completes <90s with non-zero exit on baseline regression.
5. Independent re-run of S1 ten times with same seed reproduces latency P50/P95 within ±2%.

## 9. Looking Ahead to v0.7.0

When v0.7.0 begins (separate plan, not this one):
1. Branch from `v0.6.99` tag.
2. Each v0.7.0 milestone PR re-runs the harness; diff against `baselines/v0.6.99/*.yaml` becomes part of PR description.
3. Intentional improvements regenerate the baseline (operator approval required).
4. Harness migrates with codebase: T2 (direct UART) work adds bussim UART backend; T3 (ESP32/TinyGo) work adds reduced scenario set.
5. The bus simulator becomes the foundation for the "bench-as-product" component flagged by Codex review — extractable to a separate repo when API stabilizes.
