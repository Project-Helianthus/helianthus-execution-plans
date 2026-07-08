# Issue Map

Status: `Draft`
Baseline: `Gateway 0.4.0`

This map is the intended issue shape for promotion. M0/M1 seed issues and PRs
may already be linked in `92-m0-issue-matrix.yaml`; later issues are filed only
when predecessor gates are accepted and one-active-PR-per-repo serialization
allows them.

## Model Lane Key

- `spark`: `GPT-5.3-Codex-Spark`
- `mini`: `gpt-5.4-mini`
- `55m`: `GPT-5.5 medium`
- `55h`: `GPT-5.5 high`
- `55x`: `GPT-5.5 xhigh`

## Draft Issues

| Draft ID | Repo | Milestone | Cx | Lane | Depends on | Gate focus | What |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| MSP-00A | helianthus-execution-plans | M0 | 3 | mini | none | control | Create issue matrix with repo serialization, predecessor edges, doc owner, gates, rollback, and review ledger fields. |
| MSP-00B | helianthus-execution-plans | M0 | 4 | mini | MSP-00A | control | Define model routing exactly as Spark / 5.4-mini / 5.5 medium / 5.5 high / 5.5 xhigh. |
| MSP-00C | helianthus-execution-plans | M0 | 5 | 55m | MSP-00A | transport | Define `eebus-transport-gate v0` and eBUS T01..T88 applicability rule. |
| MSP-01A | helianthus-docs-ebus | M1 | 4 | mini | MSP-00A | doc | Add `docs/platform/...` ownership and transition ADR. |
| MSP-01B | helianthus-docs-eebus | M1 | 4 | mini | MSP-01A | doc | Bootstrap `helianthus-docs-eebus` with eeBUS-native-only scope. |
| MSP-01C | helianthus-docs-eebus | M1 | 5 | 55m | MSP-01A, MSP-01B | doc/security | Add provenance, publication, restricted-source quarantine, and summary-only page policy. |
| MSP-020 | helianthus-eebusreg | M2 | 4 | mini | MSP-00A, MSP-00B, MSP-00C, MSP-01A, MSP-01B, MSP-01C | repo | Bootstrap `helianthus-eebusreg` as a raw runtime/evidence module with CI and boundary gates. |
| MSP-02A | helianthus-eebusreg | M2 | 6 | 55h | MSP-00A, MSP-00B, MSP-00C, MSP-01A, MSP-01B, MSP-01C, MSP-020 | doc/security | Draft versioned, reviewable raw runtime identity contract and unknown-field/redaction policy. |
| MSP-02B | helianthus-eebusreg | M2 | 7 | 55h | MSP-02A | mcp | Draft snapshot envelope, evidence object, and hash/replay rules. |
| MSP-02C | helianthus-docs-ebus | M2 | 6 | 55h | MSP-01A, MSP-02B | doc | Draft raw correlation policy and Leaf Promotion Dossier template. |
| MSP-03A | helianthus-eebusreg | M3 | 8 | 55x | MSP-02C | toolchain | Spike internal facade against pinned `enbility/eebus-go v0.7.0`. |
| MSP-03B | helianthus-eebusreg | M3 | 8 | 55x | MSP-03A | toolchain | Prove local and actual build-container module/toolchain boundaries. |
| MSP-03C | helianthus-ha-addon | M3 | 9 | 55x | MSP-03A, MSP-03B | transport/security | Prove HA runtime LAN-side networking, mDNS/Avahi/DBus cases, manual endpoint, and proof credential persistence. |
| MSP-03D | helianthus-eebusreg | M3 | 9 | 55x | MSP-03C | transport | Run independent black-box fake peer and live VR940f smoke. |
| MSP-035 | helianthus-eebusreg | M3.5 | 8 | 55x | MSP-03D | mcp | Freeze raw identity, raw snapshot envelope, and evidence object shape only. |
| MSP-04A | helianthus-eebusreg | M4 | 8 | 55x | MSP-035 | security | Implement production trust states and hardened `/data/eebus` store. |
| MSP-04B | helianthus-eebusreg | M4 | 9 | 55x | MSP-04A | security | Implement first-trust, admin-local boundary, listener gating, and redaction. |
| MSP-04C | helianthus-eebusreg | M4 | 8 | 55x | MSP-04B | security | Implement backup/restore/rollback, revocation tombstones, quarantine/backoff, and repair flows. |
| MSP-045 | helianthus-eebusreg | M4.5 | 8 | 55x | MSP-04C | security/mcp | Freeze trust, pairing, admin-local, restore, and quarantine state model. |
| MSP-05A | helianthus-ebusgateway | M5 | 4 | mini | MSP-045 | config | Add disabled-by-default eeBUS config scaffold with no runtime import. |
| MSP-05B | helianthus-ebusgateway | M5 | 9 | 55x | MSP-05A, MSP-045 | transport/security | Add `EEBusRuntimeAdapter` sidecar integration without touching eBUS transport/router/registry behavior. |
| MSP-06 | helianthus-ebusgateway | M6 | 9 | 55x | MSP-05B | mcp/security | Add read-only deterministic `eebus.v1.*` MCP tools and anti-leak tests. |
| MSP-065 | helianthus-ebusgateway | M6.5 | 8 | 55x | MSP-06 | evidence | Add synchronized evidence recorder using existing read-only eBUS surfaces only. |
| MSP-07 | helianthus-ebusgateway | M7 | 8 | 55x | MSP-065 | semantic-candidate | Add draft candidate fact graph with no promotion or consumer exposure. |
| MSP-08 | helianthus-ebusgateway | M8 | 10 | 55x | MSP-07 | coexistence | Prove eBUS and eeBUS coexistence with separate raw surfaces and no consumer drift. |
| MSP-085 | helianthus-ebusgateway | M8.5 | 9 | 55x | MSP-08 | promotion | Lock per-leaf promotion dossiers after coexistence evidence. |
| MSP-09A | helianthus-ebusgateway | M9 | 8 | 55x | MSP-085 | graphql | Add GraphQL only for promoted leaves. |
| MSP-09B | helianthus-ebusgateway | M9 | 7 | 55h | MSP-09A | portal | Add Portal workbench/promoted-leaf display after GraphQL. |
| MSP-09C | helianthus-ha-integration | M9 | 8 | 55x | MSP-09A, MSP-09B | ha | Add HA support only for promoted leaves. |
| MSP-09D | helianthus-ha-addon | M9 | 6 | 55h | MSP-09A, MSP-09C | ha/security | Add add-on config/persistence exposure for promoted eeBUS runtime only. |

## Accepted Issue Links

| Draft ID | Repo | Issue | PR | Merge commit |
| --- | --- | --- | --- | --- |
| MSP-00A/MSP-00B/MSP-00C | `helianthus-execution-plans` | [#33](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/33), [#32](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/32), [#34](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/34) | [#35](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/35), [#37](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/37) | `2860d742e2682fbc42d1a5d98906031a0ff3e45d`, `93ef8cebadf842ebdffb5f3a0eb34806d5766ff5` |
| MSP-01A | `helianthus-docs-ebus` | [#333](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/333) | [#334](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/334) | `55f5482e0513ceb3bed8ddd5f2656d3b3ae7be41` |
| MSP-01B/MSP-01C | `helianthus-docs-eebus` | [#1](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/3) | `9d3637e09d9573d9d7f31bdda86b1039770ba41b` |
| MSP-020 | `helianthus-eebusreg` | [#1](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/3) | `f441e4a1987f775367ad3046e68ba1caf04b2f20` |
| MSP-02A | `helianthus-eebusreg` | [#4](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/4) | [#5](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/5) | `28d2f8162b67ea274c089ed1686c9ce84b054e7d` |
| MSP-02B | `helianthus-eebusreg` | [#6](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/6) | [#7](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/7) | `c064c0d1d19cd0c392734bede136f55040b76c67` |
| MSP-02C | `helianthus-docs-ebus` | [#335](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/335) | [#336](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/336) | `70a4921f287116f539cb4ce522ee9809cd9bf3c6` |

## Mandatory Per-Issue Checklist

Every future issue must include:

- What
- Why
- Acceptance Criteria
- Dependencies
- Complexity and model lane
- Repo serialization note
- Doc-gate status and canonical doc owner
- Transport/security gate applicability
- Rollback plan
- Review ledger

## Hard Blockers

- No implementation starts before MSP-00A/B/C are complete.
- No public docs may cite `vendor_restricted` content.
- No `helianthus-eebusreg` runtime contract issue starts before MSP-020
  establishes the raw runtime/evidence repo boundary.
- No gateway import of `helianthus-eebusreg` lands before MSP-03D and MSP-035.
- No MCP v1 lands before MSP-045.
- No consumer work lands before MSP-085.
