# Milestone Map

Dependency order (merge): `M0 → M1 → M2 → M2a → M3 → M4 → M5 → M6 → M7`.

`merge_depends_on` uses transitive closure over the stack per AD14.

| Milestone | Repo | Complexity | Transport-gate | Doc-gate trigger |
| --- | --- | --- | --- | --- |
| `M0_DOC_GATE` | `helianthus-docs-ebus` | 4 | REQUIRED | yes |
| `M1_EBUSREG_DIRECTED_SCAN` | `helianthus-ebusreg` | 3 | not-required | no |
| `M2_GATEWAY_JOINBUS_ADAPTER` | `helianthus-ebusgateway` | 5 | REQUIRED | yes |
| `M2a_GATEWAY_OFFLINE_HARNESS` | `helianthus-ebusgateway` | 4 | REQUIRED | no |
| `M3_GATEWAY_STARTUP_ORDER_FLIP` | `helianthus-ebusgateway` | 6 | REQUIRED | yes |
| `M4_GATEWAY_EVIDENCE_PIPELINE` | `helianthus-ebusgateway` | 6 | REQUIRED | yes |
| `M5_GATEWAY_DEGRADED_MODE_AND_ENVELOPE` | `helianthus-ebusgateway` | 4 | REQUIRED | yes |
| `M6_GATEWAY_OVERRIDE_AND_FULL_RANGE_GUARD` | `helianthus-ebusgateway` | 5 | REQUIRED | yes |
| `M7_GATEWAY_INTEGRATION_ACCEPTANCE` | `helianthus-ebusgateway` | 6 | REQUIRED | no |

## Iteration vs Merge Dependencies

| Milestone | iteration_depends_on | merge_depends_on |
| --- | --- | --- |
| M0 | — | — |
| M1 | M0 | M0 |
| M2 | M0 | M0 |
| M2a | M0, M2, M6 | M0, M2 |
| M3 | M0, M1, M2, M2a | M0, M1, M2, M2a |
| M4 | M0, M1, M3 | M0, M1, M2, M2a, M3 |
| M5 | M0, M3, M4 | M0, M1, M2, M2a, M3, M4 |
| M6 | M0, M4, M5 | M0, M1, M2, M2a, M3, M4, M5 |
| M7 | M0, M1, M2a, M3, M4, M5, M6 | M0, M1, M2, M2a, M3, M4, M5, M6 |

Gap between iteration and merge dependencies invokes the
`iteration_vs_merge_gap` rule under `coordination.pr_strategy.rebase_protocol`:
the later-merging PR must rebase against each additional merge-
blocker's merge commit, re-run full local CI, and record blocker
SHAs in the PR description under `## Merge-blocker SHAs at rebase`.

## PR Strategy

- `helianthus-ebusreg`: one-pr-one-issue (standard invariant)
- `helianthus-docs-ebus`: one-pr-one-issue (standard invariant)
- `helianthus-ebusgateway`: operator-blessed-multi-pr-exception
  per AD14 — stacked PRs M2 → M2a → M3 → M4 → M5 → M6 → M7 in
  dependency order; squash-merge cascade with mandatory rebase +
  fresh local CI + reviewer re-approval on non-trivial rebase

## Doc-Gate Tiers (AD18)

- **Tier 1**: docs-ebus companion PR open-for-review with complete
  drafted sections unblocks M2..M6 merge.
- **Tier 2**: docs-ebus companion PR merged to main unblocks M7
  merge.
