# Semantic Fact Graph And Integration

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

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

Coverage:
Covers M4, M8, and the semantic portions of M9-M10.

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

The implementation may choose exact type names later, but it must not expose
stable consumer values without this information available internally.

## Status Vocabulary

Use this conservative vocabulary until a locked plan refines it:

- `RAW_ONLY`: native evidence exists but no semantic claim is made.
- `CANDIDATE`: semantic projection is plausible but not stable.
- `PROMOTED`: field is stable enough for GraphQL and consumers.
- `CONFLICTED`: multiple runtimes disagree and the conflict is represented.
- `WITHHELD`: evidence exists but semantic exposure is intentionally blocked.

Candidate, conflicted, and withheld values must not become Home Assistant
entities.

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
