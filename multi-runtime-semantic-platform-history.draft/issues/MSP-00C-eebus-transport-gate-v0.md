# MSP-00C - Define eeBUS Transport Gate v0

## What

Define `eebus-transport-gate v0`, the required transport/protocol validation
gate for raw eeBUS runtime work.

## Why

eBUS T01..T88 is specific to the existing eBUS transport. eeBUS introduces
SHIP/TCP, SPINE, mDNS, pairing, trust, snapshots, and HA add-on networking.
Those need a dedicated gate before `helianthus-eebusreg`, gateway sidecar, or
MCP work can proceed.

## Acceptance Criteria

- [ ] `93-eebus-transport-gate-v0.md` defines required artifacts.
- [ ] The case matrix covers disabled default, fake peer handshake, pairing
      open/closed, pairing race, listener scope, mDNS positive/negative,
      manual endpoint, cert/SKI persistence, restore/clone lock,
      retry/backoff/quarantine, snapshot capture/replay/auth/drop, redaction,
      VR940f live smoke, and coexistence no-drift.
- [ ] The gate states fake peer success is supporting evidence only and live
      VR940f smoke is required before gateway import.
- [ ] The gate states eBUS T01..T88 is still required when eBUS transport or
      eBUS capture code changes.
- [ ] The issue map references `eebus_v0` for protocol-facing eeBUS work.
- [ ] `./scripts/validate_plans_repo.sh` passes.
- [ ] `git diff --check` passes.

## Dependencies

- MSP-00A

## Routing

- Repo: `helianthus-execution-plans`
- Complexity: 5
- Model lane: `GPT-5.5 medium`
- Review: `gpt-5.4-mini` consistency review plus transport-gate review

## Gates

- Doc gate: not required
- Transport gate: not required for this issue because it defines the gate
- Security gate: not required, but security reviewer should inspect the case
  list

## Rollback

Remove the gate definition and reset issue-map gate references to draft-only
placeholders.
