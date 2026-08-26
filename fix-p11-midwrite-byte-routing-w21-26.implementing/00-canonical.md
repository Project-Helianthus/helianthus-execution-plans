# P11 mid-write byte-routing correction

Status: `implementing`, stopped at `M4_NO_GO`.

## Purpose

This is a historical planning record for the P11 first-byte arbitration correction. It
does not authorize work, schedule a repository action, or retain workflow state.

## Historical implementation

The gateway correction forwarded a first unexpected master-class byte after a purported
arbitration win so the existing bus collision classifier could handle it. The correction
was limited to the first transmitted byte before any echo matched. The original scope did
not address later mid-frame loss or response interleaving.

## Observed outcome

The M4 contention qualification was `NO_GO`: its bounded windows reached 206/hour and
246.438/hour, both below the required 500/hour contention floor. Other observations do
not turn that failed floor into a GO result.

An add-on package was delivered after the M4 NO_GO. That delivery is historical fact, not
evidence that M4 qualified successfully.

## Current boundary

No further P11 implementation, deployment, or live verification follows from this plan.
The next action requires a separately chosen rollback, waiver, or corrective plan with
its own repository-local evidence and applicable safety gates.

## Ownership

- Gateway byte-routing behavior belongs to `helianthus-ebusgateway`.
- Add-on packaging belongs to `helianthus-ha-addon`.
- Reusable protocol documentation belongs to `helianthus-docs-ebus`.
- This repository retains only planning context and factual status.
