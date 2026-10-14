# Decision and registration

Canonical-SHA256: `b41d25a1fb88f6c6bb3062b4fd4b5bcc1201abdf4a24999ac54cb9b76d157298`
Depends on: None; binding operator decision and Phase A inventory.
Scope: Decision, identity, direction and managed lifecycle.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical sections 1–2; DM-G5.

## 1. Binding decision, verbatim

The following is the complete supplied [reference-decision.md](./reference-decision.md), including its heading.

## Architectural direction (operator, 2026-10-14)

The gateway is a host for protocol drivers, not a protocol implementation. Before 1.0, every protocol-specific element moves into its driver, and the gateway offers only the abilities a driver needs:

- register itself as **northbound**, **southbound** or **both**;
- extend the MCP surface with driver-specific tools;
- present its setup elements through hooks (configuration and onboarding);
- extend the Portal;
- extend the semantic layer with the projections the driver chooses to publish.

eBUS is a driver of the gateway, not part of it. Today it is southbound only; it can become northbound once native eBUS without latency exists (a real UART on the Raspberry Pi, not a Wi-Fi adapter, whose latency is too high). eeBUS is both northbound and southbound. Modbus can be both: a virtual smart meter exposed on Modbus, an EV charging station exposed to a photovoltaic inverter, or a Gree LV CAN battery pack converted to LV RS-485 with a given flavour. CAN can be both: an RS-485 battery pack exposed on CAN to an inverter that does not know it, a Growatt CAN battery presented as Pylontech CAN, or several JKBMS packs aggregated into one virtual Growatt CAN battery.

The direction is reached across 0.7 and 0.8 and must hold before 1.0. The first slices are INT-06 (gateway #1024 hub, G5 runtime control with the managed-runtime contract) and INT-07 (provider registry); the eBUS raw-evidence stores (gateway #1021) move under the eBUS driver as part of that program.

## 2. Contract implied by the decision

A driver is a registered protocol owner: native transport integration, endpoint/session lifecycle, qualification/profile selection, framing/decoding/FSMs, evidence acquisition, chosen projections and contributed surfaces. Libraries remain in their native repositories; moving gateway bindings into a driver does not copy transport or registry implementations into the kernel. Pending O8: compiled typed gateway packages by default; descriptor v1 belongs to the gateway contract, hook schemas to DM-HOOKS. Splits/dynamic loading need a later decision. A directory move alone does not establish ownership.

Northbound means native server/emulator behavior toward an external protocol peer; southbound means acquisition/native operations toward a device. `both` declares supported roles, not permission to forward traffic or assurance that every example is implemented. HTTP/MCP/GraphQL, HA and Matter consumer feeds are separate output bindings. Direction is explicit per registered instance, constrained by its native descriptor and qualified configuration.

DM-DOC publishes proposed descriptor v1 before DM-G5 implements it. Amendments use doc-gate companions (docs merge first or together). Fields: stable DriverID, direction, enabled/configured disposition, NativeContractRef/version, factory/lifecycle adapter, owned source set, and versioned optional contribution hooks. Instance DriverIDs are distinct. Registration validates ownership/collisions and freezes descriptors without endpoint I/O. SourceID, asset/binding IDs, source epoch, driver generation, transport generation, desired revision, catalog revision and operation/publication sequences remain distinct. Unknown IDs/unavailable hooks fail explicitly; controls require executable handlers.

G4 is the semantic publication seam; G5 supplies registration and managed lifecycle over the existing DriverManager. Desired intent is durable; observed readiness/admission is current evidence. List/get are cache-only. Start/stop/restart validate trusted authority, deadline, principal-scoped idempotency key and optimistic revision, then atomically persist a receipt before native work. Replay returns that receipt before comparing a newer revision; NO_OP does not reset backoff, repair a generation or increment desired revision. One native retry/drain owner remains per runtime.

Prepare/Activate/Abort and Admit/FenceWithdrawal/Stop adapt the proposed `runtime-driver-provider-contract-v1.md` interfaces, not a newly asserted public SPI. Before native open, admit/journal the source and complete the epoch barrier. Only correlated readiness opens admission. Stop closes callback/I/O authority first, tracks semantic withdrawal/reprojection separately from native drain/close, and completes only when both obligations succeed. Missing close proof quarantines replacement. Late callbacks and staged commits cannot restore old authority. Process shutdown cleans resources without overwriting durable operator intent. Shell, health and other drivers remain available when one driver is stopped or broken.

G4 retains one source per asset, per-asset publication cursors, separate HubSeq and bounded overflow/resync. `ReadAdmitted && Settled` gates public reads; internal `Inspect` cannot escape through public surfaces. An accepted withdrawal with failed reprojection differs from a rejected/uncertain withdrawal; Resettle cannot reopen the latter. Durable recovery needs original envelopes, snapshots/cursors/index and pending work, not just EpochJournal digests. G4's legacy identity/epoch exceptions remain until each accepted family migration replaces them. Proposed, pending O6: G5 starts with `ebus.primary`, an explicit lifecycle-only adapter with no invented thermal asset; synthetic qualified publishers prove nonempty fences/recovery.
