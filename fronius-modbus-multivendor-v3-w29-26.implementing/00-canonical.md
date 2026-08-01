# Fronius-first Modbus runtime, multi-profile registry, and private output bindings

Date: `2026-07-14`
State: `implementing`
Availability: `openai_only`, `gpt-5.6-sol`, reasoning `max`
Supersedes: `fronius-modbus-eebus-bridge-w28-26.draft`

This implementing plan replaces the W28 package as execution intent. The W28 directory remains
unchanged as forensic history. The operator action on 2026-07-14 authorized plan lock and
publication. PR #91 carries the corrected pre-gateway authorization. Its merge commit is
the sole current immutable execution anchor; issue #90 tracks the change but is not
authorization evidence. PR #89 remains predecessor provenance only.

## Execution authorization

Execution activates only after PR #91 merges. Its exact merge commit is the sole current
immutable authorization anchor. Issue #90 is tracking metadata only and is not cryptographic
or authorization evidence. PR #89 is retained only as predecessor provenance and is not
authority for the corrected M1 capability or M2 ledger fields.

PR #91 must retain its exact original base/head repository and ref identity. Its squash
merge must have exactly one parent equal to the expected original base SHA and a tree equal
to the externally attested PR head tree. One submitted official
Codex bot `COMMENTED` review must equal the canonical Codex no-suggestions template for the
exact ten-character head prefix and have zero inline findings; no severity or arbitrary finding
text is accepted. Two separate submitted owner reviews then bind that head/tree, `NO_FINDINGS`,
and owner-attested fresh-process references/output digests; they are process attestations, not
independently authenticated OpenAI artifacts. One unedited aggregate binds the
immutable submitted review IDs and a mandatory, non-authoritative same-change-set post-merge
`push` workflow execution observation on canonical `main` at the exact squash SHA; the aggregate is created only after that run completes, and
the plan never self-embeds its own head SHA.

Trust model: `owner_plus_authenticated_independent_review_v1`. The authoritative decision is the
trusted repository owner's exact-tree squash decision plus the official Codex exact-head review;
owner process attestations are non-independent. The post-merge CI observation is mandatory but
non-authoritative. Resistance to a malicious or compromised repository owner is out of scope.

PR #91 is also the external bootstrap trust root for the V1 docs candidate: its immutable
exact-tree owner decision and official exact-head Codex review must precede docs PR #386's merge.
It anchors the candidate head/tree, normative manifest, policy, semantic-validator and test blobs,
the normalized V1 semantic projection, and critical invariants including runtime-source authority
and forbidden caller control. Refreshed same-change-set docs hashes or validator results are not
independent authority and cannot weaken that bootstrap semantic anchor; docs contain no reference
to an unknown PR #91 merge SHA.

The ordered `authorized_issues` list in `plan.yaml` is the sole normative execution scope:
FMV3-M0-01, FMV3-M0-02, FMV3-M0-03, FMV3-M0-06, FMV3-M1-00, FMV3-M1-01,
FMV3-M1-02, FMV3-M1-03, FMV3-M1-04, FMV3-M1-05, FMV3-M1-06, FMV3-M2-01,
FMV3-M2-02, FMV3-M2-03, FMV3-M3-01, FMV3-M3-02, and FMV3-M3-03. Milestone names
are non-authoritative grouping labels. This amendment corrects FMV3-M1-05, FMV3-M1-06,
and FMV3-M2-01 without changing the allowlist.

Authorization ignores caller Git configuration and objects after validating the supplied path shape.
The trusted launcher resolves canonical `Project-Helianthus/helianthus-execution-plans` main
through the fixed GitHub API, fetches that exact SHA from a hardcoded canonical URL into a new
owner-private checkout, and runs Git with system/global config, hooks, fsmonitor, credential
helpers, replacements, grafts, and alternates disabled. The launcher and anchored validator both
accept only the same plan-bound pinned Git and GitHub CLI executable digests, verify candidate
symlink and opened-inode stability, pass only the exact plan-bound child environment allowlists,
authenticate the PR #91 merge SHA first, materialize the validator blob directly from that
immutable commit, verify its anchored SHA-256, and only then execute the one-use blob. The claim owner supplies an
external owner-only mode-0400 256-bit secret; only its commitment enters the public claim. The
internal call binds the exact selected open GitHub issue number and one lowercase run UUID. A
self-consistent caller-supplied executable hash is never sufficient. PR-head validation receives
no GitHub token and no persisted checkout credential. Hosted Ubuntu exercises the unmodified
launcher against its platform allowlist before merge and authenticates the real PR91 anchor from
trusted canonical main after merge. The versioned launcher reference and SHA-256 are bound in the
PR91 tooling record; the installed external copy must remain byte-identical. The checked-out
candidate validator is defense-in-depth and is never the bootstrap trust root.

FMV3-M0-01 creates only the two empty public repositories `helianthus-modbus` and
`helianthus-modbusreg`. M0-02 and M0-03 each then use their sole destination-initialization
exception: direct push of exact no-parent commit `bd15e364a749adcca283570f027bfb826198952a`
with the empty tree `4b825dc642cb6eb9a060e54bf8d69288fbee4904` and no content, solely to establish
`main` as the legal base for issue #1 / PR #2. All later changes use branch/PR/squash flow.
FMV3-M1-05 publishes the public
`OPAQUE_RUNTIME_ACQUISITION_V1` companion, FMV3-M1-06 implements it after M1-05, and
FMV3-M2-01 consumes the merged M1-06 producer by exact full-SHA pin. Private governance
creation FMV3-M0-04 and destination bootstraps FMV3-M0-05/FMV3-M0-07 remain deferred.

Every authorized issue must prove completion of exactly its direct `depends_on` predecessors.
Completed FMV3 predecessors use immutable exact live-GitHub bindings for repository, issue and PR
titles/numbers, closing body and timeline relation, closure time, base/head/merge/tree/topology,
canonical-main ancestry, exact selected-issue branch and issue-contained PR interval, and exact-head
required checks bound by immutable check-run ID and completed before merge. M0-01 binds the exact no-object repository
creation closure and unedited completion-attestation comment. M0-02/M0-03 additionally bind the
shared exact empty-tree root commit, no-parent topology, message, PR #2 base, and subsequent squash
completion. Those are the only destination-initialization exceptions. Every unresolved direct predecessor must appear exactly
once in the bounded external `dependencies` certificate array; exact set equality rejects missing,
duplicate, extra, and non-direct rows. Each row binds exact repository, issue/PR selectors,
an anchored issue-spec digest and marker, head/tree/merge SHAs, the complete dynamic main
required-check policy, and an ordered exact check-run ID for every policy row, all authenticated
live. Every authorization-relevant required check has a concrete positive GitHub App ID and must
have completed before the selected PR merge; legacy context-only, any-app, unbound, and post-merge
rerun evidence is rejected.
M2-01 retains its producer extension, which must equal its M1-06 dependency row. Stale, unmerged,
wrong issue/PR, failed-check, wrong-tree/topology, or non-main evidence fails closed.
M1-05 completion is the exact docs issue #385 with its immutable title and repository, closed by
docs PR #386 through an exact `Closes #385` body line, live timeline relation, and authoritative
GraphQL `closingIssuesReferences`, with issue closure inside a bounded 60-second post-merge window. FMV3-M1-06 requires docs PR #386 merged with the exact bound candidate
head and tree, dynamically ancestral to canonical docs main, with all exact-head required checks
successful under its concrete app-bound policy, one official Codex exact-head `COMMENTED` review using the
exact canonical no-suggestions template and zero inline findings, and two owner structured
`NO_FINDINGS` process attestations submitted after CI. FMV3-M2-01 additionally accepts only external selectors for the
M1-06 issue, sequential harness and closing product PRs, merge and RED commit SHAs, anchored
RED/GREEN/mutation runs, official Codex review, and exactly two owner reviews; selector values
are not trusted outcome claims. Live GitHub must prove the exact immutable issue title and
`<!-- helianthus-fmv3-m1-06-opaque-runtime-acquisition-v1 -->` marker. Under that issue, an
owner-authored harness PR uses the selected issue branch, opens after that issue, is the sole active PR, adds only the exact plan-anchored dual-mode
workflow, executable-AST guard, docs-lock validator, and exact merged-docs lock, leaves inherited `ci.yml` and `ci_local.sh` blobs unchanged,
passes the certificate-bound pre-merge required check runs, with the checks job bound to its exact workflow attempt, job, and check-run IDs, and one clean exact-head Codex review,
and merges before product work.
The product PR starts from exactly that harness merge and then proves canonical same-repo
main/base/head identity, exact issue closure, reviewed head-tree equality with the one-parent
squash merge tree and PR base, and canonical-main ancestry. The RED commit carries the exact
pinned subject and is an implementation-head ancestor whose bounded first diff page contains only
Go tests, fixtures, or the fixed conformance-report path; diff page two is empty. Its exact anchored
`pull_request` workflow passes the test-only guard and compile/no-tests before the exact M1-06 suite
fails. All dynamically required checks then succeed on the exact implementation head, and the same
anchored workflow proves conformance success. RED, GREEN, docs, and mutation completion evidence
binds immutable app/check-run IDs; harness checks, RED, GREEN, and mutation evidence also bind the exact workflow
attempt and job IDs, so a later same-name rerun cannot invalidate or replace the certificate. Eight ordered production-Go-only mutant commits are
direct children of GREEN and retain the exact harness blobs. The GREEN report precommits each
canonical GitHub patch digest; each anchored mutation run passes executable-AST validation, the
mapped test on the GREEN parent, and compile/no-tests before that mapped test fails on the mutant.
One official Codex exact-head review after those mutations must use the exact
canonical no-suggestions template and have zero inline findings. Two owner `COMMENTED` closed-schema
`NO_FINDINGS` process attestations after GREEN and mutations must bind the exact RED/head/tree,
fixed conformance-report blob, validator-pinned case digest, and mutation-evidence digest. The regular committed report
`.github/fmv3/fmv3-m1-06-conformance-report.json` must use
`helianthus.fmv3-m1-06-conformance-report.v3`; its closed fixed case set binds deliverability
exclusions, copy one-winner, stale same-key instance cancellation isolation, terminal outcomes,
membership close/registration race,
bounds/overflow, sequence exhaustion, and coalesced isolation to exact Go test declarations,
source blobs, regular modes, nonempty failure/assertion bodies, semantic calls, `PASS`, and the
exact per-case mutation patch digest. Its exact module-root package projection binds fixed
`GOOS=linux`, `GOARCH=amd64`, `CGO_ENABLED=0`, `GOWORK=off` and the complete sorted
`GoFiles`/`CompiledGoFiles`/`TestGoFiles` set while every cgo, ignored, external-test, C/C++/assembly,
SWIG, syso, embed pattern/file, or other non-Go compiled-input category is empty. The trusted premerged guard runs
`go list -compiled` and `go/types`, binds every symbol by declaration kind, receiver, signature, and exact object identity, and credits a required test call only when its result directly controls a live failing assertion condition.
Every bound source must be in the same package and root directory,
must have no explicit or implicit build exclusion, cgo import, or nested module, and test files may
not redeclare or locally shadow any production contract symbol; every named conformance test has exactly one declaration. Its
production Go blobs must declare every fixed contract symbol. Missing, stale, fake, failed,
semantic-no-op, non-direct, or mismatched producer proof fails closed.
The exact docs R2 commit/tree, complete predecessor-inclusive normative closure, and expanded
machine projection including `bounded_values` and `downstream_conformance` are bound. They require
an opaque per-incarnation `AttemptInstance`, atomic membership close and freeze before ledger
admission, claim-in-progress, cancelling, a nonempty exact ordered all-runtime dependency set,
source-owned `CancelOpen(AttemptInstance)`, one atomic publish/cancel winner, the closed five-field
`published_attempt_v1` projection, byte/field bounds, and pre-reserved non-wrapping, non-reused
terminal sequences. M1-06 and M2-01 CI must lock the merged docs full SHA plus policy and manifest
hashes and run the eight downstream behavioral rows. Both issues still fail authorization until
docs PR #386 is merged at that exact head and tree.

The hard stop is immediately before FMV3-M4-01. Gateway work is not authorized. No gateway
issue, branch, PR, import, or code change is authorized by this action. Repository creation,
implementation issues, commits, pushes, reviews, and merges are authorized only for the
ordered issue list above and remain subject to every direct dependency and gate.

## Claim discipline

**Proven**

- `Project-Helianthus/.github` is the existing organization-governance repository that
  owns creation of the two public Modbus repositories in this execution wave.
- The four planned repositories `helianthus-modbus`, `helianthus-modbusreg`,
  `helianthus-eebus-binding-private`, and `helianthus-matter-binding-private` do not
  have local checkouts at drafting time.
- Existing local checkouts include the gateway, registry, documentation, Home
  Assistant integration, and Home Assistant add-on repositories.
- The operator's Huawei corpus distinguishes SmartLogger material from S-Dongle
  material and documents v49 and v52 as parallel firmware branches rather than a
  monotonic sequence.

**Hypothesis**

- One transport/runtime library and one multi-profile registry can serve Fronius,
  SunSpec, Growatt, and Huawei without coupling endpoint behavior to register meaning.
- A generic private eeBUS binding can expose locked PV semantics in a form accepted by
  myVaillant.

**Unknown**

- The exact Fronius models, firmware variants, unit topology, exposed blocks, and
  optional devices that will pass the phase-1 lab gate.
- Which Growatt and Huawei combinations will meet evidence and hardware support gates.
- Actual myVaillant interoperability until the M6 lab test passes.
- EMMA register and gateway applicability. EMMA remains out of scope.

Normative statements below are plan decisions, not empirical claims.

## Objective

Deliver a public, reusable Modbus stack with a Fronius-first read-only vertical:

1. `helianthus-modbus` owns Modbus protocol operations, TCP and RTU transports,
   endpoint scheduling, limits, cancellation, reconnect, runtime observability, and the
   single MBAP transaction allocator/correlation map on each TCP connection, including
   the exact ordered abnormal transport-write result set `provable_zero`, `partial_write`,
   `indeterminate_error`, `cancellation_race`, `ambiguous_completion`, where only
   `provable_zero` avoids abandonment and all other abnormal results force TCP
   close/reconnect handling and RTU quarantine/resynchronization or endpoint recovery.
   Separate `full_transmit_success` enters `response_wait` for both transports.
   RTU remains default-disabled and experimental until `RTU_PHYSICAL_QUALIFICATION_V1`
   records adapter/transceiver, baud/topology, physical silent intervals, and
   timeout/cancellation quarantine evidence; absent hardware creates no support claim and
   blocks no TCP-sufficient work. Additive successor FMV3-M1-06 also owns the
   source-issued opaque, non-serializable, single-use runtime acquisition capability
   documented first by FMV3-M1-05.
2. `helianthus-modbusreg` owns one catalog of standard and vendor profiles, codecs,
   detector rules, fixtures, and profile conformance. M3 implements the minimal SunSpec
   standard family needed by Fronius before an evidence-dependent Fronius disposition;
   only qualified vendor-specific facts create an overlay. M7 later expands SunSpec, then
   evaluates Growatt and adds Huawei SmartLogger and Huawei S-Dongle packages.
3. The gateway-local `helianthus-ebusgateway/internal/modbusadapter` package implements
   the gateway's existing protocol-agnostic adapter interface and is the only gateway
   package permitted to import `helianthus-modbus` or `helianthus-modbusreg`; gateway core tests use the
   interface and a fake adapter. No additional repository is created for this boundary.
4. Existing public platform repositories own canonical semantics and public APIs.
5. Generic private eeBUS and Matter bindings consume exactly the same locked
   `PUBLIC_GRAPHQL_M2M_V1` contract and start implementation only after public consumers
   and packaged rollout complete. Both use authenticated bounded query/polling, compatible
   versions, noninteractive least privilege, a confidential channel with verified server
   identity, and credential lifecycle/recovery. The eeBUS binding uses the packaged machine-to-machine
   access contract documented publicly before GraphQL implementation for authenticated
   bounded polling of the stable versioned API over a confidential channel with verified
   server identity, fails closed for plaintext or untrusted identity, and invents no
   subscription. PV is their first vertical, not their repository identity.

The critical delivery path is M0 -> M1 TCP slice -> M1-05 docs -> M1-06 opaque capability
corrective -> M2 pinned consumer -> M3 -> M4 -> M5 packaged
public rollout -> M6.
RTU completion, vendor expansion, and Matter remain explicit work but do not gate the
Fronius-to-eeBUS lab result unless an issue dependency says otherwise.

## Layer and ownership boundaries

```text
transport/runtime
  helianthus-modbus: TCP, RTU, endpoint owner, scheduler, deadlines, reconnect
        |
Modbus protocol
  helianthus-modbus: ADU/PDU, read functions, exceptions, uninterpreted 16-bit words/bytes
        |
profile registry
  helianthus-modbusreg: detection, signedness/scale codecs, standard profiles, overlays
        |
gateway protocol adapter
  helianthus-ebusgateway/internal/modbusadapter: sole gateway importer of modbus/modbusreg
        |
canonical semantics
  helianthus-ebusreg: protocol-independent identity, quantities, quality, versions
        |
public APIs and consumers
  helianthus-ebusgateway semantic MCP -> public GraphQL docs -> GraphQL -> Portal -> HA integration/add-on
        |
private output bindings
  helianthus-eebus-binding-private via public GraphQL query/polling; matter binding via public contract
```

Dependencies flow downward only. `helianthus-modbus` has no profile, vendor, PV, or
private-binding imports. `helianthus-modbusreg` may import `helianthus-modbus`, but it
does not own sockets, serial ports, retry loops, canonical PV IDs, or consumers.
`helianthus-ebusreg` defines canonical meaning without importing Modbus or private
packages. Inside `helianthus-ebusgateway`, `internal/modbusadapter` composes
`helianthus-modbus` and `helianthus-modbusreg` behind the existing protocol-agnostic
adapter interface. It is the only gateway package allowed to import either module;
gateway core, semantic, MCP, GraphQL, and Portal packages depend on the interface or
gateway-owned neutral DTOs only. Private repositories may depend on published public
contracts; public source, CI, builds, fixtures, and documentation must never require a
private repository, path, secret, or generated private artifact.

`Project-Helianthus/.github` owns the M0 repository-creation issue. Destination bootstrap
issues depend on it and cannot start until each destination exists. Each executable issue
has exactly one repository owner. Cross-repository milestones are coordination groupings
only; issue dependencies determine readiness.
Each issue also fixes an integer `complexity` in the 1..10 canonical routing range. The
anchored launcher materializes the exact-hash `.codex/scripts/model_route.py` and
`model-routing-policy.json`, selects `docs/architecture` for the public docs repository and
`developer` otherwise, maps issue gates to the pinned risk vocabulary, and executes the router in
`openai_only` mode with the issue's exact complexity. Authorization requires a canonical receipt
bound to issue ID, repository, complexity, risks, plan anchor, router/policy hashes, profile,
OpenAI model, and effort. The launcher never accepts a caller assertion that `max` is available
and invokes the pinned router without a runtime-capability override. A route that requires `max`
therefore remains capability-degraded and blocks claim acquisition until a future plan-anchored
extension verifies provider-produced immutable execution evidence. Missing, mismatched,
capability-degraded, or underpowered routing blocks claim acquisition; the PASS line logs the
receipt digest and resolved profile/model/effort. The receipt is only an enforced routing
prescription and makes no runtime-capability or remote-model-identity claim.

`plan.yaml` also declares a per-repository mutex owned by `cruise-topology` and
`cruise-preflight`: at most one active issue and one active PR per repository. Preflight first
checks live GitHub state, then acquires exactly one deterministic remote ref per repository under
`refs/heads/fmv3-claims-v2` in the execution-plans control repository. Integrity ruleset
`20195126` has no bypass and rejects deletion or non-fast-forward updates; writer ruleset
`20195127` restricts creation/update to the repository-administrator bypass. Preflight also
requires authenticated actor `d3vi1`/`16434603` and the plan-anchored HMAC owner commitment for
ledger `fmv3-pr91-v2`, owner epoch 1, and the external 0400 owner secret. The first `ACQUIRE`
parents canonical main; every `RENEW`, expired `TAKEOVER`, later `ACQUIRE`, and `RELEASE` is a
fast-forward child of the exact observed claim SHA with the same tree. Every event has an HMAC over
its canonical payload and binds state, repository/ref, selected issue ID/number, plan anchor, run
UUID, owner identity/epoch/commitment, predecessor, authoritative-main SHA, monotonic uint64
generation, event time, and six-hour expiry. The pinned GitHub CLI obtains lease time from the
unique authenticated API `Date` header. Every observed tip is checked through the same-tree,
generation-by-generation HMAC chain to genesis, bounded at 512 events, with exact transition and
TTL semantics. Held-event creation reserves the final event for `RELEASE`; the owner must then use
a future anchored epoch rotation instead of overrunning the history budget. Release is exposed only
through the same authenticated launcher using `--release-claim` with the exact issue number, run
UUID, plan anchor, private owner secret, and exact acquired claim SHA, and appends a release
tombstone instead of deleting the ref. Therefore an earlier owner cannot release a renewed or
successor generation, and delete/recreate cannot reset generation or ownership. A post-claim race
appends a tombstone only after its exact claim. Any active
non-PR issue, regardless of title prefix, participates in the mutex, and the sole allowed active
issue must match the selected issue number, exact anchored title, and marker.
The returned fence is `(ledger_id, generation, claim_sha, expires_at)`. Claim-ref
acquire/renew/release always re-read the exact remote ref after `git push`, including
after a nonzero client result. An exact `target_sha` is reconciled success; every other result or
unavailable re-read is completion-ambiguous and forces `STOP` without retry pending reconciliation.
Standalone `--verify-claim` is diagnostic and never authorizes a later mutation. Protected GitHub REST
mutations run only through `--fenced-gh-api`, which holds a stable kernel loopback-socket process
lock for the full operation plus an exclusive lock on the 0400 owner-secret inode, verifies the
exact signed live tip and strict `now < expires_at`, requires one declared issue-bound capability,
validates its endpoint and security-relevant payload fields from retained in-memory bytes, sends
only those bytes to the pinned CLI over stdin, and verifies the same fence again before returning.
Postflight runs after every attempted child-process exit, including interruption or an exception;
such an outcome remains completion-ambiguous and forces `STOP` without retry. Both checks also re-read the exact
selected issue and the capability-specific live PR mutex. PR creation requires zero open PRs before
the mutation and exactly one same-repository `main` PR from the exact selected issue branch after
it, with title exactly `<issue id>: <anchored what>` and exactly one closing reference to that issue;
comments and labels permit at most that same exact-title/exact-closing selected PR; repository creation permits none.
Any competing PR observed in either check makes the operation completion-ambiguous and forces
`STOP` for reconciliation. Each validator invocation uses a
fresh private one-shot directory. The allowlist covers only exact-schema comments/labels on the
exact selected issue, exact-schema PR creation with exactly one closing reference to that issue, and
FMV3-M0-01 creation of either named repository through one exact public/no-auto-init/issues-enabled/
other-features-disabled/non-template payload; unrelated same-repository issues, issue edits, extra
closing references, extra creation fields, and undeclared mutations fail closed. `--renew-claim`
requires the exact current claim
SHA and same anchored run, appends a signed `RENEW` or expired `TAKEOVER`, and returns a successor
fence. GitHub provides no atomic compare-and-swap spanning the control ref and another repository:
therefore either a nonzero mutation result or a failed post-check means the mutation may have
completed and forces `STOP` without retry plus operator reconciliation; it is not reported as
atomic exclusion. Ruleset administrators, GitHub
and TLS are trusted, possession of the owner secret is owner authority, and loss requires a future
anchored owner-epoch rotation. The stable lock is host-local; multi-host ownership is not provided,
and pre-binding the lock port can only deny authorization. Authorization is not a timeless lease.
Issue branches are created and deleted only through ordinary Git push operations under the active
repository claim; the REST capability surface does not expose `git/refs`.
The owner-private canonical checkout fetches the full history reachable from the exact observed
`main` SHA rather than a depth-one tip, so the immutable PR #91 anchor remains available after later
canonical commits. Every required-status `contexts` entry must be represented by an app-bound
`checks` entry with a positive App ID. The two docs owner-process attestations use strict lowercase
UUID syntax and have independently unique run references and output digests.
The post-merge workflow checks out and asserts the exact push-event `github.sha`; it never resolves
the moving `main` name after the run is queued.

## Standard profiles and vendor overlays

SunSpec is treated as a standard profile family: its model identities, model chains,
quantities, scale rules, and version applicability are represented without assuming one
manufacturer. A device may also expose behavior outside the applicable SunSpec family.
Fronius applicability is therefore evidence-dependent: M3 records `STANDARD_ONLY` when
the required Fronius slice is fully covered by qualified standard facts, or
`OVERLAY_REQUIRED` only when qualified model, firmware, gateway, access, and scale evidence
proves vendor-specific facts. FMV3-M3-01 is the public companion for M3-02/M3-03.
`STANDARD_ONLY` records public evidence/disposition, passes conformance CI, and creates no
implementation commit or empty overlay; only `OVERLAY_REQUIRED` invokes overlay TDD/code.
M3-03 CI always enforces the fixed TCP-import boundary test and the non-TCP neutral-fake
activation test, including when `STANDARD_ONLY` proves that no overlay package exists. Every
production overlay and every Fronius production token are confined to `profiles/fronius`. The
bound minimal neutral adapter has no imports or additional declarations: it contains only the
zero-argument error-returning `NeutralRuntime` method and the matching activation call. It is
test-only under `STANDARD_ONLY`; under `OVERLAY_REQUIRED` it is production source inside the
overlay namespace and a separate non-test implementation source is mandatory. Completion requires
an exact executable, fail-closed immutable source-directory scanner in the canonical test: it uses
`runtime.Caller(0)` and `filepath.Dir` to derive the compiled canonical test-source directory,
then `os.ReadDir`s that absolute directory and parses every direct non-test `.go` file through its
`filepath.Join(directory, name)` path without excluding build-constrained or implicitly excluded
filenames. It fails closed on caller, directory/read, parse, unquote, or zero-production-file
errors, so a production `init` that changes cwd cannot redirect the scan. Its exact path-component
predicate returns the offending import when it matches the validator's `net`/TCP/Modbus-TCP rule.
Scanner-only test imports are narrowly admitted; production imports remain unchanged. Completion rejects same-line semicolon import declarations and
empty, dead, or data-flow-disconnected named tests. The one canonical disposition-bound source is
`registry/fronius_overlay_test.go` for `STANDARD_ONLY` or
`profiles/fronius/fronius_overlay_test.go` for `OVERLAY_REQUIRED`; it is in the exact proof
package/directory and cannot locally redeclare `NeutralRuntime` or `activateFroniusProfile` outside
the bound proof source. It declares the exact scanner helpers
`froniusOverlayProductionPackages` and `hasTCPConcreteImport`, plus
`NeutralRuntime` and `activateFroniusProfile`, whose return comes from a neutral runtime
operation. The zero-field `neutralRuntimeNoTCP` carries a compile-time assertion and returns a
sentinel error which the activation test observes. Production overlay sources have no build
constraints, `init`, or test-only fake/sentinel symbols. Named tests have no explicit or implicit
build constraints or nested module. The exact unskippable workflow first removes every other
direct sibling `_test.go` source in that proof package, then performs a standalone production
`go build` of the exact package target, runs neutral activation first, and runs import-boundary
second. `STANDARD_ONLY` proves the complete exact PR-base-to-head diff is evidence-only and has
no production implementation: unchanged base production is trusted, but a cwd mutation cannot
redirect the immutable source-directory scan, and legitimate immutable base `init` is not banned.
`OVERLAY_REQUIRED` additionally proves at least one exact-tree
`profiles/fronius` package plus a RED ancestor whose complete parent-tree-to-RED-tree diff is
nonempty and test-only. RED evidence proves preparation and build succeed, activation fails, and
import has no success result; GREEN evidence proves preparation, build, activation, and import
all succeed. Completion schema `helianthus.fmv3-m3-03-completion.v2` binds selected GREEN and,
when required, RED runs by exact workflow path/blob, run attempt, job, and check-run IDs; later
reruns cannot replace either selected attempt. `STANDARD_ONLY` carries no overlay RED evidence.
Growatt and Huawei packages follow the same evidence rule for any overlay they admit.

An overlay may add or refine raw profile facts. It may not silently override a standard
fact, invent canonical meaning, weaken detection, or create a vendor-specific transport.
Conflicting eligible interpretations are an ambiguity and block activation.

Every versioned profile codec declares how raw words become a value. Its descriptor records
multi-register composition order (`high_word_first`, `low_word_first`, or
`not_applicable`), applicable byte order within each word (`high_byte_first`,
`low_byte_first`, or `not_applicable`), and for strings the encoding, byte traversal,
fixed length, pad byte, pad side, and trim policy. The selected descriptor and codec version
are decode provenance. `helianthus-modbus` preserves received words/bytes in order and owns
none of these interpretation choices.

## Deterministic read-only detection

Detection is a pure, bounded decision over a declared endpoint and unit identity:

1. Read transport-neutral identity evidence allowed by the profile catalog.
2. Evaluate static gates such as vendor, model, profile family, firmware or software
   package, gateway type, and profile version.
3. Execute only the minimum ordered read probes needed to distinguish remaining
   candidates. Probe addresses, sizes, count, total words, and deadline are bounded.
4. Record every successful, failed, illegal-address, timeout, and malformed response as
   detector evidence.
5. Select exactly one primary profile and explicit compatible overlays, or fail closed.

No write probe is permitted. No match, multiple matches, missing required identity,
unsupported version, inconsistent gateway evidence, probe-budget exhaustion, timeout,
or partial dependency data leaves the endpoint inactive for that profile. Raw diagnostic
access may remain available within authorization and bounds. Explicit operator selection
may narrow candidates but cannot bypass compatibility or evidence gates.

Every catalog entry also carries an activation lifecycle state. A fixture-only profile is
`experimental_opt_in`, is disabled by default, and can run only after explicit operator
opt-in while all normal identity, compatibility, and read-only gates still pass. It is not
auto-eligible and creates no support claim. `auto_eligible` requires a matching hardware
qualification record bound to profile version, model, gateway, firmware/software branch,
and transport. A missing, mismatched, revoked, or disabled qualification record prevents
automatic activation and safely demotes an active profile on re-evaluation.

The selected identity record contains endpoint identity, unit identity, profile ID and
version, detector version, model and firmware evidence, probe transcript reference, and
selection reason. Reconnect does not silently retain selection when identity evidence has
changed; re-detection occurs under a bounded policy.

## Source observation, canonical value, and provenance contract

`helianthus-modbus` returns uninterpreted 16-bit words/bytes plus transport identity and
timing. Every physical request/range response has a unique `wire_response_id`; every
dependent logical observation has a linked `logical_view_id` and exact slice identity. It does not assign signedness, units, scale, validity,
quality, or freshness.
`helianthus-modbusreg` codecs interpret signedness, scale, composition, and packing and emit
a source observation with:

- decoded value and source `validity`, distinct from canonical quality;
- source observation timestamp and receipt timestamp;
- endpoint, unit ID, source profile/version, detector version, engineering unit, scale
  rule, raw type, signedness, and access mode;
- codec version plus declared multi-register word order, applicable intra-word byte order,
  and string encoding/packing/padding fields or explicit `not_applicable` values;
- `sample_id`, `poll_generation_id`, `dependency_set_id`, and the complete
  identity/membership of every raw dependency used by the decode;
- for each raw dependency, endpoint, unit ID, function/table, logical zero-based PDU
  offset/count, `logical_view_id`, linked `wire_response_id`, and slice offset/count;
- raw provenance sufficient to reproduce the decode from a sanitized fixture or bounded
  raw reference, including source evidence identifier, the documentary notation, and the
  recorded normalization from documentary one-based register notation when applicable to
  the zero-based PDU offset.

`sample_id` binds the exact wire-response/logical-view set accepted for one decode; every bounded validation
or re-read response remains in its coherence transcript, and IDs are never reused across
attempts. All members of a dependency set must belong to one `poll_generation_id`;
mixed-generation input is rejected, not merged. Each profile declares a coherence rule.
Unequal overlapping reads share one wire response only when unit, table, authorization,
generation, and deadlines are compatible; each logical view replays exact words and
provenance. A multi-response sample must complete
inside a bounded profile-declared coherence window and pass its validation or bounded
re-read recipe; otherwise no source observation is emitted. A changed dependency during
validation is a torn read, not a partial value. The gateway propagates source
validity/timestamps and sample/generation/dependency/response identities unchanged.
Partial, incoherent, or torn reads do not create a new source observation.

Runtime acquisition trust is not inferred from serializable request fields or caller
booleans. Only the runtime source, after request-bound correlation proves successful data,
the dependent is still attached, its exact logical slice validates, and production is
coherent, may issue an opaque non-serializable capability from private source-owned state.
That state is shared only by copies of the same capability and is never an M2 ledger
pointer; racing copies have exactly one CAS winner. Detached, cancelled, exceptional,
malformed, failed, late/abandoned, uncorrelated, torn/incoherent, and every other
non-success acquisition receive no capability. Every coalesced dependent receives an
independent capability. Endpoint
recreation and every new acquisition create fresh independent state even when visible
identity or data match; they cannot alias, remint, reset, or merge prior state, and an
existing capability remains governed only by its own acquisition/attempt lifecycle.
Each attempt incarnation has an opaque, unforgeable, non-serializable `AttemptInstance`;
`AttemptKey` is documentary identity only. Every capability registers against that instance
before visibility. Ledger admission atomically changes membership from open to closing, blocks
late registration without exposing a capability or retained open state, drains pre-close
registrations, and freezes the exact ordered member set. A stale instance cannot cancel a later
same-key incarnation. `CancelOpen` accepts only the exact closed `AttemptInstance` and returns
after its registered operations, reclamation, and open members have drained.
Capabilities move once from `open` to exactly one immutable terminal state: `claimed`,
`cancelled`, `failed`, or `expired`. Before terminal return the source removes terminal
state synchronously in source-assigned terminal-sequence order and retains only bounded,
non-reconstructing immutable metadata; the finite-positive tombstone ring evicts the lowest
terminal sequence first. `source_kind: offline_fixture` receives no capability.

`helianthus-modbusreg` pins the full 40-character merged FMV3-M1-06 producer SHA before
consuming this contract. Its private M2 ledger is independent of M1 capability state.
Every admitted claim moves `unresolved -> claim_in_progress` only while its attempt is
`open`, then moves exactly once to `claim_succeeded`, `capability_cancelled`,
`capability_failed`, `capability_expired`, or `claim_rejected_terminal`; only cancellation
may move a still-`unresolved` claim to `attempt_cancelled`. Attempts permit exactly
`open -> sealed|cancelling`, `sealed -> publishing|cancelling`,
`cancelling -> cancelled`, and `publishing -> published|publish_failed`; all terminal
outcomes are immutable. The predecessor's nonempty, unique, exact ordered dependency set is
domain-separated and hashed with count and order; permutation, omission, duplication, extras,
or cardinality mismatch fail before allocation, sequence reservation, or capability CAS.
Cancellation blocks admission, seal, and publish, waits for every `claim_in_progress` operation
to finalize, and closes only remaining `unresolved` claims. Seal atomically requires exact
cardinality, an all-runtime data-bearing set, and every claim `claim_succeeded`; empty,
fixture-only, mixed, duplicate, omitted, or reordered sets cannot seal. `Publish()` is exactly
the one-shot `sealed -> publishing` transition and uses immutable sealed ledger state without a
mutable DTO. Its transactional commit couples the irreversible external effect with
`publishing -> published`: cancellation wins before commit as `publish_failed` with no external
effect, while cancellation after commit returns `already_published` without mutation. Neither
outcome retries. The only public result is `published_attempt_v1` with exactly schema version,
attempt terminal sequence, dependency-set digest, runtime dependency count, and claim-outcome
digest; raw keys, instances, identities, evidence, diagnostics, protocol data, and secret canaries
are absent from fields and bytes. Finite-positive hard limits cover every
retained attempt state (`open`, `sealed`, `publishing`, `published`, `publish_failed`,
`cancelled`), every retained claim state, claims per attempt, the checked product of
retained-attempt and claim limits, and the audit/tombstone ring. Zero, negative,
overflowing, or inconsistent limits fail before activation. Terminal state is reclaimed
deterministically and synchronously on terminal/admission only when no operation is in
progress and no nonterminal reference remains, in ledger-assigned terminal-sequence order.
The finite-positive ring retains only non-reconstructing immutable terminal metadata and
evicts the lowest terminal sequence first. Offline fixtures perform zero capability CAS
operations and cannot receive a production `sample_id`. The versioned normalization record
preserves source kind, evidence identity, documentary notation/address/base, function/table,
normalized zero-based PDU offset, word count, and unknown extension fields with exact record
round-trip.

Only `helianthus-ebusreg` maps source validity/timestamps to canonical quality and owns
freshness deadlines, last-good retention, stale/unavailable transitions, expiry, stable
IDs, meaning, compatibility, and schema versions. Counter rollover, reset, device restart,
and decreasing values are canonical state transitions, not codec guesses.

## Runtime contract

The shared scheduler belongs in `helianthus-modbus`, not in profile packages. One runtime
owner exists per physical endpoint. On each TCP connection/socket, exactly one MBAP
transaction-ID allocator and one in-flight correlation map own requests for every unit ID
using that socket. Endpoint scheduling and bounded connection resources are shared, while
unit and profile lifecycle/decode state remains isolated. Normal FC03/FC04 responses do not
echo the requested offset: the offset remains request provenance, while delivery matches the
active connection generation and transaction ID plus echoed unit/function and applicable
expected byte-count constraints. For RTU, serial timing and bus serialization use the same
request envelope, deadline, cancellation, fairness, and observability contracts plus the
abandonment quarantine below.

The runtime provides:

- bounded endpoint, request, word, response, queue, in-flight, retry, and memory limits;
- fair scheduling across units and profiles with starvation tests;
- coalescing only for compatible overlapping reads whose unit, table, authorization,
  generation, and operation deadlines can all be preserved, with one physical-range
  `wire_response_id` and an exact-slice `logical_view_id` per dependent observation;
- one absolute operation deadline across queue, connect, transmit, receive, retry, and
  backoff, with cancellation releasing waiters and resources;
- one exact ordered abnormal transport-write result set: `provable_zero`, `partial_write`,
  `indeterminate_error`, `cancellation_race`, `ambiguous_completion`; only `provable_zero`
  avoids abandonment after invocation, while the other four are possibly transmitted;
- a separate `full_transmit_success` transition to `response_wait` for TCP and RTU; normal
  full transmission is not `ambiguous_completion`;
- bounded exponential reconnect backoff with jitter, reset rules, and no tight loops;
- TCP correlation that checks the active socket generation and MBAP transaction ID plus the
  echoed unit/function and applicable byte-count response shape before delivery, with the
  requested zero-based PDU offset retained only as provenance;
- after full TCP transmission, response-wait timeout or cancellation tombstones the
  transaction ID, drops any late response, and forbids same-socket reuse until the normal
  tombstone rollover policy; successfully completed, non-abandoned IDs remain governed by
  the bounded allocator and no-in-flight-collision rules;
- controlled close/reconnect on tombstone exhaustion, incrementing connection generation
  before a tombstoned ID can be reused and rejecting every old-socket/generation frame;
- for every TCP possibly-transmitted write, tombstone the ID, close the connection to
  prevent stream desynchronization, reconnect with incremented generation, and reject the
  old generation;
- after `full_transmit_success` on RTU, response-wait timeout or cancellation admits no
  successor transmit until the bounded endpoint-declared response-latency
  interval and bus-idle resynchronization quarantine both complete; all quarantine frames
  are discarded, and failure to reach quiescence disables and recovers the endpoint;
- apply that same RTU quarantine/resynchronization or endpoint recovery before a successor
  for each possibly-transmitted write result: `partial_write`, `indeterminate_error`,
  `cancellation_race`, and `ambiguous_completion`;
- stable response identity, malformed-frame isolation, exception propagation, and no
  cross-unit or cross-request data reuse;
- health and metrics for queue depth, wait time, coalescing, retries, timeouts, reconnect,
  source-observation gaps, and per-endpoint resource use.

Profiles submit declarative read intents and decode complete responses. They do not own
connections, MBAP allocation/correlation, polling loops, retries, backoff, cancellation, or
endpoint locks. The runtime matches protocol identity only and never interprets profile
signedness, scale, word/byte order, strings, provenance, or canonical meaning.

`Transport write` above means sending a read request through socket/serial I/O; it does not
authorize a Modbus write function.
Write support is explicitly deferred to a separate safety plan. Phase 1 exposes no write
function, write probe, generic raw write MCP tool, semantic control, or configuration bit
that can enable writes.
The exact phase-1 operation allowlist is FC03 Read Holding Registers, FC04 Read Input
Registers, and FC2B/MEI0E Read Device Identification. `helianthus-modbus` owns MEI
conformity levels, object IDs, segmentation/more-follows, bounded aggregation, exceptions,
and malformed responses on TCP and RTU. `helianthus-modbusreg` may request these operations
but never owns PDU framing.

## Delivery phases

### M0: governance and bootstrap

The existing `Project-Helianthus/.github` governance repository owns one issue that creates
the two empty public Modbus repositories. Each public destination then uses one exact empty-tree
root commit to establish `main`, followed by its issue branch and squash-merged bootstrap PR.
That root is the sole direct-push initialization exception per destination. Private governance creation remains a future `.github` issue FMV3-M0-04; only
after it creates both empty private targets may destination bootstrap issues FMV3-M0-05
and FMV3-M0-07 run. All three require future explicit authorization. Destination work sets
license, module identity, ownership, CI, and dependency policy before product code.
Documentation fixes layer/licensing boundaries.
After the public Modbus repository bootstrap and boundary-doc issue, the existing bounded
companion issue FMV3-M1-00 publishes both the M1 Modbus protocol/read-only, TCP/RTU,
scheduling/recovery, response-correct MBAP matching, socket-lifetime tombstone/generation
rollover, abnormal transport-write linearization, separate full-transmit response-wait
transitions, RTU response-latency plus bus-idle quarantine, and runtime-versus-codec contracts
and the complete M2 source-observation/provenance, detector activation lifecycle, hardware
qualification, coherence, and fixture/mutation contracts. It is one public docs issue/PR,
merged before any M1 or M2 implementation; FMV3-M1-01 through FMV3-M1-04 and FMV3-M2-01
through FMV3-M2-03 all depend on it directly or through explicit ancestry and carry its
doc-gate/companion metadata. That original history remains unchanged. The additive lane
introduced by PR #89 starts after FMV3-M1-04 and remains predecessor provenance. PR #91,
tracked by issue #90, is the sole current authority for its corrected fields: FMV3-M1-05 publishes
`OPAQUE_RUNTIME_ACQUISITION_V1`, FMV3-M1-06 implements it after both M1-04 and M1-05, and
FMV3-M2-01 adds M1-06 as a producer dependency while retaining its original M1-00
companion and recording M1-05 as the corrective companion.

### M1-M3: shared stack and Fronius fixtures

M1 first merges FMV3-M1-00, then establishes protocol, TCP, RTU, scheduler, and transport
gates, with FMV3-M1-03 depending on M1-02. M1-02 through M1-04 deterministically cover the
exact abnormal results `provable_zero`, `partial_write`, `indeterminate_error`,
`cancellation_race`, and `ambiguous_completion` in that order, separately from
`full_transmit_success -> response_wait`. TCP tests also cover mandatory close/reconnect on
possibly-transmitted abnormal results, response-wait timeout/cancellation tombstones, late
response drop, forbidden same-socket reuse until normal tombstone rollover, generation
rollover, old-generation rejection, and bounded successful correlation. RTU tests apply
quarantine/resynchronization or recovery to all four possibly-transmitted abnormal results
and to timeout/cancellation after full-transmit response waiting. FMV3-M1-04 names the exact
rows `tcp_full_transmit_timeout_tombstone`, `tcp_full_transmit_cancellation_tombstone`,
`rtu_full_transmit_timeout_quarantine`, and `rtu_full_transmit_cancellation_quarantine`.
RTU fixture conformance may close as `FIXTURE_ONLY_NO_HARDWARE`, leaving it disabled and
experimental with no supported/enabled claim. Only `PHYSICALLY_QUALIFIED` from
`RTU_PHYSICAL_QUALIFICATION_V1` permits such a claim; absent hardware blocks neither the
TCP/Fronius path nor TCP-sufficient M1/M7 work.
Protocol
outputs remain uninterpreted words/bytes in received order. After M1-04, the corrective
path is strictly docs-first: M1-05 documents source-kind, one-shot capability, per-incarnation
attempt membership, lifecycle, bounded-state, coalesced-dependent, copy/recreation,
lossless-normalization, ordered dependency, atomic publication, and closed-projection behavior;
M1-06 then proves the opaque capability with strict hosted RED/GREEN and fresh independent
review. M2 starts only with the same FMV3-M1-00 companion merged and M1-06 merged and pinned
at its full producer SHA, and establishes
versioned codec/source-observation/detector contracts and deterministic fixtures, including
physical `wire_response_id`, linked logical `logical_view_id`/slice provenance,
explicit word composition, applicable intra-word byte order, string packing/padding, and
mixed-generation rejection. M2-01 additionally proves the runtime/offline-fixture trust
split, independent bounded attempt ledger, complete claim/attempt terminal outcomes,
nonempty exact ordered all-runtime seal, one-winner immutable publish/cancel transaction,
five-field public projection, synchronous fixed-ring reclamation, fixture
zero-CAS/no-production-sample behavior, exact normalization round-trip, merged-docs hash lock,
and all eight downstream behavioral rows.
M3-01 is the public companion for M3-02/M3-03. M3 builds that provenance-qualified evidence packet, implements the minimal standard SunSpec
family needed by phase 1, then records the Fronius TCP read-only disposition. M3-03 returns
`STANDARD_ONLY` when M3-01/M3-02 prove the required slice fully standard, or
`OVERLAY_REQUIRED` only for qualified vendor-specific facts. Both dispositions retain
Fronius fixtures and later live qualification, pass read-only conformance, and unblock M4;
the standard-only path records evidence publicly with green CI and creates neither an
implementation commit nor an overlay artifact. Only overlay-required uses
`TDD_RED_IF_OVERLAY_REQUIRED`.
M1 fixtures prove that the same numeric offset under FC03/holding-register and
FC04/input-register identities cannot alias. M2 fixtures prove documentary one-based to
zero-based PDU normalization and reject off-by-one mappings. The replay/mutation harness
pairs opposing word orders, applicable opposing intra-word byte orders, and string
packing/padding policies so an implicit default cannot pass. It also changes a dependency
between responses and proves that a torn multi-response sample is rejected or successfully
re-read under its bounded profile coherence rule. Minimal and expanded SunSpec, Fronius,
Growatt, and Huawei issues each exercise every applicable order/packing case declared by
their versioned profile.

All code issues follow strict TDD: a test-only RED commit must exist and be observed red by
CI before implementation is pushed. Conditional disposition issues invoke that rule only
when their declared implementation branch is selected. Transport changes require the applicable transport
matrix. Protocol, semantic, licensing, or reverse-engineered knowledge changes require the
documentation gate.

For FMV3-M1-06 and the amended FMV3-M2-01 specifically, hosted CI must observe the exact
test-only RED revision failing for the intended missing behavior before implementation,
then observe GREEN on the implementation head. FMV3-M1-05, M1-06, and M2-01 each require a
fresh independent OpenAI adversarial review of the exact applicable revision; all findings
must be resolved or the reviewer must return `NO_FINDINGS` before merge. The historical
epoch 3 R5 remains immutable and does not retroactively review this amendment.

### M4: raw MCP and real-device proof

The gateway-local `internal/modbusadapter` package becomes the single owner of the
configured Fronius TCP endpoint and implements the existing protocol-agnostic adapter interface. Only that
package imports `helianthus-modbus` or `helianthus-modbusreg`; gateway core is tested
against a fake adapter/interface while adapter integration tests cover the real modules.
It exposes bounded raw reads and detector/profile observations through MCP before
canonical promotion.
The add-on provides validated configuration, secret-safe logging, a disable switch, health,
and restart recovery.

Fronius phase 1 has a `hardware_required` gate. Fixtures alone cannot claim support. The
lab starts from explicit experimental opt-in; a successful record qualifies only the exact
tested profile/hardware tuple for later automatic eligibility. The smoke test must prove
detection, bounded polling, raw MCP parity, coherent sample/response
identity, source observation stop/resume and generation integrity across
disconnect/reconnect, read-only traffic, resource bounds, and no regression to existing
gateway transport. FMV3-M4-04 records exactly `GO`, `NO_GO`, or `STOP`; issue completion
alone never satisfies the gate. FMV3-M4-05 packages the exact result and sanitized evidence
for any outcome. Only M4-04 `GO` plus completed M4-05 evidence packaging permits M5
raw/semantic work. `NO_GO` or `STOP` remains honest evidence, disables the endpoint, and
leaves all M5 work blocked; it does not block raw fixture work or require a public API
rollback.

### M5: semantic lock and public promotion

Only after M4 live evidence is sanitized does `helianthus-docs-ebus` publish the candidate
canonical PV contract. FMV3-M5-02 retains the M4 prerequisites and must merge before
`helianthus-ebusreg` semantic implementation starts in FMV3-M5-01. FMV3-M5-04 then creates
the candidate Fronius-to-canonical mapping and semantic MCP and runs that exact version
through golden and live Fronius tests, preserving wire-response/logical-view provenance.
A separate semantic-lock issue depends on M5-04 and reviews that tested MCP version,
schema, evidence, quality/freshness rules, and compatibility. FMV3-M5-03 records exactly
`GO`, `NO_GO`, or `STOP`; completion is not progress. `NO_GO` or `STOP` keeps raw and
candidate semantic MCP available for remediation and blocks M5-09 plus all later consumers.
FMV3-M5-04 is outside the semantic-GO before-set.

Promotion is strictly semantic MCP golden/live proof -> M5-03 lock GO -> public GraphQL companion docs -> GraphQL ->
Portal -> Home Assistant -> recoverable add-on packaging. FMV3-M5-09 is exactly one public
`helianthus-docs-ebus` issue/PR after FMV3-M5-03 and before FMV3-M5-05. It follows the earlier
FMV3-M5-02 docs work in the same serialized repository lane and publishes the exact
`PUBLIC_GRAPHQL_M2M_V1` schema projection, external access/security/channel contract,
compatibility/versioning, credential lifecycle, and recovery contract while retaining
M5-03 `GO` ancestry. FMV3-M5-05 carries that companion metadata and implements the documented
contract for a separately deployed service client. Any credential-bearing external use
requires an authenticated confidential channel with verified server identity before
credentials are sent. Plaintext external access and untrusted server identity fail closed.
It proves external-context reachability, noninteractive authentication and authorization,
least privilege, bounded polling/rate/resource behavior, and credential provisioning,
rotation, revocation, disable, and recovery without prescribing the channel or authentication
mechanism or weakening security. The
Portal issue contains two deliberately separate surfaces: its semantic PV view remains a
GraphQL-only consumer, while an authenticated raw diagnostics/register explorer reuses the
already-bounded raw service behind MCP with the same read allowlist,
endpoint/function/range and rate/resource budgets, secret redaction, and audit controls.
Raw registers are not added to semantic GraphQL and no subscription is introduced.
FMV3-M5-08 packages and repeats the public service-client test from an external service
context, including explicit plaintext rejection, untrusted-server-identity rejection, and
the same credential lifecycle and recovery contract.
Private implementation remains blocked until that packaged public rollout completes.

### M6: private eeBUS output and myVaillant

After the M5 public rollout, FMV3-M6-00 first publishes a sanitized permissive companion
for GraphQL ingress, SHIP/SPINE discovery, TLS/pairing, trust lifecycle, identity, encoding,
capability negotiation, PV exchange, security, and the public-knowledge boundary. Only then
does the private eeBUS repository deploy a generic
canonical-to-eeBUS output binding for all future device classes. Its only semantic ingress
is exactly the machine-to-machine public GraphQL contract documented by FMV3-M5-09,
implemented by FMV3-M5-05, and packaged/tested by FMV3-M5-08, consumed with authenticated and
authorized queries at a bounded polling cadence over the same authenticated confidential
channel with verified server identity. M6-01 rejects plaintext external access and untrusted
server identity and does not prescribe the channel mechanism; no GraphQL subscription is
assumed or invented. Its
first enabled slice maps locked PV semantics. A CI-observed RED commit precedes
implementation. FMV3-M6-01 tests deployment/configuration, authn/authz, GraphQL
schema/contract compatibility, polling reconnect/backoff, explicit disable, and
unavailable/stale propagation, together with minimum eeBUS SHIP/SPINE discovery and trust
lifecycle: discovery, SHIP TLS and pairing, persisted trust, reconnect, revocation/reset,
disable recovery, capability negotiation, identity, encoding, and a complete PV exchange.
It contains no Modbus transport, register addresses, Fronius detector, raw profile codec,
or gateway-internal logic. This plan creates no public eeBUS implementation repository.

Actual myVaillant interoperability remains a hypothesis until FMV3-M6-02 records exactly
`GO`, `NO_GO`, or `STOP`; completion is not progress and `GO` is the sole objective success.
GO requires an enabled, qualified live Fronius endpoint throughout the run and at least one
traced observation that is available, non-stale, and generated after the recorded lab-run
start. That same observation identity and value must traverse `PUBLIC_GRAPHQL_M2M_V1` and
eeBUS to an accepted myVaillant-side observable with matching canonical/source identity,
value, unit/value semantics, quality, source observation time, and receipt time. Replayed,
synthetic, retained-cache-only, fixture-only, simulator-only, handshake-only, or packet-only
input cannot GO. The existing public identity/time/quality contract carries this proof; no
new public schema field is required. The required lab also
verifies discovery, SHIP TLS/pairing, trust persistence across restart/reconnect,
revocation/reset and repair, and disable recovery while recording reproducible `GO` or
`NO_GO`/`STOP` evidence. M6-02 is real-lab only and simulator qualification belongs to
M6-01. FMV3-M6-03 follows the lab and publishes reusable sanitized protocol/interoperability
findings with provenance and licensing. Knowledge that cannot be published permissively
forces `STOP`; a private-only success or support claim cannot satisfy M6. `NO_GO` or `STOP`
retains honest evidence but does not complete the plan objective or unlock success, and no
outcome adds vendor logic or distorts the public schema.

### M7: vendor expansion

FMV3-M7-01 waits until the critical docs lane reaches FMV3-M5-09 and is the public companion
for M7-02, M7-03, and M7-04; profile implementation also waits for FMV3-M3-03.
Before M7-01 closes, its merged public packet publishes the complete Growatt candidate and
admission contracts, qualified candidate facts, admission criteria, provenance/licensing,
explicit unsupported disposition, and exact code/document mapping for both dispositions.
For every vendor candidate M7-01 enumerates all detector operations and proves each belongs
to the versioned phase-1 runtime allowlist; an unsupported operation forces non-admission
rather than protocol framing in modbusreg. For every SmartLogger and S-Dongle candidate it likewise publishes a complete
provenance/licensing-qualified register, codec, gateway, branch, version, detection, and exact
code/document admission packet, or records `NO_ADMISSIBLE_PROFILE`.
The single `helianthus-modbusreg` lane is then serialized: expand the minimal SunSpec
family, evaluate Growatt, then Huawei, then mixed-catalog closure. FMV3-M7-03 may finish as
`NO_ADMISSIBLE_PROFILE` after bounded evidence and licensing analysis; that disposition
preserves the pre-published public evidence and explicit unsupported status, creates no
implementation commit, catalog entry, support claim, or later companion docs change, and
releases FMV3-M7-04 without an extra conditional GO gate. `PROFILE_ADMITTED` alone triggers
RED-first fixtures/code against the already-merged companion and likewise requires no later
companion docs change. M7 adds raw/profile support only.
New canonical fields or consumer claims require their own live evidence and semantic-lock
cycle.

Huawei intake starts from operator-authored analysis, converted Markdown, gate tables,
enrichment tables, live snapshots, and audits, but does not copy conclusions as truth.
Evidence is re-inventoried by source, license, model, gateway, software package, firmware
branch, access, and live confirmation. v49 and v52 are parallel branches; a register present
or typed one way in one branch is not inherited by the other. Model or MEI evidence,
software package identity, gateway detection, and bounded read-only probes are revalidated.
Unconfirmed live values remain Unknown. The plan contains no exact Huawei register claims.
SmartLogger and S-Dongle remain distinct profile scopes. EMMA has no implementation issue
and its semantics stay deferred. M7-01 inventories EMMA gateway/model/software/version
discriminators or marks each unavailable. M7-04/M7-05 negative fixtures require EMMA or
insufficiently distinguished endpoints to return only `no_match` or
`insufficient_evidence`, never activate SmartLogger/S-Dongle, and block Huawei automatic
eligibility whenever reliable discrimination is unavailable. M7-04 creates RED-first code and
positive gateway/branch/version/detection/codec fixtures only for a `PROFILE_ADMITTED`
candidate backed by the published packet. `NO_ADMISSIBLE_PROFILE` creates no implementation
commit, catalog entry, or support claim.

Hardware classification for M7 is `hardware_conditional`: fixtures may publish an
`experimental_opt_in` profile that is disabled by default, but automatic eligibility and
a supported model/gateway/firmware claim require a matching real-device qualification
record. Mixed-catalog closure tests activation, explicit opt-in, qualification, demotion,
disable, and restart lifecycle without permitting a mismatched hardware record.

### M8: private Matter output

After the M5 public rollout, FMV3-M8-00 publishes the sanitized permissive Matter binding
companion for ingress, identity/capability/encoding, trust/credentials, compatibility,
unavailable behavior, recovery, and forbidden imports. Only then is the private Matter
repository generic across future
device classes and has exactly one ingress: packaged `PUBLIC_GRAPHQL_M2M_V1`, using the same
authenticated bounded query/polling, version compatibility, noninteractive least privilege,
confidential channel, verified server identity, and credential lifecycle/recovery contract
as eeBUS. M8-01 requires M8-00 ancestry, its companion metadata, and a security gate and rejects Modbus,
modbusreg, gateway internals, GraphQL subscriptions, and undocumented network paths. PV is the first test slice. M8
does not depend on M6 and is not on the M0-to-M6 critical path. Simulator conformance is
required; hardware is optional until a specific product-support claim is proposed.

## Recovery and stop/go rules

Every runtime/configuration issue includes an explicit disable or recovery action. Before a
public schema is published, rollback may remove the candidate and restore a pre-schema
binary. After publication, the schema and IDs remain: recovery uses a compatible forward
fix, deprecation, capability disable, or only a prior binary/image that still implements
that published schema. Disabled data becomes unavailable. A schema-less image may never
replace a published schema. Persisted state is versioned and may be ignored safely when
producer or schema compatibility fails.

GO requires all dependencies, explicit success outcomes for conditional gates, RED/CI
evidence for code issues, relevant documentation and transport gates, required hardware
classification, and zero unresolved blocker findings.
STOP or NO_GO applies when detection is ambiguous, provenance or licensing is unclear,
private material is required upstream, resource limits fail, a write path is reachable,
required hardware evidence is absent, or recovery cannot restore the prior service.
`NO_GO` and `STOP` are valid evidence outcomes but never progress; completing their issue
does not unlock a conditional edge.
For FMV3-M6-02 specifically, only GO completes the myVaillant plan objective; NO_GO/STOP
preserves the honest lab record without converting issue completion into success. GO cannot
be derived from replay, cache, fixtures, synthetic input, or simulation.

## Non-goals

- No Modbus writes, controls, write probes, or write-capable generic APIs.
- No repository per vendor and no separate SunSpec repository.
- No EMMA profile, register claim, or support promise.
- No private binding logic in public repositories and no public dependency on private CI.
- No automatic GraphQL, Portal, HA, eeBUS, or Matter promotion from raw profile availability.
- No claim that myVaillant interoperability is already proven.
- No implementation, repository creation, issue creation, commit, push, or plan lock in
  this drafting task.

## Review and lock state

Each review epoch contains exactly five bounded OpenAI-only adversarial rounds and has state
`IN_PROGRESS`, `FAILED`, or `PASSED`. A nonterminal package has exactly one highest/current
`IN_PROGRESS` R1-R5 set. Closed epochs remain immutable epoch-qualified summaries and
evidence; their rounds and findings are never deleted or relabeled. A finding is valid
only when it identifies a concrete blocker in implementability, correctness/data integrity,
protocol interoperability, security/safety, licensing/IP boundary, operability/recovery,
testability, or dependency/DAG feasibility. Reviewers may not demand implementation-level
cryptographic proof systems or a validator that emulates the product. Raw reviewer verdict
is recorded separately as `FINDINGS` or `NO_FINDINGS`; integration is `CLOSED` for findings
and `NOT_REQUIRED` for no findings. R1-R4 may honestly return either verdict and count once
their matching integration state is recorded. A `PASSED` epoch requires five accepted rounds,
accepted R1-R5, R5 `NO_FINDINGS`, integration `NOT_REQUIRED`, `finding_ids: []`, and target
`TERMINAL_NO_FINDINGS`. It is the exactly one highest/current review terminal and permits zero
`IN_PROGRESS` epochs. R5 `FINDINGS` may close an active epoch as `FAILED` only after integration
is `CLOSED`; that epoch is then archived without deletion or relabeling, and the revised
unlocked package opens the next epoch at R1, with no invented finding or R6.
For every epoch and round, `plan.yaml` records reviewer verdict, integration state, and the
exact ordered globally unique `finding_ids`; validation compares that order to the review
table and requires `[]` for `NO_FINDINGS`.
A terminal `PASSED` review does not itself lock the plan. The separate operator action on
2026-07-14 authorizes this package to enter `locked` state without changing the reviewed
technical execution contract.

Epoch 1 R1 recorded reviewer verdict `FINDINGS`, integrated eleven valid findings as
`CLOSED`, and was accepted against snapshot
`55942929023f07b7b85776b519d8e7cab16c92d2465b63c2363bc862a423a87c`.
Epoch 1 R2 recorded reviewer verdict `FINDINGS`, integrated seven valid findings as
`CLOSED`, and was accepted against snapshot
`c6a3043660bd72114e4f451533a08b631ae2ab648ab68a300d4fd14f124410e5`.
Epoch 1 R3 recorded reviewer verdict `FINDINGS` against pre-repair snapshot
`5d2319c0a97cd7959e04d8a691612a856d142a03221407d6729c40d84e36d7ac`; R3-F01 through
R3-F05 are integrated `CLOSED` in this revision.
Epoch 1 R4 recorded reviewer verdict `FINDINGS` against pre-repair snapshot
`b5b4b6ebaf6579f5a507dc0fab26d00df1a17a814c34517597ff1f426f3a91e9`; R4-F01 through
R4-F05 are integrated `CLOSED` in this revision.
Epoch 1 R5 recorded reviewer verdict `FINDINGS` against snapshot
`467616a20c8527e71b3cd57e8f9fa2fa47f30f64ef00a0e71b233bbde6c22355`; R5-F01 added
the missing `security` gate to FMV3-M5-05 without changing its existing machine-to-machine
GraphQL design or acceptance contract. Integration reached `CLOSED` before epoch 1
transitioned to `FAILED`, and its R1-R5 history is archived immutably.

Epoch 2 R1 recorded reviewer verdict `FINDINGS` against snapshot
`b7483351faf61cf27362f920ebc1ac04145e8ec6a701d24e1a4898c43d00be88`; E2-R1-F01 through
E2-R1-F03 remain integrated `CLOSED`. Epoch 2 R2 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`65995df36c0af95196c1259a8a9e9c5396506e3238455818ed98241d6bc7bc2e`; E2-R2-F01 through
E2-R2-F03 remain integrated `CLOSED`. Epoch 2 R3 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`fbdc798570105c8a8daab2d1ae1208455db40411fde0b98f6a1b7dcb0486302e`; E2-R3-F01 through
E2-R3-F06 remain integrated `CLOSED`. Epoch 2 R4 recorded reviewer verdict `FINDINGS`
against pre-repair snapshot
`9cebd062800c3b125963c4f0541163122f3a38a5d80ed5f3a282ebe0a345c115`; E2-R4-F01 through
E2-R4-F03 remain integrated `CLOSED`. Epoch 2 R5 recorded reviewer verdict `FINDINGS`
against snapshot `987d594f721af943fc65f6f47e5f48d8d3b72011b656fd2db79dd13adceb4796`;
E2-R5-F01 through E2-R5-F03 are integrated `CLOSED` in this revision. They add the future
terminal `PASSED` model, separate full-transmit response-wait behavior from the five abnormal
write results, and repair the review claim register. Epoch 2 then transitioned to `FAILED`
and was archived immutably with its R1-R5 history preserved.

Epoch 3 R1 recorded reviewer verdict `FINDINGS` against snapshot
`d0e23922b27030b241688dec85d5e79f28de4d6730e6964511e71b6ff10b1c36`; E3-R1-F01 through
E3-R1-F05 are integrated `CLOSED` for semantic ordering, coalesced wire/view identity,
EMMA discrimination, RTU qualification, and Matter ingress. Epoch 3 R2 recorded reviewer
verdict `FINDINGS` against snapshot
`19f83175eaffc54e6e6ea5bb0f8282d0c6400e9c440ceacc80cbf5b75725f07b`; E3-R2-F01 is
integrated `CLOSED` by making Huawei positive admission public, licensed, conditional, and
fail-closed. Epoch 3 R3 recorded reviewer verdict `FINDINGS` against snapshot
`3dcfab8e8c094d8be6010caa50015100163741e460ce109c5b32ab6154eccf30`; E3-R3-F01 and
E3-R3-F02 are integrated `CLOSED` through public eeBUS/Matter companions, sanitized
post-lab publication or STOP, and consistent active-state validation. Epoch 3 R4 recorded
reviewer verdict `FINDINGS` against snapshot
`ddc3962b53f4ce8d5d29a737c501cd4eab2e30ccd2e3e4bab12a16113c95a58e`; E3-R4-F01 is
integrated `CLOSED` by assigning FC2B/MEI0E identity to the runtime and gating every M7
detector operation on its allowlist. Epoch 3 R5 recorded `NO_FINDINGS` against snapshot
`320f9383d26b640a423ad5902cad90643dc42e18d2c76544f6293d46253866ea`, with no findings and
integration `NOT_REQUIRED`. Epoch 3 is the sole highest/current terminal `PASSED` epoch.
Accepted rounds: `5/5`. Current target: `TERMINAL_NO_FINDINGS`.
Lock authorized: `yes`, for plan publication only.
