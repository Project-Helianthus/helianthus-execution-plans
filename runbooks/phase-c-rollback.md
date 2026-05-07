# Phase C Rollback Runbook — `address-table-registry-w19-26.locked`

Source: `address-table-registry-w19-26.locked/14-phase-c-frame-type-transport.md`

Status: Authoritative rollback procedure for the Phase C frame-type-aware
transport amendment. Referenced from chunk §"Rollback".

Scope: rollback covers M-C1..M-C9 (impl + live validation). M-C0 (docs)
and M-C0A (baseline matrix) do not roll back — they remain as the floor
for the next attempt.

---

## 1. Trigger conditions

Rollback is mandated if **any** of the following M-C8 assertions
falsify on the live HA deploy and a same-day patch is not viable:

| Assertion | Failure mode | Severity |
| --- | --- | --- |
| C-P1 | BAI ecoTEC M2S writes still address `0x03` post-deploy (pcap evidence) | hard rollback — original regression resurrected |
| C-P2 | NM heartbeat `FFh 00h` stops emitting OR validator rejects a legitimate `dst == 0xFE` frame | hard rollback — bus-membership regression |
| C-P3 | B524 read on BAI alias addresses `0x03` instead of `0x08` | hard rollback — registry helper broken |
| C-P4..C-P6 | Synthetic harness fails to reject (validator silent on wrong-class injection) | partial — validator broken; consider patch-forward if M-C5 logic is salvageable |
| C-P7 | NETX3 M2S writes go to `0xF1` or `0xFF` instead of `0xF6`/`0x04` | hard rollback — alias resolution broken |
| C-P8 | Clause-6 caller-vs-central mismatch is not rejected | partial — `Frame.Validate` clause-6 logic broken |
| C-N1 | `ebus_transport_invalid_frame_address_total` > 0 under default 10-minute soak | hard rollback if counter > 100/min sustained; patch-forward via M-C7 enrichment if < 10/min |
| C-N2 | Phase A registry behavior changed (DeviceEntry count or alias structure differs from baseline) | hard rollback — Phase A regression |
| C-N3 | `entry.Address()` deprecation panics in production OR fails to panic in tests | partial — AD30 enforcement broken; patch-forward likely viable |

Rollback is **NOT** mandated for:

- A C-N1 counter increment of <10/min sustained — this is treated as an
  M-C7 enrichment gap and patched forward by adding the missing
  callsite's `FrameType` declaration and re-deploying.
- A documentation-only failure in M-C0 — that is fixed by a docs-ebus
  follow-up, not a code revert.
- Test-only failures in M-C0B that did not block the impl PRs (those
  could not have shipped to live).

---

## 2. Reverse-merge order

PRs MUST be reverted in **strict reverse merge order** to avoid leaving
the gateway against an ebusgo HEAD that lacks `Frame.Validate`. Operator
fills concrete PR numbers post-impl.

1. **M-C10 docs evidence** — `helianthus-docs-ebus#____` — revert first
   (low-risk text revert; isolates the post-merge evidence trail from
   the rollback record).
2. **M-C9 transport-verify** — `helianthus-ebusgateway#____` — revert
   the matrix diff PR.
3. **M-C8 live validation** — `helianthus-ebusgateway#____` — revert
   the deploy-script + assertion PR.
4. **M-C7 semantic API enrich** — `helianthus-ebusgateway#____` —
   revert the per-callsite `Frame.FrameType` declarations. This step
   is the largest revert; expect ~30+ callsite changes.
5. **M-C6 registry helpers** — `helianthus-ebusreg#____` — revert
   `AddressByRole` AND the `entry.Address()` deprecation guard. Both
   live in the same PR.
6. **M-C5 Bus.Send enforce** — `helianthus-ebusgo#____` (Bus.Send) +
   `helianthus-ebus-adapter-proxy#____` (proxy propagation). Revert
   ebusgo first, then proxy.
7. **M-C4 validator sweep** — `helianthus-ebusgo#____` — revert the
   exhaustive test suite. Optional: keep the bench file as proof
   of pre-revert performance baseline.
8. **M-C3 Frame.Validate** — `helianthus-ebusgo#____` — revert the
   `Frame.FrameType` field, `Frame.Validate()` method, and
   `ErrInvalidFrameAddress` sentinel.
9. **M-C2 FrameType unify** — `helianthus-ebusgo#____` — revert the
   enum renames; restore `FrameTypeInitiatorTarget` etc. Note: if any
   downstream PR landed against the new names BEFORE rollback, that
   downstream PR must be reverted first or pinned to the deprecation
   alias.
10. **M-C1 AddressClass** — `helianthus-ebusgo#____` — revert the
    `AddressClass` enum and `AddressClassOf` classifier.

M-C0A baseline matrix and M-C0 docs DO NOT revert. Both stay as the
floor for re-attempt.

---

## 3. Per-repo revert commands

All reverts MUST go through PR (no force-push to main). Use
`git revert <merge-sha> -m 1` to revert a squash-merged commit (M
parent 1 keeps the pre-merge tree). Operator uses standard cruise-control
PR creation flow; auto-merge applies once Codex thumbs-up + CI green.

```bash
# helianthus-docs-ebus (M-C10)
cd helianthus-docs-ebus
git fetch origin
git checkout -b rollback/phase-c-mc10 origin/main
git revert <M-C10 squash-merge SHA> -m 1
git push -u origin rollback/phase-c-mc10
gh pr create --title "Rollback Phase C M-C10 (live validation evidence)" --body-file ../runbooks/phase-c-rollback.md

# helianthus-ebusgateway (M-C9, M-C8, M-C7) — three separate PRs, in order
cd ../helianthus-ebusgateway
git checkout -b rollback/phase-c-mc9 origin/main
git revert <M-C9 SHA> -m 1
git push -u origin rollback/phase-c-mc9
gh pr create --title "Rollback Phase C M-C9 (transport-matrix verify)"
# ... repeat for M-C8, then M-C7

# helianthus-ebusreg (M-C6)
cd ../helianthus-ebusreg
git checkout -b rollback/phase-c-mc6 origin/main
git revert <M-C6 SHA> -m 1
git push -u origin rollback/phase-c-mc6
gh pr create --title "Rollback Phase C M-C6 (AddressByRole + entry.Address deprecation)"

# helianthus-ebusgo (M-C5 ebusgo half, M-C4, M-C3, M-C2, M-C1)
cd ../helianthus-ebusgo
git checkout -b rollback/phase-c-mc5-ebusgo origin/main
git revert <M-C5 ebusgo SHA> -m 1
git push -u origin rollback/phase-c-mc5-ebusgo
gh pr create --title "Rollback Phase C M-C5 (Bus.Send validate)"
# ... repeat for M-C4, M-C3, M-C2, M-C1

# helianthus-ebus-adapter-proxy (M-C5 proxy half)
cd ../helianthus-ebus-adapter-proxy
git checkout -b rollback/phase-c-mc5-proxy origin/main
git revert <M-C5 proxy SHA> -m 1
git push -u origin rollback/phase-c-mc5-proxy
gh pr create --title "Rollback Phase C M-C5 (proxy frame-type propagation)"
```

If a revert produces a merge conflict (e.g. Phase D landed on top of
Phase C in ebusgo), STOP. Do not force the revert. Open an operator
escalation issue describing the conflicting commits and pause until
operator resolves precedence.

---

## 4. Verification post-rollback

After all reverts are merged:

1. **Cross-repo go.mod alignment** — run `cd helianthus-ebusgateway && go mod tidy && go build ./...` and verify it pins ebusgo at a SHA that pre-dates M-C1. Repeat for ebus-adapter-proxy and ebusreg.
2. **Transport matrix replay** — re-run T01..T88 from `matrix/phase-c-baseline-w19-26.json` (the M-C0A baseline). Expected: identical fingerprints, zero deltas. Any delta = the rollback is incomplete.
3. **Live HA deploy** — cross-compile + deploy the rolled-back gateway to HA (192.168.100.4) per existing flow. Smoke test:
   - BAI ecoTEC M2S writes are observed in pcap (any byte; we are NOT asserting `0x08` post-rollback because the original regression returns).
   - NM heartbeat `FFh 00h` emits at the expected cadence.
   - 10-minute soak: no panics, no crash loops, no `ErrInvalidFrameAddress` references in logs (the symbol no longer exists).
4. **Operator pcap reproduction** — confirm the original BAI 0x03↔0x08 regression IS observable again (this is unfortunate but expected — the regression is the price of rolling back; the floor for re-attempt re-establishes the baseline).
5. **Cruise-state meta-issue update** — append a "Phase C rolled back at <date>" entry to the pinned cruise-state comment, with links to the revert PRs.

---

## 5. Floor for the next attempt

The next Phase C attempt restarts from **M-C0A baseline + M-C0 docs**.
Specifically:

- M-C0 (`12-address-table.md` rename + 256-byte taxonomy + frame-type
  contract) **stays merged** — it is doc-only and represents the
  authoritative reference for any subsequent attempt.
- M-C0A (`matrix/phase-c-baseline-w19-26.json` + regression fixture)
  **stays merged** — the baseline is the only artifact that proves the
  pre-Phase-C wire behavior. The next attempt diffs against the same
  baseline.
- All other milestones restart from RED state in M-C0B.
- The next attempt MUST trace its decisions back to AD24..AD30 in
  the locked plan; any deviation requires a `15-...md` amendment, not
  a silent re-interpretation.

Lessons from the failed attempt MUST be captured in
`address-table-registry-w19-26.locked/15-phase-c-rollback-postmortem.md`
before the next M-C1 PR is opened. The postmortem identifies which
trigger condition fired, which AD assumption broke, and what the next
attempt does differently. Without this artifact, cruise-control refuses
to authorize a new M-C1 PR.

---

## 6. Open questions deferred to operator

- If only one C-P assertion fires (e.g. C-P1 alone) and the others all
  pass, may the rollback be PARTIAL — reverting only the registry helper
  (M-C6) while keeping the validator (M-C3..M-C5)? Lean: NO, full
  rollback is simpler and safer; partial rollback risks subtle interaction
  bugs. Operator confirms before any partial-rollback PR is opened.
- Do we keep `Frame.FrameType` field in ebusgo if M-C3 reverts but
  M-C0 docs pre-announced it? Lean: revert the field along with the
  rest of M-C3; doc reference becomes a forward-looking spec item until
  the next attempt lands. Operator confirms.
