# Modbus Runtime, Multi-Vendor Registry, And Generic Private Protocol Bindings - v2.6 Terminal Repair 22 Draft

<!-- DISPLAY_HASHES_BEGIN -->
Canonical-SHA256: `10fba769cda75189fd563b0b8667d0d3f358764d69de808ebc82ad2b9b725c92`
Pre-Execution-Matrix-SHA256: `0e548c3ec3627807a72abd22cfc3961888daed6becb5141c9b197b7b686b043a`
Topology-Edges-SHA256: `0eb3baec238255ab04aad773a28e6c2739cbe23c70d540e4619f244e3b348bd2`
Validator-SHA256: `6ee0d1402003e0af470fbc59b8b1dfffa324086fc170b61f290e29c99387453b`
Validation-Report-SHA256: `4171691425d7d8bd4a96d03467b5520da008392ecfa853096714b11ab0b2ebc9`
Validation-Payload-SHA256: `e95a68254fb8f9cd4a59f74fec8121839dd67e094179ea03ae2ed6b37e9d5bbd`
<!-- DISPLAY_HASHES_END -->





Reviewable M5 dependency order: FMB-05B evidence; FMB-03E0 -> FMB-05R -> FMB-05D ->
FMB-05A (GO only) || FMB-05C -> FMB-05G -> FMB-05H || FMB-05F -> FMB-05E -> FMB-05I -> FMB-05J. FMB-05A and FMB-05C
are the two post-document branches; this deterministic display adds no edge.

Revision: `v2.6-draft-terminal-repair-22`
Date: `2026-07-10`
Status: `Draft v2.6 Terminal Repair 22 - terminal review pending; review_clean=false; lock_ready=false; PLAN_LOCK pending/unauthorized`
Baseline: `multi-runtime-semantic-platform.draft` and Gateway `0.4.0`

## Objective

Deliver a Fronius-first, read-only Modbus-TCP photovoltaic integration while
establishing reusable public Modbus protocol, profile, and canonical semantic
contracts. Exactly one public runtime repository owns every Modbus transport,
and exactly one public registry repository owns every vendor or standard
profile package; neither transport nor vendor expansion creates another repo.

The public ownership layers are:

1. `helianthus-modbus`: the sole home for generic Modbus PDU/value types and all
   Modbus transports/runtime: current TCP, the RTU lane, deterministic replay,
   and future transports. It contains no vendor, SunSpec, or photovoltaic
   semantics.
2. `helianthus-modbusreg`: the sole home for all standard and vendor profile
   packages, including SunSpec, Fronius, Growatt, and Huawei, plus raw/profile
   facts, catalog, shared decoder primitives, fixtures, and selection metadata.
   It does not own the canonical PV schema.
3. `helianthus-ebusgateway`: runtime composition and evidence-bearing PV
   candidate observation. It applies promotion contracts; it does not own the
   canonical schema.
4. `helianthus-ebusreg`: canonical protocol-independent PV semantic schema,
   stable IDs and types, schema versioning, and the candidate-to-promoted
   contract.

Raw MCP evidence precedes semantic promotion. GraphQL, Portal, Home Assistant,
and generic private eeBUS/Matter binding products consume only promoted
canonical facts. `pv.v1` is their first enabled capability slice, not their
repository scope.

## Proven / Hypothesis / Unknown

### Proven

- The platform reserves Modbus-TCP/RTU for SunSpec and vendor profiles.
- Fronius publishes Modbus TCP/RTU material and GEN24 SunSpec surfaces.
- SunSpec Modbus is an open DER information-model family over Modbus.
- Local HA evidence identifies a Fronius SolarNet, GEN24 inverter, and Smart
  Meter target. This proves a lab target exists, not register interpretation.
- `helianthus-ebusreg` is an existing public core repository and is the correct
  ownership boundary for protocol-independent registry and semantic types.

### Hypothesis

- One generic runtime and one multi-vendor catalog can scale without transport,
  profile, or canonical-schema coupling.
- A static catalog gate followed by bounded runtime probes can select profiles
  deterministically without writes.
- Generic private eeBUS and Matter binding products can consume promoted
  canonical facts across domains without gaining upstream ownership; `pv.v1`
  can be their first enabled capability slice.

### Unknown

- Local Fronius unit IDs, active models, meter mapping, battery exposure,
  register mode, and scale-factor representation.
- Whether myVaillant accepts the selected eeBUS PV service subset.
- Which Huawei SmartLogger and S-Dongle facts can complete fact-level clean-room
  clearance for specific family/model/firmware/map applicability keys.
- EMMA identity and register semantics; EMMA remains blocked until its explicit
  evidence gate is complete.
- First supported Growatt/Huawei device and firmware matrices.
- Which later profiles require RTU rather than TCP.

## Target Repository Ownership

### Public repositories

- `helianthus-execution-plans`: control plane, issue topology, review ledger,
  canonical digest, and auditable PLAN_LOCK evidence.
- `helianthus-docs-ebus`: protocol-agnostic platform architecture and
  documentation of promoted semantics. The legacy eBUS-specific repository
  name is acknowledged; it does not transfer schema ownership from
  `helianthus-ebusreg`.
- `helianthus-docs-modbus`: raw Modbus protocol/vendor evidence, provenance,
  fixture source records, and conformance reports only. It does not define
  promoted PV meaning.
- `helianthus-modbus`: the only Modbus transport/runtime repo, owning generic
  PDU/function/exception codecs, raw value types, TCP framing/session, replay,
  the Modbus matrix runner, RTU, and every future Modbus transport.
- `helianthus-modbusreg`: the only standard/vendor profile repo, owning the base
  profile API, shared decoder primitives, catalog, isolated SunSpec, Fronius,
  Growatt, and Huawei packages, raw/profile fixtures, and conformance.
- `helianthus-ebusgateway`: gateway-side latch enforcement, Modbus composition,
  read-only raw MCP, candidate PV observation, promotion-contract application,
  semantic GraphQL authorization/resolution, and Portal.
- `helianthus-ebusreg`: canonical protocol-independent PV schema, stable
  identities/types, versioning, validation, and promotion contract.
- `helianthus-ha-integration`: GraphQL consumer after promotion.
- `helianthus-ha-addon`: wrapper/supervisor latch and atomic config, release
  schemas/verifier, candidate image packaging, exact-image final validation,
  and detached public tuple.

### Private repositories

- `helianthus-eebus-binding-private`: generic downstream eeBUS protocol binding
  product spanning every canonical domain; `pv.v1` is its first enabled slice.
- `helianthus-matter-binding-private`: generic downstream Matter protocol binding
  product spanning every canonical domain; `pv.v1` is its first enabled slice.

No second public Modbus runtime repository and no public per-vendor or
per-standard profile repository is part of this workstream. Future TCP, RTU, or
other Modbus transports stay in `helianthus-modbus`; Fronius, SunSpec, Growatt,
Huawei, and future profile packages stay in `helianthus-modbusreg`.

## Dependency Direction

```text
helianthus-modbus raw/value/runtime contracts
  -> helianthus-modbusreg raw and profile facts
  -> helianthus-ebusgateway evidence-bearing candidate projection
  -> helianthus-ebusreg canonical schema and promotion contract
  -> helianthus-ebusgateway GraphQL/Portal
  -> Home Assistant and generic private eeBUS/Matter bindings
```

Dependency arrows express fact and contract progression. Implementation import
edges must remain acyclic: `modbus` imports no upper layer; `modbusreg` imports
only `modbus`; `ebusreg` imports neither gateway nor protocol/vendor packages;
gateway imports `modbus`, `modbusreg`, and `ebusreg`; consumers import only the
published GraphQL or promoted-semantic interface. Private modules, generated
artifacts, and private facts never flow upstream into public repositories.

## Architectural Invariants

1. `helianthus-modbus` contains no vendor names, SunSpec model meanings,
   profile selection, PV paths, or canonical semantics.
2. Fronius v1 requires generic PDU, Modbus-TCP, deterministic replay, and the
   executable Modbus matrix. RTU is a parallel, independently rollbackable
   `M2R` milestone and does not block M3 or M4.
3. `helianthus-modbusreg` is the sole public Modbus profile/catalog home.
4. `helianthus-ebusreg` exclusively owns canonical PV schema IDs, types,
   versions, compatibility, and promotion contracts.
5. Gateway observes candidates and applies `ebusreg` contracts. It cannot
   establish schema by local structs, GraphQL shape, or dossier prose.
6. Docs-modbus owns raw protocol/vendor evidence only. Docs-ebus documents
   platform architecture and promoted semantics while citing `ebusreg` as
   normative schema authority.
7. Profiles receive bounded raw operations from `modbus`; they never open
   sockets/serial ports or implement retries.
8. Profile selection has two mandatory fail-closed phases defined below.
9. Duplicate IDs, namespace collisions, incompatible ranges, undeclared
   capabilities, ambiguity, no match, or probe-budget breach block activation.
10. Every observation carries profile ID/version, raw evidence, source class,
    source reference, unit/scale policy, timestamp, and explicit unknown state.
11. Candidate facts are hidden from all consumers until an `ebusreg` promotion
    contract and leaf dossier pass.
12. Private bindings depend only on promoted interfaces and never import raw,
    profile, candidate, or gateway-internal packages.
13. Fronius v1 is read-only Modbus-TCP. No write/control API is shipped.
14. Public builds fail on missing, unknown, restricted, or private provenance.
15. HA's Fronius integration is comparison evidence only.
16. The Modbus matrix and gateway eBUS T01..T88 matrix are independent. Neither
    may substitute for the other.
17. A TCP endpoint has one v1 connection pool keyed without unit ID; unit IDs
    share its session and are isolated by correlation, fairness, and budgets.
18. Every operation has one absolute deadline across queue, dial, write, read,
    and backoff. A retry sends a fresh complete ADU with a new transaction ID.
19. An identity domain activates exactly one exclusive primary profile.
    Fronius and generic SunSpec cannot both be primary for one endpoint/unit.
20. A field is committed only from a complete, validated dependency set from
    one poll generation. Partial failure never refreshes retained data.
21. Gateway owns generic non-destructive merge mechanics. `helianthus-ebusreg`
    owns stable canonical freshness TTL, expiry/unavailable policy, and schema
    compatibility; profiles cannot redefine those canonical policies.
22. Published canonical or GraphQL contracts are never destructively rolled
    back. Recovery after publication is additive forward-fix plus deprecation.
23. Persisted state is versioned by schema and producer, rejects or quarantines
    unknown versions, and has migration and restore-snapshot tests.
24. Canonical identity is independent of endpoint, unit ID, register address,
    and transport. Replacement is explicit and never inferred as an endpoint move.
25. Directional canonical power and energy are separate non-negative SI leaves;
    signed raw values never cross promotion without proven polarity and deadband.
26. Canonical unknown/state reasons are typed and never represented by zero.
27. Transport/profile live proof and semantic per-leaf proof are independent gates.
28. Only `ebusreg`-validated extended monotonic energy reaches consumer statistics.
29. GraphQL schema compatibility is frozen before resolver and HA rollout.
30. Generic private eeBUS and Matter work begins with revision-pinned complete
    domain/capability inventories and bounded conformance manifests. Private
    requirements can return `NO_GO`, `unsupported`, or `not-yet-implemented`,
    but cannot mutate or request changes to public semantics.
31. Freshness and ordering use gateway monotonic observation/generation evidence,
    never device source time or cache/replay ingestion time.
32. V1 connects only through a persisted random endpoint UUID. One structured
    parser produces canonical address bytes before policy; callers never supply
    network coordinates and alternate textual encodings are rejected.
33. Fronius v1 is plaintext, unauthenticated, unencrypted Modbus-TCP for a
    trusted isolated LAN only. It accepts no credential or opportunistic
    security field and reports `transport_security=none`.
34. One central gateway governor atomically admits complete resource vectors;
    it never nests blocking token acquisition. The eBUS/core reserve is
    non-borrowable and Modbus may use only the declared remainder.
35. Fresh install, migration, downgrade, or ambiguous/partial configuration
    keeps Modbus disabled. FMB-03P owns wrapper/supervisor sentinel and
    environment precedence plus atomic storage; FMB-04K independently owns the
    gateway second latch before config load and Modbus initialization.
36. Raw Modbus MCP requires authenticated admin by default. Without a verified
    authenticated boundary it may exist only on a restrictive Unix-domain
    socket with no ingress/proxy exposure; unauthenticated TCP or loopback is
    forbidden. Authorization and policy generation are checked per request.
37. Runtime and independent-lab capture use the same FMB-01E AEAD envelope,
    quota, retention, sanitization, erasure, audit, and provenance contract.
38. Modbus degradation is isolated from gateway/eBUS readiness and must satisfy
    a versioned failure-injection SLO before production enablement using the one
    normative recovery formula defined below.
39. Production runs only an immutable detached public release tuple accepted by
    `public-release-control-v1`, binding the exact FMB-06H-validated image,
    embedded compatibility manifest, evidence, SBOM, provenance, release serial,
    predecessor, signing-key epoch/status, revocation generation, validity, and
    minimum compatible persistent-state schema range. A private extension independently binds the
    public base digest, binding contract version, canonical schema range,
    promotion-manifest digest, capability-manifest digest, enabled capabilities,
    opaque private artifact digest, flags, signature, issuance, expiry, and
    revocation; it never adds private identity to public artifacts.
40. FMB-03E is standalone profile/runtime live proof with exact-target reads and
    no writes/off-target access. FMB-04L is the later gateway/add-on system lab
    for kill, reconnect, breaker/governor, eBUS isolation, config, and health.
41. Disabling a source/profile/promotion/release immediately increments a
    disable epoch and makes affected current leaves unavailable with a typed
    reason; retained values remain history only and never refresh timestamps.
42. Endpoint `address-class-policy-v1` is deny-first and default-deny. Only an
    exact administrator target plus explicit port and site/policy authorization
    can be eligible; there is no discovery or implicit subnet allow.
43. Semantic GraphQL authorization is server-side, default-deny, and evaluated
    against an authoritative principal and site/component scopes before any
    lookup or resolution, with normalized denial and no existence leakage.
44. FMB-06H deploys the exact immutable FMB-06D image digest and validates the
    complete applicable Modbus, gateway, SLO, and independent eBUS matrices on
    that digest, config, and embedded-manifest digest.
45. FMB-06G is the sole future-tuple contract-test and final-evidence owner. It
    signs only after FMB-06H and executes the FMB-03T verifier after producing
    the tuple; any rebuild or digest/config/schema mismatch requires new 06H.
46. `helianthus-modbus` is the single runtime boundary for TCP, RTU, and every
    future Modbus transport; no transport-specific runtime repository is allowed.
47. `helianthus-modbusreg` is the single registry boundary for all standard and
    vendor profiles; no SunSpec, Fronius, Growatt, Huawei, or other per-profile
    repository is allowed.
48. Huawei publication is fact-level clean-room work. Restricted source bytes
    never enter public code, docs, fixtures, generated output, SBOM, or release;
    an uncleared fact blocks only its consuming selector, field, or semantic leaf.
49. Every Huawei register, predicate, sentinel, unit assumption, applicability
    claim, and selector budget is a provisional fact ID with opaque source ID,
    evidence class, falsifier, and scope until FMB-08A emits an immutable matching
    `GO(fact-set-digest)`. No provisional number is a pre-clearance requirement.
50. A GO-generated Huawei selector is read-only, positive-fingerprint,
    hard-budgeted, and fail-closed to `Matched`, `Ambiguous`, or `Unknown`.
    SmartLogger and S-Dongle have separate selector/profile and topology
    contracts; timeout, readability, MEI failure, or unit number proves nothing.
51. `helianthus-eebus-binding-private` and
    `helianthus-matter-binding-private` are generic all-domain product repos.
    Their implementation is restricted to manifest-supported capabilities and
    begins with enabled capabilities exactly `[pv.v1]`.
52. Restricted Huawei source remains only in an operator-controlled vault outside
    every public repo. Public repos contain opaque source IDs/digests and signed
    custody/role-separation attestations, never restricted or reconstructable bytes.
53. FMB-08A independently decides `GO(fact-set-digest)`, `NO_GO`, or `DEFER` for
    each family and direct/downstream/RTU scope. NO_GO creates no code/catalog;
    DEFER remains blocked. Revocation removes only generated consumers/leaves.
54. FMB-05H owns the immutable canonical capability catalog and proves exact
    equality with authoritative static declarations and runtime registrations.
    Enabled capabilities are a supported-only subset; schema/status/range change
    creates a successor.
55. Every production M8 profile digest flows through candidate, semantic,
    promotion, API/Portal, HA, image, exact-image validation, and successor public
    tuple artifacts. A machine validator rejects any missing or changed digest.
56. Huawei RTU closes only through FMB-08G-RED -> FMB-08H -> FMB-08G-CLOSE.
    `BLOCKED_RUNTIME_GAP(failing-matrix-digest)` is the sole correction handoff;
    a fix requires CI-observed RED before implementation and full matrix reclosure.
57. Public artifacts, tuples, SBOMs, provenance, and evidence contain no private
    manifest/evidence/artifact digest, status, repo identity, commit, URI, or
    correlatable fingerprint. Extension attachment cannot change any public byte.
58. `93-pre-execution-matrix.md` is intent only and exactly equals executable
    `plan.yaml.milestones`. Installed preflight success contains only status green,
    mode, eight row results, and authorization digest; detailed live evidence stays
    in cruise-state. Intent alone cannot authorize branch, code, or PR work.
59. A Huawei GO is executable data, not prose: it contains a canonical predicate
    DAG and truth table whose leaves reference cleared fact IDs and whose generated
    bytes and outcomes must equal immutable GO goldens.
60. Huawei gateway classification and downstream observation are different typed
    contracts. Routing units/readability never identify a gateway; downstream
    observations cannot create canonical topology before FMB-08J.
61. One monotonic endpoint-selection ledger bounds the complete SmartLogger plus
    S-Dongle attempt across every connection, ADU, retry, exception, MEI, returned
    word, reconnect, and wall deadline using the strictest applicable cap.
62. Huawei applicability is parsed and normalized only by GO-owned exact,
    disjoint firmware/model/map rules. Every field has independently revocable
    child facts for address through applicability; no lexical or nearest fallback.
63. A signed monotonic fact-clearance epoch and expiry fence every Huawei work and
    publication stage. Revocation denies new work, cancels/drains old work, and
    prevents late responses or values from matching, refreshing, or crossing
    canonical counter lineage.
64. Private extensions are anti-replay state machines. Independently rooted
    authority/key epochs, monotonic serial/predecessor/revocation data, bounded-
    age append-only control data, and crash-atomic highest-seen state are verified
    before private credentials or capabilities activate.
65. Public M8 scheduling is independent of M7 and every private system. It starts
    solely from public predecessors and has identical schedule, bytes, evidence,
    and bounded timing when private repos are absent, partitioned indefinitely,
    running, PASS, NO_GO, or PRIVATE_UNAVAILABLE. No public node waits on or has
    an ancestor, control input, timing input, or artifact from a private system.
66. Canonical capability completeness begins with an authoritative static domain/
    schema declaration inventory independent of runtime registration. Declaration,
    registration, and generated-catalog unique-key sets must be exactly equal.
67. Public outputs reveal zero private-extension presence, validity, count,
    registry state, or timing. Public content/cardinality/timing is invariant for
    zero, valid, invalid, expired, revoked, or unavailable private extensions.
68. A private capability is `supported` only when every revision-pinned mandatory
    feature row passes full bounded-conformance replay. Optional gaps are explicit
    unsupported/nonadvertised; `not-yet-implemented` is never supported.
69. Public release trust is independently rooted. An offline authority root,
    separate release-signing key epochs/status/revocation, monotonic serial,
    predecessor/genesis, validity, persistent-schema range, and an activation WAL
    atomically bind the active pointer and authoritative high-water at COMMITTED.
70. Public images are reproducible artifacts. Source commit/tree, lockfiles, base
    image, toolchain/compiler, build flags/environment/time normalization, and all
    dependencies are pinned; two independent clean rebuilds must match image,
    SBOM, and provenance bytes and digests.
71. Public packages use durable A/B slots and `activation-wal-v1` states
    OLD_ACTIVE -> PREPARED -> COMMITTED -> CLEANED. PREPARED high-water is only a
    candidate. Before COMMITTED recovery boots old; after COMMITTED it boots new
    and never rejects the current active tuple. Rollback is another authorized
    committed transition.
72. Fact, poll, topology, candidate, promotion, and counter epochs use rooted,
    generation-stamped A/B or WAL records with checksum, predecessor, and durable
    pointer. Stale disk/snapshot/clock rollback is rejected; state is durable before
    any match, topology edge, candidate, promotion, or counter publication.
73. `WHOLE_PROCESS_HARD_STOP` and `MODBUS_DISABLED` are disjoint. Hard stop is
    supervisor-owned zero exec with gateway and eBUS unavailable. Modbus-disabled
    starts gateway/core before config, performs no Modbus config/socket/work, and
    keeps eBUS available. No evidence may claim both outcomes for one run.
74. TCP route admission and RTU device admission are generation-fenced identities.
    TCP defaults to RFC1918/ULA and revalidates address/port/interface/VRF/network-
    namespace/next-hop/route before every dial; RTU binds stable hardware/OS device
    identity, character-device ownership/mode/exclusive-open, and exact serial config.
75. `resource-manifest-v1` freezes numeric whole-fleet global/site/protocol/bus/
    endpoint/unit/profile limits and non-borrowable eBUS CPU/memory/disk reserve
    before implementation. Profile caps can only narrow their strict intersection.
76. FMB-01E/FMB-04S enumerate every MCP method/resource and every operational-
    data class with exact authorization, pagination/export/rate limits, encryption,
    quota, retention, erasure, backup/cache/log handling, and compromise response.
77. `plan.yaml.milestones` is the sole executable topology source. Each node has
    exact ID/repo/milestone/wave, artifact-only `depends_on`, typed conditional
    `consumes_if`, ordering-only `schedule_after`, terminal outcomes, scope,
    selection, and acceptance artifact. All maps are exact rendered mirrors.
78. Draft curation, installed skill adapters, authoritative architecture-map
    amendment, fresh terminal review, and operator-authorized cruise lock are
    non-executable planning gates. The skill and architecture gates are external,
    currently pending, and must pass before lock.
79. FMB-00D is the only post-lock root. It verifies exact already-installed
    adapter versions/hashes and architecture attestation under the compatible
    installed preflight. It cannot create, install, patch, or adapt skills.
80. Repository creation/settings are distinct from in-repo bootstrap. FMB-00E-*
    emit independent per-repo readiness rows; FMB-00F-* run inside each new repo,
    establish README/AGENTS/license-or-private-policy/CI/templates/CODEOWNERS and
    prove issue -> branch -> draft PR -> CI/review. Each first product issue
    consumes only its own bootstrap READY artifact.
81. Transport baselines are keyed by repo, milestone, matrix family, and exact
    HEAD. Families are eBUS T01..T88 and Modbus PDU/TCP/RTU/REPLAY. A new empty
    repo uses signed GENESIS_ABSENT; its first runner establishes v1 and never
    claims comparison to nonexistent rows.
82. Doc-gate routing is semantic: platform/semantic contracts go to docs-ebus;
    raw Modbus/profile/RE facts go to docs-modbus. Every companion is self or an
    ancestor/merge blocker. Raw dossier FMB-05B and platform contract FMB-05D
    precede candidate/schema implementation; no synthetic downstream cycle exists.
83. `fresh-review-v1` is a signed digest-addressed attestation, not a URL. It
    binds exact HEAD/canonical/topology/validator/report digests, zero findings,
    issue/expiry/non-revocation state, two distinct fresh OpenAI context IDs,
    trusted reviewer signers, and independent planner/adversary/reviewer route
    records. One reviewer, reused context, stale time, fallback, or a non-OpenAI
    route fails. No trusted review API is claimed; verification uses the pinned
    operator-controlled local trusted-key contract.
84. FMB-03E0 exclusively decides Fronius-specific live scope. GO enables those
    live/product nodes; NO_GO marks only those nodes N/A while generic public
    semantics, APIs, base release, eeBUS base, and alternative profiles continue.
    DEFER blocks Fronius-specific work without fabricated evidence.
85. Branches run in parallel:

- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.

    FMB-08A-SCOPE references only those exact inventory IDs and never governs base
    Fronius. Only matching GO enters the immutable inventory scope-selected set;
    non-GO creates no profile/catalog bytes. Schedule ordering still advances, so
    one DEFER cannot block a later independent GO profile.
86. Raw MCP precedes consumers. FMB-04D provides an admin-scoped read-only Portal
    RE workbench after raw/profile MCP. FMB-05I records operator-signed,
    digest-bound MCP_STABLE over exact schemas and evidence; FMB-06A depends
    directly on it, and later MCP changes require an immutable successor.
87. `validate_plan.py` and deterministic `94-validation-report.json` are mandatory.
    The normalized payload excludes only delimited validation-attestation blocks
    and the report itself, preventing self-hash cycles. PG-DRAFT-CURATION is
    complete only when the checked-in report verifies byte-for-byte.

## Planning Gates And Executable Topology

FMB-00A/B/C remain absent from executable work. The non-executable planning
sequence is PG-DRAFT-CURATION, PG-ARCHITECTURE-MAP-AMENDMENT,
PG-MODEL-ROUTING-POLICY-AMENDMENT, PG-SKILL-ADAPTER-REGISTRY,
PG-FRESH-TERMINAL-REVIEW, then the final installed lock gate.

<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_BEGIN -->
PLAN_LOCK through PG-CRUISE-LOCK requires exactly these three chained external amendment gates:

- PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY.
<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_END -->

The three operator-owned prerequisites are pending, so `review_clean=false`,
`lock_ready=false`, and PLAN_LOCK remains pending/unauthorized.

PG-SKILL-ADAPTER-REGISTRY is owned by the actual operator skill layer. During
pre-lock preparation it must pin source URI/version/source and installed SHA-256 for
cruise-plan, cruise-state-sync, cruise-preflight, cruise-topology, doc-gate,
transport-gate, review-loop, merge-gate, cruise-dev-supervise, and
cruise-tdd-gate adapters; record runtime version; pass clean-start and resume
fixtures; and emit the installed-runtime attestation. FMB-00D later verifies those exact installed
bytes. Skill installation or adaptation is forbidden in post-lock execution.

PG-ARCHITECTURE-MAP-AMENDMENT is owned by the root AGENTS operator. It records
every contradictory normalized assertion: the separate adapter-repository rule,
planned `helianthus-sunspec` row, naming/ownership contract, RS-485/Modbus
assignment, missing checkout-map entries, and per-protocol adapter-delivery
wording. It replaces them with
`helianthus-modbus` as the sole Modbus transport/runtime repo beneath
`helianthus-modbusreg` as the sole standard/vendor profile registry. It pins the
root AGENTS version/hash, normalized expected-assertion digest, contradiction-
absence digest, checkout-map additions, import boundary, signer, revocation
generation, and operator authorization. This draft does not edit root AGENTS;
lock refuses until the installed authoritative file matches all assertions.

<!-- MANUAL_PREFLIGHT_EXACT_SCHEMA_BEGIN -->

The installed preflight success envelope is generated from the machine schema below; every listed field set is exact, so omission and extension are both invalid.

Single top-level exact fields: `["preflight","next_skill"]`

Single preflight exact fields: `["status","mode","rows","authorization"]`

Single row-map exact names: `["routing","workflow","doc_gate","review","deps","transport_gate","smoke","tdd"]`

Single row-result exact fields: `["status","repo","milestone","issue","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","provider_query_id","semantic_result_sha256","evidence_artifact_type","evidence_artifact_path","evidence_artifact_sha256"]`

Single authorization exact fields: `["schema","signer_id","signed_at","envelope_sha256","draft_payload_sha256","locked_payload_sha256","lock_transform_manifest_sha256","final_locked_commit_oid","route_records","route_records_sha256","pre_execution_intents_sha256","risk_classes","risk_classes_sha256","revocation_generation","signature"]`

Multi top-level exact fields: `["preflight","next_skill"]`

Multi preflight exact fields: `["status","mode","batch_id","per_repo","batch","max_parallel","cross_repo_deps","authorization"]`

Multi per_repo container type: `"list"`

Multi per_repo item exact fields: `["repo","milestone","issue","issue_number","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","pre_execution_intent_sha256","risk_classes","workflow_semantic_result_sha256","semantic_results_sha256","evidence_set_sha256","rows_sha256","rows"]`

Multi per_repo row-map exact names: `["routing","workflow","doc_gate","review","deps","transport_gate","smoke","tdd"]`

Multi row-result exact fields: `["status","repo","milestone","issue","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","provider_query_id","semantic_result_sha256","evidence_artifact_type","evidence_artifact_path","evidence_artifact_sha256"]`

Multi batch container type: `"list"`

Multi batch item exact fields: `["repo","milestone","issue","issue_number","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","complexity","risk_classes","pre_execution_intent_sha256","acceptance_criteria","workflow_semantic_result_sha256","semantic_results_sha256","evidence_set_sha256","rows_sha256"]`

Multi authorization exact fields: `["schema","signer_id","signed_at","envelope_sha256","draft_payload_sha256","locked_payload_sha256","lock_transform_manifest_sha256","final_locked_commit_oid","route_records","route_records_sha256","pre_execution_intents_sha256","risk_classes","risk_classes_sha256","revocation_generation","signature"]`

The multi envelope therefore carries its own batch_id and binds every per_repo and batch identity, issue/branch target, target object and exact repository HEAD, dependency closure, workflow and row semantic digests, evidence-set digest, and rows digest before signed authorization may derive cruise-dev-supervise.

<!-- MANUAL_PREFLIGHT_EXACT_SCHEMA_END -->
Row 7 is HA real-hardware smoke intent per issue; operator override is recorded
only in live preflight and bound to authorization.

`plan.yaml.milestones` separates ordering from artifacts. `schedule_after`
advances after the source's declared terminal outcomes according to its edge
policy. `depends_on` consumes only PASS artifacts. `consumes_if` uses the
declared predicate AST and consumes only when true. All node sets, inventory
IDs, artifacts, sources, operators, and actions are concrete and validator-
resolvable. `90`, `91`, and `93` are exact ordered mirrors.

Repository lanes are first-class topology input.

<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_BEGIN -->
Branches run in parallel:

- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.
<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_END -->

Intent transport families use only the closed enum `NONE`,
`MODBUS_PDU`, `MODBUS_TCP`, `MODBUS_RTU`, `MODBUS_REPLAY`, and
`EBUS_T01_T88`, plus a separately validated conditional expression. Every
expanded concrete family requires same-family baseline and verify evidence.

Expansion maintains three immutable sets: scope-selected inventory,
fact-cleared, and currently executable. Huawei DEFER can narrow only the latter
two; M2R availability can narrow only executability. Static canonical schema
declarations, runtime registrations, and generated catalog/private-manifest
inputs are separately owned digest-bearing artifacts and must match by normalized
domain/capability/major, owner, range, schema version, and semantic version.

After constructing the single unreferenced final locked commit, pinned cruise-plan and
cruise-state-sync jointly own `external-lock-metadata-v5` in cruise-state and
the meta-issue. It carries schema/version/predecessor, content commit and exact
canonical/matrix/topology/validator/report/payload hashes, signed installed
skill and architecture attestations, signed `fresh-review-v1`, signed explicit
operator PLAN_LOCK authorization, pre-CAS ready gate/status values,
and the bound OpenAI-only route-record digest. Pre-CAS validation accepts only
`--external-lock-metadata` and `--trusted-attestation-keys`, a clean exact HEAD,
active/nonrevoked trusted signers, complete operator attestations, zero-finding review,
explicit authorization, `review_clean=true`, `lock_ready=true`, terminal
NO_FINDINGS/complete, and `plan_lock=ready_for_cas_not_applied`, while ref and
HEAD remain on the draft parent. Post-CAS adds the signed receipt and requires
the final ref/HEAD. Every pending/stale/missing/altered case fails without
changing content. Ordinary draft validation rejects lock options and remains
valid with pending/false state; explicit `--lock-phase pre-cas` is separate.

## Provisioning And Bootstrap

FMB-00E-PUBLIC/EEBUS/MATTER in `helianthus-org-github` own repository creation
and organization settings only. They emit independent per-repo READY/NO_GO/
DEFER rows. FMB-00F-DOCS, FMB-00F-MODBUS, FMB-00F-MODBUSREG, FMB-00F-EEBUS,
and FMB-00F-MATTER then execute inside their own repo, establish README/AGENTS,
public license or private policy, CI/local CI, templates and CODEOWNERS, and
prove issue -> issue branch -> draft PR -> CI/review. A first product issue
consumes only its own bootstrap READY. Mixed public/private outcomes are
independent and private state never changes public scheduling or bytes.

## Typed Outcome And Schedule Semantics

The AST permits only `all`, `any`, `outcome_is`, `artifact_field_is`, and
`node_set_nonempty` predicates plus declared state/artifact actions. Custody
PASS enables facts; custody NO_GO or DEFER blocks fact/profile consumers and is
never coerced to N/A. FMB-08EEBUS-A consumes the signed FMB-07A manifest with full producer identity. FMB-07B supplies schedule ordering only and no artifact to FMB-08EEBUS-A. FMB-08EEBUS owns the exclusive validated producer-envelope choice: the FMB-07B extension on PASS or a separately signed fresh-genesis envelope otherwise. M8 profile DEFER schedules the next independent profile but emits
no bytes. Closure conditionally consumes only selected PASS artifacts and
records all non-GO states. Machine simulations cover every truth table, mixed
readiness, early DEFER followed by later GO, RTU absent/present, Fronius outcomes,
custody NO_GO, runtime gap, private predecessor absence, and empty selection.

## Endpoint, Network, And Transport-Security Policy

The v1 endpoint grammar accepts only a persisted random endpoint UUID. Its
operator-admin record contains a site UUID, exactly one literal IPv4 or IPv6
TCP address, an explicit port, and config/policy generations. One structured
parser equivalent to Go `net/netip` emits canonical address bytes before any
policy decision and rejects legacy integer/octal/hex forms, leading-zero or
alternate encodings, hostnames/DNS, URLs, paths, userinfo, redirects, discovery,
and caller-supplied coordinates.

`address-class-policy-v1` uses this ordered decision table. `DENY` is evaluated
before exact eligibility and the final row makes every unlisted class deny.

| Order | Canonical address class/input | policy-v1 decision |
| --- | --- | --- |
| 1 | Invalid or unspecified, including `0.0.0.0` and `::` | `DENY` |
| 2 | Any IPv6 zone identifier | `DENY` |
| 3 | IPv4-mapped IPv6 `::ffff:0:0/96` | `DENY` |
| 4 | Loopback `127.0.0.0/8` and `::1` | `DENY` |
| 5 | Link-local `169.254.0.0/16` and `fe80::/10` | `DENY` |
| 6 | Multicast `224.0.0.0/4` and `ff00::/8` | `DENY` |
| 7 | IPv4 limited broadcast `255.255.255.255` | `DENY` |
| 8 | Any other non-unicast or reserved form rejected by parser/policy | `DENY` |
| 9 | Every configured HA-management or metadata deny CIDR | `DENY`; absolute precedence, no v1 override |
| 10 | RFC1918 `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` | `ELIGIBLE_EXACT` only |
| 11 | IPv6 ULA `fc00::/7` | `ELIGIBLE_EXACT` only |
| 12 | Other canonical global/shared unicast not matched by a deny row | `CONDITIONAL_EXACT`: explicit operator exception plus approved source interface/VRF/network namespace and next-hop/route proof |
| 13 | Every unlisted class | `DENY` |

`ELIGIBLE_EXACT` still requires the exact configured administrator target,
explicit port, and site/policy authorization. There is no broad discovery or
implicit subnet allow. An optional CIDR may narrow an exact target but never
broaden it. Port 502 is a configuration default, not an implicit authorization.
`CONDITIONAL_EXACT` adds a separately approved operator record that pins source
interface, VRF or network namespace, expected next hop, and route proof; absence
or mismatch is DENY. RFC1918/ULA are the only default eligible target classes.
The endpoint/security matrix has versioned fixtures for every IPv4/IPv6 row,
all configured HA-management/metadata CIDRs, zone and encoding bypasses, and
exact-target/port/site authorization.

Before every dial and reconnect, admission re-resolves the actual source
interface, VRF/network namespace, next hop, route, canonical destination address,
port, and policy generation against the same record. Route, interface, namespace,
VPN, partition, address, site, or policy change increments/fences the generation,
rejects new work, and cancels or bounded-drains denied sessions. No DNS, redirect,
proxy, or inherited route fallback exists; endpoint identity remains the UUID.

Fronius v1 deliberately supports plaintext Modbus-TCP only on a trusted,
isolated LAN. It is unauthenticated and unencrypted, accepts no credentials,
and exposes `transport_security=none` in health/diagnostics without secrets.
Opportunistic TLS, insecure-skip-verify, Modbus Security, client certificates,
and proxy credentials are unsupported; any such field fails config validation.
Future TLS/security support requires a separate ADR, capability and matrix, and
adds trust-policy identity to the pool key. Deployment documentation requires
network segmentation and host/network firewall egress restriction and states
that endpoint spoofing, on-path observation/modification, and compromised LAN
peers are outside v1 protocol protection.

## Resource Governor And Circuit Breaker

Gateway issue FMB-03R precedes gateway integration but not standalone FMB-03E.
It owns immutable `resource-manifest-v1`; every hard numeric limit is frozen and
reviewed before implementation. The manifest bounds configured and active
endpoints, total and concurrent opens, ADU/word/byte rate and burst, queue/state/
metrics memory, cumulative deadline occupancy, retries, serial handles, captures,
and disk at global, site, protocol, bus, endpoint, unit, and profile levels. Each
operation declares the complete vector. Effective admission is the strict
componentwise intersection of whole-fleet and applicable profile caps. Admission
atomically grants the vector or enters one bounded queue/reject path; nested
blocking acquisition is forbidden. The eBUS/core CPU, memory, and disk minimum
is non-borrowable and Modbus may consume only the declared remainder.

Queued work owns only a queue slot. Dispatch atomically exchanges that slot for
worker/in-flight resources. A retry preserves one operation, absolute deadline,
and retry budget, releases worker/in-flight between attempts, and reacquires
dial/in-flight. Reconnect and half-open work use a dedicated capped class and
cannot preempt healthy polls. Capture reserves its full byte quota before it
starts. Cancellation/deadline/shutdown releases exactly once through an
idempotent release path. Hierarchical fairness across protocol, site, endpoint,
unit, and profile is versioned. Each RTU bus is serialized independently; no
second handle bypasses the bus queue. Per-identity scheduler/metrics/breaker state
is bounded, and persistent breaker records count against explicit caps.

Each endpoint breaker is deterministic `CLOSED -> OPEN -> HALF_OPEN`. The
versioned bounded policy declares eligible failures, threshold/window, open
duration, and exactly one bounded half-open trial. Trial success closes;
failure reopens. OPEN admits no probes. Manual reset is admin-only and audited.
Property and invariant tests include 10,000 configured endpoints, reconnect
storm, maximum reads/rates/bursts, raw-MCP abuse, mixed TCP/RTU, RTU bus
serialization, cancellation/drain, persistent-breaker cap, metrics/state memory,
and disk-full capture. At every step the sum of grants is at or below every cap,
the eBUS reserve remains intact, no deadlock occurs, and each resource is released
exactly once. FMB-04L, FMB-04O, FMB-06H, and FMB-08O directly consume and reprove
the exact manifest digest.

## Configuration, Authorization, And Operational Data

FMB-03P owns the add-on wrapper/supervisor modes and must never conflate them.
`WHOLE_PROCESS_HARD_STOP` is a separately authorized supervisor state checked
before parse or exec: the wrapper performs zero gateway exec, so gateway and eBUS
are explicitly unavailable. `MODBUS_DISABLED` is the normal safe mode: the
wrapper executes the gateway, gateway/core starts before Modbus config, no Modbus
config is parsed, no Modbus socket/serial handle/work is created, and eBUS remains
available. Evidence names exactly one mode and expected readiness; no run may
claim both zero exec and eBUS availability.

FMB-04K consumes the FMB-03P protocol and FMB-03T release/config schemas. It
owns `MODBUS_DISABLED` inside the gateway before Modbus config loading and before
any Modbus subsystem/socket/serial-factory initialization. A factory spy proves
zero Modbus sockets and serial handles while eBUS/core starts. The guarded factory
also rejects creation without current config, policy, route/device, and resource-
manifest generation tokens, so FMB-04A has no unguarded transport path.

Config and migration use generation-stamped A/B slots with schema, predecessor
digest, checksum, migration state, and a separately durable commit/active pointer.
The writer fills the inactive slot, fsyncs file and directory, validates bytes and
old/new binary compatibility, records resumable migration progress, then flips and
fsyncs the pointer. Downgrade is allowed only when the target binary accepts the
active schema and predecessor chain; otherwise `MODBUS_DISABLED` starts. Tests
inject corrupt directory/slot/pointer, partial migration, incompatible downgrade,
ENOSPC, SIGKILL, and power loss at every write/fsync/slot/commit/pointer/migration
boundary. The last complete compatible slot remains active; ambiguous state never
selects a partial slot. FMB-03P proves hard-stop zero exec separately; FMB-04K,
FMB-04L, FMB-06H, and FMB-08O prove Modbus-disabled eBUS/core readiness.

Every MCP method/resource is registered in `mcp-custody-v1`: endpoint inventory,
runtime/profile state, raw reads, capture create/read/delete, typed snapshots,
and exports. Each row declares principal, site, endpoint, component and policy-
generation scopes; pagination, word, row, export-byte, rate, concurrency and
retention caps; and a normalized no-existence-leak denial shared by lookup and
enumeration. Raw probe/read/capture MCP requires an authenticated admin principal from an
explicit auth/supervisor adapter and defaults deny. Without a verified
authenticated boundary, raw tools may exist only on a Unix-domain socket with
restrictive filesystem permissions and verified absence of ingress or
reverse-proxy exposure; startup refuses the raw surface if that proof is
missing. There is no unauthenticated TCP, loopback, or local-network exception.
Scope `admin.raw.modbus` carries site, endpoint, and policy-generation
constraints; `semantic.read` is separate. Every request re-evaluates auth,
scope, generations, rate, and concurrency.

Audit records UTC plus monotonic sequence, principal pseudonym and key ID,
action, site/endpoint pseudonym, request ID, config/policy generation, scope and
rate decisions, outcome/error class, and evidence hash, without raw register,
secret, or address. Pseudonyms are HMACs under a secret-reference key; rotation
records key IDs, bounded overlap, and bounded linkability. Records form a
tamper-evident hash chain with periodically signed or attested checkpoints.
Negative ingress/proxy/socket-permission and chain/rotation verification tests
are mandatory. Unauthorized endpoint inventory, runtime/profile state, snapshot,
capture, and export tests; 10,000-endpoint pagination; cursor/filter/export/rate
cap bypass; and cross-site/endpoint/component denial all return the normalized
shape without identifiers, existence, cardinality, or timing distinctions.

FMB-01E governs runtime and independent-lab capture through one versioned AEAD
envelope: algorithm, key ID, nonce, KEK secret reference, and per-capture DEK.
Files use restrictive permissions. Rotation is explicit; cryptographic erasure
deletes the DEK, unlinks ciphertext, fsyncs the directory, and records verified
audit evidence. Quota is reserved before start. Disk-full, encryption, or key
failure fails capture closed without blocking polling, and a live gate cannot
PASS if its required capture failed.

`operational-data-lifecycle-v1` has one row for captures, audit, metrics, crash
records, support bundles, and generated evidence. Each row fixes classification,
encryption/key reference, hard memory/disk quota, retention/deletion or crypto-
erasure, backup/cache/log treatment, and compromise response. Public custody and
attestations use opaque role IDs only. Pseudonym and canary keys are rotatable;
key compromise increments a generation, bounds old-key linkability, rekeys or
deletes affected stores, and invalidates derived support/evidence outputs.

Raw retention defaults to 24 hours with a hard maximum. Longer quarantine needs
an explicit legal/security owner and a separate bounded policy. Before erasure,
the owner writes a durable sanitized evidence manifest containing only the raw
ciphertext hash, allowed sanitized-fixture hash, exact versions/config/policy/
target reference, provenance, redaction result, deviations and PASS/FAIL,
reviewer/attestation, and deletion verification. It must not enable raw
reconstruction. Retention/erasure, backup/cache/log exclusion, support bundle,
crash record, identifier-leak, pseudonym-key-compromise, and canary-rotation tests
run before FMB-04B, FMB-06H, and FMB-08O. Logs, crashes, support bundles, fixtures,
generated evidence, and release outputs remain sanitizer/provenance scanned.

## Rollback-Safe Persistent Epochs

All safety-critical persisted records use a generation-stamped A/B slot or WAL
record with schema, checksum, exact predecessor digest or genesis, committed
generation, and a separately fsynced durable pointer. Startup validates both
slots/WAL chain and pointer, selects only the highest complete monotonic record,
and rejects stale snapshot, disk rollback, predecessor fork, corrupt state, or
wall-clock rollback. Every transition is persist-before-observe: no output may be
published before the corresponding durable record and pointer commit.

FMB-08A owns the independently rooted fact-signing-key epoch and fact-revocation
high-water schema. A revoked or lower GO epoch remains revoked after restart even
if cache/disk/wall clock is rolled back. FMB-08I owns a boot-unique namespace for
poll/session/topology generations plus durable gateway/topology identity and
present/stale/removed/reused transitions. Reconnect, gateway identity/firmware
change, remove/reuse, or topology disagreement must durably advance identity
before raw/candidate output; late packets from prior boot/generation are rejected.

FMB-05G owns journaled counter state and persists identity lineage, source epoch,
width/modulus/scale, offset and last accepted raw/extended value before publishing
the next counter. FMB-08I candidate epoch and FMB-08K promotion/disable epoch are
likewise durable before candidate or promoted publication. FMB-08J consumes the
durable topology/counter/fact coordinates; FMB-08O and FMB-08Q directly validate
the same high-water/checkpoint digests in exact-image and release evidence.

Fault tests inject SIGKILL, ENOSPC, and power loss before and after every record
write, file fsync, directory fsync, pointer flip, migration, and publication.
Fixtures cover revoked-GO restart, stale cache/snapshot/disk/clock, late packets,
unit removal/reuse, topology replacement, candidate/promotion epoch rollback,
and counter crash immediately before/after durable commit. Failure quarantines
only affected outputs; it never republishes stale state or crosses counter lineage.

## Normative Modbus-TCP V1 Session Contract

`helianthus-modbus` owns the scheduler and session primitives. Gateway supplies
endpoint configuration and poll intents and must not create a second pool,
retry loop, or transaction allocator.

An endpoint/pool key is transport kind plus normalized address and port plus a
security/configuration identity. RTU additionally includes serial-device and
serial-configuration identity. Unit ID is explicitly excluded: unit IDs route
over the endpoint session. Normalization and security/config equality are
versioned and fixture-tested so aliases cannot accidentally create two pools.

Each TCP pool/connection has a monotonically increasing `connection_generation`.
Reconnect increments it and atomically invalidates all pending requests from
the prior generation. A connection allocates 16-bit transaction IDs without
reusing any issued ID. Every ID is retired immediately on issuance and remains
retired after success, timeout, cancellation, exception, or parser rejection
for the full connection generation.
The pending key is exactly `(connection_generation, transaction_id,
expected_unit_id)`.

Before wrap, exhaustion, or any attempted ID reuse, the runtime closes and
fences the connection and advances generation; it never reuses an issued ID on
the old stream. Generation-counter overflow fails closed and restarts a durable
connection-identity epoch without alias. Successful-completion wrap, delayed
duplicate, timeout, cancellation, exhaustion, reconnect, generation rollover/
overflow, and late old-generation fixtures prove that stale bytes cannot match.

A response satisfies a request only after all of these checks pass:

- its connection generation equals the pending generation;
- MBAP protocol ID is zero;
- MBAP length is exact, internally consistent, and within configured bounds;
- unit ID equals the expected unit;
- PDU shape and response function/exception match the request contract.

Unknown, duplicate, late, retired-ID, and old-generation frames never satisfy
a request. They increment typed metrics and enter recorder evidence. Invalid
protocol/length/PDU framing that loses stream synchronization closes and resets
the connection; a well-framed but unmatched response follows the explicit
unknown/late policy and cannot be reassigned. Reconnect fences old bytes even
when a transaction ID is later reused.

V1 uses one TCP connection per endpoint. `max_in_flight` is configurable and
hard bounded, with production default `1`; the queue is also hard bounded.
Weighted deficit round-robin schedules by unit/profile, with configured weight,
per-unit outstanding cap, and per-cycle poll budget. A ready unit with budget
must progress within a bounded number of dispatches, proving no starvation.
Queue overflow returns a typed backpressure error and never opens another
connection.

Shutdown rejects new work, cancels queued requests, waits only a configured
in-flight drain bound, then cancels pending state and closes the connection.
Poll coalescing is disabled by default. Any later enablement requires identical
endpoint, unit, function, register range, and connection generation plus
compatible absolute deadlines, and requires a separately versioned matrix.

## Modbus-RTU Device Security Contract

FMB-02R-A admits a serial endpoint by stable OS/hardware identity, not pathname.
The configured record pins platform device ID, USB/vendor/product/serial or
equivalent immutable hardware identity, expected character-device major/minor,
owner, group, mode, and exact baud/parity/data/stop settings. Admission resolves
the path without following an unapproved symlink, rejects non-character devices,
requires expected permissions and exclusive open, then rechecks identity and
config after open before the first byte.

Hotplug, symlink/path swap, USB replacement, ownership/mode change, another open,
or serial-config change increments the device generation, fences queued/in-flight
work, closes the handle, and requires explicit reauthorization. An old handle or
late byte cannot satisfy the replacement generation. RTU bus serialization and
serial-handle budgets come from `resource-manifest-v1`. Tests cover symlink swap,
non-character file, USB remove/reinsert with same path and different identity,
permissions, exclusive-open contention, every serial parameter mismatch, late
bytes, and mixed TCP/RTU operation under the fleet governor.

## Retry And Cancellation FSM

M2 exposes reads only: the runtime allowlist is FC01-FC04, while a profile
descriptor may narrow it. Fronius v1 permits only FC03 and FC04. One absolute
operation deadline covers queue wait, dial, write, read, and backoff. Attempts
are configurable and bounded; the conservative production default is two total
attempts.

| State | Event | Action / next state |
| --- | --- | --- |
| QUEUED | admitted | Wait under absolute deadline; scheduler dispatches to DIAL_OR_READY. |
| QUEUED | cancel/deadline/shutdown | Remove from queue; return typed cancellation/deadline/shutdown result. |
| DIAL_OR_READY | connection ready | Allocate fresh transaction ID and generation key; enter WRITE. |
| DIAL_OR_READY | transient dial failure | Retry through BACKOFF if attempt/deadline permit; otherwise terminal. |
| WRITE | full ADU written | Enter READ with pending key installed. |
| WRITE | zero bytes, definitely not written | BACKOFF may retain the stream only when the transport proves no byte entered it, parser/pending state is empty, cancellation is clear, and retry/deadline budgets permit. The issued ID remains retired and retry uses a new transaction ID and complete ADU. Otherwise close/fence. |
| WRITE | short/partial write, timeout after write, or uncertain write | Connection-fatal: retire the issued transaction ID for the generation, close immediately, discard parser/pending bytes, advance connection generation, and retry only on a fresh connection with a new complete ADU. |
| READ | valid fully correlated response | Remove pending key; return success or typed protocol exception. |
| READ | malformed/wrong-unit/wrong-function | Never retry; record evidence, apply framing reset policy, return typed terminal error. |
| READ | transient transport failure/timeout | Remove pending key, keep the issued ID retired for the generation, and retry the whole ADU if attempt/deadline permit. |
| BACKOFF | timer | Re-enter DIAL_OR_READY with a new complete ADU and new transaction ID. |
| ANY | cancel/deadline/shutdown | Interrupt queue/dial/read/backoff, remove pending state, keep every issued ID retired, reject late responses, and return a typed terminal result. |

Retry is permitted only for classified transient transport failures before a
valid full response and for an explicitly configured retryable exception such
as device-busy. It is forbidden for malformed frames, wrong unit/function,
illegal function/address/value, profile provenance, or selection errors. A
retry never resumes a partial ADU, never reuses its transaction ID, and never
reuses a stream after a possibly partial write. Fault injection covers every
byte offset, the zero-byte definitely-not-written case, timeout-after-write,
generation advance, clean parser/pending state, and late old-generation response.

## Profile Package DAG

`helianthus-modbusreg` uses an explicit acyclic package layout:

```text
api/                         -> helianthus-modbus raw/value types only
primitives/sunspec/          -> helianthus-modbus raw/value types only
profiles/sunspec/            -> api + primitives/sunspec
profiles/fronius/            -> api + primitives/sunspec
profiles/growatt/            -> api and declared shared primitives
profiles/huawei/             -> api and declared shared primitives
catalog/                     -> api + profile registration packages
```

- Base profile API and shared primitives depend only on `helianthus-modbus`
  value/raw types.
- Profiles may depend on shared primitives; shared primitives never import a
  profile or catalog.
- Profiles never import one another.
- Catalog imports/registers profiles; profiles do not import catalog.
- The top-level SunSpec profile owns SunSpec detection and descriptor policy.
- Fronius composes SunSpec primitives directly and never imports
  `profiles/sunspec`.
- Import-graph CI rejects every forbidden edge.

FMB-03C emits only `sunspec-primitives-v1`: unregistered model/value/chain
primitives with no descriptor, catalog entry, detection, or profile identity.
FMB-03D is the first profile registration and registers only Fronius. The first
generic SunSpec profile/detection/catalog registration is FMB-08B after its M8
scope GO. Fixtures reject any FMB-03C generic SunSpec registration, pre-Fronius
catalog entry, or FMB-03D dependency on a registered generic SunSpec profile.

## Two-Phase Profile Selection Lifecycle

### Phase 1 - Static catalog validation before transport creation

Validate globally stable profile IDs and versions, fixture namespaces,
descriptor/catalog schema, runtime API ranges, required capabilities, declared
read-only probe operations and budgets, priority/tie policy, and exact manual
override syntax. Failure prevents socket or serial creation.

### Phase 2 - Bounded runtime probes after connection

After connection but before decoder activation, candidate creation, MCP typed
publication, or semantic publication, execute only declared read-only probes.
Enforce per-profile and aggregate read/word/time budgets. Record requests,
responses, exceptions, timing, candidate scores, rejection reasons, and final
decision in replayable evidence.

Ambiguity, no match, budget breach, undeclared operation, or any attempted
write fails closed. A manual override must identify an exact profile ID and
version; it bypasses ranking only, never Phase 1 compatibility/capability
checks or Phase 2 read-only identity probes and budgets.

## Profile Coexistence And Identity Domains

Every descriptor declares `identity_domain`, `activation_group`,
`composition_mode` (`exclusive_primary` or `auxiliary`), owned probe/register
ranges, specificity, conflict policy, supported functions, and budgets. The
default identity domain is normalized endpoint plus unit ID. A descriptor may
declare a safely disjoint sub-device domain only with deterministic evidence
and non-overlapping probe/register ownership.

Exactly one `exclusive_primary` may activate in an identity domain and
activation group. Generic SunSpec and Fronius are both in
`pv-inverter-primary`. Fronius wins only on affirmative Fronius vendor identity
evidence; generic SunSpec does not win merely because Fronius evidence is
missing or contradictory. Dual affirmative matches, unresolved conflicts, and
ambiguous ownership fail closed with both evidence sets recorded.

Fronius internally composes SunSpec primitives; `profiles/sunspec` is not also
activated for the same identity domain. Separate unit IDs are separate default
domains and may select independently. An exact manual override chooses the
primary candidate but never enables a conflicting profile, bypasses identity
proof, or changes register ownership.

## Versioned Fixture Contract

Every fixture has a manifest schema version and namespace
`<profile-id>/<profile-schema-version>/<fixture-id>`. The manifest records:

- immutable input bytes/events and per-object checksums;
- expected typed values, raw evidence, explicit errors, and unknown states;
- deterministic clock epoch, event ordering, timeout/retry schedule, and
  replay-completion condition;
- device, model, firmware, mode, and applicability bounds;
- source classification, SPDX identifier, redistribution permission, and
  provenance reference;
- capture redaction/sanitizer version and reviewer attestation.

Canonical serialization is UTF-8 JSON using sorted keys, normalized numeric
forms, no insignificant whitespace, LF endings, and SHA-256 over serialized
bytes. Golden diffs are byte-stable. Positive suites include unknown/sentinel,
truncation, protocol exception, timeout, partial response, and replay
completion; missing required metadata is a conformance failure.

## Executable Modbus Transport Matrix

`helianthus-modbus` owns versioned manifest
`conformance/modbus-matrix-v1.yaml`, its runner, and baseline reports under
`artifacts/modbus-matrix/v1/`. Stable test-ID categories are:

- `PDU-*`: function encoding/decoding, bounds, exceptions, malformed/truncated;
- `TCP-*`: MBAP length/protocol ID, transaction and unit correlation, partial
  I/O, stale response, reconnect, timeout, cancellation, and bounded retry;
- `RTU-*`: address, CRC, timing, truncation, noise/resync, cancellation, and
  serial-loop behavior, owned and activated by M2R;
- `REPLAY-*`: canonical event serialization, deterministic clock/order,
  completion, hash stability, and mismatch detection.

The v1 baseline includes, at minimum, deterministic rows for transaction-ID
  wrap with every issued ID retired; successful-completion delayed duplicates; out-of-order valid responses; wrong
protocol ID, MBAP length, unit, and PDU/function; unknown and duplicate IDs;
timeout/cancel followed by a late response; reconnect generation fencing; hard
queue overflow; no-starvation weighted scheduling; shutdown drain bound; one
absolute deadline across every FSM phase; retry allow/deny classification; a
new transaction ID and full ADU per retry; cancellation in queue/dial/read/
backoff; and profile-domain dual-match/conflict/separate-unit selection.

Stable required IDs are `TCP-WRAP-001`, `TCP-OOO-001`, `TCP-MBAP-001..003`,
`TCP-CORR-001..004`, `TCP-RECONNECT-001`, `TCP-BP-001`, `TCP-FAIR-001`,
`TCP-SHUTDOWN-001`, `TCP-DEADLINE-001`, `TCP-RETRY-001..004`,
`TCP-CANCEL-001..004`, and `PROFILE-COEXIST-001..003`. Coalescing, if later
enabled, adds a separately versioned `TCP-COALESCE-*` set before activation.

Each manifest row declares category, owner milestone, fixture, expected
outcome, timeout, and applicability. Expected `xfail` requires a reason, owner,
and expiry; unexpected fail, pass-to-fail, or xpass is a blocker. The baseline
report captures manifest/runtime versions, Go version, OS/architecture, matrix
runner version, serial-emulator version when applicable, start/end timestamps,
and per-ID evidence hash.

Proposed authoritative command:

```sh
go run ./cmd/modbus-matrix \
  --manifest conformance/modbus-matrix-v1.yaml \
  --report artifacts/modbus-matrix/v1/report.json
```

M2 baselines PDU/TCP/REPLAY. M2R independently adds RTU rows and baseline.
Gateway CI reruns applicable Modbus IDs when composition changes. Existing
gateway eBUS T01..T88 runs only as an independent regression when gateway
transport/runtime composition is touched.

## Public Provenance And Licensing Gate

Every public build runs a mandatory gate covering:

- per-source provenance manifest and fact/fixture/generated-artifact links;
- SPDX allowlist, denylist, and quarantine policy;
- clean-room, verbatim, derived, operator-capture, and generated classification;
- explicit redistribution permission and redaction/sanitizer attestation;
- dependency/import scan proving public dependency closure contains no private
  module, checkout, binary, fixture, generated artifact, or private URI;
- generated-artifact content/provenance scan;
- SBOM generation and policy evaluation.

Missing/unknown SPDX, provenance, derivation, or redistribution status fails
CI for the consuming fact. Denied/restricted/private source bytes cannot enter
public code, docs, fixtures, tests, reports, generated outputs, SBOMs, or release
artifacts. Private facts cannot flow upstream. Huawei clearance is fact-level:
an unknown or restricted fact blocks only its consuming selector, profile field,
or semantic leaf and does not blanket-block independently cleared facts.

## Restricted Evidence Custody Gate

FMB-08A-CUSTODY precedes FMB-08A. Actual restricted source remains in an
operator-controlled restricted evidence vault outside every public repository,
checkout, worktree, artifact store, and CI workspace. The public docs-modbus
artifact contains only opaque source IDs, cryptographic digests, policy versions,
and signed attestations that cannot reconstruct or identify the source payload.

`restricted-evidence-custody-v1` defines named ACL roles, least-privilege access,
acquisition and license decision records, legal owner, retention deadline,
cryptographic deletion plus verification, revocation, incident containment,
notification, and audit-chain requirements. These roles cannot overlap for one
fact set:

- restricted-source custodian/extractor, who alone sees restricted bytes;
- clean implementer, who sees only sanitized fact packets or independent live/
  public evidence and never source bytes, filenames, locations, or prose;
- independent verifier, who receives the fact hypothesis and independent
  evidence but neither the clean implementation nor restricted payload.

Signed non-overlap attestations bind role identities, source-set digest, fact-set
digest, time range, and revocation state. Canary tokens and forbidden-byte scans
cover Git history and objects, all worktrees, CI caches, logs, reports, fixtures,
generated artifacts, build contexts, packages, SBOMs, provenance, and releases.
A canary or ACL/retention/incident failure returns custody `NO_GO`, revokes the
fact set, and blocks FMB-08A. No new public or vendor repository is introduced.

## Huawei Provisional Facts And Independent Decisions

FMB-08A owns `expansion-provenance-v2` and these immutable, versioned artifacts:

- `huawei-applicability-v1`;
- `huawei-register-gates-v1`;
- `huawei-sentinels-v1`;
- `huawei-discovery-fsm-v1`;
- `huawei-provenance-ledger-v1`;
- `huawei-fact-clearance-v1`.

Before FMB-08A, every Huawei register, value predicate, sentinel, unit/topology
assumption, applicability branch, and budget is only a hypothesis. Each record
contains stable fact ID, opaque custody source ID/digest, evidence class,
paraphrased hypothesis, exact scope, applicability key/range, falsifier,
independent evidence, and consuming generators. Converted Huawei PDF/Markdown
bytes are never copied or redistributed. Tancabesti/operator analysis is a
derivation lead; `wlrcs` is implementation cross-check only. Neither is authority.

The Tancabesti corpus is represented publicly only by an opaque corpus ID,
opaque custody digest, operator-ownership attestation digest, custodian signer,
revocation generation, and signature. Source bytes, excerpts, filenames, URI,
source-document digest, and author identity are forbidden. Every Huawei fact
binds that opaque corpus ID to a sanitized fact-packet digest, derivation-step
digest, independent-verifier attestation, evidence class, and falsifier.
Substituting a corpus requires a new custody and clearance epoch. `wlrcs` can
only be listed as a non-sufficient implementation cross-check and can never
independently satisfy GO.

The initial provisional inventory is:

| Fact ID | Provisional hypothesis, not a requirement | Source/evidence class before FMB-08A | Required falsifier |
| --- | --- | --- | --- |
| `HUA-SL-UNIT0-H1` | A SmartLogger selector may begin at unit 0. | Restricted-source or operator lead; independent live/public corroboration required. | A supported applicability key identifies SmartLogger positively elsewhere or unit 0 produces contradictory family evidence. |
| `HUA-SL-ID-65521-H1` | Register 65521 may provide one SmartLogger positive predicate. | Restricted-source lead; independent confirmation required. | Positive non-SmartLogger fixture, supported SmartLogger counterexample, or predicate instability. |
| `HUA-SL-CONFIRM-40713-H1` | Register 40713 may independently enrich SmartLogger identity. | Restricted-source lead plus independent fixture/live corroboration required. | Counterexample, sentinel ambiguity, or model/firmware branch contradiction. |
| `HUA-SL-CONFIRM-40736-H1` | Register 40736 may independently enrich SmartLogger identity. | Restricted-source lead plus independent fixture/live corroboration required. | Counterexample, sentinel ambiguity, or model/firmware branch contradiction. |
| `HUA-SL-DOWNSTREAM-65534-H1` | Register 65534 values may describe downstream presence and not gateway identity. | Operator/restricted lead; independent topology evidence required. | Any cleared source or controlled fixture proves the values identify the gateway itself or have another scope. |
| `HUA-SL-DOWNSTREAM-UNITS-H1` | Downstream values 1 through 247 may be protocol unit IDs rather than UI ordinals. | Protocol plus operator lead; independent topology evidence required. | Cleared family evidence maps them as UI ordinals or uses a narrower/different valid domain. |
| `HUA-SD-UNIT100-H1` | After inconclusive SmartLogger evidence, a fresh connection at unit 100 may probe S-Dongle. | Operator/restricted lead; independent family fixture required. | Cleared evidence requires another unit/session order or shows unsafe ambiguity unresolved by the FSM. |
| `HUA-SD-STRUCT-37411-H1` | Register 37411 may be a structural S-Dongle fingerprint. | Restricted-source lead; positive and negative fixtures required. | Non-S-Dongle positive, supported S-Dongle negative, or firmware branch contradiction. |
| `HUA-SD-SEQUENCE-37412-H1` | Register 37412 may be a topology change sequence with a source-defined valid domain; nonzero is not assumed. | Restricted-source lead plus boundary fixtures required. | Cleared domain differs, a valid zero is rejected, or sequence semantics are not stable. |
| `HUA-SD-ID-30050-H1` | Register 30050 may enrich S-Dongle identity. | Restricted-source lead plus independent fixture/live corroboration required. | Counterexample, sentinel ambiguity, or branch contradiction. |
| `HUA-SD-ID-30015-H1` | Register 30015 may enrich S-Dongle identity. | Restricted-source lead plus independent fixture/live corroboration required. | Counterexample, sentinel ambiguity, or branch contradiction. |
| `HUA-SELECTOR-ORDER-H1` | Complete SmartLogger match may terminate selection; S-Dongle probe may run only after inconclusive SmartLogger evidence on a fresh connection. | Safety design hypothesis plus deterministic conflict fixtures required. | A supported topology cannot be selected safely in this order or produces unresolved cross-family false positives. |
| `HUA-SELECTOR-BUDGET-V1-H1` | A ceiling of two TCP connections, six FC03 ADUs including retries, one optional MEI ADU, and five seconds may be sufficient. | Planner safety hypothesis; deterministic and live latency evidence required. | Any supported key needs more work/time or the ceiling causes nondeterministic selection. |
| `HUA-SL-MAP-ISSUE39-H1` | SmartLogger map Issue 39 may change field types. | Restricted/public map lead; independent decode fixtures required. | Cleared map or fixture contradicts the type transition. |
| `HUA-SL-MAP-ISSUE40-H1` | SmartLogger map Issue 40 may contain divergent firmware branches. | Restricted/public map lead; independent branch fixtures required. | Cleared map proves one branch or different branch boundaries. |
| `HUA-SD-MODEL-FW-H1` | S-Dongle may require model/firmware-specific maps. | Restricted/operator lead; independent model fixtures required. | Supported models share one proven map or require different key dimensions. |
| `HUA-SENTINEL-SET-H1` | Per-field sentinel candidates may exist. Every numeric candidate receives a child fact ID. | Restricted-source lead; positive value and sentinel fixtures required per child. | A candidate is a valid value for any applicable key or omits a sentinel. |

FMB-08A consumes the passing custody attestation and independently emits exactly
one immutable outcome per `smartlogger.gateway`, `smartlogger.downstream`,
`s-dongle.gateway`, `s-dongle.downstream`, `emma.direct`, `emma.downstream`,
`relevant_rtu.direct`, and `relevant_rtu.downstream` scope:

- `GO(fact-set-digest)` lists the exact fact IDs, source/evidence classes,
  applicability, falsifiers exercised, independent verification digests,
  generator version, and expiry/revocation state permitted for that scope. It
  also embeds canonical `huawei-predicate-dag-v1`,
  `huawei-predicate-truth-table-v1`, `huawei-firmware-normalization-v1`,
  `huawei-field-facts-v1`, selector-cap vectors, and signed
  `huawei-fact-epoch-v1` bytes and digests;
- `NO_GO(reason,evidence-digest)` closes the consuming profile issue without
  generated predicate, profile, or catalog entry;
- `DEFER(reason,missing-evidence)` leaves the consuming issue blocked.

FMB-08F and FMB-08F-SD are conditional on matching nonexpired GO outcomes.
Generated predicates, selectors, sentinel tables, profiles, fixtures, and catalog
entries must contain the exact GO and fact-set digests. No handwritten fallback
is allowed. If the corresponding outcome is NO_GO, the issue closes without code
or catalog mutation. If DEFER, it cannot close or merge.

A blocked/revoked-fact mutation suite removes or revokes each fact ID and proves
that no predicate/profile/catalog is generated from it. At runtime, revocation
increments the source/fact disable epoch, removes only consuming selectors and
current leaves, preserves unrelated GO scopes and profiles, marks consuming
leaves typed unavailable without timestamp refresh, and preserves history.

### Executable Huawei Predicate Contract

Only a GO-generated `huawei-discovery-fsm-v1` may perform read-only FC03
positive-fingerprint selection. Writes, broadcasts, unit sweeps, and broad scans
are forbidden; optional MEI is enrichment only. The GO predicate DAG is canonical JSON under the existing byte-stable
fixture serializer. Every internal node has stable `node_id`, ordered children,
and exactly one operator: `all_of`, `any_of`, or `threshold`. A threshold node is
legal only when its source-cleared fact explicitly defines `k`, child set, and
truth table; a planner or generator cannot invent voting logic.

Every predicate leaf contains `fact_id`, `classification` (`match_required`,
`enrichment_only`, or `routing_only`), `evidence_independence_class`,
`source_chain_id`, `gateway_scope` (`exclusive` or `nonexclusive`), exact FC,
address, requested length, returned width, scalar/aggregate type, encoding,
signedness, byte order, word order, scale, value domain, sentinel handling, and
the outcome for malformed, truncated, Modbus exception, timeout, cancellation,
and unexpected length/type/value. Two predicates are independent only when both
their independence classes and source-chain IDs differ as required by the GO.
Readability, response timing, and unit 0 or 100 are always `routing_only`; MEI
success/failure is `enrichment_only`. None can be a positive discriminator or
satisfy a threshold.

`Matched` requires at least two source-cleared independent positive
discriminators classified `match_required`; enrichment-only facts cannot satisfy
the minimum. A S-Dongle match after inconclusive SmartLogger work additionally
requires at least one source-cleared `gateway_scope=exclusive` discriminator,
because unit 100 may be a SmartLogger downstream protocol address. Missing,
partial, sentinel, malformed, truncated, exception, timeout, cancellation, or
conflicting evidence never becomes positive. The GO truth table maps the full
DAG to exactly `Matched`, `Ambiguous`, or `Unknown`; conflict/cross-family/partial
positive evidence is `Ambiguous`, while absence of positive proof is `Unknown`.

For SmartLogger, FMB-08A must classify each cleared provisional 65521, 40713, and
40736 fact as `match_required` or `enrichment_only`; unit 0 remains routing-only.
For S-Dongle, the GO defines the joint source-cleared value/type/sentinel domain
for 37411 plus 37412 and classifies each 30050/30015 fact as match-required or
enrichment-only. A nonzero 37412 predicate is forbidden unless the cleared GO
domain explicitly requires nonzero. The literal numbers remain powerless outside
the matching GO.

FMB-08F/FMB-08F-SD generate predicate bytes without handwritten branches. The
generated bytes/digest and every evaluated outcome must equal the GO goldens.
Fixtures `HUA-PRED-VALID-*`, `HUA-PRED-NONHUA-*`, `HUA-PRED-MALFORMED-*`,
`HUA-PRED-TRUNCATED-*`, `HUA-PRED-EXCEPTION-*`, `HUA-PRED-TIMEOUT-*`,
`HUA-PRED-PARTIAL-*`, `HUA-PRED-SENTINEL-*`, and `HUA-PRED-CONFLICT-*` cover
every leaf and DAG branch. NO_GO or DEFER emits no generated selector, profile,
fixture, or catalog bytes. Complete GO-backed SmartLogger match terminates
top-level selection; no S-Dongle session then opens.

### Gateway Classification And Downstream Topology

FMB-08I exposes two noninterchangeable raw contracts. `GatewayClassification`
contains exactly `decision`, `endpoint_id`, nullable `gateway_family`, nullable
`gateway_asset`, nullable `topology_generation`, `selection_attempt_id`,
`session_generation`, `fact_epoch`, `fact_expiry`, `predicate_digest`,
`evidence_digest`, and monotonic observation coordinates. `gateway_asset` and
`topology_generation` are non-null only for `Matched`. `RawDownstreamObservation`
contains `gateway_asset`, `protocol_unit_id`, `topology_generation`,
`observation_state`, `fact_epoch`, source fact IDs, enumeration/status evidence
digests, session generation, and monotonic observation coordinates. It carries
no UI ordinal, device role, canonical edge, direction, unit, or semantic claim.

A positive unit-100 response after SmartLogger timeout/exception remains
`Ambiguous` plus unbound raw selector evidence unless the S-Dongle GO DAG
satisfies the two-independent-discriminator rule and includes an exclusive
cleared gateway discriminator. No keyed RawDownstreamObservation is emitted
without a Matched gateway_asset. The downstream identity key is exactly
`(gateway_asset, protocol_unit_id, topology_generation)`. `ui_ordinal` is a
separate non-address type and cannot populate, compare with, or alias
`protocol_unit_id`.

Enumeration and presence/status are committed atomically from one matched
gateway, one session generation, and one validated topology generation. The raw
topology FSM is `present -> stale -> removed`, with `reused` creating a new raw
identity when a removed protocol unit ID reappears in a later topology
generation. A complete agreeing enumeration/status set enters `present`; age or
loss of current validation enters `stale`; only a later complete validated
generation proving absence enters `removed`. Reconnect, gateway firmware or
identity change, fact-epoch change, or enumeration/status disagreement invalidates
the current generation, fences its observations, and requires a new atomic
generation. Disagreement is raw conflict/Ambiguous, never inferred absence.

`HUA-MIXED-TOPO-*` fixtures cover SmartLogger timeout and exception followed by
downstream unit-100 positives, multiple positives, stale enumeration, status
disagreement, UI-ordinal collision, removal/reuse, reconnect, and gateway
firmware change. No `RawDownstreamObservation` creates a canonical asset, role,
or topology edge before FMB-08J independently proves it from semantic scenarios.

### Compositionally Bounded Discovery

One monotonic `endpoint-selection-ledger-v1` spans the entire SmartLogger-first
and conditional S-Dongle attempt. Its aggregation key is exactly
`(endpoint_id, selection_attempt_id, config_generation, fact_epoch)`; connection
and session generations are children, never new budget scopes. Before each
operation it atomically records total connection opens, current/maximum concurrent
connections, attempted ADUs including every retry and attempt yielding an
exception, requested words, returned words, MEI attempts, and elapsed monotonic
time against one wall deadline. Reconnect and half-open work consume the same
ledger.

The effective cap vector is the componentwise strict intersection of the catalog
cap, central-governor grant, and every applicable nonexpired GO cap. A missing,
invalid, expired, or zero required dimension denies work. No family transition,
retry, exception, MEI request, or reconnect resets or widens a counter. A fresh
connection has a new generation and begins with no inherited pending entries,
cache values, parser bytes, partial ADU, or buffered response. Late prior-
generation responses are discarded and still cannot refund budget.

Boundary-minus-one, exact-boundary, and over-boundary fixtures exercise queue,
dial, write, read, backoff, exception retry, optional MEI, reconnect, late
response, mixed topology, cancellation, and deadline in every state. Exhaustion
or cancellation returns `Unknown`, cancels/drains the selection attempt, and
activates no decoder, profile, downstream generation, or candidate.

### Applicability And Field Parser Contract

Applicability is generated only from GO facts and keyed by
`(family, model, firmware_branch, map_issue)`. The GO owns the canonical firmware
grammar, byte normalization, parsed components, exact disjoint allowlists/closed
ranges, branch precedence, explicit backport IDs, and expected normalized bytes.
Precedence is declared and golden-tested as deny/quarantine, explicit backport,
exact ID, disjoint closed range, then unknown. Overlapping accepted ranges make
the GO invalid; malformed, unknown, overlapping-at-runtime, newer-unlisted, or
conflicting identity yields `Ambiguous` classification or field `Unknown` and
never lexical comparison, prefix matching, coercion, nearest-version/model/map,
or optimistic fallback.

Every generated profile field has separately revocable child fact IDs for
address, FC, width, encoding, signedness, byte order, word order, scale, unit,
sentinels, and applicability. FMB-08A models SmartLogger Issue 39 and Issue 40
field by field rather than as one map switch. An unknown/revoked dimension
quarantines only that field, prevents its FMB-08J semantic PASS, and leaves
independent fields eligible. Fixtures cover every lower/upper boundary, newer
version, malformed form, explicit backport, overlap, conflicting identity, and
every type/signedness/order/scale/unit/sentinel transition.

### Fact-Epoch Revocation Fence

Each GO includes signed monotonic `fact_epoch`, predecessor epoch/digest,
`not_before`, and `expires_at`. The exact epoch/expiry binds selector work,
profile activation, GatewayClassification, RawDownstreamObservation, candidates,
profile-set closure, semantic evidence, promotion, candidate image, exact-image
validation, and release evidence. Consumers revalidate signature, monotonicity,
scope, and expiry before profile activation, enqueue, dial, every retry/reconnect,
match commit, profile-set closure commit, raw/downstream or candidate output,
semantic/promotion publication, image build/validation, and release signing/
verification.

Revocation atomically rejects new work, increments the source/fact disable epoch,
cancels and boundedly drains all old-epoch ledger/session work, invalidates
topology generations, and withdraws only consuming outputs. A late old-epoch
response cannot produce Matched, refresh `observed_at`, republish a raw/canonical
value, activate a decoder, or enter/cross an energy-counter lineage. Fixtures
`HUA-REVOKE-RACE-QUEUE`, `-DIAL`, `-WRITE`, `-READ`, `-BACKOFF`, `-MEI`, and
`-RECONNECT` inject revocation at each state and record bounded cancellation,
drain completion, late-response rejection, and unaffected-scope continuity.

A readable register or selector/profile proof still does not establish role,
topology, direction, units, scale, or canonical meaning. FMB-08J remains the
independent successor semantic scenario and first canonical-topology gate.

The Tancabesti topology has no ESS and proves no ESS or EMMA semantics. EMMA
starts `DEFER` and has no catalog/profile/semantic claim before an FMB-08A GO
contains a source-backed discriminator, register map, applicability, per-field
sentinels, sanitized positive fixture, and independent verification. SmartLogger
or S-Dongle facts cannot satisfy that GO.

## Expansion Profile Scope Decision

The corrected contract order uses FMB-05B as evidence and FMB-03E0 -> FMB-05R -> FMB-05D -> FMB-05A/FMB-05C;
FMB-05A is GO-only, FMB-05C remains vendor-neutral, and documentation companions are artifact ancestors rather than downstream cycles.

Branches run in parallel:

- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.

The one-issue docs-modbus lane serializes execution without creating a cross-branch
artifact dependency.

FMB-08A-INVENTORY emits immutable `profile-candidate-inventory-v1` with the ten
concrete IDs declared in `plan.yaml.profile_candidate_inventory`. Every row names
standard, vendor, family, transport, direct/gateway/downstream attachment, gateway
family, consumer, and profile artifact. Wildcards, placeholders, duplicates,
omissions, or an undeclared consumer fail. This inventory is M8 expansion only;
Fronius base remains exclusively under FMB-03E0 and has no inventory/scope
dependency.

FMB-08A-CUSTODY is unconditional after its public documentation ancestors; it
never reads another downstream profile decision.

FMB-08A-SCOPE emits immutable `profile-scope-decision-v1` referencing only those
inventory IDs. It cannot create an extra row or substitute a family alias.

Every row binds exact fact-set digest, applicability/model/firmware/map digest,
positive/negative fixture digest, provenance/custody digest, transport-matrix
family, consumer node list, and exactly one outcome GO/NO_GO/DEFER/N/A. GO alone
enters the immutable inventory scope-selected set and enables only named
consumers. NO_GO
and N/A generate no profile, selector, fixture, or catalog bytes. DEFER leaves
that consumer unresolved, but all are terminal for schedule ordering and cannot
block a later independent row.
Growatt TCP/RTU therefore cannot run unconditionally. Huawei SmartLogger,
S-Dongle, and RTU consumers require both scope GO and matching nonexpired
FMB-08A detailed executable fact GO; scope never weakens the fact gate.

`selected_rtu_profile_nodes` derives only from concrete RTU inventory GO rows
owned by the ancestor scope decision. FMB-02R-A PASS/N/A does not select scope;
it separately controls whether selected RTU work is executable and whether the
RTU artifact/matrix is available. M2R N/A leaves the independent RTU scope set
auditable but terminalizes its executable consumers N/A and cannot reach M8
closure through absent transport evidence.

Each inventory row first becomes an immutable row fact. SmartLogger gateway,
SmartLogger downstream, S-Dongle gateway, and S-Dongle downstream are four
separate aggregation keys and component artifacts under their respective FMB-08F
or FMB-08F-SD bundle. A component is selected only by the exact row GO plus its
matching fact-scope GO. Downstream-only GO can emit only the downstream component;
gateway-only GO can emit only the gateway component. Neither can mint the other,
and SmartLogger cannot select S-Dongle. The union bundle contains exactly the
selected components and their fact/profile digests. Aggregation is commutative
and idempotent; conflicting outcomes for one exact row/family fail Ambiguous with
no component artifact.

Truth-table fixtures cover every outcome for every transport/family class,
the full paired Huawei cartesian product and input permutations, omitted/
duplicate consumer, stale digest, scope/fact disagreement, M2R N/A/PASS,
empty/each-single/mixed selected sets, generated-byte mutation under non-GO,
and exact selected-set closure/release reachability. FMB-08G-CLOSE conditionally
consumes only selected PASS profile artifacts and records every non-GO state.
An empty effective selected set terminalizes every expansion profile node,
FMB-08G-CLOSE, and FMB-08I through FMB-08Q as N/A with no artifact while leaving
FMB-06G active.

## Huawei RTU RED, Runtime Correction, And Reclosure

FMB-08G-RED consumes FMB-08A-SCOPE, matching FMB-08A outcomes, conditionally
selected TCP profile artifacts, and FMB-02R-A PASS only when an RTU row is
selected. For each selected GO-authorized RTU family it adds the exact failing profile/
transport case before any runtime correction and emits only one handoff:
`BLOCKED_RUNTIME_GAP(failing-matrix-digest)`. If no generic runtime defect is
present, FMB-08G-RED closes local `PASS(profile-evidence-digest)` and sends no
cross-repository handoff artifact or correction request.
`selected_rtu_profile_nodes` is derived only from concrete ancestor inventory
rows whose transport is RTU and whose scope outcome is GO. FMB-02R-A does not
participate in that derivation. If M2R is
N/A, or M2R is PASS with no RTU row selected, FMB-08C, FMB-08E, FMB-08G-RED,
and FMB-08H are N/A with absent artifacts. FMB-08G-CLOSE is N/A when no effective
profile remains, or emits a TCP-only selected closure when TCP profiles remain.
FMB-08O has no FMB-02R-A artifact edge; its exact matrix includes RTU only when
the derived selected RTU set is nonempty.

FMB-08H accepts only a signed `BLOCKED_RUNTIME_GAP` as a handoff. When that
artifact exists, a verified signed `tdd-unlock-v1` object and its digest must
already bind exact repo/issue/branch/HEAD, RED commit and parent, tests-only
changed paths/diff digest, CI-observed expected failure and time, live Git
ancestry evidence, gate version, OpenAI-only developer/tester/gate routes,
trusted signer, revocation generation, and signature before any implementation
commit. A mutable `VALID` string is never accepted. Future time, fabricated
string, wrong ancestry/diff/failure/signature, rewritten RED, or local bypass
fails. First invocation after implementation cannot retroactively unlock. The runtime fix remains semantics-
free and reruns the exact case plus the complete PDU/TCP/RTU/REPLAY matrix. When
FMB-08G-RED instead closed local PASS, FMB-08H deterministically closes N/A from
the predecessor terminal state, with no handoff payload and no code, release, or
capability change.

FMB-08G-CLOSE schedules after FMB-08G-RED and conditionally consumes its PASS
artifact, FMB-08H PASS only for a runtime-gap branch, and every selected profile
PASS artifact. It is the sole production-path profile closure and reruns the exact case, all applicable Huawei
profile/selector fixtures, the full RTU matrix, provenance/revocation tests, and
emits immutable `profile-set-closure-v2` containing every production profile
digest, GO fact-set digest or NO_GO/N/A state, runtime digest, matrix digest, and
rollback pin. There is no edge from FMB-08H back to FMB-08G-RED.

## Profile Acceptance Contract

All M8 expansion profiles require a matching FMB-08A-SCOPE GO row, stable descriptor identity, explicit applicability,
two-phase selection tests, namespaced versioned fixtures, provenance/license
manifests, runtime compatibility, typed raw-preserving observations, package
DAG compliance, public-build licensing gate, and deterministic replay.

- **Fronius v1:** read-only TCP; common/device inventory; inverter and Smart
  Meter observations; optional battery explicit unavailable/unsupported;
  integer/scale and float-mode evidence where applicable; live/replay hashes.
- **SunSpec:** independent detection/descriptor; model-chain discovery,
  termination, model versions, scale factors, and not-implemented sentinels.
- **Growatt:** never unconditional; a selected family TCP/RTU GO row binds its
  fact/applicability/fixture digests, device/firmware matrix, endian/word-order
  fixtures, and isolated provenance.
- **Huawei:** only matching scope GO plus FMB-08A detailed fact GO may generate separate
  SmartLogger/S-Dongle TCP selectors/profiles, topology contracts, applicability,
  sentinels, positive read-only fingerprints, or budgets. NO_GO produces no code/
  catalog; DEFER remains blocked. EMMA remains absent without its dedicated GO.
  RTU closes only through FMB-08G-RED/FMB-08H/FMB-08G-CLOSE.

## Fronius Live-Scope Decision And FMB-03E Proof

FMB-03E0 precedes any live network work and emits immutable
`fronius-live-scope-decision-v1` over exact operator target, safety/maintenance,
approved function/range, no-write, capture/custody, abort/restoration, runtime,
profile, and policy digests. Its outcome is exactly GO, NO_GO, or DEFER. GO alone selects FMB-03E and the Fronius-specific live branch.
Fronius NO_GO disables only Fronius-specific live and product nodes. It emits generic-public-library-release-v1 through FMB-05R; generic semantics and APIs continue to FMB-06G public-base-release-v1, which gates FMB-07B and later alternative-profile releases.

After FMB-05R, FMB-08A-INVENTORY emits the vendor-neutral candidate inventory independently of Huawei custody and fact clearance.
DEFER leaves Fronius-specific nodes blocked without fabricated live, semantic,
image, or release evidence. Machine simulations cover all three outcomes.

FMB-03E is a PROFILE-LEVEL live proof owned by `helianthus-modbusreg`. It uses a
standalone modbusreg conformance harness linked to the released
`helianthus-modbus` runtime. It depends on FMB-03D profile completion, FMB-02C
runtime/replay release, FMB-01E capture/security policy, and operator target
approval through FMB-03E0 GO. It does not depend on gateway, add-on configuration, resource
governor, release tuple, or kill switch.

Before live work it records the approved exact canonical target address/port,
unit IDs, FC03/FC04 register ranges, maintenance window, harness/runtime/profile
versions, fixed read/deadline limits, abort owner, and the FMB-01E capture
policy. A deterministic dry replay passes first. Harness construction exposes
no write API; egress enforcement and independent capture prove zero writes and
zero off-target access. Any target, function, range, capture, or restoration
deviation is FAIL and quarantines the run.

Elapsed time alone is insufficient. The minimum live matrix is startup
inventory; at least three complete polls; every discovered unit ID; at least
one timeout or cancellation; reconnect with generation fence; a late response
when safely injectable; and meter/battery absent or present cases as applicable.
The exact replay/decoder used by conformance processes the capture at least
twice. Acceptance requires byte-stable evidence hashes and equality of typed
results, unknown reasons, and errors across runs.

The same profile decoder runs the live capture twice and produces byte-stable
typed observations/errors/unknowns. FMB-01E decides whether sanitized bytes are
redistributable; otherwise only non-reconstructing hashes and attestation enter
public evidence. FMB-03E proves exact-target reads, no writes/off-target access,
profile decode, and live/replay equivalence. FMB-04B requires PASS; FMB-03E0
NO_GO propagates N/A without fabricating an FMB-03E attestation, and DEFER blocks.

## Gateway Live Lab, Reproducible SLO, Release, And Kill Latch

FMB-04L is the SYSTEM live-lab gate after FMB-04C and after both independent
latch evidence producers FMB-03P and FMB-04K, plus FMB-03R and FMB-03E. It runs
the gateway/add-on on the approved lab topology and proves the sentinel and
supervisor flag at wrapper pre-exec and gateway pre-init,
bounded drain, reconnect-storm suppression, breaker/governor invariants,
healthy-Modbus progress, eBUS isolation, atomic config rollback, typed health,
and observability. A socket spy proves zero Modbus sockets while disabled and
continued eBUS/core startup. This gate owns system abort/restore evidence; it
does not change the profile-level meaning of FMB-03E.

RTU remains nonblocking. When FMB-02R-A is not selected, every RTU transport row
in FMB-04L, FMB-04O, and base FMB-06H is typed N/A; base evidence proves TCP plus
the guarded RTU factory has zero config and zero opens. No mixed-RTU workload runs. The FMB-02R-A baseline key is exactly `repo+milestone+RTU+exact-HEAD`; every declared transport family requires a same-family immutable baseline, and a PDU baseline cannot satisfy RTU.

Helianthus Modbus v1 is read-only. FMB-02A permits exactly FC01-FC04; FC05, FC06, FC0F, and FC10 and every write quantity limit are absent. An explicit topology-ordered inventory, independent of behavior-class inference, covers every issue that can declare, transport, or execute a Modbus operation, including profile descriptors, selectors, live harnesses, and exact-image/release harnesses. Every listed issue declares exactly FC01-FC04, sets `raw_write_supported=false`, and executes FC05, FC06, FC0F, FC10, and generic write fixtures with and without authorization. Every attempt returns exact `UNSUPPORTED` before transport access; independently committed receipts prove zero transport and write-transport calls. Per-issue mutants replace each descriptor with FC05, FC06, FC0F, or FC10 and mutate authorization, transport access, outcome, and fixture completeness. Write capability is reserved for an explicit future milestone and is out of scope for v1.

Helianthus Modbus v1 is read-only. FMB-02A permits exactly FC01-FC04; FC05, FC06, FC0F, and FC10 and every write quantity limit are absent. FMB-02A and every gateway/API/runtime raw Modbus issue set `raw_write_supported=false` and execute FC05, FC06, FC0F, FC10, and generic write fixtures with and without authorization. Every attempt returns exact `UNSUPPORTED` before transport access; independently committed receipts prove zero transport and write-transport calls. Write capability is reserved for an explicit future milestone and is out of scope for v1.

Pre-M8 RTU dispatch for FMB-04L, FMB-04O, and FMB-06H requires a producer-signed FMB-02R-A release envelope. Fixture input binds its exact verified envelope digest; independently signed source-contract evidence resolves the complete producer repo, issue, exact HEAD, tree, artifact schema, version, content digest, authority, and signer tuple. The receipt records both verified evidence digests and the complete tuple, and dispatch occurs only on exact equality with no caller-controlled source label.

Helianthus Modbus v1 is read-only. FMB-02A permits exactly FC01-FC04; FC05, FC06, FC0F, and FC10 and every write quantity limit are absent. Every gateway/API/raw contract sets `raw_write_supported=false`; every write attempt returns `UNSUPPORTED` before and regardless of authorization. Write capability is reserved for an explicit future milestone and is out of scope for v1.

Pre-M8 RTU dispatch for FMB-04L, FMB-04O, and FMB-06H requires a producer-signed FMB-02R-A release envelope. Independently signed source-contract evidence resolves the expected producer repo, issue, exact HEAD, tree, artifact schema, version, content digest, authority, and signer tuple; dispatch requires exact equality, and the transport-authority envelope binds the producer-envelope digest rather than caller source labels. If M2R is selected and PASS, the exact-head RTU
baseline and full device/mixed/system matrix become applicable. The topology
simulates both traces and proves the absent trace reaches FMB-06G. M8 consumes
RTU only for profile-scope GO rows and otherwise records RTU N/A.

Gateway FMB-04O follows FMB-04L and precedes candidate production work.
Metrics have bounded cardinality and use pseudonymous endpoint, profile, and
state keys, never raw addresses or unbounded labels. They cover endpoint/session/
breaker state; queue depth/delay; outcomes, deadlines, retries, and reconnects;
rejected ADU reasons; scheduler starvation; probe/capture budgets; stale,
expired, and quarantined leaves; process sockets/goroutines/memory; and eBUS
pressure. Health emits structured reasons. A degraded Modbus subsystem does not
make the whole gateway unavailable unless core readiness fails.

FMB-04O publishes a versioned SLO protocol manifest with exact hardware, OS,
architecture, build, public release candidate, topology, poll intervals, exact
poll set, load, deterministic seed/injection timeline, and baseline hash.
Protocol v1 uses 5 minutes warmup, 30 minutes baseline, 30 minutes fault, and at
least 10 minutes recovery or until criteria; it extends duration until each
evaluated healthy endpoint has at least 300 scheduled polls. Baseline and fault
use the same tuple/hardware/config except the declared injection. Three
independent runs must all PASS.

The SLO manifest and report schema use exactly one normative recovery formula:
`from fault-clear to three consecutive successful polls <= breaker_max_open +
max_operation_deadline (which already includes bounded retry/backoff) + 3 *
configured_poll_interval`. Each run reports the numeric `breaker_max_open`,
`max_operation_deadline`, `configured_poll_interval`, and calculated bound;
tests recalculate the bound and verify the observed recovery duration.

The denominator is scheduled polls for endpoints declared healthy by the fault
manifest. The failing or breaker-open target is excluded from that healthy
ratio but remains in isolation metrics. Backpressure and deadline outcomes are
failures. p95 is nearest-rank over declared samples excluding warmup. The fault
schedule is deterministic. Each JSON report contains per-run evidence and
PASS/FAIL; all existing thresholds (healthy polls
at least 99% within 2x interval, eBUS p95 regression at most 5%, no T01..T88
drift, cap invariants, typed backpressure) must pass in every run.

FMB-03T creates the release mechanism early in `helianthus-ha-addon`: embedded
compatibility-manifest schema, detached public-attestation schema,
`public-release-control-v1`, generic private-extension schema, canonical digest
rules, verifier, persistent-state formats, and negative fixtures.

`public-release-control-v1` is independently rooted. Its offline authority root
is separate from every online release-signing key and signs append-only key-
control records containing authority epoch, signing-key epoch/key ID/status,
revocation generation, predecessor control digest, issuance, and maximum accepted
control age. Each public tuple contains monotonic `release_serial`, exact
predecessor tuple digest or explicit genesis, `not_before`, expiry, revocation
generation, signing-key epoch/ID, and minimum compatible persistent-state schema
range. A stale key, E2->E1 replay, duplicate/out-of-order serial, fork, expired
control, clock/disk/state rollback, or compromised signing key cannot activate or
sign its own recovery. Accepted release state becomes authoritative only in the
activation WAL's COMMITTED record, atomically with the active package pointer.

Rollback below committed public state is denied unless an independently
authorized, offline-root-signed one-use rollback token names exact current tuple,
target predecessor, allowed persistent-state schema range, reason, issuance/
expiry, and nonce. Token consumption and target activation are one separate
committed WAL transition and cannot be replayed. Authorized rollback never bypasses state-
schema compatibility, migration validation, or tuple signature/revocation checks.

FMB-06D and FMB-08N pin source commit and tree, dependency lockfiles, base-image
digest, toolchain/compiler versions, build flags, complete environment, normalized
time/locale/ordering/ownership, and every dependency digest. Two independent
clean builders with separate work/cache roots build the same source inputs; image,
SBOM, and provenance bytes and digests must be identical. Their manifests embed
only component/schema/config constraints, feature defaults, reproducibility
inputs/report digest, and the embedded manifest's own digest, never the image
digest. Any clean-rebuild mismatch blocks FMB-06H or FMB-08O.

Public packages use two durable package slots plus `activation-wal-v1`:
OLD_ACTIVE -> PREPARED -> COMMITTED -> CLEANED. PREPARED durably names the new
tuple, inactive slot, migration result, and high-water candidate, but that
candidate is not authoritative. COMMITTED is one checksum/predecessor-bound,
fsynced record that atomically binds the active pointer and authoritative
high-water. Recovery before COMMITTED boots old; recovery after COMMITTED boots
new and never rejects the current active tuple. CLEANED may remove obsolete
staging only. FMB-03T defines the machine; FMB-06H/08O validate it; FMB-06G/08Q
commit it. ENOSPC, SIGKILL, and power tests cover every WAL/data/fsync/pointer/
high-water/cleanup boundary before and after COMMITTED.

The private schema independently requires binding ID, public base digest and
base-lineage ID, binding contract version, canonical schema range, promotion-
manifest digest, capability-manifest digest, enabled capabilities, opaque artifact
digest, flags, `private_authority_epoch`, `signing_key_epoch`, monotonic
`extension_serial`, predecessor/genesis, `not_before`, expiry,
`revocation_generation`, signing key ID, and signature.

Private key rotation and revocation are append-only control records signed by an
authority root outside all extension signing keys. Each record binds binding ID,
authority epoch, signing-key epoch/key ID/status, revocation generation,
predecessor control digest, issuance, and maximum control-data age. The trust
policy declares that maximum age; stale, expired, unavailable, forked, or
signature-invalid control data disables only that private binding and boundedly
revokes its credentials. A compromised extension key cannot sign its own
reinstatement, key rotation, revocation removal, or authority epoch.

Before private activation, the verifier atomically compares the tuple with the
persisted highest-seen record keyed exactly by `(binding_id, base_lineage_id)`.
That record contains authority epoch, signing-key epoch, extension serial,
predecessor/tuple digest, revocation generation, highest trusted wall-clock value,
and append-only control checkpoint digest. Storage uses same-filesystem temp
write, file fsync, schema/signature/chain validation, directory fsync, rename,
and directory fsync. A torn, missing, corrupt, rolled-back, or checkpoint-lower
state disables the private binding until independently rooted control data and
state recovery prove a monotonic successor. Clock rollback or time uncertainty
cannot make an expired, not-yet-valid, old-key, or revoked tuple valid again.

Acceptance requires strict authority epoch/key epoch/revocation generation and
serial monotonicity, exact predecessor continuity, exact base lineage, current
control data, and current validity interval. Reusing, duplicating, reordering, or
forking a tuple is reject, never idempotent activation. FMB-03T fixtures and each
private release test E2->E1, duplicate/out-of-order serial, predecessor fork,
stale base, clock rollback, old key after rotation, compromised key, expired
revocation data, registry outage, and torn/rollback local state.

FMB-06H depends directly on FMB-03T and follows FMB-06D and every selected public gateway/schema/resolver/
Portal/HA artifact required by the candidate. It deploys the exact immutable
candidate image digest and reruns the complete applicable Modbus PDU/TCP/REPLAY
matrix, gateway SYSTEM live gate, versioned three-run SLO protocol, and
independent eBUS T01..T88 regression on that exact image digest, config digest,
and embedded-manifest digest. The SLO run uses the one normative recovery
formula above and reports/tests every numeric term and calculated bound.
FMB-06H emits immutable `final-candidate-validation-v1` evidence containing the
image and embedded-manifest digests, config and release-tuple inputs,
environment manifest, two-clean-builder byte/digest equality report, A/B package-
slot/pointer/migration fault report, public authority/key/control/high-water and
rollback-token negative report, and hashes of every matrix/live/SLO/eBUS report.

Only after FMB-06H may FMB-06G produce and sign the detached public tuple. It
may reference only the exact FMB-06H-validated image, embedded-manifest, and
evidence digests plus the validated public component versions/ranges, flags,
SBOM, and provenance. After tuple production, FMB-06G assigns the next public
release serial and exact predecessor, executes the FMB-03T verifier, persists
public highest-seen state, stages the inactive slot, verifies/migrates it, and
activates the durable pointer. It owns immutable final verification and startup
evidence. No earlier issue validates a future tuple. Any rebuild, gateway
change, config/schema change, or digest mismatch invalidates the evidence,
requires a new FMB-06H run, and makes signing fail. Startup verifies the tuple
before Modbus enablement; public operation needs no private extension. Tests cover
offline-root/signing-key separation, key compromise/rotation/revocation, E2->E1,
unauthorized and authorized one-use rollback/replay, incompatible state range,
rebuild mismatch, and every package/pointer/migration/signing/startup fault point.

Each generic private binding product signs a separate extension tuple under its
private licensing/release authority using the full FMB-03T anti-replay schema.
It contains no private repo name, commit, URI, bytes, or secret. The detached
public tuple is valid and complete without any extension and contains no private
identity. Missing, incompatible, expired, revoked, replayed, stale-control, or
registry-unavailable extension state disables only its manifest-supported
private capabilities and boundedly revokes private credentials.

Public logs, health, metrics, traces, support bundles, API payloads, evidence,
startup status, and timing expose no private extension presence, validity, count,
serial, registry state, or failure class. The preferred public schema omits an
extension field entirely; a compatibility-preserved field, if unavoidable, is
the constant `extension_capability_state=opaque` in every zero/one/multiple,
valid/invalid/expired/revoked/registry-outage case. Public request/startup paths
never synchronously wait for private registry or verification. Content, byte
digest, record/label cardinality, and deterministic timing envelope remain equal
across all cases. Detailed diagnostics exist only on a separately authorized
private control surface, use private credentials/storage, and never enter public
evidence or support bundles. Upgrade/rollback pins the public tuple first, then
independently selects or removes a monotonic compatible private extension.

## Canonical Cross-Repository Gate Ownership Matrix

This table is generated from milestone `depends_on` and internal `consumes_if`.
It excludes `schedule_after`. Its edge set is exactly all cross-repository
artifact edges; `justified_non_gate_edges` is empty. Conditional edges consume
bytes only when their predicate is true.

| Gate | Producer issue/repo | Immutable artifact | Exact cross-repo consumers | Contract test and final evidence | Rollback |
| --- | --- | --- | --- | --- | --- |
| G-AE-00D | FMB-00D / helianthus-execution-plans | `installed-gate-registry-verification-v1` | FMB-00D -> FMB-00E-EEBUS, FMB-00D -> FMB-00E-MATTER, FMB-00D -> FMB-00E-PUBLIC, FMB-00D -> FMB-01A | FMB-00D validates and publishes `installed-gate-registry-verification-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-00E-EEBUS | FMB-00E-EEBUS / helianthus-org-github | `eebus-private-repo-readiness-v2` | FMB-00E-EEBUS -> FMB-00F-EEBUS | FMB-00E-EEBUS validates and publishes `eebus-private-repo-readiness-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-00E-MATTER | FMB-00E-MATTER / helianthus-org-github | `matter-private-repo-readiness-v2` | FMB-00E-MATTER -> FMB-00F-MATTER | FMB-00E-MATTER validates and publishes `matter-private-repo-readiness-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-00E-PUBLIC | FMB-00E-PUBLIC / helianthus-org-github | `public-repo-readiness-v2` | FMB-00E-PUBLIC -> FMB-00F-DOCS, FMB-00E-PUBLIC -> FMB-00F-MODBUS, FMB-00E-PUBLIC -> FMB-00F-MODBUSREG | FMB-00E-PUBLIC validates and publishes `public-repo-readiness-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-01A | FMB-01A / helianthus-docs-ebus | `platform-modbus-architecture-v1` | FMB-01A -> FMB-03T, FMB-01A -> FMB-05R | FMB-01A validates and publishes `platform-modbus-architecture-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-01E | FMB-01E / helianthus-docs-modbus | `endpoint-mcp-custody-policy-v1` | FMB-01E -> FMB-02A, FMB-01E -> FMB-02R-A, FMB-01E -> FMB-03E, FMB-01E -> FMB-03E0, FMB-01E -> FMB-03P, FMB-01E -> FMB-03T, FMB-01E -> FMB-04A, FMB-01E -> FMB-04D, FMB-01E -> FMB-04K, FMB-01E -> FMB-04L, FMB-01E -> FMB-04S, FMB-01E -> FMB-06H, FMB-01E -> FMB-08O | FMB-01E validates and publishes `endpoint-mcp-custody-policy-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-02C | FMB-02C / helianthus-modbus | `modbus-matrix-v1` | FMB-02C -> FMB-03A, FMB-02C -> FMB-03E, FMB-02C -> FMB-03E0, FMB-02C -> FMB-05R, FMB-02C -> FMB-08B | FMB-02C validates and publishes `modbus-matrix-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-02R-A | FMB-02R-A / helianthus-modbus | `modbus-rtu-v1` | FMB-02R-A -> FMB-08C, FMB-02R-A -> FMB-08E, FMB-02R-A -> FMB-08G-RED | FMB-02R-A validates and publishes `modbus-rtu-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03D | FMB-03D / helianthus-modbusreg | `fronius-profile-v1` | FMB-03D -> FMB-03P, FMB-03D -> FMB-03R, FMB-03D -> FMB-05R | FMB-03D validates and publishes `fronius-profile-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03E | FMB-03E / helianthus-modbusreg | `fronius-live-evidence-v1` | FMB-03E -> FMB-04B, FMB-03E -> FMB-04L, FMB-03E -> FMB-05B | FMB-03E validates and publishes `fronius-live-evidence-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03E0 | FMB-03E0 / helianthus-modbusreg | `fronius-live-scope-decision-v1` | FMB-03E0 -> FMB-05R | FMB-03E0 validates and publishes `fronius-live-scope-decision-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03P | FMB-03P / helianthus-ha-addon | `config-kill-mode-conformance-v1` | FMB-03P -> FMB-03R, FMB-03P -> FMB-04K, FMB-03P -> FMB-04L | FMB-03P validates and publishes `config-kill-mode-conformance-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03R | FMB-03R / helianthus-ebusgateway | `resource-manifest-v1` | FMB-03R -> FMB-06H, FMB-03R -> FMB-08O | FMB-03R validates and publishes `resource-manifest-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-03T | FMB-03T / helianthus-ha-addon | `public-release-control-v1` | FMB-03T -> FMB-04K, FMB-03T -> FMB-07B, FMB-03T -> FMB-08EEBUS, FMB-03T -> FMB-09B | FMB-03T validates and publishes `public-release-control-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-04K | FMB-04K / helianthus-ebusgateway | `gateway-transport-latch-v1` | FMB-04K -> FMB-06D, FMB-04K -> FMB-06H, FMB-04K -> FMB-08N, FMB-04K -> FMB-08O | FMB-04K validates and publishes `gateway-transport-latch-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-04L | FMB-04L / helianthus-ebusgateway | `system-live-conformance-v1` | FMB-04L -> FMB-06H, FMB-04L -> FMB-08O | FMB-04L validates and publishes `system-live-conformance-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-04O | FMB-04O / helianthus-ebusgateway | `production-slo-v1` | FMB-04O -> FMB-05B, FMB-04O -> FMB-06H, FMB-04O -> FMB-08O | FMB-04O validates and publishes `production-slo-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-04S | FMB-04S / helianthus-ebusgateway | `mcp-custody-conformance-v1` | FMB-04S -> FMB-06H, FMB-04S -> FMB-08O | FMB-04S validates and publishes `mcp-custody-conformance-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05A | FMB-05A / helianthus-ebusgateway | `candidate-generation-v1` | FMB-05A -> FMB-05H | FMB-05A validates and publishes `candidate-generation-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05B | FMB-05B / helianthus-docs-modbus | `raw-promotion-dossier-v1` | FMB-05B -> FMB-05A | FMB-05B validates and publishes `raw-promotion-dossier-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05C | FMB-05C / helianthus-ebusreg | `canonical-pv-schema-v1` | FMB-05C -> FMB-05F, FMB-05C -> FMB-07A, FMB-05C -> FMB-08J | FMB-05C validates and publishes `canonical-pv-schema-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05D | FMB-05D / helianthus-docs-ebus | `canonical-pv-contract-doc-v1` | FMB-05D -> FMB-05A, FMB-05D -> FMB-05C, FMB-05D -> FMB-05F | FMB-05D validates and publishes `canonical-pv-contract-doc-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05E | FMB-05E / helianthus-ebusgateway | `promotion-manifest-v1` | FMB-05E -> FMB-06D, FMB-05E -> FMB-06H, FMB-05E -> FMB-07A, FMB-05E -> FMB-07B | FMB-05E validates and publishes `promotion-manifest-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05G | FMB-05G / helianthus-ebusreg | `energy-counter-fsm-v1` | FMB-05G -> FMB-05E, FMB-05G -> FMB-05F, FMB-05G -> FMB-08I, FMB-05G -> FMB-08J, FMB-05G -> FMB-08K, FMB-05G -> FMB-08M, FMB-05G -> FMB-08O, FMB-05G -> FMB-08Q | FMB-05G validates and publishes `energy-counter-fsm-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05H | FMB-05H / helianthus-ebusreg | `canonical-capability-catalog-v1` | FMB-05H -> FMB-06H, FMB-05H -> FMB-07A, FMB-05H -> FMB-08A-SCOPE, FMB-05H -> FMB-08EEBUS-A, FMB-05H -> FMB-08I, FMB-05H -> FMB-08J, FMB-05H -> FMB-08K, FMB-05H -> FMB-08L, FMB-05H -> FMB-08M, FMB-05H -> FMB-08N, FMB-05H -> FMB-08O, FMB-05H -> FMB-09A | FMB-05H validates and publishes `canonical-capability-catalog-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05I | FMB-05I / helianthus-ebusgateway | `mcp-stable-v1` | FMB-05I -> FMB-05J, FMB-05I -> FMB-06D, FMB-05I -> FMB-06H, FMB-05I -> FMB-08O, FMB-05I -> FMB-08Q | FMB-05I validates and publishes `mcp-stable-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05J | FMB-05J / helianthus-docs-ebus | `frozen-pv-mcp-graphql-companion-doc-v1` | FMB-05J -> FMB-06A, FMB-05J -> FMB-07A, FMB-05J -> FMB-07B, FMB-05J -> FMB-08EEBUS, FMB-05J -> FMB-08EEBUS-A, FMB-05J -> FMB-09A, FMB-05J -> FMB-09B | FMB-05J validates and publishes `frozen-pv-mcp-graphql-companion-doc-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-05R | FMB-05R / helianthus-ebusreg | `vendor-neutral-pv-rebaseline-v1` | FMB-05R -> FMB-05D, FMB-05R -> FMB-05F, FMB-05R -> FMB-05I, FMB-05R -> FMB-05J, FMB-05R -> FMB-06D, FMB-05R -> FMB-06G, FMB-05R -> FMB-06H, FMB-05R -> FMB-07B, FMB-05R -> FMB-08A, FMB-05R -> FMB-08A-CUSTODY, FMB-05R -> FMB-08A-INVENTORY, FMB-05R -> FMB-08A-SCOPE, FMB-05R -> FMB-08I, FMB-05R -> FMB-08N | FMB-05R validates and publishes `vendor-neutral-pv-rebaseline-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06A | FMB-06A / helianthus-ebusgateway | `graphql-schema-snapshot-v1` | FMB-06A -> FMB-06F, FMB-06A -> FMB-06H, FMB-06A -> FMB-07A, FMB-06A -> FMB-08A | FMB-06A validates and publishes `graphql-schema-snapshot-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06B | FMB-06B / helianthus-ebusgateway | `semantic-portal-v1` | FMB-06B -> FMB-06D, FMB-06B -> FMB-06H | FMB-06B validates and publishes `semantic-portal-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06C | FMB-06C / helianthus-ha-integration | `ha-entities-v1` | FMB-06C -> FMB-06D, FMB-06C -> FMB-06H | FMB-06C validates and publishes `ha-entities-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06E | FMB-06E / helianthus-ebusgateway | `graphql-resolver-conformance-v1` | FMB-06E -> FMB-06C, FMB-06E -> FMB-06D, FMB-06E -> FMB-06G, FMB-06E -> FMB-06H, FMB-06E -> FMB-07B | FMB-06E validates and publishes `graphql-resolver-conformance-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06F | FMB-06F / helianthus-ha-integration | `ha-compatibility-v1` | FMB-06F -> FMB-06H | FMB-06F validates and publishes `ha-compatibility-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-06G | FMB-06G / helianthus-ha-addon | `public-base-release-v1` | FMB-06G -> FMB-07B, FMB-06G -> FMB-08I | FMB-06G validates and publishes `public-base-release-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08A | FMB-08A / helianthus-docs-modbus | `huawei-fact-clearance-v1` | FMB-08A -> FMB-08F, FMB-08A -> FMB-08F-SD, FMB-08A -> FMB-08G-RED | FMB-08A validates and publishes `huawei-fact-clearance-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08A-SCOPE | FMB-08A-SCOPE / helianthus-docs-modbus | `profile-scope-decision-v1` | FMB-08A-SCOPE -> FMB-08B, FMB-08A-SCOPE -> FMB-08C, FMB-08A-SCOPE -> FMB-08D, FMB-08A-SCOPE -> FMB-08E, FMB-08A-SCOPE -> FMB-08F, FMB-08A-SCOPE -> FMB-08F-SD, FMB-08A-SCOPE -> FMB-08G-CLOSE, FMB-08A-SCOPE -> FMB-08G-RED, FMB-08A-SCOPE -> FMB-08I, FMB-08A-SCOPE -> FMB-08J, FMB-08A-SCOPE -> FMB-08O, FMB-08A-SCOPE -> FMB-08Q | FMB-08A-SCOPE validates and publishes `profile-scope-decision-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08G-CLOSE | FMB-08G-CLOSE / helianthus-modbusreg | `profile-set-closure-v2` | FMB-08G-CLOSE -> FMB-08I, FMB-08G-CLOSE -> FMB-08J, FMB-08G-CLOSE -> FMB-08K, FMB-08G-CLOSE -> FMB-08O, FMB-08G-CLOSE -> FMB-08Q | FMB-08G-CLOSE validates and publishes `profile-set-closure-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08G-RED | FMB-08G-RED / helianthus-modbusreg | `huawei-rtu-evidence-v1` | FMB-08G-RED -> FMB-08H | FMB-08G-RED validates and publishes `huawei-rtu-evidence-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08H | FMB-08H / helianthus-modbus | `modbus-runtime-gap-closure-v1` | FMB-08H -> FMB-08G-CLOSE | FMB-08H validates and publishes `modbus-runtime-gap-closure-v1`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08I | FMB-08I / helianthus-ebusgateway | `successor-candidates-v2` | FMB-08I -> FMB-08N, FMB-08I -> FMB-08O, FMB-08I -> FMB-08Q | FMB-08I validates and publishes `successor-candidates-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08J | FMB-08J / helianthus-ebusgateway | `semantic-scenario-manifest-v2` | FMB-08J -> FMB-08O, FMB-08J -> FMB-08Q | FMB-08J validates and publishes `semantic-scenario-manifest-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08K | FMB-08K / helianthus-ebusgateway | `promotion-manifest-v2` | FMB-08K -> FMB-08EEBUS-A, FMB-08K -> FMB-08M, FMB-08K -> FMB-08N, FMB-08K -> FMB-08O, FMB-08K -> FMB-08Q, FMB-08K -> FMB-09A | FMB-08K validates and publishes `promotion-manifest-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08L | FMB-08L / helianthus-ebusgateway | `api-portal-compatibility-v2` | FMB-08L -> FMB-08EEBUS-A, FMB-08L -> FMB-08M, FMB-08L -> FMB-08N, FMB-08L -> FMB-08O, FMB-08L -> FMB-08Q, FMB-08L -> FMB-09A | FMB-08L validates and publishes `api-portal-compatibility-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08M | FMB-08M / helianthus-ha-integration | `ha-compatibility-v2` | FMB-08M -> FMB-08N, FMB-08M -> FMB-08O, FMB-08M -> FMB-08Q | FMB-08M validates and publishes `ha-compatibility-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |
| G-AE-08Q | FMB-08Q / helianthus-ha-addon | `successor-public-release-v2` | FMB-08Q -> FMB-08EEBUS, FMB-08Q -> FMB-09A, FMB-08Q -> FMB-09B | FMB-08Q validates and publishes `successor-public-release-v2`; each target verifies exact digest/predicate before use. | Revoke or pin producer artifact; block only consuming edges; preserve unrelated schedule lanes. |

The validator derives this table and enforces
`cross_repo_artifact_edges == direct_gate_edges` with an empty, disjoint
justified-non-gate set. FMB-02R-A therefore gates FMB-08C, FMB-08E, and
FMB-08G-RED; FMB-08H is same-repo and is classified only as a
conditional artifact edge. Every schedule edge is validated separately.

## Candidate Sample, Merge, And Freshness Contract

Each versioned raw/profile candidate sample includes `poll_generation_id`,
endpoint `connection_generation`, the gateway observation pair defined below,
optional `source_at`, quality, evidence hash, profile ID/version, unit ID, raw
integer/value, scale, and typed unknown reason. Poll generation IDs are
monotonic per endpoint scheduling epoch and fenced across reconnect. Older
generations cannot overwrite newer committed fields.

Each semantic field declares a register dependency set. Gateway commits that
field only when every required register came from the same successful poll
generation and field validation passes. A failed or partial multi-register
read retains the previous value and both timestamps and never refreshes
freshness. Complete sibling fields from the same or another successful poll
may merge independently when their own dependency sets are complete. Sentinel,
unknown, malformed, and out-of-order samples produce typed evidence, not a
fresh value.

Gateway owns these generic non-destructive merge mechanics. `helianthus-ebusreg`
owns stable per-leaf freshness TTL, `fresh -> stale -> expired/unavailable`
transitions, compatibility, and expiry policy. A profile may supply observed
cadence metadata but cannot change canonical TTL or availability semantics.
Fake-clock tests cover each transition, reconnect fences, partial dependency
sets, sentinel values, retained timestamps, sibling merge, and out-of-order
poll/session generations.

## Canonical PV V1 Contract

`helianthus-ebusreg` owns a versioned, protocol-neutral graph. Transport
coordinates are mutable bindings and never identity. A site ID is a persisted
operator/config UUID. A physical asset ID is an opaque stable ID derived from
validated normalized manufacturer plus serial and model identity when that
identity is available. Otherwise it is a persisted generated UUID associated
with an evidence fingerprint. Endpoint, port, unit ID, and register addresses
may be rebound without changing the asset ID. A serial, model-identity, or
fingerprint change enters replacement review; it never silently merges with an
existing asset. Component IDs are opaque, asset-scoped stable IDs. Canonical
phase values are exactly `L1`, `L2`, `L3`, and `TOTAL`.

Topology is an explicit typed graph. V1 edges are `site_contains_asset`,
`site_contains_component`, `asset_contains_component`,
`component_has_role`, `meter_measures_boundary`, and
`meter_measures_asset`. V1 roles are `inverter`, `meter.grid_boundary`,
`meter.production`, `meter.load`, and `battery`; a meter edge identifies the
measured site boundary or asset. Register address, endpoint, unit ID, profile
selection, or numerical similarity alone cannot create a topology edge.

The minimum canonical leaf IDs are:

| Family | Required total leaf IDs | Optional phase form |
| --- | --- | --- |
| PV production | `pv.production.power.total`, `pv.production.energy.total` | replace `total` with `l1`, `l2`, or `l3` |
| Grid import | `grid.import.power.total`, `grid.import.energy.total` | replace `total` with `l1`, `l2`, or `l3` |
| Grid export | `grid.export.power.total`, `grid.export.energy.total` | replace `total` with `l1`, `l2`, or `l3` |
| Load consumption | `load.consumption.power.total`, `load.consumption.energy.total` when evidenced | replace `total` with `l1`, `l2`, or `l3` |
| Battery | `battery.state_of_charge`, `battery.charge.power.total`, `battery.charge.energy.total`, `battery.discharge.power.total`, `battery.discharge.energy.total` when present | no v1 phase leaves |

Asset/component-scoped `electrical.voltage.l1|l2|l3`,
`electrical.current.l1|l2|l3`, and `electrical.frequency.total` are measurement
leaves only where independently evidenced. Other values remain raw candidates
and are out of canonical v1 scope. Gateway promotion maps vendor candidate
fields into these IDs; vendor-specific canonical fields are forbidden.

Directional power and energy leaves are non-negative SI watts and watt-hours.
Import/export and charge/discharge are separate leaves; no canonical signed
direction value exists. A signed raw value needs a proven polarity mapping,
configured evidence-backed deadband, and direction scenario coverage. Both
directions being positive in one generation is `conflict` unless the device
explicitly proves independent channels. Raw integer and scale evidence is
retained. Conversion to SI is exact and rejects overflow, underflow, precision
loss beyond the declared source resolution, invalid scale, and non-finite
values. An absent phase is `not_supported` or unknown, never zero.

An authoritative measured `TOTAL` wins. A total may be derived only when all
required phases are present, valid, and from the same poll/connection
generation; it is marked `derived` with phase provenance. The contract defines
per-leaf absolute/relative comparison tolerances. A measured-versus-derived
tolerance breach is `conflict` and blocks promotion of that affected leaf.

Every quantity has one typed state from `valid`, `derived`, `not_supported`,
`not_applicable`, `temporarily_unavailable`, `stale`, `expired`, `invalid`,
`conflict`, or `quarantined`. Non-value states carry a null numeric value and
never substitute zero. Quality/evidence and provenance are retained through
promotion.

## Gateway Observation Time Contract

`observed_at` is a gateway-authoritative pair: a UTC wall timestamp for display
and audit plus a monotonic observation sequence/elapsed basis for ordering and
TTL. Freshness, duplicate rejection, late-response rejection, and ordering use
the monotonic observation/generation evidence, never device time or wall-clock
comparison alone.

`source_at` is optional provenance-tagged device-clock evidence. Configured
skew, future-time, rollback, and device-clock-reset checks assign its quality.
Invalid source time is retained only as evidence with `invalid` quality and
cannot determine ordering or freshness. Replay is marked `replayed` and uses
the recorded relative monotonic schedule. Cache restore is marked `restored`,
preserves original `observed_at` and age, and never refreshes TTL. A delayed or
late response cannot refresh a leaf. Fake-clock/replay coverage includes absent
source time, future/rollback source time, process restart, replay, cache restore,
wall-clock step, reconnect, and delayed response.

## Energy Counter FSM V1

`helianthus-ebusreg` owns a versioned per-component/per-leaf FSM with states
`UNINITIALIZED`, `TRACKING`, `WRAP_CONFIRMED`, `RESET_CONFIRMED`,
`DECREASE_QUARANTINED`, `REPLACED`, `STALE`, and `EXPIRED`. Persisted state stores
raw width/modulus/scale, source epoch, last accepted raw value, extended
monotonic Wh, explicit continuity offset/reset epoch, asset and component IDs,
observation generation/time, and quality/evidence provenance.

A plausible increase is accepted. A near-modulus to near-zero transition is a
wrap only when declared width/modulus, elapsed time, and configured maximum
rate prove it; the extended counter advances across the wrap. A confirmed
same-asset restart/reset begins a new source epoch and preserves extended
continuity only through an explicit offset. An ambiguous decrease enters
`DECREASE_QUARANTINED` and leaves the published counter unchanged. Replacement
changes component identity and statistic lineage; energy never accumulates
across assets. Gaps are not interpolated. A scale change requires profile
evidence plus a continuity check; otherwise it quarantines.

Fake-clock/replay tests cover wrap, duplicate, out-of-order, stale recovery,
confirmed reboot reset, ambiguous decrease, evidenced and unevidenced scale
change, replacement, and maximum-rate violation. Only a validated extended
monotonic counter may map to HA `total_increasing` or long-term statistics.

## MCP-First Raw Workbench, Contracts, And Stability

FMB-04D follows authorized raw/profile MCP integration FMB-04B and FMB-04S.
Its Portal workbench is an admin-scoped RE surface: paginated register grids,
side-by-side snapshot diff, immutable snapshots/exports, and bounded crafted
read-only probes using only allowed functions/ranges. Every operation reuses
MCP principal/site/endpoint/component policy, word/row/export/rate/concurrency
caps, audit, capture lifecycle, normalized denial, and route/transport fences.
It has no write path, semantic resolver, semantic.read bypass, direct canonical
publication, or consumer API. Tests attempt unauthorized inventory/snapshot/
export, cap/cursor bypass, semantic principal escalation, write functions, raw-
to-semantic leakage, retention failure, and support-bundle leakage.

The doc adapter makes evidence order executable. FMB-05B is the raw promotion
dossier contract and evidence ancestor; it depends on public raw/provenance docs,
FMB-03E profile proof, and FMB-04O system evidence, never FMB-05A. FMB-05D then
publishes the platform/semantic contract in docs-ebus. FMB-05A and FMB-05C
depend directly on those appropriate ancestors. Every intent companion is self
or graph ancestor; a machine audit rejects a companion that is downstream or
would require a synthetic cycle.

After raw MCP/workbench and promotion stabilize, the only promoted semantic MCP
tool is exactly `modbus.v1.semantic.pv.get`; alternate names are forbidden.
Its versioned request/response/error/auth schema binds promoted canonical PV
leaves, typed states, stable IDs, `observed_at`, cumulative counters, and one
consistency snapshot. Candidates remain internal and never enter public MCP
schema. The tool is unreachable before promotion and stability.

FMB-05I requires the operator to sign `MCP_STABLE` binding exact raw/profile
tools, workbench, `modbus.v1.semantic.pv.get` schema bytes, behavior and error
contracts, auth/custody/cap manifests, replay/negative evidence, promotion digest,
and predecessor/genesis. No elapsed observation period substitutes. FMB-06A
depends directly on this digest and proves GraphQL parity against the exact tool
for authorization, values, null/state/errors, identity, counters, consistency,
and shared fixtures. GraphQL is unreachable before PASS. Any later MCP schema or
behavior change creates a successor MCP_STABLE declaration and reruns downstream
compatibility rather than mutating the frozen declaration.

## Canonical Capability Catalog

FMB-05H follows FMB-05C and FMB-05G in the serialized `helianthus-ebusreg` lane.
FMB-05C emits authoritative `canonical-domain-schema-declarations-v1` from
static domain/schema source declarations independently of runtime registration,
reflection, package initialization, or linked binary reachability. FMB-05H owns
`canonical-capability-catalog-v1` and consumes that declaration inventory, the
runtime registration inventory, and generated catalog. Their normalized unique-
key sets and owner/range/schema/semantics bytes must be exactly equal. A wholly
unregistered domain therefore remains visible as a declaration/registration
mismatch rather than disappearing from all compared runtime sets. A PV hand-
list, private manifest, consumer list, or gateway reflection is not an input.

The unique key is exactly normalized `(domain, capability, major)`. Domain and
capability use canonical lower-case ASCII identifiers with one separator grammar;
major is an unsigned canonical integer. Every key has exactly one declared owner.
Ranges normalize to lower bound plus `lower_inclusive`, optional upper bound plus
`upper_inclusive`, explicit open-ended marker, and SemVer prerelease-inclusion
policy. Overlap analysis evaluates inclusive endpoints, open ends, and prerelease
ordering after normalization. Any overlap or cross-domain/normalized-key
collision rejects unless one declaration is an explicit alias to one canonical
key and schema bytes, semantic digest, owner and owner policy, status/range, and
deprecation policy are byte-identical. Aliases cannot create a second owner or
weaken compatibility.

Every domain/capability has stable ID, schema owner/version/range, status,
dependencies, enabled eligibility, successor/predecessor digest, and deprecation
window. The allowed status graph is:

```text
unsupported -> not-yet-implemented -> supported -> deprecated -> unsupported
```

Self-transitions are allowed only when schema/status/range bytes are unchanged.
No edge may be skipped. An enabled set is a strict subset of `supported`.
Any schema, status, range, enabled-set, or dependency change creates an immutable
successor catalog and requires successor private capability manifests/extensions;
published predecessors remain verifiable and cannot be rewritten.

Contract tests reject an entirely unregistered declared domain, missing runtime
registration, omitted/extra catalog capability, duplicate owner, cross-domain or
normalized-key collision, inclusive/open-ended/prerelease overlap, incompatible
alias, enabled-but-unsupported item, stale predecessor/catalog digest,
nondeterministic replay, unsupported direct transition, incompatible or ambiguous
downgrade. FMB-07A, FMB-08EEBUS-A, and FMB-09A depend directly on FMB-05H and
derive complete inventories from exact unique-key declaration/registration/
catalog equality evidence and digest.

## Semantic Scenario Promotion Matrix

FMB-03E proves transport/profile safety and reproducibility only. It does not
prove canonical direction, topology, quantity, or counter semantics. Before
FMB-05E, gateway FMB-05F produces a versioned per-role/per-leaf scenario matrix
and golden canonical outputs against the exact `ebusreg` contract. Evidence
methods are tagged `live_controlled`, `live_corroborated`, `replay_capture`, or
`synthetic_boundary`.

The matrix covers controlled or independently corroborated grid import and
export, PV production, load, every available phase, battery charge/discharge/
idle when applicable, meter present/absent and topology edges, scale-factor
changes, sentinels/unavailable, restart/reconnect, counter wrap/reset/
replacement, and measured-versus-derived conflict. Live evidence is required
where safe for direction/topology; deterministic synthetic/replay evidence
covers unsafe boundaries. Every direction/topology claim has at least one
independent reference or cross-check.

Each leaf/role result is `PASS`, `NOT_APPLICABLE` with evidence, or
`CANDIDATE_RAW`. Only `PASS` leaves promote; unproven leaves remain hidden/raw.
Golden outputs include IDs, topology, SI value or null, state, unit, quality,
timestamps, derivation/provenance, raw/scale evidence link, and counter lineage.

## GraphQL And Home Assistant Compatibility Contract

Before resolver rollout, FMB-06A publishes an exact versioned GraphQL schema
snapshot and compatibility matrix. Site, asset, component, node, and leaf IDs
are opaque and stable. The quantity shape always exposes `value` (nullable for
non-value states), non-null `state`, `unit`, `quality`, `observedAt`, observation
sequence, `derived`, and provenance/replay/restore flags; `sourceAt` is optional.
Power uses W. Energy uses a lossless decimal/string-backed Wh scalar or an
equivalent non-floating counter scalar. Unknown states have null value, never a
magic number. Evolution is additive-only with explicit deprecation. CI pins
nullability/types and runs prior-client query snapshots before every resolver
change.

FMB-06E owns server-side `semantic.read` authorization as part of resolver
execution. The authoritative principal comes only from the server-owned,
authenticated request/session context established by the configured auth or
supervisor adapter; resolver arguments, caller-supplied identity, and
unverified proxy headers are never principal sources. Default deny, required
scope, site scope, and component/endpoint scope are evaluated before object
lookup, identifier enumeration, cache access, or value resolution.

Denial is normalized across unauthenticated, missing-scope, wrong-site,
wrong-component/endpoint, and cross-site enumeration cases. It reveals no
value, object existence, identifier, cardinality, or timing-distinguishable
detail beyond the normalized denial contract. Fixtures equalize observable
status/error shape and bounded timing class. Authorized site-scoped Portal and
HA queries must succeed through the same path. FMB-06B, FMB-06C, FMB-06D,
FMB-06H, FMB-06G, FMB-07B, and FMB-09B depend on this passing contract.

FMB-06F owns the pre-implementation HA compatibility artifact. HA `unique_id`
is canonical component ID plus leaf ID, never endpoint/unit/address. Device
grouping is the site plus inverter/meter/battery components, using a via-device
relationship where HA supports it. Endpoint moves preserve identity;
replacement creates a new component/statistic lineage unless an explicit
evidence-backed migration is approved.

The per-leaf HA matrix records `device_class`, `state_class`, native unit,
entity category, availability mapping, precision/conversion, and
`statistic_id`. Power is W with `measurement`. Energy is `total_increasing` only
from the validated FSM output, with deterministic lossless Wh-to-kWh conversion.
Fixtures cover registry migration, duplicate prevention, restore snapshots,
stale/unavailable, topology change, endpoint move, replacement, and rollback.

The compatibility matrix spans profile, gateway candidate/promotion, ebusreg,
GraphQL, Portal, HA, add-on public tuple, and each private extension. On source,
profile, promotion, release disable, or tuple mismatch, gateway atomically
increments a disable epoch and immediately publishes every affected current
leaf as unavailable with typed reason `source_disabled` or
`incompatible_release`. GraphQL numeric values are null, availability is false,
and `observed_at` remains the original observation and never refreshes. Last
known values remain internal/history only.

HA keeps entities and recorder/statistics history but marks current entities
unavailable and emits no current sample. Portal and private bindings show the
same typed unavailable state. Entity deletion occurs only through explicit
component replacement/deprecation policy. Re-enable into the same lineage is
permitted only when asset/component ID, energy-counter FSM namespace, profile,
and schema compatibility all pass. Otherwise a new component/statistic lineage
is created or the source remains quarantined. A private extension mismatch
disables only that private capability. Replay, migration, rollback, and tuple-
mismatch tests prove retained values never appear current and counters never
cross incompatible identity.

## Private Bounded Conformance Contracts

`helianthus-eebus-binding-private` and `helianthus-matter-binding-private` are
generic protocol binding products spanning every domain in the public canonical
schema. Their names and product boundaries do not change when a new domain is
enabled. Every base or successor private manifest consumes the exact FMB-05H
unique-key declaration/registration/catalog equality artifact, binding/protocol
revision, canonical schema range, promotion manifest, and API/auth/schema
contract for its public base era. Every catalog key is exactly `supported`,
`unsupported`, or `not-yet-implemented`; omission is invalid. Enabled
capabilities are a subset of supported and begin exactly `[pv.v1]`.

Each manifest has a revision-pinned per-feature matrix covering every mandatory
and optional protocol service, operation, attribute, command/event, feature-map
bit, access direction, canonical leaf, unit, identity/topology mapping,
quality/freshness/availability behavior, and cumulative-counter reset/wrap/
reboot/replacement lineage rule. Each row identifies protocol/binding/schema/
promotion/API revisions, catalog unique key, mandatory/optional classification,
fixture, expected behavior, and PASS/unsupported/not-yet-implemented result. A
capability is `supported` only when every mandatory row is PASS. Optional gaps
are explicitly unsupported and not advertised. `not-yet-implemented` never
counts as supported, enabled, advertised, or partially available.

Full bounded-conformance replay rejects partial mapping, unsupported write/
command/event advertisement or execution, subscription expiry/reconnect/restart
failure, counter reset/wrap/reboot/replacement lineage error, partial protocol
availability advertised as complete, and any missing mandatory feature. eeBUS
matrices include SPINE entities/use cases/services/features, read/write direction,
pairing/discovery, retrieval/subscription and expiry. Matter matrices include
device type/endpoint/cluster, attributes, commands/events, feature maps, access,
availability and counter behavior. Matter remains bounded mapping conformance,
not parity.

FMB-07A is the M7 base-era eeBUS manifest against FMB-05E/FMB-06A and exact
eeBUS/SPINE/binding revisions. FMB-07B implements only its supported enabled
rows and closes terminal M7 as PASS, NO_GO, or PRIVATE_UNAVAILABLE. It signs a
fresh FMB-03T anti-replay extension against FMB-06G or emits no extension and
boundedly revokes private credentials.

FMB-08EEBUS-A is a distinct immutable successor eeBUS capability/conformance
manifest in the same private repo. It directly consumes exact FMB-08K promotion,
FMB-08L API/auth/schema, FMB-05H successor unique-key catalog evidence,
FMB-03T binding contract, exact successor eeBUS/SPINE/binding revisions, and the
signed FMB-07A manifest with full producer identity. FMB-07B is a terminal
scheduling predecessor only; no FMB-07B artifact/digest is a manifest input.
Full bounded-conformance replay is mandatory even when declared ranges overlap.
FMB-08EEBUS then consumes FMB-08EEBUS-A plus FMB-08Q and either signs a fresh
anti-replay extension or emits `PRIVATE_UNAVAILABLE`; in-place reissue, tuple
mutation, or reuse of FMB-07A PASS evidence is forbidden.

FMB-09A executes only after FMB-08Q and is the successor-current Matter manifest.
It directly pins FMB-08Q public base, FMB-08K promotion, FMB-08L API/auth/schema,
FMB-05H successor unique-key catalog evidence, and exact Matter/binding revision.
FMB-09B depends on that manifest and FMB-08Q, implements only supported enabled
rows, and signs a fresh FMB-03T anti-replay extension or emits
`PRIVATE_UNAVAILABLE`. FMB-05E-era conformance cannot authorize either successor
release.

Any public base, promotion, API/auth/schema, catalog, protocol, or binding
revision change creates an immutable successor private manifest and requires the
complete feature replay. An old manifest is rejected even if its declared range
overlaps. Private CI permits only promoted canonical public fixtures or
authorized semantic reads and rejects raw Modbus, modbusreg, candidate, gateway-
internal, unpromoted evidence, or private-to-public imports. A private gap creates
only NO_GO/unsupported/not-yet-implemented/PRIVATE_UNAVAILABLE and never requests
or mutates upstream public semantics.

FMB-07B, FMB-08EEBUS, and FMB-09B run all anti-replay/control-data/state tests and
bounded credential revocation from FMB-03T. Private release registries exclusively
own private digests, detailed diagnostics, status and audit. No public artifact,
tuple, SBOM, provenance, evidence, log, health, metric, support bundle, API,
startup output, cardinality or timing may reveal extension presence/validity/
count/registry state. Public outputs omit the field or use only the invariant
constant `extension_capability_state=opaque`; public bytes/content/cardinality/
timing remain equal for zero/one/multiple valid/invalid/expired/revoked/outage
cases. FMB-03T, FMB-06H, FMB-07B, FMB-08O, FMB-08EEBUS-A, FMB-08EEBUS and FMB-09B
own those canary and timing fixtures. Public release and operation succeed with
zero extension.

## Public Scheduling Independence From Private Systems

The prior M7-before-M8 scheduling barrier is superseded and forbidden. Public M8
dispatch and reachability depend only on public issue predecessors. The scheduler
does not query, wait for, subscribe to, or time out on a private repository,
registry, extension verifier, M7 state, or private control plane. M8 starts and
proceeds identically when the private repo is absent, the private registry is
partitioned indefinitely, M7 is still running, or M7 is PASS, NO_GO, or
PRIVATE_UNAVAILABLE.

PG-DRAFT-CURATION validates both artifact and scheduler graphs. Every public M8 ancestor,
readiness input, queue transition, timer, retry, and release input must be public.
Deterministic scheduler traces and public byte/content/cardinality/timing evidence
must match across all private cases, and FMB-08Q/exact-image validation must pass
with zero extensions. Any private control dependency or timing difference fails.
Private FMB-08EEBUS-A may wait for its private predecessor; FMB-08EEBUS may wait
for that manifest and FMB-08Q. Neither can gate, delay, or alter public work.

## M8 Successor Production And Release Contract

M8 profile work is not terminal at raw/profile proof. The public production path
is serialized by repository and carries immutable exact digests through these
issues and artifacts:

1. FMB-08G-CLOSE emits `profile-set-closure-v2` with every expansion profile,
   runtime, fixture, matrix, applicable GO fact-set, predicate/parser bytes and
   digest, signed fact epoch/expiry, and PASS/NO_GO/N/A digest.
2. Gateway FMB-08I consumes FMB-08G-CLOSE, FMB-08A, FMB-05H, and the FMB-06G
   predecessor tuple. It pins exact profile/fact/catalog digests in
   `candidate-source-manifest-v2`, composes the catalog, executes the one
   endpoint-selection ledger and gateway/downstream FSMs, and emits hidden
   generation/fact-epoch-fenced candidates only for production-enabled profiles.
3. Gateway FMB-08J depends directly on FMB-05C, FMB-05G, FMB-05H, FMB-08A,
   FMB-08F, FMB-08F-SD, FMB-08G-CLOSE, and FMB-08I. It emits
   `semantic-scenario-manifest-v2` and family/role/leaf goldens. Each result is
   PASS, evidenced N/A, or raw-only; detection/readability never proves semantics,
   and no raw downstream observation creates a canonical edge without this proof.
4. Gateway FMB-08K consumes FMB-08J and emits immutable
   `promotion-manifest-v2`, preserving predecessor IDs/history and promoting only
   PASS leaves. It binds profile, GO, candidate, catalog, counter, and scenario
   digests, fact epoch/expiry, and topology generation and implements atomic
   fact-revocation consuming-leaf-only disable and counter-lineage fencing.
5. Gateway FMB-08L reruns additive GraphQL compatibility, server-side semantic
   authorization/no-existence-leak, prior-query snapshots, Portal rendering, and
   rollback against the exact FMB-08K/catalog digests. It emits
   `api-portal-compatibility-v2`.
6. HA FMB-08M reruns compatibility, entity identity, availability, migration,
   restore, and statistics/counter lineage against FMB-08K/FMB-08L/FMB-05H and
   emits `ha-compatibility-v2` plus exact entity build digest.
7. Add-on FMB-08N builds `successor-candidate-image-v2` twice on independent
   clean builders from exact pinned source/tree/lock/base-image/toolchain/build-
   environment/dependency inputs and FMB-08I/K/L/M digests. Image, SBOM, and
   provenance bytes/digests must match. The embedded public manifest includes
   config/latch/auth, current fact/key/revocation/candidate/promotion/counter/
   topology high-water, persistent-state compatibility, rollback, and
   reproducibility digests, and contains no private data or identity.
8. Add-on FMB-08O deploys that exact image/config/embedded-manifest digest and
   reruns complete applicable Modbus PDU/TCP/RTU/REPLAY, all production profile/
   revocation fixtures, gateway SYSTEM live, three-run SLO, and independent eBUS
   T01..T88 plus HUA-PRED/HUA-MIXED-TOPO/HUA-REVOKE-RACE fixtures and bounded
   selection-ledger reports. It also exercises public release anti-replay,
   reproducibility mismatch, A/B package/config slots, durable epoch/counter/
   topology state, route/RTU device, governor, kill-mode, and MCP custody fault
   matrices. It emits immutable `final-candidate-validation-v2`.
9. Add-on FMB-08Q produces `public-successor-tuple-v2` only from FMB-08O-validated
   public digests and current durable fact/counter/topology/candidate/promotion/
   public-release high-water. It assigns the next release serial/predecessor,
   rechecks offline-root control and signing-key/revocation/validity/state range,
   signs, persists accepted high-water, stages/verifies/migrates the inactive A/B
   package slot, activates its pointer, and verifies deterministic startup. Any
   byte, config, profile, fact/epoch, catalog, schema, state, or evidence change
   requires a new 08O.

`m8-release-reachability-v1`, specified by the planning gate and executed by FMB-08Q,
loads these artifacts as structured data. For every `production_enabled` profile
in FMB-08G-CLOSE it requires the identical profile, GO fact-set, predicate/parser,
fact-epoch/expiry, and applicable topology-contract digests in
FMB-08I candidate, FMB-08J semantic, FMB-08K promotion, FMB-08N image input,
FMB-08O exact-image evidence, and FMB-08Q tuple trace sets. Missing, duplicate,
unknown, reordered-with-digest-change, or mismatched traces fail. The graph check
also proves FMB-08Q has no dependency path from any private issue or extension.

FMB-08EEBUS-A follows FMB-07B in the private eeBUS lane and rebuilds the complete
successor-current manifest from FMB-08K/FMB-08L/FMB-05H plus exact protocol/
binding revisions. FMB-08EEBUS then follows that manifest and FMB-08Q and emits
only a fresh anti-replay extension or PRIVATE_UNAVAILABLE. Public M8 never waits
for or depends on any private issue, state, timer, or artifact. Matter FMB-09A starts only after
FMB-08Q and builds the successor-current manifest; FMB-09B must bind it and
FMB-08Q, never FMB-05E-era conformance or FMB-06G.

Rollback is downstream-first: revoke/disable private extensions, pin the prior
FMB-06G public tuple, mark M8 leaves unavailable by disable/fact epoch without
timestamp refresh, preserve public schema/IDs/history/counters, discard FMB-08N/
08O/08Q successors, then withdraw only affected profile/GO/runtime artifacts
after dependency-freeze checks. Public rollback bytes remain independent of
private extension count or contents.

## Per-Issue Pre-Execution Matrix

`93-pre-execution-matrix.md` is the machine-readable PRE-EXECUTION INTENT matrix,
not authorization or a cached live preflight result. It contains exactly one row
per executable `plan.yaml.milestones` node with ID, repo, numeric complexity,
risk classes, and explicit doc, transport-family, smoke, and TDD intent/scopes.
Planning gates have no row. It contains no hard-coded developer, reviewer,
service, model, effort, or route. No field is inherited or blank.

PG-DRAFT-CURATION validates intent exact-set/repo/complexity/enums/nonempty
scopes, canonical/matrix/edge hashes, plan.yaml-to-90/91/lane exact parity,
outcome truth tables, selected-branch reachability, public/private independence,
and `m8-release-reachability-v1`. Before every executable issue/PR, installed
preflight inspects actual paths/state. Its success envelope contains only green
status, single/multi mode, eight row results, and authorization digest. The
authorization-bound cruise-state stores resolved route, workflow, doc companion,
two fresh review artifacts, topology readiness, exact transport baseline,
smoke scope, and TDD evidence.

Intent alone cannot create a branch, modify code, or open a PR. Any live row that
differs from intent must be resolved by an approved plan successor or stricter
live result before execution. FMB-08A predicate/parser/golden executable changes
are strict RED-CI even though their owning repo is documentation-oriented.
Docs-only issues may be docs-exempt only when actual paths prove no executable,
generator, schema-parser, fixture-runner, or test-code change.

PG-CRUISE-LOCK dry-runs the installed success envelope before authorization.
Schema drift, missing row results, unresolved routing, or non-green status refuses
lock/handoff. FMB-00D then verifies the exact pre-lock installed adapter registry
and attestation under that current generic preflight; it cannot install, patch,
or adapt skills after lock. No product issue becomes ready before verification.

Any new reverse-engineered fact discovered during code/profile work forces a
docs-modbus successor revision of the applicable FMB-08A artifact before that
code issue may merge. Protocol or transport work runs its declared Modbus matrix
even outside gateway repos; gateway composition and exact-image work run both
the Modbus matrix and independent T01..T88. Strict RED-CI requires a tests-only
commit observed RED by CI before implementation; juxtaposed mode requires the
installed workflow's exact paired test/implementation proof. Docs-exempt is
never inferred from repository name.

## Milestones

### M0 - Planning Gates, Adapter Alignment, And Provisioning

Repair the v2.6 Terminal Repair 22 Draft, maintain its prior ledgers,
synchronize canonical and pre-execution-matrix hashes, validate every preflight
row and release path, and complete a new terminal review. R1-R5 and Terminal Repair
Passes 1-3 remain historical evidence; Terminal Audit #4 `NO_FINDINGS` applies
only to the superseded v1.0 content. This amendment has `review_clean=false`,
`lock_ready=false`, and terminal review pending.

Gate: AMR1-A1..A7, AMR2-A1..A5, AMR3-A1..A5, AMR4-A1..A8, and AMR5-A1..A10 are RESOLVED with executable issue/gate/matrix artifacts,
`93-pre-execution-matrix.md` exactly equals the executable milestone set, focused checks pass,
and a fresh terminal reviewer returns no findings against this
exact canonical digest. Until then M1 remains blocked and no current
`NO_FINDINGS`, review-clean, or lock-ready claim is allowed.

After a fresh terminal review, PG-CRUISE-LOCK requires explicit operator
authorization and installed cruise-plan performs the committed `.locked` copy,
one meta-issue, cruise-state, and first FMB-00D preflight. FMB-00D is the first
executable node; FMB-00E-PUBLIC/EEBUS/MATTER then verify/provision exact
repos. Current curation is not authorized to commit, rename, push, create repos,
create GitHub state, install skills, or claim PLAN_LOCK.

### M1 - Public Documentation Grounding

Bootstrap docs-modbus raw protocol/evidence contracts; document architecture,
profile DAG, selection, fixture, matrix, provenance, endpoint/transport security,
operational-data handling, and vendor acceptance.
Docs-ebus records platform architecture and points canonical PV ownership to
`helianthus-ebusreg`.

Depends: authorized PG-CRUISE-LOCK, FMB-00D adapter PASS, and PUBLIC READY for
the new docs-modbus repo, not local review-clean or private readiness.

Gate: public docs build and licensing/dependency closure pass without private
checkouts, restricted facts, or promoted-schema ownership in docs-modbus.

### M2 - Generic PDU, Modbus-TCP, Replay, And Matrix

After PUBLIC READY, implement `helianthus-modbus` with read-only PDU/value contracts, generation-fenced
Modbus-TCP, bounded fair scheduling/backpressure, the retry/cancellation FSM,
deterministic recorder/replay, and PDU/TCP/REPLAY matrix categories.

Depends: M1. Gate: matrix baseline passes and a non-PV client imports the
library without profile dependencies. Rollback: pin/revert TCP runtime release.

### M2R - Nonblocking Modbus-RTU Runtime

Add RTU framing/session and RTU matrix rows after M1 and shared M2 PDU types are
available. Bind stable hardware/OS device identity, character-device ownership/
mode/exclusive-open, exact serial configuration, and hotplug generation fencing.
It is selected or typed N/A and does not block M3/M4/M6 base or Fronius TCP.

Gate when selected: RTU address/CRC/timing/truncation/noise matrix rows pass.
When absent, machine traces prove FMB-06G reachability and guarded zero-open.
Rollback:
withdraw RTU capability/release independently; TCP and profile catalog remain.

### M3 - Multi-Vendor Registry And Fronius Profile

Create the package DAG, static catalog validation, identity-domain coexistence,
bounded runtime probes, fixture/provenance conformance, unregistered shared SunSpec primitives,
and the Fronius profile composing those primitives directly. The first registered generic SunSpec profile remains FMB-08B after scope GO.

Depends: PUBLIC READY and M2 for profile code. FMB-03E0 first emits GO/NO_GO/
DEFER over the operator target/safety manifest. GO alone enables FMB-03E and the
product branch; NO_GO emits generic 02C/03D libraries and preserves generic successor eligibility; DEFER blocks product.
FMB-03E uses the standalone harness. In parallel, add-on FMB-03T freezes public/private
release-control, reproducible-build, and package-slot schemas/verifiers; FMB-03P
implements disjoint hard-stop/Modbus-disabled modes and A/B config migration;
gateway FMB-03R freezes numeric whole-fleet `resource-manifest-v1`.
Gateway second-latch ownership starts in M4 FMB-04K. Gate: profile
selection/replay pass; live proof is required only on GO and remains independent
of gateway/semantic claims. Rollback disables only the affected profile/branch.

### M4 - Gateway Sidecar And Raw MCP v1

Add offline-validated endpoint-ID-only composition with exact runtime/catalog
pins and the two-phase selection lifecycle. Enforce plaintext-isolated-LAN
policy with RFC1918/ULA default and explicit route-bound global exceptions,
admin/scoped/budgeted/audited complete MCP inventory, lifecycle custody, and
bounded operational diagnostics. Expose read-only raw/profile MCP evidence and
then FMB-04D admin-only raw Portal grids/diff/snapshots/crafted read probes.

Depends: FMB-03P/FMB-03R and M3, not M2R. FMB-04K consumes FMB-03P/FMB-03T
and owns the gateway second latch before FMB-04A or any downstream gateway
work. FMB-04B consumes FMB-03E PASS; 04D follows it and precedes FMB-04C.
FMB-04L follows composition and both 03P/04K latch evidence, then proves gateway/add-on system
behavior before reproducible FMB-04O. Base gate proves TCP plus guarded RTU
zero-config/zero-open and types RTU rows N/A; selected M2R adds full RTU identity/
mixed matrices. Hard-stop/Modbus-disabled, A/B config, fleet governor, MCP
workbench/custody, SLO, and T01..T88 pass. Rollback:
retain prior compatible config or MODBUS_DISABLED; whole-process stop explicitly
makes gateway/eBUS unavailable.

### M5 - Candidate Facts, Canonical Schema, And Promotion

Docs-modbus FMB-05B first publishes the raw dossier contract/evidence from
profile/system proof; docs-ebus FMB-05D then publishes the platform contract.
Gateway FMB-05A consumes both before emitting hidden candidates. `helianthus-ebusreg` defines stable canonical
PV identity/topology/leaves/quantities/time contract, freshness states,
versioning, and public canonical domain/capability enumeration. A second
serialized `ebusreg` issue implements the energy-counter FSM; FMB-05H then
compares authoritative static declarations, runtime registrations, and the
immutable capability catalog for exact unique-key equality. Gateway then proves
the scenario matrix, promotes, and FMB-05I obtains operator MCP_STABLE over exact
raw/workbench/promoted schemas before GraphQL.

Depends: M4. Gate: dependency direction is preserved; no candidate reaches a
consumer; each promoted leaf/role is PASS or evidenced NOT_APPLICABLE in the
scenario matrix and passes raw evidence, canonical contract, counter rules,
dossier, and rollback. Rollback: unpromote leaves while retaining raw MCP.

### M6 - GraphQL, Portal, And HA Rollout

After exact FMB-05I MCP_STABLE, freeze the additive GraphQL schema/compatibility snapshot, then implement
resolvers with server-side semantic authorization before Portal. In parallel
after schema freeze, author the HA compatibility matrix; HA implementation
waits for matrix and the authorized resolvers. FMB-06D builds two independently
reproducible candidates and stages the inactive A/B package slot. FMB-06H deploys
that exact digest and reruns complete Modbus/system/SLO/eBUS plus release anti-
replay/rollback, package/config faults, fleet-governor, kill-mode and MCP-custody
matrices. Base transport is PDU/TCP/REPLAY plus guarded RTU N/A/zero-open; only
selected M2R adds full RTU. Only then may FMB-06G issue, persist, migrate, activate and
verify the detached signed public base tuple.

Depends: M5 promotion. Gate: nullability/backward-query, semantic.read default-
deny/no-existence-leak, lossless energy, disable-epoch unavailable behavior,
entity/statistic lineage, migration/restore, embedded-manifest/image separation,
exact-image FMB-06H evidence, offline-root/key-control/serial/predecessor/state-
range verification, two-clean-build equality, one-use rollback token, A/B slot/
startup, distinct kill modes, and public dependency closure pass. Rollback uses
an independently authorized one-use token to a compatible verified predecessor
or remains on current slot; GraphQL/canonical IDs persist.

### M7 - Generic Private eeBUS Binding, PV v1 First

In `helianthus-eebus-binding-private`, FMB-07A pins the exact FMB-05H unique-key
inventory, FMB-05E/FMB-06A era, and eeBUS/SPINE/binding revisions. Its complete
per-feature matrix permits supported only when every mandatory row passes and
does not advertise optional gaps or not-yet-implemented rows. FMB-07B implements
only supported enabled rows, runs full bounded conformance and FMB-03T anti-
replay/zero-fingerprint tests, and closes terminal M7 as PASS, NO_GO, or
PRIVATE_UNAVAILABLE.

M7 has no scheduling relationship to public M8. Public work proceeds while M7 is
absent, partitioned, running, or terminal. Gate: feature replay, extension trust/
state/control-data negatives, bounded credential revocation, and public byte/
content/cardinality/timing identity pass. Rollback:
remove/revoke private extension and credentials; public tuple/runtime remain
unchanged.

### M8 - Custody, Profile Expansion, And Successor Public Release

Public M8 starts solely from public predecessors and never queries or waits on
private state.

Branches run in parallel:

- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.

FMB-08A-INVENTORY independently emits the immutable, concrete M8 expansion
inventory, and FMB-08A-SCOPE exhaustively classifies every inventory ID.

FMB-08A-CUSTODY establishes external-vault custody, role separation, canary
scans, and signed opaque attestations before FMB-08A. FMB-08A decides
GO/NO_GO/DEFER over provisional fact sets and freezes executable
predicate/applicability/field/cap/epoch goldens.

Fronius base remains
governed solely by FMB-03E0. Broaden SunSpec/Growatt only from scope GO, conditionally
generate SmartLogger FMB-08F and S-Dongle FMB-08F-SD only from scope+fact GO, and
close RTU through FMB-08G-RED -> FMB-08H -> FMB-08G-CLOSE. NO_GO creates no
code/catalog; DEFER remains blocked; EMMA has no profile without dedicated GO.

Production then follows FMB-08I candidate composition -> FMB-08J semantic
scenarios -> FMB-08K promotion -> FMB-08L GraphQL/auth/Portal -> FMB-08M HA ->
FMB-08N reproducible image/SBOM -> FMB-08O exact-image complete validation ->
FMB-08Q post-production verifier, durable A/B activation and successor tuple.
Every production profile/
fact/catalog digest reaches each node and passes the machine reachability
validator. FMB-08EEBUS-A builds and fully replays a distinct successor manifest
from 08K/08L/05H and exact protocol/binding revisions; FMB-08EEBUS then emits a
fresh anti-replay extension against 08Q or PRIVATE_UNAVAILABLE. Public release
has no private dependency and succeeds with zero extension.

Gate: custody, independent fact decision and rooted fact-revocation high-water,
byte-equal predicate goldens,
two-independent-discriminator identity, mixed-topology FSM, aggregate budget
ledger, exact applicability/field transitions, HUA-PRED/HUA-MIXED-TOPO/
HUA-REVOKE-RACE, blocked/revoked mutation, RED-CI runtime handoff, exact case/full
matrices, semantic/consumer compatibility, public-byte identity, exact-image
Modbus/profile/system/SLO/eBUS evidence, durable counter/topology/candidate/
promotion epochs, release anti-replay/reproducibility/A-B activation, route/RTU,
fleet governor, kill modes, MCP custody, private-independent scheduler traces,
current-epoch verification, and digest reachability all pass. Rollback uses an
authorized compatible public token or retains FMB-06G and disables
private successors first with bounded credential revocation, preserves public
schema/IDs/history and zero-fingerprint behavior, and withdraws only affected
profiles/facts/runtime after freeze checks.

### M9 - Generic Private Matter Binding, PV v1 First

In `helianthus-matter-binding-private`, FMB-09A starts only after FMB-08Q and
pins exact FMB-08Q/FMB-08K/FMB-08L/FMB-05H plus Matter/binding revisions. Its
successor-current per-feature matrix requires every mandatory row PASS and full
replay. FMB-09B depends on FMB-09A and FMB-08Q, implements only supported enabled
rows, and emits a fresh anti-replay extension or PRIVATE_UNAVAILABLE.

Gate: feature-level bounded conformance, FMB-03T trust/anti-replay and public
zero-fingerprint tests pass; no FMB-05E-era conformance, raw/profile/private
upstream flow, or semantic request is accepted. Rollback removes/revokes the
private extension and credentials only; FMB-08Q public runtime continues.

## Executable Per-Repository Lanes

Every executable milestone in plan.yaml is assigned to exactly one repository;
the following table is rendered from that source, and issue
and PR concurrency is one per repository. Default lanes are deterministic:

| Repository | Serialized lane |
| --- | --- |
| `helianthus-execution-plans` | FMB-00D |
| `helianthus-org-github` | FMB-00E-PUBLIC -> FMB-00E-EEBUS -> FMB-00E-MATTER |
| `helianthus-docs-ebus` | FMB-01A -> FMB-05D |
| `helianthus-docs-modbus` | FMB-00F-DOCS -> FMB-01B -> FMB-01C -> FMB-01D -> FMB-01E -> FMB-05B -> FMB-08A-CUSTODY -> FMB-08A ~> FMB-08A-INVENTORY -> FMB-08A-SCOPE |
| `helianthus-modbus` | FMB-00F-MODBUS -> FMB-02A -> FMB-02B -> FMB-02C -> FMB-02R-A -> FMB-08H |
| `helianthus-modbusreg` | FMB-00F-MODBUSREG -> FMB-03A -> FMB-03B -> FMB-03C -> FMB-03D -> FMB-03E0 -> FMB-03E ~> FMB-08B -> FMB-08C -> FMB-08D -> FMB-08E -> FMB-08F -> FMB-08F-SD -> FMB-08G-RED -> FMB-08G-CLOSE |
| `helianthus-ebusgateway` | FMB-03R -> FMB-04K -> FMB-04A -> FMB-04S -> FMB-04B -> FMB-04D -> FMB-04C -> FMB-04L -> FMB-04O -> FMB-05A -> FMB-05F -> FMB-05E -> FMB-05I -> FMB-06A -> FMB-06E -> FMB-06B -> FMB-08I -> FMB-08J -> FMB-08K -> FMB-08L |
| `helianthus-ebusreg` | FMB-05C -> FMB-05G -> FMB-05H |
| `helianthus-ha-integration` | FMB-06F -> FMB-06C -> FMB-08M |
| `helianthus-ha-addon` | FMB-03T -> FMB-03P -> FMB-06D -> FMB-06H -> FMB-06G -> FMB-08N -> FMB-08O -> FMB-08Q |
| `helianthus-eebus-binding-private` | FMB-00F-EEBUS -> FMB-07A -> FMB-07B -> FMB-08EEBUS-A -> FMB-08EEBUS |
| `helianthus-matter-binding-private` | FMB-00F-MATTER -> FMB-09A -> FMB-09B |

FMB-00D is the only initial node after external planning gates and lock. The
lane arrows are schedule-only; artifact requirements remain `depends_on` and
`consumes_if`. Provisioning rows independently select FMB-00F bootstraps. FMB-02R-A is
selected PASS or typed N/A after the TCP critical path; base work does not wait
on RTU evidence. Every M8 profile outcome terminally schedules the next profile;
DEFER supplies no artifact and cannot block a later independent GO. FMB-08G-RED then hands
only a signed BLOCKED_RUNTIME_GAP to cross-repo FMB-08H or closes local PASS;
FMB-08G-CLOSE conditionally consumes 08H PASS only for a runtime-gap branch and
is the sole profile-set production closure. Gateway, HA, add-on,
and private successor issues remain serialized in their own lanes.
Parallelism exists only across different repositories when all predecessor
edges are satisfied.

## Cross-Repository Compatibility And Rollback Matrix

The base matrix is emitted by FMB-06F/FMB-06G and its immutable successor by
FMB-08M/FMB-08Q. Every row names exact digests and supported ranges; prose such
as "latest" or "compatible" is invalid.

| Layer / producer artifact | Exact consumers | Required compatibility proof | Mismatch behavior |
| --- | --- | --- | --- |
| Modbus runtime release | modbusreg profile catalog; gateway adapter | runtime API range plus matrix baseline hash | Profile remains inactive; no socket for incompatible profile. |
| Modbusreg profile release | gateway candidate decoder | descriptor/profile/fixture schema ranges and FMB-03E attestation | Increment source disable epoch; affected source unavailable. |
| Gateway candidate/promotion | ebusreg validator; GraphQL resolver | durable fact/counter/topology/candidate/promotion high-water, schema and promotion-manifest digest | Stale/uncommitted state is quarantined; no current semantic value. |
| Ebusreg canonical schema/FSM | gateway promotion/resolver; HA matrix; private manifests | schema, state-reason, identity, and counter namespace ranges | `incompatible_release`; no counter/identity lineage reuse. |
| Canonical capability catalog | private manifests; gateway/HA/add-on successor | exact static declaration=runtime registration=generated catalog unique-key/owner/schema/semantics/range equality, predecessor digest, status transitions, supported-only enabled set | Reject stale/omitted/unregistered/duplicate/overlapping/ambiguous capability or alias; require successor manifest/extension. |
| Huawei custody/fact decision | generated profiles; gateway classification/downstream/candidates/promotion | custody digest plus exact nonexpired GO fact/predicate/parser/field/cap/epoch digests or NO_GO/N/A | DEFER blocks; NO_GO generates nothing; revocation denies/cancels/drains and removes only consuming outputs. |
| Expansion profile-set closure | successor candidate/semantic/image/release | exact profile/GO/predicate/parser/fact-epoch/runtime/matrix digest trace | Profile remains non-production; stale epoch cannot activate; release reachability fails. |
| GraphQL schema/resolver | Portal; HA; private bindings | pinned schema snapshot, prior-query set, nullability and reason fixtures | Consumers retain identity but show unavailable; no current sample. |
| Portal build | add-on image | GraphQL schema range and rollback fixture hash | Portal feature disabled; gateway/HA continue. |
| HA integration build | add-on image | GraphQL and HA matrix ranges plus migration/rollback hash | HA entities unavailable; registry/statistics history retained. |
| Add-on embedded manifest/image | FMB-06H exact-image validator | pinned source/tree/locks/base/toolchain/flags/env/time/dependencies, two-build image/SBOM/provenance equality, config/package A/B schemas and all public ranges | Discard inactive candidate; retain prior active verified slot or MODBUS_DISABLED with eBUS/core. |
| `final-candidate-validation-v1` | FMB-06G tuple producer/verifier | exact reproducible image/config/manifest/evidence plus release-control, package/config fault, route/RTU, governor, kill-mode and MCP-custody reports | Signing/activation fails; retain prior active slot; rerun FMB-06H. |
| Detached public base tuple | add-on startup; optional private extensions | offline-root key control, release serial/predecessor/validity/revocation/state range, exact FMB-06H binding, activation-WAL committed active pointer plus authoritative high-water, A/B migration/startup evidence | Unauthorized rollback/replay fails; one-use authorized rollback is a committed transition to a verified state-compatible predecessor. |
| M8 successor public tuple | add-on startup; private extensions downstream only | exact 08O reproducible image/evidence and durable fact/counter/topology/candidate/promotion/release high-water plus private-independent scheduler/reachability traces | Revocation/expiry/stale state blocks activation; retain verified FMB-06G slot; never wait for or inspect private state. |
| Private extension tuple | one generic private binding product, restricted to manifest-supported enabled capabilities | authorized private registry verifies exact public base/lineage, binding contract, canonical schema range, promotion and capability manifests, enabled `[pv.v1]`, opaque artifact, independently rooted authority/key epochs and control-data age, monotonic serial/predecessor, not-before/expiry/revocation generation, signature, and crash-atomic highest-seen state | Any replay/fork/stale base/key/control data, clock rollback, outage, or torn/rollback state disables and boundedly revokes only that private binding. Public bytes, content, cardinality, and timing remain invariant and reveal no extension presence or result. |

| Publication stage | Ordered action | Owner and issue gate |
| --- | --- | --- |
| Before stable consumer publication | Enter MODBUS_DISABLED for normal rollback, reject/drain work, withdraw profile/catalog after freeze, and retain prior config/package active slots. WHOLE_PROCESS_HARD_STOP is only an explicit supervisor action and makes gateway/eBUS unavailable. | Config/modes FMB-03P/04K; runtime FMB-02B/C/02R-A; resources/security FMB-03R/04A/04S; profile/gateway FMB-03D/04B. Gate: mode-specific readiness, bounded drain, no publication. |
| Canonical promotion but before consumers | Stop new promotion; select last durable fact/counter/topology/candidate/promotion records; preserve IDs/history/raw evidence and publish additive fixes. | Fact FMB-08A; counter FMB-05G; topology/candidate FMB-08I; semantics/promotion FMB-05A/F/05E/08J/K. Gate: checksum/predecessor/pointer, fault injection and nullable unavailable pass. |
| After GraphQL/consumer publication | Disable private bindings and boundedly revoke their credentials first; increment disable epoch for incompatible public source/tuple; current leaves immediately become typed unavailable/null without timestamp refresh; retain entities/IDs/history; assert both latch layers and pin prior public tuple. Forward-fix/deprecate additively. | Private: FMB-07B/FMB-08EEBUS-A/FMB-08EEBUS/FMB-09A/FMB-09B; public release: FMB-03T/FMB-06D/FMB-06H/FMB-06G; HA: FMB-06F/FMB-06C; Portal/GraphQL/auth: FMB-06B/FMB-06E/FMB-06A; latch: FMB-03P/FMB-04K; promotion/canonical: FMB-05E/FMB-05F/FMB-05G/FMB-05C. Gate: anti-replay/control-state rollback tests pass, public observations remain invariant, no retained value appears current, and counters do not cross lineage. |
| M8 successor publication | Revoke fact epoch, deny/drain work, durably invalidate topology/candidate/promotion, retain active FMB-06G slot or consume one-use compatible rollback token, mark successor leaves unavailable without timestamp refresh, then withdraw affected profile/runtime. Private state is not consulted. | Public FMB-08A/I/J/K/N/O/Q, FMB-05G/H and release FMB-03T/06G; profiles FMB-08B..G-CLOSE/H. Gate: durable high-water/fault, release-control/A-B startup, reachability and private-independent schedule/bytes/timing. |
| Profile expansion before successor publication | Withdraw only the affected selector/profile/field set; preserve compatible runtime, other identity domains, and unrelated GO fact IDs. | Custody/facts FMB-08A-CUSTODY/FMB-08A; profile closure FMB-08B/C/D/E/F/F-SD/G-RED/G-CLOSE; runtime FMB-08H. Gate: GO revocation, RED/reclosure, compatibility freeze, and rollback pin pass. |
| Security/licensing emergency | Assert the sentinel/flag, hard-disable affected data flow, append independently signed private authority/key revocation control data, boundedly revoke credentials/extensions, quarantine captures/artifacts, and retain the public schema contract as unavailable. | Security/data policy FMB-01E; wrapper latch/config FMB-03P; gateway latch FMB-04K; provenance FMB-01D/FMB-08A; affected runtime/profile/gateway owner; private owners FMB-07A, FMB-07B, FMB-08EEBUS-A, FMB-08EEBUS, FMB-09A, FMB-09B. Gate: incident records scope, control-data age, retained contract, pins, deletion/quarantine, bounded revocation, and remediation. |

Persisted caches/state carry schema and producer versions. Unknown versions are
rejected or quarantined, never guessed. Migration tests cover supported prior
versions; restore tests use immutable snapshots. A dependency freeze prevents
withdrawing a version while any merged downstream compatibility range requires
it. Before each merge, the owning issue records compatible producer/consumer
ranges, rollback pin set, snapshot hash, and the issue that removes the freeze.

| Milestone | Rollback/compatibility owner issues | Required gate |
| --- | --- | --- |
| M0 planning | PG-DRAFT-CURATION/PG-FRESH-TERMINAL-REVIEW/PG-CRUISE-LOCK; FMB-00D; FMB-00E-PUBLIC/EEBUS/MATTER | Draft-only revert before authorization; adapters/provisioning roll back in their control repos without implicit repo creation or public/private coupling. |
| M1 | FMB-01A/B/C/D/E | Revert docs independently; public dependency/provenance/security policy remains valid. |
| M2 | FMB-02A/B/C | Reject/drain/cancel, close session, pin prior runtime; matrix and consumer ranges identify the pin. |
| M2R | FMB-02R-A | Fence/close RTU device generation and disable RTU after freeze; TCP remains. |
| M3 | FMB-03A/B/C/D/E0/E/T/P/R | Preserve generic 02C/03D release on NO_GO; withdraw live/product branch independently; retain active config slots and eBUS reserve. |
| M4 | FMB-03P/R, FMB-04K/A/S/B/D/C/L/O | Disable raw Portal separately; base RTU stays N/A unless selected; preserve kill/config/route/custody evidence. |
| M5 | FMB-05A/B/C/D/E/F/G/H/I | Revoke MCP_STABLE successor/downstream consumers, stop promotion, preserve raw dossier/docs/IDs/history/catalog predecessors. |
| M6 | FMB-03T, FMB-06A/B/C/D/E/F/H/G | Invalidate 06H on change; retain highest verified active slot or use authorized compatible one-use rollback; preserve schemas/IDs/history. |
| M7 | FMB-07A/B | Disable/revoke private binding and credentials without any public scheduling, artifact, or timing dependency. |
| M8 | FMB-08A-CUSTODY, FMB-08A, FMB-08A-INVENTORY, FMB-08A-SCOPE, FMB-08B, FMB-08C, FMB-08D, FMB-08E, FMB-08F, FMB-08F-SD, FMB-08G-RED, FMB-08H, FMB-08G-CLOSE, FMB-08I, FMB-08J, FMB-08K, FMB-08L, FMB-08M, FMB-08N, FMB-08O, FMB-08Q, FMB-08EEBUS-A, FMB-08EEBUS | Revoke inventory/scope/fact epochs, remove only selected consumers, pin FMB-06G, preserve contracts/history/counter lineage, and keep private successor downstream. |
| M9 | FMB-09A/B | Require successor-current full conformance after FMB-08Q; disable private binding and boundedly revoke credentials before public-layer changes. |

## Decision Matrix

| ID | Decision | Resolution |
| --- | --- | --- |
| AD01 | Generic runtime stays semantics-free. | `helianthus-modbus` owns PDU/TCP/replay, RTU, and every future Modbus transport only. |
| AD02 | Profiles share one public repository. | `helianthus-modbusreg` is the sole SunSpec/vendor catalog/profile home; no per-standard or per-vendor repo exists. |
| AD03 | Canonical PV schema has a core owner. | `helianthus-ebusreg` owns stable IDs/types/versioning/promotion; gateway applies it. |
| AD04 | Documentation ownership is split. | docs-modbus owns raw evidence; docs-ebus documents architecture/promoted semantics. |
| AD05 | RTU is nonblocking. | M2 is Fronius TCP critical path; M2R is independent expansion. |
| AD06 | Selection is two-phase. | Static pre-transport validation then bounded read-only runtime probes. |
| AD07 | Manual override remains checked. | Exact profile+version; compatibility, capabilities, identity probes, and budgets still apply. |
| AD08 | Decoder reuse follows an explicit DAG. | Profiles compose primitives, never profiles; catalog registers profiles. |
| AD09 | SunSpec detection is profile-owned. | Fronius imports SunSpec primitives directly, not the SunSpec profile. |
| AD10 | Fixtures are versioned deterministic evidence. | Canonical byte serialization, immutable inputs, checksums, schedule, and completion are mandatory. |
| AD11 | Modbus conformance has its own executable matrix. | Stable PDU/TCP/RTU/REPLAY IDs, expected outcomes, baseline, versions, fail/xpass gate. |
| AD12 | eBUS T01..T88 remains independent. | It runs only for touched gateway composition and never substitutes for Modbus tests. |
| AD13 | Public provenance is a build gate. | SPDX policy, derivation, redistribution, scans, closure, and SBOM are mandatory. |
| AD14 | Fronius v1 is read-only TCP. | No writes or RTU dependency. |
| AD15 | Delivery remains raw MCP first. | candidate -> ebusreg contract -> GraphQL -> consumers/private bindings. |
| AD16 | Private knowledge cannot flow upstream. | Public closure scans reject private modules/artifacts/facts. |
| AD17 | Review-clean differs from PLAN_LOCK. | Locked content hashes, the committed `.locked` copy, validator/report, and separately recorded external lock metadata are authoritative. |
| AD18 | TCP correlation is generation-fenced. | Pending key is generation/transaction/unit; strict MBAP/PDU validation and quarantine prevent late/old satisfaction. |
| AD19 | Endpoint owns one bounded fair session. | Pool key excludes unit; one default connection, bounded queue/in-flight, weighted deficit round-robin, typed backpressure. |
| AD20 | Retry/cancel is one-deadline FSM. | Read allowlists, two-attempt default, classified retry, fresh ADU/transaction ID, interruptible phases. |
| AD21 | Profiles coexist by identity domain. | One exclusive primary; Fronius and generic SunSpec conflict for one unit; affirmative vendor evidence is required. |
| AD22 | Live proof is matrix-based and reproducible. | Approved safety manifest, attested sanitized capture, minimum scenarios, two byte-stable replays, redistribution gate. |
| AD23 | Merge and freshness have separate owners. | Gateway merges complete field generations; `ebusreg` owns canonical TTL and availability transitions. |
| AD24 | Issues execute in deterministic repo lanes. | Exact repos/predecessors serialize each repository; cross-repo parallelism only after prerequisites. |
| AD25 | Rollback preserves published contracts. | Disable downstream first, forward-fix published schema, version/quarantine state, and enforce dependency freezes. |
| AD26 | Canonical PV v1 is graph- and evidence-defined. | Stable site/asset/component identity, typed topology, exact leaves, SI direction/state rules, and total precedence are `ebusreg` contracts. |
| AD27 | Counter continuity is an explicit FSM. | Wrap/reset/replacement/scale/decrease decisions are evidence-gated; only extended monotonic Wh reaches statistics. |
| AD28 | Semantic promotion is scenario-gated. | FMB-03E is transport/profile proof; FMB-05F independently proves per-leaf/role canonical outputs. |
| AD29 | Observation time is gateway-authoritative. | Monotonic observation/generation drives TTL/order; device time is optional evidence only; replay/restore never refresh age. |
| AD30 | Consumer rollout freezes compatibility first. | GraphQL snapshot precedes resolvers; HA matrix precedes entities; IDs derive from canonical components/leaves. |
| AD31 | Private exports are bounded conformance. | Complete revision-pinned all-domain capability manifests precede implementation; private gaps become NO_GO/unsupported/not-yet-implemented and never request upstream semantics. |
| AD32 | Endpoint identity and address policy are separate. | Random UUID identity; one structured canonical parser; absolute deny first; exact address+port allow; generation fence and reauthorization on change. |
| AD33 | Fronius v1 transport security is explicit none. | Trusted isolated LAN only; no credentials/TLS/proxy security fields; future security requires ADR/capability/matrix and pool-key trust identity. |
| AD34 | Global resources use numeric whole-fleet atomic admission. | `resource-manifest-v1` freezes hierarchical fleet dimensions; strict profile intersection, RTU serialization, bounded persistent state and non-borrowable eBUS CPU/memory/disk are invariant-tested. |
| AD35 | Whole-process stop and Modbus-disabled are disjoint. | Hard stop is zero exec with gateway/eBUS unavailable; normal Modbus-disabled starts core/eBUS before config with zero Modbus transport/work; config uses crash-safe A/B migration. |
| AD36 | Raw tooling requires a proven authenticated boundary. | Admin adapter or restrictive Unix socket only; per-request generation/scopes; HMAC pseudonyms; chained/checkpointed audit; no unauthenticated TCP/loopback. |
| AD37 | Every operational-data class has explicit custody. | Captures, audit, metrics, crashes, support and generated evidence each bind classification, encryption/key, hard quota, retention/erasure, backup/cache/log handling, compromise response and rotatable opaque IDs. |
| AD38 | Production enablement uses a reproducible SLO. | Exact environment/seed/timeline; 5m+30m+30m+>=10m; >=300 healthy scheduled polls; nearest-rank p95; three runs all pass. |
| AD39 | Public release is reproducible, anti-replay, and crash-atomic. | FMB-03T owns independently rooted release control; 06D/08N build twice; 06H/08O validate; 06G/08Q commit active pointer and authoritative high-water together through the activation WAL. |
| AD40 | Live proof has profile and system levels plus final exact-image replay. | FMB-03E standalone runtime/profile proof; FMB-04L gateway/add-on system proof; FMB-06H reruns complete applicable gates on the candidate digest. |
| AD41 | Private release metadata never contaminates public release. | Private registries alone carry private digests/status/evidence; public surfaces expose generic schema/trust only, reveal no presence/result/timing, and remain byte/content/cardinality/timing-identical under every extension case. |
| AD42 | Rollback cannot republish retained values as current. | Disable epoch, typed unavailable/null, original observed_at, retained history only, lineage compatibility gate, and no entity deletion by rollback. |
| AD43 | Cross-repo gates have one artifact and verifier owner. | Canonical ownership matrix fixes producer, immutable schema, dependency consumers, contract test, evidence location, and rollback for every gate. |
| AD44 | Kill/config ownership is split by mode and process boundary. | FMB-03P owns supervisor hard stop and A/B config; FMB-04K owns gateway Modbus-disabled pre-config/pre-init and guarded TCP/RTU factories. |
| AD45 | Semantic authorization precedes lookup. | FMB-06E authoritative principal plus site/component scope default-denies with normalized no-existence-leak responses. |
| AD46 | Recovery has one formula. | `from fault-clear to three consecutive successful polls <= breaker_max_open + max_operation_deadline (which already includes bounded retry/backoff) + 3 * configured_poll_interval`; reports expose all numeric terms and calculated bound. |
| AD47 | Address admission is classed and versioned. | policy-v1 deny-first/default-deny table, exact admin target+port+site authorization, one pre-socket/reconnect generation, active fencing. |
| AD48 | One runtime repo owns every Modbus transport. | TCP, RTU, replay, and future transport runtime stay exclusively in `helianthus-modbus`. |
| AD49 | One registry repo owns every Modbus profile. | SunSpec, Fronius, Growatt, Huawei, and future standard/vendor packages stay exclusively in `helianthus-modbusreg`. |
| AD50 | Huawei inputs are hypotheses until an immutable decision. | Registers, predicates, sentinels, units, applicability, and budgets have provisional fact IDs/evidence/falsifiers; only matching FMB-08A GO digests generate consumers. |
| AD51 | Huawei gateway selection is fail-closed and family-specific. | Only GO-generated read-only positive fingerprints/budgets may return Matched/Ambiguous/Unknown; SmartLogger/S-Dongle selectors and topology contracts stay separate. |
| AD52 | Huawei applicability never guesses. | GO-generated family+model+firmware_branch+map_issue keys and per-field sentinels apply; unknown/revoked facts quarantine affected leaves with no nearest-map fallback. |
| AD53 | Private binding repos are generic all-domain products. | Exact generic repo names persist; FMB-05H-derived complete manifests gate supported-only implementation and enabled capabilities begin `[pv.v1]`. |
| AD54 | Restricted evidence custody is external and role-separated. | FMB-08A-CUSTODY keeps bytes in an operator vault and publishes only opaque signed attestations; custodian, clean implementer, and independent verifier cannot overlap. |
| AD55 | Huawei fact decisions are ternary and scope-specific. | FMB-08A emits GO(fact-set-digest), NO_GO, or DEFER per family/direct/downstream/RTU scope; NO_GO generates nothing and DEFER remains blocked. |
| AD56 | Canonical capabilities reconcile static declarations and runtime registration. | FMB-05H requires declaration=registration=generated unique-key equality before immutable successor catalogs; enabled is a supported-only subset and private manifests pin exact catalog digests. |
| AD57 | RTU gaps use strict RED/fix/reclosure. | FMB-08G-RED is the sole failing-digest handoff, FMB-08H requires CI-observed RED before fix, and FMB-08G-CLOSE is the sole production closure. |
| AD58 | M8 profiles must complete the public production pipeline. | Exact profile/GO digests flow through 08I/J/K/L/M/N/O/Q; machine reachability and exact-image evidence gate the successor tuple. |
| AD59 | Private attachment cannot mutate public bytes. | Zero/one/multiple canary extensions produce identical public artifacts/digests and no private canary or correlatable fingerprint. |
| AD60 | Plan intent never substitutes for live preflight. | `93` has exact executable-node intent only; installed success is green status, mode, eight row results and authorization, while details stay in cruise-state. |
| AD61 | Huawei identity is executable and independently corroborated. | GO-owned canonical predicate DAG/truth table requires two independent cleared match discriminators; routing units/readability never count and generated bytes/outcomes equal goldens. |
| AD62 | Gateway identity and downstream topology are separate. | Typed GatewayClassification and RawDownstreamObservation FSMs use atomic topology generations and exact downstream keys; only FMB-08J can create canonical topology. |
| AD63 | Discovery budgets compose across the whole endpoint attempt. | One monotonic ledger uses the strict intersection of catalog, governor, and all GO caps across families, retries, reconnects, MEI, words, and deadline. |
| AD64 | Applicability is parsed per field without guessing. | GO owns canonical firmware normalization, disjoint ranges/backports/precedence, and revocable field child facts; malformed/overlap/newer/unknown never falls back. |
| AD65 | Fact revocation is a cross-stage epoch fence. | Signed monotonic epoch/expiry is rechecked from enqueue through release; revocation cancels/drains old work and late data cannot match, refresh, republish, or cross counter lineage. |
| AD66 | Private extension trust is independently rooted and anti-replay. | Authority/key epochs, serial/predecessor/revocation chain, bounded-age control data and crash-atomic highest-seen lineage reject replay, forks, rollback, stale registry and compromised keys. |
| AD67 | Public M8 scheduling has no private dependency. | The M7 barrier is removed; absent/partitioned/running/terminal private cases yield identical public dispatch, reachability, bytes and bounded timing. |
| AD68 | Catalog completeness begins from static declarations. | Normalized `(domain, capability, major)` declaration, registration and generated sets/owners/ranges match exactly; only byte-identical explicit aliases may overlap. |
| AD69 | Public surfaces have zero private-extension fingerprint. | Presence/validity/count/registry/timing is omitted or one invariant opaque constant; detailed diagnostics stay on an authorized private control surface. |
| AD70 | Private support is feature-complete, not optimistic. | Revision-pinned per-feature matrices require every mandatory row PASS; optional/NYI gaps are unsupported, nonadvertised and force successor replay on any input revision. |
| AD71 | Public authority and signing keys are separate. | Offline-root append-only key control, serial/predecessor/validity/revocation/state range, activation-WAL committed state and one-use rollback transitions gate every public activation. |
| AD72 | Public builds are independently reproducible. | Two clean builders with pinned source/tree/locks/base/toolchain/flags/env/time/dependencies must match image/SBOM/provenance bytes and digests. |
| AD73 | Safety epochs persist before output. | Fact/counter/poll/topology/candidate/promotion state uses checksum/predecessor A/B or WAL plus durable pointer and rejects stale disk/clock/restart/late data. |
| AD74 | TCP and RTU admission bind actual routes/devices. | TCP rechecks route/interface/VRF/namespace/next hop per dial; RTU pins hardware identity, char device, permissions, exclusive open and serial config across hotplug. |
| AD75 | MCP authorization is exhaustive. | Every inventory/state/raw/capture/snapshot/export surface has principal/site/endpoint/component scopes, bounded pagination/words/rows/export/rates and normalized denial. |
| AD76 | Plan.yaml is executable topology authority. | Every issue node and explicit edge lives in `milestones`; 90/91/lanes/93 are exact rendered mirrors and the edge serialization is hashed. |
| AD77 | Planning and lock are not executable issues. | Draft curation, terminal review and authorized cruise-plan lock/meta/preflight are planning gates; FMB-00D is the sole post-lock root. |
| AD78 | New repositories require explicit readiness. | Org control-plane issues emit READY/NO_GO/DEFER with full repo policy/smoke evidence; private readiness cannot block public work. |
| AD79 | Installed gates require a versioned adapter. | The external pre-lock skill-layer gate installs and attests outcome topology, dual transport families/GENESIS_ABSENT, two docs routes and exact-HEAD fresh-review support; FMB-00D only verifies those exact installed versions after lock. |
| AD80 | Base release is RTU-independent. | M2R N/A reaches FMB-06G with guarded RTU zero-config/zero-open; selected M2R alone activates full RTU evidence. |
| AD81 | Fronius live scope is explicit. | FMB-03E0 GO enables product; NO_GO releases exact generic 02C/03D libraries and marks product N/A; DEFER blocks without fake evidence. |
| AD82 | Every expansion profile is scope-selected. | FMB-08A-SCOPE exhaustively classifies standard/vendor/family/transport/attachment; only GO enters the immutable inventory scope-selected set, while fact clearance and runtime availability derive the separate executable set before bytes can be generated. |
| AD83 | Raw Portal remains an MCP RE surface. | FMB-04D provides admin read-only grids/diff/snapshots/probes with custody/caps and no semantic bypass/write path. |
| AD84 | MCP stability gates GraphQL. | Operator-signed digest-bound MCP_STABLE FMB-05I precedes FMB-06A; later MCP changes require a successor declaration. |
| AD85 | Normative plan rows never pin models. | Issue/intent rows carry numeric complexity and risks only; model_route.py and canonical roles resolve every live route into cruise-state. |
| AD86 | External lock identity is post-commit state. | Pinned cruise-plan and cruise-state-sync jointly own predecessor-bound `external-lock-metadata-v5`; locked validation requires signed prerequisites, fresh review, explicit authorization, locked status, trusted keys, clean-clone HEAD, and every content hash. |
| AD87 | Installed preflight has one exact nested union. | Single and multi results keep `preflight` and `next_skill` at the top level; pinned cruise-dev-supervise must round-trip exact row, per-repo, batch, authorization, and dependency shapes. |
| AD88 | Outcome simulation executes semantics. | The deterministic evaluator interprets every declared predicate, action, selected branch, derived set, conditional artifact, schedule edge, state, and reachability rule and rejects order-dependent results. |
| AD89 | RED evidence unlocks implementation durably. | `tdd-unlock-v1` must exist before implementation and bind repository, issue, branch, tests-only RED commit, CI-observed-red evidence, ancestry, gate version, and signature. |
| AD90 | Empty expansion is a terminal no-op. | An empty selected expansion set makes all M8 expansion profile/closure/public-release nodes N/A with no artifacts and leaves the FMB-06G base release active. |
| AD91 | RTU scope is concrete and same-family. | Selected RTU nodes derive only from ancestor concrete RTU inventory GO rows; M2R separately gates execution. RTU baselines cannot be satisfied by PDU or another family and FMB-08O has no unconditional RTU edge. |
| AD92 | Huawei family aggregation is commutative. | Per-row facts aggregate by exact family; conflicting GO/NO_GO/DEFER is ERROR/Ambiguous with no artifact, and input order cannot change selected nodes or bytes. |
| AD93 | Uncertain writes poison the connection generation. | Any short, partial, timeout-after-write, or uncertain ADU write closes the stream, discards pending/parser state, advances generation, and permits retry only with a fresh transaction and ADU. |
| AD94 | Promoted PV MCP has one exact contract. | `modbus.v1.semantic.pv.get` is the sole promoted semantic tool; FMB-05I freezes its exact schema with raw/profile/workbench surfaces and FMB-06A proves semantic and authorization parity. |
| AD95 | Predicate threshold syntax is canonical. | `threshold` is the only threshold operator token in machine schema, generated bytes, truth tables, and positive goldens; aliases are rejected. |
| AD96 | Locked validation rejects draft state. | Pending external gates/review/authorization, false lock flags, incomplete lock gate, or absent trusted metadata cannot validate as `.locked`. |
| AD97 | Fresh review is signed data, not a URL. | Two independent OpenAI contexts and trusted signers bind zero findings, exact HEAD/content digests, validity, and non-revocation through `fresh-review-v1`. |
| AD98 | External prerequisites gate twice. | The generated canonical F4 statement exclusively governs external amendment sequencing; the declared root-architecture and installed-skill artifacts also remain unconditional FMB-00D execution inputs. |
| AD99 | Predicate references are graph edges. | Branch, conditional, derived-set, and outcome-rule node references participate in cycle and independent-ancestor validation. |
| AD100 | One evaluator owns transitions. | Rules, branch predicates, schedule, dependencies, conditional artifacts, and generic completion alone derive complete closure; direct PASS injection is forbidden. |
| AD101 | Preflight authorization signs exact GREEN rows. | Exact repo/milestone/batch/HEAD/dependency/evidence rows, multi-batch bounds, route records, and allowlisted derived next skill are envelope-bound. |
| AD102 | TDD unlock is a verified object. | Trusted signature, nonfuture CI RED, exact Git ancestry, tests-only diff, expected failure, HEAD, gate version, and OpenAI routes produce the consumed digest. |
| AD103 | This plan is OpenAI-only. | `availability_mode=openai_only`, OpenAI orchestrator, Sol/max minimum, no fallback, and fresh context separation are machine-enforced for every role. |
| AD104 | Root architecture replacement is exhaustive. | The external amendment hashes all contradictory assertions and all normalized runtime/profile/checkout/import replacements; this draft does not edit root AGENTS. |
| AD105 | Fronius registers first. | FMB-03C emits unregistered SunSpec primitives, FMB-03D first registers Fronius, and only M8 FMB-08B registers generic SunSpec. |
| AD106 | Huawei derivation is opaque and owned. | Tancabesti corpus custody/ownership and per-fact derivation lineage are opaque and mandatory; wlrcs-only evidence cannot GO and EMMA remains DEFER. |
| AD107 | Huawei attachment artifacts are exact. | Gateway and downstream rows have separate fact scopes/components; the bundle is the exact union and cannot cross-mint. |
| AD108 | Every issued transaction ID lives with its generation. | Success, timeout, cancellation, exception, and parser rejection retire the ID until fenced reconnect/generation advance; exhaustion or wrap reconnects, overflow restarts the identity epoch fail-closed, and delayed old-generation responses never match. |

## Global Acceptance And PLAN_LOCK Conditions

The v2.6 Terminal Repair 22 Draft is locally structurally acceptable only when
`validate_plan.py` reproduces byte-identical `94-validation-report.json` twice,
the normalized payload and canonical/matrix/topology/validator/report hashes
synchronize, every mirror/edge/outcome/order check passes, and initial,
AMR1-A1..A7, AMR2-A1..A5, AMR3-A1..A5, AMR4-A1..A8, AMR5-A1..A10, and
TA1-A1..A13, TA2-A1..A12, TA3-A1..A13, TA5-A1..A21, TA6B-A1..A18, and TA7-A1..A18 ledger items are verified in draft. That does not make it review-clean
or lock-ready. A fresh terminal review against this exact digest remains
required; the prior v1.0 `NO_FINDINGS` verdict is historical and superseded.

Authoritative PLAN_LOCK requires all of the following in one auditable state:

1. the three amendment attestations are cryptographically verified and nonrevoked under the generated canonical F4 sequence;
2. two trusted independent OpenAI reviewers in `fresh-review-v1` report zero findings for exact HEAD and content digests;
3. every content file is committed once and the committed directory is `.locked`;
4. post-commit cruise-state/meta-issue metadata records content commit SHA,
   canonical/matrix/topology/validator/report/payload hashes, signed prerequisites,
   review attestation, explicit operator authorization, route digest, completed
   lock gates, and locked status;
5. `validate_plan.py` and the repository validator pass from a clean clone against
   that external metadata pointer and local trusted-key registry; and
6. installed preflight returns one exact accepted single/multi serialization.

The locked content never embeds its own commit SHA or signed fresh-review attestation. Those values
exist only in `external-lock-metadata-v5`; no second self-referential content
commit is required.

M1 cannot start before PLAN_LOCK. A local rename, local validator run, clean
working tree, or terminal NO_FINDINGS alone is never a lock.

## Public Reference Anchors

- Fronius Modbus TCP open interface:
  `https://www.fronius.com/en-us/usa/solar-energy/installers-partners/technical-data/all-products/system-monitoring/open-interfaces/modbus-tcp`
- Fronius GEN24 Modbus TCP/RTU instructions:
  `https://manuals.fronius.com/html/4204102649/en-US.html`
- SunSpec Modbus overview: `https://sunspec.org/modbus/`
- SunSpec specifications: `https://sunspec.org/specifications/`
## Normative Lock And Execution Contracts

The final lock uses `final-lock-object-v4` with distinct package roots and an
exact draft/locked normalized payload digest pair. From the
exact draft parent containing every declared `.draft/<file>`, the installed
operator constructs one unreferenced commit that deletes that exact 14-file set
and adds the exact `.locked/<file>` set. Immutable files are byte-identical;
only declared state/status/report/attestation files may change. Fresh review, operator authorization, the signed
post-provision identity map, and the actual signed preflight envelope bind that
exact commit and tree. Only then may `PG-CRUISE-LOCK` complete and one atomic
compare-and-swap advance the exact intended ref from the draft parent to the
reviewed object. Pre-CAS validation requires ref and HEAD still at the draft
parent and the final object unreferenced. Post-CAS validation requires a signed
receipt bound to metadata, old/new object, tree, ref, time, and successful
result, then exact ref/HEAD equality. Wrong parent, tree, delete/add set, mixed
root, path transition, ref, metadata predecessor, intervening commit, receipt,
or post-advance HEAD is a hard failure.

Locked validation hashes the supplied authoritative root `AGENTS.md` and every
installed skill byte at explicit operator paths. The root must contain the
normalized single-runtime/single-registry import and ownership assertions and
checkout mappings for `helianthus-modbus`, `helianthus-modbusreg`,
`helianthus-eebus-binding-private`, `helianthus-matter-binding-private`, and
`helianthus-execution-plans`; it must contain no separate `helianthus-sunspec`
repository assertion. Every required cruise component, including the actual RED
diff/CI-aware TDD adapter amendment, has pinned source, version, installed hash,
and three stored immutable clean-start/resume/compatibility result artifacts.
Each result binds canonical/topology, source/skill bytes, command/schema,
environment, semantic contracts, PASS, and execution time; a test-shaped digest
without the stored result is invalid.

The package manifest is recursively exact: the fourteen declared regular files
are the entire package. Undeclared files or directories, symlinks, hardlinks,
unsupported types, `edges.yaml`, and `__pycache__` are forbidden. Validation
runs with bytecode generation disabled.

Live preflight identity is never self-described. Machine `next_ready`, the
signed issue-number/branch map, final object ID, exact dependency closure,
milestone acceptance criteria, provisioned repository identity, and batch policy
derive the accepted target. All eight rows are GREEN, fresh, signed, and bound
to those values. `next_skill` remains derived and allowlisted.

`tdd-unlock-v1` binds actual RED diff bytes and Git-derived paths, base/RED/head
ancestry, first implementation parent, issue/branch, issuance/expiry, exact
tests-only policy, and CI provider/run/check/workflow/job/log/result identity.
A path merely containing `test`, such as `contest/runtime.go`, is not a test
path. No implementation commit may precede the durable unlock.

All 81 milestones execute through the single fixed-point engine. Scenario
execution outcomes are explicit external inputs and can transition a node only
after the engine derives READY; no input assigns node state directly. Rules require their declared source state or artifact; exact
schedule overrides, predicates, conditional artifacts, legal state transitions,
and every node/artifact are included in the topology digest. Checked-in
declarative oracle closures are independent inputs and are never generated by
the validator during validation. `READY` is derived only: selected plus all
required dependencies, artifacts, and schedule policies satisfied. Terminal
outcomes are milestone-declared and disjoint from derived states.

Each milestone carries a specific machine What and architecture Why, five
nonempty testable acceptance criteria including issue behavior, unit tests, CI,
and explicit smoke YES/NO, exact dependencies, a rendered AGENTS-template issue
body and body digest, an exact issue branch template, and a signed provisioning
identity requirement. The signed post-provision map and typed provider evidence
own exact Project-Helianthus GitHub owner/repo/URL/number/body/branch/final-object
binding; this plan creates no issue.

Every route record uses a runtime-owned Ed25519 key whose private bytes never
enter this package. It includes exact resolver argv and normalized output, selected
profile, complexity, risks, task kind, vendor/model/effort, freshness,
availability/session/fallback, invocation/context lineage, and exact routing
policy/resolver digests. Required fresh roles use distinct public-key identities. The
local resolver and policy bytes are rehashed and normalized output is compared
where available; locked validation requires platform invocation evidence.

Huawei execution consumes a supplied signed opaque custody/fact artifact with
exactly eight scopes: SmartLogger gateway/downstream, S-Dongle
gateway/downstream, EMMA direct/downstream, and relevant RTU direct/downstream.
Operator, custodian, and verifier are distinct; revocation is monotonic and
nonnegative; facts have unique IDs, scope affinity, attachment and source-chain
lineage. GO needs two independent non-wlrcs sufficient chains. EMMA remains
DEFER until its own evidence gate. Restricted content remains absent.

Neutral SunSpec and Growatt inventory, scope, closure, and release consume no
Huawei custody or fact artifact. Huawei nonavailability, NO_GO, or fact DEFER
terminalizes only Huawei consumers; selected neutral profiles can still reach
the successor public release.

Every issued Modbus/TCP transaction ID, including a successfully completed ID,
is retired for the full connection-generation lifetime. Wrap, allocator
exhaustion, or proposed reuse fences and closes the connection before a new
generation. Generation-counter overflow fails closed and restarts the connection
identity epoch without alias. Delayed duplicates and old-generation responses
never match.

`modbus-pdu-v1` carries a digest-bearing resource contract: PDU maximum 253
bytes, TCP ADU maximum 260, FC01/02 quantity 1..2000, FC03/04 quantity 1..125,
no address-plus-quantity overflow beyond 65535, exact response byte counts, TCP
parser cap 260, RTU frame maximum 256, RTU unicast 1..247 with address 0
write-only and never discovery/read, and exact t1.5/t3.5 handling. Conservative
runtime caps are 256 configured endpoints, 64 active endpoints, 2048 global and
32 per-endpoint queued requests, 64 global and one per-endpoint in flight, and
eight serial handles.

FMB-05C emits both `canonical-pv-schema-v1` and digest-bearing
`canonical-domain-schema-declarations-v1`. FMB-05H directly consumes the latter
and requires exact equality of static declarations, runtime registrations, and
generated catalog; omission of an entire domain fails. FMB-08I owns successor
candidates, FMB-08N separately owns the successor image, and machine/prose owner
and edge assertions must agree.

Machine edge assertions: `FMB-05C -> FMB-05H` consumes
`canonical-domain-schema-declarations-v1`; `FMB-08A-INVENTORY` depends only on
`FMB-05B` and has no cross-branch schedule edge. Machine owner assertions:
`successor_candidate_owner=FMB-08I` and `successor_image_owner=FMB-08N`.

## Machine Operator Registry v4

<!-- MACHINE_OPERATOR_REGISTRY_BEGIN -->
Predicate operators: `["always","all","any","not","outcome_is","artifact_field_is","node_set_nonempty","selected_set_empty","inventory_row_outcome_is","verified_artifact_digest_present"]`
Action operators: `["set_node_state","set_node_set_state","emit_artifact","emit_fresh_genesis","enable_conditional_consumer","record_no_artifact","record_inventory_fact","aggregate_profile_families","derive_rtu_selection","record_node_set_artifacts_absent"]`
<!-- MACHINE_OPERATOR_REGISTRY_END -->

## Terminal Repairs 6 And 7 Executable Contracts

1. `final-lock-object-v4` binds distinct draft and locked normalized payload
   digests and `normalized-lock-transform-manifest-v1`. Review, authorization,
   preflight, prerequisite attestations, and pre-CAS metadata bind the pair,
   parent, unreferenced tree/commit, and transform. A detached temporary checkout
   runs complete strict candidate and external-authority validation before CAS;
   post-CAS repeats it with the state-sync receipt and unchanged tree.
2. Live expansion accepts only a signed ten-row `profile-scope-decision-v1`
   from FMB-08A-SCOPE. It derives digest-bearing scope-selected, fact-cleared,
   executable, and RTU sets together with the validated fact result; caller
   `inventory_outcomes` and independent fact-authority references are forbidden.
3. Huawei validation aggregates independent observations before scope projection
   and returns packet/policy/genesis digests, monotonic epoch, exact commitments,
   and eight outcomes including AMBIGUOUS. An authenticated replay chain rejects
   reset, rollback, lineage change, or A-B-A use.
4. The installed resolver is executed from canonical argv reconstructed from
   issue complexity, risks, task kind, and role. The current gate route resolves
   below Sol/max, so PG-MODEL-ROUTING-POLICY-AMENDMENT is a pending external
   lock prerequisite; this package does not edit policy or fabricate approval.
5. TDD unlock verification returns the only consumable digest/object and commits
   an authenticated append-only consumed-digest set and predecessor chain before
   the first non-test parent. Target HEAD is the tests-only RED commit; bypass,
   A-B-A replay, rollback, or preexisting implementation fails.
6. Provisioning uses one signed v2 schema. Exact repo rows and provider-evidence
   digests derive the singular aggregate; unsigned maps or partial rows cannot
   enable a bootstrap.
7. Skill compatibility uses fixed per-component schemas. The validator executes
   built-in semantic fixtures for all 11 components and eight clean/restart
   phases, including cruise-resume; arbitrary or stored PASS is never accepted.
8. Root authority validation parses normalized architecture and checkout
   semantics, hashes both sections, and rejects every contradiction class even
   when reworded. Current root AGENTS remains an external lock blocker.
9. CAS receipts are signed only by `cruise-state-sync` and bind a fresh ordered
   compare-and-swap invocation, ref, old/new object, result, and evidence digest.
10. FMB-05A canonically produces `canonical-runtime-registrations-v1`; all 14
    former supplemental consumptions are typed milestone edges participating in
    readiness, topology, preflight, issues, gates, metrics, and mirrors.
11. The catalog encodes lifecycle, legal transitions, eligibility, dependencies,
    predecessors/successors, four canonical keys, all 12 features, and exact
    eeBUS/Matter matrices. Only `pv.v1` is initially enabled.
12. `authoritative-activation-record-v1` atomically binds package, migration,
    pointer, and high-water in one fsynced record. Secondary state is idempotently
    derived; every exact operation boundary has old/new crash recovery evidence.
13. Transport intent is a per-issue typed `{family, when}` list dispatched by a
    closed six-condition function from signed context. Every condition and issue
    has true/false coverage; unknown conditions fail.
14. Every issue body embeds an exact derived machine contract with anchors,
    invariants/tests, serialized condition ASTs, schedule outcomes, artifacts,
    failure, and rollback. FMB-03T names every activation operation; private
    predecessor predicates are exclusive and exhaustive.
15. MC/DC pairs bind the hashed actual selector AST. Every mutant is applied to
    an isolated plan copy and must fail targeted validation; unchanged mutations
    fail with `NO_MUTATION_APPLIED`.
16. Asymmetric preflight v3 receipts bind role-specific provider/public key,
    exact argv and input, exit/stdout/stderr/output digests, freshness, target,
    and dependency closure. Validator subprocess and independent replay must agree.
17. The generated canonical F3 statement is the sole authority for the M8 branch
    relationship. Neutral rows never carry a Huawei digest; Huawei digest/epoch
    enters only Huawei fact-cleared and executable derivation.
18. WRITE/ZERO is distinct and may back off only with transport proof of zero
    stream bytes, empty parser/pending state, clear cancellation, and budget.
    Partial/timeout/uncertain writes always close/fence, discard state, advance
    generation, and retry only fresh with a new TID and complete ADU.



## Neutral And Huawei Parallel Graph


<!-- GENERATED_TA15_MODEL_BEGIN -->
Plan identity: `{"revision":"v2.6-draft-terminal-repair-22","title":"Modbus Runtime, Multi-Vendor Registry, And Generic Private Protocol Bindings - v2.6 Terminal Repair 22 Draft"}`
Planning gate model: `{"PG-ARCHITECTURE-MAP-AMENDMENT":{"acceptance_artifact":"authoritative-architecture-map-amendment-v1","depends_on":["PG-DRAFT-CURATION"]},"PG-CRUISE-LOCK":{"acceptance_artifact":"post-cas-lock-validation-v1","depends_on":["PG-FRESH-TERMINAL-REVIEW"]},"PG-DRAFT-CURATION":{"acceptance_artifact":"94-validation-report.json-PASS-for-normalized-payload","depends_on":[]},"PG-FRESH-TERMINAL-REVIEW":{"acceptance_artifact":"fresh-terminal-review-verdict-for-exact-canonical-digest","depends_on":["PG-SKILL-ADAPTER-REGISTRY"]},"PG-MODEL-ROUTING-POLICY-AMENDMENT":{"acceptance_artifact":"model-routing-policy-amendment-v1","depends_on":["PG-ARCHITECTURE-MAP-AMENDMENT"]},"PG-SKILL-ADAPTER-REGISTRY":{"acceptance_artifact":"skill-adapter-registry-v1-installed-runtime-attestation","depends_on":["PG-MODEL-ROUTING-POLICY-AMENDMENT"]}}`
External prerequisite count: `3`
External prerequisite IDs: `["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY"]`
Ordered lock gate chain: `["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY","PG-FRESH-TERMINAL-REVIEW","PG-CRUISE-LOCK"]`
Lock gate prose: `PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY -> PG-FRESH-TERMINAL-REVIEW -> PG-CRUISE-LOCK.`
External lock metadata fields: `["schema","metadata_version","metadata_predecessor_digest_or_genesis","final_lock_object","canonical_sha256","matrix_sha256","topology_sha256","validator_sha256","validation_report_sha256","validation_payload_sha256","draft_payload_sha256","locked_payload_sha256","lock_transform_manifest_sha256","skill_adapter_attestation","architecture_map_attestation","model_routing_policy_attestation","fresh_review_attestation","operator_authorization","signed_preflight_envelope","post_provision_issue_map","pre_cas_gate_states","pre_cas_status","route_records_sha256"]`
Installed preflight success schema: `{"multi":{"batch_item_exact_fields":["repo","milestone","issue","issue_number","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","complexity","risk_classes","pre_execution_intent_sha256","acceptance_criteria","workflow_semantic_result_sha256","semantic_results_sha256","evidence_set_sha256","rows_sha256"],"batch_type":"list","mode":"multi","per_repo_item_exact_fields":["repo","milestone","issue","issue_number","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","pre_execution_intent_sha256","risk_classes","workflow_semantic_result_sha256","semantic_results_sha256","evidence_set_sha256","rows_sha256","rows"],"per_repo_row_fields":["routing","workflow","doc_gate","review","deps","transport_gate","smoke","tdd"],"per_repo_type":"list","preflight_exact_fields":["status","mode","batch_id","per_repo","batch","max_parallel","cross_repo_deps","authorization"],"row_result_exact_fields":["status","repo","milestone","issue","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","provider_query_id","semantic_result_sha256","evidence_artifact_type","evidence_artifact_path","evidence_artifact_sha256"],"top_level_exact_fields":["preflight","next_skill"]},"single":{"mode":"single","preflight_exact_fields":["status","mode","rows","authorization"],"row_fields":["routing","workflow","doc_gate","review","deps","transport_gate","smoke","tdd"],"row_result_exact_fields":["status","repo","milestone","issue","branch","batch_id","target_object_id","target_repo_head_sha","dependency_closure_sha256","provider_query_id","semantic_result_sha256","evidence_artifact_type","evidence_artifact_path","evidence_artifact_sha256"],"top_level_exact_fields":["preflight","next_skill"]}}`
Machine metrics: `{"canonical_gates":45,"conditional_artifact_edges":69,"cross_repo_artifact_edges":178,"depends_on_edges":216,"executable_issues":81,"lane_schedule_edges":67,"promoted_typed_artifact_edges":14,"schedule_edges":68,"serialized_repo_lanes":12}`
Model route mismatches: `{"matrix":{"adversary":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"planner_adversary"},"developer":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"developer_critical"},"gate":{"mismatch":true,"resolved_effort":"medium","resolved_model":"gpt-5.6-luna","resolved_profile":"semantic_gate"},"planner":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"planner_primary"},"reviewer-primary":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"reviewer_max"},"reviewer-secondary":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"reviewer_max"},"tester":{"mismatch":false,"resolved_effort":"max","resolved_model":"gpt-5.6-sol","resolved_profile":"adversarial_tester_critical"}},"mismatched_roles":["gate"]}`
Executable repository order: `{"helianthus-docs-ebus":["FMB-01A","FMB-05D","FMB-05J"],"helianthus-docs-modbus":["FMB-00F-DOCS","FMB-01B","FMB-01C","FMB-01D","FMB-01E","FMB-05B","FMB-08A-CUSTODY","FMB-08A","FMB-08A-INVENTORY","FMB-08A-SCOPE"],"helianthus-ebusgateway":["FMB-03R","FMB-04K","FMB-04A","FMB-04S","FMB-04B","FMB-04D","FMB-04C","FMB-04L","FMB-04O","FMB-05A","FMB-05F","FMB-05E","FMB-05I","FMB-06A","FMB-06E","FMB-06B","FMB-08I","FMB-08J","FMB-08K","FMB-08L"],"helianthus-ebusreg":["FMB-05R","FMB-05C","FMB-05G","FMB-05H"],"helianthus-eebus-binding-private":["FMB-00F-EEBUS","FMB-07A","FMB-07B","FMB-08EEBUS-A","FMB-08EEBUS"],"helianthus-execution-plans":["FMB-00D"],"helianthus-ha-addon":["FMB-03T","FMB-03P","FMB-06D","FMB-06H","FMB-06G","FMB-08N","FMB-08O","FMB-08Q"],"helianthus-ha-integration":["FMB-06F","FMB-06C","FMB-08M"],"helianthus-matter-binding-private":["FMB-00F-MATTER","FMB-09A","FMB-09B"],"helianthus-modbus":["FMB-00F-MODBUS","FMB-02A","FMB-02B","FMB-02C","FMB-02R-A","FMB-08H"],"helianthus-modbusreg":["FMB-00F-MODBUSREG","FMB-03A","FMB-03B","FMB-03C","FMB-03D","FMB-03E0","FMB-03E","FMB-08B","FMB-08C","FMB-08D","FMB-08E","FMB-08F","FMB-08F-SD","FMB-08G-RED","FMB-08G-CLOSE"],"helianthus-org-github":["FMB-00E-PUBLIC","FMB-00E-EEBUS","FMB-00E-MATTER"]}`
Explicit lane edges: `[{"repo":"helianthus-org-github","source":"FMB-00E-PUBLIC","target":"FMB-00E-EEBUS"},{"repo":"helianthus-org-github","source":"FMB-00E-EEBUS","target":"FMB-00E-MATTER"},{"repo":"helianthus-docs-modbus","source":"FMB-00F-DOCS","target":"FMB-01B"},{"repo":"helianthus-docs-modbus","source":"FMB-01B","target":"FMB-01C"},{"repo":"helianthus-docs-modbus","source":"FMB-01C","target":"FMB-01D"},{"repo":"helianthus-docs-modbus","source":"FMB-01D","target":"FMB-01E"},{"repo":"helianthus-docs-modbus","source":"FMB-01E","target":"FMB-05B"},{"repo":"helianthus-docs-modbus","source":"FMB-05B","target":"FMB-08A-CUSTODY"},{"repo":"helianthus-docs-modbus","source":"FMB-08A-CUSTODY","target":"FMB-08A"},{"repo":"helianthus-docs-modbus","source":"FMB-08A-INVENTORY","target":"FMB-08A-SCOPE"},{"repo":"helianthus-modbus","source":"FMB-00F-MODBUS","target":"FMB-02A"},{"repo":"helianthus-modbus","source":"FMB-02A","target":"FMB-02B"},{"repo":"helianthus-modbus","source":"FMB-02B","target":"FMB-02C"},{"repo":"helianthus-modbus","source":"FMB-02C","target":"FMB-02R-A"},{"repo":"helianthus-modbus","source":"FMB-02R-A","target":"FMB-08H"},{"repo":"helianthus-modbusreg","source":"FMB-00F-MODBUSREG","target":"FMB-03A"},{"repo":"helianthus-modbusreg","source":"FMB-03A","target":"FMB-03B"},{"repo":"helianthus-modbusreg","source":"FMB-03B","target":"FMB-03C"},{"repo":"helianthus-modbusreg","source":"FMB-03C","target":"FMB-03D"},{"repo":"helianthus-modbusreg","source":"FMB-03D","target":"FMB-03E0"},{"repo":"helianthus-modbusreg","source":"FMB-03E0","target":"FMB-03E"},{"repo":"helianthus-modbusreg","source":"FMB-08B","target":"FMB-08C"},{"repo":"helianthus-modbusreg","source":"FMB-08C","target":"FMB-08D"},{"repo":"helianthus-modbusreg","source":"FMB-08D","target":"FMB-08E"},{"repo":"helianthus-modbusreg","source":"FMB-08E","target":"FMB-08F"},{"repo":"helianthus-modbusreg","source":"FMB-08F","target":"FMB-08F-SD"},{"repo":"helianthus-modbusreg","source":"FMB-08F-SD","target":"FMB-08G-RED"},{"repo":"helianthus-modbusreg","source":"FMB-08G-RED","target":"FMB-08G-CLOSE"},{"repo":"helianthus-eebus-binding-private","source":"FMB-00F-EEBUS","target":"FMB-07A"},{"repo":"helianthus-eebus-binding-private","source":"FMB-07A","target":"FMB-07B"},{"repo":"helianthus-eebus-binding-private","source":"FMB-07B","target":"FMB-08EEBUS-A"},{"repo":"helianthus-eebus-binding-private","source":"FMB-08EEBUS-A","target":"FMB-08EEBUS"},{"repo":"helianthus-matter-binding-private","source":"FMB-00F-MATTER","target":"FMB-09A"},{"repo":"helianthus-matter-binding-private","source":"FMB-09A","target":"FMB-09B"},{"repo":"helianthus-docs-ebus","source":"FMB-01A","target":"FMB-05D"},{"repo":"helianthus-docs-ebus","source":"FMB-05D","target":"FMB-05J"},{"repo":"helianthus-ha-addon","source":"FMB-03T","target":"FMB-03P"},{"repo":"helianthus-ha-addon","source":"FMB-03P","target":"FMB-06D"},{"repo":"helianthus-ha-addon","source":"FMB-06D","target":"FMB-06H"},{"repo":"helianthus-ha-addon","source":"FMB-06H","target":"FMB-06G"},{"repo":"helianthus-ha-addon","source":"FMB-06G","target":"FMB-08N"},{"repo":"helianthus-ha-addon","source":"FMB-08N","target":"FMB-08O"},{"repo":"helianthus-ha-addon","source":"FMB-08O","target":"FMB-08Q"},{"repo":"helianthus-ebusgateway","source":"FMB-03R","target":"FMB-04K"},{"repo":"helianthus-ebusgateway","source":"FMB-04K","target":"FMB-04A"},{"repo":"helianthus-ebusgateway","source":"FMB-04A","target":"FMB-04S"},{"repo":"helianthus-ebusgateway","source":"FMB-04S","target":"FMB-04B"},{"repo":"helianthus-ebusgateway","source":"FMB-04B","target":"FMB-04D"},{"repo":"helianthus-ebusgateway","source":"FMB-04D","target":"FMB-04C"},{"repo":"helianthus-ebusgateway","source":"FMB-04C","target":"FMB-04L"},{"repo":"helianthus-ebusgateway","source":"FMB-04L","target":"FMB-04O"},{"repo":"helianthus-ebusgateway","source":"FMB-04O","target":"FMB-05A"},{"repo":"helianthus-ebusgateway","source":"FMB-05A","target":"FMB-05F"},{"repo":"helianthus-ebusgateway","source":"FMB-05F","target":"FMB-05E"},{"repo":"helianthus-ebusgateway","source":"FMB-05E","target":"FMB-05I"},{"repo":"helianthus-ebusgateway","source":"FMB-05I","target":"FMB-06A"},{"repo":"helianthus-ebusgateway","source":"FMB-06A","target":"FMB-06E"},{"repo":"helianthus-ebusgateway","source":"FMB-06E","target":"FMB-06B"},{"repo":"helianthus-ebusgateway","source":"FMB-06B","target":"FMB-08I"},{"repo":"helianthus-ebusgateway","source":"FMB-08I","target":"FMB-08J"},{"repo":"helianthus-ebusgateway","source":"FMB-08J","target":"FMB-08K"},{"repo":"helianthus-ebusgateway","source":"FMB-08K","target":"FMB-08L"},{"repo":"helianthus-ebusreg","source":"FMB-05R","target":"FMB-05C"},{"repo":"helianthus-ebusreg","source":"FMB-05C","target":"FMB-05G"},{"repo":"helianthus-ebusreg","source":"FMB-05G","target":"FMB-05H"},{"repo":"helianthus-ha-integration","source":"FMB-06F","target":"FMB-06C"},{"repo":"helianthus-ha-integration","source":"FMB-06C","target":"FMB-08M"}]`
Artifact/schedule relationship: `After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.`
Private manifest inputs: `{"FMB-07A":["FMB-05C","FMB-05E","FMB-05H","FMB-06A","FMB-05J","FMB-00F-EEBUS"],"FMB-08EEBUS-A":["FMB-05H","FMB-08K","FMB-08L","FMB-07A","FMB-05J"],"FMB-09A":["FMB-08Q","FMB-08K","FMB-08L","FMB-05H","FMB-05J","FMB-00F-MATTER"],"forbidden_artifact_sources":["FMB-08A-SCOPE","FMB-07B"],"lineage_choice_owner":"FMB-08EEBUS","schedule_only_predecessor":"FMB-07B","signed_manifest_source":"FMB-07A"}`
eeBUS successor lineage: `{"canonical_prose":"FMB-08EEBUS-A consumes the signed FMB-07A manifest with full producer identity. FMB-07B supplies schedule ordering only and no artifact to FMB-08EEBUS-A. FMB-08EEBUS owns the exclusive validated producer-envelope choice: the FMB-07B extension on PASS or a separately signed fresh-genesis envelope otherwise.","choice":{"manifest_issue":"FMB-08EEBUS-A","manifest_source_issue":"FMB-07A","owner_issue":"FMB-08EEBUS","producer_envelopes":[{"artifact":"eebus-base-extension-v1","artifact_schema":"helianthus-immutable-artifact-envelope-v1","artifact_version":1,"condition_ast":{"node":"FMB-07B","op":"outcome_is","outcome":"PASS"},"content_digest_field":"content_digest_sha256","edge_kind":"lineage_choice","evidence_schema":"signed-consumed-artifact-evidence-v1","generation_rule":"topology-resolves-source-contract-then-queries-and-signs-producer-HEAD-tree-and-content;consumer-caller-fields-forbidden","producer_authority_id":"helianthus-eebus-binding-private:FMB-07B:artifact-authority-v1","producer_head_field":"producer_head_oid","producer_issue":"FMB-07B","producer_repo":"helianthus-eebus-binding-private","producer_signer_id":"helianthus-eebus-binding-private:FMB-07B:release-signer-v1","producer_tree_field":"producer_tree_oid","source":"FMB-07B","source_contract_sha256":"46ac3f95efcc3d7a6fae65833021dfdefc6f32dcdbd95ae8f4ec7c873daae2d4","verifier_signer_id":"preflight-deps"},{"artifact":"eebus-fresh-genesis-v1","artifact_schema":"helianthus-immutable-artifact-envelope-v1","artifact_version":1,"condition_ast":{"args":[{"node":"FMB-07B","op":"outcome_is","outcome":"NO_GO"},{"node":"FMB-07B","op":"outcome_is","outcome":"PRIVATE_UNAVAILABLE"},{"node":"FMB-07B","op":"outcome_is","outcome":"N/A"}],"op":"any"},"content_digest_field":"content_digest_sha256","edge_kind":"lineage_choice","evidence_schema":"signed-consumed-artifact-evidence-v1","generation_rule":"topology-resolves-source-contract-then-queries-and-signs-producer-HEAD-tree-and-content;consumer-caller-fields-forbidden","producer_authority_id":"helianthus-eebus-binding-private:EEBUS-FRESH-GENESIS-AUTHORITY-V1:artifact-authority-v1","producer_head_field":"producer_head_oid","producer_issue":"EEBUS-FRESH-GENESIS-AUTHORITY-V1","producer_repo":"helianthus-eebus-binding-private","producer_signer_id":"helianthus-eebus-binding-private:EEBUS-FRESH-GENESIS-AUTHORITY-V1:release-signer-v1","producer_tree_field":"producer_tree_oid","source":"EEBUS-FRESH-GENESIS-AUTHORITY-V1","source_contract_sha256":"2904b07ee980a834c1568aeca5bcba22b559df3e2628ffd5c696f11737e8230d","verifier_signer_id":"preflight-deps"}],"schedule_only_issue":"FMB-07B","schema":"eebus-successor-lineage-choice-v1","selection":"exactly-one-validated-producer-envelope"},"lineage_choice_owner":"FMB-08EEBUS","schedule_only_issue":"FMB-07B","schema":"eebus-successor-lineage-v1","signed_manifest_artifact":"eebus-base-feature-manifest-v1","signed_manifest_source":"FMB-07A","successor_manifest_issue":"FMB-08EEBUS-A"}`
eeBUS lineage prose: `FMB-08EEBUS-A consumes the signed FMB-07A manifest with full producer identity. FMB-07B supplies schedule ordering only and no artifact to FMB-08EEBUS-A. FMB-08EEBUS owns the exclusive validated producer-envelope choice: the FMB-07B extension on PASS or a separately signed fresh-genesis envelope otherwise.`
Terminal Repair 12b state: `{"audit_id":"Audit 12","finding_ids":["AUDIT12-HIGH-D3","AUDIT12-MEDIUM-ROADMAP","AUDIT12-LOW-REVIEW-STATE"],"repair_id":"Terminal Repair 12b","state":"repaired_in_draft_external_prelock_gates_pending"}`
eeBUS executable producer fixtures: `{"base_fixture_binding":{"base_fixture_id":"FMB-08EEBUS-ACCEPT-EEBUS-SUCCESSOR-EXTENSION-V1","base_fixture_input_sha256":"bb72836f728c71b90ff606727e2ecbd7a5da24a2acff86ee737d3a98e2066a61","base_fixture_oracle_sha256":"0bf1204d81c13e766d85f55bd40a80e5fb506e6d026a3e8b8f3600dcfc1cddc2","base_fixture_output_sha256":"61715207332d72ea125cc405f6998ccefa54013e71cfa0970aa78cf72a362f25","machine_contract_sha256":"90fafa33ec120a9daa86b800e9e557ff90a3d61f38221c56c6577074fcecc95f","owner_issue":"FMB-08EEBUS","schema":"fmb-08eebus-base-fixture-binding-v1","test_ids_sha256":"31877ed1e12347daaa52b6ad39367ea2107028dcbe014faf32ced3dcd4b862d4"},"base_fixture_id":"FMB-08EEBUS-ACCEPT-EEBUS-SUCCESSOR-EXTENSION-V1","composition_mutation_classes":["base-fixture-omission","base-fixture-drift","base-test-id-omission"],"composition_schema":"fmb-08eebus-executable-fixture-composition-v1","covered_predecessor_outcomes":["PASS","NO_GO","PRIVATE_UNAVAILABLE","N/A"],"fixture_ids":["FMB-08EEBUS-SELECT-PASS","FMB-08EEBUS-SELECT-NO-GO","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE","FMB-08EEBUS-SELECT-N-A"],"fixture_set_sha256":"cac4f65dbfb16d3c8726d885560bbab93c10e8f31fd5662f442162fd024f1bbb","mutation_classes":["zero-selected","both-selected","wrong-producer","wrong-condition","stale-identity","envelope-omission"],"owner_issue":"FMB-08EEBUS","report_check_id":"terminal_repair_12b_eebus_selected_producer_fixture_execution","report_field":"executed_fixture_sets","schema":"fmb-08eebus-selected-producer-envelope-execution-v1"}`
Indexed roadmap chunk declarations: `{"chunk_index":13,"declaration_order":["scope","idempotence","falsifiability","coverage"],"declarations":{"coverage":"Covers M0A through M9, all 81 executable issues, planning and pre-lock gates, repository lanes, artifact and schedule edges, rollback, risks, current-round repair status, generated mirrors, report checks, and lock blockers.","falsifiability":"Validation fails if any declaration is missing, duplicated, reordered, not byte-equal to plan.yaml, detached from the index entry, or claims review-clean, lock-ready, or PLAN_LOCK while the package remains DRAFT.","idempotence":"Regeneration from the same plan.yaml renders byte-identical declarations and preserves artifact ordering independently from schedule ordering; reruns add no issue, edge, gate, or state transition.","scope":"Defines the plan.yaml-derived milestone roadmap, issue and lane ordering, planning gates, rollback boundaries, risk register, current DRAFT status, and generated execution mirrors."},"file":"13-roadmap-issues-risks.md"}`
Audit 12 current round: `{"audit_id":"Audit 12","finding_ids":["AUDIT12-HIGH-D3","AUDIT12-MEDIUM-ROADMAP","AUDIT12-LOW-REVIEW-STATE"],"header_values":{"authoritative_plan_lock":"not achieved","current_revision":"v1.6-draft-terminal-repair-12b","current_round":"Terminal Repair 12b / Audit 12 targeted findings repaired in draft; external pre-lock gates and fresh terminal review pending","lock_ready":"false","plan_state":".draft","review_clean":"false"},"repair_id":"Terminal Repair 12b","state":"repaired_in_draft_external_prelock_gates_pending"}`
Terminal Repair 13 state: `{"finding_ids":["E1","E2","E3","E4","E5","E6","E7"],"header_values":{"authoritative_plan_lock":"not achieved","current_revision":"v1.7-draft-terminal-repair-13","current_round":"Terminal Repair 13 requirements E1-E7 repaired in draft; external pre-lock gates and fresh terminal review pending","lock_ready":"false","plan_state":".draft","review_clean":"false"},"repair_id":"Terminal Repair 13","state":"repaired_in_draft_external_prelock_gates_pending"}`
Terminal Repair 13 mutation coverage: `{"expected_mutation_ids":["FMB-08EEBUS-SELECT-PASS::zero-selected","FMB-08EEBUS-SELECT-PASS::both-selected","FMB-08EEBUS-SELECT-PASS::wrong-producer","FMB-08EEBUS-SELECT-PASS::wrong-condition","FMB-08EEBUS-SELECT-PASS::stale-identity","FMB-08EEBUS-SELECT-PASS::envelope-omission","FMB-08EEBUS-SELECT-NO-GO::zero-selected","FMB-08EEBUS-SELECT-NO-GO::both-selected","FMB-08EEBUS-SELECT-NO-GO::wrong-producer","FMB-08EEBUS-SELECT-NO-GO::wrong-condition","FMB-08EEBUS-SELECT-NO-GO::stale-identity","FMB-08EEBUS-SELECT-NO-GO::envelope-omission","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::zero-selected","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::both-selected","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::wrong-producer","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::wrong-condition","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::stale-identity","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE::envelope-omission","FMB-08EEBUS-SELECT-N-A::zero-selected","FMB-08EEBUS-SELECT-N-A::both-selected","FMB-08EEBUS-SELECT-N-A::wrong-producer","FMB-08EEBUS-SELECT-N-A::wrong-condition","FMB-08EEBUS-SELECT-N-A::stale-identity","FMB-08EEBUS-SELECT-N-A::envelope-omission"],"expected_receipt_count":24,"fixture_classes":["extension","fresh-genesis"],"fixture_classes_by_id":{"FMB-08EEBUS-SELECT-N-A":"fresh-genesis","FMB-08EEBUS-SELECT-NO-GO":"fresh-genesis","FMB-08EEBUS-SELECT-PASS":"extension","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE":"fresh-genesis"},"fixture_ids":["FMB-08EEBUS-SELECT-PASS","FMB-08EEBUS-SELECT-NO-GO","FMB-08EEBUS-SELECT-PRIVATE-UNAVAILABLE","FMB-08EEBUS-SELECT-N-A"],"mutation_classes":["zero-selected","both-selected","wrong-producer","wrong-condition","stale-identity","envelope-omission"],"negative_receipt_mutations":["missing","duplicate"],"receipt_schema":"fmb-08eebus-producer-mutation-execution-receipt-v1","report_check_id":"terminal_repair_13_eebus_genesis_mutation_coverage","report_field":"executed_fixture_sets","schema":"fmb-08eebus-two-branch-mutation-coverage-v1"}`
Terminal Repair 13 manual preflight schema: `{"manual_files":["00-canonical.md","10-boundaries-and-repo-split.md"],"mutation_classes":["field-omission","field-extra"],"source_sha256":"c03b29534aac5c73be1efaab1d0fbe42c4072f63221fcc93c9f103593a9236bb"}`
Terminal Repair 13 root singularities: `{"current_external_conflicts":["root-version-metadata-conflict-v2.5-v2.4","transport-gate-wave-ownership-conflict-wave-2-vs-wave-1.5"],"mutation_classes":["unchanged","paraphrase","dual-value"],"required_governance":{"root_version_metadata":{"cardinality":1,"value":"2.5"},"transport_gate_wave_ownership":{"cardinality":1,"value":"Wave 1.5"}},"schema":"terminal-repair-13-root-authority-singularities-v1"}`
Terminal Repair 13 emergency private owners: `{"canonical_file":"00-canonical.md","canonical_row_key":"Security/licensing emergency","manual_file":"12-pv-semantics-consumers-and-private-exports.md","mutation_classes":["omission","extra","duplicate"],"owners":["FMB-07A","FMB-07B","FMB-08EEBUS-A","FMB-08EEBUS","FMB-09A","FMB-09B"],"owners_sha256":"1a94f06beec8cb24629fe71b9fd3cb982d9f48caa5ba7436597f3b159be8122c","schema":"terminal-repair-13-private-emergency-owner-inventory-v1"}`
Terminal Repair 13 transport heading: `{"cardinality":1,"file":"93-pre-execution-matrix.md","heading":"## Typed Per-Family Transport Intent Mirror","mutation_classes":["malformed-plus-prefix","omission","duplicate","wrong-text"],"schema":"terminal-repair-13-normative-transport-heading-v1"}`
Terminal Repair 14 state: `{"finding_ids":["F1","F2","F3","F4","F5","F6"],"header_values":{"authoritative_plan_lock":"not achieved","current_revision":"v1.8-draft-terminal-repair-14","current_round":"Terminal Repair 14 requirements F1-F6 repaired in draft; external pre-lock gates and fresh terminal review pending","lock_ready":"false","plan_state":".draft","review_clean":"false"},"repair_id":"Terminal Repair 14","state":"repaired_in_draft_external_prelock_gates_pending"}`
Terminal Repair 14 pre-M8 RTU dispatch: `{"condition":"M2R_SELECTED_EXECUTABLE","consumer_issues":["FMB-04L","FMB-04O","FMB-06H"],"context_fields":["schema","context_id","validation_phase","consumer_repo","consumer_issue","consumer_head_sha","source_evidence","source_evidence_sha256","issued_at","expiry","signer_id","revocation_generation","signature"],"context_schema":"signed-pre-m8-m2r-dispatch-context-v1","context_signer":"transport-context-authority","fixture_ids":["pre-m8-m2r-pass","pre-m8-m2r-na"],"issue_fixture_mutation_classes":["rtu-fixture-omission","rtu-fixture-duplicate","rtu-test-id-omission","rtu-test-id-duplicate","rtu-paired-cardinality-omission","rtu-paired-cardinality-duplicate"],"mutation_classes":["wrong-repo","wrong-issue","stale-head","wrong-tree","wrong-digest","wrong-authority","signature","pass-with-absent-artifact","na-with-artifact"],"report_check_id":"terminal_repair_14_pre_m8_rtu_dispatch","report_field":"executed_fixture_sets","report_mutation_classes":["report-fixture-omission","report-fixture-duplicate","report-execution-cardinality"],"required_test_roles":{"FMB-04L":"system","FMB-04O":"SLO","FMB-06H":"exact-image"},"schema":"signed-pre-m8-m2r-dispatch-contract-v1","source_authority":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","source_contract_sha256":"eba1a95882395366db523ea0d5ac483a814b559dc43987d0e4c7552602a78a7f"},"source_evidence_fields":["schema","artifact","artifact_schema","artifact_version","producer_repo","producer_issue","producer_head_oid","producer_tree_oid","outcome","artifact_state","content_digest_sha256","producer_authority_id","source_contract_sha256","issued_at","expiry","signer_id","revocation_generation","signature"],"source_evidence_schema":"signed-fmb-02r-a-outcome-evidence-v1","source_evidence_signer":"transport-context-authority","source_outcomes":["PASS","N/A"]}`
Terminal Repair 14 RTU scope/executability: `{"executable_rule":"selected_rtu_profile_nodes-intersect-FMB-02R-A-PASS-and-runtime-readiness","executable_set":"executable_rtu_profile_nodes","mutation_classes":["selected-derived-from-m2r","selected-omission","selected-extra","executable-not-subset","m2r-na-executable"],"relationship":"executable_rtu_profile_nodes-is-always-a-subset-of-selected_rtu_profile_nodes","required_fixture":{"executable_rtu_profile_nodes":[],"scenario":"m2r-na-with-rtu-go","selected_rtu_profile_nodes":["FMB-08C"]},"schema":"terminal-repair-14-rtu-scope-executability-v1","selected_rule":"exact-set-of-all-profile-candidate-inventory-rows-with-transport-RTU-and-scope-outcome-GO-independent-of-M2R","selected_set":"selected_rtu_profile_nodes"}`
Terminal Repair 14 sensitive relationships: `{"begin_marker":"<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_BEGIN -->","canonical_prose":"After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.","canonical_statements":["After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other."],"declared_branch_aliases":{"huawei":["Huawei","FMB-08A-CUSTODY","FMB-08A clearance","custody/fact-clearance branch","custody/facts branch","custody and facts branch","custody -> facts","custody to facts","fact-clearance branch","custody/fact classification"],"neutral":["FMB-08A-INVENTORY","FMB-08A-SCOPE","neutral inventory/scope branch","neutral inventory and scope branch","inventory/scope branch","neutral branch","inventory -> scope","inventory to scope"]},"end_marker":"<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_END -->","expected_mutation_receipt_ids":["declared-alias-paraphrase","table-row-paraphrase","grouped-list-split","split-wrapped-block","mixed-clause-canonical-plus-dependency"],"forbidden_assertion":"semantic-serialization-of-neutral-branch-behind-huawei-clearance","manual_files":["00-canonical.md","10-boundaries-and-repo-split.md"],"mutation_receipt_schema":"terminal-repair-14-sensitive-block-mutation-receipts-v1","positive_fixture_ids":["canonical","canonical-markdown-wrapped"],"relationship_terms":["independent of","independent from","independent branch","independent branches","parallel with","parallel artifact path","parallel artifact paths","parallel artifact branch","parallel artifact branches","non-gating from","non gating from","gates it","gates the other","gated by","depends on","waits for","cannot begin until","starts after","starts once","unlocks","conditioned on","subject to","follows Huawei","follows from","clearance predicates","downstream of","antecedent","condition precedent","awaits","unlocked by","serializes","serialization","serialized behind"],"required_assertions":["after-common-predecessor","huawei-branch","neutral-branch","independent","neutral-not-gated"],"schema":"terminal-repair-14-sensitive-relationship-blocks-v1","sensitive_block_kinds":["paragraph","table-row","table-group","list-item","list-group","wrapped-block"],"sensitive_group_max_tokens":128,"sensitive_window_tokens":48,"validation_rule":"every-sensitive-block-normalizes-to-exactly-one-generated-canonical-independent-statement"}`
Terminal Repair 14 lock assertions: `{"begin_marker":"<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_BEGIN -->","canonical_statements":["PLAN_LOCK through PG-CRUISE-LOCK requires exactly these three chained external amendment gates: PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY."],"end_marker":"<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_END -->","exact_chain":"PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY","expected_mutation_receipt_ids":["reduced-chain","reordered-chain","partial-gate-id","mixed-clause","table-chain","grouped-list-chain"],"external_prerequisite_ids":["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY"],"external_prerequisite_subjects":["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY","PG-ARCHITECTURE","PG-ARCHITECTURE-MAP","PG-MODEL-ROUTING","PG-MODEL-ROUTING-POLICY","PG-SKILL-ADAPTER","external gate","external gates","external gate check","external gate checks","both gates","two gates","external prerequisite","external prerequisites","external lock condition","external lock conditions","external amendment","external amendments"],"lock_prose":"PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY -> PG-FRESH-TERMINAL-REVIEW -> PG-CRUISE-LOCK.","manual_files":["00-canonical.md","10-boundaries-and-repo-split.md"],"mutation_receipt_schema":"terminal-repair-14-sensitive-block-mutation-receipts-v1","positive_fixture_ids":["canonical","canonical-markdown-wrapped"],"prerequisite_order_terms":["requires","require","prerequisite order","exact order","ordered","chain","before","after","follows","followed by","depends on","waits for","cannot pass until","cannot complete until","must precede"],"schema":"terminal-repair-14-sensitive-lock-assertion-blocks-v1","sensitive_block_kinds":["paragraph","table-row","table-group","list-item","list-group","wrapped-block"],"sensitive_identifiers":["PLAN_LOCK","PG-CRUISE-LOCK","PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY","PG-ARCHITECTURE","PG-ARCHITECTURE-MAP","PG-MODEL-ROUTING","PG-MODEL-ROUTING-POLICY","PG-SKILL-ADAPTER","PG-SKILL-ADAPTER-REGISTRY"],"sensitive_window_tokens":24,"validation_rule":"every-sensitive-prerequisite-or-order-block-normalizes-to-the-exact-generated-three-gate-chained-statement"}`
Terminal Repair 14 RTU baseline prose: `{"canonical_sentence":"No mixed-RTU workload runs. The FMB-02R-A baseline key is exactly `repo+milestone+RTU+exact-HEAD`; every declared transport family requires a same-family immutable baseline, and a PDU baseline cannot satisfy RTU.","exact_files":["00-canonical.md","11-modbus-runtime-and-fronius-profile.md"],"forbidden_stale_fragments":["No mixed-RTU workload or"],"occurrences_per_file":1,"schema":"terminal-repair-14-rtu-baseline-prose-v1"}`
Terminal Repair 14 canonical coverage: `{"authority":{"architecture_decisions":{"count":108,"first":"AD01","ids_sha256":"3bc63bf26dd8fcc70f9c0cb69700e65122991746ca0e347fb9369d1cb85b9024","last":"AD108"},"invariants":{"count":87,"first":1,"ids_sha256":"44518a20100d2f73652ce108d7db6acbbec00b30bffc4768e56f59e13f451146","last":87}},"begin_marker":"<!-- CANONICAL_COVERAGE_RANGE_BEGIN -->","end_marker":"<!-- CANONICAL_COVERAGE_RANGE_END -->","mirror_file":"10-boundaries-and-repo-split.md","mutation_classes":["stale-invariant-last","stale-invariant-count","stale-ad-last","stale-ad-count"],"schema":"terminal-repair-14-canonical-coverage-ranges-v1","source_file":"00-canonical.md"}`
Terminal Repair 15 state: `{"finding_ids":["G1","G2","G3","G4","G5"],"header_values":{"authoritative_plan_lock":"not achieved","current_revision":"v1.9-draft-targeted-terminal-repair-15b","current_round":"Targeted Terminal Repair 15b residuals R1-R4 closed in draft; G1-G5 retained; external pre-lock gates and fresh terminal review pending","lock_ready":"false","plan_state":".draft","review_clean":"false"},"repair_id":"Targeted Terminal Repair 15b","state":"repaired_in_draft_external_prelock_gates_pending"}`
Terminal Repair 15 issue authority: `{"candidate_or_lock_validation":"external-signature-required","draft_validation":"allowed-only-for-this-exact-payload","schema":"terminal-repair-15-pending-issue-authority-v1","signed_payload_sha256":"4c5ee484f65cdaa8b5f0495c4483fa0e205ad95549998f0de74b1bcf5d6cc9ec","status":"PENDING_EXTERNAL_SIGNATURE"}`
Terminal Repair 15 read-only v1: `{"authorization_states":["UNAUTHORIZED","AUTHORIZED"],"canonical_prose":"Helianthus Modbus v1 is read-only. FMB-02A permits exactly FC01-FC04; FC05, FC06, FC0F, and FC10 and every write quantity limit are absent. An explicit topology-ordered inventory, independent of behavior-class inference, covers every issue that can declare, transport, or execute a Modbus operation, including profile descriptors, selectors, live harnesses, and exact-image/release harnesses. Every listed issue declares exactly FC01-FC04, sets `raw_write_supported=false`, and executes FC05, FC06, FC0F, FC10, and generic write fixtures with and without authorization. Every attempt returns exact `UNSUPPORTED` before transport access; independently committed receipts prove zero transport and write-transport calls. Per-issue mutants replace each descriptor with FC05, FC06, FC0F, or FC10 and mutate authorization, transport access, outcome, and fixture completeness. Write capability is reserved for an explicit future milestone and is out of scope for v1.","fixtures_per_issue":10,"fmb_02a_issue":"FMB-02A","forbidden_write_function_codes_hex":["05","06","0F","10"],"forbidden_write_quantity_limit_fields":["max_write_coils_fc0f","max_write_registers_fc10"],"future_write_scope":"explicit-future-milestone-only-out-of-scope-for-v1","gateway_surface_behavior_classes":["gateway_api","gateway_runtime"],"gateway_surface_issues":["FMB-00F-MODBUS","FMB-02C","FMB-03R","FMB-04K","FMB-04A","FMB-04S","FMB-04B","FMB-04D","FMB-04C","FMB-04L","FMB-04O","FMB-05A","FMB-05F","FMB-05E","FMB-05I","FMB-06A","FMB-06E","FMB-06B","FMB-08I","FMB-08J","FMB-08K","FMB-08L"],"inventory_authority":"per-milestone-typed-operation-descriptors-derived-from-transport-intents-and-artifact-contracts","manual_files":["00-canonical.md","11-modbus-runtime-and-fronius-profile.md"],"modbus_operation_capable_issues":["FMB-00F-MODBUS","FMB-02A","FMB-02B","FMB-02C","FMB-02R-A","FMB-03A","FMB-03B","FMB-03C","FMB-03D","FMB-03E0","FMB-03R","FMB-03E","FMB-04K","FMB-04A","FMB-04S","FMB-04B","FMB-04D","FMB-04C","FMB-04L","FMB-04O","FMB-05A","FMB-06H","FMB-08B","FMB-08C","FMB-08D","FMB-08E","FMB-08F","FMB-08F-SD","FMB-08G-RED","FMB-08H","FMB-08G-CLOSE","FMB-08I","FMB-08J","FMB-08O"],"mutation_classes":["add-fc05","add-fc06","add-fc0f","add-fc10","add-fc0f-write-limit","add-fc10-write-limit","pdu-write-enabled","gateway-api-write-enabled","gateway-runtime-write-enabled","authorization-bypass","authorized-write-accepted","write-reaches-transport","wrong-write-outcome","omitted-write-fixture"],"per_issue_mutation_operators":["accept-authorized-raw-write","allow-write-transport-call","replace-write-outcome","omit-write-rejection-fixture","replace-descriptor-with-fc05","replace-descriptor-with-fc06","replace-descriptor-with-fc0f","replace-descriptor-with-fc10"],"raw_modbus_issues":["FMB-00F-MODBUS","FMB-02A","FMB-02B","FMB-02C","FMB-02R-A","FMB-03A","FMB-03B","FMB-03C","FMB-03D","FMB-03E0","FMB-03R","FMB-03E","FMB-04K","FMB-04A","FMB-04S","FMB-04B","FMB-04D","FMB-04C","FMB-04L","FMB-04O","FMB-05A","FMB-06H","FMB-08B","FMB-08C","FMB-08D","FMB-08E","FMB-08F","FMB-08F-SD","FMB-08G-RED","FMB-08H","FMB-08G-CLOSE","FMB-08I","FMB-08J","FMB-08O"],"raw_write_supported":false,"read_function_codes_by_issue":{"FMB-00F-MODBUS":["03","04"],"FMB-02A":["01","02","03","04"],"FMB-02B":["01","02","03","04"],"FMB-02C":["03","04"],"FMB-02R-A":["01","02","03","04"],"FMB-03A":["03","04"],"FMB-03B":["03","04"],"FMB-03C":["03","04"],"FMB-03D":["03","04"],"FMB-03E":["03","04"],"FMB-03E0":["03","04"],"FMB-03R":["03","04"],"FMB-04A":["01","02","03","04"],"FMB-04B":["01","02","03","04"],"FMB-04C":["03","04"],"FMB-04D":["01","02","03","04"],"FMB-04K":["03","04"],"FMB-04L":["03","04"],"FMB-04O":["03","04"],"FMB-04S":["01","02","03","04"],"FMB-05A":["03","04"],"FMB-06H":["03","04"],"FMB-08B":["03","04"],"FMB-08C":["03","04"],"FMB-08D":["03","04"],"FMB-08E":["03","04"],"FMB-08F":["03","04"],"FMB-08F-SD":["03","04"],"FMB-08G-CLOSE":["03","04"],"FMB-08G-RED":["03","04"],"FMB-08H":["01","02","03","04"],"FMB-08I":["03","04"],"FMB-08J":["03","04"],"FMB-08O":["03","04"]},"receipt_schema":"raw-modbus-write-rejection-receipt-v1","receipt_signer_role":"independent-issue-verifier","rejection_stage":"BEFORE_TRANSPORT_ACCESS","schema":"targeted-terminal-repair-15b-read-only-modbus-v2","supported_function_codes_hex":["01","02","03","04"],"transport_call_count":0,"write_attempt_error":"UNSUPPORTED","write_authorization_effect":"NONE","write_request_kinds":["FC05","FC06","FC0F","FC10","GENERIC_WRITE"]}`
Terminal Repair 15 pre-M8 RTU evidence: `{"canonical_prose":"Pre-M8 RTU dispatch for FMB-04L, FMB-04O, and FMB-06H requires a producer-signed FMB-02R-A release envelope. Fixture input binds its exact verified envelope digest; independently signed source-contract evidence resolves the complete producer repo, issue, exact HEAD, tree, artifact schema, version, content digest, authority, and signer tuple. The receipt records both verified evidence digests and the complete tuple, and dispatch occurs only on exact equality with no caller-controlled source label.","canonical_source_bundle_schema":"producer-signed-fmb-02r-a-canonical-source-bundle-v1","canonical_source_bundles":{"N/A":{"outcome":"N/A","producer_release_envelope":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_state":"ABSENT","artifact_version":1,"content_digest_sha256":"ABSENT","expiry":"2026-07-11T20:00:00Z","issued_at":"2026-07-11T10:00:00Z","outcome":"N/A","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"8aba9446783a948335982f61a4eec809599783f3","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"3b636b4dc6e8385fb613f771bcd1fe8f43e1d678","revocation_generation":1,"schema":"producer-signed-fmb-02r-a-release-envelope-v1","signature":"eqr6A+P/dGbn5G7SSvI/wo5ziRlsUpAm58btzwjeaqJVqSVbMqwdoVGoUp+2JJ1ZbWpsgVui4TmY61fSHowXCA==","signer_id":"fmb-02r-a-release-authority"},"producer_release_envelope_sha256":"7c7b93b7943e05a9bf9a7edd44f1e03b0df833aed8d9e4f7f08270cc38bb8d50","schema":"producer-signed-fmb-02r-a-canonical-source-bundle-v1","source_contract_evidence":{"expected_source_tuple":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"content_digest_sha256":"ABSENT","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"8aba9446783a948335982f61a4eec809599783f3","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"3b636b4dc6e8385fb613f771bcd1fe8f43e1d678"},"expiry":"2026-07-11T20:00:00Z","issued_at":"2026-07-11T10:00:00Z","outcome":"N/A","revocation_generation":1,"schema":"signed-fmb-02r-a-source-contract-evidence-v1","signature":"X+K0Nu3Nqzdgzy97+nKOOzCJ8Zxdz5XoL60DevrZdtRW2+R/HW7ARFvg5pR6wq1Jqjysk+FHa5ItYevnviD+BA==","signer_id":"fmb-02r-a-source-contract-authority","source_contract_id":"FMB-02R-A:release-source-contract-v1"},"source_contract_evidence_sha256":"d46f04ac84576059c0bcf94fafccd9758df183852065ede659b00b61083bc77d","verified_source_tuple":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"content_digest_sha256":"ABSENT","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"8aba9446783a948335982f61a4eec809599783f3","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"3b636b4dc6e8385fb613f771bcd1fe8f43e1d678"}},"PASS":{"outcome":"PASS","producer_release_envelope":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_state":"AVAILABLE","artifact_version":1,"content_digest_sha256":"f6260695e7e9b92a194f1fba7785c0ac54fd4298afaa4369d2f593e87b986441","expiry":"2026-07-11T20:00:00Z","issued_at":"2026-07-11T10:00:00Z","outcome":"PASS","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"2e65f5542ea59dc10fb49992d2e433568ac866a1","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"603448dc108fb363e66a77265915c3946bfb24b4","revocation_generation":1,"schema":"producer-signed-fmb-02r-a-release-envelope-v1","signature":"dd0cyv4nq0o/sH4DnYtzxGAQ/yN1rtM+8vKzW7Js8r3Wi6k3dIMSVFKjQF2biarbTMTvb4D1v6xHFHg6NUXOCQ==","signer_id":"fmb-02r-a-release-authority"},"producer_release_envelope_sha256":"b53c621528092f6de63d2f9633ddeef848309b07b7fb122b196a39a333ce6092","schema":"producer-signed-fmb-02r-a-canonical-source-bundle-v1","source_contract_evidence":{"expected_source_tuple":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"content_digest_sha256":"f6260695e7e9b92a194f1fba7785c0ac54fd4298afaa4369d2f593e87b986441","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"2e65f5542ea59dc10fb49992d2e433568ac866a1","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"603448dc108fb363e66a77265915c3946bfb24b4"},"expiry":"2026-07-11T20:00:00Z","issued_at":"2026-07-11T10:00:00Z","outcome":"PASS","revocation_generation":1,"schema":"signed-fmb-02r-a-source-contract-evidence-v1","signature":"1JI8LedmSZhgVxYdk13AwtZpIMGRWDhWGWw6Fqm8e1+xrTTr7vxF2ACwPcE3SB346J41s/7eKSsO0uqk/GhNBA==","signer_id":"fmb-02r-a-source-contract-authority","source_contract_id":"FMB-02R-A:release-source-contract-v1"},"source_contract_evidence_sha256":"396ee4997569b658422696c956bda412b87ca5a1c48c29f745a096c385c91f9a","verified_source_tuple":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"content_digest_sha256":"f6260695e7e9b92a194f1fba7785c0ac54fd4298afaa4369d2f593e87b986441","producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_head_oid":"2e65f5542ea59dc10fb49992d2e433568ac866a1","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","producer_signer_id":"fmb-02r-a-release-authority","producer_tree_oid":"603448dc108fb363e66a77265915c3946bfb24b4"}}},"condition":"M2R_SELECTED_EXECUTABLE","consumer_issues":["FMB-04L","FMB-04O","FMB-06H"],"context_fields":["schema","context_id","validation_phase","consumer_repo","consumer_issue","consumer_head_sha","source_contract_evidence","source_contract_evidence_sha256","producer_release_envelope","producer_release_envelope_sha256","issued_at","expiry","signer_id","revocation_generation","signature"],"context_schema":"signed-pre-m8-m2r-dispatch-context-v2","context_signer":"transport-context-authority","dispatch_receipt_fields":["schema","consumer_repo","consumer_issue","transport_family","source_contract_id","source_outcome","dispatch_outcome","verified_source_contract_evidence_sha256","verified_producer_release_envelope_sha256","verified_source_tuple","verified_source_tuple_sha256","exact_source_tuple_equality","evidence_roles"],"dispatch_receipt_schema":"verified-pre-m8-rtu-dispatch-receipt-v1","manual_files":["00-canonical.md","11-modbus-runtime-and-fronius-profile.md"],"mutation_classes":["validly-resigned-stale-head","validly-resigned-wrong-tree","validly-resigned-wrong-digest","validly-resigned-wrong-repo","validly-resigned-wrong-issue","validly-resigned-wrong-schema","validly-resigned-wrong-signer","validly-resigned-wrong-envelope-digest"],"mutation_expected_failures":{"validly-resigned-stale-head":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-digest":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-envelope-digest":"pre-M8 RTU producer release envelope digest drift","validly-resigned-wrong-issue":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-repo":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-schema":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-signer":"pre-M8 RTU source tuple mismatch","validly-resigned-wrong-tree":"pre-M8 RTU source tuple mismatch"},"producer_envelope_fields":["schema","artifact","artifact_schema","artifact_version","producer_repo","producer_issue","producer_head_oid","producer_tree_oid","content_digest_sha256","producer_authority_id","producer_signer_id","outcome","artifact_state","issued_at","expiry","signer_id","revocation_generation","signature"],"producer_envelope_schema":"producer-signed-fmb-02r-a-release-envelope-v1","producer_envelope_signer":"fmb-02r-a-release-authority","required_test_roles":{"FMB-04L":"system","FMB-04O":"SLO","FMB-06H":"exact-image"},"schema":"targeted-terminal-repair-15b-authoritative-pre-m8-rtu-evidence-v2","source_authority":{"artifact":"modbus-rtu-v1","artifact_schema":"immutable-modbus-rtu-release-v1","artifact_version":1,"producer_authority_id":"FMB-02R-A:exact-head-release-authority","producer_issue":"FMB-02R-A","producer_repo":"helianthus-modbus","source_contract_id":"FMB-02R-A:release-source-contract-v1"},"source_contract_evidence_fields":["schema","source_contract_id","outcome","expected_source_tuple","issued_at","expiry","signer_id","revocation_generation","signature"],"source_contract_evidence_schema":"signed-fmb-02r-a-source-contract-evidence-v1","source_contract_evidence_signer":"fmb-02r-a-source-contract-authority","source_outcomes":["PASS","N/A"],"source_resolution_rule":"verify-producer-envelope-and-independent-source-contract-evidence-then-dispatch-only-on-exact-complete-source-tuple-equality","source_tuple_fields":["artifact","artifact_schema","artifact_version","producer_repo","producer_issue","producer_head_oid","producer_tree_oid","content_digest_sha256","producer_authority_id","producer_signer_id"],"transport_binding_rule":"transport-authority-envelope-references-exact-verified-producer-release-envelope-digest-no-caller-source-labels"}`
Terminal Repair 15 lock sensitivity: `{"begin_marker":"<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_BEGIN -->","canonical_block":"PLAN_LOCK through PG-CRUISE-LOCK requires exactly these three chained external amendment gates:\n\n- PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY.","canonical_child":"- PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY.","canonical_parent":"PLAN_LOCK through PG-CRUISE-LOCK requires exactly these three chained external amendment gates:","canonical_statements":["PLAN_LOCK through PG-CRUISE-LOCK requires exactly these three chained external amendment gates:\n\n- PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY."],"end_marker":"<!-- MANUAL_PLAN_LOCK_EXTERNAL_GATES_END -->","exact_chain":"PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY","expected_mutation_receipt_ids":["standalone-prerequisite","gated-by","arrow-only","table-arrow","grouped-list-bypass","canonical-plus-bypass","blank-line-child-bypass","list-child-bypass","table-child-bypass","arrow-child-bypass"],"external_prerequisite_ids":["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY"],"external_prerequisite_subjects":["PG-ARCHITECTURE-MAP-AMENDMENT","PG-MODEL-ROUTING-POLICY-AMENDMENT","PG-SKILL-ADAPTER-REGISTRY","PG-ARCHITECTURE","PG-ARCHITECTURE-MAP","PG-MODEL-ROUTING","PG-MODEL-ROUTING-POLICY","PG-SKILL-ADAPTER","external gate","external gates","external gate check","external gate checks","both gates","two gates","external prerequisite","external prerequisites","external lock condition","external lock conditions","external amendment","external amendments"],"lock_prose":"PG-ARCHITECTURE-MAP-AMENDMENT -> PG-MODEL-ROUTING-POLICY-AMENDMENT -> PG-SKILL-ADAPTER-REGISTRY -> PG-FRESH-TERMINAL-REVIEW -> PG-CRUISE-LOCK.","manual_files":["00-canonical.md","10-boundaries-and-repo-split.md"],"mutation_receipt_schema":"targeted-terminal-repair-15b-sensitive-block-mutation-receipts-v1","positive_fixture_ids":["canonical-parent-child","canonical-parent-child-blank-line"],"prerequisite_order_terms":["requires","require","prerequisite order","exact order","ordered","chain","before","after","follows","followed by","depends on","waits for","cannot pass until","cannot complete until","must precede"],"schema":"targeted-terminal-repair-15b-lock-parent-child-sensitivity-v2","sensitive_block_kinds":["paragraph","table-row","table-group","list-item","list-group","wrapped-block","standalone-prerequisite","arrow-only-cell"],"sensitive_group_max_tokens":128,"sensitive_identifiers":["PLAN_LOCK","PG-CRUISE-LOCK"],"sensitive_window_tokens":48,"sensitivity_rule":"lock-identifier-plus-external-gate-subject-regardless-of-relation-vocabulary","validation_rule":"aggregate-parent-with-immediately-following-list-or-table-across-blank-lines-and-require-the-exact-generated-canonical-chain-block"}`
Terminal Repair 15 neutral Huawei sensitivity: `{"begin_marker":"<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_BEGIN -->","canonical_block":"Branches run in parallel:\n\n- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.","canonical_child":"- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.","canonical_parent":"Branches run in parallel:","canonical_prose":"Branches run in parallel:\n\n- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.","canonical_statements":["Branches run in parallel:\n\n- After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other."],"declared_branch_aliases":{"huawei":["Huawei","FMB-08A-CUSTODY","FMB-08A clearance","custody/fact-clearance branch","custody/facts branch","custody and facts branch","custody -> facts","custody to facts","fact-clearance branch","custody/fact classification"],"neutral":["FMB-08A-INVENTORY","FMB-08A-SCOPE","neutral inventory/scope branch","neutral inventory and scope branch","inventory/scope branch","neutral branch","inventory -> scope","inventory to scope"]},"end_marker":"<!-- MANUAL_NEUTRAL_HUAWEI_RELATIONSHIP_END -->","expected_mutation_receipt_ids":["standalone-list","table-independent","table-parallel","arrow-only","grouped-standalone","canonical-plus-serialization","blank-line-child-bypass","list-child-bypass","table-child-bypass","split-parent-bypass"],"forbidden_assertion":"semantic-serialization-of-neutral-branch-behind-huawei-clearance","generated_assertion_prose":"After FMB-05R, the neutral FMB-08A-INVENTORY -> FMB-08A-SCOPE branch is independent of and runs in parallel with the Huawei custody and fact-clearance FMB-08A-CUSTODY -> FMB-08A branch; neither branch gates the other.","manual_files":["00-canonical.md","10-boundaries-and-repo-split.md"],"mutation_receipt_schema":"targeted-terminal-repair-15b-sensitive-block-mutation-receipts-v1","positive_fixture_ids":["canonical-parent-child","canonical-parent-child-blank-line"],"relationship_terms":["independent of","independent from","independent branch","independent branches","parallel with","parallel artifact path","parallel artifact paths","parallel artifact branch","parallel artifact branches","non-gating from","non gating from","gates it","gates the other","gated by","depends on","waits for","cannot begin until","starts after","starts once","unlocks","conditioned on","subject to","follows Huawei","follows from","clearance predicates","downstream of","antecedent","condition precedent","awaits","unlocked by","serializes","serialization","serialized behind"],"required_assertions":["after-common-predecessor","huawei-branch","neutral-branch","independent","neutral-not-gated"],"schema":"targeted-terminal-repair-15b-neutral-parent-child-sensitivity-v2","sensitive_block_kinds":["paragraph","table-row","table-group","list-item","list-group","wrapped-block","standalone","arrow-only-cell"],"sensitive_group_max_tokens":128,"sensitive_window_tokens":48,"sensitivity_rule":"declared-neutral-and-huawei-aliases-cooccur-with-independent-parallel-or-arrow-structure","validation_rule":"aggregate-parent-with-immediately-following-list-or-table-across-blank-lines-and-require-the-exact-generated-canonical-relationship-block"}`
Terminal Repair 15 predicate operator docs: `{"action_operators":["set_node_state","set_node_set_state","emit_artifact","emit_fresh_genesis","enable_conditional_consumer","record_no_artifact","record_inventory_fact","aggregate_profile_families","derive_rtu_selection","record_node_set_artifacts_absent"],"begin_marker":"<!-- MACHINE_OPERATOR_REGISTRY_BEGIN -->","end_marker":"<!-- MACHINE_OPERATOR_REGISTRY_END -->","heading":"## Machine Operator Registry v4","manual_files":["00-canonical.md","01-index.md","10-boundaries-and-repo-split.md","11-modbus-runtime-and-fronius-profile.md","12-pv-semantics-consumers-and-private-exports.md","13-roadmap-issues-risks.md","90-issue-map.md","91-milestone-map.md","92-adversarial-review.md","93-pre-execution-matrix.md","99-status.md"],"mutation_classes":["predicate-missing","predicate-extra","predicate-order","action-missing","action-extra","action-order"],"predicate_operators":["always","all","any","not","outcome_is","artifact_field_is","node_set_nonempty","selected_set_empty","inventory_row_outcome_is","verified_artifact_digest_present"],"schema":"terminal-repair-15-predicate-operator-docs-v1","source":"predicate_action_schema"}`
Terminal Repair 16 critical issue oracles: `{"FMB-02B":{"case_bindings":[{"case_id":"TCP-MBAP-LENGTH","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPMBAPLENGTH$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-MBAP-LENGTH"},{"case_id":"TCP-TXID-WRAP-NO-REUSE","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPTXIDWRAPNOREUSE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-TXID-WRAP-NO-REUSE"},{"case_id":"TCP-CORRELATION-UNIT-ISOLATION","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPCORRELATIONUNITISOLATION$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-CORRELATION-UNIT-ISOLATION"},{"case_id":"TCP-FAIRNESS","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPFAIRNESS$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-FAIRNESS"},{"case_id":"TCP-BACKPRESSURE","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPBACKPRESSURE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-BACKPRESSURE"},{"case_id":"TCP-ABSOLUTE-DEADLINE","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPABSOLUTEDEADLINE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-ABSOLUTE-DEADLINE"},{"case_id":"TCP-RETRY-FRESH-COMPLETE-ADU","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPRETRYFRESHCOMPLETEADU$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-RETRY-FRESH-COMPLETE-ADU"},{"case_id":"TCP-CANCELLATION-DRAIN","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPCANCELLATIONDRAIN$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-CANCELLATION-DRAIN"},{"case_id":"TCP-SHUTDOWN-DRAIN","case_kind":"required","command_argv":["go","test","./tcp/...","-run","^TestTCPSHUTDOWNDRAIN$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-02B-CRITICAL-TCP-SHUTDOWN-DRAIN"},{"case_id":"TXID-REUSE-WHILE-INFLIGHT","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestTXIDREUSEWHILEINFLIGHT$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-TXID-REUSE-WHILE-INFLIGHT"},{"case_id":"CROSS-UNIT-RESPONSE","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestCROSSUNITRESPONSE$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-CROSS-UNIT-RESPONSE"},{"case_id":"STARVATION","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestSTARVATION$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-STARVATION"},{"case_id":"QUEUE-OVERFLOW","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestQUEUEOVERFLOW$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-QUEUE-OVERFLOW"},{"case_id":"DEADLINE-RESET-ON-RETRY","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestDEADLINERESETONRETRY$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-DEADLINE-RESET-ON-RETRY"},{"case_id":"PARTIAL-STREAM-RETRY","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestPARTIALSTREAMRETRY$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-PARTIAL-STREAM-RETRY"},{"case_id":"LATE-RESPONSE-AFTER-CANCEL","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestLATERESPONSEAFTERCANCEL$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-LATE-RESPONSE-AFTER-CANCEL"},{"case_id":"NEW-WORK-AFTER-SHUTDOWN","case_kind":"negative","command_argv":["go","test","./tcp/...","-run","^TestNEWWORKAFTERSHUTDOWN$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-02B-CRITICAL-NEW-WORK-AFTER-SHUTDOWN"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["case_results_sha256","correlation_ledger_sha256","fairness_report_sha256","deadline_report_sha256"],"issue":"FMB-02B","negative_case_ids":["TXID-REUSE-WHILE-INFLIGHT","CROSS-UNIT-RESPONSE","STARVATION","QUEUE-OVERFLOW","DEADLINE-RESET-ON-RETRY","PARTIAL-STREAM-RETRY","LATE-RESPONSE-AFTER-CANCEL","NEW-WORK-AFTER-SHUTDOWN"],"numeric_limits":{"absolute_deadline_count":1,"max_adu_bytes":260,"max_unmatched_responses":0,"transaction_id_bits":16},"oracle_sha256":"f59c666bb00bbcc3ed305bd276b422222837a312e5d85254c6b5e80ca2666de9","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","case_results_sha256","correlation_ledger_sha256","fairness_report_sha256","deadline_report_sha256"],"report_schema":"modbus-tcp-conformance-report-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"modbus-tcp-conformance-report-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-02B","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["TCP-MBAP-LENGTH","TCP-TXID-WRAP-NO-REUSE","TCP-CORRELATION-UNIT-ISOLATION","TCP-FAIRNESS","TCP-BACKPRESSURE","TCP-ABSOLUTE-DEADLINE","TCP-RETRY-FRESH-COMPLETE-ADU","TCP-CANCELLATION-DRAIN","TCP-SHUTDOWN-DRAIN"],"schema":"critical-issue-specific-oracle-v1"},"FMB-03E":{"case_bindings":[{"case_id":"FRONIUS-EXACT-TARGET","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSEXACTTARGET$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-EXACT-TARGET"},{"case_id":"FRONIUS-FC03","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSFC03$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-FC03"},{"case_id":"FRONIUS-FC04","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSFC04$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-FC04"},{"case_id":"FRONIUS-ZERO-WRITE","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSZEROWRITE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-ZERO-WRITE"},{"case_id":"FRONIUS-OFF-TARGET-ZERO-ACCESS","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSOFFTARGETZEROACCESS$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-OFF-TARGET-ZERO-ACCESS"},{"case_id":"FRONIUS-CAPTURE","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSCAPTURE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-CAPTURE"},{"case_id":"FRONIUS-RECONNECT","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSRECONNECT$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-RECONNECT"},{"case_id":"FRONIUS-DOUBLE-REPLAY-BYTE-EQUALITY","case_kind":"required","command_argv":["go","test","./profiles/fronius/...","-run","^TestFRONIUSDOUBLEREPLAYBYTEEQUALITY$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-03E-CRITICAL-FRONIUS-DOUBLE-REPLAY-BYTE-EQUALITY"},{"case_id":"WRONG-ENDPOINT","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestWRONGENDPOINT$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-WRONG-ENDPOINT"},{"case_id":"WRONG-UNIT","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestWRONGUNIT$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-WRONG-UNIT"},{"case_id":"FC-WRITE","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestFCWRITE$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-FC-WRITE"},{"case_id":"OFF-TARGET-READ","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestOFFTARGETREAD$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-OFF-TARGET-READ"},{"case_id":"CAPTURE-DRIFT","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestCAPTUREDRIFT$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-CAPTURE-DRIFT"},{"case_id":"RECONNECT-EPOCH-REUSE","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestRECONNECTEPOCHREUSE$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-RECONNECT-EPOCH-REUSE"},{"case_id":"REPLAY-DIVERGENCE","case_kind":"negative","command_argv":["go","test","./profiles/fronius/...","-run","^TestREPLAYDIVERGENCE$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-03E-CRITICAL-REPLAY-DIVERGENCE"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["target_identity_sha256","capture_sha256","request_ledger_sha256","replay_1_sha256","replay_2_sha256","zero_write_receipt_sha256"],"issue":"FMB-03E","negative_case_ids":["WRONG-ENDPOINT","WRONG-UNIT","FC-WRITE","OFF-TARGET-READ","CAPTURE-DRIFT","RECONNECT-EPOCH-REUSE","REPLAY-DIVERGENCE"],"numeric_limits":{"allowed_function_codes_hex":["03","04"],"off_target_access_count":0,"required_replay_count":2,"write_transport_call_count":0},"oracle_sha256":"176669cdf41ef60cb8d253e4cd051a7905df73167db20cc354596cc0b4e8ceb1","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","target_identity_sha256","capture_sha256","request_ledger_sha256","replay_1_sha256","replay_2_sha256","zero_write_receipt_sha256"],"report_schema":"fronius-live-proof-report-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"fronius-live-proof-report-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-03E","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["FRONIUS-EXACT-TARGET","FRONIUS-FC03","FRONIUS-FC04","FRONIUS-ZERO-WRITE","FRONIUS-OFF-TARGET-ZERO-ACCESS","FRONIUS-CAPTURE","FRONIUS-RECONNECT","FRONIUS-DOUBLE-REPLAY-BYTE-EQUALITY"],"schema":"critical-issue-specific-oracle-v1"},"FMB-04O":{"case_bindings":[{"case_id":"SLO-RUN-1","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLORUN1$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-RUN-1"},{"case_id":"SLO-RUN-2","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLORUN2$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-RUN-2"},{"case_id":"SLO-RUN-3","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLORUN3$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-RUN-3"},{"case_id":"SLO-RECOVERY-BOUND","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLORECOVERYBOUND$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-RECOVERY-BOUND"},{"case_id":"SLO-EBUS-NO-DRIFT","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLOEBUSNODRIFT$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-EBUS-NO-DRIFT"},{"case_id":"SLO-BACKPRESSURE","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestSLOBACKPRESSURE$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-04O-CRITICAL-SLO-BACKPRESSURE"},{"case_id":"RUN-OMISSION","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestRUNOMISSION$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-RUN-OMISSION"},{"case_id":"POLL-COUNT-BELOW-300","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestPOLLCOUNTBELOW300$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-POLL-COUNT-BELOW-300"},{"case_id":"HEALTHY-RATIO-BELOW-99","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestHEALTHYRATIOBELOW99$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-HEALTHY-RATIO-BELOW-99"},{"case_id":"EBUS-P95-REGRESSION-OVER-5","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestEBUSP95REGRESSIONOVER5$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-EBUS-P95-REGRESSION-OVER-5"},{"case_id":"RECOVERY-BOUND-EXCEEDED","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestRECOVERYBOUNDEXCEEDED$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-RECOVERY-BOUND-EXCEEDED"},{"case_id":"CAP-BREACH","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestCAPBREACH$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-04O-CRITICAL-CAP-BREACH"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["run_reports_sha256","ebus_matrix_sha256"],"issue":"FMB-04O","negative_case_ids":["RUN-OMISSION","POLL-COUNT-BELOW-300","HEALTHY-RATIO-BELOW-99","EBUS-P95-REGRESSION-OVER-5","RECOVERY-BOUND-EXCEEDED","CAP-BREACH"],"numeric_limits":{"baseline_minutes":30,"ebus_p95_regression_percent_max":5,"fault_minutes":30,"healthy_polls_within_2x_percent_min":99,"independent_runs":3,"minimum_recovery_minutes":10,"minimum_scheduled_polls_per_healthy_endpoint":300,"warmup_minutes":5},"oracle_sha256":"b778ac30b38e7f78a3d379cc9ae7139cd7616a0f14e01beb87c427914a285b45","recovery_formula":"fault_clear_to_three_consecutive_successes<=breaker_max_open+max_operation_deadline+3*configured_poll_interval","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","run_reports","run_reports_sha256","breaker_max_open","max_operation_deadline","configured_poll_interval","calculated_recovery_bound","observed_recovery","ebus_matrix_sha256"],"report_schema":"versioned-three-run-slo-report-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"versioned-three-run-slo-report-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-04O","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["SLO-RUN-1","SLO-RUN-2","SLO-RUN-3","SLO-RECOVERY-BOUND","SLO-EBUS-NO-DRIFT","SLO-BACKPRESSURE"],"schema":"critical-issue-specific-oracle-v1"},"FMB-06H":{"case_bindings":[{"case_id":"EXACT-IMAGE-PDU","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-PDU"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-PDU"},{"case_id":"EXACT-IMAGE-TCP","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-TCP"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-TCP"},{"case_id":"EXACT-IMAGE-REPLAY","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-REPLAY"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-REPLAY"},{"case_id":"EXACT-IMAGE-RTU-IF-SELECTED","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-RTU-IF-SELECTED"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-RTU-IF-SELECTED"},{"case_id":"EXACT-IMAGE-SYSTEM-LIVE","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-SYSTEM-LIVE"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-SYSTEM-LIVE"},{"case_id":"EXACT-IMAGE-THREE-RUN-SLO","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-THREE-RUN-SLO"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-THREE-RUN-SLO"},{"case_id":"EXACT-IMAGE-EBUS-T01-T88","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-EBUS-T01-T88"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-EBUS-T01-T88"},{"case_id":"EXACT-IMAGE-TWO-CLEAN-BUILDERS","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-TWO-CLEAN-BUILDERS"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-TWO-CLEAN-BUILDERS"},{"case_id":"EXACT-IMAGE-A-B-FAULTS","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-A-B-FAULTS"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-A-B-FAULTS"},{"case_id":"EXACT-IMAGE-RELEASE-TRUST","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-RELEASE-TRUST"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-RELEASE-TRUST"},{"case_id":"EXACT-IMAGE-CUSTODY","case_kind":"required","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EXACT-IMAGE-CUSTODY"],"expected_outcome":"PASS","fixture_id":"FMB-06H-CRITICAL-EXACT-IMAGE-CUSTODY"},{"case_id":"IMAGE-DIGEST-MISMATCH","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","IMAGE-DIGEST-MISMATCH"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-IMAGE-DIGEST-MISMATCH"},{"case_id":"CONFIG-DIGEST-MISMATCH","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","CONFIG-DIGEST-MISMATCH"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-CONFIG-DIGEST-MISMATCH"},{"case_id":"EMBEDDED-MANIFEST-MISMATCH","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EMBEDDED-MANIFEST-MISMATCH"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-EMBEDDED-MANIFEST-MISMATCH"},{"case_id":"MATRIX-OMISSION","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","MATRIX-OMISSION"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-MATRIX-OMISSION"},{"case_id":"SLO-TERM-OMISSION","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","SLO-TERM-OMISSION"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-SLO-TERM-OMISSION"},{"case_id":"EBUS-DRIFT","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","EBUS-DRIFT"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-EBUS-DRIFT"},{"case_id":"BUILDER-BYTE-MISMATCH","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","BUILDER-BYTE-MISMATCH"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-BUILDER-BYTE-MISMATCH"},{"case_id":"WAL-FAULT","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","WAL-FAULT"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-WAL-FAULT"},{"case_id":"REVOKED-RELEASE-KEY","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","REVOKED-RELEASE-KEY"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-REVOKED-RELEASE-KEY"},{"case_id":"CUSTODY-LEAK","case_kind":"negative","command_argv":["./scripts/verify_exact_candidate_case.sh","--case","CUSTODY-LEAK"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-06H-CRITICAL-CUSTODY-LEAK"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["image_sha256","config_sha256","embedded_manifest_sha256","pdu_report_sha256","tcp_report_sha256","replay_report_sha256","rtu_report_sha256_or_na","system_live_report_sha256","slo_report_sha256","ebus_t01_t88_report_sha256","two_builder_report_sha256","package_fault_report_sha256","release_trust_report_sha256","custody_report_sha256"],"issue":"FMB-06H","negative_case_ids":["IMAGE-DIGEST-MISMATCH","CONFIG-DIGEST-MISMATCH","EMBEDDED-MANIFEST-MISMATCH","MATRIX-OMISSION","SLO-TERM-OMISSION","EBUS-DRIFT","BUILDER-BYTE-MISMATCH","WAL-FAULT","REVOKED-RELEASE-KEY","CUSTODY-LEAK"],"numeric_limits":{"ebus_matrix_first":1,"ebus_matrix_last":88,"independent_clean_builders":2,"unexpected_matrix_failures":0,"unexpected_matrix_xpasses":0},"oracle_sha256":"af451c79a3e359c3650e1f1023d321c56732b43dbf65ce90acf7a83d227e0e67","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","image_sha256","config_sha256","embedded_manifest_sha256","pdu_report_sha256","tcp_report_sha256","replay_report_sha256","rtu_report_sha256_or_na","system_live_report_sha256","slo_report_sha256","ebus_t01_t88_report_sha256","two_builder_report_sha256","package_fault_report_sha256","release_trust_report_sha256","custody_report_sha256"],"report_schema":"final-candidate-validation-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"final-candidate-validation-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-06H","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["EXACT-IMAGE-PDU","EXACT-IMAGE-TCP","EXACT-IMAGE-REPLAY","EXACT-IMAGE-RTU-IF-SELECTED","EXACT-IMAGE-SYSTEM-LIVE","EXACT-IMAGE-THREE-RUN-SLO","EXACT-IMAGE-EBUS-T01-T88","EXACT-IMAGE-TWO-CLEAN-BUILDERS","EXACT-IMAGE-A-B-FAULTS","EXACT-IMAGE-RELEASE-TRUST","EXACT-IMAGE-CUSTODY"],"schema":"critical-issue-specific-oracle-v1"},"FMB-08A":{"case_bindings":[{"case_id":"HUA-PRED-TRUTH-TABLE","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-PRED-TRUTH-TABLE"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-PRED-TRUTH-TABLE"},{"case_id":"HUA-APPLICABILITY-DISJOINT","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-APPLICABILITY-DISJOINT"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-APPLICABILITY-DISJOINT"},{"case_id":"HUA-ENDPOINT-BUDGET","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-ENDPOINT-BUDGET"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-ENDPOINT-BUDGET"},{"case_id":"HUA-GATEWAY-CLASSIFICATION","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-GATEWAY-CLASSIFICATION"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-GATEWAY-CLASSIFICATION"},{"case_id":"HUA-DOWNSTREAM-SEPARATION","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-DOWNSTREAM-SEPARATION"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-DOWNSTREAM-SEPARATION"},{"case_id":"HUA-REVOCATION-RACE","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-REVOCATION-RACE"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-REVOCATION-RACE"},{"case_id":"HUA-GO-GOLDEN-BYTE-EQUALITY","case_kind":"required","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","HUA-GO-GOLDEN-BYTE-EQUALITY"],"expected_outcome":"PASS","fixture_id":"FMB-08A-CRITICAL-HUA-GO-GOLDEN-BYTE-EQUALITY"},{"case_id":"UNCLEARED-FACT-LEAF","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","UNCLEARED-FACT-LEAF"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-UNCLEARED-FACT-LEAF"},{"case_id":"OVERLAPPING-APPLICABILITY","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","OVERLAPPING-APPLICABILITY"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-OVERLAPPING-APPLICABILITY"},{"case_id":"BUDGET-OVERFLOW","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","BUDGET-OVERFLOW"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-BUDGET-OVERFLOW"},{"case_id":"ROUTING-UNIT-AS-GATEWAY","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","ROUTING-UNIT-AS-GATEWAY"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-ROUTING-UNIT-AS-GATEWAY"},{"case_id":"READABILITY-AS-GATEWAY","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","READABILITY-AS-GATEWAY"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-READABILITY-AS-GATEWAY"},{"case_id":"LATE-RESPONSE-AFTER-REVOCATION","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","LATE-RESPONSE-AFTER-REVOCATION"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-LATE-RESPONSE-AFTER-REVOCATION"},{"case_id":"GO-GOLDEN-DRIFT","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","GO-GOLDEN-DRIFT"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-GO-GOLDEN-DRIFT"},{"case_id":"EMMA-WITHOUT-EVIDENCE","case_kind":"negative","command_argv":["python3","scripts/validate_huawei_oracle_case.py","--case","EMMA-WITHOUT-EVIDENCE"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08A-CRITICAL-EMMA-WITHOUT-EVIDENCE"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["predicate_dag_sha256","truth_table_sha256","applicability_rules_sha256","endpoint_budget_ledger_sha256","gateway_classification_goldens_sha256","downstream_goldens_sha256","revocation_race_report_sha256","go_golden_bytes_sha256"],"issue":"FMB-08A","negative_case_ids":["UNCLEARED-FACT-LEAF","OVERLAPPING-APPLICABILITY","BUDGET-OVERFLOW","ROUTING-UNIT-AS-GATEWAY","READABILITY-AS-GATEWAY","LATE-RESPONSE-AFTER-REVOCATION","GO-GOLDEN-DRIFT","EMMA-WITHOUT-EVIDENCE"],"numeric_limits":{"emma_enabled":false,"late_post_revocation_publications_max":0,"overlapping_applicability_rules_max":0,"uncleared_fact_consumers_max":0},"oracle_sha256":"a00d4d902e41976f620e48a724887b174a17cecc215d0f0194ee97c8f7865724","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","predicate_dag_sha256","truth_table_sha256","applicability_rules_sha256","endpoint_budget_ledger_sha256","gateway_classification_goldens_sha256","downstream_goldens_sha256","revocation_race_report_sha256","go_golden_bytes_sha256"],"report_schema":"huawei-fact-clearance-oracle-report-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"huawei-fact-clearance-oracle-report-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-08A","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["HUA-PRED-TRUTH-TABLE","HUA-APPLICABILITY-DISJOINT","HUA-ENDPOINT-BUDGET","HUA-GATEWAY-CLASSIFICATION","HUA-DOWNSTREAM-SEPARATION","HUA-REVOCATION-RACE","HUA-GO-GOLDEN-BYTE-EQUALITY"],"schema":"critical-issue-specific-oracle-v1"},"FMB-08I":{"case_bindings":[{"case_id":"HUA-GATEWAY-CLASSIFICATION-SCHEMA","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUAGATEWAYCLASSIFICATIONSCHEMA$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-GATEWAY-CLASSIFICATION-SCHEMA"},{"case_id":"HUA-RAW-DOWNSTREAM-OBSERVATION-SCHEMA","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUARAWDOWNSTREAMOBSERVATIONSCHEMA$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-RAW-DOWNSTREAM-OBSERVATION-SCHEMA"},{"case_id":"HUA-FIRMWARE-EXACT-APPLICABILITY","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUAFIRMWAREEXACTAPPLICABILITY$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-FIRMWARE-EXACT-APPLICABILITY"},{"case_id":"HUA-MIXED-TOPOLOGY-GENERATIONS","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUAMIXEDTOPOLOGYGENERATIONS$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-MIXED-TOPOLOGY-GENERATIONS"},{"case_id":"HUA-REVOCATION-AT-OUTPUT","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUAREVOCATIONATOUTPUT$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-REVOCATION-AT-OUTPUT"},{"case_id":"HUA-SELECTION-LEDGER","case_kind":"required","command_argv":["go","test","./internal/runtime/...","-run","^TestHUASELECTIONLEDGER$","-count=1"],"expected_outcome":"PASS","fixture_id":"FMB-08I-CRITICAL-HUA-SELECTION-LEDGER"},{"case_id":"NEAREST-MAP-FALLBACK","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestNEARESTMAPFALLBACK$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-NEAREST-MAP-FALLBACK"},{"case_id":"UNGATED-FIRMWARE","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestUNGATEDFIRMWARE$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-UNGATED-FIRMWARE"},{"case_id":"ROUTING-UNIT-AS-IDENTITY","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestROUTINGUNITASIDENTITY$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-ROUTING-UNIT-AS-IDENTITY"},{"case_id":"ORDINAL-COLLISION","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestORDINALCOLLISION$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-ORDINAL-COLLISION"},{"case_id":"REMOVAL-REUSE-WITHOUT-GENERATION","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestREMOVALREUSEWITHOUTGENERATION$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-REMOVAL-REUSE-WITHOUT-GENERATION"},{"case_id":"LATE-OUTPUT-AFTER-REVOCATION","case_kind":"negative","command_argv":["go","test","./internal/runtime/...","-run","^TestLATEOUTPUTAFTERREVOCATION$","-count=1"],"expected_outcome":"REJECTED_AS_EXPECTED","fixture_id":"FMB-08I-CRITICAL-LATE-OUTPUT-AFTER-REVOCATION"}],"case_transcript_contract":{"exact_fields":["schema","case_id","fixture_id","command_argv","command_argv_sha256","source_head_sha","environment_sha256","exit_code","stdout_payload","stdout_sha256","stderr_sha256","measured_output_sha256","outcome","signer_id","revocation_generation","signature"],"report_verifier_signer_id":"independent-critical-oracle-verifier","runner_signer_id":"critical-oracle-execution-runner","schema":"critical-oracle-executed-case-transcript-v1"},"evidence_digest_fields":["gateway_classification_schema_sha256","raw_downstream_observation_schema_sha256","firmware_applicability_sha256","mixed_topology_report_sha256","revocation_report_sha256","selection_ledger_sha256"],"issue":"FMB-08I","negative_case_ids":["NEAREST-MAP-FALLBACK","UNGATED-FIRMWARE","ROUTING-UNIT-AS-IDENTITY","ORDINAL-COLLISION","REMOVAL-REUSE-WITHOUT-GENERATION","LATE-OUTPUT-AFTER-REVOCATION"],"numeric_limits":{"late_post_revocation_outputs":0,"nearest_map_fallback_count":0,"topology_generation_required":true,"ungated_firmware_publications":0},"oracle_sha256":"52bd134366ce6fa4f04c791b1d40b045a54978f0a679d8fc494bd6c51ed5d44b","report_fields":["schema","issue","source_head_sha","artifact_sha256","report_sha256","fixture_set_sha256","environment_sha256","evidence_provider","signer_id","revocation_generation","signature","oracle_sha256","case_set_sha256","case_results","case_transcripts","case_transcripts_sha256","numeric_results","resolved_verifier_argv_sha256","validator_sha256","gateway_classification_schema_sha256","raw_downstream_observation_schema_sha256","firmware_applicability_sha256","mixed_topology_report_sha256","revocation_report_sha256","selection_ledger_sha256"],"report_schema":"huawei-runtime-topology-oracle-report-v1","report_signature_contract":{"extra_fields":"forbidden","head_binding":"EXACT","schema":"huawei-runtime-topology-oracle-report-v1","signature_algorithm":"Ed25519","signer_role":"independent-critical-oracle-verifier"},"report_verifier_execution":{"argv_template":["{python}","{package}/validate_plan.py","{package}","--verify-critical-oracle-report","FMB-08I","--critical-report","{report}","--critical-report-trusted-keys","{trusted_keys}","--critical-report-target-head","{target_head}"],"cwd":"execution-plan-package-root","resolved_argv_digest_field":"resolved_verifier_argv_sha256","schema":"resolved-critical-oracle-verifier-execution-v1","substitution_sources":{"package":"resolved-package-root","python":"validator-runtime-sys.executable","report":"resolved-critical-report-path","target_head":"exact-target-head-argument","trusted_keys":"resolved-trusted-key-registry-path"},"validator_digest_field":"validator_sha256"},"required_test_ids":["HUA-GATEWAY-CLASSIFICATION-SCHEMA","HUA-RAW-DOWNSTREAM-OBSERVATION-SCHEMA","HUA-FIRMWARE-EXACT-APPLICABILITY","HUA-MIXED-TOPOLOGY-GENERATIONS","HUA-REVOCATION-AT-OUTPUT","HUA-SELECTION-LEDGER"],"schema":"critical-issue-specific-oracle-v1"}}`
Terminal Repair 16 pre-execution intents: `{"critical_complexities":{"FMB-00D":10,"FMB-02A":10,"FMB-02B":10,"FMB-02C":10,"FMB-02R-A":10},"issue_count":81,"schema":"pre-execution-intent-authority-v1","sha256":"cd82837e5d705c877d63b1085401dfda7d841bfdd7db9255d41d0934db091d91"}`
Terminal Repair 16 state: `{"finding_ids":["H1","H2","H3","H4","H5"],"issue_commitment_schema":"immutable-issue-behavior-commitment-v4","pre_execution_intents_sha256":"cd82837e5d705c877d63b1085401dfda7d841bfdd7db9255d41d0934db091d91","repair_id":"Terminal Repair 16","schema":"terminal-repair-16-contracts-v1"}`
Generation recovery: `{"divergent_successor_negatives":["tdd-pending","tdd-active","huawei-pending","huawei-active"],"fallback_rule":"atomically-repair-active-pointer-to-validated-effective-generation-before-successor-derivation","orphan_rule":"remove-incomplete-or-invalid-orphan-generation-paths-only-after-signed-recovery-authorization","pending_rule":"idempotently-resume-only-one-fully-validated-exact-successor-bundle-bound-to-predecessor-generation-bundle-and-lineage-state","reason_codes":["fallback-to-validated-generation","resume-validated-pending-bundle","remove-incomplete-orphan-generation","remove-invalid-or-divergent-orphan-generation"],"record_directory":"recovery","record_fields":["schema","lineage_id","recovery_sequence","reason_code","pointer_before_sha256","selected_generation","selected_bundle_sha256","pointer_after_sha256","orphan_actions","repaired_at","signer_id","revocation_generation","signature"],"record_schema":"signed-generation-recovery-record-v1","report_binding":"execution-entry-includes-successfully-returned-callable-source-sha256","report_check_id":"terminal_repair_12_generation_recovery_successor_harness","schema":"repairable-generation-store-recovery-v1","signed_predecessor_binding_fields":["predecessor_generation","predecessor_bundle_sha256","predecessor_lineage_state_sha256"],"successor_rule":"next-generation-equals-repaired-effective-active-generation-plus-one-and-appends-exactly-one-record-without-history-rewrite","tested_stores":["tdd-consumption","huawei-replay"]}`
Issue execution classes: `{"classification_source":"explicit-issue-id-map-never-scope-substring-heuristics","fields":["schema","repository_owner","behavior_class","test_class","toolchain"],"issue_count":81,"issues":{"FMB-00D":{"behavior_class":"planning_gate","repository_owner":"helianthus-execution-plans","schema":"explicit-issue-execution-class-v1","test_class":"plan-validator","toolchain":"python3"},"FMB-00E-EEBUS":{"behavior_class":"repository_governance","repository_owner":"helianthus-org-github","schema":"explicit-issue-execution-class-v1","test_class":"repository-policy","toolchain":"gh+python3"},"FMB-00E-MATTER":{"behavior_class":"repository_governance","repository_owner":"helianthus-org-github","schema":"explicit-issue-execution-class-v1","test_class":"repository-policy","toolchain":"gh+python3"},"FMB-00E-PUBLIC":{"behavior_class":"repository_governance","repository_owner":"helianthus-org-github","schema":"explicit-issue-execution-class-v1","test_class":"repository-policy","toolchain":"gh+python3"},"FMB-00F-DOCS":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-00F-EEBUS":{"behavior_class":"private_binding","repository_owner":"helianthus-eebus-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-00F-MATTER":{"behavior_class":"private_binding","repository_owner":"helianthus-matter-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-00F-MODBUS":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-00F-MODBUSREG":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-01A":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-ebus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-01B":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-01C":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-01D":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-01E":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-02A":{"behavior_class":"modbus_pdu","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"modbus-pdu","toolchain":"go"},"FMB-02B":{"behavior_class":"modbus_tcp","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"modbus-tcp","toolchain":"go"},"FMB-02C":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-02R-A":{"behavior_class":"modbus_rtu","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"modbus-rtu","toolchain":"go"},"FMB-03A":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03B":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03C":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03D":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03E":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03E0":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-03P":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-03R":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-03T":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-04A":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-04B":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-04C":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-04D":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-04K":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-04L":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-04O":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-04S":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-05A":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-05B":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-05C":{"behavior_class":"canonical_semantics","repository_owner":"helianthus-ebusreg","schema":"explicit-issue-execution-class-v1","test_class":"canonical-semantics","toolchain":"go"},"FMB-05D":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-ebus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-05E":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-05F":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-05G":{"behavior_class":"canonical_semantics","repository_owner":"helianthus-ebusreg","schema":"explicit-issue-execution-class-v1","test_class":"canonical-semantics","toolchain":"go"},"FMB-05H":{"behavior_class":"canonical_semantics","repository_owner":"helianthus-ebusreg","schema":"explicit-issue-execution-class-v1","test_class":"canonical-semantics","toolchain":"go"},"FMB-05I":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-05J":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-ebus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-05R":{"behavior_class":"canonical_semantics","repository_owner":"helianthus-ebusreg","schema":"explicit-issue-execution-class-v1","test_class":"canonical-semantics","toolchain":"go"},"FMB-06A":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-06B":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-06C":{"behavior_class":"home_assistant_consumer","repository_owner":"helianthus-ha-integration","schema":"explicit-issue-execution-class-v1","test_class":"home-assistant-consumer","toolchain":"python3-pytest"},"FMB-06D":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-06E":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-06F":{"behavior_class":"home_assistant_consumer","repository_owner":"helianthus-ha-integration","schema":"explicit-issue-execution-class-v1","test_class":"home-assistant-consumer","toolchain":"python3-pytest"},"FMB-06G":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-06H":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-07A":{"behavior_class":"private_binding","repository_owner":"helianthus-eebus-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-07B":{"behavior_class":"private_binding","repository_owner":"helianthus-eebus-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-08A":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-08A-CUSTODY":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-08A-INVENTORY":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-08A-SCOPE":{"behavior_class":"protocol_documentation","repository_owner":"helianthus-docs-modbus","schema":"explicit-issue-execution-class-v1","test_class":"documentation-contract","toolchain":"python3"},"FMB-08B":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08C":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08D":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08E":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08EEBUS":{"behavior_class":"private_binding","repository_owner":"helianthus-eebus-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-08EEBUS-A":{"behavior_class":"private_binding","repository_owner":"helianthus-eebus-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-08F":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08F-SD":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08G-CLOSE":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08G-RED":{"behavior_class":"profile_registry","repository_owner":"helianthus-modbusreg","schema":"explicit-issue-execution-class-v1","test_class":"profile-registry","toolchain":"go"},"FMB-08H":{"behavior_class":"modbus_rtu","repository_owner":"helianthus-modbus","schema":"explicit-issue-execution-class-v1","test_class":"modbus-rtu","toolchain":"go"},"FMB-08I":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-08J":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-08K":{"behavior_class":"gateway_runtime","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-runtime","toolchain":"go"},"FMB-08L":{"behavior_class":"gateway_api","repository_owner":"helianthus-ebusgateway","schema":"explicit-issue-execution-class-v1","test_class":"gateway-api","toolchain":"go"},"FMB-08M":{"behavior_class":"home_assistant_consumer","repository_owner":"helianthus-ha-integration","schema":"explicit-issue-execution-class-v1","test_class":"home-assistant-consumer","toolchain":"python3-pytest"},"FMB-08N":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-08O":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-08Q":{"behavior_class":"release_activation","repository_owner":"helianthus-ha-addon","schema":"explicit-issue-execution-class-v1","test_class":"ha-addon-release-activation","toolchain":"posix-shell+ha-cli"},"FMB-09A":{"behavior_class":"private_binding","repository_owner":"helianthus-matter-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"},"FMB-09B":{"behavior_class":"private_binding","repository_owner":"helianthus-matter-binding-private","schema":"explicit-issue-execution-class-v1","test_class":"private-binding","toolchain":"posix-shell"}},"repository_policies":{"helianthus-docs-ebus":{"behavior_classes":["protocol_documentation"],"toolchains":["python3"]},"helianthus-docs-modbus":{"behavior_classes":["protocol_documentation"],"toolchains":["python3"]},"helianthus-ebusgateway":{"behavior_classes":["gateway_api","gateway_runtime"],"toolchains":["go"]},"helianthus-ebusreg":{"behavior_classes":["canonical_semantics"],"toolchains":["go"]},"helianthus-eebus-binding-private":{"behavior_classes":["private_binding"],"toolchains":["posix-shell"]},"helianthus-execution-plans":{"behavior_classes":["planning_gate"],"toolchains":["python3"]},"helianthus-ha-addon":{"behavior_classes":["release_activation"],"toolchains":["posix-shell+ha-cli"]},"helianthus-ha-integration":{"behavior_classes":["home_assistant_consumer"],"toolchains":["python3-pytest"]},"helianthus-matter-binding-private":{"behavior_classes":["private_binding"],"toolchains":["posix-shell"]},"helianthus-modbus":{"behavior_classes":["modbus_pdu","modbus_tcp","modbus_rtu","gateway_runtime"],"toolchains":["go"]},"helianthus-modbusreg":{"behavior_classes":["profile_registry"],"toolchains":["go"]},"helianthus-org-github":{"behavior_classes":["repository_governance"],"toolchains":["gh+python3"]}},"schema":"explicit-all-issue-execution-class-authority-v1"}`
Failure fixture parity: `{"issue_count":81,"mutation_classes":["omission","duplicate","extra","wrong-code"],"rule":"for-every-issue-negative-fixture-expected-failure-set-and-cardinality-equal-declared-failure-code-set","schema":"declared-failure-negative-fixture-exact-set-v1"}`
Root authority amendments: `{"gate_rule":"PG-ARCHITECTURE-MAP-AMENDMENT-cannot-pass-until-exact-root-invariant-amendments-and-singular-governance-authority-are-present-and-conflicting-rules-are-removed","pending_conflicts":["planned-cross-repo-parallelism-conflicts-with-root-invariant-1","operator-openai-only-mode-conflicts-with-root-invariant-6","root-version-metadata-conflict-v2.5-v2.4","transport-gate-wave-ownership-conflict-wave-2-vs-wave-1.5"],"required_governance_keys":["root_version_metadata","transport_gate_wave_ownership"],"required_invariant_ids":["ROOT-INVARIANT-01","ROOT-INVARIANT-06"],"required_section_headings":["1.2 Repository Dependency Chain","1.2A Workspace Checkout Map","12. INVARIANTS (ALWAYS TRUE)"],"schema":"root-authority-amendment-inventory-v1"}`
Compatibility inventory: `{"component_count":14,"component_output_schemas":{"codex-fresh-reviewer":"codex-fresh-reviewer-compatibility-result-v1","cruise-by-design-reject":"cruise-by-design-reject-compatibility-result-v1","cruise-dev-supervise":"cruise-dev-supervise-compatibility-result-v1","cruise-doc-gate":"cruise-doc-gate-compatibility-result-v1","cruise-merge-gate":"cruise-merge-gate-compatibility-result-v1","cruise-plan":"cruise-plan-compatibility-result-v1","cruise-pr-review-loop":"cruise-pr-review-loop-compatibility-result-v1","cruise-preflight":"cruise-preflight-compatibility-result-v1","cruise-resume":"cruise-resume-compatibility-result-v1","cruise-state-sync":"cruise-state-sync-compatibility-result-v1","cruise-tdd-gate":"cruise-tdd-gate-compatibility-result-v1","cruise-topology":"cruise-topology-compatibility-result-v1","cruise-transport-gate":"cruise-transport-gate-compatibility-result-v1","fresh-adversarial-5round":"fresh-adversarial-5round-compatibility-result-v1"},"components":["cruise-plan","cruise-resume","cruise-state-sync","cruise-preflight","cruise-topology","cruise-doc-gate","cruise-transport-gate","cruise-pr-review-loop","cruise-by-design-reject","fresh-adversarial-5round","codex-fresh-reviewer","cruise-merge-gate","cruise-dev-supervise","cruise-tdd-gate"],"phase_count":8,"phases":["clean_start","resume","pre_cas","post_cas","tdd_ledger_restart","huawei_epoch_restart","huawei_genesis_restart","release_wal_restart"]}`
Schema snapshot: `{"activation_record":"signed-content-addressed-activation-record-v3","external_lock_metadata":"external-lock-metadata-v5","genesis_transport_context":"signed-pre-m8-transport-genesis-context-v1","issue_commitment":"immutable-issue-behavior-commitment-v4","pre_m8_rtu_context":"signed-pre-m8-m2r-dispatch-context-v2","runtime_transport_context":"signed-runtime-transport-condition-context-v4","validation_report":"helianthus-plan-validation-report-v3"}`
Durable generation bundles: `{"activation":"fully-written-and-file-fsynced-triple-directory-fsynced-renamed-and-parent-fsynced-before-one-atomic-signed-pointer-switch","applies_to":["tdd-consumption","huawei-replay","shared-durable-generation-helper"],"bundle_file_order":["ledger.json","head.json","high-water.json"],"bundle_files":{"head":"head.json","high_water":"high-water.json","ledger":"ledger.json"},"head_fields":["schema","lineage_id","generation","sequence","record_head_sha256","ledger_sha256","lineage_state_sha256","predecessor_generation","predecessor_bundle_sha256","predecessor_lineage_state_sha256","committed_at","signer_id","revocation_generation","signature"],"head_schema":"authenticated-generation-head-v3","high_water_fields":["schema","lineage_id","minimum_generation","minimum_sequence","record_head_sha256","ledger_sha256","lineage_state_sha256","predecessor_generation","predecessor_bundle_sha256","predecessor_lineage_state_sha256","committed_at","signer_id","revocation_generation","signature"],"high_water_schema":"authenticated-generation-high-water-v3","in_place_ledger_head_high_water_publication":"forbidden","pointer_fields":["schema","lineage_id","active_generation","active_bundle_sha256","previous_generation","previous_bundle_sha256","committed_at","signer_id","revocation_generation","signature"],"pointer_filename":"active-generation.json","pointer_schema":"signed-generation-bundle-pointer-v1","predecessor_binding_fields":["predecessor_generation","predecessor_bundle_sha256","predecessor_lineage_state_sha256"],"publish_boundaries":["create-generation-temp-directory","write-ledger-file","fsync-ledger-file","write-head-file","fsync-head-file","write-high-water-file","fsync-high-water-file","fsync-generation-temp-directory","rename-generation-directory","fsync-generations-directory","write-pointer-file","fsync-pointer-file","rename-pointer-switch","fsync-store-directory"],"recovery":"validate-complete-genesis-to-active-exact-successor-chain;resume-one-fully-validated-pending-successor-or-atomically-repair-pointer-to-validated-fallback;remove-incomplete-invalid-or-divergent-orphans-under-signed-recovery-record;derive-next-from-effective-active","retention":"retain-active-and-exact-immediate-prior-complete-generation-minimum","schema":"complete-versioned-generation-bundle-triple-v1","successor_record_delta":1}`
Consumed artifact lineage: `{"evidence_fields":["schema","source","artifact","producer_repo","producer_issue","producer_head_oid","producer_tree_oid","artifact_schema","artifact_version","content_digest_sha256","producer_authority_id","producer_signer_id","source_contract_sha256","issued_at","expiry","signer_id","revocation_generation","signature"],"evidence_schema":"signed-consumed-artifact-evidence-v1","external_producers":{"ARCHITECTURE-MAP-AMENDMENT-V1":{"artifact":"authoritative-architecture-map-amendment-v1","producer_issue":"ARCHITECTURE-MAP-AMENDMENT-V1","producer_repo":"root-authority"},"CRUISE-TDD-UNLOCK-FMB-08H":{"artifact":"tdd-unlock-v1","producer_issue":"CRUISE-TDD-UNLOCK-FMB-08H","producer_repo":"helianthus-modbus"},"EEBUS-FRESH-GENESIS-AUTHORITY-V1":{"artifact":"eebus-fresh-genesis-v1","producer_issue":"EEBUS-FRESH-GENESIS-AUTHORITY-V1","producer_repo":"helianthus-eebus-binding-private"},"SKILL-ADAPTER-REGISTRY-V1":{"artifact":"skill-adapter-registry-v1-installed-runtime-attestation","producer_issue":"SKILL-ADAPTER-REGISTRY-V1","producer_repo":"operator-skill-layer"}},"generation":"topology-owned-from-verified-producer-release-evidence-never-consumer-caller-supplied","negative_mutations":["wrong-repo","stale-head","stale-tree","wrong-schema","wrong-version","same-name-substitute","digest-mutation","authority-mutation"],"reference_fields":["source","artifact","edge_kind","condition_ast","producer_repo","producer_issue","artifact_schema","artifact_version","producer_head_field","producer_tree_field","content_digest_field","producer_authority_id","producer_signer_id","verifier_signer_id","evidence_schema","generation_rule","source_contract_sha256"],"schema":"topology-generated-consumed-artifact-lineage-v1","source_contract_validation":"exact-producer-repo-issue-artifact-schema-version-authority-and-signature-identity-plus-current-immutable-HEAD-tree-and-content-digest"}`
Huawei lineage fact identity: `{"identity_rule":"each-fact-id-identifies-exactly-one-observation-and-is-never-reused-across-packets-epochs-generations-or-restarts","lineage_id":"huawei-tancabesti","mapping_fields":["fact_id","claim_id","claim_definition_sha256","observation_id","scope","conclusion","evidence_root_sha256"],"mapping_hash_surfaces":["packet","fact-binding-merkle-custody","durable-ledger","generation-head","generation-high-water","scope-decisions","downstream-scope-commitments"],"reassignment":"reject-any-repeated-fact-id-or-observation-id-even-when-scope-conclusion-and-evidence-root-match","schema":"signed-lineage-wide-huawei-fact-map-v1"}`
Issue acceptance criteria: `{"agents_required":["Unit tests cover the implemented code.","CI green.","Smoke test required: YES/NO."],"criteria_count_per_issue":9,"issue_count":81,"schema":"behavior-derived-acceptance-criteria-v1","source":"immutable-issue-behavior-commitment-v4"}`
Mandatory check sets: `{"candidate_count":95,"candidate_sha256":"1ebd23a81efd6734114d4b34adf0f8e3add5d5926ce386ce4ed2934a459facd7","draft_count":101,"draft_sha256":"a78ff32f1e6838e796663276e772878d8788afdc742e98e163cdc259e872b6c8","must_include":["preflight_and_transport","hashes"]}`
PLAN_LOCK transport boundary: `{"genesis_context_fields":["schema","context_id","validation_phase","consumer_repo","consumer_issue","consumer_head_sha","applicability","epoch","reason_code","blocked_post_lock_artifact_set_sha256","derived_sets","issued_at","expiry","signer_id","revocation_generation","signature"],"genesis_context_schema":"signed-pre-m8-transport-genesis-context-v1","plan_lock_rule":"signed-NOT_APPLICABLE-GENESIS-only-before-M8; no issue-owned output or transitive substitute","post_lock_artifacts":["FMB-08A-CUSTODY","restricted-evidence-custody-v1","FMB-08A-INVENTORY","profile-candidate-inventory-v1","signed-profile-candidate-inventory-v1","FMB-08A-SCOPE","profile-scope-decision-v1","FMB-08A","huawei-fact-clearance-v1","scope-selected-profile-set-v1","fact-cleared-profile-set-v1","executable-profile-set-v1","selected-rtu-profile-set-v1"],"runtime_artifact_keys":["inventory_artifact","profile_scope_artifact","huawei_scope_artifact","source_bindings","rows","rows_sha256","provenance_packet","scope_outcome","fact_outcome"],"runtime_artifact_schemas":["signed-profile-candidate-inventory-v1","profile-scope-decision-v1","huawei-fact-clearance-v1","signed-runtime-transport-condition-context-v4"],"runtime_context_fields":["schema","context_id","validation_phase","consumer_repo","consumer_issue","consumer_head_sha","source_bindings","inventory_artifact","profile_scope_artifact","huawei_scope_artifact","rtu_runtime_outcome","fronius_live_outcome","hardware_scope_outcome","issued_at","expiry","signer_id","revocation_generation","signature"],"runtime_context_schema":"signed-runtime-transport-condition-context-v4","runtime_producers":{"huawei":{"authority_id":"huawei-fact-authority","producer_issue":"FMB-08A","producer_repo":"helianthus-docs-modbus"},"inventory":{"authority_id":"profile-inventory-authority","producer_issue":"FMB-08A-INVENTORY","producer_repo":"helianthus-docs-modbus"},"scope":{"authority_id":"profile-scope-authority","producer_issue":"FMB-08A-SCOPE","producer_repo":"helianthus-docs-modbus"}},"runtime_rule":"M8-and-runtime-require-all-three-actual-signed-source-owned-artifacts","source_binding_fields":["kind","artifact","schema","producer_repo","producer_issue","source_head_sha","epoch","digest_sha256","authority_id","signer_id"]}`
Issue behavior authority: `{"authority_id":"helianthus-independent-issue-behavior-board-v1","epoch":4,"issue_count":81,"merkle_root_sha256":"acc24f86d3c0a60f5a658e6aa96b99b452315aa4fc2ec026ffdb7c61d92ef4ff","signed_payload_sha256":"4c5ee484f65cdaa8b5f0495c4483fa0e205ad95549998f0de74b1bcf5d6cc9ec"}`
Issue contracts: `81 behavior-specific checked copies bound to a distinct immutable Ed25519 authority root; signed applicability evidence is independent`
Catalog rows: `28 EXPECTED_SPECIFICATION rows; no observed execution status without an independent exact-code-HEAD transcript`
Curation-time external blocker snapshot: `{"root_architecture":["authoritative-root-is-not-a-versioned-git-checkout","structured-architecture-authority-block-absent","additive-modbus-checkout-rows-absent","existing-per-protocol-repository-assertions-conflict","structured-root-invariant-authority-block-absent","planned-cross-repo-parallelism-conflicts-with-root-invariant-1","operator-openai-only-mode-conflicts-with-root-invariant-6","root-version-metadata-conflict-v2.5-v2.4","transport-gate-wave-ownership-conflict-wave-2-vs-wave-1.5"],"routing":["gate-resolves-gpt-5.6-luna-medium-not-gpt-5.6-sol-max"],"skill_adapters":["codex-fresh-reviewer","cruise-by-design-reject","cruise-dev-supervise","cruise-doc-gate","cruise-merge-gate","cruise-plan","cruise-pr-review-loop","cruise-preflight","cruise-resume","cruise-state-sync","cruise-tdd-gate","cruise-topology","cruise-transport-gate","fresh-adversarial-5round"],"skill_semantics":["cruise-by-design-reject-declares-Claude-plus-Codex-and-degraded-consensus-in-openai-only","cruise-pr-review-loop-labels-Codex-only-second-reviewer-signal-weaker","fresh-adversarial-5round-openai-only-fresh-independent-component-absent"]}`
<!-- GENERATED_TA15_MODEL_END -->
