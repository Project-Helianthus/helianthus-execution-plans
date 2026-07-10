# AD-DOCS-01 Amendment

Status: `PASS`
Date: `2026-07-10`
Plan state: `locked`
Cruise phase: `RECOVERY_RECONCILIATION`
Amendment: `external-only-documentation`

## Basis

This artifact records the accepted AD-DOCS-01 amendment after five GPT-5.5
xhigh amendment rounds. The amendment does not rename the locked directory,
does not accept dirty code, and does not publish local recovery commit SHAs,
private paths, raw HMAC mappings, source-bundle details, or sensitive evidence.

## Decisions

1. `MSP-R00` is completed locally for issue #14 with no code acceptance,
   architecture review `PASS`, and no runtime successor unlock.
2. The initial ready set is exactly `MSP-R00-L` and `DOCS-VERIFY`.
3. `helianthus-eebusreg` and clean-main branches contain no `docs/` directory
   and own no substantive protocol, architecture, API, harness, test, or user
   documentation.
4. eeBUS documentation ownership is split across
   `helianthus-docs-eebus/protocols/`, `architecture/`, `api/`, `devices/`,
   `evidence/`, and `re-notes/`; language-neutral platform contracts remain in
   `helianthus-docs-ebus/docs/platform/`.
5. R00-L public evidence uses random nonsemantic per-publication opaque IDs and
   only `public_redacted`, `private_restricted`, or `discarded` classes.
6. Recovered dirty docs are not facts. Without publishable evidence IDs, they
   remain candidate or hypothesis with falsifiers.
7. The documentation DAG is serialized:
   `DOCS-VERIFY -> MSP-DOCS-API-SCHEMA`,
   `MSP-R00-L + MSP-DOCS-API-SCHEMA -> MSP-DOCS-PLATFORM`,
   `MSP-DOCS-PLATFORM -> MSP-DOCS-E2`,
   `MSP-DOCS-E2 -> MSP-DOCS-CLEAN`,
   `MSP-DOCS-CLEAN -> MSP-03D-R`.
8. `MSP-DOCS-CANDIDATE-CLEANUP` is dormant and conditional; it is not initially
   ready and is not a normal required predecessor.
9. `MSP-036 -> MSP-DOCS-API-CANDIDATE -> MSP-055 ->
   MSP-DOCS-API-FREEZE -> MSP-04B` enforces a docs-first exact-head handshake:
   the single source PR remains unmerged until its hidden candidate manifest
   and provenance merge, then active docs freeze against the merged source
   commit before first-trust work.

## Security Review

Verdict: `PASS`.

The amendment removes public bundle/hash publication requirements that could
conflict with privacy policy. Public commitments are limited to opaque IDs,
classes, dispositions, and redaction metadata. Raw HMACs and mappings stay
private. Cross-repo provenance requires clean clones, explicit refs, pinned
tools, GitHub OIDC DSSE/in-toto attestation, immutable head SHA, run
id/attempt, extractor/schema versions, clean checkout, and manifest digest.

## Architecture Review

Verdict: `PASS`.

The amendment strengthens ownership boundaries instead of adding runtime
behavior. Platform contracts remain language-neutral in docs-ebus. eeBUS
protocol, architecture, and API documentation move to docs-eebus. eebusreg
keeps only implementation and mechanical API extraction under
`internal/apiboundary`; the manifest is a CI artifact, not code-local docs.

The independent post-curation review found and closed three stale ownership
references: the former generic protocol-knowledge rule, MSP-055 lifecycle
facade ownership, and MSP-045 trust/admin freeze ownership. A full matrix sweep
then assigned each eeBUS-specific protocol, architecture, and API row to its
exact docs-eebus subtree while preserving only language-neutral MSP-035
contracts in docs-ebus/platform.

A second fresh-context verification after those fixes returned `PASS` with no
findings. PR review then identified and closed two additional consistency
gaps: the missing pre-merge API candidate row and the contradictory evidence-ID
requirement for unsupported hypotheses. The amended matrix has 43 unique rows,
no cycles or missing dependencies, the exact initial ready set, a synchronized
canonical hash, and no private recovery-data leak.

## Residual Risks

- MSP-R00-L still requires independent public redaction review.
- Candidate API docs depend on exact attestation and source immutability.
- Cross-repo CI must remain portable across Linux and macOS or casefold
  emulation.
- The dormant cleanup row must preempt same-repo successors if a candidate is
  abandoned or expires.
