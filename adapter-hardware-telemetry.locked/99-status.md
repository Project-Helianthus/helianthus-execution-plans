# Adapter Hardware Telemetry — Status

## Current State

- **Plan state:** Partially complete; gateway and HA tails are now closed, but proxy/docs backfill is still open
- **Backfill status:** `ebusgo#121` merged, `helianthus-ebus-adapter-proxy#83` still open, `helianthus-ebusgateway#442` merged and closed `GW-05`, `helianthus-ha-integration#169` and `#178` are both merged, docs backfill still pending.

## Blockers

- `ISSUE-DOC-01` still needs the docs backfill in `helianthus-docs-ebus`.
- `helianthus-ebus-adapter-proxy#83` remains open, so the proxy telemetry path is not fully closed.
- Docs backfill for the adapter INFO reference still has not landed in `helianthus-docs-ebus`.
- `helianthus-ebus-adapter-proxy#83` remains the only code-path follow-up still open in the transport/proxy layer.

## History

| Date | Event |
|------|-------|
| 2026-03-10 | Plan created, canonical + split authored |
| 2026-03-10 | Adversarial R1-R5 completed, CONVERGED |
| 2026-03-29 | `helianthus-ebusgo#119` merged; `GO-01`/`GO-02` backfilled into the issue map |
| 2026-03-29 | `helianthus-ha-integration#169` merged; adapter enrichment landed |
| 2026-03-29 | `helianthus-ha-integration#178` opened as the hardening follow-up |
| 2026-03-29 | `helianthus-ebusgateway#440` merged at `becf3b52919775b3c4b2d23fab9d352726b2d193`; `GW-05` remains open |
| 2026-03-29 | `helianthus-ebusgo#121` merged at `e5d3f666fcfa51a151ea0fecb36ba6d1e4f4a877`; ENH INFO timeout under chatter is now bounded on `main` |
| 2026-03-29 | `helianthus-ebusgateway#442` merged at `ba0def9bce6a589a2bd9c0ccc6145496d7eb4e52`; `GW-05` closed after live ENS/proxy smoke showed populated adapter telemetry/status and `LIVE_READY` startup |
| 2026-03-29 | Closure audit refreshed; plan remains partially complete only because docs backfill and proxy issue `#83` are still open |
