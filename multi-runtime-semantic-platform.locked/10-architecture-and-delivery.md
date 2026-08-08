# Architecture And Delivery

Depends on:
The eBUS baseline and merged predecessors recorded in the issue matrix.

Scope:
Add native eeBUS transport and SPINE feature access without turning eBUS-specific
assumptions into platform contracts.

Idempotence contract:
Repeated planning or discovery does not create duplicate issues, repositories, branches,
or PRs. Existing GitHub state is reconciled before any mutation.

Falsifiability gate:
Each implementation row must have repository-owned tests and CI that can demonstrate a
failure before the implementation is accepted.

Coverage:
SHIP/SPINE foundations, raw eeBUS identity and evidence, lifecycle, read-only feature
acquisition, gateway MCP integration, live eBUS coexistence, promoted semantic facts,
and consumer rollout.

## Boundaries

- Transport owns connections and frames.
- Protocol libraries own SHIP/SPINE encoding, decoding, and state machines.
- The eeBUS registry owns raw identity, evidence, and native feature state.
- The gateway owns adapter composition and consumer APIs, not protocol truth.
- The semantic layer consumes stable observations with provenance.
- Consumers never bypass the public machine-to-machine contract.

Write paths remain separate from read paths and require explicit repository-level safety,
rollback, and hardware evidence. Planning prose is not proof of runtime behavior.
