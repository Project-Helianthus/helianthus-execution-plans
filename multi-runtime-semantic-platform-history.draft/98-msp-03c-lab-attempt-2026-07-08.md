# MSP-03C Lab Attempt 2026-07-08

Status: `failed_degraded_mdns`
Date: `2026-07-08`

## Scope

This records the first live MSP-03C lab attempt after the add-on proof gate
merged. It is public-safe and redacted. Raw LAN addresses, device identifiers,
and command transcripts are intentionally not included.

This is not an accepted `lab_run` artifact.

## Attempted Topology

- Runtime host: Home Assistant add-on container with `host_network=true`.
- External peer: operator workstation on the same reachable LAN path.
- Temporary proof runtime: Python TCP listener plus `_ship._tcp` mDNS
  advertisement using a copied, temporary `zeroconf` package.
- Temporary store: `/data/eebus-proof`, disposable only.

No add-on configuration was changed. No production eeBUS runtime was enabled.
No production trust store was written.

## Observed Results

| Gate | Result | Notes |
| --- | --- | --- |
| `EEBUS-G05` listener scope | partial-pass | Listener was observed bound to the LAN interface address only, not wildcard. |
| `EEBUS-G06` mDNS positive | fail | External peer did not observe the temporary `_ship._tcp` service. |
| Existing mDNS sanity check | fail | External peer also did not observe existing browsed mDNS service classes during the attempt window. |
| `EEBUS-G08` manual endpoint fallback | pass | External peer reached the temporary TCP proof endpoint directly and received the proof banner. |
| `EEBUS-G09` disposable credential persistence | partial-pass | Store permissions were observed as `0700` directory and `0600` identity file, with a redacted identity ref emitted before cleanup. Restart continuity was not claimed because the mDNS positive gate failed first. |

## Cleanup

The temporary proof process was stopped. The temporary copied `zeroconf`
package, proof script, ready files, and `/data/eebus-proof` disposable store
were removed from the Home Assistant host/container.

## Decision

MSP-03C remains blocked on mDNS/LAN discovery diagnosis. The next attempt must
either:

- prove `_ship._tcp` browse/resolve from an external LAN peer; or
- explicitly classify missing multicast discovery as a lab/network degraded
  state and decide whether manual endpoint fallback is sufficient for the next
  milestone.

Until that decision is recorded, MSP-03D remains blocked.
