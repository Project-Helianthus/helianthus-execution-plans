# Semantic Fact Graph And Integration

Canonical-SHA256: `c60f6dfd111bd02af78a28b858f4a9770cd1c4ffa00da837a96c05ec13c91f90`

Depends on:
`10-platform-taxonomy-and-boundaries.md`; eBUS and eeBUS runtimes may implement
this incrementally.

Scope:
Defines canonical semantic facts, provenance, status, conflict handling, and
long-run cross-runtime integration.

Idempotence contract:
Adding fact provenance must not require immediate consumer rollout. MCP may
expose richer facts before GraphQL, Portal, or Home Assistant consume them.

Falsifiability gate:
Given two runtimes reporting the same conceptual field, the semantic layer must
show provenance and either choose a value by explicit policy or mark the field
as conflicted.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

Coverage:
Covers M7, M8, M8.5, and the semantic portions of M9.

## Semantic Fact Contract

Every semantic fact must be traceable to native evidence.

Minimum fact metadata:

- runtime identifier;
- transport;
- base protocol;
- profile;
- device profile when known;
- native evidence reference;
- confidence;
- status.
- promotion dossier reference when promoted.

The implementation may choose exact type names later, but it must not expose
stable consumer values without this information available internally.

Recovered dirty documentation is not evidence by itself and is not a fact.
Publishable evidence IDs are required before material can be treated as
supported. If a publishable evidence ID is absent, the material remains only a
candidate or hypothesis and must carry a falsifier.

M7 facts are draft candidate facts only. They do not promote leaves and they do
not drive GraphQL, Portal, Home Assistant, raw writes, or command routing.
Feature graph completeness and reconnect durability are proven by MSP-055/M6
before semantic candidates can depend on them; they are not G17 evidence.

## Status Vocabulary

Use this conservative vocabulary until a locked plan refines it:

- `RAW_ONLY`: native evidence exists but no semantic claim is made.
- `CANDIDATE`: semantic projection is plausible but not stable.
- `PROMOTED`: field is stable enough for GraphQL and consumers.
- `CONFLICTED`: multiple runtimes disagree and the conflict is represented.
- `WITHHELD`: evidence exists but semantic exposure is intentionally blocked.

Candidate, conflicted, and withheld values must not become Home Assistant
entities.

Negative results are terminal withheld states until retested:

- `NO_SIGNAL`
- `CLOUD_ONLY`
- `CONFLICT`
- `NOT_TESTED`

They may be visible only on raw/debug surfaces with reason code, evidence
bundle, and retest trigger.

## Integration Rule

Native protocols do not speak to each other by raw translation. The gateway
integrates systems through semantic facts and intents.

Example:

```text
solar/inverter runtime -> excess energy fact
HVAC runtime -> DHW thermal capacity fact
semantic policy -> increase DHW target intent
runtime command router -> native eBUS or eeBUS write
```

The command is sent in the target runtime's native language. The semantic layer
does not synthesize raw Modbus registers into eBUS frames or vice versa.

## Conflict Handling

Conflicts are first-class output, not hidden exceptions.

Examples:

- eBUS and eeBUS report different target temperatures for the same zone.
- SunSPEC and Huawei private maps disagree on inverter state.
- Classic eBUS and a vendor profile disagree on a decoded field.

Until precedence is explicit, the semantic fact must be `CONFLICTED` or
`WITHHELD`.

## Consumer Gates

- MCP may expose raw, candidate, conflicted, and withheld states.
- GraphQL receives only stable schemas after MCP convergence.
- Portal may expose raw and candidate states as a reverse-engineering
  workbench.
- Home Assistant receives only promoted semantic entities and diagnostics.

No consumer work may start until M8.5 locks the relevant leaf promotion
dossier. Each dossier must include source-family identity, comparator
pass/fail parameters, coexistence evidence, replay regeneration, terminal
negative-state handling, and public-safe redaction metadata. R00-L public
evidence commitments use random opaque IDs and never raw paths, timestamps,
sizes, byte counts, deterministic IDs, or raw hashes.
