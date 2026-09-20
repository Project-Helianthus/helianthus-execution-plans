# 0.8 work-package and dependency map

| ID | Release | Owner | Outcome | Prerequisites |
|---|---|---|---|---|
| INT-18 | 0.8 | Project-Helianthus/.github | Descriptive IR, native-driver extraction plan, comparator and reduction measure | None |
| INT-22 | 0.8 | Project-Helianthus/helianthus-gateway | Deliver approved extraction/codegen parity across native drivers | INT-18 |
| INT-23 | 0.8 | Project-Helianthus/helianthus-gateway | Daybreak Blue review and valid-finding remediation | INT-22 |
| INT-24 | 0.8 | Project-Helianthus/helianthus-gateway | Exact-candidate real-hardware validation and release | INT-23 |

The external prerequisite is accepted 0.7, stated in the canonical guide rather
than encoded as a dependency on a package in another plan. `INT-18` selects the
actual native-owner issues; the gateway retains only generic composition and
extension hooks.

