# Issue Map

Status: `Locked`
Baseline: `Gateway 0.4.0`
Current milestone: `M5_PRODUCTION_PREREQUISITES`
Accepted through: `MSP-05A with M4.5 trust and admin state frozen`
Successor unlocks: `only through the corrected production-prerequisite chain`
Amendment: `MSP-05B production-prerequisite correction`

This map preserves historical evidence and records the M5B preflight NO-GO.
Runtime activation proceeds through the matrix-defined production prerequisites,
with one active PR per repo and one `helianthus-eebusreg` PR at a time.

## Active Control Surface

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.
This page deliberately does not duplicate active routing contracts, provider or
model selections, or completion-token edges. The live matrix is the only
source that can authorize a successor; its 107 audit is a deterministic,
complete projection for review.

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

- Direct `MSP-05B` dispatch is forbidden while the protected-material provider
  and scoped SHIP service remain production stubs.
- Gateway configuration must not silently ignore, collapse, or alias interface,
  subnet, certificate, key, trust-store, state-root, discovery, or pairing policy.
- The sole ready row is `MSP-05P-REG-API-V1-CLEANUP`; the complete prerequisite chain is
  authoritative only in the matrix and its deterministic topology audit.

## AD-DOCS-02 token chain

The matrix requires `MSP-DOCS-CLEAN` and `MSP-03C` completion tokens for
`MSP-03D-R`; `MSP-03D-G01` is evidence-only. Completion tokens, not historical
observations, authorize every active edge.

- No publication of MSP-R00 private details: local SHA, private path, raw HMAC
  mapping, source-bundle detail, raw paths, volume, sizes, timestamps, bytes,
  deterministic IDs, raw hashes, or sensitive evidence.
- No runtime successor unlock from dirty code existence.
- No public artifact may contain packet captures, raw transcripts, keys, PEM,
  tokens, trust stores, raw SKI, raw SHIPID, raw IP/MAC address, or raw serial.
- No `helianthus-eebusreg/docs/` on clean main and no substantive code-repo
  protocol, architecture, API, harness, test, or user documentation.
- No gateway import before canonical docs and eebusreg contracts merge.
- No GraphQL, Portal, HA, command routing, raw writes, or promoted semantics
  before the later milestone and per-leaf lock.
