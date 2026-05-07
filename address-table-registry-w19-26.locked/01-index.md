# Index — Address-Table Registry

Canonical-SHA256: `eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b`

## Files

- `00-canonical.md` — full canonical plan (objective, decision matrix AD01..AD15, phase split, falsifiability gate)
- `10-architecture-and-decisions.md` — AddressSlot / DeviceEntry / BusFace data model; companion derivation; ACK/NACK insertion rules; 0xFF disambiguation; SN merge gate forward-reference; static seed semantics
- `11-milestones-phase-a.md` — M0..M9 detailed scope, falsifiability per milestone, dependencies, repo
- `12-milestones-phase-b.md` — M6, M7 deferred (enrichment merge + EvidenceBuffer migration)
- `13-acceptance-criteria-and-falsifiability.md` — live HA validation: positive + negative assertions; transport matrix; consumer compatibility
- `14-phase-c-frame-type-transport.md` — Phase C amendment: 4-class `AddressClass` taxonomy, unified `FrameType`, `RawTransport.Send(ft, src, dst, ...)` breaking change, `ValidateFrameAddressing` enforcement, `DeviceEntry.AddressForFrameType` registry helper, per-API-site frame-type declaration, M-C0..M-C10 milestone sketch (AD24..AD30)
- `90-issue-map.md` — per-repo issue rollup
- `91-milestone-map.md` — dependency DAG + iteration vs merge deps
- `99-status.md` — runtime state tracker (cruise-state-sync mirror)

## Reference

- Parent plan: `ebus-good-citizen-network-management.maintenance/91-milestone-map.md` (M3 Identity model refactor — superseded but never executed; this plan completes it)
- Predecessor PRs: `helianthus-ebusgateway#560` + `#562` (merged 2026-05-06; remain intact in Phase A)
- Consultant validation: agent run `aa67dc058ee96d896` (eBUS NM design GO recommendation, 3 mandatory corrections C1/C2/C3)
- Adversarial planning: Codex gpt-5.5 thread `019dfd04-18e8-78f1-8651-760fea1b3092`, 3 rounds, ready_to_lock=true round 3
