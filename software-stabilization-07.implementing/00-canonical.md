# Helianthus 0.7 software stabilization

Board mandate, revised 20 September 2026. This active guide records the 0.7
software outcome and is not a workflow engine or additional authorization.
The later [0.8 declarative guide](../software-declarative-08.locked/00-canonical.md)
is a separate future program. It may start only after 0.7 is accepted.

## Outcome and boundary

0.7 closes and integrates already-started software: protocol-native evidence and
qualification, the existing public Semantic Registry contracts, north--south
composition, a usable extensible Portal, public bindings, coherent observability,
the gateway rename, and existing product paths. `helianthus-semreg` is the
existing public owner of protocol-neutral canonical types and semantic contracts;
those types do not move into the gateway. `helianthus-ebusreg` remains eBUS-native.

The gateway composes generic semantic services and supplies extension hooks for
drivers to contribute Portal, MCP, GraphQL, metrics, diagnostics and other public
surfaces. It does not retain driver-specific protocol FSMs, decoders or electrical
semantics as common gateway policy. Each native north/south driver owns its
protocol-native framing, qualification, profile selection, decoder and FSM logic;
the gateway dispatches through explicit contracts and preserves native evidence.

There is no compatibility promise for mappable legacy behavior before v1.0: migrate
it to the selected 0.7 public contract with a clear cutover. Unmappable daemon or
adapter runtime behavior remains outside electrical SemReg types, but is in 0.7
when it is required for the product runtime. New kernel/FlexPort hardware stays in
the inactive private hardware program and is not a 0.7 dependency.

## Priority public-proof actions

These actions are selected in the `PUBLIC-01` through `PUBLIC-08` order ahead of
ordinary backlog where their owning repositories are otherwise ready. They are
public maintenance and proof work, not a grant application or outreach program.

1. `PUBLIC-01`: make the gateway README and organization profile truthful about
   the present public SemReg ownership and current product boundary.
2. `PUBLIC-02`: prove a clean anonymous clone can resolve dependencies, build and
   test without a token, `.netrc`, helper or private cache; correct the quickstart
   only after recording the result.
3. `PUBLIC-03`: publish a maturity matrix covering model, firmware, function,
   specification, decoder, integration, consumer, offline evidence and physical
   evidence, and distinguish `main` from HA add-on packaging pins.
4. `PUBLIC-04`: clarify public/private and licensing boundaries: independent
   public Matter and eeBUS work, inactive private hardware, CC0 knowledge versus
   upstream/vendor rights, and a CLA only where one already exists. It changes no
   license.
5. `PUBLIC-05`: prove the existing PV SunSpec path through SemReg to MCP,
   GraphQL and Portal with positive and negative exact-revision examples; it adds
   no simulator.
6. `PUBLIC-06`: provide the first contributor/profile demonstration quick path.
7. `PUBLIC-07`: make the eebusreg README useful to a public user and contributor.
8. `PUBLIC-08`: make temporary upstream-fork badges and active-branch status clear.

## 0.7 architecture and release order

The semantic kernel remains protocol-, vendor- and gateway-free. Upward flow is
native observation -> qualification -> facts and capabilities -> projections.
Downward flow is intent -> authority, capability and preconditions -> exact driver
and endpoint -> native operation -> ACK/readback/outcome -> public state. ACK,
timeout and state confirmation remain distinct. Driver-provided Portal descriptions
are versioned; the Portal owns navigation, search, accessibility and coherence, not
register decoding or semantic decisions. Matter and eeBUS bindings are independent
projections with explicit mapping loss.

| Wave | Delivery | Boundary |
|---|---|---|
| A | Priority public-proof actions, existing regressions and native evidence | No new product family or private dependency |
| B | Existing SemReg contracts, native-driver contracts and gateway composition | Native FSM/decoder ownership stays with the driver; SemReg owns canonical types |
| C | MCP, GraphQL, Portal, HA, metrics, eeBUS and Matter bindings | Each target declares provenance and projection loss |
| D | Gateway rename, exact candidate packaging and offline acceptance | Preserve consumer IDs, state, pairing/trust and pins through the cutover |
| E | Daybreak Blue review, remediation and real-hardware acceptance | The final candidate must pass review and every required physical row |

Accepted 0.7 after Wave E is the external prerequisite for the future 0.8 guide.
The guide is not a 0.7 package, dependency or deliverable.

## Acceptance and hard stops

`HARDWARE_TEST_READY` requires integrated binary composition, end-to-end
fixture/replay coverage, semantics and consumers, degraded/restart/reconnect/cleanup
behavior, exact-BOM CI and review, and an operator-run procedure. An injectable MCP
alone is insufficient. `T01..T88` is **DEFERRED AND NOT RUN** until authorized
hardware validation; it is mandatory before 0.7.0 and cannot be replaced by
offline fixtures. P01--P06 are not deferred.

The conservative B503 decision remains unknown/deny-enable. The related 525
research remains deferred; do not infer enablement from adjacent evidence.

Release acceptance is tied to the exact candidate BOM. Daybreak Blue reviews the
candidate, valid findings are remediated, and exhaustive physical validation covers
each claimed model/profile/firmware and operation, normal and degraded paths,
reconnect/restart, freshness, identity, authorized control, indeterminate outcomes
and recovery. A missing device remains a blocker. No later declarative work can
substitute for this evidence.

Any code, configuration, dependency or package fix discovered during Daybreak or
hardware validation invalidates the earlier candidate evidence. The changed final
BOM requires a fresh Daybreak review and affected hardware and conformance
revalidation before `INT-21` may publish it. Only the BOM covered by those final
results is releasable.

## Dated baseline and working rule

The 4 September 2026 inventory and early semantic-draft links are historical
comparators only. Before repository work, read current GitHub state and the merged
guide, then use the owning repository's ordinary issue, branch, validation, review
and merge workflow. This guide neither creates work nor reports live completion.

Matter is anchored to `AryaHassanli/connectedhomeip:dm-0.9-1.7`, SHA `29b4768a513cf566011ab8cd60df1bc495204953` (ballot 0.9, draft 1.7, upstream PR #73842).
The applicable eeBUS normative corpus is pinned by `STD-01` before affected mapping is frozen.
