# Issue Map — Runtime State File

Source: [00-canonical.md](./00-canonical.md)

Per-repo canonical issue identifiers. Each gets a real GitHub issue at
M0_PLAN_LOCK execution time; this map is the seed.

## Reconciled Completion Evidence

| Milestone | Disposition | Recorded merge evidence |
| --- | --- | --- |
| M0_PLAN_LOCK | merged | execution-plans PR #28 |
| M0_DOC_GATE | merged | docs-ebus PRs #304 and #305 |
| M0A_TRANSPORT_BASELINE | merged | gateway PR #610 |
| M1_TDD_RED_GATEWAY | merged | gateway PR #611 |
| M1_TDD_RED_ADDON | merged | ha-addon PR #126 |
| M2_GATEWAY_LOADER / M3_GATEWAY_PERSISTER | merged | gateway PR #612 |
| M4_SOURCE_SELECTION_HINT | merged | gateway PR #613 |
| M5_ADDRESS_TABLE_REVALIDATE | merged | gateway PRs #614 and #615 |
| M6_HA_ADDON_MIGRATION | merged | ha-addon PR #127 |
| M7_LIVE_VALIDATION | current | live validation remains nonterminal |
| M8_TRANSPORT_VERIFY | merged | gateway PR #616 |

## helianthus-execution-plans

- **RTS-PLAN-01** — Lock `runtime-state-w19-26.draft → .locked` (M0_PLAN_LOCK).
- **RTS-PLAN-02** — Append back-reference amendment to
  `instance-identity-rediscovery.maintenance/00-canonical.md` (AD21).

## helianthus-docs-ebus

- **RTS-DOC-01** — Author normative "Runtime State File" doc section.
- **RTS-DOC-02** — Ship `runtime_state.schema.json` artifact (Draft 2020-12).
- **RTS-DOC-03** — Add `make validate-schemas` target +
  `santhosh-tekuri/jsonschema/cmd/jv` CI step.
- **RTS-DOC-04** — Author ≥3 negative fixtures (out-of-range addr, invalid
  UUIDv4, missing required `meta.instance_guid`).
- **RTS-DOC-05** — Cross-link from
  `instance-identity-rediscovery` doc section.

## helianthus-ebusgateway

- **RTS-GW-00A** — Capture transport-matrix baseline (M0A).
- **RTS-GW-01** — RED tests: loader, persister, eager persist, ticker,
  EXDEV path, fault-injection, concurrent-write serialization (M1).
- **RTS-GW-02** — Loader implementation (M2).
- **RTS-GW-03** — Persister implementation per AD13 contract (M3).
- **RTS-GW-04** — SourceAddressSelector-hint integration + AD24 invariant test (M4).
- **RTS-GW-05** — Address-table revalidate burst + cap=32 + ordering +
  no-reply telemetry (M5).
- **RTS-GW-07** — Live validation P1..P6 + N1..N4 (M7).
- **RTS-GW-08** — Transport-matrix verify vs M0A baseline (M8).

## helianthus-ha-addon

- **RTS-ADDON-01** — RED tests: AD09b 5 precedence cases, AD09a halt,
  AD27 flag, AD26 ENOENT retry (M1_TDD_RED_ADDON).
- **RTS-ADDON-06** — Migration implementation: AD09a/b/27 + ENOENT retry +
  stop writing legacy file + Supervisor restart-loop CPU-budget test (M6).

## Cross-plan amendments

- **RTS-AMENDMENT-01** — One-paragraph back-ref appended to
  `instance-identity-rediscovery.maintenance/00-canonical.md` documenting
  file-path migration (AD21). Bundled with RTS-PLAN-01 PR.
