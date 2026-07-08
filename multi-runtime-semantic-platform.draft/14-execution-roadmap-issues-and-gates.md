# Execution Roadmap, Issues, And Gates

Canonical-SHA256: `de84f3f35afecd3317e2a62089fdaa78150adb4b62110771296b7fd7c7ab24df`

Depends on:
All previous chunks.

Scope:
Defines issue slicing, model routing, validation gates, review gates, and draft
promotion criteria for the raw-first eeBUS VR940f execution path.

Idempotence contract:
The roadmap may be converted into issues repeatedly. Duplicate issue creation
must be avoided by checking the issue map first. One active PR per repo remains
the default.

Falsifiability gate:
Each issue must have a testable gate. If implementers cannot prove the gate
without subjective judgment, the issue is not ready for locked execution.

Coverage:
Covers the executable milestone order, M0 control plane, doc gates, transport
gates, and consumer promotion gates.

## Required M0 Control Plane

Before any code issue starts, M0 creates a machine-readable issue matrix. Every
row must include:

- issue id;
- repo;
- milestone;
- complexity from 1 to 10;
- model lane;
- assigned route;
- predecessor edges;
- one-PR-per-repo serialization state;
- canonical doc owner;
- doc-gate requirement;
- transport/security gate applicability;
- rollback ledger entry;
- review ledger entry.

Model lanes are fixed for this plan:

- complexity 1-2: `GPT-5.3-Codex-Spark` for smoke, checklist, and mechanical
  gap checks;
- complexity 3-4: `gpt-5.4-mini` for small doc-gate, issue splitting,
  acceptance criteria, and consistency tasks;
- complexity 5: `GPT-5.5 medium` owner; Spark or `gpt-5.4-mini` may review;
- complexity 6-7: `GPT-5.5 high` owner with adversarial review;
- complexity 8-10: `GPT-5.5 xhigh` owner, with independent review before
  merge.

## Milestone Order

1. `M0 - Control Plane And Issue Matrix`
2. `M1 - Documentation Grounding`
3. `M2 - Raw Identity, Snapshot, Evidence, And Correlation Drafts`
4. `M3 - eeBUS Runtime Feasibility`
5. `M3.5 - Raw Runtime Contract Freeze`
6. `M4 - Production Trust, First-Trust, And Security`
7. `M4.5 - Trust And Admin State Freeze`
8. `M5 - Gateway Sidecar Integration`
9. `M6 - Read-Only eeBUS MCP v1`
10. `M6.5 - Synchronized Evidence Recorder`
11. `M7 - Draft Candidate Fact Graph`
12. `M8 - Multi-Runtime Coexistence`
13. `M8.5 - Leaf Promotion Lock`
14. `M9 - GraphQL, Portal, And HA Consumers`

## Issue Slicing

Each issue must touch one execution surface. If an issue needs two surfaces,
split it. Allowed surfaces are:

- docs/control plane;
- runtime feasibility;
- trust/security;
- gateway sidecar;
- native raw evidence;
- MCP;
- candidate fact graph;
- coexistence;
- GraphQL;
- Portal;
- Home Assistant.

M5 is explicitly split: configuration scaffolding may be low complexity, but
sidecar/network/container integration is high complexity and requires
architecture plus security review.

M6.5 may consume only existing read-only eBUS debug, MCP, or log surfaces. If
new B509/B524/B555 capture is needed, create a separate eBUS issue/PR and run
the eBUS transport gate before continuing to M7.

M2 starts with a separate `helianthus-eebusreg` bootstrap issue. That issue may
create only the raw runtime/evidence module shell, CI, boundary gates, and
repository policy. It must not import `enbility/eebus-go`, open network
listeners, create trust-store code, or add any gateway dependency.

## Documentation Gates

Required documentation order:

1. `helianthus-docs-ebus/docs/platform/...` ownership and transition ADR;
2. `helianthus-docs-eebus` bootstrap;
3. eeBUS provenance and publication policy.

`helianthus-docs-ebus` remains the canonical protocol knowledge and platform
contract repo for doc-gate purposes. `helianthus-docs-eebus` is the eeBUS-native
documentation/workbench repo for transport, device, discovery, evidence, and
RE notes; it must cross-seed publishable conclusions back to
`helianthus-docs-ebus` when they become durable protocol knowledge.
`helianthus-docs-ebus/docs/platform/` owns cross-protocol contracts such as MCP
lifecycle, promotion gates, consumer rollout, evidence recorder format, and
coexistence/conflict policy until a future docs-platform repo exists.

Non-owning docs must use the summary-only template:

- canonical-source banner;
- one-paragraph purpose;
- link list to canonical pages;
- optional local usage notes.

They must not contain requirements, `MUST`/`SHALL` language, acceptance
criteria, checklists, version tables, deprecation policy, or approval steps.

Restricted-source quarantine is mandatory. `vendor_restricted` content must
never appear in public repos, public issues, public PR text, public review
comments, or public ADR rationale. Public normative claims cite only
publishable evidence ids. `operator_note` is context only and never sufficient
to establish a protocol fact.

Every code PR must list canonical doc paths and merged doc PR/commit refs.
An opened docs PR is insufficient.

## Transport And Security Gates

M0 defines `eebus-transport-gate v0` before M3 starts. The minimum gate covers:

- fake peer handshake;
- pairing open and closed;
- listener bind/interface/subnet;
- mDNS positive and negative cases;
- manual endpoint fallback;
- cert/store persistence;
- retry/backoff/quarantine;
- deterministic snapshot/replay.

eBUS T01..T88 is required only when eBUS transport or eBUS capture code is
touched.

Security gate artifacts are required for:

- first-trust race behavior;
- admin-local boundary;
- HA network exposure;
- backup/restore/rollback;
- trust-store hardening;
- redaction;
- quarantine/backoff;
- future experimental mutation gating.

## MCP v1 Gate

M6 freezes final read-only `eebus.v1.*` only after M3.5 raw contracts and M4.5
trust/admin state are composed.

The gate must prove:

- snapshot refs bind to runtime, contract, tool/scope, mask tier, and effective
  auth scope;
- dereference requires exact binding match and never re-masks a captured ref;
- RFC 8785/JCS hash stability;
- exhaustive error-code precedence;
- `snapshot.drop` returns `dropped` or `already_gone`;
- v1 evolution is additive-only;
- no leak into `ebus.v1.*`, GraphQL, Home Assistant, or semantic registry
  outputs.

## Leaf Promotion Gate

M7 creates draft candidate facts only. M8 proves coexistence. M8.5 locks
individual leaf promotion.

No consumer work may start until each promoted leaf has a dossier with:

- source-family identity for B509/B524/B555;
- eeBUS entity/service/feature/path;
- comparator pass/fail parameters;
- negative terminal states;
- coexistence result;
- replay regeneration;
- redacted hashes;
- retest trigger.

Mutable proof additionally requires lab lease, one writer, gateway/router write
path only, no direct adapter writes, abort conditions, rollback verification,
and three independent perturbation cycles.

## Review Gates

Dual review and doc gate are per PR/issue, not only per milestone. Milestone
architecture reviews are aggregate signoffs.

No PR may merge unless it links:

- doc-gate result;
- rollback ledger entry;
- relevant transport/security gate artifact;
- review disposition for every comment.

Code-structure reviews are required after M3.5/M4, after M5/M6, and after final
plan execution.

## Draft Promotion Criteria

Before promotion to `.locked/`:

- complete M0 issue matrix with model lanes and predecessor edges;
- create or link the docs ownership ADR and provenance policy issues;
- create or link the `helianthus-eebusreg` raw repo bootstrap issue before
  runtime-contract issues start;
- run adversarial review against taxonomy leakage, trust boundary leakage, MCP
  determinism, and false semantic promotion;
- confirm gateway `0.4.0` lab baseline artifacts;
- confirm eeBUS feasibility gates are separately issue-scoped;
- update `plan.yaml` state and directory suffix from `.draft` to `.locked`;
- update canonical hash references after content changes.

## Git Hygiene

This draft is added directly on `main` by owner override. It must not stage or
modify existing dirty files in other plan directories.
