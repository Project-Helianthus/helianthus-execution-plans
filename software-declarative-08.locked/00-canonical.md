# Helianthus 0.8 declarative software program

Board mandate, revised 20 September 2026. This is an inert future guide, not a
workflow engine or authority. It is tracked publicly with the
[0.8 software project](https://github.com/orgs/Project-Helianthus/projects/4).
It begins only after acceptance of the active
[0.7 stabilization program](../software-stabilization-07.implementing/00-canonical.md).
The project link is planning context, not a public-build dependency.

## Objective

0.8 reduces repeated handwritten driver behavior through a descriptive IR and
deterministic code generation while preserving 0.7 behavior. The work must cover
all driver-specific and protocol FSM logic currently accumulated in the gateway,
including eBUS and every other started native north/south driver. That logic moves
to its owning native driver/profile package. The gateway is left with generic
semantic composition and versioned extension hooks for drivers to contribute
Portal, MCP, GraphQL, metrics, diagnostics and other bindings.

`helianthus-semreg` remains the owner of protocol-neutral canonical types and
semantic contracts. The IR/codegen work does not move SemReg types into the
gateway, flatten protocol evidence, or make `helianthus-ebusreg` a cross-protocol
semantic owner. A driver retains native framing, profile qualification, decoder,
FSM and evidence; generated code is accepted only where behavior, failure handling,
provenance and performance remain demonstrably equivalent.

## Work and acceptance

1. `DRIVER-EXTRACTION-01` defines and delivers the native-owner extraction and
   parity work for each started driver/profile before the declarative layer is
   applied. It leaves the gateway with only generic composition and extension hooks.
2. `INT-18` retains its original outcome: design and implement the descriptive IR,
   deterministic generation, comparator and measured reduction. It inventories
   handwritten, generated, test, fixture, vendor/dependency, documentation and RE
   lines separately. Deleting tests or functionality is not reduction.
3. `INT-22` retains its original outcome: Daybreak Blue reviews the transformed
   exact candidate and valid findings are remediated.
4. `INT-23` retains its original outcome: exhaustive authorized real-hardware
   validation of that exact candidate.
5. `INT-24` retains its original outcome: publish 0.8 only with the validated
   measured reduction and the final covered BOM.

The target packages must specify each driver/profile's selected native owner before
implementation. No new protocol or product feature is created merely to exercise
the IR. 0.8 repeats the Daybreak and hardware gates because 0.7 evidence cannot
certify transformed code.

Any code, configuration, dependency or package fix during Daybreak or hardware
validation invalidates earlier candidate evidence. The changed final BOM requires
a fresh Daybreak review and affected hardware and conformance revalidation before
`INT-24` publishes it. Only the BOM covered by those final results is releasable.

## Hard stops

This guide remains `locked` until accepted 0.7. It does not start a compiler,
repository migration, physical test, live-device action or hardware purchase.
T01..T88 and all required physical rows are performed only with their action-time
authorization and remain mandatory for the final 0.8 candidate. FlexPort and
kernel work remain private and inactive, outside this program.
