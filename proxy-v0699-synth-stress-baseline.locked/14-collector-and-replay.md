# Proxy v0.6.99 Chunk 14: Metrics Collector + Reporter + pcap Replay (M7..M8)

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: [10-foundations.md](./10-foundations.md) (AD02 wire-time fairness,
AD07 pprof source, AD08 pcap synthetic+best-effort policy),
[11-anchor-and-sim.md](./11-anchor-and-sim.md) (bussim + fidelity fixtures),
[12-schema-and-runner.md](./12-schema-and-runner.md) (metric schema, runner,
diff utility), [13-scenarios-and-failures.md](./13-scenarios-and-failures.md)
(scenarios S2..S11 producing data the collector must aggregate).

Scope: M7 metrics collector + report generator (per-client / wire-side /
pprof-side); M8 pcap replay support + S13 simulator-fidelity-vs-real check.
Out of scope: baseline capture (M9), CI smoke + soak (M10), any v0.7.0
behavior change.

Idempotence contract: M7's collector is read-only against the proxy
(pprof endpoints) and bussim (ground truth timestamps) — re-applying must
not introduce write paths to either. M8's replay mode is an additional
`bussim` source; reapplying must not modify fixture files committed in M2,
only register the replay backend.

Falsifiability gate: M7 fails if the produced YAML does not populate every
required field of the M3 schema for a 5-min run of S3, or if Jain index
computed by the collector differs by >1% from a hand-computed reference on a
small synthetic dataset. M8 fails if pcap replay of an M2 golden fixture
produces a different byte stream than the bussim-emitted fixture (must be
byte-identical for synthetic fixtures); for live pcaps (if available),
fails if `>1%` of frames cannot be matched to a known device-register pair.

Coverage: §4.3 Metrics Sources; §7 milestones M7 + M8; AD08 outcome path.

## M7 — Metrics Collector + Report Generator

Single PR. Deliverables:

### Per-client collector (`test/bench/metrics/client_collector.go`)

Already partially in M4 (HDR Histogram per client). M7 extends:

- Aggregates per-client histograms across all in-process clients.
- Computes P50/P95/P99/P999 from HDR data structures.
- Tracks per-client throughput (transactions/sec, bytes/sec wall-clock).
- Categorizes errors using a fixed taxonomy:
  - `timeout` — request exceeded deadline without response.
  - `crc` — response CRC failure.
  - `nack` — slave NACK.
  - `malformed` — frame structure invalid.
  - `connection_lost` — TCP severed mid-request.
  - `arbitration_lost` — proxy reported arbitration loss.
  - `other` — unclassified.

### Wire-side collector (`test/bench/metrics/wire_collector.go`)

Reads bussim's wire-time event log (monotonic-timestamped symbols), computes:

- **Per-client wire-time share**: for each ingress request, attributes the
  bus-occupied microseconds (from first request byte to last response byte)
  to the originating client.
- **Jain fairness index** across N clients with identical workload weight:
  `J = (Σxᵢ)² / (N · Σxᵢ²)`.
- **Gini coefficient** for wider workload-mix scenarios.
- **Busload %**: sum of all transaction wire-time / scenario duration.
- **Per-device transaction count** + per-device latency.

### pprof-side collector (`test/bench/metrics/pprof_collector.go`)

Scrapes proxy `/debug/pprof/*` and `/debug/vars` at scenario start, mid, end:

- `/debug/pprof/goroutine?debug=1` parsed for goroutine count + per-stack
  breakdown; takes `peak` and `steady` (last sample of steady-state region).
- `/debug/pprof/mutex` parsed for mutex P99 wait time. Note: requires
  `runtime.SetMutexProfileFraction(N)` to be enabled. Since the proxy code
  is bit-identical to v0.6.5, this must be set externally — `proxy-bench
  run` will trigger it via a debug-pprof endpoint hit before starting the
  scenario (POST to `/debug/pprof/mutex?rate=10` if accepted, else fall
  back to a documented-as-unmeasurable result and emit a warning).
- `/debug/pprof/heap` parsed for `HeapAlloc`, `HeapInuse`, `HeapSys`; RSS
  via `/proc/<pid>/status` if available (Linux only).
- GC pauses via `/debug/vars` `memstats` → `PauseNs` ring buffer.

### Report generator (`cmd/proxy-bench/report.go`)

`proxy-bench report <results.yaml>` emits a Markdown summary with:

- Per-client latency histogram (ASCII bar chart, log-spaced buckets).
- Fairness summary (Jain, Gini, per-client wire-time-share table).
- Mux-internals timeline (goroutines/heap over scenario duration).
- Error-category breakdown.
- A "diff vs baseline" section if `--baseline <path>` is passed.

### Tests

`go test ./test/bench/metrics/...` includes:

- Hand-computed Jain on `[10ms, 10ms, 10ms]` → 1.0 (within 1e-9).
- Jain on `[30ms, 0ms, 0ms]` → 0.333.
- Round-trip schema marshal/unmarshal preserves all fields.
- pprof scraper parses a captured sample without error.

Acceptance: Running `proxy-bench run S3.yaml` followed by `proxy-bench
report results/S3-*.yaml` produces a Markdown report that has data in
every section. Field coverage versus M3 schema is 100% for S3 (no `omitempty`
fields blank that should be populated).

## M8 — pcap Replay + S13 Fidelity Check

Single PR. Deliverables (per AD08: synthetic mandatory + live best-effort).

### Replay backend (`internal/emulation/bussim/replay.go`)

- New bussim mode: instead of generating responses from the scripted device
  table, replay a sequence of `(time_offset, direction, bytes)` records
  from a fixture or pcap file.
- Two input formats:
  - **M2 synthetic fixtures**: replay the committed `.in.bin`/`.out.bin`
    pairs as a ground-truth check that bussim's scripted output equals its
    own replayed input.
  - **Live pcap** (best-effort per AD08): standard `.pcap` capturing the
    TCP stream between gateway/proxy and real PIC adapter. Decoded
    ENH-over-TCP frames replayed in time order.

### S13 scenario (`test/bench/scenarios/S13.yaml`)

```yaml
id: S13
name: pcap-replay-realism
seed: 0   # unused for replay
duration: derived
sources:
  synthetic:
    - test/bench/fixtures/v0.6.99/boiler-status-read
    - test/bench/fixtures/v0.6.99/dhw-temp-write
    - test/bench/fixtures/v0.6.99/zone-time-program-read
    - test/bench/fixtures/v0.6.99/scan-id
    - test/bench/fixtures/v0.6.99/radio-device-id
  live_pcap:                     # optional, populated by operator if captured
    path: test/bench/fixtures/v0.6.99/live-deploy-2026-05.pcap
    optional: true
acceptance:
  synthetic_byte_diff_must_be_zero: true
  live_unmatched_frame_pct_max: 1.0
  live_optional_if_missing: true
```

### Operator capture instructions (`docs/bench-spec.md § replay`)

Documented procedure for capturing a live pcap from the
`192.168.100.4` deploy:

```
ssh root@192.168.100.4
tcpdump -i any -w /tmp/live-deploy-$(date +%F).pcap \
        -s 0 host <adapter-ip> and port <adapter-port>
# Run for >= 15 minutes during representative traffic
scp ...
```

If operator provides the pcap before M8 PR merge, commit it to
`test/bench/fixtures/v0.6.99/`. If not, ship M8 with synthetic-only and add
to `docs/bench-spec.md § replay` a "REALISM GAP" note describing that
live-deploy fidelity is unverified; reopen as a v0.7.0 task.

Acceptance: `proxy-bench replay scenarios/S13.yaml` succeeds against all
five synthetic fixtures with zero byte-diff. If `live_pcap` is provided,
matched-frame % ≥ 99%; unmatched frames are logged with timestamp + bytes
for operator review.

## Risk Notes

- **R1 attack A2** (sim fidelity too late) is fully resolved by the M2+M8
  split: M2 is the lock-blocking minimum (synthetic), M8 is the late-stage
  realism check (live). v0.6.99 baseline trustworthiness rests on M2; M8
  upgrades it from "self-consistent" to "real-world-validated" when live
  capture is available.
- **Mutex profile activation** (M7) requires either an external pprof hit
  to enable mutex profiling, or accepting that mutex P99 is unmeasurable
  for v0.6.99 baseline (which would weaken AD07's promise). Default plan:
  enable via the standard pprof debug endpoint; if rejected by upstream
  Go runtime, document as-unmeasurable.
- **Live pcap topology disclosure** (M8): the live capture includes the
  adapter IP and port. Sanitize before commit — replace with placeholders
  in any docs-ebus reference (the conditional doc-gate per M8 covers this).
