# W31/26 M6.25 SPINE 1.3 Completion

Date: `2026-07-30`
Status: `Published completion reconciliation`
Depends on: `123-w31-26-m625-spine-13-erratum.md`

`92-m0-issue-matrix.yaml` records dependency guidance. Current readiness comes
from GitHub and the owning code repositories.

This record is additive. Records 100 through 123 remain historical;
`100-topology-audit.md` remains a historical snapshot.
The base LAB control remains exactly
`lab_release_proof=released_chain_redeployed`. S13 completion is represented by
the independent `s13_completion_proof=published_evidence_verified` control.

## Current Control

<!-- M625_RELEASE_PROJECTION_BEGIN -->
Release-proof control: `released_chain_redeployed`
S13 completion proof: `published_evidence_verified`
Cruise phase: `MSP-065-LIVE-R1`
Current milestone: `MSP-065-LIVE-R1`
LAB acceptance state: `accepted`
Selected batch: `MSP-065-LIVE-R1`
Accepted through: `M6.25 stable MCP and the bounded SPINE 1.3 erratum are accepted after released-chain redeploy, live 49-READ non-regression, and restart-persistence proof; zero promoted leaves`
<!-- M625_RELEASE_PROJECTION_END -->

The existing completion-token graph is unchanged. In particular,
`MSP-065-LIVE-R1` still requires, in order, `MSP-0625-LAB`,
`MSP-0625-DOCS-P`, and `MSP-0625-S13-GW-LAB`. This reconciliation only records
that the final S13 predecessor now has published completion evidence.

## Published Release Chain

| Milestone | Issue | Pull request | Published commit | Green canonical CI |
| --- | --- | --- | --- | --- |
| `MSP-0625-S13-DOCS` | `Project-Helianthus/helianthus-docs-eebus#96` | `Project-Helianthus/helianthus-docs-eebus#97` | `b9166d68ac0fd063598e5f0e8d8f8c941e56aa15` | `30499461902` |
| `MSP-0625-S13-SPINE` | `Project-Helianthus/helianthus-spine-go#15` | `Project-Helianthus/helianthus-spine-go#16` | `5db11e32ca673fad3fc0d8f8a318615e96e0873d` | `30499509829` |
| `MSP-0625-S13-EEBUS` | `Project-Helianthus/helianthus-eebus-go#23` | `Project-Helianthus/helianthus-eebus-go#24` | `3c13e51aa114627ec6e129c73527cc04cbabcf17` | `30500565485` |
| `MSP-0625-S13-REG` | `Project-Helianthus/helianthus-eebusreg#103` | `Project-Helianthus/helianthus-eebusreg#104` | `bff5f9e5cbc875a488028a94a741218cb54c8adf` | `30501630742` |
| `MSP-0625-S13-GW-LAB` | `Project-Helianthus/helianthus-ebusgateway#762` | `Project-Helianthus/helianthus-ebusgateway#763` | `1a02388170a1ee6befeed1529956a7104aa94e21` | `30502756714` |

The tagged dependency closure is:

- SPINE `v0.7.1-helianthus.8`, annotated tag object
  `90cc7e1e68d2951577a2199d06e2dea4bc695c56`;
- eebus-go `v0.7.1-helianthus.12`, annotated tag object
  `c972309a0aa422c53939cf88a74ed4c56b9d2681`;
- eebusreg `v0.1.26`, annotated tag object
  `d8665381a82b28eea04373ce1ad64586d9064911`.

The deployed gateway binary is bound to SHA-256
`cb7b8ff8ad2e18b497132fa8fe2a5093963c4616f7e8bfe9fe1cf89fdc433fd6`
and the exact gateway merge above.

## Live Read-Only Acceptance

The public acceptance receipt is:

`https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/762#issuecomment-5125059807`

| Metric | Before | After |
| --- | ---: | ---: |
| Declared READ targets | 49 | 49 |
| Success | 26 | 41 |
| Failure | 23 | 8 |
| `internal` | 6 | 0 |
| `decode_error` | 13 | 4 |
| `disconnected` | 4 | 4 |

All 26 baseline successes remained successful, with zero regressions. Fifteen
READs recovered, including all bounded HVAC-description, HVAC-relation, and
setpoint-description targets. The remaining failures are four unavailable
local-source reads and four typed-empty replies. No HVAC or setpoint erratum
target remains failed. Every attempted operation was READ; WRITE, SET,
rollback-dispatch, and mutation probes remained zero.

Public-safe evidence commitments are:

| Evidence | SHA-256 |
| --- | --- |
| Immutable target set | `00cd8388b5f384c0d77a56c2de59045f0514759f115c05a44544f7abbee3aa43` |
| After result table | `705cd691da1a54f321f644202b913b930e8c6442fa49986e1afb436cb89c0e4b` |
| Private evidence manifest commitment | `ba089a68ac568054b8db2be9d70c8fcec6531fe2bcb568d32dcb7ed7c991ffe5` |
| Post-restart proof manifest commitment | `d764666f6be6cda21162a2aaeca9891c1a852d2a8c61c6e6bcb903de4c127415` |
| Byte-preserving private evidence tree commitment | `0bcb08f42a98de30cae02d718ce8d5906ef4ae115babbc5a5dfff819507aeba3` |

The restart recreated the runtime container. The same released binary returned
to `ready`, retained paired trust, restored the raw topology counts, recovered
the owner-only MCP boundary and SHIP listener, and kept public output redacted.

## Safety And Successor Gate

No raw identity, protocol address, endpoint, payload, transcript, correlation
material, trust material, or restricted preimage is stored here. The exact
five M6.25 tools, one initial `eebus.v1.*` namespace, `candidate_ref`
prohibition, owner-local raw/public-redacted split, and all no-write stops are
unchanged.

`MSP-065-LIVE-R1` is now the sole logical-ready, dispatchable, selected, and
initial-ready row. This record does not complete M6.5, create candidate facts,
promote a leaf, or unlock M9. Historical synthetic M6.5-M8.5 rows remain
non-authoritative for the live chain, and M9 remains blocked by the
digest-bound `MSP-085-LIVE-R1` token with `promoted_leaf_count > 0`.
