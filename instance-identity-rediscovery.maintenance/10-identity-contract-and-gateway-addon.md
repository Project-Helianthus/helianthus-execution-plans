# Stable Helianthus Instance Identity — Contract, Gateway, Add-on

Source: [00-canonical.md](./00-canonical.md)
Canonical-SHA256: `1d501312433ef888f2447cc6fd7fb48babbb9a0f4b2fd9bd3cf398e98d3bcdf6`

Depends on: None. This chunk defines the canonical `instanceGuid` identity,
the add-on ownership contract, and the gateway surfaces that later HA work
imports.

Scope: UUIDv4 format and ownership contract, `/data/instance_guid` persistence
semantics, gateway CLI/config plumbing, Zeroconf TXT advertisement, and the
GraphQL identity surface.

Idempotence contract: Re-running add-on startup with preserved `/data` must not
change the GUID. Re-advertising mDNS and GraphQL must reuse the same configured
GUID. Re-running tests must not mutate any persistent state outside test
fixtures.

## Gateway/Add-on Tasks

1. Add `/data/instance_guid` bootstrap to the HA add-on run script
2. Validate and normalize the persisted value as lowercase UUIDv4
3. Pass the value to the gateway with `-instance-guid`
4. Add gateway config/flag validation
5. Publish `instance_guid` in Zeroconf TXT
6. Expose `gatewayIdentity.instanceGuid` in GraphQL

Falsifiability gate: Starting the add-on twice with the same `/data` must show
the same GUID. `gatewayIdentity.instanceGuid` must equal the persisted file
content. Zeroconf TXT `instance_guid` must equal the same value. Invalid GUID
input to `-instance-guid` must fail validation.

Coverage: Gateway unit tests for CLI parsing, GraphQL query surface, and mDNS
TXT payload; add-on script syntax validation; add-on docs for update versus
reinstall semantics.
