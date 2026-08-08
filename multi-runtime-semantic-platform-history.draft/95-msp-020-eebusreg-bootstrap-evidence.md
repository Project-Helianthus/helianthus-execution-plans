# MSP-020 eeBUS Runtime Repo Bootstrap Evidence

Status: `completed-bootstrap`
Date: `2026-07-08`

## Scope

This evidence note records the `helianthus-eebusreg` bootstrap required before
MSP-02A can draft raw runtime identity contracts.

The bootstrap is intentionally a contract shell only. It contains no
`enbility/eebus-go` facade, listener, trust-store implementation, gateway
adapter, raw write surface, GraphQL surface, Portal surface, Home Assistant
surface, command routing, or promoted semantic facts.

## Artifacts

- Repository: https://github.com/Project-Helianthus/helianthus-eebusreg
- Issue: https://github.com/Project-Helianthus/helianthus-eebusreg/issues/1
- Bootstrap commit: `6c4fa77435db48f5cdecfb6b2d586ae0b22d8837`
- Bootstrap hardening issue: https://github.com/Project-Helianthus/helianthus-eebusreg/issues/2
- Bootstrap hardening PR: https://github.com/Project-Helianthus/helianthus-eebusreg/pull/3
- Bootstrap hardening commit: `41c0d5e9bb90ced7ae3e5a32c8870b3e330a1ef4`
- Bootstrap hardening merge commit:
  `f441e4a1987f775367ad3046e68ba1caf04b2f20`
- Module path: `github.com/Project-Helianthus/helianthus-eebusreg`

Public packages:

- `eebusruntime`
- `eebusraw`
- `eebusevidence`

## Validation

Local command:

```bash
./scripts/ci_local.sh
```

Result in `helianthus-eebusreg`: PASS.

GitHub Actions:

- https://github.com/Project-Helianthus/helianthus-eebusreg/actions/runs/28944941173
- Result: PASS for commit `6c4fa77435db48f5cdecfb6b2d586ae0b22d8837`
- https://github.com/Project-Helianthus/helianthus-eebusreg/actions/runs/28945525030
- Result: PASS for hardening commit
  `41c0d5e9bb90ced7ae3e5a32c8870b3e330a1ef4`

Covered gates:

- terminology gate;
- public package boundary;
- `enbility` import boundary;
- public export boundary;
- no premature listener or trust-store code;
- `gofmt`;
- `go vet`;
- `go build`;
- `go test -race`.

## Remaining Work

- Keep MSP-02A blocked until the M0/M1 PRs are accepted and the raw repo
  boundary is acknowledged.
