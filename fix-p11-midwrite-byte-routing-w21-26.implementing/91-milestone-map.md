# Milestone map

Canonical-SHA256: `ddd1786c883f07395e417d63c71607b46f92b8968126363fd11c55b8e0d8de7d`

Depends on: 00-canonical.md (milestone definitions), 90-issue-map.md (issue URLs).

Scope: maps each milestone to its repo branch, PR URL, and current status. Populated by cruise-dev-supervise as work progresses.

Idempotence contract: re-entering a milestone's row after merge updates only the merge SHA and merged_at; PR URL and branch are immutable post-creation.

Falsifiability gate: every milestone reaching status=done must have a non-empty merge_sha. M4 verification cannot reach done without M3* merges; M5 cannot reach done without M4 verification pass.

Coverage: per-milestone branch + PR + merge tracking. Cross-repo dependency order enforced per AD07.

| Milestone | Repo | Branch | PR URL | Merge SHA | Status |
|---|---|---|---|---|---|
| M0 | helianthus-execution-plans | — | (this plan locks the gate) | — | done |
| M0 | helianthus-docs-ebus | tbd | tbd | — | pending |
| M1 | helianthus-ebusgateway | tbd | tbd | — | pending |
| M2 | helianthus-ebusgateway | (baseline already captured 2026-05-23) | n/a | — | done |
| M3a | helianthus-ebusgateway | tbd | tbd | — | pending |
| M3b | helianthus-ebusgateway | tbd | tbd | — | pending |
| M3c | helianthus-ebusgateway | tbd | tbd | — | pending |
| M4 | HA host .4 (verification report) | n/a | n/a | — | blocked-by-M3 |
| M5 | helianthus-ha-addon | tbd | tbd | — | blocked-by-M4 |

## PR sequencing

Per AD07: PR1 ebusgo (CONDITIONAL — likely SKIPPED) → PR2 gateway (M3a+M3b+M3c combined as a single PR with TDD red→green) → PR3 addon (M5).

M3a/M3b/M3c may land in a single gateway PR because they are tightly coupled. Splitting risks landing M3b without the M3a accessors, breaking the build.
