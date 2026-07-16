# W28/2026 Temporary Fork And Upstream Checkpoint

Status: `accepted_execution_policy`
Recorded: `2026-07-16`
Canonical architecture merge: `b75968a958bec2a252980da9dd5894667cef5457`

This append-only checkpoint records repository lifecycle and execution order.
The normative architecture remains in `Project-Helianthus/helianthus-docs-eebus`.

## Decision

`Project-Helianthus/helianthus-ship-go` and
`Project-Helianthus/helianthus-eebus-go` are temporary downstream patch
carriers. They are not permanent Helianthus protocol forks.

Current M4 execution does not depend on upstream maintainer response time. The
forks remain required while no tagged upstream release exposes equivalent
pre-dial authorization and bridge behavior without a Go `replace` directive.

## Baselines

| Fork | Canonical branch | Upstream tag | Peeled commit | Upstream tree |
| --- | --- | --- | --- | --- |
| `helianthus-ship-go` | `helianthus-v0.6` | `v0.6.0` | `760c312bf723d726d8882af3bb06650ddcd11ca9` | `958ddf185fc09dd4d3b382fc108641513412d927` |
| `helianthus-eebus-go` | `helianthus-v0.7` | `v0.7.0` | `99f07ff79819b728dd2fe37472c4a26865d8076c` | `fee9de0ecb34dcb7c4165922fd49fedd42d8df23` |

Inherited upstream `dev` branches remain preserved but are not implementation
bases. Each fork accepts only the module-path rewrite, the reviewed gate or
bridge delta, tests, CI hardening, and required legal provenance. Unrelated
features are forbidden.

## Patch Structure

Module-path rewrites remain mechanically separate from functional changes.
This permits an upstream-neutral functional patch to be reviewed without
Project-Helianthus import churn. At the pinned baselines, the measured rewrite
surface is:

- `ship-go`: 42 Go files importing its upstream module path;
- `eebus-go`: 182 Go files importing its own upstream module path and 79 Go
  files importing the upstream SHIP module path.

Published dependency graphs use reviewed semantic prerelease tags and zero
`replace`, local override, branch, or pseudo-version dependencies.

## Upstream Sequence

The external sequence begins only after the current implementation proves the
VR940f path and the bounded M4 architecture review returns `PASS` or
`PASS_WITH_CARRIED_EVIDENCE`:

1. Produce a public, redacted, upstream-neutral proposal and evidence pack.
2. Open an Enbility `ship-go` Discussion and obtain positive feedback, as
   required by its `CONTRIBUTING.md`.
3. Open the accepted issue or draft PR with the optional gate, attempt handle,
   cancellation, dialer seam, tests, and behavior delta.
4. Wait for a tagged upstream SHIP release with equivalent behavior.
5. Open the dependent Enbility `eebus-go` Discussion, then accepted issue or
   draft PR for the configuration and callback bridge.
6. Wait for a tagged upstream eeBUS release with equivalent behavior.

Discussion, PR, and release timing is nonblocking for current M4 closure.

## Repatriation Gate

Only tagged upstream releases may replace the temporary forks. Repatriation
must:

- restore `github.com/enbility/*` module paths with zero `replace` directives;
- prove equivalent selected-path, root-fallback, hostname, IPv4, and IPv6
  behavior;
- rerun EEBUS-G10, EEBUS-G11, EEBUS-G16, public API anti-leak, and coexistence
  checks;
- bind exact upstream annotated tags, peeled commits, module graph, source SHA,
  and CI evidence.

After that gate passes, both Project-Helianthus forks are archived read-only.
They are never deleted because their immutable tags remain part of historical
build provenance.
