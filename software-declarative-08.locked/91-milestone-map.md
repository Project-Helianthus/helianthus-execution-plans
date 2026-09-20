# 0.8 work-package and dependency map

| ID | Release | Owner | Outcome | Prerequisites |
|---|---|---|---|---|
| DRIVER-EXTRACTION-01 | 0.8 | Project-Helianthus/.github | Native-owner driver extraction and parity | None |
| INT-18 | 0.8 | Project-Helianthus/.github | Design and implement descriptive IR/codegen, comparator and reduction measure | DRIVER-EXTRACTION-01 |
| INT-22 | 0.8 | Project-Helianthus/helianthus-gateway | Daybreak Blue review and valid-finding remediation | INT-18 |
| INT-23 | 0.8 | Project-Helianthus/helianthus-gateway | Exact-candidate real-hardware validation | INT-22 |
| INT-24 | 0.8 | Project-Helianthus/helianthus-gateway | Publish only the final validated 0.8 BOM | INT-23 |

The external prerequisite is accepted 0.7, stated in the canonical guide rather
than encoded as a dependency on a package in another plan.
`DRIVER-EXTRACTION-01` selects the actual native-owner issues; the gateway retains
only generic composition and extension hooks. Any changed candidate repeats
Daybreak plus affected hardware/conformance validation before publication.
