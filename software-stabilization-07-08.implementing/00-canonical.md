# Helianthus: the 0.7 → 0.8 → 1.0 software program

Board mandate, 4 September 2026. Working document for execution from current GitHub state; it is not a workflow engine and grants no additional authority. The product name remains provisional.

## Intended outcome

**0.7:** close and integrate already-started software, with a common semantic architecture, complete north–south flows, a usable and extensible Portal, coherent public surfaces, and the gateway rename. Follow this with the adversarial Daybreak Blue audit, remediation of findings, and exhaustive testing on real hardware. The release is not accepted before these results.

**0.8:** move suitable descriptions from code into a descriptive language/IR and deterministic generation while preserving behavior verified in 0.7. Repeat Daybreak Blue, remediation, and exhaustive hardware testing. Reducing approximately 1.2 million lines to 200,000 is a Board aspiration, not a verified measurement or a criterion permitting functionality to be removed.

**1.0:** the destination remains the complete discussed feature set. It is not redefined as a pilot or minimal intersection among protocols. Reconcile additional 1.0 release criteria after 0.8, without adding speculative functionality now.

New hardware and future kernel/FlexPort components belong to a separate private project in the dedicated private hardware repository. Software uses existing adapters, without FlexPort. Matter/eeBUS software outputs do not move to that hardware repository and must not create a private dependency for the public build.

## Verified baseline

GitHub snapshot: 2026-09-04 20:16:40 UTC, 27 repositories inspected, 39 open issues and 4 open PRs. This is a dated inventory; every intervention rechecks remote HEAD and current acceptance.

The native audit verified **25/25 GitHub checks successful at the HEADs of 9 repositories**. It did not rerun local suites, issue a new review verdict, or test hardware. Add-on 0.6.56 pins gateway `a759efd7f72a099288f1fc2b7cf20236d37cfa0b`, while inspected gateway main is `16903f04ee7be107fd8770eec23860e40a06f420`.

| Domain | Exists | Remains for integration |
|---|---|---|
| Vaillant/eBUS | Transport, registry, providers, MCP, GraphQL/HA, eBUS DriverManager | Open regressions, semantic migration, and UX; VRC Explorer remains an active independent product |
| SunSpec/Fronius | TCP acquisition, qualification/refresh, observed GEN24 profile, PV MCP and GraphQL/HA | Convergence in semreg, observability, and physical qualification on the exact profile |
| Huawei | Separate offline SmartLogger, EMMA, and S-Dongle identity/inventory mechanisms | Qualification evidence, connected acquisition, capabilities, and projections; EMMA identity does not mean complete support |
| Growatt Modbus/BMS, Tesla Gen3/legacy, OutBack | Native profiles and decoders, some injectable MCPs | Normal gateway acquisition, lifecycle, semantics, and consumers |
| Gree CAN and Growatt CAN | Receive-only transport, Gree candidates/mappings, Growatt LV V1.04 | Gateway composition and projections; V1.05 is not equivalent to V1.04 |
| eeBUS | SHIP/SPINE runtime, registry, pairing, and limited semantic promotion | Discovery/pending pairing, full semantic integration, and distinct output binding |
| Semantic Layer | Existing eBUS/PV designs and donations; semreg still absent | Protocol-neutral contract and complete implementation for started domains |
| Portal | Existing UI and product paths | New design and extensibility through driver contributions |
| Matter / eeBUS output | Matter is a placeholder; binding intent in plans | Independent mapping, implementation, and conformance for each output |
| Prometheus | Predominantly eBUS instrumentation and useful native sources | Common runtime/transport and semantic exporter, bounded labels, no scrape I/O |

“Module implemented,” “connected into the binary,” “validated offline,” and “physically verified” are different states.

## The three 0.7 design decisions

1. **IOKit-inspired Semantic Layer.** Equipment may have several sources and perspectives: communications, physical, electrical, hydraulic, sensors, energy, and firmware. Identity, services/capabilities, relationships, and versioned contracts retain provenance, exact quantities, time, freshness, conflict, and unknown. The semantic kernel imports no protocol/vendor/gateway packages. Matching depends on model, version, features, and configuration; it does not become universal scanning.
2. **North–south flows.** Upward: native observation → qualification → facts/capabilities → projections. Downward: intent → authority/capability/preconditions/deadline → exact driver and endpoint/generation → native operation → ACK/readback/outcome → public state. Timeout, ACK, and state confirmation remain distinct. Reuse DriverManager and existing native mechanisms. Autonomous control/optimization is not added to this program.
3. **Extensible, driver-provided Portal.** Drivers contribute versioned descriptions of values, groups, relationships, diagnostics, actions, and specific components where required. The Portal owns navigation, search, perspectives, accessibility, and visual coherence. It does not decode registers or decide semantics itself. The extensibility demonstration adds a fixture driver and its UI without a new central vendor switch.

Matter is anchored to `AryaHassanli/connectedhomeip:dm-0.9-1.7`, SHA `29b4768a513cf566011ab8cd60df1bc495204953` (ballot 0.9, draft 1.7, upstream PR #73842). The semantic matrix uses the latest verified accessible eeBUS corpus per component—SHIP, SPINE, and each use case—without inventing a single “latest eeBUS” version. Normative versions in the authenticated eeBUS area remain an open verification point; this does not block independent bug fixes.

## Execution order

| Wave | Delivery | Dependencies and boundary |
|---|---|---|
| A — start now | Issue reconciliation; governance; VR940f #148; existing SunSpec/add-on/HA probes | Independent repositories, separate worktrees; every issue receives exact-HEAD review |
| B | Semantic, north–south, and Portal design; plan #93/PR #94 reconciliation | Correct the stale claim that DriverManager does not exist; select the public contract owner |
| C | Semreg and migration of existing contracts; connect all started drivers/profiles | B designs, native evidence, and compatibility; no new universal semantics in ebusreg |
| D | Native + semantic MCP, GraphQL, Portal, HA through GraphQL, Prometheus, eeBUS/Matter outputs | C contracts, mapping, and explicit projection loss per target; independent public build |
| E | Rename `helianthus-ebusgateway` → `helianthus-gateway`, BOM/release candidate, complete offline acceptance | Migrate imports/modules/CI/docs/pins; preserve/test HA IDs, pairing/trust, and persistent state |
| F | Daybreak Blue on the 0.7 candidate, remediation and re-verification; exhaustive hardware matrix | The audit does not certify devices. Physical tests start only after confirmation of concrete operations |
| G — 0.8 | LOC inventory, descriptive language/IR, codegen, and migration with comparator | After 0.7 acceptance; runtime/FSM/I/O/concurrency do not move blindly into a DSL |
| H — 0.8 | Daybreak Blue, remediation, repeat hardware matrix, and release | Functional parity with 0.7, real reduction measurements, and physical acceptance |

Waves are dependency groups, not promises to finish overnight. Every cross-repository package is split into issues in its owning repository before implementation. A single responsible party integrates the result; merges do not execute the plan automatically.

## Explicit dependencies and retained historical requirements

- `STD-01` is owned by docs-eeBUS and fixes the normative corpus before mappings in `INT-04`/`INT-12` are frozen. Conceptual design and independent bugs can proceed in the meantime.
- `SEMREG-BOOTSTRAP`, after ownership selection in `INT-04`, creates the public repository, license, self-contained AGENTS, CI, and import/documentation contracts. It precedes `INT-05` implementation; north–south design can continue in parallel.
- Native packages close only their provider capabilities and probes. `INT-07` consumes those artifacts and owns gateway acquisition; `INT-08` owns public surfaces; `INT-17` validates full composition. There is no reverse dependency from provider to consumer.
- `LEGACY-PERSIST`, `LEGACY-IDENTITY`, and `LEGACY-MUX` retain assertions from plans #27/#23/#30. The exact criteria are in `92-retained-acceptance.md` in the public guide. Reconcile them with current code: a historical NO_GO is neither PASS nor automatic proof of a remaining bug. Offline work precedes packaging; physical rows are in `INT-20`, before release.
- Rename `INT-14` waits for `INT-10/11/12/13/15`: Portal, metrics, bindings, and HA reach freeze; then inventory and integrate affected PRs, coordinate remote/module/import/pin migration, and verify consumers. Do not move the name under active branches. Forward fix or rollback is explicit in the issue before cutover.

## Cruise-control rules

Board → Executive Director (Astra High) → Delivery Leads (Sol High) → Specialists (Terra Medium/High). The independent auditor reports to the Board. Anthropic mapping and the three operating modes are in the AGENTS proposal. Daybreak Blue is the named adversarial specialist required for releases, separate from the organizational audit.

Continue with the next issue whose dependencies are satisfied, using GitHub, merged guides, and repository contracts. Do not wait for GitHub Projects to fix an independent bug. For changes in the same repository, serialize integration or use disjoint worktrees and recheck the base before merge.

Real P0–P2 findings block; P3/P4 are fixed, recorded, or justified without ritual rounds. Apply CI/docs/conformance/smoke according to the repository and an independent fresh `NO_BLOCKING_FINDINGS` verdict on the full SHA. Do not treat a reviewer’s silence or timer expiry as positive review.

Product persistent state remains necessary: restart, migration, continuity, identity/pairing/trust, and recovery. The prohibition on plan authorization engines does not prohibit product persistence.

An issue closes as **resolved** only with acceptance evidence. Duplicates/supersessions identify the successor; abandoned work in deprecated repositories closes as **not planned**, preserving history. Hardware-only or evidence-blocked work does not close as completed software. Gateway PR #917 remains excluded under the prior Board decision until an explicit request to resume it.

## Release acceptance

`HARDWARE_TEST_READY`: real configuration and connected acquisition in the binary composition, fixture/replay through the full path, semantics and consumers, degraded/restart/reconnect/cleanup behavior, CI and review at the exact BOM, and an executable hardware procedure. An injectable MCP alone does not meet the criterion.

`QUALIFICATION_TEST_READY`: a bounded experiment capable of obtaining missing native evidence; the product remains semantically incomplete until qualification and verified implementation. Such products stay visible in scope and do not disappear from the matrix.

0.7/0.8 hardware acceptance must enumerate every claimed model/profile/firmware and operation, normal and degraded flows, reconnect/restart, freshness, identity, authorized control, timeout/indeterminate, and recovery. A missing device is reported as a blocker; it does not pass by fixture. Do not claim coverage of every possible physical combination in a family.

0.8 measures handwritten code, generated code, tests, fixtures, vendor/dependencies, documentation, and RE artifacts separately. Line reduction preserves functionality, performance, and evidence; deleting tests is not productization.

## State at drafting

Audits and proposals are the starting point; they are not evidence of implementation or physical testing. Independent issues can proceed before semantic design is completed. Concrete results for every PR are reported from GitHub; this section is not a runtime registry.
