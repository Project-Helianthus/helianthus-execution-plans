# Proxy v0.6.99 Synthetic & Stress-Test Baseline — Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

This directory contains the canonical Proxy v0.6.99 plan plus a lossless,
execution-oriented split into reviewable chunks. The split exists so Opus,
Sonnet, Codex, and implementation agents can attack bounded pieces without
losing the source contract.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk stays below `10000` tokens on both the GPT-5-family tokenizer
  (`o200k_base`) and the Claude tokenizer.
- Each chunk is reviewable in isolation and repeats:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is lossless except for deliberate dependency repetition needed for
  isolated review.
- Drift detection is explicit: every chunk and this index carry the canonical
  hash of `00-canonical.md`.

## Sequencing Rules

- The milestone order is `M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7 -> M8 -> M9 -> M10`.
- Codex R1 review reordered M3 (metric schema) **before** M4..M6 (scenarios)
  because scenarios without metrics are unfalsifiable harness demos.
- M2 (simulator fidelity-min via golden fixtures) gates M4..M7 because all
  measurements after M2 trust bussim by construction. M8 (full pcap replay)
  is the late-stage realism check.
- Locked decisions in the canonical plan (`AD01..AD10`) override milestone
  shorthand if drift appears between this split and the canonical source.

## Chunk Map

1. [`10-foundations.md`](./10-foundations.md)
   Covers the measurement-only invariant, decision matrix `AD01..AD10`,
   doc-gate classification per milestone, transport-gate non-trigger.
2. [`11-anchor-and-sim.md`](./11-anchor-and-sim.md)
   Covers `M0` release anchor + bit-identical watchdog, `M1` bussim package
   (framing + scripted devices + admin pprof wiring), `M2` simulator
   fidelity-min via golden synthetic fixtures.
3. [`12-schema-and-runner.md`](./12-schema-and-runner.md)
   Covers `M3` metric schema + golden SLO YAML format, `M4` proxy-bench runner
   binary + first scenario `S1` single-client-baseline.
4. [`13-scenarios-and-failures.md`](./13-scenarios-and-failures.md)
   Covers `M5` workload profiles (`pollLoop`, `scanBurst`, `writeAfterRead`,
   `adHoc`, `greedy`, `slowConsumer`) + multi-client scenarios `S2..S6`, and
   `M6` failure-injection primitives + scenarios `S7..S11`.
5. [`14-collector-and-replay.md`](./14-collector-and-replay.md)
   Covers `M7` metrics collector + report generator (per-client / wire-side /
   pprof-side), and `M8` pcap replay + `S13` synthetic-vs-live fidelity check.
6. [`15-baseline-and-ci.md`](./15-baseline-and-ci.md)
   Covers `M9` baseline capture + commit `baselines/v0.6.99/*.yaml`, and `M10`
   CI smoke wiring + on-demand soak runner `S12`.

## Coverage Matrix

| Source range                                | Destination chunk                       |
| ------------------------------------------- | --------------------------------------- |
| §0 Summary; §1 Central Invariant; §2 AD01..AD10; §3 Doc-Gate | `10-foundations.md` |
| §4 Architecture; §7 milestones M0..M2       | `11-anchor-and-sim.md`                  |
| §7 milestones M3..M4; §6 metrics map        | `12-schema-and-runner.md`               |
| §5 scenarios S2..S11; §7 milestones M5..M6  | `13-scenarios-and-failures.md`          |
| §7 milestones M7..M8; AD08 outcome path     | `14-collector-and-replay.md`            |
| §7 milestones M9..M10; §8 acceptance        | `15-baseline-and-ci.md`                 |
| §9 Looking ahead to v0.7.0                  | `10-foundations.md` (referenced)        |

## Adjacent Maps

- [`90-issue-map.md`](./90-issue-map.md) — mapping from milestones to per-repo
  GitHub issues (filled in as M0..M10 issues are created in
  `helianthus-ebus-adapter-proxy`).
- [`91-milestone-map.md`](./91-milestone-map.md) — DAG of milestone
  dependencies + critical-path notes.
- [`99-status.md`](./99-status.md) — live progress: current milestone,
  blocked-on, last PR.
