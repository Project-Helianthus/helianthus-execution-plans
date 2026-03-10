# Energy v1 Execution Plan 01: Source Ownership and Doc-Gates

Source: [00-canonical.md](./00-canonical.md)

Canonical-SHA256: `17af2e502f3e5588be52f7b0355743cd0840834d434b810de76f97471c3a58f3`

Depends on: None. This chunk defines the evidence model, source ownership,
doc-gates, and out-of-scope boundaries that the rest of the plan imports.

Scope: Proven versus unknown energy surfaces, `B516`/`B524` precedence,
documentation obligations, and non-goals.

Idempotence contract: Declarative-only. Reapplying this chunk must not create a
second energy source model, a generic fallback rule, or hidden hourly/power
promises.

Falsifiability gate: A review fails this chunk if it permits `B524` to suppress
`B516 today`, treats `B516` and `B524` as interchangeable, or silently expands
scope to hourly history or live power discovery.

Coverage: Summary; Sections 1-3 from the source plan.

## Summary

- Energy v1 is a split-source plan, not a single-source-with-fallback plan.
- `B516 day/current-year` owns `today so far` and completed daily history.
- `B524` owns `this month`, `last month`, and the lifetime/all-time anchor.
- Same-day local behavior is in scope. Historical hourly backfill and live
  `W`/`kW` discovery are not.

## Evidence Status

### Proven

- `B516` provides day-level energy values and is the validated local surface for
  intraday/day semantics.
- `B524` provides stable aggregate counters and remains the validated local
  surface for monthly and lifetime-style anchors.
- Home Assistant Energy Dashboard needs cumulative energy continuity, not an
  instantaneous power register, to accept backfill.

### Hypothesis

- myVaillant hourly views are not yet tied to a validated local eBUS source in
  Helianthus, so local historical hourly backfill must not be promised in v1.

### Unknown

- A validated generic power-draw register in `W` or `kW`.
- Previous-year `B516` support on target hardware.
- The exact Home Assistant version floor and anchor-tolerance constant to codify
  during implementation.

## Locked Source Rules

- `B516 day/current-year` is the only source of truth for:
  - `today so far`
  - completed daily history
  - prospective hourly Home Assistant statistics after rollout
- `B524` is the only source of truth for:
  - `this month`
  - `last month`
  - lifetime/all-time anchor
- `B524` must not zero, lock, or overwrite the `B516`-owned `today` surface.
- Consumers must not implement a cross-period fallback rule such as
  `try B516 else B524`.
- Retaining `B524` is mandatory in Energy v1 because aggregate ownership has not
  moved.

## Doc-Gates

- This plan triggers:
  - `architecture change`
  - `semantic behavior change`
  - `RE-derived protocol knowledge`
  - `GraphQL parity / consumer contract change`
- Required documentation targets:
  - `architecture/decisions.md`
  - `architecture/energy-merge.md`
  - `protocols/ebus-vaillant-B516-energy.md`
  - `protocols/ebus-vaillant-B524-register-map.md`
  - `api/graphql.md`
- No FSM document is required unless implementation adds an explicit
  energy-history lifecycle state machine.

## Scope Boundary

- Energy v1 does not include discovery of a generic live power sensor.
- Energy v1 does not include historical hourly backfill.
- If a local hourly source is proven later, that becomes a follow-up plan rather
  than an implicit scope extension here.
- Transport-gate applicability remains unresolved at plan level and must be
  decided in each concrete gateway pre-execution checklist.
