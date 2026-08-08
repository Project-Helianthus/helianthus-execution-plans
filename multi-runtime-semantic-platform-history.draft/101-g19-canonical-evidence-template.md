# G19 Canonical Evidence Template

Status: `Locked`
Gate: `EEBUS-G19 direct outbound VR940 access`

G19 proves direct outbound VR940f TCP/TLS/WebSocket/SHIP access completion plus
first post-access SPINE data. It does not carry public device identity and does
not close MSP-03D unless revised G17 also passes with owner acceptance.

```yaml
schema_version: 1
gate: EEBUS-G19
repo:
  name: helianthus-eebusreg
  branch: <branch>
  commit: <sha>
commands:
  - <exact command>
environment:
  timestamp_utc: <iso8601>
  go_version: <redacted-or-public-version>
  tool_versions:
    <tool>: <version>
  topology: <redacted topology label>
trust_preconditions:
  local_identity_state: <redacted state>
  preseeded_trust_or_allowlist: <true|false>
  operator_window: <opened|closed|not_applicable>
operator_live_proof:
  result: PASS|FAIL
  redacted_json: <path>
  transcript_hashes:
    - sha256:<hash>
  first_post_access_spine_data:
    redacted_json: <path>
    data_hash: sha256:<hash>
ci_replay_authority:
  result: PASS|FAIL
  deterministic_replay_fixtures:
    - <path>
  replay_command: <exact command>
negative_cases:
  denied_access:
    result: PASS|FAIL
    evidence_hash: sha256:<hash>
  reconnect_failure:
    result: PASS|FAIL
    evidence_hash: sha256:<hash>
public_redaction:
  no_packet_captures: true
  no_raw_transcripts: true
  no_keys_pem_tokens_trust_stores: true
  no_raw_ski_shipid_ip_mac_serial: true
  full_fidelity_location: encrypted_outside_git_0600_or_discarded
owner_acceptance:
  accepted_by: <owner>
  accepted_at: <iso8601>
  notes: <redacted optional>
```

Public artifacts may contain the template's redacted JSON, UTC timestamps,
owner-acceptance metadata, and cryptographic evidence commitments. Hashes bind
only to public-safe redacted evidence or act as nonreversible commitments to
restricted evidence held outside git; they never authorize publication of the
restricted preimage. Public artifacts must not contain packet captures, raw
transcripts, keys, PEM blocks, tokens, trust stores, raw SKI, raw SHIPID, raw
IP/MAC address, or raw serial values.
