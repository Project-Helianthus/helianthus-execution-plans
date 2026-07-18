# Execution Roadmap, Issues, And Gates

Canonical-SHA256: `258e75ba6e0aaa784f00e8e4acd34bd727fc2c5d6ab32bdbd39083d34bb6357a`

Depends on:
All previous chunks.

Scope:
Defines issue slicing, model routing, validation gates, review gates, recovery
reconciliation, and locked execution criteria for the raw-first eeBUS VR940f
path.

Idempotence contract:
The roadmap may be converted into issues repeatedly. Duplicate issue creation
must be avoided by checking the issue map first. One active PR per repo remains
mandatory, and dirty local rescue code never unlocks successors.

Falsifiability gate:
Each issue must have a testable gate. If implementers cannot prove the gate
without subjective judgment, the issue is not ready for locked execution.

Coverage:
Covers the executable milestone order, recovery reconciliation, M0 control
plane, doc gates, transport/security gates, and consumer promotion gates.

## Required Row Contract

Every row in `92-m0-issue-matrix.yaml` must include:

- issue id, repo, milestone, complexity from 1 to 10, and exactly one routing
  authority: a symbolic routing contract for active work or historical routing
  evidence for terminal work;
- authoritative completion-token edges, including explicit empty lists;
- canonical docs owner and doc-gate result;
- transport and security gate classification;
- rollback ledger, review ledger, TDD mode, smoke scope, and acceptance list.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

## Locked Milestone Order

1. `RECOVERY_RECONCILIATION`
2. `M3 - eeBUS Runtime Feasibility` completion by clean-main MSP-03D-R only
3. `M3.5 - Raw Runtime Contract Freeze`
4. `M4 - Store, Raw View, Lifecycle Facade, And Trust Security`
5. `M4.5 - Trust And Admin State Freeze`
6. `M5 - Gateway Sidecar Integration`
7. `M6 - Read-Only eeBUS MCP v1`
8. `M6.5 - Synchronized Evidence Recorder`
9. `M7 - Draft Candidate Fact Graph`
10. `M8 - Multi-Runtime Coexistence`
11. `M8.5 - Leaf Promotion Lock`
12. `M9 - GraphQL, Portal, And HA Consumers`

Historical M0, M1, M2, MSP-03A, MSP-03B, MSP-03C, and the merged MSP-03D
EEBUS-G01 fake-peer harness slice remain preserved evidence. They do not let
M3 close without MSP-R00-L, DOCS-VERIFY, the AD-DOCS-01 documentation chain,
and MSP-03D-R.

## Initial Ready Rows

After AD-DOCS-01, `MSP-R00` is completed locally with no code acceptance,
issue `Project-Helianthus/helianthus-eebusreg#14`, architecture review
`PASS`, and no successor unlock beyond making the publication row eligible.
The initial ready set is exactly:

- `MSP-R00-L` in `helianthus-execution-plans`, after local MSP-R00 completion;
- `DOCS-VERIFY` in `helianthus-docs-eebus`, with no predecessor.

`MSP-R00` remains local evidence only. Public plan artifacts omit local commit
SHA, private path, raw HMAC mapping, source-bundle detail, and sensitive raw
evidence. It does not accept code and does not unlock runtime successors.

`MSP-R00-L` is the separately serialized execution-plans publication row. It
depends on MSP-R00 and publishes only the reviewed redacted ledger. Public IDs
are random, nonsemantic, and regenerated per publication. The only public
classes are `public_redacted`, `private_restricted`, and `discarded`. Public
commitment covers only opaque IDs, classes, dispositions, and redaction
metadata. It never publishes raw or identifying paths, volume, sizes,
timestamps, byte counts, deterministic IDs, raw hashes, source bundles, rescue
commits, packet captures, transcripts, keys, credentials, trust stores, or
device identities.

`DOCS-VERIFY` blocks runtime successors until license, canonical owners, issue
template compliance, path layout, and cross-seeding to `helianthus-docs-ebus`
are verified.

## AD-DOCS-01 Serialized Documentation Chain

The recovery documentation chain is:

1. completed local `MSP-R00` -> ready `MSP-R00-L`;
2. `DOCS-VERIFY` -> `MSP-DOCS-API-SCHEMA`;
3. `MSP-R00-L` plus `MSP-DOCS-API-SCHEMA` -> `MSP-DOCS-PLATFORM`;
4. `MSP-DOCS-PLATFORM` -> `MSP-DOCS-E2`;
5. `MSP-DOCS-E2` -> `MSP-DOCS-E2R-PLATFORM` ->
   `MSP-DOCS-E2R-PUBLISH` -> `MSP-DOCS-E2R-AGGREGATE` -> `MSP-DOCS-CLEAN`;
6. `MSP-DOCS-CLEAN` and `MSP-03C` completion tokens -> `MSP-03D-R`;
   `MSP-03D-G01` is evidence-only and cannot authorize that row.

Later, the single source PR follows a pre-merge handshake:
`MSP-036` -> `MSP-DOCS-API-CANDIDATE` -> `MSP-055` ->
`MSP-DOCS-API-FREEZE` -> `MSP-04B`. Preparing and pinning the `MSP-055`
source PR after `MSP-036` does not make `MSP-055` complete or merge-eligible.

`MSP-DOCS-CANDIDATE-CLEANUP` is a dormant conditional row after
`MSP-DOCS-E2`. It is not initially ready and is not a required predecessor for
normal successors. It activates only when a candidate expires or the source PR
closes unmerged. Once activated, it preempts same-repo successors, blocks the
bound cross-repo source PR, marks the candidate `withdrawn`, removes candidate
artifacts, and restores docs main green before a new candidate cycle.

## Clean-Main Serialized Sequence

After the initial ready rows and documentation chain merge, eebusreg work is
serialized one PR at a time:

1. `MSP-DOCS-CLEAN` - delete any eebusreg docs and install ownership/API gates.
2. `MSP-03D-R` - G17+G19 harness and canonical recovery evidence.
3. `MSP-035` - raw identity/snapshot/evidence freeze.
4. `MSP-04A` - internal persistent store/schema only.
5. `MSP-036` - public immutable raw snapshot/view only.
6. `MSP-DOCS-API-CANDIDATE` - merge the hidden candidate API pages and
   exact-head manifest/provenance while the single `MSP-055` source PR remains
   unmerged.
7. `MSP-055` - merge the disabled-by-default read-only lifecycle facade only
   after its current source head exactly matches the merged candidate.
8. `MSP-DOCS-API-FREEZE` - compile examples, compare exact Go AST/API
   manifest, and promote the candidate API docs to active.
9. `MSP-04B` - first-trust, OOB confirmation, and admin-local boundary.
10. `MSP-04C` - restore, revocation, quarantine, and repair.
11. `MSP-045` - trust and admin state freeze.

Gateway M5, MCP M6, evidence/candidates/coexistence/promotion, and consumers
remain blocked until the prior canonical docs and eebusreg contracts merge.
GraphQL, Portal, Home Assistant, command routing, raw writes, and promoted
semantics stay out until their later milestones and per-leaf locks.

## M5 Production-Prerequisite Correction

The earlier direct MSP-05B path was closed because the production
protected-material provider and scoped SHIP constructor were not installed,
and the M5A gateway configuration could not be mapped losslessly to the
original runtime shape.
Those production prerequisites, the pre-release API v1 correction, and exact
gateway mapping are now complete. The MSP-05B pre-review found that worker-level
process termination can bypass deferred cleanup and that the mapped remote
allowlist is not emitted in its canonical lowercase sorted form. The sole ready
row is therefore MSP-05A-R2. It establishes one process-exit boundary in main,
propagates wrapped worker/helper errors, and canonicalizes remote identities
before MSP-05B.

MSP-05B must keep its disabled path at zero resolver, New, Start, and Shutdown
calls. Enabled activation uses typed interface-address resolution, zones only
IPv6 link-local addresses, shuts down every constructed runtime exactly once,
and joins Shutdown errors with any existing run error. Runtime Start proves
synchronous acquisition and worker launch only; it does not prove sustained
gateway readiness.

No prerequisite may weaken the M4.5 trust freeze. Pairing stays closed, mDNS
publication is independent from listener startup, wildcard or ambiguous scope
fails closed, and disabled gateway behavior performs no eeBUS construction,
filesystem access, goroutine, socket, or publication.

## Documentation Gates

`helianthus-docs-ebus/docs/platform/` owns language-neutral cross-runtime
envelopes, hash/auth binding, shared registry boundary, and promotion/consumer
rules.

`helianthus-docs-eebus/protocols/` owns eeBUS/SHIP/SPINE protocol behavior.
`helianthus-docs-eebus/architecture/` owns eeBUS runtime, adapter, trust,
persistence, and lifecycle architecture. `helianthus-docs-eebus/api/` owns
eeBUS-specific Go public API schema, reference, and examples. `devices/`,
`evidence/`, and `re-notes/` remain valid docs-eebus roots.

Every page has `canonical_source`. Duplication is forbidden.
`helianthus-eebusreg` and clean-main branches contain no `docs/` directory and
own no substantive protocol, architecture, API, harness, test, or user
documentation. Only exact minimal README entry/status/build pointers and
concise Go package metadata comments may remain, linking only to
manifest-state `active` pages or pre-existing stable landing pages.

Manifest states:

- `planned`: absent allowed, noncanonical/nonlinkable, source issue/PR,
  14-day expiry.
- `candidate`: path exists only in candidate area, hidden from stable outputs,
  source PR/head/hash, 30-day expiry.
- `active`: exists and approved/frozen.
- `withdrawn`: excluded and mandatory cleanup.

Combined-ref CI runs for PRs; main CI enforces expiry. Owner/source pairs are
globally unique.

`DOCS-VERIFY` must prove license, owner, issue-template, path-layout, and
cross-seeding compliance before runtime successors begin. Gateway import is
blocked until prior canonical docs and eebusreg contracts are merged.

`MSP-DOCS-API-SCHEMA` merges the `helianthus.eebus.api-surface.v1` schema,
canonical extraction/normalization rules, and golden positive/negative
fixtures before extractor consumption.

`MSP-DOCS-PLATFORM` adds or migrates the platform contracts and
`docs/platform/manifests/eebus-doc-ownership.yaml`.

`MSP-DOCS-E2` creates `architecture/` and `api/` beside existing `protocols/`.
It migrates only supported claims. Otherwise content is candidate or
hypothesis with a falsifier. Candidate API pages are excluded from stable
navigation, search, sitemap, versioned bundles, and release bundles.

`MSP-DOCS-CLEAN` starts from clean main, idempotently deletes `docs/` if
present, never uses code-repo docs as migration input, trims README/doc
comments, and installs local plus GitHub ownership and API extractor gates.
The gate rejects tracked or untracked `docs/**`, symlinks, absolute paths,
traversal, casefold collisions, extra Markdown beyond allowlist, non-template
README text, and substantive package comments via AST allow/deny rules. It
uses positive and negative fixtures on Linux plus macOS or portable casefold
emulation. Path-safety and `canonical_source` gates are mirrored in
docs-eebus and docs-ebus owned roots.

`MSP-DOCS-API-CANDIDATE` runs after `MSP-036`. The single `MSP-055` source PR
may be prepared and pinned at an immutable candidate-ready head, but remains
unmerged. Docs-eebus verifies the exact-head manifest and attestation, merges
the hidden candidate pages and provenance first, and invalidates the candidate
on any source push. `MSP-055` cannot merge until its current head exactly
matches that merged candidate; the same issue, branch, and PR continue through
the source merge gate.

`MSP-DOCS-API-FREEZE` runs against the exact merged source commit. It compiles
examples, compares the Go AST/API manifest, verifies provenance, and promotes
candidate API docs to an active version.

Cross-repo CI uses clean clones, explicit refs, pinned tools, and no absolute
paths. Platform merges first without forward links. E2 links only merged active
platform pages. README links only active/stable targets.

Rollback is forward-only and never restores `docs/` to eebusreg main.
Break-glass restoration requires explicit owner approval, blocks all
successors, and creates cleanup.

Recovered dirty docs are not facts. Publishable evidence IDs are required;
otherwise content remains candidate or hypothesis.

Candidate API handshake rules:

- only org-owned `Project-Helianthus` branches are valid; forks are rejected;
- after `MSP-036`, the single `MSP-055` source PR may be prepared and pinned,
  but it remains merge-blocked until `MSP-DOCS-API-CANDIDATE` merges;
- no force-push may happen after docs preparation;
- eebusreg CI produces a normalized manifest and GitHub OIDC DSSE/in-toto
  attestation;
- predicate verification binds issuer, workflow identity, org repo, ref,
  immutable head SHA, run id, run attempt, extractor/schema versions, clean
  checkout, and manifest digest;
- docs-eebus commits the candidate manifest copy plus provenance and merges
  first;
- eebusreg merge gate requires an exact match to the current source head, and
  manifest state `candidate` with `expires_at` later than trusted gate time;
- any source push invalidates the candidate and re-blocks `MSP-055`;
- active cleanup or candidate state `withdrawn`/expired blocks the source merge;
- abandoned or expired candidates trigger cleanup and require a fresh
  candidate cycle before `MSP-055` can merge.

## Transport And Security Gates

`eebus-transport-gate v0` is required for SHIP/SPINE runtime, listener,
discovery, pairing, trust, snapshot/replay, or gateway sidecar wiring changes.
eBUS T01..T88 is required only when eBUS transport or eBUS capture code is
touched.

Exact gate meanings:

- `EEBUS-G17`: configured local SHIP advertisement/discovery, myVaillant trust
  visibility, and negative/TTL behavior. It is not evidence that the VR940f
  advertises a server.
- `EEBUS-G18`: M8 coexistence no drift only.
- `EEBUS-G19`: direct outbound VR940f TCP/TLS/WebSocket/SHIP access completion
  plus first post-access SPINE data.

MSP-03D closes only after both revised G17 and G19 pass with owner acceptance.
Feature graph completeness and reconnect durability belong to MSP-055/M6, not
G17.

## Raw View And Lifecycle Boundaries

`MSP-036` can export only versioned immutable raw snapshot/view fields. It has
no semantic device ID, lifecycle authority, trust/pairing mutation, or
availability guarantee. It depends on internal store schema plus migration and
conformance tests.

`MSP-055` is disabled by default. The public lifecycle facade is read-only.
Outbound sockets require explicit config plus pre-seeded trust or an allowlist.
No public trust or pairing mutation is allowed. First-trust/OOB/admin mutation
stays in later admin-local gated rows.

## MCP And Consumer Gates

M6 freezes final read-only `eebus.v1.*` only after raw contracts, immutable raw
views, lifecycle facade constraints, and trust/admin state are composed.

M7 creates draft candidate facts only. M8 proves coexistence. M8.5 locks
individual leaf promotion. M9 consumers are ordered GraphQL, Portal, Home
Assistant, then add-on exposure, and they expose only promoted leaves.

## Review Gates

Dual review and doc gate are per PR/issue, not only per milestone. Every
milestone ends with complete architecture review. Final execution adds one
extra code-structure review.

No PR may merge unless it links:

- doc-gate result;
- rollback ledger entry;
- relevant transport/security gate artifact;
- review disposition for every comment.

## Lock Criteria

This plan is locked when:

- plan state is `locked` and current milestone is `M5_PRODUCTION_PREREQUISITES`;
- accepted-through text records M4.5 and M5A completion;
- direct MSP-05B dispatch is blocked by the full production prerequisite chain;
- MSP-05A-R2 is the only current ready row;
- AD-DOCS-01 rows are serialized and the dormant cleanup row is not treated as
  initially ready or as a normal required predecessor;
- all future dependencies are explicit and acyclic;
- the canonical SHA-256 is synchronized through the index and split chunks.
