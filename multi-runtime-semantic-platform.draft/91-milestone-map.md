# Milestone Map

Status: `Draft`
Baseline: `Gateway 0.4.0`

| Milestone | Primary repo | Depends on | Gate |
| --- | --- | --- | --- |
| M0 - Gateway 0.4.0 Baseline Lock | helianthus-ebusgateway | none | Direct eBUS no-proxy build, deploy, and smoke are reproducible. |
| M1 - Platform Vocabulary ADR | helianthus-docs-ebus | M0 | Every future protocol component can be classified unambiguously. |
| M2 - eBUS Runtime Boundary | helianthus-ebusgateway | M0, M1 | Existing eBUS public behavior is unchanged. |
| M3 - eBUS Base/Profile Split | helianthus-ebusreg | M1, M2 | Raw/classic eBUS remains available without Vaillant semantics. |
| M4 - Semantic Provenance v1 | helianthus-ebusgateway | M1, M2 | Semantic facts carry runtime/profile/evidence metadata. |
| M5 - helianthus-eebusreg | helianthus-eebusreg | M1 | eeBUS raw registry runs without consumer dependencies. |
| M6 - eeBUS MCP Raw First | helianthus-ebusgateway | M5 | VR940f raw discovery is visible through MCP. |
| M7 - eeBUS Semantic Candidate | helianthus-ebusgateway | M4, M6 | Candidate/promoted/withheld statuses are visible through MCP. |
| M8 - Multi-Runtime Coexistence | helianthus-ebusgateway | M2, M6 | eBUS and eeBUS run together with separate raw surfaces. |
| M9 - GraphQL, Portal, HA | gateway + consumers | M7, M8 | Consumers receive only stable promoted semantics. |
| M10 - Next Runtime Families | multiple | M1, M4 | New families start raw-first using the same contracts. |

## Parallelism

M3 and M5 may proceed in parallel after M1 if one-active-issue-per-repo is
respected. M9 must not start until MCP behavior for the relevant semantic
family is stable.
