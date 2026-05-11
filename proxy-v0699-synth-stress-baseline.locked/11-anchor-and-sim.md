# Proxy v0.6.99 Chunk 11: Release Anchor + Bus Simulator + Fidelity-Min (M0..M2)

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `6f9d935e93bdf69b56928090d4f72b1fb85eed3b932549a8f0c5a615c6e19d0d`

Depends on: [10-foundations.md](./10-foundations.md) — the measurement-only
invariant, AD07 (always-on pprof), AD09 (v0.6.5 release anchor).

Scope: M0 release-anchor + bit-identical watchdog; M1 bussim package
(framing + scripted devices + admin pprof wiring); M2 simulator fidelity-min
via golden synthetic fixtures. Out of scope: scenario runner (M4),
multi-client scenarios (M5..M6), pcap replay (M8).

Idempotence contract: Bussim is additive. Reapplying M1 must not introduce
or mutate code outside `internal/emulation/bussim/` and the pprof
registration in `internal/admin/http.go`. Reapplying M2 must not modify
recorded golden fixtures; new fixtures appended only.

Falsifiability gate: M0 fails if `check_bit_identical.sh` does not flag a
SHA-mismatched §1 path. M1 fails if any PR check observes a behavior change
in `internal/proxy/**`, `internal/scheduler/**`, `internal/session/**`,
`internal/southbound/**`, `internal/northbound/**`, or if bussim's TCP
output cannot be parsed by an existing ENH/ENS client (`cmd/ebusd-compat-harness/`
or equivalent). M2 fails if bussim's byte stream for a fixture seed does
not match the committed fixture file byte-exactly across 10 deterministic
runs.

Coverage: §4 Architecture (4.1 Bus Simulator); §7 milestones M0, M1, M2.

## M0 — Release Anchor + Bit-Identical Watchdog

Single PR. Deliverables:

1. **Anchor**: Wait for `v0.6.5` tag to land on `main`. If not tagged within
   72h of M0 PR creation, escalate to operator per AD09. Record `v0.6.5`
   commit SHA in `scripts/check_bit_identical.sh`.
2. **Watchdog**: New script `scripts/check_bit_identical.sh` that:
   - For each §1-invariant path, computes `git ls-tree -r v0.6.5 -- <path>` and
     `git ls-tree -r HEAD -- <path>`, asserts identical blob SHAs.
   - Exits non-zero on first mismatch.
   - Lists explicit allowlist for `internal/admin/http.go` (AD07 exempt).
3. **CI wiring**: Append a `bit-identical-check` step to `scripts/ci_local.sh`
   that runs the watchdog. PRs in M1..M10 must pass this check.
4. **Build-tag scaffolding**: Add empty `internal/admin/pprof_register.go`
   stub with `package admin` + comment placeholder. M1 fills it in.

Acceptance: `./scripts/ci_local.sh` runs the watchdog clean against a fresh
checkout off `v0.6.5`. Intentionally introducing a one-byte diff in
`internal/proxy/*.go` makes the watchdog fail.

## M1 — bussim Package + Admin pprof Wiring

Single PR. Deliverables:

1. **bussim package** at `internal/emulation/bussim/`:
   - `framing.go` — ENH/ENS frame encode/decode. Must round-trip every frame
     emitted by `internal/southbound/` (the existing proxy code that decodes
     real-PIC framing) — this is the cross-check.
   - `devices.go` — scripted device table:
     - BAI00 at 0x08 (boiler).
     - BASV2 at 0x15 (heating-circuit slave).
     - VR_71 at 0x26 (room controller).
     - SOL00 at 0xEC (solar; stealth — same hardware as BASV2 per project memory).
     - NETX3 at 0x04/0xF6 (network).
     - Per-device: register-table stub with deterministic responses; programmable
       response latency `mean + jitter` (µs); per-register error injection knob.
   - `inject.go` — error-injection primitives: NACK, malformed CRC, byte drop,
     stuck-bus, response-timeout. Toggleable per-device per-register.
   - `bussim.go` — top-level: TCP listener accepting one connection (mimics
     real PIC's single-master link); dispatches inbound frames to device
     table; emits responses with wire-time timestamps.
   - **Wire-time ground truth**: every emitted/consumed symbol carries
     `time.Now().UnixNano()`; this is the sole source of truth for AD02
     fairness measurement.
2. **Admin pprof registration** (per AD07) in `internal/admin/http.go`:
   - Import `net/http/pprof`.
   - In `NewHandler`, after existing route registration, add:
     `mux.Handle("/debug/pprof/", http.HandlerFunc(pprof.Index))` and the four
     sub-handlers (`/debug/pprof/cmdline`, `/profile`, `/symbol`, `/trace`).
   - Also `expvar`: `mux.Handle("/debug/vars", expvar.Handler())`.
   - Single-line code addition; no other admin handler changes. Watchdog from
     M0 explicitly allowlists this file.
3. **Unit tests** for bussim framing round-trip against captured live samples
   (use existing fixtures from `internal/southbound/` test data if available;
   else use a hand-crafted minimal frame).

Acceptance: `go test ./internal/emulation/bussim/...` passes. `curl
http://localhost:<admin-port>/debug/pprof/goroutine?debug=1` returns goroutine
dump when proxy is running. Bit-identical watchdog still green
(only `internal/admin/http.go` and `internal/emulation/bussim/` changed).

## M2 — Simulator Fidelity-Min via Golden Fixtures

Single PR. Deliverables:

1. **Golden fixture format** at `test/bench/fixtures/v0.6.99/`:
   - Per fixture: input file `<name>.in.bin` (bytes the proxy would send to
     PIC), expected output file `<name>.out.bin` (bytes bussim must emit in
     reply), seed file `<name>.seed.txt`, manifest `<name>.toml` describing
     which device(s) and registers participated.
   - Initial fixtures (committed):
     - `boiler-status-read.{in,out,seed,toml}` — minimal B524 GG=0/Reg=0
       read against BAI00.
     - `dhw-temp-write.{in,out,seed,toml}` — B524 write against BAI00 DHW.
     - `zone-time-program-read.{in,out,seed,toml}` — B555 timer read against
       BASV2.
     - `scan-id.{in,out,seed,toml}` — B509 0x29 scan against VR_71.
     - `radio-device-id.{in,out,seed,toml}` — GG=0x09 OP=0x06 against VR_71.
   - **5 fixtures minimum** for v0.6.99 to ship; more added in M5/M6 as
     scenarios demand.
2. **Fidelity harness** at `test/bench/fidelity/replay_test.go`:
   - Loads each fixture, instantiates bussim with the seed and device table,
     feeds the `.in.bin` bytes, captures output, byte-diffs against
     `.out.bin`. Test fails on any mismatch.
   - Re-runs each fixture 10 times to confirm determinism (AD03).
3. **`docs/bench-spec.md § fidelity-fixtures`** — document the fixture format
   and how to add new fixtures.

Acceptance: `go test ./test/bench/fidelity/...` passes. Running the harness
ten times with same seed produces zero byte-diff across all fixtures.

## Risk Notes (carried from R1 review)

- **R1 attack A2** (sim fidelity too late) is mitigated by M2 landing
  immediately after M1 and before any scenario or metric work. The full pcap
  replay (M8) is the late-stage realism check; M2 is the lock-blocking
  minimum.
- **R1 attack A3** (AD07 invariant tension) is resolved by AD07's operator
  decision: pprof goes in `internal/admin/`, which is observation-layer.
  The watchdog allowlist makes this explicit.
- **R1 attack A6** (v0.6.5 dependency) is resolved by M0's 72h escalation
  clause and explicit anchor SHA recording.
