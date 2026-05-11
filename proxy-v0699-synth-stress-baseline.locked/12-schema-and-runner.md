# Proxy v0.6.99 Chunk 12: Metric Schema + proxy-bench Runner (M3..M4)

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: [10-foundations.md](./10-foundations.md) (AD02 wire-time fairness,
AD06 baseline immutability, AD07 pprof source), [11-anchor-and-sim.md](./11-anchor-and-sim.md)
(bussim package, fidelity fixtures).

Scope: M3 metric schema + golden SLO YAML format (contract first, no
scenarios yet); M4 `cmd/proxy-bench` runner binary + scenario `S1`
(single-client-baseline) end-to-end. Out of scope: multi-client scenarios,
failure injection, metrics collector implementation.

Idempotence contract: M3 introduces only schema files and the YAML format
contract — re-applying M3 must not alter the schema after lock without an
explicit amendment (semver-bumped). M4 introduces a single binary and a
single scenario YAML — re-applying must not modify S1's seed, busload, or
duration without baseline regeneration.

Falsifiability gate: M3 fails if the SLO YAML format cannot represent any
metric in §6 of the canonical (per-client P50/P99/P999, Jain fairness, Gini,
deadline-miss rate, busload, mux internals). M4 fails if `proxy-bench run
scenarios/S1.yaml` does not produce a result file matching the M3 schema, or
if the result is not deterministic across 10 runs with same seed (variance
in P50/P95 > 2%).

Coverage: §4 Architecture (client generator and metrics sources); §6 metrics
map; §7 milestones M3 + M4.

## R1 Fix Note

Codex R1 attack A1 surfaced that M2..M3 scenarios without metric definitions
are unfalsifiable. **This chunk places metric schema (M3) before any scenario
beyond S1.** Scenarios S2..S11 land in chunk 13 (M5..M6) AFTER M3 has locked
what is being measured.

## M3 — Metric Schema + Golden SLO YAML Format

Single PR. Deliverables:

1. **Metric schema** at `test/bench/metrics/schema.go`:
   ```go
   package metrics

   type Result struct {
       Scenario     string          `yaml:"scenario"`
       ProxyVersion string          `yaml:"proxy_version"`
       Seed         uint64          `yaml:"seed"`
       Duration     Duration        `yaml:"duration"`
       Clients      []ClientResult  `yaml:"clients"`
       Fairness     FairnessResult  `yaml:"fairness"`
       MuxInternals MuxInternals    `yaml:"mux_internals"`
       Tolerance    *Tolerance      `yaml:"tolerance,omitempty"`
   }
   type ClientResult struct {
       ID                  string  `yaml:"id"`
       Profile             string  `yaml:"profile"`
       LatencyP50Ms        float64 `yaml:"latency_p50_ms"`
       LatencyP95Ms        float64 `yaml:"latency_p95_ms"`
       LatencyP99Ms        float64 `yaml:"latency_p99_ms"`
       LatencyP999Ms       float64 `yaml:"latency_p999_ms"`
       ThroughputTxPerS    float64 `yaml:"throughput_tx_per_s"`
       WireTimeSharePct    float64 `yaml:"wire_time_share_pct"`
       DeadlineMissRate    float64 `yaml:"deadline_miss_rate"`
       ErrorCategoryCounts map[string]int `yaml:"error_category_counts,omitempty"`
   }
   type FairnessResult struct {
       JainIndex float64 `yaml:"jain_index"`  // 1.0 = perfect fairness
       Gini      float64 `yaml:"gini"`         // 0.0 = perfect fairness
   }
   type MuxInternals struct {
       GoroutinesPeak   int     `yaml:"goroutines_peak"`
       GoroutinesSteady int     `yaml:"goroutines_steady"`
       AllocBytesPerS   int64   `yaml:"alloc_bytes_per_s"`
       MutexP99WaitNs   int64   `yaml:"mutex_p99_wait_ns"`
       GCPausesP99Ms    float64 `yaml:"gc_pauses_p99_ms"`
       HeapRSSBytes     int64   `yaml:"heap_rss_bytes"`
   }
   type Tolerance struct {
       LatencyP99MsDeltaPct  float64 `yaml:"latency_p99_ms_delta_pct"`
       LatencyP999MsDeltaPct float64 `yaml:"latency_p999_ms_delta_pct"`
       JainDeltaPct          float64 `yaml:"jain_delta_pct"`
       DeadlineMissDeltaAbs  float64 `yaml:"deadline_miss_delta_abs"`
   }
   ```
2. **Golden SLO YAML format** documented in `docs/bench-spec.md § schema`
   with an annotated example, including the `tolerance` block semantics:
   - `latency_p99_ms_delta_pct: 10` means v0.7.0 must not exceed baseline
     P99 by more than 10%.
   - `jain_delta_pct: -5` means v0.7.0 should IMPROVE Jain; regression
     beyond -5% (i.e., baseline 0.94 → v0.7.0 0.89) fails.
   - `deadline_miss_delta_abs: 0.0` means deadline-miss rate must not
     increase in absolute terms.
3. **Diff utility** at `cmd/proxy-bench/diff.go` (subcommand `proxy-bench
   compare <baseline.yaml> <current.yaml>`): reads two Result YAMLs, applies
   tolerance, emits PASS/FAIL with per-metric delta. M9 uses this to gate
   baseline capture; v0.7.0 uses it for regression detection.

Acceptance: Schema is consumed by M4's runner and emits valid YAML. `proxy-bench
compare` correctly classifies a synthetic "no-change" pair as PASS and a
"P99 regressed by 20%" pair as FAIL.

## M4 — proxy-bench Runner + S1 Single-Client-Baseline

Single PR. Deliverables:

1. **`cmd/proxy-bench/main.go`** with subcommands:
   - `run <scenario.yaml>` — spin up bussim (M1), proxy (built from `v0.6.5`
     SHA pinned in M0 + admin pprof from M1), and N clients per the
     scenario; collect metrics; write `results/<scenario>-<timestamp>.yaml`.
   - `compare <baseline.yaml> <current.yaml>` — wired from M3.
   - `soak <scenario.yaml> --duration 24h` — long-run mode (M10 wires this
     into a separate script).
   - `replay <scenario.yaml> --pcap <file>` — pcap replay mode (M8 wires this).
2. **Scenario YAML format** documented in `docs/bench-spec.md § scenarios`:
   ```yaml
   id: S1
   name: single-client-baseline
   seed: 0x42
   duration: 60s
   clients:
     - id: client-0
       profile: pollLoop
       params:
         period: 1s
         registers: [0x0000, 0x0001]
   bussim:
     devices:
       - id: BAI00
         address: 0x08
         response_latency_us:
           mean: 12000
           jitter: 2000
   sweep:                       # optional — runs scenario at each busload %
     busload_pct: [10, 20, 30, 40, 50, 60]
   ```
3. **First scenario file** at `test/bench/scenarios/S1.yaml` implementing
   the table above for single-client-baseline.
4. **Skeleton clients package** at `test/bench/clients/`:
   - `client.go` — common interface, request-tagging, latency histogram
     accumulator (HDR Histogram or similar — `github.com/HdrHistogram/hdrhistogram-go`).
   - `pollloop.go` — first profile (only profile needed by S1). Other
     profiles land in M5.

Acceptance: `proxy-bench run test/bench/scenarios/S1.yaml` produces
`results/S1-*.yaml` matching M3 schema. Re-run with same seed reproduces
P50/P95 latency within ±2% (verifies AD03 determinism). Runtime < 60s per
busload sweep step (so the full sweep is <6 minutes — short enough for
M4 to ship before scenarios M5/M6).

## Risk Notes

- **AD07 dependency**: M4 must read `/debug/pprof/*` from the proxy under
  test. If the proxy is not running with the admin port exposed (or pprof
  is built without the M1 wiring), `mux_internals` block will be empty.
  M4's acceptance requires `mux_internals.goroutines_steady > 0`.
- **HDR Histogram dependency**: adds a new transitive Go dep. Vendored or
  pinned via `go.mod`. Verify it builds cleanly under the v0.6.5 toolchain
  (Go 1.22) without modifying any §1 path.
