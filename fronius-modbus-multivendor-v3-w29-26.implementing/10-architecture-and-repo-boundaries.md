# Architecture and repository boundaries

## Layer ownership

The dependency direction remains transport -> profile registry -> gateway adapter ->
canonical semantics -> public consumers -> private output bindings.

| Layer | Repository | Owns | Does not own |
|---|---|---|---|
| Organization governance | `Project-Helianthus/.github` | Repository policy and creation | Protocol or product code |
| Modbus protocol/runtime | `Project-Helianthus/helianthus-modbus` | PDU types, codecs, TCP/RTU, endpoint lifecycle, bounds, recovery | Vendor profiles or canonical PV meaning |
| Profile registry | `Project-Helianthus/helianthus-modbusreg` | Profiles, codecs, detection, observations, provenance, fixtures | Sockets, gateway lifecycle, canonical PV IDs |
| Gateway adapter | `Project-Helianthus/helianthus-ebusgateway` | Runtime composition, raw MCP, semantic MCP, GraphQL, Portal | Modbus framing or private binding protocols |
| Canonical semantics | `Project-Helianthus/helianthus-ebusreg` | Protocol-independent PV identities, quantities, quality, freshness | Transport or vendor detection |
| HA consumer | `Project-Helianthus/helianthus-ha-integration` | Stable GraphQL consumption and entities | Raw registers or profile logic |
| Add-on | `Project-Helianthus/helianthus-ha-addon` | Configuration, packaging, health, rollback | API or profile semantics |
| Public knowledge | `Project-Helianthus/helianthus-docs-ebus` | Contracts, evidence, mappings, retained unknowns | Runtime enforcement |
| Private eeBUS output | `Project-Helianthus/helianthus-eebus-binding-private` | Generic eeBUS output from the public M2M API | Modbus input, canonical meaning, vendor detection |
| Private Matter output | `Project-Helianthus/helianthus-matter-binding-private` | Generic Matter output from the public M2M API | Modbus input, canonical meaning, vendor detection |
| Plan record | `Project-Helianthus/helianthus-execution-plans` | Cross-repository IDs, DAG, boundaries, and stop decisions | Product execution or runtime proof |

There is one shared profile repository, not a repository per inverter vendor. The
private repositories are generic bindings and remain downstream of public, stable
contracts.

## Import direction

Allowed high-level imports follow ownership:

```text
helianthus-modbusreg -> helianthus-modbus
helianthus-ebusgateway -> helianthus-modbusreg + helianthus-modbus
helianthus-ebusgateway -> helianthus-ebusreg
helianthus-ha-integration -> public GraphQL
private bindings -> PUBLIC_GRAPHQL_M2M_V1
```

Forbidden directions include:

- public repositories importing either private binding;
- `helianthus-modbus` importing a vendor profile or canonical semantic package;
- `helianthus-modbusreg` owning sockets, serial ports, or gateway lifecycle;
- private bindings importing Modbus, registry internals, or gateway internals;
- Home Assistant consuming raw registers or unstable MCP schemas;
- the execution-plan repository acting as a product execution service or change broker.

## Contract flow

Contract work follows docs -> producer -> consumer:

1. public companion documentation establishes the ID, version, ownership, and
   compatibility intent;
2. the producer implements interfaces and types and proves them with repository-local
   fixtures and conformance tests;
3. consumers pin a compatible producer/API version and prove compatibility in their own
   tests;
4. durable findings return to public documentation.

The plan DAG records this order. It does not replace normal code-repository issue and PR
workflow.

## Modbus runtime boundary

`helianthus-modbus` serves all profile families. TCP is the first Fronius acquisition
path. RTU uses the same public runtime contract but remains disabled and experimental
until `RTU_PHYSICAL_QUALIFICATION_V1` version 1 is satisfied by physical evidence in the
runtime repository. Missing RTU hardware does not block TCP-sufficient Fronius work.

The retained M1 contract identifiers are:

- `OPAQUE_RUNTIME_ACQUISITION_V1` version 1;
- `helianthus.modbus.opaque-runtime-acquisition` version 1;
- `published_attempt_v1` schema version 1;
- `helianthus.fmv3-m1-06-conformance-report.v3` version 3.

Their implementation detail and proof remain in `helianthus-modbus` and
`helianthus-modbusreg`, not in this plan.

## Fronius transport-neutral boundary

`FMV3-M3-03` may use Modbus TCP traces and fixtures to decide Fronius phase-1
applicability. It may not make Fronius profile behavior depend on TCP-specific types or
endpoint state. The two allowed outcomes are:

- `STANDARD_ONLY`: minimal SunSpec is sufficient, so no vendor overlay is added;
- `OVERLAY_REQUIRED`: evidence requires a read-only Fronius overlay implemented against
  the transport-neutral registry/runtime boundary.

The completion record retains schema `helianthus.fmv3-m3-03-completion.v2` version 2.
Code-repository interfaces, compile-time boundaries, golden fixtures, and conformance
tests prove the result. This plan validates only the ownership and DAG facts.

## Semantic promotion boundary

Raw and profile observations precede canonical semantics. Canonical PV documentation and
types precede candidate semantic MCP. A separate plan decision locks the tested semantic
MCP version. `PUBLIC_GRAPHQL_M2M_V1` documentation then precedes GraphQL implementation,
Portal, Home Assistant, add-on packaging, and private bindings.

Consumers do not drive semantic shape. Published IDs remain stable across rollback;
disabled data becomes unavailable rather than being silently remapped.

## Plan-repository behavior

All validation is local and read-only. The validator parses YAML, checks graph and mirror
consistency, and exits. It has no network client, no repository checkout logic, and no
product-source scanner. CI performs that same validation and unit tests in one read-only
job. A merge here creates no issue, branch, PR, repository, deployment, or follow-up job.
