# Planning status — 2026-10-14

Canonical-SHA256: `ca9edfc928fe862162c6d349c4f226580aa05145d04ae53c81a0aa557c464a85`

Phase B revision 4 for execution-plans #126 is drafted locally on issue/126-driver-model-transition. State `implementing` is the permitted directory label reflecting the already-started G4/0.7 workstream; current_milestone PHASE-B describes planning only. This guide has not been committed, published or accepted. The supplied gpt-6-astra rounds are same-camp reads: DM-PLAN is Codex-authored, and Astra/Sol are both Codex. Claude Opus 5.5 supplied the opposite-camp revision-2 FINDINGS review (canonical 783534aad1f2b54a871ccf75fab453a4171bde770c39f1da6865643570bc9254); revision 3 applies all nine dispositions from that review. Revision 4 closes the four supplied small review items from Claude Opus 5.5 and gpt-6-astra. Revision 4 confirmations: gpt-6-astra NOFINDINGS (same camp); Claude Opus 5.5 (opposite camp) no P0–P2, one P3 — a blanket sentence claiming that no DM-07 node descends from a human checkpoint, contradicted by the lane checkpoints retained on the leaf compositions (C1, X1, Board dispositions) and by O1 through DM-PLAN — narrowed by the orchestrator in 90-issue-map.md and 92-retained-acceptance.md before commit. No product implementation, issue filing, remote status queries, code-repository scans, CI, hardware I/O or runtime mutation was performed.

The supplied decision is binding. O1–O12 and G5 D1–D6 are explicitly pending. Existing 0.7 and future 0.8 guides remain untouched and authoritative until a Board-approved reconciliation; no execution resumes from this draft. Native profile/support/physical unknowns remain unknown.

Local validation covers YAML uniqueness, metadata, document hashes/links, canonical/chunk agreement, issue/milestone DAGs and mirrors, fixed or dispatch-time opposite-camp assignments, retained contract ID/version mirrors, dependency release ranks (planning < 0.7 < 0.8 < pre-1.0), R-INT21 ancestry for 0.8/pre-1.0 and exclusion below 0.8, three required family-order pairs, exact decision-row tokens, preamble mirror and hard-stop text mirror. The repository runner validates active plan structure and invokes the named plan companions, including this guide’s validate_plan.py, with failures propagated under set -euo pipefail. Release-rank checks rely on the declared release labels of external prerequisites; relabelling an external node can hide an inversion. The preamble check proves the canonical preamble equals reference-preamble.md; an edit made to both mirrors passes. Neither checks product behavior or current issue readiness.

Tokenizer availability: a disposable venv was created successfully inside this directory, but tiktoken installation failed twice with “No matching distribution found for tiktoken” (including explicit PyPI index, no retries); it was removed. Exact tokenizer counts are unavailable. Each 1x chunk is under 6,100 UTF-8 bytes, conservatively below 10,000 byte-BPE tokens; byte sizes are reported separately, never called measured token counts. The canonical file is the complete assembled plan and is read through the split chunks.

Recorded revision 2 local results: guide companion PASS (45 issues, 6 milestones, 8 chunks); full repository runner PASS (24 active plan files, all four named companions including this guide, 74 tests). The runner here-doc completed normally; no stage fallback was needed. These are planning/structure results only.

Recorded revision 3 local results: guide companion PASS (45 issues, 6 milestones, 8 chunks); full repository runner PASS (24 active plan files, all four named companions, 74 tests). The here-doc completed normally; no fallback or refused write occurred. This validator has no self-test pattern: 15 negative mutations on disposable copies were rejected by the expected rule (local/external/milestone release inversions, premature/missing R-INT21, each missing family pair, exact O1/O2/O10 rows, contradictory preamble edits in one of the two mirrors after digest refresh, and YAML/Markdown hard-stop text drift). Decision bytes, census totals and retained inventory anchors were preserved; no implementation anchors were reverified here.

Next planning step: operator/Board choices and fresh independent review of the final plan diff through the normal workflow. Publishing this guide has no post-merge effects and does not authorize any code or live work.

Hard-stop text mirrored from plan.yaml (structural agreement only):

| Hard stop |
|---|
| O1..O12 remain pending; affected nodes require recorded answers in owning issues |
| No native profile admission from registration, decoder presence or retained DTOs |
| No public shape change without goldens/approved contract and applicable parity |
| Unknown semantic outcome or native close proof withholds replacement/admission |
| R-INT21 acceptance precedes all 0.8 moves |
| eBUS northbound excluded from 1.0 unless real Pi UART hardware/backend and wire timing are qualified |
| Fresh exact-HEAD NO_BLOCKING_FINDINGS and applicable code-repository checks before merge |
| Exact final BOM Daybreak and physical acceptance are not replaced by fixtures or plan validation |
