# MSP-03C Lab Acceptance 2026-07-08

Status: `accepted_lab_run`
Date: `2026-07-08`

## Scope

This records the accepted MSP-03C Home Assistant runtime network proof. It is
public-safe and redacted. Raw LAN addresses, command transcripts, device
identifiers, MAC addresses, serials, and secrets are intentionally not included.

The accepted artifact is
`98-msp-03c-ha-network-proof-lab-run.json`.

## Lab Result

| Gate | Result | Evidence ref |
| --- | --- | --- |
| `EEBUS-G05` listener/interface/subnet | pass | `msp03c-g05-listener-interface`, `msp03c-g05-lan-tcp` |
| `EEBUS-G06` mDNS positive | pass | `msp03c-g06-mdns-ptr`, `msp03c-g06-mdns-srv`, `msp03c-g06-mdns-a` |
| `EEBUS-G07` mDNS negative/degraded DBus | pass | `msp03c-g07-mdns-absent`, `msp03c-g07-dbus-degraded` |
| `EEBUS-G08` manual endpoint fallback | pass | `msp03c-g08-manual-endpoint` |
| `EEBUS-G09` disposable credential persistence | pass | `msp03c-g09-store-permissions`, `msp03c-g09-identity-restart` |

## What Changed From The First Attempt

The first live attempt used a temporary `zeroconf` package and failed to prove
external-peer `_ship._tcp` visibility. A follow-up diagnostic first eliminated
the off-subnet operator workstation as valid mDNS evidence, then used an
external LAN peer in the Home Assistant subnet.

The accepted run used a minimal stdlib DNS-SD proof responder bound to the
configured LAN interface. That responder advertised `_ship._tcp`, served a
manual TCP proof endpoint, wrote only a disposable proof identity under
`/data/eebus-proof`, and was removed after collection.

This proves the Home Assistant runtime and LAN path can carry SHIP-style
DNS-SD traffic. It does not claim that `enbility/eebus-go`, `zeroconf`, or a
future production runtime has selected the correct interface; that remains
inside the next runtime/fake-peer work.

## Redacted Observations

- Add-on network mode was `host`.
- The add-on did not expose a host DBus socket, so Avahi/DBus support remains
  an explicit degraded state for this runtime profile.
- The proof listener was bound to the configured LAN interface address, not to
  wildcard.
- The external LAN peer reached the proof endpoint over TCP.
- The external LAN peer resolved PTR, SRV, and A records for `_ship._tcp`.
- After the proof responder stopped, `_ship._tcp` browse/resolve returned no
  matching records.
- The disposable proof directory was `0700`; the identity file was `0600`.
- The redacted disposable identity ref survived proof restart:
  `sha256:65988afdc3a8`.

## Validation

The accepted artifact was validated with the merged add-on gate:

```bash
python3 scripts/check_eebus_ha_network_proof.py \
  --artifact ../helianthus-execution-plans/multi-runtime-semantic-platform.locked/98-msp-03c-ha-network-proof-lab-run.json \
  --mode lab
```

Expected result:

```text
eeBUS HA network proof: PASS (lab)
```

## Cleanup

The temporary proof process was stopped. The proof script, query script, ready
files, and `/data/eebus-proof` disposable store were removed from the Home
Assistant host/container and the external LAN peer.

No add-on configuration was changed. No production eeBUS runtime was enabled.
No production trust store was written.

## Decision

MSP-03C is accepted for the HA runtime network proof gate.

MSP-03D may now be filed, but remains scoped to independent black-box fake peer
and live VR940f smoke. MSP-03D must not treat this proof as an `eebus-go`
interface-selection pass.
