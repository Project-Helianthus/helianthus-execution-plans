# Gateway-Embedded Proxy 05: Matrix, Validation, and Gates

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f600ff2254ab7a300399ff85496c41b9b8ff13a0149dc62b137735e13e84c011`

Depends on: [00-canonical.md](./00-canonical.md),
[90-issue-map.md](./90-issue-map.md),
[91-milestone-map.md](./91-milestone-map.md).

Scope: AD01..AD12 matrix definitions, gate policy, regression requirements,
orchestrator contract, assumptions and defaults, and maintenance readiness
definition. Covers milestone M5 and canonical Sections 4-7, 11.

Idempotence contract: Declarative-only. Reapplying this chunk must not create
new issues, mutate matrix IDs, or weaken gate policy.

Falsifiability gate: Review fails this chunk if any AD01..AD12 definition is
absent, gate policy does not require T01..T88 regression, orchestrator
contract does not enforce one-issue-per-repo, or maintenance readiness
criteria are missing.

Coverage: Canonical Section 3 (M5), Sections 4-7, 11.

## 1. M5: Matrix Validation + E2E

Repos: `helianthus-ebusgateway`, `helianthus-docs-ebus`

### 1.1 Test Definitions

Each AD test must have documented evidence in the docs repo:
- Description of test setup
- Expected behavior
- Pass/fail criteria
- Evidence format (log excerpts, counter values, screenshot)

### 1.2 Live Bus Validation

3-master topology: 0x71 (gateway), 0x31 (ebusd), 0x10 (VRC700)

Measurements:
- Active path transaction success rate (target: same as proxy-based)
- Passive path corrupted frame rate (target: significant reduction from ~40%)
- Observer broadcast delivery correctness (AD05, AD06)
- Arbitration fairness: gateway vs ebusd transaction distribution (AD07)
- Escape corruption: zero instances of 0xA9/0xAA mangling (AD12)

### 1.3 Performance Comparison

Side-by-side: proxy-based vs adapter-direct on same bus topology:
- Request/response latency (active path)
- Observe-first coverage percentage (passive path)
- Corrupted frame count per 1000 bus transactions
- Memory usage (gateway process)

### 1.4 Regression

- T01..T88: all pass (existing transport modes unmodified)
- PX01..PX12: all pass (standalone proxy unmodified)
- Existing MCP tools functional (zones.get, dhw.get, etc.)
- Observe-first semantics: broadcast listener, shadow cache, deduplicator

### 1.5 Falsifiability

Review fails if:
- Any AD01..AD12 lacks documented evidence
- T01..T88 regression not demonstrated
- No corrupted frame rate comparison data

## 2. Required Matrix Subset: AD01..AD12

| ID | Description | Evidence Format | Milestone |
|----|-------------|----------------|-----------|
| AD01 | Active path sends and receives transactions correctly | Transaction success count + zero-error log | M2 |
| AD02 | Passive path sees zero self-echo frames | Self-echo counter = 0 for 1000+ transactions | M2 |
| AD03 | Passive path reconstructs third-party traffic | Classified event count matching ebusd tx count | M2 |
| AD04 | RESETTED propagates to active + passive + external | Log showing reset delivery to all consumers | M1, M3 |
| AD05 | ebusd connects and receives observer broadcasts | ebusd log showing received broadcasts | M3 |
| AD06 | ebusd sends START/SEND and completes transaction | ebusd log showing successful bus command | M3 |
| AD07 | Gateway and ebusd compete fairly at SYN | Transaction distribution log (no starvation) | M3 |
| AD08 | Per-session echo suppression works correctly | Zero echo leak in observer streams | M1, M3 |
| AD09 | Adapter disconnect: reconnection recovers | Reconnection log + resumed operation | M1 |
| AD10 | Migration preserves all semantics | Before/after MCP tool comparison | M4 |
| AD11 | Rollback restores original behavior | Config revert + proxy-based operation log | M4 |
| AD12 | No escape corruption in observer streams | Zero CRC mismatch from escape-containing frames | M1, M3 |

## 3. Gate Policy

Adapter-direct transport/protocol PRs must pass:
- Full `T01..T88` (existing transport matrix)
- Full `AD01..AD12` (adapter-direct matrix)
- No unexpected `fail`
- No unexpected `xpass`

`PX01..PX12` remain as the standalone proxy gate:
- Required for proxy repo PRs
- Not required for gateway adapter-direct PRs (separate product)

## 4. Orchestrator Contract

Execution rules for an orchestrator receiving this plan:

1. Resolve child issues from the canonical map; do not infer missing work.
2. Execute strictly `M0 -> M1 -> M2 -> M3 -> M4 -> M5`.
3. M2 and M3 both depend on M1 but are independent of each other. Parallel
   execution is permitted if one-issue-per-repo is satisfied.
4. Maintain one active issue per repo at a time.
5. Keep doc-gate ahead of behavior-change merge decisions.
6. Transport-gate: T01..T88 regression must pass for any transport-affecting PR.
7. AD01..AD12 gate must pass for adapter-direct PRs.
8. Do not modify standalone proxy code. This plan is additive to the gateway.
9. Do not modify existing transport modes (ENH, ENS, ebusd-tcp via proxy).

## 5. Assumptions and Defaults

- The eBUS adapter hardware supports only one simultaneous TCP connection.
- The gateway is the primary bus owner (eBUS address 0x71). External clients
  are secondary owners.
- ENH is the primary adapter protocol. ENS included; UDP-plain and TCP-plain
  out of scope.
- Local target emulation is out of scope for the embedded multiplexer.
- Source policy lease management is out of scope.
- Zero-downtime migration is not required. Addon restart is acceptable.
- The standalone proxy remains a first-class product, not deprecated.

## 6. Maintenance Readiness Definition

This plan transitions from `.locked` to `.implementing` when:
- M0 issues are created on GitHub with real issue numbers
- Architecture doc PR is opened

This plan transitions from `.implementing` to `.maintenance` when:
- All AD01..AD12 gates have documented evidence
- T01..T88 regression is demonstrated
- Migration and rollback documentation is complete
- No stale locked-state instructions remain in the split package
- Issue map is updated with real issue numbers and status
