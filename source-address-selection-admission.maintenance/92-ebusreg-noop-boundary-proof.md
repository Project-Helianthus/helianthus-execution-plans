# SAS-09 ebusreg No-Op Boundary Proof

Status: pending PR/evidence publication

Issue: Project-Helianthus/helianthus-ebusreg#130

This artifact satisfies the SAS-09 "no-op boundary proof" lane without using
the abandoned ebusreg PR129 work. The local ebusreg checkout currently contains
unrelated dirty work on `issue/controller-capable-thermostats`; this proof was
therefore produced by read-only inspection only.

## Boundary

`helianthus-ebusreg` is registry and protocol projection code. It does not own
gateway startup source selection, source admission state, source persistence, or
adaptermux session source authority.

The repo has legitimate source-byte parameters in router/registry APIs because
callers must supply the already-selected transport source when building eBUS
frames. That byte is an input to frame construction, not an admission decision.

Representative read-only evidence:

- `registry/scan.go` exposes `Scan(ctx, bus, registry, source, targets)` and
  `ScanDirected(...)`; callers provide `source`, and the registry uses it when
  sending scan frames.
- `router/router.go` copies `frame.Source` into projection output; it records
  observed wire source and does not select one.
- `vaillant/system/router_plane.go`, `vaillant/b555/router_plane.go`, and
  `vaillant/dhw/energy.go` require a `source` parameter for request template
  building; they do not choose or persist a source.
- `schema/selector.go` implements schema selection by target/hardware version,
  unrelated to eBUS source address selection.

Read-only search evidence found no source-selection admission owner in ebusreg:

- no `SourceAddressSelector` implementation;
- no source-admission state machine;
- no `source_addr.last` persistence;
- no adapter signal/admission cache;
- no gateway GraphQL/MCP/Portal source override path.

## Decision

No ebusreg code change is required for source-selection admission.

M4/M7 must continue to treat ebusreg's `source` parameters as lower-level
frame-construction inputs. Normal gateway-owned paths are responsible for
passing only the admitted source; transport-specific diagnostics and external
proxy clients remain outside ebusreg's registry/projection boundary.

## Acceptance

- Do not reuse abandoned ebusreg PR129.
- Close ebusreg#130 by referencing this artifact from the final execution-plan
  evidence PR, or by opening a fresh no-op PR if the operator later wants a
  repo-local marker.
- No CI is required in ebusreg for this no-code proof unless a fresh ebusreg PR
  is opened.
