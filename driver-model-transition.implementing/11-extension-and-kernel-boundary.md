# Extension and kernel boundary

Canonical-SHA256: `b41d25a1fb88f6c6bb3062b4fd4b5bcc1201abdf4a24999ac54cb9b76d157298`
Depends on: [10-decision-and-registration.md](./10-decision-and-registration.md).
Scope: Contribution hooks and retained kernel responsibilities.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical section 2; DM-G5, DM-G6, DM-HOOKS.

| Hook | Driver supplies | Kernel supplies and enforces |
|---|---|---|
| MCP | Names, schemas, typed handlers, availability, classification, evidence/error mapping | Discovery/dispatch, authenticated context, collision rejection, bounded detached responses; contributions withdraw with their generation |
| Setup | Versioned CLI/config schema, validation, onboarding steps, secret references, migration and applied-state reporting | Parser/config storage and conflict handling, shared standalone Portal onboarding; saved/applied/observed remain distinct |
| Add-on | Driver option meaning and supported device/transport requirements | Add-on owns safe argv, device mounts, packaging and HA embedding; never native qualification or gateway ownership |
| Portal | Versioned descriptors, native pages/data and bounded actions | Contribution registry, generation/revision fences, catalog/action claims, navigation/search/accessibility and visual coherence |
| GraphQL/events | Native fields/types/providers and accepted projection/event producers | Schema/router/subscription delivery, collision detection and shared access boundary |
| Semantics | Which admitted facts/capabilities/packs/projections to publish, qualification, lineage and loss | SemHub identity/publication/control; SemReg owns canonical meaning/validation; no kernel-selected vendor mapping |
| Evidence/state/metrics | Native bytes/provenance, payload codec/migration, native health/counters | Atomic namespace envelope, detached capture coordination, common exporter and process readiness |

Kernel mechanisms that stay are the inventory section 3 responsibilities: process/listener composition and shutdown (`GW cmd/gateway/gateway_run_lifecycle.go:32`); lifecycle coordination (`GW internal/drivermanager/manager.go:149,822`); publication/control (`GW internal/semhub/hub.go:47`, `control.go:368`); HTTP/MCP/GraphQL host (`GW cmd/gateway/gateway_http_control_plane.go:109`, `graphql/builder.go:76`); Portal composer/claims (`GW portal/catalogv1/compose.go:1`, `portalgraphql/handler.go:26`); identity/atomic state envelope (`GW internal/runtimestate/runtimestate.go:79`); secure M2M/consumer feeds (`GW m2mgraphql/handler.go:75`, `matter/feedv1/server.go:1`); shared metrics/readiness/release cache (`GW semantic_prometheus_text.go:11`); investigation/config/onboarding host (`GW portal/handler.go:1087`, `cmd/gateway/gateway_cli.go:36`). Mixed files are split by responsibility; these anchors do not declare whole files neutral.

G5 provides a kernel-owned operator boundary: by default a kernel-owned socket with the same peer-credential check, independent of eeBUS configuration. The existing operator socket is eeBUS-owned and conditional (`GW cmd/gateway/gateway_http_control_plane.go:158-165`, supplied revision-5 evidence in the inventory). Fallback: typed internal service only, with no operator tools; O5 records the selected exposure.

The kernel never frames native traffic, selects vendor profiles, decodes registers, implements protocol FSMs, invents evidence/capabilities, chooses battery aggregation/control policy, or treats cached identity as live admission. It never performs native protocol translation merely because two drivers register. Cross-driver bindings preserve lineage/loss and choose an exact qualified route; their native encoders and policy have explicit owners. Family capture stays in drivers; detached comparisons may use host tooling. Raw eBUS bytes do not enter a generic semantic store under #1021.
