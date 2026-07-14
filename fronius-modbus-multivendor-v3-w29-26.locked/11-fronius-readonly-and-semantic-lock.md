# Fronius read-only vertical and semantic lock

Canonical-SHA256: `d01dcf33f46878f30c3a627e7e037a69660d55ab8d23ee8294923261b3979ee6`

Depends on: `10-architecture-and-repo-boundaries.md`; M1 TCP and M2 profile contracts.
Scope: Fronius phase-1 evidence, fixtures, profile detection, gateway raw MCP, live hardware proof, canonical PV lock, and public consumer order.
Idempotence contract: Repeating fixture replay, detection, polling, or promotion with the same inputs produces the same profile outcome and canonical observation without duplicate endpoints, entities, or counters.
Falsifiability gate: Reject the vertical if fixtures and live reads disagree without an explicit applicability explanation, a write is emitted, raw evidence cannot reproduce a decode, GraphQL or a downstream consumer precedes lock of the tested semantic MCP, or recovery cannot disable the endpoint.
Coverage: Decisions D03-D06, D11-D12; issues M3-M5; risks R01-R03, R07-R08.

## Claim register

**Proven**

- The operator has identified a real Fronius lab target for later read-only testing.
- Fronius phase 1 is limited by operator decision to Modbus TCP reads.

**Hypothesis**

- Applicable SunSpec models, with an overlay only if qualified Fronius-specific facts
  require one, will cover the first useful PV semantic slice.

**Unknown**

- Active unit topology, model-chain variants, optional meter/battery visibility, firmware
  behavior, and scale representations until M3 evidence and M4 live proof complete.

## Evidence and fixtures

M3 starts with source inventory, not code. The evidence packet records document identity,
version, acquisition date, license or permitted use, model and firmware applicability,
standard versus vendor-private status, and unresolved conflicts. The plan intentionally
does not embed register addresses or conclusions.

Fixtures are minimal, sanitized, and attributable. Each fixture includes endpoint/unit
identity, profile candidates, model and firmware evidence, raw responses, expected decode
metadata, `sample_id`, `poll_generation_id`, `dependency_set_id`, complete member identity,
each physical request/range's endpoint/unit/function/table/zero-based PDU offset/word count
and `wire_response_id`, and each dependent observation's linked `logical_view_id`, logical
offset/count, and exact slice offset/count within the wire response,
expected detector outcome, and a provenance record. FC03-versus-FC04 fixtures keep the
same numeric offset distinct. Documentary one-based-versus-zero-based fixtures record and
verify normalization. Mutation cases cover truncation, bad lengths, illegal-address
responses, codec signedness/scale, opposing multi-register word orders, applicable opposing
intra-word byte orders, string byte traversal and left/right/NUL/space padding, mixed
generations, missing dependency members, unsupported versions, competing profiles,
no-match, a dependency changing between responses, unequal overlapping reads that must
replay exact words/provenance for each logical view, and cross-unit, cross-table,
cross-authorization, cross-generation, or deadline-incompatible reads that must not
coalesce. Codec version and the selected
order/packing descriptor remain in provenance. The torn-read case must either pass the
profile's bounded coherence validation and re-read or emit no observation. A fixture cannot claim hardware support; it proves
deterministic code behavior only and leaves the profile default-disabled
`experimental_opt_in`.

FMV3-M3-01 is the public docs companion for M3-02 and M3-03, with explicit companion
metadata and ancestry. M3-02 first implements the minimal applicable SunSpec standard-family
slice in `helianthus-modbusreg`. FMV3-M3-03 then uses that public evidence and M3-02
conformance to record `STANDARD_ONLY` when the required Fronius slice is fully standard, or
`OVERLAY_REQUIRED` only for qualified vendor-specific facts. Both dispositions retain
Fronius fixtures and live-qualification scope, exercise every applicable codec order and
packing case, remain read-only, publish the evidence/disposition, and pass conformance CI
before unblocking M4. `STANDARD_ONLY` creates no implementation commit and no empty or
invented overlay. Only `OVERLAY_REQUIRED` invokes `TDD_RED_IF_OVERLAY_REQUIRED`; an admitted overlay states why the standard family is insufficient, which
model/firmware/gateway evidence admits it, and how conflicts fail closed.

## Gateway raw-MCP phase

Gateway configuration names endpoint, transport, unit candidates, poll budgets, detector
policy, credentials reference if needed, and an explicit enable flag or experimental
opt-in. Gateway package `internal/modbusadapter` implements the existing protocol-agnostic adapter
interface, creates one endpoint owner, and rejects duplicate ownership. It is the only
gateway package allowed to import `helianthus-modbus` or `helianthus-modbusreg`. Gateway
core tests use a fake adapter/interface; separate adapter integration tests exercise the
real runtime and registry. Configuration validation occurs before activation; secrets are
never returned by MCP or logs.

Raw MCP ships before canonical semantics and provides only bounded, authorized operations:

- list configured endpoint and detector state without secrets;
- perform or replay bounded read-only ranges within allowlists and budgets;
- inspect profile candidates and activation lifecycle, selection/qualification evidence,
  source validity/timestamps, endpoint/unit/function/table/zero-based-offset/count,
  sample/poll/dependency identity, physical `wire_response_id`, linked per-observation
  `logical_view_id`/slice identity, versions, and unknowns;
- retrieve sanitized raw/provenance references used by a decode;
- show endpoint health, queue, timeout, reconnect, and source-observation gap diagnostics.

No MCP route accepts a write function, arbitrary unbounded range, arbitrary endpoint, or
private material path. Replay and live output use the same response envelope so tests can
compare them without pretending replay is hardware proof.

## Required live gate

M4 hardware classification is `hardware_required`. The record identifies software
versions, target model/firmware/profile versions, endpoint mode, test time, sanitized
topology, and exact commands or harness version. It proves:

1. deterministic detection and a bounded probe transcript;
2. repeated raw read and fixture parity for selected facts;
3. fair/coalesced polling within resource and deadline limits;
4. disconnect, timeout, cancellation, reconnect, and re-detection behavior;
5. source observation stop/resume and unchanged sample/generation/dependency,
   wire-response, and logical-view/slice identity without mixed-generation or
   incoherent/torn decode;
6. no write request and no unexpected regression to existing gateway traffic;
7. add-on disable and restoration of the previous gateway/add-on pair.

FMV3-M4-04 records exactly `GO`, `NO_GO`, or `STOP`; completion is not gate success.
FMV3-M4-05 packages the exact outcome and sanitized evidence whether or not it is GO. M5
raw/semantic work starts only when M4-04 is `GO` and M4-05 is complete. `NO_GO` or `STOP`
is retained as honest evidence and leaves every M5 issue blocked. Raw fixture development
and bounded diagnostic MCP may continue, but GraphQL, Portal, HA, and private bindings
cannot consume candidate meaning.

## Semantic lock and promotion

After sanitized live evidence, `helianthus-docs-ebus` publishes and merges the versioned,
protocol-neutral PV contract in FMV3-M5-02. Only then may `helianthus-ebusreg` semantic
implementation start in FMV3-M5-01. FMV3-M5-04 depends on both and implements the candidate
Fronius-to-canonical mapping and semantic MCP before lock. Its golden and live Fronius tests
run one exact candidate version, preserve physical wire-response and per-observation logical
view/slice provenance, reject mixed or incoherent samples, and prove raw-to-canonical
traceability. The code contract solely owns canonical quality,
freshness deadlines/transitions, unavailable
behavior, stable device/source identity, quantities, counter rollover/reset, provenance,
capability enumeration, and compatibility. Source validity/timestamps are inputs, not
canonical policy. A value absent from evidence remains Unknown.

The semantic-lock issue FMV3-M5-03 in `helianthus-execution-plans` depends on FMV3-M5-04 and
reviews that exact golden- and live-tested semantic MCP version, schema, fixtures, live
record, mappings, evidence, quality/freshness behavior, and compatibility. It records
exactly `GO`, `NO_GO`, or `STOP`; completion alone is not success. `GO` pins the tested
public contract version for consumers. `NO_GO` or `STOP` leaves raw and candidate semantic
MCP active, returns specific remediation work, and blocks FMV3-M5-09 plus every later
consumer descendant. It never gates FMV3-M5-04 and cannot be bypassed by directly adding
GraphQL fields.

Candidate proof, lock, and promotion order is strict:

1. FMV3-M5-04 gateway mapping and candidate semantic MCP depend on FMV3-M5-01/M5-02,
   propagate sample/generation/dependency plus physical wire-response and per-observation
   logical-view/slice identity, reject mixed or incoherent samples, and prove
   source-to-canonical traceability with golden and live tests. This step is outside
   `CG-M5-SEMANTIC-GO` and creates no GraphQL or consumer contract.
2. FMV3-M5-03 reviews and locks that exact tested candidate only when it records explicit
   `GO`. `NO_GO` or `STOP` preserves the candidate for remediation but permits no promotion.
3. FMV3-M5-09 is exactly one public `helianthus-docs-ebus` issue/PR after M5-03 lock GO and
   before GraphQL implementation. It follows FMV3-M5-02 in the serialized docs lane and
   publishes the exact `PUBLIC_GRAPHQL_M2M_V1` schema projection,
   external access/security/channel contract, compatibility/versioning, credential lifecycle,
   and recovery contract.
4. FMV3-M5-05 depends on FMV3-M5-09, carries its companion metadata, reaches parity with
   semantic MCP, and implements exactly one externally routable machine-to-machine contract
   for a separately deployed service client. Credential-bearing external use requires the
   documented authenticated confidential channel with verified server identity before
   credentials are sent; plaintext external access and untrusted server identity fail closed.
   Tests from that external context cover endpoint reachability, noninteractive authn/authz,
   least privilege, bounded polling/rate/resource behavior, credential provisioning,
   rotation, revocation, disable, and recovery without prescribing the channel/auth mechanism,
   weakening security, adding subscriptions, or exposing raw registers.
5. A separate serialized gateway Portal issue delivers two surfaces: the semantic PV view
   remains GraphQL-only, while an authenticated and authorized raw diagnostics/register
   explorer reuses the bounded raw MCP service contract with the same read allowlists,
   endpoint/function/range and rate/resource budgets, secret redaction, and audit evidence.
   Raw registers do not enter semantic GraphQL and no Portal package imports Modbus.
6. Home Assistant starts only after Portal and consumes GraphQL with stable IDs.
7. The add-on packages exact compatible versions and proves both Portal surfaces, raw and
   semantic MCP, GraphQL, HA, independent disable, restart, and recovery. It repeats the
   exact public machine-to-machine contract test from a separately deployed external
   service context, including plaintext rejection, untrusted-server-identity rejection,
   credential lifecycle, and bounded resource behavior.
8. Only after that packaged public rollout may private eeBUS consume exactly the tested
   contract and independent Matter work start.

The mapper commits only profile-coherent complete dependency sets from one poll generation
and carries their sample/response identity while using `ebusreg` transitions rather than
gateway-defined canonical timers. Before publication,
candidates and schema-less images may be restored. After publication, schema and IDs remain;
recovery uses compatible code or additive correction, and disabled data is unavailable.
No schema-less image may replace a published schema.

## Stop/go criteria

GO requires green RED-first tests, TCP transport gate, fixture mutations, documentation and
licensing clearance, explicit M4/M5 conditional GO outcomes where applicable, real-device
M4 smoke, raw/canonical traceability, and zero unresolved blocker findings. `NO_GO` and
`STOP` preserve evidence but unlock nothing. STOP applies to ambiguous detection, unsupported firmware, unexplained
fixture/live mismatch, missing provenance, resource-limit failure, any write path, secret
exposure, unqualified automatic activation, torn/partial-refresh corruption, or failed
disable/rollback.
