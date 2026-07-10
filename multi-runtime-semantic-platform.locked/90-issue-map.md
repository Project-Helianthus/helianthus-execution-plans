# Issue Map

Status: `Locked`
Baseline: `Gateway 0.4.0`
Current milestone: `RECOVERY_RECONCILIATION`
Accepted through: `MSP-03C plus merged MSP-03D EEBUS-G01 fake-peer harness only`
Successor unlocks: `false until MSP-R00 and MSP-03D-R merge from clean main`

This map preserves historical evidence without treating dirty rescue code as
accepted. Future runtime work resumes from clean main, with one active PR per
repo and one `helianthus-eebusreg` PR at a time.

## Model Lane Key

- complexity 1-2: `GPT-5.3-Codex-Spark`
- complexity 3-4: `gpt-5.4-mini`
- complexity 5: `GPT-5.5 medium`
- complexity 6-7: `GPT-5.5 high`
- complexity 8-10: `GPT-5.5 xhigh`

## Locked Rows

| ID | Repo | Milestone | Cx | Model lane | Depends on | Gate focus | What |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| MSP-R00 | helianthus-eebusreg | RECOVERY_RECONCILIATION | 5 | GPT-5.5 medium | none | recovery/security | Secret scan, synthetic fixtures, local never-pushed rescue branch, source-only forensic WIP commit and bundle SHA-256; publish only a redacted companion ledger in execution-plans. |
| DOCS-VERIFY | helianthus-docs-eebus | RECOVERY_RECONCILIATION | 4 | gpt-5.4-mini | none | doc | Verify license, canonical owners, issue template, path layout, and docs-eebus cross-seeding to docs-ebus. |
| MSP-03D-R | helianthus-eebusreg | M3 | 9 | GPT-5.5 xhigh | MSP-R00, DOCS-VERIFY, MSP-03C, MSP-03D-G01 | transport/security | Clean-main G17+G19 harness and canonical recovery evidence. |
| MSP-035 | helianthus-eebusreg | M3.5 | 8 | GPT-5.5 xhigh | MSP-03D-R | raw-contract | Freeze raw identity, snapshot envelope, and evidence object only. |
| MSP-04A | helianthus-eebusreg | M4 | 8 | GPT-5.5 xhigh | MSP-035 | store/security | Internal persistent store/schema only. |
| MSP-036 | helianthus-eebusreg | M3.6 | 8 | GPT-5.5 xhigh | MSP-04A | raw-view | Public immutable raw snapshot/view only; no lifecycle, trust, semantic ID, or availability authority. |
| MSP-055 | helianthus-eebusreg | M5.5 | 9 | GPT-5.5 xhigh | MSP-036 | lifecycle/security | Disabled-by-default read-only lifecycle facade with explicit config plus pre-seeded trust/allowlist. |
| MSP-04B | helianthus-eebusreg | M4 | 9 | GPT-5.5 xhigh | MSP-055 | security | First-trust, OOB confirmation, admin-local boundary, and no public trust mutation. |
| MSP-04C | helianthus-eebusreg | M4 | 8 | GPT-5.5 xhigh | MSP-04B | security | Restore, revocation, quarantine, repair, and rollback semantics. |
| MSP-045 | helianthus-eebusreg | M4.5 | 8 | GPT-5.5 xhigh | MSP-04C | security/contract | Freeze trust, pairing, admin-local, restore, and quarantine state model. |
| MSP-05A | helianthus-ebusgateway | M5 | 4 | gpt-5.4-mini | MSP-045 | config | Disabled eeBUS config scaffold; no runtime import. |
| MSP-05B | helianthus-ebusgateway | M5 | 9 | GPT-5.5 xhigh | MSP-05A, MSP-045 | gateway/security | Disabled-by-default `EEBusRuntimeAdapter` sidecar after canonical docs and eebusreg contracts merge. |
| MSP-06 | helianthus-ebusgateway | M6 | 9 | GPT-5.5 xhigh | MSP-05B | mcp/security | Read-only deterministic `eebus.v1.*` MCP tools and anti-leak tests. |
| MSP-065 | helianthus-ebusgateway | M6.5 | 8 | GPT-5.5 xhigh | MSP-06 | evidence | Synchronized evidence recorder using existing read-only eBUS surfaces only. |
| MSP-07 | helianthus-ebusgateway | M7 | 8 | GPT-5.5 xhigh | MSP-065 | semantic-candidate | Draft candidate fact graph only. |
| MSP-08 | helianthus-ebusgateway | M8 | 10 | GPT-5.5 xhigh | MSP-07 | coexistence | eBUS and eeBUS coexistence with no consumer drift. |
| MSP-085 | helianthus-ebusgateway | M8.5 | 9 | GPT-5.5 xhigh | MSP-08 | promotion | Per-leaf promotion dossiers locked after coexistence evidence. |
| MSP-09A | helianthus-ebusgateway | M9 | 8 | GPT-5.5 xhigh | MSP-085 | graphql | GraphQL only for promoted leaves. |
| MSP-09B | helianthus-ebusgateway | M9 | 7 | GPT-5.5 high | MSP-09A | portal | Portal support after GraphQL, without treating candidate/conflict/withheld as stable. |
| MSP-09C | helianthus-ha-integration | M9 | 8 | GPT-5.5 xhigh | MSP-09A, MSP-09B | ha | Home Assistant support only for promoted leaves. |
| MSP-09D | helianthus-ha-addon | M9 | 6 | GPT-5.5 high | MSP-09A, MSP-09C | ha/security | Add-on exposure for promoted runtime only, disabled by default. |

## Historical Accepted Evidence

| ID | Repo | Issue | PR | Merge commit | Acceptance state |
| --- | --- | --- | --- | --- | --- |
| MSP-00A/MSP-00B/MSP-00C | `helianthus-execution-plans` | [#33](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/33), [#32](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/32), [#34](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/34) | [#35](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/35), [#37](https://github.com/Project-Helianthus/helianthus-execution-plans/pull/37) | `2860d742e2682fbc42d1a5d98906031a0ff3e45d`, `93ef8cebadf842ebdffb5f3a0eb34806d5766ff5` | accepted |
| MSP-01A | `helianthus-docs-ebus` | [#333](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/333) | [#334](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/334) | `55f5482e0513ceb3bed8ddd5f2656d3b3ae7be41` | accepted |
| MSP-01B/MSP-01C | `helianthus-docs-eebus` | [#1](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-docs-eebus/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-docs-eebus/pull/3) | `9d3637e09d9573d9d7f31bdda86b1039770ba41b` | accepted |
| MSP-020 | `helianthus-eebusreg` | [#1](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/1), [#2](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/2) | [#3](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/3) | `f441e4a1987f775367ad3046e68ba1caf04b2f20` | accepted |
| MSP-02A | `helianthus-eebusreg` | [#4](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/4) | [#5](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/5) | `28d2f8162b67ea274c089ed1686c9ce84b054e7d` | accepted |
| MSP-02B | `helianthus-eebusreg` | [#6](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/6) | [#7](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/7) | `c064c0d1d19cd0c392734bede136f55040b76c67` | accepted |
| MSP-02C | `helianthus-docs-ebus` | [#335](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/335) | [#336](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/336) | `70a4921f287116f539cb4ce522ee9809cd9bf3c6` | accepted |
| MSP-03A | `helianthus-eebusreg` | [#8](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/8) | [#9](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/9) | `2b5b06315bd873dc214f602e9c5e9d0d6922208b` | accepted |
| MSP-03B | `helianthus-eebusreg` | [#10](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/10) | [#11](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/11) | `82f8f3cfd42d8e5c830d1e8e4e9e029614c14a7e` | accepted |
| MSP-03C | `helianthus-ha-addon` | [#166](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/166), [execution-plans #48](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/48) | [#167](https://github.com/Project-Helianthus/helianthus-ha-addon/pull/167) | `b3c9930ca244dfe636f79356b8d482c6c84e043c` | accepted |
| MSP-03C doc-gate | `helianthus-docs-ebus` | [#337](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/337) | [#338](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/338) | `c1fc6bde5a273fdd1ccbe1826479769fe0731a71` | accepted |
| MSP-03D-G01 | `helianthus-eebusreg` | [#12](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/12), [execution-plans #50](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/50) | [#13](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/13) | `0e58327dfdb86ef243a19e18d590564813feaa00` | EEBUS-G01 fake peer accepted only; MSP-03D and M3 remain open |

## Hard Blockers

- No recovery mutation before MSP-R00 preflight is fully green.
- No runtime successor unlock from dirty code existence.
- No public artifact may contain packet captures, raw transcripts, keys, PEM,
  tokens, trust stores, raw SKI, raw SHIPID, raw IP/MAC address, or raw serial.
- No gateway import before canonical docs and eebusreg contracts merge.
- No GraphQL, Portal, HA, command routing, raw writes, or promoted semantics
  before the later milestone and per-leaf lock.
