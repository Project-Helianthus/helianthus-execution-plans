# Issue map

Canonical-SHA256: `ddd1786c883f07395e417d63c71607b46f92b8968126363fd11c55b8e0d8de7d`

Depends on: 00-canonical.md, 91-milestone-map.md.

Scope: maps each milestone to its tracking GitHub issue. Populated by cruise-preflight after meta-issue creation.

Idempotence contract: re-running cruise-preflight against an already-populated map updates only the rows for new milestones; existing rows remain. Issue URLs are immutable once set (no rewriting).

Falsifiability gate: each row must have either a valid GitHub issue URL or be marked `tbd-by-preflight`. No row may stay `tbd-by-preflight` after cruise-preflight completes.

Coverage: M0–M5 milestones from 00-canonical.md. Cross-repo PR sequencing per AD07.

| Milestone | Repo | Issue URL |
|---|---|---|
| M0 | helianthus-execution-plans (meta) | tbd-by-preflight |
| M0 | helianthus-docs-ebus | tbd-by-preflight |
| M1 | helianthus-ebusgateway | tbd-by-preflight |
| M2 | helianthus-ebusgateway | tbd-by-preflight |
| M3a | helianthus-ebusgateway | tbd-by-preflight |
| M3b | helianthus-ebusgateway | tbd-by-preflight |
| M3c | helianthus-ebusgateway | tbd-by-preflight |
| M4 | helianthus-execution-plans (verification report) | tbd-by-preflight |
| M5 | helianthus-ha-addon | tbd-by-preflight |
