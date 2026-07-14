# Milestone map

Milestones group cross-repository work. They are not executable issues. The issue DAG in
`plan.yaml` and `90-issue-map.md` is authoritative when a grouping and an individual issue
have different readiness.

| Milestone | Depends on | Entry | Exit | Parallelism |
|---|---|---|---|---|
| M0 | - | Draft reviewed enough to identify owners | `.github` creates four repos, then four destination bootstraps and boundary docs complete | Docs can run separately; destination bootstraps wait for governance creation |
| M1 | M0 | Modbus bootstrap and M0 boundary docs complete | FMV3-M1-00 fixes FC03/FC04/FC2B-MEI0E read-only operations plus recovery/coalescing; TCP/RTU matrices prove bounded Device Identification, while RTU remains qualified or disabled experimental | One docs issue covers M1/M2; protocol runtime owns MEI framing, TCP precedes RTU, and absent RTU hardware blocks no TCP work |
| M2 | M0 | Modbusreg bootstrap, merged FMV3-M1-00 complete M2 contracts, and M1 protocol core | Per-observation logical views replay exact slices/provenance from physical wire responses; unequal-overlap and cross-unit/table/authorization/generation/deadline-incompatibility mutations plus detector/qualification/coherence conformance are stable | Reuses the one docs issue and can overlap default-disabled RTU work after shared protocol types exist |
| M3 | M2 | M2 contracts plus M1 TCP runtime available | M3-01 companion evidence and minimal SunSpec precede public STANDARD_ONLY or qualified OVERLAY_REQUIRED; either releases M4 | STANDARD_ONLY has green conformance CI and no implementation commit/empty overlay; overlay-only TDD is conditional |
| M4 | M3 | Fronius profile and TCP runtime pass | Gateway boundary/raw MCP/recovery pass; M4-04 records GO and M4-05 packages it before M5 | NO_GO/STOP is evidence, not progress; add-on recovery can develop alongside raw MCP |
| M5 | M4 | M4-04 GO plus completed M4-05 evidence exists | M5-02 docs -> M5-01 semantic contract -> M5-04 candidate semantic MCP golden/live proof -> M5-03 exact-version lock GO -> M5-09 PUBLIC_GRAPHQL_M2M_V1 docs -> GraphQL, Portal, HA, and packaged proof | M5-04 is outside CG-M5-SEMANTIC-GO; M5-03 GO gates M5-09/later only, and the two docs issues remain serialized |
| M6 | M5 | Packaged PUBLIC_GRAPHQL_M2M_V1 proof and public eeBUS/SHIP-SPINE companion are complete | Private implementation follows docs; live GO requires the same fresh Fronius observation through GraphQL+eeBUS, then M6-03 publishes reusable sanitized findings or STOP | Private-only protocol knowledge or unpublishable evidence cannot satisfy M6; replay/simulation cannot GO |
| M7 | M1, M2, M3 | FC03/FC04/FC2B-MEI0E runtime, Fronius vertical, and critical docs lane are ready | M7-01 maps every detector PDU to the runtime allowlist before SunSpec/Growatt/Huawei admission and mixed-catalog closure | Unsupported operations force non-admission; modbusreg never frames PDUs, EMMA stays fail-closed, and RTU absence blocks no TCP work |
| M8 | M0, M5 | Private repo, packaged M5-08 proof, and public Matter binding companion exist | Private kernel follows docs; exactly one authenticated/confidential/verified-server/versioned ingress passes security/recovery, then PV conformance passes | Independent of M6; reusable Matter knowledge remains public while licensed binding code stays private |

## Critical path

```text
M0 .github creation -> modbus/modbusreg destination bootstrap
  -> M1/M2 public companion docs -> protocol + TCP full-transmit response-wait/tombstone correlation
  -> M2 profile/detector/qualification/fixture contracts
  -> M3 minimal SunSpec -> Fronius STANDARD_ONLY or qualified OVERLAY_REQUIRED
  -> M4 gateway-local adapter -> raw MCP -> real-device GO + packaged evidence
  -> M5 canonical docs -> semantic code -> candidate semantic MCP golden/live proof -> exact-version lock GO -> PUBLIC_GRAPHQL_M2M_V1 docs -> confidential GraphQL implementation -> Portal -> HA -> packaged external rejection/proof
  -> M6 exact verified-identity PUBLIC_GRAPHQL_M2M_V1 ingress + private eeBUS SHIP/SPINE qualification -> live Fronius-to-myVaillant proof
```

Independent branches:

```text
M1 protocol -> physical wire-response/logical-view coalescing + abnormal write/response wait + default-disabled RTU fixture or physical qualification
M1 TCP + M2 + M3 Fronius + evidence -> M7 SunSpec -> Growatt disposition -> EMMA-negative Huawei -> catalog closure
M0 Matter bootstrap + packaged M5-08 PUBLIC_GRAPHQL_M2M_V1 -> secured sole-ingress M8 kernel + PV slice
```

M7 profile availability never bypasses a future live evidence and semantic-lock cycle for
new canonical meaning. M8 completion never gates M6.

Conditional gate mirror:

| Gate | Required outcome/evidence | Blocked ancestry otherwise |
|---|---|---|
| CG-M4-LIVE-GO | FMV3-M4-04 = GO and FMV3-M4-05 complete | All 9 M5 issues |
| CG-M5-SEMANTIC-GO | FMV3-M5-04 completed, then FMV3-M5-03 = GO on that exact version | FMV3-M5-09 and all later public/private consumers; M5-04 is never blocked by this gate |

Completion with `NO_GO` or `STOP` preserves the record but advances no milestone.
