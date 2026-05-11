# Proxy v0.6.99 Chunk 13: Workload Profiles + Scenarios + Failure-Injection (M5..M6)

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: [10-foundations.md](./10-foundations.md) (AD03 determinism, AD10
WFQ deferral), [11-anchor-and-sim.md](./11-anchor-and-sim.md) (bussim + error
injection primitives), [12-schema-and-runner.md](./12-schema-and-runner.md)
(metric schema + runner).

Scope: M5 workload profiles (`scanBurst`, `writeAfterRead`, `adHoc`,
`greedy`, `slowConsumer` — `pollLoop` already landed in M4) and multi-client
scenarios `S2..S6`; M6 failure-injection primitives wired into bussim, and
scenarios `S7..S11`. Out of scope: metrics collector implementation
(M7), pcap replay (M8), baseline capture (M9), CI smoke (M10).

Idempotence contract: Each workload profile is a pure function of `(seed,
config, time)` — re-applying M5 must not change the request stream for a
given seed. Scenario YAML files are immutable once committed; new scenarios
append, not replace. Failure-injection in M6 is additive to bussim and gated
by per-scenario config — disabled by default.

Falsifiability gate: M5 fails if a workload's request sequence differs
across runs with identical seed (verify with `proxy-bench run --dry-run`
diffing tagged request streams). M6 fails if failure-injection alters
bussim behavior when disabled, or if a scenario expecting injection (S7
expects 5% CRC corruption) produces zero injected errors over its duration.

Coverage: §5 Test Scenarios S2..S11; §7 milestones M5 + M6.

## M5 — Workload Profiles + Multi-Client Scenarios S2..S6

Single PR. Deliverables:

### Workload profiles (`test/bench/clients/`)

Each profile is a Go struct implementing the `client.Profile` interface from
M4. All accept a seed and emit deterministic request streams.

1. **`scanburst.go`** — emits a B509 ID scan or B524 group scan against a
   list of target slave addresses. Config: `{kind: id|group, targets: [...], period_jitter}`.
   Realistic discovery-tool analog. Highest wire-time cost per request.
2. **`writeafterread.go`** — issues `Read(reg)` then `Write(reg, value)`
   then `Read(reg)` to verify. Config: `{reg, write_value, dwell}`.
   Models config-flow clients.
3. **`adhoc.go`** — randomized request mix drawn from a configurable pool.
   Config: `{pool: [...request templates], rate, jitter}`. Models
   operator/ebusctl manual traffic.
4. **`greedy.go`** — unbounded request rate, no backoff, no flow control.
   Stresses admission. Config: `{template, max_in_flight}`.
5. **`slowconsumer.go`** — issues at normal rate but delays the ACK/read of
   the response by `delay_ms`. Stresses proxy-side backpressure (does
   per-session queue grow? does it OOM?). Config: `{template, period, ack_delay_ms}`.

### Scenarios S2..S6 (`test/bench/scenarios/`)

| ID  | YAML name                       | Clients | Busload  | Duration | Profile mix |
|-----|---------------------------------|---------|----------|----------|-------------|
| S2  | identical-pollers-fairness.yaml | 2,3,6   | 60%      | 5min     | All pollLoop, identical params. Sweep N=2/3/6. |
| S3  | mixed-workload.yaml             | 6       | 60%      | 5min     | 2× pollLoop, 1× scanBurst, 1× writeAfterRead, 2× adHoc. |
| S4  | one-greedy-five-fair.yaml       | 6       | overload | 5min     | 5× pollLoop, 1× greedy. Tests starvation under current FIFO (AD10 baseline). |
| S5  | one-slow-consumer.yaml          | 6       | 60%      | 5min     | 5× pollLoop, 1× slowConsumer with 200ms ack delay. |
| S6  | scan-storm-during-polling.yaml  | 6       | overload | 5min     | 3× pollLoop steady-state, 3× scanBurst simultaneous. |

Acceptance: Each scenario completes; each emits a `results/<id>-*.yaml`
matching M3 schema. Same seed reproduces the same wire-time distribution
within ±2%. S2 reveals current FIFO fairness numbers (likely Jain ≈ 0.95 for
identical pollers); S4 reveals current FIFO starvation behavior (likely Jain
crashes to <0.5 with greedy client dominating); S6 reveals scan-storm tail
latency.

## M6 — Failure-Injection + Scenarios S7..S11

Single PR. Deliverables:

### Failure-injection wiring (`internal/emulation/bussim/inject.go` extension)

Already added as primitives in M1; M6 wires them to scenario config and
adds the missing modes:

| Mode             | Effect                                                           |
|------------------|------------------------------------------------------------------|
| `corrupt_crc`    | Flip last CRC byte of every Nth response.                         |
| `byte_drop`      | Drop M random bytes from response stream per session.             |
| `stuck_bus`      | Stop emitting SYN; bus appears wedged for `duration`.             |
| `response_delay` | Add `delay_us` to response emission (jitter test).                |
| `tcp_drop`       | bussim severs TCP connection; proxy must reconnect.               |
| `tcp_refuse`     | bussim refuses reconnection for `duration`.                       |

Each mode is enable-per-scenario via YAML; default state is OFF.

### Scenarios S7..S11

| ID  | YAML name                          | Clients | Failures | Duration | Purpose |
|-----|------------------------------------|---------|----------|----------|---------|
| S7  | failure-corrupt-crc.yaml           | 3       | corrupt_crc rate=5% on BAI00 | 5min | Per-client error isolation; does one corrupt response affect other clients? |
| S8  | failure-stuck-bus.yaml             | 3       | stuck_bus 3s/60s repeating | 60s × 3 | Recovery semantics; deadline-miss distribution; how long does proxy wedge? |
| S9  | adapter-reconnect-storm.yaml       | 6       | tcp_drop 5×/min | 5min | Does proxy reconnect cleanly? do client sessions survive? |
| S10 | client-reconnect-storm.yaml        | 6→0→6   | none (client churn) | 5min | Goroutine-leak gate: post-churn goroutine count must return to baseline ±5. |
| S11 | queue-overflow.yaml                | 6       | none (overload) | 5min | What does current FIFO do at saturation? Captured as v0.7.0 admission-control baseline. |

Acceptance: Each scenario emits results YAML. S7 must show non-zero
`ErrorCategoryCounts["crc"]` for the affected client and near-zero for
others (cross-client isolation baseline). S8 must produce a recovery-time
histogram. S10 must show `goroutines_peak - goroutines_steady < 20` (sets
v0.7.0 leak-guard tolerance). S11 must produce a queue-depth-over-time trace
saved alongside the YAML (separate `<id>-queue-trace.json`).

## Risk Notes

- **AD10 baseline expectation**: S4 and S11 are EXPECTED to reveal poor
  fairness / unbounded queue growth under current FIFO. This is the v0.7.0
  improvement target, not a v0.6.99 bug. Document baseline numbers as-is;
  v0.7.0 WFQ + admission control will move them.
- **Determinism vs failure-injection**: Failures are gated by the same seed
  as the workload. The Nth response is determined by request count, not
  wall-clock, to keep injection reproducible across machines.
- **S10 churn timing**: Client disconnects must happen at deterministic
  request boundaries to keep the goroutine-count probe meaningful. Implement
  as scheduled events (`at: 60s, 120s, 180s`), not random.
- **S11 saturation interpretation**: "overload" busload is achieved by a
  greedy client + 5 fair clients all pushing concurrently. The current FIFO
  may queue unboundedly; M6 must add a hard guard: if results YAML reports
  `mux_internals.heap_rss_bytes > 500MB`, abort the scenario and mark
  result as `aborted_for_safety: true`. v0.7.0 will fix this; the abort
  itself is the v0.6.99 baseline finding.
