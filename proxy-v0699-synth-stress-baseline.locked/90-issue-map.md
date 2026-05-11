# Proxy v0.6.99 — Issue Map

Source: [00-canonical.md](./00-canonical.md)

This file maps each milestone to its per-repo GitHub issue. Per AGENTS.md
`one-issue-per-repo-per-milestone` invariant, every milestone gets ONE
issue in `helianthus-ebus-adapter-proxy` (the single target repo for this
plan). The meta-issue lives in `helianthus-execution-plans`.

The table is filled in by `cruise-preflight` / `cruise-dev-supervise` as
each milestone reaches the dispatch phase. Entries are immutable once a PR
is opened.

## Meta-Issue

| Repo                            | Issue | Title                                                    |
|---------------------------------|-------|----------------------------------------------------------|
| helianthus-execution-plans      | _TBD_ | meta: proxy v0.6.99 — synthetic & stress-test baseline   |

## Milestone Issues (target repo: `helianthus-ebus-adapter-proxy`)

| Milestone | Issue | PR    | Status   | Notes |
|-----------|-------|-------|----------|-------|
| M0  release-anchor + bit-identical watchdog              | _TBD_ | _TBD_ | pending  | Blocks on `v0.6.5` tag landing. |
| M1  bussim package + admin pprof wiring                  | _TBD_ | _TBD_ | pending  | Depends on M0. AD07 wiring lives here. |
| M2  simulator fidelity-min (golden synthetic fixtures)   | _TBD_ | _TBD_ | pending  | Depends on M1. AD08 synthetic-mandatory. |
| M3  metric schema + golden SLO YAML format               | _TBD_ | _TBD_ | pending  | Depends on M1 (admin pprof for `MuxInternals` shape). |
| M4  proxy-bench runner + S1 single-client baseline       | _TBD_ | _TBD_ | pending  | Depends on M3. Smallest end-to-end loop. |
| M5  workload profiles + multi-client scenarios S2..S6    | _TBD_ | _TBD_ | pending  | Depends on M4. |
| M6  failure-injection primitives + scenarios S7..S11     | _TBD_ | _TBD_ | pending  | Depends on M5. |
| M7  metrics collector + report generator                 | _TBD_ | _TBD_ | pending  | Depends on M5, M6 (collector consumes their data sources). |
| M8  pcap replay + S13 fidelity                           | _TBD_ | _TBD_ | pending  | Depends on M2 (synthetic fixtures), M7 (report integration). AD08 best-effort live capture. |
| M9  baseline capture + commit `baselines/v0.6.99/*.yaml` | _TBD_ | _TBD_ | pending  | Depends on M1..M8. Requires operator review. |
| M10 CI smoke wiring + soak runner (S12)                  | _TBD_ | _TBD_ | pending  | Depends on M9 (baselines exist to diff against). |

## Doc-Gate Companion Issues (conditional)

| Trigger milestone | Repo                  | Issue | PR    | Status  | Notes |
|-------------------|-----------------------|-------|-------|---------|-------|
| M1                | helianthus-docs-ebus  | _TBD_ | _TBD_ | pending | bussim device-table RE knowledge doc. |
| M8 (conditional)  | helianthus-docs-ebus  | _TBD_ | _TBD_ | pending | Only if live pcap is captured AND its topology references warrant cross-product note. |

## Issue Lifecycle

- Created by `cruise-preflight` after routing decision.
- Title format: `proxy-v0699-<slug>: <milestone-id> <short-description>`.
- Body links back to this meta-issue and the canonical plan chunk.
- Closed by the merging PR (`Closes #N` in PR body).
