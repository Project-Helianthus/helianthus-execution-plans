# Surface targets

Canonical-SHA256: `217dc7da48f733a233d675404f57bae6e69b5d67cb178e8be54b12ec5df341f9`
Depends on: [12-family-targets.md](./12-family-targets.md).
Scope: MCP, GraphQL, Portal, setup, metrics, state and consumers.
Idempotence contract: Re-reading creates no work; fixed fixtures preserve outputs, and lifecycle retries reuse receipts and exact uncertain bytes.
Falsifiability gate: Compare pre-move characterization, ownership, parity and applicable transport evidence; unmet decisions stop the affected node.
Coverage: Canonical section 3; all surface follow-ups.

### Surface destination matrix

This covers native implementation plus MCP, GraphQL/subscriptions, Portal, metrics, setup, state/health, output bindings and evidence in inventory sections 1–4. Exact schemas stay in producer/consumer repositories; this guide does not reproduce 73 tool definitions.

| Surface | Inventory file:line evidence | Target split |
|---|---|---|
| Lifecycle/factories | `GW cmd/gateway/gateway_run_lifecycle.go:32`; `internal/drivermanager/manager.go:149,822` | Host orchestrates typed registrations; drivers own construction/cleanup. Remove each direct start/defer atomically when its managed adapter lands. |
| MCP catalogs | `GW mcp/server_tools.go:3`, `server_construction.go:9`, `modbus_v1.go:106`, `eebus_v1.go:149`; eeBUS `eebusraw/raw_feature_v1.go:21` | Driver contributions replace default eBUS construction. Preserve all inventoried names/classifications: native eBUS/eeBUS/Modbus, semantic PV/storage/EVSE, aliases and conditional availability. Shared router remains host. |
| MCP governance gap | `GW mcp/tool_classification_test.go:112`, `mcp/server.go:751,1182` | Cover conditional families and protocol_specimens explicitly; v1 spelling alone is not stable-contract proof. Experimental capture/state remains host coordination with evidence hooks (`mcp/leaf_promotion_capture.go:15`, `mcp/synchronized_evidence.go:15`). |
| Legacy GraphQL/aliases | `GW graphql/query_root.go:27,51,63,103,168,204,255`; `graphql/vaillant_b503.go:451`; `graphql/mutations.go:427,447,547` | Daemon/build identity stays host; adapter/bus/registry/B503/Vaillant fields and writes are eBUS contributions; promoted zone/DHW/system overlays are eeBUS mappings. Preserve aliases and native write admission. |
| Subscriptions | `GW graphql/subscription_schema.go:81,115`, `graphql/subscriptions.go:1` | Host delivers streams; eBUS contributes broadcasts and thermal events. SemHub event publication is not implied by legacy BroadcastHub. |
| Secure semantic/output APIs | `GW m2mgraphql/handler.go:32,75`, `cmd/gateway/m2m_graphql_runtime.go:1`, `matter/feedv1/server.go:1`, `portalgraphql/handler.go:13,60` | Host owns mTLS/asset limits, feed and catalog/action boundaries; drivers supply immutable accepted projections/actions. These APIs do not count as native northbound emulators. |
| Portal contributions | `GW cmd/gateway/portal_catalog_v1.go:96,100,119`; `portal/contributionv1/validate.go:1`; `portal/catalogv1/admission.go:1` | Replace fixed PV/storage/EVSE/native-member lookup with typed driver source adapters; keep detached validation/quarantine and exact generation/revision withdrawal. |
| Portal native routes | `GW portal/handler.go:956,962,1075,1118`; `portal/explorer.go:1241`; `portal/explorer_ebus_standard.go:1`; `internal/eebusadmin/server.go:220` | eBUS owns registry/scan/B524/B509/standard explorer pages; Modbus owns raw-read/PV/storage data; eeBUS owns pairing/trust/selection. Shared shell/router/auth mounts contributions. |
| Investigation/readiness | `GW portal/handler.go:1087,992`; `cmd/gateway/gateway_runtime_state.go:54` | Capture/diff/session/issue-export substrate and aggregate readiness stay host; drivers provide native provenance and truthful availability. |
| Metrics | `GW bus_observability_store.go:1019,1201`; `admission_metrics.go:16`; `runtime_transport_metrics.go:9`; `semantic_prometheus_text.go:11` | Native counters stay drivers; generic exporter and evaluated semantic metrics stay host. Remove semantic export's dependency on existence of the eBUS store. No invented CAN series; no private endpoint/serial labels. |
| CLI/config | `GW cmd/gateway/gateway_cli.go:42,48,52,86,107,113,152,177`; `eebus_config_flags.go:16`; `config.go:300` | Driver-owned option schemas/validation/meaning behind host parser/storage. Generic labels on legacy polling/cache flags do not make them kernel policy. Preserve protected endpoint-file and secret ingress. |
| Add-on setup | `ha-addon helianthus/config.json:27,57,63,69,80,120`; `helianthus/rootfs/usr/share/helianthus/serial_can_options.py:36` | Packaging consumes driver option contracts, retains safe argv/device mounts. Current serial helper has no CAN options. HA Ingress is optional; Portal is primary setup. |
| State/health | `GW internal/runtimestate/runtimestate.go:68`, `codec.go:189,246`, `hint.go:16`, `revalidate.go:124`; `cmd/gateway/status_provider.go:22,129` | Atomic envelope/GUID and daemon health stay host; eBUS namespace/member hints and revalidation belong to driver. Future namespaces round-trip opaquely. Cached firmware cannot imply live adapter admission. |
| Consumers/docs | `ha-integration custom_components/helianthus/graphql.py:1`, `pv_m2m.py:1`, `eebus_admin.py:324`; `docs-ebus api/mcp.md:81`, `api/graphql.md:1`, `api/modbus-v1-mcp.md:1` | HA consumes accepted upstream contracts; no lifecycle/config ownership transfer. docs-ebus remains evidenced API docs owner until an explicit relocation; native docs in family repos, semantics in docs-semantic. |

Cross-native comparisons (`GW internal/syncevidence/store.go:1`, `internal/promotioncapture/registry.go:1`, `internal/coexistence/boundaries.go:1`) consume detached driver evidence; they neither promote unknown profiles nor acquire native traffic in the kernel.
