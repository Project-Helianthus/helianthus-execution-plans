# ebus_standard 12: Milestones, Issues, Acceptance, Risks

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`

Depends on: `10-scope-decisions.md` establishes the catalog identity key
and NM subsumption. `11-execution-safety-and-surfaces.md` establishes the
safety-class model, whitelist, execution-policy module, and portal/HA
gating. This chunk turns those contracts into discrete milestones, issues,
acceptance criteria, and risks.

Scope: Milestone Plan (`M0` through `M6b`), Canonical Issues across all
target repos plus the conditional proxy/firmware issue, Acceptance
Criteria, and Risk Table.

Idempotence contract: Declarative-only. Reapplying this chunk must not
reorder milestones in a way that breaks the gate topology, drop any
acceptance criterion, widen the safety envelope, or silently add repos to
the target set.

Falsifiability gate: Review fails this chunk if it ships without
`M4B_read_decode_lock` before consumer rollout, declares `M4c2` before
`M4b2` returns go, omits the Vaillant-independent conformance vectors,
skips the portal decode-sandbox hardening, or closes out the deprecated
NM plan without reconciling its issue map and cross-links in `M6b`.

Coverage: Milestone Plan; Canonical Issues; Acceptance Criteria; Risks.

## Milestone Plan

| Milestone | Scope | Repo | Depends on | Result |
| --- | --- | --- | --- | --- |
| `M0_DOC_GATE` | Normative catalog; type rules; safety policy; adopt-and-extend inventory of merged NM docs `#251/#253/#256` plus ownership preface and migration appendix | `helianthus-docs-ebus` | none | Normative source frozen; NM docs adopted in-place |
| `M1_TYPES` | L7 primitive types (BYTE, CHAR, DATA1c, raw, composite BCD, length-dependent selector) with positive and negative golden vectors | `helianthus-ebusgo` | `M0` | Type primitives locked |
| `M2_CATALOG` | Catalog schema + YAML data; identity key model; collision test; SHA pinning; version tagging | `helianthus-ebusreg` | `M0` | Catalog is a versioned artifact |
| `M3_PROVIDER` | Generic `ebus_standard` provider; catalog-driven method generation; identity/provenance policy; namespace-isolation tests vs Vaillant `0xB5`; feature-flag disable switch | `helianthus-ebusreg` | `M2` | Provider plan stable in registry |
| `M4_GATEWAY_MCP` | MCP `services.list`/`commands.list`/`command.get`/`decode`; single execution-policy module; `rpc.invoke` safety gating; NM runtime wiring to catalog for broadcast subset | `helianthus-ebusgateway` | `M1`, `M3` | MCP surfaces live; NM broadcast routed via catalog |
| `M4B_read_decode_lock` | Freeze envelope shape for `list`/`get`/`decode`, safety metadata names, error schema, replacement-value schema, catalog version reporting | `helianthus-ebusgateway` | `M4` | Semantic lock for read/decode consumers |
| `M4b1` | Transport feasibility primitives for slave-address receive/reply on ENH/ENS | `helianthus-ebusgo` | `M1` | Responder substrate available |
| `M4b2` | Gateway capability observation plus go/no-go signal for responder lane | `helianthus-ebusgateway` | `M4b1` | Responder feasibility answered |
| `M4c1` | Transport support for responder-mode frames on approved transports | `helianthus-ebusgo` | `M4b2=go` | Transport substrate for responder |
| `M4c2` | Responder runtime for `07 04` and `FF 03/04/05/06`, driven by catalog | `helianthus-ebusgateway` | `M4c1` | Responder lane live where supported |
| `M4D_responder_lock` | Freeze responder capability/status fields in MCP | `helianthus-ebusgateway` | `M4c2` | Semantic lock for responder consumers |
| `M5_PORTAL` | Portal read/list/decode UI with decode-sandbox hardening; no invocation UI for denied classes | `helianthus-vrc-explorer` | `M4B_read_decode_lock` | Operator-visible inspection surface |
| `M5b_HA_NOOP_COMPAT` | HA compatibility checkpoint: no new entities/fields; identity/provenance regression | `helianthus-ha-integration` | `M4B_read_decode_lock` | HA-visible contracts unchanged |
| `M6a` | Live-bus matrix artifact: offline conformance vectors, Vaillant regression transcripts, NM wire regression, `07 FF` cadence floor, rollback criteria per repo | `helianthus-ebusgateway` | `M4B_read_decode_lock`, `M4D_responder_lock`, `M5`, `M5b` | Deployment-grade proof |
| `M6b` | Matrix publication in docs; NM plan `.maintenance` transition; issue map reconciliation | `helianthus-docs-ebus` | `M6a` | Deprecated plan closed out |

Coordination notes for multi-repo gating:

- `M4b2` is the sole gate for `M4c1`/`M4c2`. Responder work does not
  begin without go-signal. If proxy or firmware work is required, it is
  opened as a new issue in the conditional repo with an explicit
  dependency edge to `M4b2` outcome.
- `M4B_read_decode_lock` and `M4D_responder_lock` are independent gates.
  `M5` responder UI (if any) waits for `M4D`; read/decode UI waits on
  `M4B`.
- `M6a` and `M6b` are strictly serial. `M6b` closes the deprecated plan
  only after `M6a` publishes the matrix artifact.

## Canonical Issues

| ID | Repo | Summary |
| --- | --- | --- |
| `ISSUE-DOC-EBS-00` | `helianthus-docs-ebus` | Normative ebus_standard catalog covering services `0x03/0x05/0x07/0x08/0x09/0x0F/0xFE/0xFF`; adopt-and-extend merged NM docs `#251/#253/#256` with ownership preface and migration appendix |
| `ISSUE-DOC-EBS-01` | `helianthus-docs-ebus` | L7 type rules: BYTE/CHAR/DATA1c/raw/BCD/length-selector exact semantics |
| `ISSUE-DOC-EBS-02` | `helianthus-docs-ebus` | Execution-safety policy: safety classes, default-deny, `system_nm_runtime` whitelist contract |
| `ISSUE-DOC-EBS-03` | `helianthus-docs-ebus` | Matrix publication plus NM plan `.maintenance` transition plus issue-map reconciliation (`M6b`) |
| `ISSUE-GO-EBS-01` | `helianthus-ebusgo` | Implement L7 type primitives with positive and negative golden vectors |
| `ISSUE-GO-EBS-02` | `helianthus-ebusgo` | Transport feasibility primitives for slave-address receive/reply (`M4b1`) |
| `ISSUE-GO-EBS-03` | `helianthus-ebusgo` | Transport support for responder-mode frames (`M4c1`) |
| `ISSUE-REG-EBS-01` | `helianthus-ebusreg` | Catalog schema + data file + identity key model + collision test + SHA pinning |
| `ISSUE-REG-EBS-02` | `helianthus-ebusreg` | Generic `ebus_standard` provider with catalog-driven method generation, identity provenance, disable switch |
| `ISSUE-REG-EBS-03` | `helianthus-ebusreg` | Namespace-isolation tests vs Vaillant `0xB5` (codec, registry lookup, generated identifiers, envelope helpers) |
| `ISSUE-GW-EBS-01` | `helianthus-ebusgateway` | MCP surfaces: `services.list`, `commands.list`, `command.get`, `decode` |
| `ISSUE-GW-EBS-02` | `helianthus-ebusgateway` | Execution-policy module + `rpc.invoke` safety gating + `caller_context` enforcement |
| `ISSUE-GW-EBS-03` | `helianthus-ebusgateway` | NM runtime wiring to catalog-driven emit and responder paths |
| `ISSUE-GW-EBS-04` | `helianthus-ebusgateway` | Gateway capability observation + go/no-go for responder feasibility (`M4b2`) |
| `ISSUE-GW-EBS-05` | `helianthus-ebusgateway` | Responder runtime for `07 04` and `FF 03/04/05/06` (`M4c2`) |
| `ISSUE-GW-EBS-06` | `helianthus-ebusgateway` | `M4B_read_decode_lock` semantic-lock artifact |
| `ISSUE-GW-EBS-07` | `helianthus-ebusgateway` | `M4D_responder_lock` semantic-lock artifact |
| `ISSUE-GW-EBS-08` | `helianthus-ebusgateway` | Live-bus matrix artifact (`M6a`): offline vectors, Vaillant regression, NM regression, cadence enforcement, rollback criteria |
| `ISSUE-VRC-EBS-01` | `helianthus-vrc-explorer` | Portal read/list/decode UI with hardened decode sandbox |
| `ISSUE-HA-EBS-01` | `helianthus-ha-integration` | Compatibility checkpoint: prove no HA-visible contract change from identity/provenance shifts |

Conditional (opened only if `M4b2` requires):

| ID | Repo | Summary |
| --- | --- | --- |
| `ISSUE-PROXY-EBS-01` | `helianthus-ebus-adapter-proxy` | Responder-path mediation, opened with explicit dependency edges only if `M4b2` proves it needed |

## Acceptance Criteria

- Normative catalog and type rules are frozen in `helianthus-docs-ebus`
  with adopt-and-extend of merged PRs `#251/#253/#256`. No normative
  rewrite of adopted sections.
- L7 type primitives decode and encode correctly for positive and
  negative golden vectors. Validity and replacement-value status
  propagate to decode output.
- Catalog generation fails on duplicate identity keys and on ambiguous
  length-selector branches. Catalog carries a version and SHA.
- Generic `ebus_standard` provider is registered with a stable plan name
  and a feature-flag disable switch. `DeviceInfo` contract unchanged.
  Identification descriptors never silently overwrite existing
  `DeviceInfo` values; disagreements retain both sources with labels.
- Namespace-isolation tests pass. Vaillant `0xB5` quirks do not affect
  `ebus_standard` decode and vice versa.
- MCP surfaces `services.list` / `commands.list` / `command.get` /
  `decode` ship with declared envelope shapes. `command.get` includes
  `safety_class`. `decode` accepts PB, SB, direction, frame_type, and
  payload hex; returns decoded fields, validity, replacement-value
  status, and raw bytes.
- `rpc.invoke` default-denies
  `mutating|destructive|broadcast|memory_write` for every caller context
  except `system_nm_runtime`, which is restricted to the compile-time
  whitelist keyed by full catalog identity. Deny-parity tests across
  adjacent variants pass. Deny-parity tests across entry points
  (`rpc.invoke` vs provider-direct) pass.
- NM runtime emits `FF 00`, `FF 02`, and (optionally) `07 FF` through
  catalog-driven paths after `M4_GATEWAY_MCP`. Responder replies to
  `FF 03/04/05/06` ship only on transports approved by `M4b2` and after
  `M4c2`; `ebusd-tcp` documents the no-responder outcome if confirmed.
- `M4B_read_decode_lock` and `M4D_responder_lock` artifacts freeze
  envelope and responder-field shapes before portal and HA checkpoint
  milestones start.
- Portal decode sandbox enforces hex validation, size caps, worker
  timeout isolation, HTML escaping, and no unsafe Markdown/HTML
  rendering. Tests cover malformed hex, oversized input, invalid CHAR
  bytes, and replacement-value display.
- HA integration carries no new entities, no new GraphQL fields, and no
  change to HA-visible contracts. Regression tests cover identity and
  provenance paths.
- `M6a` publishes offline conformance vectors plus Vaillant live-bus
  regression transcripts across transports. Rollback criteria are
  documented per repo: catalog version pinning, provider disable
  switch, MCP surface back-compat policy, documented revert path.
- `M6b` transitions `ebus-good-citizen-network-management` to
  `.maintenance` with cross-links and issue map reconciled. Merged docs
  `#251/#253/#256` remain authoritative; this plan's canonical carries
  the ownership preface and migration appendix.

## Risks

| # | Risk | Severity | Mitigation |
| --- | --- | --- | --- |
| 1 | Catalog identity key misses an eBUS dispatch axis (service-specific length prefix, class-2 broadcast, typed-payload selector) | HIGH | explicit fixtures per axis in `M2`; generation collision test; identity tuple enumerated in the catalog decision (see chunk 10) |
| 2 | Execution-safety whitelist drift lets adjacent variants execute under `system_nm_runtime` | HIGH | whitelist keyed by full catalog identity tuple; deny-parity tests across adjacent variants; single execution-policy module |
| 3 | Responder lane requires proxy or firmware changes not visible from gateway code | HIGH | `M4b1`+`M4b2` dedicated feasibility spike; out-of-scope repos get new issues with explicit dependency edges |
| 4 | Portal decode sandbox becomes an XSS/size-bomb/UI-lockup vector | MEDIUM | hardening acceptance in `M5` (hex validation, size caps, worker timeout, HTML escape, no unsafe markup) |
| 5 | NM plan deprecation breaks traceability of merged docs `#251/#253/#256` | MEDIUM | adopt-and-extend; no rewrite; ownership preface plus migration appendix; `.maintenance` transition only after reconciliation in `M6b` |
| 6 | Shared infrastructure lets Vaillant `0xB5` quirks leak into `ebus_standard` decode | MEDIUM | namespace-isolation tests in `M3`; regression fixtures independent of Vaillant |
| 7 | `M4B` semantic lock premature relative to responder fields added by `M4c2` | MEDIUM | split into `M4B_read_decode_lock` and `M4D_responder_lock`; portal responder UI (if any) gates on `M4D` |
| 8 | HA-visible contracts change silently through identity/provenance shifts | MEDIUM | `M5b_HA_NOOP_COMPAT` compatibility checkpoint; identity regression tests |
| 9 | `rpc.invoke` gating and provider-direct invocation diverge in denial policy | MEDIUM | single execution-policy module; denial-parity tests across entry points |
| 10 | Operator override deferral blocks legitimate maintenance execution | LOW | `system_nm_runtime` whitelist covers required NM emit and responder; operator override is an explicit future locked-plan decision, not a silent code change |
