# eeBUS VR940f Raw-First Track

Canonical-SHA256: `f2392801ccdc00dfeaaf48166582cbbea42770a4d14998ca082b2624b1e9e18e`

Depends on:
`10-platform-taxonomy-and-boundaries.md`, the gateway `0.4.0` baseline
described in `11-ebus-040-baseline-and-profile-split.md`, and the control
plane in `14-execution-roadmap-issues-and-gates.md`.

Scope:
Defines the raw-first eeBUS track for the existing VR940f/myVaillant gateway.
The first delivery is raw SHIP/SPINE runtime visibility and read-only MCP, not
semantic parity and not consumer rollout.

Idempotence contract:
Initial eeBUS work is additive. It must not change existing eBUS MCP,
GraphQL, Portal, Home Assistant, transport, registry, or semantic behavior.

Falsifiability gate:
The operator can pair/bind the VR940f in the lab, inspect SHIP/SPINE sessions,
services, topology, raw evidence, trust state, and deterministic snapshots
through MCP, then restart and verify stable raw state without promoting a
single semantic field.

Routing and completion-token authority is exclusively 92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json.

Coverage:
Covers recovery reconciliation, M3 completion, M3.5 through M8.5 for eeBUS raw
runtime, MCP, evidence, candidate facts, and leaf-promotion locking.

## Repository And Boundary

Create `helianthus-eebusreg` with module path
`github.com/Project-Helianthus/helianthus-eebusreg`. The bootstrap repo does
not import `github.com/enbility/eebus-go`. The first M3 internal facade spike
pins `github.com/enbility/eebus-go v0.7.0`.

The repo name is allowed only after an ADR states that the repo is raw eeBUS
runtime and evidence plumbing, not a semantic registry fork. Public package and
export names must use `eebusruntime`, `eebusraw`, or `eebusevidence`. Public
API names must not use `registry`, `reg`, `projection`, or `semantic`.

AD-DOCS-01 makes the code-repo documentation boundary absolute:
`helianthus-eebusreg` and clean-main branches contain no `docs/` directory and
own no substantive protocol, architecture, API, harness, test, or user
documentation. Only exact minimal README entry/status/build pointers and
concise Go package metadata comments may remain, linking only to
manifest-state `active` pages or pre-existing stable landing pages.

Only `helianthus-eebusreg/internal/...` may directly import
`github.com/enbility/*`, SHIP, or SPINE packages. Direct imports from gateway,
shared packages, and public `helianthus-eebusreg` packages are forbidden.
Exported public API signatures must not expose `enbility`, SHIP, or SPINE
types. Transitive dependency on `enbility/*` hidden behind the internal facade
is allowed.

The public API extractor implementation lives in
`helianthus-eebusreg/internal/apiboundary`. Its schema and specification live
in `helianthus-docs-eebus/api`; the normalized manifest is a CI artifact, never
code-local documentation. Version 1 normalization is deterministic over
package, symbol, type, and signature with stable ordering and no formatting,
internal, or unexported noise.

## Runtime API

The pre-MSP-055 public runtime API is intentionally internal or read-only.
The first public lifecycle facade is disabled by default and read-only:

- `Start(ctx)`
- `Shutdown()`
- `Snapshot()`
- `PairingState()`

Pairing and trust mutation primitives, including `RegisterRemoteSKI()`,
`UnregisterRemoteSKI()`, and `SetPairingWindow(enabled bool)`, may exist only
behind internal/admin-gated interfaces until M4.5 freezes trust, pairing,
admin-local, restore, and quarantine semantics. No gateway, MCP, or public Go
package may call or expose those mutation methods before the M4/M4.5 security
gate proves local-admin binding, first-trust race behavior, idempotency,
fingerprint confirmation, audit events, store generation checks, and rollback.

Snapshots include local SKI, visible services, paired services, sessions,
remote devices, entities, features, usecase claims, pairing state, raw evidence
references, degraded states, and timestamps. Snapshot fields are raw eeBUS
facts; they do not imply semantic promotion.

## Feasibility Gates Before Gateway Import

M3 uses a disposable proof-only credential store. It proves library and lab
feasibility, not production trust safety.

Required M3 proof artifacts:

- facade spike compiles against pinned `eebus-go v0.7.0` with module JSON and
  checksum evidence;
- local and actual build-container proof with `GOWORK=off`,
  `GOTOOLCHAIN=local`, no local `replace`, `go mod tidy -diff`,
  `go mod verify`, `go list -m all`, SBOM/checksum diff, `go test ./...`, and
  build;
- no `go` or `toolchain` directive exceeds the fleet/container version;
- source import scan and exported API check prove the `enbility/*` boundary;
- HA add-on runtime proof uses a LAN peer outside the add-on namespace, not a
  same-container shortcut;
- mDNS/Avahi/DBus positive and negative cases are recorded;
- manual endpoint fallback works when discovery is degraded;
- disposable cert/SKI proof credentials survive restart and rebuild with the
  same data volume;
- fake peer is a wire-level black-box harness independent of the facade under
  test;
- G17 covers configured local SHIP advertisement/discovery, myVaillant trust
  visibility, and negative/TTL behavior; it is not evidence that the VR940f
  advertises a server;
- G19 covers direct outbound VR940f TCP/TLS/WebSocket/SHIP access completion
  plus first post-access SPINE data;
- canonical G19 evidence records exact repo, branch, commit, commands,
  redacted JSON, transcript hashes, environment/tool versions, topology,
  timestamps, trust preconditions, deterministic replay fixtures,
  denied-access negative cases, reconnect-failure negative cases, separate
  `operator_live_proof` and `ci_replay_authority` fields, and no public device
  identity leakage.

Gateway may not gain a persistent `helianthus-eebusreg` import until recovery
reconciliation, DOCS-VERIFY, MSP-DOCS-API-SCHEMA, MSP-DOCS-PLATFORM,
MSP-DOCS-E2, MSP-DOCS-CLEAN, MSP-03D-R, raw contract freeze, immutable raw
view, read-only lifecycle facade, API freeze, and trust/admin contracts merge.

## Candidate API Handshake

Candidate API documentation is prepared only from org-owned
`Project-Helianthus` branches. Forks are rejected. Once docs preparation
starts, force-push is forbidden.

`helianthus-eebusreg` CI produces the normalized API manifest and a GitHub OIDC
DSSE/in-toto attestation. Verification binds issuer, workflow identity, org
repo, ref, immutable head SHA, run id, run attempt, extractor version, schema
version, clean checkout, and manifest digest. `helianthus-docs-eebus` commits
the candidate manifest copy plus provenance and merges first. The eebusreg
merge gate requires exact match against that candidate. Any source push
invalidates the candidate and requires re-preparation.

Candidate API pages are hidden from stable navigation, search, sitemap,
versioned bundles, and release bundles until MSP-DOCS-API-FREEZE promotes
them to `active`. If the source PR closes unmerged or the candidate expires,
MSP-DOCS-CANDIDATE-CLEANUP moves the entry to `withdrawn`, removes candidate
artifacts, and restores docs main green before same-repo successors resume.

## Trust And Pairing

Production trust is owned by M4 and frozen at M4.5. MSP-04A is internal
persistent store/schema only. MSP-036 exports only versioned immutable raw
snapshot/view fields and has no semantic device ID, lifecycle authority,
trust/pairing mutation, or availability guarantee. MSP-055 is disabled by
default, exposes a read-only lifecycle facade, and opens outbound sockets only
with explicit config plus pre-seeded trust or allowlist. Trust states are:

- `NO_LOCAL_IDENTITY`
- `UNPAIRED_LOCKED`
- `PAIRING_WINDOW_OPEN`
- `PAIRED_TRUSTED`
- `REVOKED`
- `CORRUPT_STORE`
- `QUARANTINED`

eeBUS is disabled by default. No production SHIP listener or port mapping may
exist unless `eebus.enabled=true`, interface/subnet are explicit, the
production store is valid, and the current trust state permits listening.
Wildcard bind, automatic multi-interface selection, and mDNS advertisement
while pairing is closed are forbidden.

Admin and pairing APIs bind to an `AF_UNIX` socket by default. Loopback is
allowed only after proof that it is unreachable from HA ingress, add-on web UI,
host networking, LAN, and container bridge. Proxy headers such as
`X-Forwarded-*`, `Forwarded`, and `Host` are ignored unless they come from a
pinned Supervisor channel.

First trust uses exactly one ephemeral candidate during a short
operator-armed window. No trust-store write, peer ID allocation, mDNS trust
claim, or persistent pin may occur before out-of-band fingerprint
confirmation. A second remote during the candidate state is deterministically
denied and cannot replace the candidate except by explicit cancel or TTL
expiry.

The trust store lives under `/data/eebus` with `0700` directory and `0600`
files, `lstat`/nofollow symlink rejection, path traversal rejection, atomic
replace plus fsync of file and parent directory, no secrets in env or argv, and
core dumps disabled. Generic HA backup restore to another host cannot preserve
trusted state. The private key is host-bound or excluded from restorable
backups; missing host anchor fails closed. Revocation tombstones are monotonic
and non-restorable or the store enters locked/corrupt state.

## Gateway Runtime

`EEBusRuntimeAdapter` is a sibling of `EBusRuntimeAdapter`. eeBUS configuration
is separate from eBUS transport configuration and includes enable flag, listen
port, network interfaces/subnets, cert/key/trust-store paths, optional remote
SKI allowlist, and pairing-window mode.

The eeBUS sidecar must not modify:

- `transportFromConn`
- `protocol.Bus`
- `router.BusEventRouter`
- eBUS registry semantics in `helianthus-ebusreg`

Disabled-default acceptance requires no eeBUS sockets, no trust files, no eBUS
config regression, and unchanged eBUS CI and transport matrix. Gateway import
is blocked until prior canonical docs and eebusreg contracts merge.

## MCP Raw v1

Stable read-only tools are:

- `eebus.v1.runtime.status.get`
- `eebus.v1.services.list`
- `eebus.v1.services.get`
- `eebus.v1.sessions.list`
- `eebus.v1.sessions.get`
- `eebus.v1.topology.get`
- `eebus.v1.snapshot.capture`
- `eebus.v1.snapshot.drop`
- `eebus.v1.pairing.status.get`

No pairing or trust mutation tool is registered in the stable namespace.
Future mutation tools must live under `eebus.experimental.pairing.*` and remain
unregistered unless protected by feature flag, admin auth, local origin,
CSRF/origin checks, TTL token bound to operation, peer fingerprint, store
generation, idempotency key, and immutable audit event. `GET` never mutates.

`snapshot.capture` materializes an immutable whole-root `snapshot_root`. If a
whole-root capture is impossible, the stable tool spec must declare
`scoped_only` before v1, require `snapshot_scope` on capture, echo scope on
every response, and bind refs to runtime, contract, tool, scope, mask tier, and
effective auth scope.

Every `snapshot_ref` and `evidence_ref` is minted at capture time with:

- runtime identity;
- contract identity;
- tool identity;
- snapshot scope or whole-root marker;
- mask tier;
- effective auth scope or principal class.

Dereference requires an exact binding match and never re-masks the same ref at
read time. Mismatched binding returns `permission_denied` or `admin_required`
after syntax and scope validation.

MCP uses RFC 8785/JCS canonical JSON for hash material. Non-finite numbers and
negative zero are forbidden. Exact decimals and integers beyond portable JSON
safe-integer range are encoded as strings. `data_hash` hashes a `hash_view`
containing schema version, mask tier, data, stable degraded machine fields, and
only immutable evidence descriptors or content hashes. Transient evidence
handles are excluded and linked by a separate `provenance_hash` when needed.
Hashes are comparable only when tool id, schema version, mask tier, effective
auth scope, and snapshot scope/whole-root are identical.

Exhaustive v1 error codes are:

- `invalid_argument`
- `not_found`
- `permission_denied`
- `admin_required`
- `backend_unavailable`
- `timeout`
- `snapshot_gone`
- `quota_exceeded`
- `contract_violation`

Error precedence is parse/tool-shape/scope validation, authorization,
previously issued ref lifecycle, backend reachability/latency, then impossible
internal invariant break. `snapshot.drop` returns `dropped` or `already_gone`
and never `not_found`.

## Evidence And Candidate Facts

M6.5 records synchronized eeBUS, eBUS, and myVaillant/myPyllant evidence using
existing read-only eBUS debug, MCP, or log surfaces only. If exact
B509/B524/B555 source identity is absent, the leaf is `WITHHELD` or
`NOT_TESTED`; no inferred register identity, log-scraping guess, or new eBUS
capture path is allowed inside M6.5.

Recorder acceptance requires one capture clock, monotonic timestamps for eBUS,
eeBUS, and cloud observations, measured max drift/latency, pre/action/post
windows bound to that clock, and replay using captured timestamps only.

M7 creates draft candidate facts only. M8 proves coexistence. M8.5 locks leaf
promotion after coexistence evidence exists. Feature graph completeness and
reconnect durability are MSP-055/M6 concerns, not G17 acceptance.

Each Leaf Promotion Dossier includes:

- canonical semantic path plus protocol source identity;
- B509/B524/B555 source-family identity, with B524 opcode/group/instance/register
  and OP=0x02 and OP=0x06 treated as separate namespaces;
- eeBUS entity/service/feature/path;
- comparator type and pass/fail parameters: time window, tolerance, unit
  conversion, rounding, minimum samples, max missing samples, stale cutoff, and
  conflict threshold;
- terminal negative states for `NO_SIGNAL`, `CLOUD_ONLY`, `CONFLICT`, and
  `NOT_TESTED`, all remaining `WITHHELD` and raw/debug only;
- coexistence result, replay regeneration, provenance, redacted hashes, and
  retest trigger.

No family, device, or sibling inheritance is allowed. B509/B524/B555 may enrich
provenance and context, but cannot promote a leaf unless the exact leaf value
is directly observed and compared.

Mutable proof requires a lab-safe whitelist, lab lease, one writer,
poller-safe arbitration through the gateway/router write path, no direct
adapter writes, abort on bus errors, timeouts, heating or DHW safety
conditions, rollback verification after every cycle, and three independent
perturbation cycles.
