# Multi-Runtime Semantic Platform Draft Split Index

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `f7c48073085d32dbe1de9e352f454a29fa60b6b7ac05954c5f253cb9593dccdc`

This directory contains an owner-approved draft for turning Helianthus into a
multi-runtime native protocol gateway. It uses the standard execution-plan
layout so it can later be promoted to a locked plan, but the `.draft` suffix is
intentional and outside the current active-plan validator.

## Split Rules

- The canonical source of truth is [00-canonical.md](./00-canonical.md).
- Each chunk repeats the canonical hash for drift detection.
- Each chunk is reviewable in isolation and declares:
  - `Depends on`
  - `Scope`
  - `Idempotence contract`
  - `Falsifiability gate`
  - `Coverage`
- The split is execution-oriented, not a replacement for the canonical file.
- Gateway `0.4.0` is the named direct eBUS baseline throughout this draft.

## Chunk Map

1. [10-platform-taxonomy-and-boundaries.md](./10-platform-taxonomy-and-boundaries.md)
   defines the transport/base protocol/profile/runtime/native registry/semantic
   boundaries.

2. [11-ebus-040-baseline-and-profile-split.md](./11-ebus-040-baseline-and-profile-split.md)
   captures the gateway `0.4.0` eBUS baseline and the required split between
   classic eBUS and vendor profiles.

3. [12-eebus-mcp-first-vr940f.md](./12-eebus-mcp-first-vr940f.md)
   defines the eeBUS raw-first path, the new `helianthus-eebusreg` repo, and
   the VR940f binding/discovery target.

4. [13-semantic-fact-graph-and-integration.md](./13-semantic-fact-graph-and-integration.md)
   defines canonical semantic facts, provenance, conflict handling, and
   cross-runtime integration.

5. [14-execution-roadmap-issues-and-gates.md](./14-execution-roadmap-issues-and-gates.md)
   maps milestones M0-M10 to execution gates and issue sequencing.

## Coverage Matrix

| Source content | Destination chunk |
| --- | --- |
| Platform model, architectural rules, target architecture | `10-platform-taxonomy-and-boundaries.md` |
| Gateway `0.4.0`, eBUS runtime boundary, base/profile split | `11-ebus-040-baseline-and-profile-split.md` |
| eeBUS repo, MCP raw-first, VR940f lab target | `12-eebus-mcp-first-vr940f.md` |
| Semantic status model, fact provenance, integration rules | `13-semantic-fact-graph-and-integration.md` |
| Milestones, execution rules, acceptance | `14-execution-roadmap-issues-and-gates.md` |

## Review Target

The draft is ready for adversarial review when reviewers can falsify:

- whether `0.4.0` is sufficient as the eBUS baseline;
- whether the taxonomy prevents protocol/profile leakage;
- whether eeBUS can start raw-first without GraphQL or HA dependencies;
- whether semantic provenance is strong enough for future Modbus, CAN, UART,
  and KM-Bus families.
