# Semantic-draft reconciliation

This is a dated reconciliation of the early semantic bridge draft and issue #93.
It preserves traceability, not a claim that any historical SHA, issue state or
acceptance item is current.

The 0.7 scope retains existing public SemReg contracts, protocol-native evidence,
driver contracts, gateway composition, Portal and public bindings. `helianthus-semreg`
is an existing public repository and owns protocol-neutral canonical types. The
gateway owns generic composition and public extension hooks; native drivers own
protocol/profile FSMs, decoders and evidence. `helianthus-ebusreg` is not a
cross-protocol semantic owner.

Historical draft clauses about an IR, code generation, line-count reduction or a
second Daybreak/physical-validation cycle have moved to the separate future
[0.8 guide](../software-declarative-08.locked/00-canonical.md). Their only 0.7
boundary is the release prerequisite: 0.8 starts after accepted 0.7. They are not
0.7 deliverables, packages or release criteria.

The retained runtime, identity, state and live-evidence assertions are recorded in
[92-retained-acceptance.md](./92-retained-acceptance.md). Reconcile all historical
claims against current owner evidence before treating them as implementation facts.
