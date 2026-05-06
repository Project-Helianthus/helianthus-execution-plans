# M7 Live Rollout Evidence - 2026-05-06

## Scope

SAS-10 live HA rollout evidence for source-selection admission after all M4
public API cleanup PRs were merged.

This run found and fixed two M7 blockers in `helianthus-ebusgateway`:

1. `bus_admission` could remain `null` after a one-shot `active_probe_passed`
   because the AD22 stability window had no delayed re-observation.
2. Source admission was incorrectly tied to Vaillant semantic/root
   confirmation. A successful bounded `0x07/0x04` active scan under
   source-selection must admit the selected source even if later semantic B524
   root confirmation remains incomplete.

The final live proof below used merged gateway `main` commit
`29c1aab1e8d99783c064f843a2a8de43095b36f2` from
`Project-Helianthus/helianthus-ebusgateway#559`.

## Inputs

- Gateway base before M7 fix: `3efe87abfc1a8a850139c3b268ea71df8a5e5c3a`
- Gateway M7 fix PR: `Project-Helianthus/helianthus-ebusgateway#559`
- Gateway final rollout commit: `29c1aab1e8d99783c064f843a2a8de43095b36f2`
- HA add-on main: `1c4988103ff402adffd11643733bb3a73a6d7007`
- Execution plan status commit before evidence: `3a8feab`
- GHCR add-on build: `25410793909`, success, manifest digest
  `sha256:7f4f85624817e90dd05640765a3227bc0e94757dc6b4cd8d7513627d7a0c79f2`

## HA Rollout

Gateway binary built locally for HA:

```sh
GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -o /tmp/helianthus-gateway ./cmd/gateway
file /tmp/helianthus-gateway
```

Observed binary type:

```text
ELF 64-bit LSB executable, ARM aarch64, statically linked
```

Add-on image was refreshed manually because HA reported no update for the same
`0.5.0` tag:

```sh
ha apps stop local_helianthus
docker pull ghcr.io/project-helianthus/helianthus-ha-addon:0.5.0
ha apps start local_helianthus
```

Wrapper proof after image refresh:

```text
Using gateway binary override from /data/helianthus-gateway
source_addr=auto; using gateway default source-selection policy
```

## Proxy Guard

M7 baseline requires eBUSd stopped and the reconnectable proxy listener disabled
or mechanically guarded.

Supervisor add-on options were updated through the Supervisor API:

```json
{
  "proxy_listen_addr": "",
  "source_addr": "auto",
  "adapter_direct_enabled": true,
  "adapter_direct_address": "ens://192.168.100.2:9999",
  "transport": "ens",
  "proxy_profile": "ens"
}
```

Process/listener proof after restart:

```text
/data/helianthus-gateway -transport adapter-direct -network tcp -address adapter-direct-ens://192.168.100.2:9999 -source-addr auto ... -external-write-policy record_and_invalidate
tcp LISTEN *:8080 users:(("helianthus-gate",...))
```

No `:19001`, `:7624`, `:8888`, or external ebusd/adapter-proxy listener was
present in the baseline listener proof.

## Final Live Status

Final GraphQL snapshot from the merged gateway `main` binary after the M7
gateway fixes and AD22 stability window:

```json
{
  "bus_admission": {
    "source_selection": {
      "state": "active",
      "outcome": "active_probe_passed",
      "selected_source": 127,
      "companion_target": 132,
      "reason": "active_probe_passed",
      "active_probe": {
        "target": 132,
        "status": "active_probe_passed"
      },
      "last_successful_source": 127,
      "retryable": false,
      "automatic_retry_scheduled": false
    }
  },
  "degraded": {
    "active": false,
    "reasons": []
  },
  "devices": [
    {
      "address": 8,
      "deviceId": "BAI00",
      "manufacturer": "Vaillant"
    }
  ],
  "zones": [],
  "dhw": null
}
```

Expvar snapshot:

```json
{
  "startup_source_selection_state": 1,
  "startup_source_selection_degraded_total": 0,
  "startup_source_selection_explicit_source_active": 0,
  "startup_source_selection_warmup_cycles_total": 1,
  "startup_source_selection_warmup_events_seen": 0
}
```

Portal proof:

```text
GET /portal/ -> HTTP 200
```

## Validation

Targeted tests:

```sh
go test ./cmd/gateway -run '^(TestRecordBusAdmissionTransitionWithStabilityRefreshPublishesOneShotActive|TestSourceAdmissionProbeSatisfied|TestShouldStopDiscoveryScan)$' -count=1
go test ./... -run 'Test(BusObservabilityStore|GraphQLBusObservability|Run_WiresBusObservability|RecordBusAdmissionTransition|SourceAdmissionProbe|ShouldStopDiscoveryScan|StartupScan)' -count=1
```

Full local CI status:

```text
TRANSPORT_MATRIX_REPORT=results-matrix-ha/20260504T183356Z-sas02-ebusgo-c9a4697-full88-correct-adapter-signal/index.json \
PASSIVE_SMOKE_REPORT=results-matrix-ha/20260505T134601Z-sas03a-gateway-passive-p01-p06-combined-pass/index.json \
./scripts/ci_local.sh

PASS: terminology, gofmt, portal assets, go vet, go build, go test -race,
source-selection artifact schema coverage, Python tests, golangci-lint,
transport gate, and passive smoke gate.
```

Transport gate report used for this rollout:

```text
results-matrix-ha/20260504T183356Z-sas02-ebusgo-c9a4697-full88-correct-adapter-signal/index.json
transport gate: PASS (pass=46, xfail=7, xpass=0, blocked=35, total=88)
```

Passive smoke report used for this rollout:

```text
results-matrix-ha/20260505T134601Z-sas03a-gateway-passive-p01-p06-combined-pass/index.json
passive smoke gate: PASS (6 passive cases, all pass)
```

GitHub PR state:

```text
Project-Helianthus/helianthus-ebusgateway#559
merge commit: 29c1aab1e8d99783c064f843a2a8de43095b36f2
checks: terminology PASS, build PASS, test PASS, lint PASS
review threads: 0 unresolved
```

## Rollback

Remove the gateway binary override and restart the add-on:

```sh
ha apps stop local_helianthus
rm -f /mnt/data/supervisor/addons/data/local_helianthus/helianthus-gateway
ha apps start local_helianthus
```

Re-enable the embedded proxy listener only for an operator-approved
coexistence/proxy run by restoring `proxy_listen_addr` to `0.0.0.0:19001`.

## Status

Baseline M7 source-selection rollout is live-green on HA with:

- eBUSd stopped;
- proxy listener disabled;
- gateway source-selection active;
- selected source `0x7F`;
- companion target `0x84`;
- no degraded admission;
- BAI00 discovered at `0x08`.

Gateway PR `#559` is merged and the live HA override was rebuilt from merged
`main`, so the baseline M7 rollout evidence is closed.
