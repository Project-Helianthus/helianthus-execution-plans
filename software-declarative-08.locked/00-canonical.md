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

1. `INT-18` designs the descriptive IR, comparator, target repository split and
   measured reduction. It inventories handwritten, generated, test, fixture,
   vendor/dependency, documentation and RE lines separately. Deleting tests or
   functionality is not reduction.
2. `INT-22` applies the approved migration under native-driver ownership and proves
   parity using repository-owned fixtures, contract tests and comparators.
3. `INT-23` runs Daybreak Blue on the transformed exact candidate and remediates
   valid findings.
4. `INT-24` runs exhaustive authorized real-hardware validation and publishes 0.8
   only with the validated measured reduction.

The target packages must specify each driver/profile's selected native owner before
implementation. No new protocol or product feature is created merely to exercise
the IR. 0.8 repeats the Daybreak and hardware gates because 0.7 evidence cannot
certify transformed code.

## Hard stops

This guide remains `locked` until accepted 0.7. It does not start a compiler,
repository migration, physical test, live-device action or hardware purchase.
T01..T88 and all required physical rows are performed only with their action-time
authorization and remain mandatory for the final 0.8 candidate. FlexPort and
kernel work remain private and inactive, outside this program.

