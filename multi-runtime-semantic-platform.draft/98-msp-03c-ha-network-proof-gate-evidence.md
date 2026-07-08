# MSP-03C HA Network Proof Gate Evidence

Status: `gate_harness_merged_lab_run_pending`
Date: `2026-07-08`

## Scope

This evidence records the merged MSP-03C Home Assistant add-on proof gate:
artifact contract, validator, CI wiring, redaction policy, and canonical docs.

It does not claim MSP-03C lab acceptance. The contract fixture merged in the
add-on repository is not LAN-side lab evidence. MSP-03C remains open at the
transport-gate level until a redacted `lab_run` artifact is collected from a
real Home Assistant runtime and an external LAN peer.

MSP-03D is therefore still blocked.

## GitHub Evidence

Add-on proof gate:

- Repo: `Project-Helianthus/helianthus-ha-addon`
- Issue: [#166](https://github.com/Project-Helianthus/helianthus-ha-addon/issues/166)
- PR: [#167](https://github.com/Project-Helianthus/helianthus-ha-addon/pull/167)
- Merge commit: `b3c9930ca244dfe636f79356b8d482c6c84e043c`
- Branch: `issue/166-msp-03c-ha-eebus-network-proof`

Canonical docs gate:

- Repo: `Project-Helianthus/helianthus-docs-ebus`
- Issue: [#337](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/337)
- PR: [#338](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/338)
- Merge commit: `c1fc6bde5a273fdd1ccbe1826479769fe0731a71`
- Branch: `issue/337-msp-03c-ha-network-proof`

## Accepted Implementation

The merged add-on gate:

- adds `EEBUS_HA_NETWORK_PROOF.md`;
- adds `scripts/check_eebus_ha_network_proof.py`;
- adds the redacted contract fixture
  `scripts/fixtures/eebus_ha_network_proof_contract_pass.json`;
- adds `scripts/check_markdown_private_ips.py`;
- wires both checkers into local CI and GitHub PR CI;
- updates `SMOKE_RUNBOOK.md` to avoid private IPv4 examples;
- records that the expected SHIP discovery service is `_ship._tcp`;
- rejects relabeled contract fixtures in `--mode lab`;
- requires lab artifacts to carry branch, commit, build id, command-log ref,
  interface/subnet ref, external LAN peer ref, listener socket ref, mDNS
  browse/resolve refs, restart ref, and per-case evidence ids;
- rejects secret-bearing keys and values, PEM/private keys, MACs, device
  serial-like values, and raw IPv4/IPv6 addresses in public artifacts;
- rejects wildcard/bridge/ingress/admin/production-trust contradiction fields.

The merged docs gate:

- adds `docs/platform/eebus-ha-network-proof.md`;
- links it from the platform docs index and raw-first contract;
- states that a CI contract fixture is not lab evidence;
- requires real `lab_run` evidence before MSP-03C can be accepted;
- keeps GraphQL, Portal, Home Assistant consumers, command routing, and
  candidate semantic enrichment out of this milestone.

## Verification

Add-on local verification before merge:

```bash
python3 scripts/check_eebus_ha_network_proof.py --self-test
python3 scripts/check_eebus_ha_network_proof.py --artifact scripts/fixtures/eebus_ha_network_proof_contract_pass.json --mode contract
python3 scripts/check_markdown_private_ips.py --self-test
python3 scripts/check_markdown_private_ips.py
./scripts/ci_local.sh
python3 -m pytest tests/test_runtime_state_wrapper_red.py tests/test_source_addr_wrapper_m4.py -q
git diff --check
```

GitHub CI on add-on PR #167:

- `syntax-checks` passed.
- `Analyze (python)` passed.

Docs local verification before merge:

```bash
PATH="$PATH:$(go env GOPATH)/bin" ./scripts/ci_local.sh
git diff --check
```

GitHub CI on docs PR #338:

- `Docs Checks` passed.

## Review Ledger

GPT-only review passes were run before merge:

- `GPT-5.5 xhigh` security review flagged false lab proof by relabeling,
  secret-bearing keys, IPv6/raw IP leaks, and contradiction fields. Fixed with
  strict lab provenance, key/value redaction, raw IPv4/IPv6 rejection, and
  schema-style field allowlists. Re-review was clear.
- `GPT-5.5 high` transport review flagged lab relabeling and wrong mDNS service
  `_eebus._tcp`. Fixed with lab object requirements and exact `_ship._tcp`
  validation. Re-review was clear.
- `gpt-5.4-mini` docs/CI review flagged a broken private IPv4 regex, missing
  GitHub CI parity, and missing README validation row. Fixed with a shared
  checker, CI wiring, and README update. Re-review was clear.

## Gate Decision

MSP-03C gate harness and canonical docs are merged.

MSP-03C is not yet accepted as runtime/lab evidence. Required before MSP-03D:

- collect a redacted `lab_run` artifact from a real Home Assistant runtime;
- prove `EEBUS-G05` through `EEBUS-G09` with an external LAN peer;
- validate the artifact with
  `python3 scripts/check_eebus_ha_network_proof.py --mode lab`;
- record the accepted lab artifact in this plan.

No end-of-M3 architecture review is due yet. The M3 review must wait until
MSP-03C lab evidence and MSP-03D black-box fake peer/live VR940f smoke complete.
