# W30/26 Post-M6 Hardening Inventory

Date: `2026-07-26`
Classification: `Historical implementation beyond the original plan`

`92-m0-issue-matrix.yaml` records dependency guidance. Current readiness comes from GitHub and the owning code repositories.

This inventory records public-safe categories only. It does not move the
original milestone boundaries and does not disclose raw identity, endpoint,
payload, trust-store, or vendor-restricted material.

| Already-added hardening | Public-safe current-state classification |
| --- | --- |
| Trust direction | Trust is bound to authenticated peer identity and admitted runtime state, not to an assumed fixed network client/server role. |
| Transient trust | Candidate/transient trust is isolated from durable trust and cannot silently replace an admitted peer. |
| Outbound/inbound races | Simultaneous or reordered inbound/outbound establishment is resolved to one admitted session without duplicate trust or lifecycle ownership. |
| Concrete endpoint selection | Runtime selection uses an explicit configured interface/endpoint decision and fails closed rather than choosing an ambiguous wildcard route. |
| SPINE concurrency refresh | Session refresh and feature-graph publication avoid stale generation reuse and race-tested concurrent snapshot mutation. |
| Raw/redacted split | Owner-authorized `AF_UNIX` access carries the raw operator tier; public HTTP/LAN remains redacted. |
| `local_ski` correction | The local raw metadata field now carries the authorized operational identity while its public export remains redacted. |

The live public-safe inventory was observed as:

- devices: `1`;
- entities: `11`;
- features: `20`;
- use-case claims: `22`;
- distinct use-case names: `13`.

These counts prove topology/capability inventory only. They do not prove generic
SPINE function-data READ/WRITE, synchronized M6.5 values, candidate promotion,
or consumer readiness. Those are gated by the M6.25 and live-completion rows.
