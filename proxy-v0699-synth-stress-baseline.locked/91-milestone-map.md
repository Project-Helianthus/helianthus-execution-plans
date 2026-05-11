# Proxy v0.6.99 — Milestone DAG and Critical Path

Source: [00-canonical.md](./00-canonical.md)

## DAG

```
                         (external)
                       v0.6.5 tagged
                            │
                            ▼
                       ┌────────┐
                       │   M0   │ release anchor + bit-identical watchdog
                       └────┬───┘
                            ▼
                       ┌────────┐
                       │   M1   │ bussim + admin pprof
                       └─┬──┬───┘
                         │  │
              ┌──────────┘  └──────────┐
              ▼                        ▼
         ┌────────┐               ┌────────┐
         │   M2   │ fidelity-min  │   M3   │ schema + SLO YAML format
         └────┬───┘               └────┬───┘
              │                        ▼
              │                   ┌────────┐
              │                   │   M4   │ proxy-bench runner + S1
              │                   └────┬───┘
              │                        ▼
              │                   ┌────────┐
              │                   │   M5   │ workload profiles + S2..S6
              │                   └────┬───┘
              │                        ▼
              │                   ┌────────┐
              │                   │   M6   │ failure-injection + S7..S11
              │                   └────┬───┘
              │                        ▼
              │                   ┌────────┐
              └──────────────────►│   M7   │ collector + reporter
                                  └────┬───┘
                                       ▼
                                  ┌────────┐
                                  │   M8   │ pcap replay + S13
                                  └────┬───┘
                                       ▼
                                  ┌────────┐
                                  │   M9   │ baseline capture + commit
                                  └────┬───┘
                                       ▼
                                  ┌────────┐
                                  │  M10   │ CI smoke + soak runner
                                  └────┬───┘
                                       ▼
                                v0.6.99 release
                                       │
                                       ▼
                                  (v0.7.0 plan)
```

## Critical Path

`M0 → M1 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10`

Critical-path length: **10 milestones**. M2 is parallelizable with M3+M4
once M1 lands (both depend on M1; M2 also unblocks M8). The shortest
sequential execution touches every milestone because each later
milestone consumes the prior's deliverables.

## Parallelism Opportunities

- **M2 ∥ M3+M4**: After M1 merges, M2 (fidelity-min via fixtures) can be
  developed by one agent while M3+M4 (schema + runner + S1) are developed
  by another. Both rejoin at M7 (collector reads fixture-validated bussim)
  and M8 (replay consumes M2 fixtures).
- **M5 ∥ M6** within the scenarios stream: workload profiles (M5) and
  failure-injection wiring (M6) touch different files. M5 owns
  `test/bench/clients/*.go`; M6 owns `internal/emulation/bussim/inject.go`
  extensions and scenarios S7..S11. They may merge in either order; M7
  waits for both.
- **Per cruise-control**: parallel dispatch is allowed but requires
  cruise-dev-supervise to enforce `one-PR-per-repo-at-a-time` invariant.
  Since all milestones target the same repo, true parallel PRs are NOT
  allowed; dispatch order is M1 → (M2, M3+M4) sequentially-mergeable →
  M5 → M6 → M7 → M8 → M9 → M10.

## External Blockers

- **M0 → v0.6.5 tag**: M0 blocks until the separate v0.6.5 PR (operator's
  other thread) lands. AD09 specifies 72h escalation if not tagged within
  that window.
- **M8 → live pcap (best-effort)**: M8 has an OPTIONAL dependency on a
  live pcap capture from `192.168.100.4`. If operator does not provide
  one by M8 PR time, M8 ships with synthetic-only per AD08.
- **M9 → operator review**: M9 baseline capture PR requires explicit
  operator approval before squash-merge (per AD06 baseline immutability).

## Slip Risk Per Milestone

| Milestone | Slip risk | Notes |
|-----------|-----------|-------|
| M0  | medium    | Depends on v0.6.5 tag landing externally. |
| M1  | low       | Pure new code in a new package; existing ENH framing well-understood. |
| M2  | low       | Fixture format is internal; 5 fixtures minimum is small. |
| M3  | low       | Schema design; pure contract work. |
| M4  | medium    | First end-to-end integration; runner-vs-proxy-vs-bussim interaction surface. |
| M5  | medium    | 5 workload profiles each with non-trivial state machines. |
| M6  | medium    | Failure-injection interacts with bussim and scenario YAML; integration risk. |
| M7  | high      | Mutex-profile activation may be unsupported (per chunk 14 risk note); pprof scraper fragility. |
| M8  | medium    | Synthetic path is deterministic; live capture depends on operator. |
| M9  | medium    | Reproducibility within ±2% across machines is an empirical question. |
| M10 | low       | Append + new script; smallest deliverable. |

## Re-Plan Triggers

The plan is re-locked (amendment per `cruise-plan AMEND_PLAN`) if any of
these occur:

- v0.6.5 introduces a wire-protocol change that invalidates M1's framing
  assumptions.
- AD07 pprof wiring is rejected by Codex review or operator on second
  thought (would require a major re-design of M7).
- M2 fidelity-min reveals bussim cannot reproduce ENH framing
  deterministically (would require either ENH framing fixes — out of
  v0.6.99 scope — or a major bussim rearchitecture).
- Operator decides to add T2/T3 scaffolding to v0.6.99 scope (currently
  deferred to v0.7.0).
