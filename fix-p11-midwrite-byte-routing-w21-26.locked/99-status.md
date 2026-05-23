# Execution status

Canonical-SHA256: `ddd1786c883f07395e417d63c71607b46f92b8968126363fd11c55b8e0d8de7d`

Depends on: 91-milestone-map.md.

Scope: live cruise-state snapshot for resume. Updated by cruise-state-sync each FSM transition.

Idempotence contract: each status entry is append-only with iso8601 timestamp; the latest entry is authoritative. Re-running cruise-resume against the latest entry restores the same FSM state.

Falsifiability gate: every entry must include `active_skill`, `active_state`, and `iso8601_ts`. Missing fields fail the schema check and block resume.

Coverage: full lifecycle from PLAN_LOCKED through MERGED+VERIFIED.

## Status log

| iso8601_ts | active_skill | active_state | notes |
|---|---|---|---|
| 2026-05-23T04:40:00Z | cruise-plan | PLAN_STABLE | Adversarial R1 (Codex) + R1/R2 (fresh-Opus angry-tester) converged on refined Direction C. Baseline captured. Plan locked. |
| (next) | cruise-preflight | ROUTING | tbd |
| 2026-05-23T09:48:58Z | cruise-deploy-remediation | DEPLOY_FIXED | HA local add-on source was stale at 0.6.25 and a backup under `/mnt/data/supervisor/addons/local/` shadowed the 0.6.27 package. Synced `helianthus-ha-addon/helianthus` to HA, moved backup to `local-backups/`, refreshed Supervisor, and updated `local_helianthus` to 0.6.27. Running image: `ghcr.io/project-helianthus/helianthus-ha-addon:0.6.27`; gateway module string includes `cc0beb132330`. |
| 2026-05-23T09:51:26Z | cruise-m4-live-verify | ESCALATED_STARTUP_O1O2_FAILED | Clean 0.6.27 deploy reached S6. M4 script report `_work_adaptermux_audit/v8-enforce-stress/m4-verification/20260523T094956Z_m4.txt`: O2 failed, no `semantic_b524_root_discovery` within 90s; O1 failed 10/12 with `radio_devices` and `boiler_status` null. Failure bundle: `_work_adaptermux_audit/META-AUDIT/S14-STARTUP_O1O2_FAILED-20260523T095126Z.json`. |
