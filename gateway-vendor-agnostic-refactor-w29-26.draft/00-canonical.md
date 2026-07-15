# Gateway Vendor-Agnostic Refactor — Canonical Draft

- Draft directory: `gateway-vendor-agnostic-refactor-w29-26.draft/`
- Draft classification: `OBJECTIVES_ONLY / NON_EXECUTABLE / NOT_LOCK_READY`
- Package shape: intentionally incomplete; this directory contains only `00-canonical.md`
- Status: canonical objective draft; no issue map, milestone map, dependency graph, implementation design, adversarial lock or validator result exists yet
- Prepared: 2026-07-16
- Requested future surface: a fresh `/goal` session orchestrated by Ultra, first to complete the plan and only later to execute it under separate authorization
- Authority boundary: apart from publication of this draft explicitly requested on 2026-07-16, this document authorizes plan completion only. It does not, by itself, authorize code changes, further publication, repository renames, deployment, or execution of the resulting plan.

## 1. Purpose

Produce a complete, independently understandable execution plan for refactoring the current eBUS-oriented Helianthus stack into a protocol- and vendor-agnostic gateway platform before Modbus support begins.

The future session must be able to use this document without access to the conversation that produced it. It must verify the current repository state before completing the plan and must treat the target architecture below as a planning hypothesis to refine, not as an already locked design.

The combined plan-completion and refactor effort is intended for a bounded autonomous run of approximately 7–8 active days after the eEBUS implementation has finished and stabilized.

## 2. Primary objective

Transform the `helianthus-ebusgo`–`helianthus-ebusreg`–`helianthus-ebusgateway` stack into a maintainable multi-runtime gateway whose shared core is independent of eBUS, Vaillant and any other protocol or vendor, while preserving existing eBUS and completed eEBUS behavior and making the subsequent addition of Modbus driver families possible without another structural redesign of the gateway or its northbound surfaces.

## 3. Activation conditions and time envelope

The work must not start until all of the following are true:

- the active eEBUS implementation has reached its declared completion state;
- its public contracts and compatibility baseline are stable enough to be used as read-only evidence;
- the three code repositories in scope have clean, reproducible baselines;
- the current host test suites pass independently, without relying on workspace replacement through `go.work`;
- no conflicting architecture migration is active in the same repositories.

Operator scheduling intent:

- 18–20 July 2026: activate the goal and complete the execution plan after eEBUS is ready;
- 21–26 July 2026: six-day target window for the refactor itself;
- 7–8 active days in total: desired autonomous `/goal` timebox for plan completion plus refactor.

The calendar is a scheduling constraint, not a substitute for completion evidence. Expiry of the timebox must not convert an incomplete or unverified refactor into success. If activation occurs late, the plan must report the resulting schedule risk rather than silently reduce validation or expand scope.

## 4. Scope

Code repositories in scope:

- `helianthus-ebusgo`;
- `helianthus-ebusreg`;
- `helianthus-ebusgateway`.

Documentation scope:

- durable platform, driver, semantic, lifecycle, compatibility and TinyGo contracts related to those repositories;
- reconciliation with the existing multi-runtime platform contracts;
- selection of one canonical owner for every cross-protocol normative contract, without assuming in advance that a new documentation repository must be created.

The completed eEBUS implementation is a compatibility baseline and architectural validation input. Its repository is not in modification scope. If compatibility requires an out-of-scope change, the plan must identify the dependency and stop instead of extending its own scope.

## 5. Explicit exclusions

The following are not deliverables of this refactor:

- implementation or extension of Modbus, SunSpec, Fronius, Huawei, Growatt or any other Modbus profile;
- implementation of GREE VRF, Viessmann, Resol VBus, LG, Daikin, Zigbee, Salus, Matter bridges or any other future protocol integration;
- changes to VRC Explorer;
- PIC firmware work;
- ESP32 or other board bring-up;
- consumer feature expansion or Home Assistant redesign;
- new semantic product features unrelated to the confirmed cleanup findings;
- dynamic third-party plugin installation or hot unloading;
- repository, module, binary or add-on renaming unless separately authorized after compatibility and migration impact are established.

These future directions are extensibility pressures only. They must constrain the architecture against protocol or vendor lock-in, but they must not become implementation work or acceptance dependencies for this objective.

## 6. Audit baseline

The initial audit used the following public heads:

- `helianthus-ebusgateway`: `46fc6b475a133610b47997e52409afe9e052c969`;
- `helianthus-ebusreg`: `16466b27eaaf50af346b7d5d789755ff2d7b1288`;
- `helianthus-ebusgo`: `f9919f4b10071b7fbb8114498a241302e43b8771`;
- `helianthus-docs-ebus` contract baseline: `e1962c0dc83836b0dbea129d198c7be6bea738da` on `origin/main`.

At that snapshot, standalone host builds and tests were green for all three code repositories. Race validation was green where run. This evidence does not prove TinyGo behavior, 32-bit portability, hardware behavior, all concurrency properties or semantic parity outside the covered tests. The future planning session must refresh the heads and record any drift before relying on these findings.

## 7. Executive audit verdict

The required work is not a cosmetic split of `cmd/gateway/main.go`. The main problem is that runtime composition, eBUS/Vaillant assumptions, semantic ownership, northbound adaptation, lifecycle and operational policy are entangled across repository and package boundaries.

The current host implementation has no confirmed P0 at the audited heads, but it contains confirmed correctness defects, false portability signals and architectural coupling that must be addressed before a third protocol family is introduced.

The refactor must therefore combine:

- correction of confirmed defects;
- behavior-preserving containment of the existing eBUS runtime;
- extraction of stable protocol-neutral contracts;
- reduction of navigational and lifecycle complexity;
- honest portability boundaries;
- durable documentation and executable compatibility evidence.

## 8. Audit criteria to preserve in the completed plan

Every plan objective and later finding must be falsifiable and must identify the evidence that proves closure.

The completed plan must evaluate at least these dimensions:

1. **Navigability and cohesion** — entrypoints, large files and long functions are inspection triggers; size alone is not a defect. Responsibilities must be independently discoverable by a human maintainer.
2. **Ownership and dependency direction** — transport, protocol, vendor profile, native registry, semantic core and northbound responsibilities must each have one owner and acyclic dependencies.
3. **Lifecycle and concurrency** — startup, readiness, degraded operation, cancellation, shutdown, resource ownership and error propagation must be explicit and testable.
4. **Correctness and silent failure** — invalid state, partial results and failed projections must not appear successful or silently erase valid prior state.
5. **Determinism and boundedness** — caches, queues, retries, coalescing, event ordering, backpressure and shared state must have explicit limits and ownership.
6. **Operation policy and trust boundaries** — mutability, danger, authorization, idempotency and raw access decisions must not vary accidentally by northbound surface. Deployment-owned authentication must be distinguished from in-process policy.
7. **Compatibility** — public eBUS behavior, completed eEBUS integration, GraphQL, MCP semantic and raw surfaces, Portal, metrics and existing consumer contracts must have parity evidence.
8. **Portability** — host Go, 32-bit Go, TinyGo compile portability, TinyGo behavioral portability and board support are separate claims.
9. **Documentation truth** — normative contracts must have one canonical owner, explicit versioning and evidence that implementation and documentation describe the same behavior.

## 9. Findings that the execution plan must address

### 9.1 Confirmed correctness and contract defects

- Duplicate eBUS B5/16 subscriptions can produce duplicate decode and publication of the same event.
- Failure to build a canonical projection can leave a device apparently registered while its semantic projections are silently absent.
- The legacy ENH initialization path loses the distinction between confirmed and unconfirmed initialization, while the gateway can report success.
- Current TinyGo gates can pass without exercising relevant code, and real 32-bit/TinyGo checks expose an integer overflow in code that the smoke gate does not reach.
- Operation metadata and safety policy are interpreted differently by the registry/router, MCP and GraphQL paths. This is a contract and security gate, not proof of an exploitable bypass.

### 9.2 Confirmed architectural and maintainability debt

- The gateway configuration and runtime surface expose concrete eBUS and `ebusreg` types, while the default composition is Vaillant-specific.
- The gateway entrypoint and major semantic, GraphQL and MCP files contain multiple unrelated responsibilities and are difficult to navigate or test independently.
- Semantic contracts and DTO transformations are duplicated across GraphQL, MCP and Portal, creating a material drift risk even though output divergence has not yet been demonstrated.
- HTTP serving, shutdown and background activity do not have a single explicit lifecycle owner, and some server failures are not propagated to the application outcome.
- Registry and router APIs expose unbounded or externally mutable state, including an invocation cache without an explicit bound and data that can escape lock protection.
- Discovery paths lose useful failure classification and can return partial results without a sufficiently explicit diagnostic contract.
- `ebusgo` mixes low-level protocol concerns with gateway/northbound terminology, contains competing codec and FSM paths, and carries procedural review history in production code.

### 9.3 Conditional risks and hypotheses requiring proof

- Absence of in-process authentication is not by itself a confirmed vulnerability if authentication and TLS are owned by a trusted deployment edge. The trust boundary must be documented and tested.
- Different B524 bounds may represent semantic limits versus conservative discovery limits; drift must not be declared without establishing the intended scope.
- The active and newer telegram FSMs are not proven equivalent, and their apparent payload-limit difference is not automatically a current runtime bug.
- GraphQL, MCP and Portal are not proven to return divergent semantic values merely because their mappings are duplicated.
- Mutable state exposure and unbounded structures are confirmed contract hazards, but must not be described as observed races or memory leaks without a reproducer.

## 10. Objectives for the completed execution plan

1. **Preserve a verified behavioral baseline.** Establish reproducible compatibility evidence for eBUS and the completed eEBUS integration before structural changes, covering semantic and raw surfaces, operations, lifecycle-visible behavior and existing consumers.

2. **Close confirmed correctness defects.** Eliminate duplicate event publication, hidden projection failure, false initialization success, inconsistent operation policy and false-green portability validation without introducing unrelated behavior changes.

3. **Make repository responsibilities explicit.** Keep eBUS transport and protocol mechanics in `ebusgo`, eBUS-native identity/profile/registry knowledge in `ebusreg`, and shared orchestration, semantic integration and northbound policy in the gateway platform.

4. **Create a stable southbound driver boundary.** Define a protocol-neutral, versionable contract through which complete runtime drivers describe identity and capabilities, participate in lifecycle, publish native evidence and semantic candidates, expose supported operations and report health.

5. **Support deterministic driver availability.** Make built-in drivers available through the common contract without protocol- or vendor-specific branches in the shared gateway entrypoint or semantic core. The execution plan must select and justify the mechanism; this brief does not equate registration with runtime dynamic loading.

6. **Establish one protocol-independent semantic authority.** Define stable identities, facts, provenance, quality, freshness, revisions, conflict states, non-destructive merge and command routing independently of any native bus representation.

7. **Create selective northbound boundaries.** Ensure GraphQL, MCP, Portal, Home Assistant-facing contracts, future Matter/eeBUS roles and Prometheus-style telemetry consume only the capabilities they require. Raw protocol evidence must remain a distinct, controlled surface for diagnostics and reverse engineering.

8. **Make lifecycle deterministic.** Give runtime instances and the gateway explicit, testable readiness, degraded state, failure propagation, cancellation, bounded shutdown and resource ownership semantics suitable for multiple simultaneous driver instances.

9. **Reduce human navigation cost.** Leave the executable entrypoint primarily responsible for composition, make each major responsibility independently locatable and testable, remove obsolete scaffolding and move procedural archaeology out of production logic while preserving useful design rationale.

10. **Define an honest TinyGo boundary.** Identify exactly which contracts and eBUS core functions are portable, which are host-only and which remain unsupported; replace smoke-only claims with validation that reaches the declared portable behavior.

11. **Align durable documentation.** Publish or amend normative contracts for driver roles, semantic ownership, provenance, freshness, conflicts, operations, lifecycle, compatibility, raw access, registration and portability under one canonical documentation owner per concern.

12. **Demonstrate readiness for the next protocol family.** Show that a future Modbus runtime and its independent profiles can be added through the resulting contracts without changing the common semantic model, northbound contracts or gateway bootstrap structure. No Modbus implementation is required for this proof.

13. **Prepare, but do not assume, the gateway identity migration.** Determine the compatibility and publication conditions under which `ebusgateway` can later become the generic `gateway`; do not perform the repository/module/binary rename merely to claim architectural completion.

## 11. Provisional target architecture

The execution plan must refine and either confirm or replace this provisional model while preserving its separation principles:

```text
protocol engine
  owns native transport, framing, timing and base-protocol mechanics

runtime driver
  composes the protocol engine with native discovery, identity, profiles,
  observations, operations and raw evidence

gateway host
  owns driver supervision, shared lifecycle, configuration, health aggregation
  and deterministic availability of configured runtime instances

semantic core
  owns canonical facts, identity linking, provenance, promotion, freshness,
  conflicts, non-destructive merge and common operation policy

northbound adapters
  consume selective semantic query, event, intent and telemetry capabilities
  without importing native protocol or vendor types

raw evidence surface
  remains separate from promoted semantics and is exposed only through
  explicitly granted diagnostic and reverse-engineering capabilities
```

Architectural invariants:

- the common contract must be dependency-leaf and import no gateway runtime, GraphQL, MCP, Vaillant, eBUS or future protocol implementation;
- an eBUS driver means the complete runtime composition of `ebusgo` and `ebusreg` responsibilities, not `ebusreg` alone;
- drivers own native decode, discovery and candidate production; the shared platform owns canonical integration and conflict policy;
- northbound roles are not assumed to share one universal CRUD interface;
- eEBUS southbound control and a possible eeBUS northbound bridge are different roles;
- raw access remains available but does not bypass common safety and trust policy;
- registration must be deterministic and observable, but its implementation mechanism remains a decision for the completed plan;
- the target must not depend on dynamic in-process plugins, hot unloading or a specific repository split unless those choices are separately justified.

## 12. TinyGo portability contract to be refined

The full gateway host is not a TinyGo target.

The completed plan must define three distinct evidence levels:

1. **Compile-portable** — the declared packages and contracts compile for explicit 32-bit and TinyGo targets.
2. **Behavior-portable** — the same protocol vectors, state-machine behavior and error outcomes pass on host Go and the declared TinyGo target.
3. **Board-supported** — real I/O, timing, memory, scheduling and hardware behavior are proven on a named board.

Only the first two levels are objectives of this refactor. Board support is explicitly deferred.

The portable surface is expected to include protocol-neutral value contracts and the bounded eBUS wire/codec/state-machine core where evidence permits. Networking, HTTP, GraphQL, MCP, persistent host services and gateway orchestration remain host-only unless separately proven.

Every support claim must identify packages, target, toolchain version, exercised API surface and resource limits. A successful empty-link or blank-import smoke build is not sufficient evidence.

## 13. Documentation objectives

The completed execution plan must reconcile the new refactor with the existing multi-runtime platform model rather than create a competing vocabulary.

Durable contracts must cover:

- layer and ownership taxonomy;
- southbound driver responsibilities and compatibility;
- native evidence versus semantic candidate versus promoted fact;
- semantic identity, provenance, quality, freshness, revision and conflict behavior;
- operations, intent, safety, idempotency and trust decisions;
- lifecycle, readiness, degraded state and shutdown;
- northbound capability boundaries and raw-access separation;
- deterministic driver registration and capability discovery;
- public compatibility and deprecation;
- TinyGo and 32-bit portability claims;
- the future gateway identity/rename boundary.

The plan must name one canonical owner for each normative contract and remove or demote contradictory duplicate normative text. It must not preselect a new documentation repository solely because the current repository name is eBUS-specific.

## 14. Objective-level completion outcomes

The resulting execution plan may declare the refactor complete only when it requires evidence that:

- all three repositories build and validate independently at the published heads;
- the confirmed correctness defects are closed and protected by regression evidence;
- the shared gateway core has no required dependency on eBUS/Vaillant native types or concrete runtime objects;
- the eBUS runtime operates through the common driver boundary while preserving its established behavior;
- completed eEBUS behavior remains compatible without an out-of-scope source change;
- semantic ownership is unique and protocol-independent;
- all existing northbound and raw surfaces have explicit parity or compatibility evidence;
- lifecycle, failure propagation, readiness, degraded state and shutdown have falsifiable contracts;
- caches, queues and shared state used by the common runtime have explicit ownership and bounds;
- registration of available drivers is deterministic and does not require vendor logic in the common gateway path;
- the declared TinyGo/32-bit subset passes meaningful reachability and behavior validation, while host-only and unsupported surfaces are documented honestly;
- documentation ownership is unambiguous and normative contracts match the verified implementation;
- a future independent protocol family can satisfy the driver and semantic contracts without structural changes to the gateway core or northbound consumers;
- remaining hypotheses and conditional risks are explicitly classified rather than silently presented as resolved defects.
