# Proxy v0.6.99 Chunk 15: Baseline Capture + CI Smoke + Soak Runner (M9..M10)

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: [10-foundations.md](./10-foundations.md) (AD04 soak-on-demand,
AD06 baseline immutability), [11-anchor-and-sim.md](./11-anchor-and-sim.md),
[12-schema-and-runner.md](./12-schema-and-runner.md), [13-scenarios-and-failures.md](./13-scenarios-and-failures.md),
[14-collector-and-replay.md](./14-collector-and-replay.md). M9 must run AFTER
M1..M8 are merged — it consumes their full output.

Scope: M9 baseline capture (run S1..S11 + S13; commit
`baselines/v0.6.99/*.yaml` with per-scenario `tolerance` blocks; operator
review); M10 CI smoke wiring (append S1+S2 to `ci_local.sh`) + on-demand
soak runner (S12 24h via separate script). Out of scope: any v0.7.0 work,
real-hardware testing, the v0.6.99 release tag itself (operator action
after M10 merges).

Idempotence contract: M9 commits a one-time artifact (the baselines). Per
AD06, re-running M9 must not overwrite committed baselines without
operator-approved amendment. M10 appends to `ci_local.sh` and creates new
scripts — re-applying must not duplicate the smoke step or change S12
parameters.

Falsifiability gate: M9 fails if any baseline YAML is missing the
`tolerance` block, if S1..S11 numbers are not reproducible within ±2% on
operator's re-run, or if `proxy-bench compare baselines/v0.6.99/S3.yaml
results/S3-rerun.yaml` reports any FAIL on the first commit. M10 fails if
the appended `ci_local.sh` smoke step pushes total CI runtime above 90s,
or if `scripts/run-bench-soak.sh` cannot run S12 to completion on operator's
reference hardware (RPi4 64-bit).

Coverage: §7 milestones M9 + M10; §8 plan-level acceptance criteria.

## M9 — Baseline Capture + Commit

Single PR. Deliverables:

### Baseline-capture run

On operator's reference hardware (RPi4 64-bit at `192.168.100.4` per
project memory, OR a comparable workstation if RPi4 is unavailable for the
M9 run):

1. Build proxy at v0.6.5 SHA with M1..M8 changes applied (admin pprof
   wiring + bussim + bench harness).
2. Run each scenario S1..S11 once. Capture `results/<id>-baseline.yaml`.
3. Run S13 in synthetic mode (5 fixtures); if operator supplied live pcap
   via M8, run S13 with live source as well.
4. Re-run S1..S11 once more on a separate machine (operator's choice) to
   verify within-±2% determinism.

### Baselines (`baselines/v0.6.99/`)

Files committed in this PR (one YAML per scenario):

- `baselines/v0.6.99/S1.yaml` — single-client baseline curve (six
  busload-sweep entries).
- `baselines/v0.6.99/S2.yaml` — fairness (one entry per N ∈ {2, 3, 6}).
- `baselines/v0.6.99/S3.yaml` — mixed workload.
- `baselines/v0.6.99/S4.yaml` — greedy starvation baseline (expected
  Jain ≪ 1 per AD10).
- `baselines/v0.6.99/S5.yaml` — slow consumer / backpressure.
- `baselines/v0.6.99/S6.yaml` — scan storm.
- `baselines/v0.6.99/S7.yaml` — CRC corruption / per-client error
  isolation.
- `baselines/v0.6.99/S8.yaml` — stuck-bus / recovery.
- `baselines/v0.6.99/S9.yaml` — adapter reconnect storm.
- `baselines/v0.6.99/S10.yaml` — client reconnect / goroutine-leak baseline.
- `baselines/v0.6.99/S11.yaml` — queue overflow / saturation.
- `baselines/v0.6.99/S13.yaml` — pcap-replay fidelity baseline. Annotates
  whether live capture was included.

Each YAML carries a `tolerance` block per M3 schema. Default tolerances
(operator may tighten per scenario):

| Metric                       | Default tolerance              |
|------------------------------|--------------------------------|
| `latency_p99_ms_delta_pct`   | +10% (v0.7.0 must not regress P99 by more than 10%) |
| `latency_p999_ms_delta_pct`  | +20%                            |
| `jain_delta_pct`             | -5% (v0.7.0 must not drop Jain by more than 5pp)  |
| `deadline_miss_delta_abs`    | 0.0 (must not increase deadline-miss rate)        |

Special-case tolerances:

- S4 (greedy starvation): baseline Jain expected ≪ 1. v0.7.0 target is
  IMPROVEMENT. Tolerance set as `jain_delta_pct: +30%` (v0.7.0 MUST
  improve Jain by ≥ 30% of the gap to 1.0).
- S11 (queue overflow): baseline likely shows aborted-for-safety. v0.7.0
  target is admission-control producing bounded queue. Tolerance:
  `heap_rss_bytes_max: 200MB` and `aborted_for_safety_allowed: false`.

### Operator review

The M9 PR description includes a per-scenario table summarizing baseline
numbers. Operator reviews and approves before squash-merge. After merge,
per AD06, these baselines are immutable until a v0.7.0 amendment
explicitly authorizes regeneration.

### `baselines/v0.6.99/README.md`

Documents:
- What each YAML represents.
- The capture procedure (so future regeneration is reproducible).
- The tolerance semantics.
- The AD06 immutability rule.

Acceptance: All 12 YAMLs committed (or 11 if S13 live capture absent —
synthetic-only S13 still counts). Operator-approved PR description.
Re-running `proxy-bench compare baselines/v0.6.99/<id>.yaml
results/<id>-rerun.yaml` reports PASS on a same-hardware re-run.

## M10 — CI Smoke Wiring + Soak Runner

Single PR. Deliverables:

### CI smoke wiring (`scripts/ci_local.sh`)

Append a `bench-smoke` step after existing steps:

```bash
# bench-smoke (v0.6.99): run S1-1client + S2-2client and diff against baselines
./cmd/proxy-bench/proxy-bench run test/bench/scenarios/S1.yaml \
    --busload 30 --duration 30s --seed 0x42 \
    --out /tmp/ci-bench-S1.yaml
./cmd/proxy-bench/proxy-bench compare \
    baselines/v0.6.99/S1.yaml /tmp/ci-bench-S1.yaml || exit 1
./cmd/proxy-bench/proxy-bench run test/bench/scenarios/S2.yaml \
    --clients 2 --duration 30s --seed 0x42 \
    --out /tmp/ci-bench-S2.yaml
./cmd/proxy-bench/proxy-bench compare \
    baselines/v0.6.99/S2.yaml /tmp/ci-bench-S2.yaml || exit 1
```

Total runtime budget for the smoke: < 90 seconds. Hard requirement per
plan-level acceptance (§8 of canonical, item 4).

### On-demand soak runner (`scripts/run-bench-soak.sh`)

```bash
#!/usr/bin/env bash
# S12: 24h soak at 30% busload, 3 clients. Run manually, not in CI.
set -euo pipefail
mkdir -p /tmp/soak-results
./cmd/proxy-bench/proxy-bench soak test/bench/scenarios/S12.yaml \
    --duration 24h --out /tmp/soak-results/S12-$(date +%F).yaml \
    --probe-interval 5m
# Acceptance probes:
# - goroutines_steady stays within ±20 of M0 measurement
# - heap_rss_bytes growth < 10MB over 24h
# - zero unrecoverable errors
```

Documented in `scripts/README.md`: when to run, what to watch for, expected
durations. Operator runs ad-hoc; results are not committed to the repo
(they accumulate in `/tmp/soak-results/` or operator's choice of path).

### `test/bench/scenarios/S12.yaml`

Already partially scaffolded in M5; M10 finalizes its parameters:
- 3 clients (mixed: 1 pollLoop, 1 adHoc, 1 writeAfterRead).
- 30% busload target.
- Probe-interval 5 minutes (pprof scrape every 5 min).
- No baseline YAML for S12 (soak results are too noisy for tolerance gating;
  they're trend-analysis instruments, not regression gates).

Acceptance: `./scripts/ci_local.sh` runs end-to-end in < 90s including
bench-smoke. `./scripts/run-bench-soak.sh --dry-run` exits clean. Operator
verifies the soak runs successfully for at least 2 hours as a sanity check
before signing off M10 (full 24h soak not required for merge — that's a
post-merge trend-tracking activity).

## Plan-Level Acceptance (mirrors §8 of canonical)

After M10 merges:

1. `baselines/v0.6.99/*.yaml` exists with golden SLOs for S1..S11 (and S13
   per AD08 outcome).
2. Operator tags `v0.6.99` against head of M10 merge.
3. `scripts/check_bit_identical.sh` passes against `v0.6.5` for every PR
   in M1..M10.
4. `scripts/ci_local.sh` < 90s with non-zero exit on baseline regression.
5. S1 re-run with same seed: latency P50/P95 within ±2% of baseline.

After tag, the v0.7.0 plan (separate cruise-plan run, not this one) can
begin.

## Risk Notes

- **Operator hardware variance**: baselines captured on one machine may not
  reproduce within ±2% on different hardware. Mitigation: baseline YAMLs
  include `captured_on:` metadata (CPU model, kernel, Go version);
  cross-machine comparisons widen tolerance per documented rule.
- **CI smoke false positives**: if the smoke step is flaky on busy CI
  hardware (timer skew, noisy neighbor), the 30s S1 + 30s S2 may not
  reproduce baseline. Mitigation: `proxy-bench compare` has a `--ci-tolerance-multiplier`
  flag (default 2.0) that doubles tolerance for the smoke run only.
  Operator-tunable.
- **S12 reaching 24h without supervision**: operator must verify the
  reference hardware can sustain the workload — RPi4 SD-card I/O is the
  most likely failure mode (heap/log-write contention). Mitigation: M10
  documents disk-space and journald rotation prereqs.
