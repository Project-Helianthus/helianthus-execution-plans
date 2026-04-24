# Issue Map

This plan uses canonical issue identifiers. GitHub issue and PR
linkage is backfilled as it lands. Canonical IDs remain the stable
mapping surface for the workstream.

Status legend:
- `planned`: defined in the locked plan, not yet started
- `queued`: waiting on an earlier milestone or prerequisite
- `merged`: landed on main via squash; squash SHA is stable merge
  reference
- `final`: last milestone in its lane; plan seals after all `final`
  entries merge

## Docs Gate (M0)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-DOC-SAD-00` | `helianthus-docs-ebus` | Startup Admission + Discovery Pipeline normative docs; cross-links from nm-model/nm-discovery/nm-participant-policy; degraded-mode surface; operator override docs; startup ordering contract; Discovery-Class Burst Budget subsection; Evidence buffer retention + rejoin backoff; admission-artifact JSON schema key-path listing (AD23) | planned | TBD |

## ebusreg (M1)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-EBUSREG-SAD-01` | `helianthus-ebusreg` | Directed scan API (`ScanDirected`/`ScanOptions{Mode,Targets}`) with non-empty-targets contract + snapshot/golden test pinning `Scan(ctx, bus, reg, source, nil)` + ebusd-tcp sanctioned bounded-retry exercise | planned | TBD |

## ebusgateway (M2..M7 — stacked PRs per AD14 operator-blessed multi-PR exception)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `ISSUE-GW-SAD-M2` | `helianthus-ebusgateway` | JoinBus adapter + transport classifier + 5s warmup observation integration test + AD22 config-load FATAL invariant unit test | planned | TBD |
| `ISSUE-GW-SAD-M2a` | `helianthus-ebusgateway` | Offline admission+discovery test harness (admission FSM, degraded-mode transitions, evidence promotion, override paths Validate=true/false, semanticBarrier predicate); schema validation against AD23-frozen `admission-artifact.schema.json`; CI check on override-stub alignment with M6 | planned | TBD |
| `ISSUE-GW-SAD-M3` | `helianthus-ebusgateway` | Startup order flip + semanticBarrier predicate extension in `cmd/gateway/main.go` (signal-source gate per AD16); warmup-before-active-frame invariant with override carve-out | planned | TBD |
| `ISSUE-GW-SAD-M4` | `helianthus-ebusgateway` | Evidence pipeline with `max_entries=128` LRU + baseline-topology-protection; rejoin backoff Base=5s Max=60s; degraded-mode escalation K=5/T=5min with `fixed_bucket_1s` 900-slot ring buffer (AD17); flood-test for default + non-default seeds | planned | TBD |
| `ISSUE-GW-SAD-M5` | `helianthus-ebusgateway` | Degraded-mode surfaces (11 expvars) + additive `bus_admission` field in `ebus.v1.bus_observability` data body (AD08); state-stability window 30s; dual enum enforcement (runtime FATAL + CI schema) | planned | TBD |
| `ISSUE-GW-SAD-M6` | `helianthus-ebusgateway` | Operator override wiring (StartupSource.Override + .Validate) with (c2)+(i) semantics; retrospective conflict detection at t≈5s; full-range retry guard on non-ebusd-tcp; regression test for `registry.Scan(nil/empty)` | planned | TBD |
| `ISSUE-GW-SAD-M7` | `helianthus-ebusgateway` | Integration acceptance artifact emission + live-bus 5-min evidence window (ens-tcp @ 192.168.100.2 baseline); transport-gate evidence YAML with 11 required fields; CI JSON-schema validation | planned | final |

## Execution-plans repo (plan-lock commit)

| Canonical ID | Repo | Summary | Status | Linked execution |
| --- | --- | --- | --- | --- |
| `PLAN-LOCK-SAD-W17-26` | `helianthus-execution-plans` | Plan-lock commit: rename `<slug>.draft/` → `<slug>.locked/` + one-line back-reference in `ebus-good-citizen-network-management.maintenance/11-runtime-discovery-and-policy.md` under ISSUE-GW-JOIN-01 (AD19) | planned | TBD |
