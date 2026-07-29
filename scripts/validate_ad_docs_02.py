#!/usr/bin/env python3
"""Typed, fail-closed validator for the active eeBUS control plane."""
from __future__ import annotations

import hashlib
import html
import json
import re
import subprocess
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN = "multi-runtime-semantic-platform.locked"
ANCHOR = "f25d9ac7d3f25f0f45821cdff27ff968a0ef5cfb"
MATRIX = "92-m0-issue-matrix.yaml"
INTEGRITY = "106-ad-docs-02-integrity.json"
EXACT_IDS = (
    "MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C",
    "MSP-020", "MSP-02A", "MSP-02B", "MSP-02C", "MSP-03A", "MSP-03B",
    "MSP-03C", "MSP-03D-G01", "MSP-R00", "MSP-R00-L", "DOCS-VERIFY",
    "MSP-DOCS-API-SCHEMA", "MSP-DOCS-PLATFORM", "MSP-DOCS-E2",
    "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH",
    "MSP-DOCS-E2R-AGGREGATE", "MSP-DOCS-CLEAN",
    "MSP-DOCS-CANDIDATE-CLEANUP", "MSP-03D-R", "MSP-035", "MSP-04A",
    "MSP-036", "MSP-DOCS-API-CANDIDATE", "MSP-055", "MSP-DOCS-API-FREEZE",
    "MSP-04B", "MSP-04C", "MSP-045", "MSP-05A", "MSP-DOCS-05P",
    "MSP-05P-SHIP", "MSP-05P-EEBUS", "MSP-05P-REG-API-V2",
    "MSP-05P-REG-ID", "MSP-05P-REG-RUNTIME", "MSP-05P-REG-API-V1-CLEANUP",
    "MSP-05A-R1", "MSP-05B-PLAN-R1", "MSP-05A-R2", "MSP-05B", "MSP-06",
    "MSP-0625-PLAN", "MSP-0625-DOCS-E", "MSP-0625-SPINE",
    "MSP-0625-EEBUS", "MSP-0625-REG-EXEC", "MSP-0625-REG-MUT",
    "MSP-0625-GW-ROUTER", "MSP-0625-GW-MCP", "MSP-0625-LAB",
    "MSP-0625-DOCS-P", "MSP-0625-S13-DOCS", "MSP-0625-S13-SPINE",
    "MSP-0625-S13-EEBUS", "MSP-0625-S13-REG",
    "MSP-0625-S13-GW-LAB", "MSP-065", "MSP-07", "MSP-08", "MSP-085",
    "MSP-065-LIVE-R1", "MSP-07-LIVE-R1", "MSP-08-LIVE-R1",
    "MSP-085-LIVE-R1", "MSP-09A", "MSP-09B", "MSP-09C", "MSP-09D",
)
E2_ROOTS = (
    "62e4c2f2022c22f5129db923079268aafdc5617b",
    "6476e39811677041ba11911457baab4c602ac557",
)
SERIAL_EDGES = {
    "MSP-DOCS-E2R-PLATFORM": ["MSP-DOCS-E2"],
    "MSP-DOCS-E2R-PUBLISH": ["MSP-DOCS-E2R-PLATFORM"],
    "MSP-DOCS-E2R-AGGREGATE": ["MSP-DOCS-E2R-PUBLISH"],
    "MSP-DOCS-CLEAN": ["MSP-DOCS-E2R-AGGREGATE"],
    "MSP-03D-R": ["MSP-DOCS-CLEAN", "MSP-03C"],
}
REQUIRES_COMPLETION_TOKENS = {
    "MSP-00A": [], "MSP-00B": ["MSP-00A"], "MSP-00C": ["MSP-00A"], "MSP-01A": ["MSP-00A"],
    "MSP-01B": ["MSP-01A"], "MSP-01C": ["MSP-01B"],
    "MSP-020": ["MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C"],
    "MSP-02A": ["MSP-00A", "MSP-00B", "MSP-00C", "MSP-01A", "MSP-01B", "MSP-01C", "MSP-020"],
    "MSP-02B": ["MSP-02A"], "MSP-02C": ["MSP-01A", "MSP-02B"], "MSP-03A": ["MSP-02C"],
    "MSP-03B": ["MSP-03A"], "MSP-03C": ["MSP-03A", "MSP-03B"], "MSP-03D-G01": ["MSP-03C"],
    "MSP-R00": [], "MSP-R00-L": [], "DOCS-VERIFY": [], "MSP-DOCS-API-SCHEMA": ["DOCS-VERIFY"],
    "MSP-DOCS-PLATFORM": ["MSP-R00-L", "MSP-DOCS-API-SCHEMA"], "MSP-DOCS-E2": ["MSP-DOCS-PLATFORM"],
    "MSP-DOCS-E2R-PLATFORM": ["MSP-DOCS-E2"], "MSP-DOCS-E2R-PUBLISH": ["MSP-DOCS-E2R-PLATFORM"],
    "MSP-DOCS-E2R-AGGREGATE": ["MSP-DOCS-E2R-PUBLISH"], "MSP-DOCS-CLEAN": ["MSP-DOCS-E2R-AGGREGATE"],
    "MSP-DOCS-CANDIDATE-CLEANUP": ["MSP-DOCS-E2R-PUBLISH"], "MSP-03D-R": ["MSP-DOCS-CLEAN", "MSP-03C"],
    "MSP-035": ["MSP-03D-R"], "MSP-04A": ["MSP-035"], "MSP-036": ["MSP-04A"],
    "MSP-DOCS-API-CANDIDATE": ["MSP-036", "MSP-DOCS-E2"], "MSP-055": ["MSP-036", "MSP-DOCS-API-CANDIDATE"],
    "MSP-DOCS-API-FREEZE": ["MSP-055"], "MSP-04B": ["MSP-DOCS-API-FREEZE"], "MSP-04C": ["MSP-04B"],
    "MSP-045": ["MSP-04C"], "MSP-05A": ["MSP-045"],
    "MSP-DOCS-05P": ["MSP-05A", "MSP-045"],
    "MSP-05P-SHIP": ["MSP-DOCS-05P"],
    "MSP-05P-EEBUS": ["MSP-05P-SHIP"],
    "MSP-05P-REG-API-V2": ["MSP-05P-EEBUS"],
    "MSP-05P-REG-ID": ["MSP-05P-REG-API-V2"],
    "MSP-05P-REG-RUNTIME": ["MSP-05P-REG-ID"],
    "MSP-05P-REG-API-V1-CLEANUP": ["MSP-05P-REG-RUNTIME"],
    "MSP-05A-R1": ["MSP-05P-REG-API-V1-CLEANUP"],
    "MSP-05B-PLAN-R1": ["MSP-05A-R1", "MSP-05P-REG-RUNTIME", "MSP-DOCS-05P"],
    "MSP-05A-R2": ["MSP-05B-PLAN-R1"],
    "MSP-05B": ["MSP-05A-R2", "MSP-05P-REG-RUNTIME", "MSP-DOCS-05P"],
    "MSP-06": ["MSP-05B"],
    "MSP-0625-PLAN": ["MSP-06"],
    "MSP-0625-DOCS-E": ["MSP-0625-PLAN"],
    "MSP-0625-SPINE": ["MSP-0625-DOCS-E"],
    "MSP-0625-EEBUS": ["MSP-0625-SPINE"],
    "MSP-0625-REG-EXEC": ["MSP-0625-EEBUS"],
    "MSP-0625-REG-MUT": ["MSP-0625-REG-EXEC"],
    "MSP-0625-GW-ROUTER": ["MSP-0625-REG-MUT"],
    "MSP-0625-GW-MCP": ["MSP-0625-GW-ROUTER"],
    "MSP-0625-LAB": ["MSP-0625-GW-MCP"],
    "MSP-0625-DOCS-P": ["MSP-0625-DOCS-E"],
    "MSP-0625-S13-DOCS": ["MSP-0625-LAB", "MSP-0625-DOCS-P"],
    "MSP-0625-S13-SPINE": ["MSP-0625-S13-DOCS"],
    "MSP-0625-S13-EEBUS": ["MSP-0625-S13-SPINE"],
    "MSP-0625-S13-REG": ["MSP-0625-S13-EEBUS"],
    "MSP-0625-S13-GW-LAB": ["MSP-0625-S13-REG"],
    "MSP-065": ["MSP-06"], "MSP-07": ["MSP-065"], "MSP-08": ["MSP-07"],
    "MSP-085": ["MSP-08"],
    "MSP-065-LIVE-R1": [
        "MSP-0625-LAB", "MSP-0625-DOCS-P", "MSP-0625-S13-GW-LAB",
    ],
    "MSP-07-LIVE-R1": ["MSP-065-LIVE-R1"],
    "MSP-08-LIVE-R1": ["MSP-07-LIVE-R1"],
    "MSP-085-LIVE-R1": ["MSP-08-LIVE-R1"],
    "MSP-09A": ["MSP-085-LIVE-R1"],
    "MSP-09B": ["MSP-09A", "MSP-085-LIVE-R1"],
    "MSP-09C": ["MSP-09A", "MSP-09B", "MSP-085-LIVE-R1"],
    "MSP-09D": ["MSP-09A", "MSP-09C", "MSP-085-LIVE-R1"],
}
EVIDENCE_INPUTS = {row_id: [] for row_id in EXACT_IDS} | {
    "MSP-R00-L": ["Project-Helianthus/helianthus-eebusreg#14"], "MSP-03D-R": ["MSP-03D-G01"],
}
PRESERVED_ACCEPTED_IDS = tuple(
    row_id
    for row_id in EXACT_IDS[:EXACT_IDS.index("MSP-06") + 1]
    if row_id != "MSP-DOCS-CANDIDATE-CLEANUP"
)
ACCEPTANCE_STATES = {row_id: "proposed" for row_id in EXACT_IDS}
ACCEPTANCE_STATES.update({row_id: "accepted" for row_id in PRESERVED_ACCEPTED_IDS})
ACCEPTANCE_STATES.update({
    "MSP-03D-G01": "accepted_partial_no_successor_unlock",
    "MSP-R00": "completed_local_no_code_acceptance",
    "MSP-DOCS-CANDIDATE-CLEANUP": "dormant_conditional",
    "MSP-0625-PLAN": "completed_published",
    "MSP-0625-DOCS-E": "completed_published",
    "MSP-0625-SPINE": "completed_published",
    "MSP-0625-EEBUS": "completed_published",
    "MSP-0625-REG-EXEC": "completed_published",
    "MSP-0625-REG-MUT": "completed_published",
    "MSP-0625-GW-ROUTER": "completed_published",
    "MSP-0625-GW-MCP": "completed_published",
    "MSP-0625-LAB": "release_proof_pending",
    "MSP-0625-DOCS-P": "completed_published",
    "MSP-065": "framework_complete",
    "MSP-07": "synthetic_only",
    "MSP-08": "synthetic_only",
    "MSP-085": "synthetic_only",
})
CURRENT_AMENDMENT_COUNT = 9
CURRENT_AMENDMENT = "M6.25 bounded SPINE 1.3 erratum"
CURRENT_ACCEPTED_THROUGH = (
    "Base M6.25 LAB remains accepted after released-chain redeploy, but "
    "stable-MCP/M6.25 final closure is held by the bounded SPINE 1.3 erratum; "
    "zero promoted leaves"
)
RELEASE_PROOF_STATES = {
    "released_chain_redeployed": {
        "cruise_phase": "MSP-0625-S13-DOCS",
        "current_milestone": "MSP-0625-S13-DOCS",
        "lab_acceptance_state": "accepted",
        "selected_batch": ["MSP-0625-S13-DOCS"],
        "accepted_through": CURRENT_ACCEPTED_THROUGH,
    },
}
RELEASE_PROJECTION_SURFACES = (
    "00-canonical.md",
    "01-index.md",
    "14-execution-roadmap-issues-and-gates.md",
    "90-issue-map.md",
    "91-milestone-map.md",
    "99-status.md",
    "123-w31-26-m625-spine-13-erratum.md",
)
RELEASE_PROJECTION_RE = re.compile(
    r"<!-- M625_RELEASE_PROJECTION_BEGIN -->\n.*?"
    r"<!-- M625_RELEASE_PROJECTION_END -->",
    re.DOTALL,
)
CURRENT_SUCCESSOR_UNLOCK_CONDITION = (
    "M6.25 SPINE 1.3 erratum and live DAG complete through "
    "MSP-085-LIVE-R1 and "
    "promoted_leaf_count is greater than zero before M9"
)
PRE_M625_HISTORY_SHA256 = "d9b5db0aca18e0732fc352b388fb06b76b5cdb44830970f448f337ffbec9ba4f"
LOCKED_ACCEPTANCE = {
    "MSP-05B-PLAN-R1": [
        "the locked DAG inserts MSP-05A-R2 before MSP-05B and names MSP-05A-R2 as the sole next-ready row",
        "the MSP-05B rollback retains the merged eebusreg dependency and the inert MSP-05A-R1 mapper/state",
        "runtime Start is classified as synchronous acquisition and worker launch only, with no sustained-readiness claim",
        "the disabled MSP-05B path requires zero resolver, New, Start, and Shutdown calls",
        "93-eebus-transport-gate-v0.md remains semantically unchanged",
    ],
    "MSP-05A-R2": [
        "a tests-only commit is observed RED by external CI before implementation",
        "the exact implementation head is observed GREEN by external CI after implementation",
        "main is the sole process-exit boundary; gateway workers and helpers return wrapped errors instead of calling Fatal, Fatalf, Fatalln, os.Exit, or equivalent termination primitives",
        "remote SKIs are emitted as lowercase ascending values while nil versus explicit empty is preserved and duplicates remain case-insensitively rejected",
        "cleanup reached through newly returned errors is bounded, idempotent, race-free, and preserves error causes",
        "no sidecar lifecycle, socket, discovery, trust, MCP, GraphQL, semantic, or eBUS transport behavior is added",
    ],
    "MSP-05B": [
        "prior canonical docs and eebusreg contracts are merged",
        "disabled configuration performs zero resolver, runtime New, Start, and Shutdown calls",
        "interface resolution uses net.InterfaceByName plus typed *net.IPNet or *net.IPAddr conversion; IPv6 link-local addresses alone receive the selected interface zone and unknown address types fail closed",
        "runtime construction or Start failure aborts gateway startup, every constructed runtime is shut down exactly once, and errors.Join combines Shutdown failure with any existing run error including later eBUS or HTTP startup failures",
        "lifecycle tests prove errors.Is reaches both the existing run error and the Shutdown error after errors.Join",
        "runtime Start proves synchronous acquisition and worker launch only; no sustained gateway-readiness monitor or claim is introduced",
        "eBUS transport/router/registry code paths are unchanged",
        "disabled default leaves eBUS CI and transport matrix unchanged",
    ],
}
M625_ACCEPTANCE_FRAGMENTS = {
    "MSP-0625-PLAN": (
        "100-topology-audit.md is byte-identical",
        "historical framework and synthetic rows cannot unlock",
        "promoted_leaf_count greater than zero",
    ),
    "MSP-0625-SPINE": (
        "callback registration completes before send",
        "synchronous reply during send",
        "clean callbacks",
        "monotonic keys and tombstones prevent late-reply ABA reuse",
    ),
    "MSP-0625-EEBUS": (
        "only full READ and full WRITE",
        "partial, selectors, filterDelete, and invoke emit zero frames",
    ),
    "MSP-0625-REG-EXEC": (
        "runtime_epoch",
        "connection_generation",
        "stale token or session binding emits zero frames",
        "JCS",
    ),
    "MSP-0625-REG-MUT": (
        "one global runtime writer lease",
        "idempotency is scoped",
        "constraints_unknown",
        "fresh full READ under the writer lease",
        "mismatch emits zero WRITE frames",
        "ACK or send success alone is never applied",
        "probe TTL survives restart",
        "rollback_intent restart reacquires the lease",
        "outcome_unknown converges by readback",
    ),
    "MSP-0625-GW-ROUTER": (
        "public denial precedes provider, router, runtime, connection, and remote contact",
    ),
    "MSP-0625-GW-MCP": (
        "exactly features.get, features.data.get, features.data.set, mutations.get, mutations.rollback",
        "owner-authorized AF_UNIX",
        "integrated public denial causes zero provider, router, runtime, connection, and remote contact",
        "no v2, aliases, candidate_ref, semantics, GraphQL, Portal, or HA",
    ),
    "MSP-0625-LAB": (
        "restart during probe TTL",
        "public denial at the registered tool boundary proves zero provider, router, runtime, connection, and remote contact",
        "anti-leak checks pass",
    ),
    "MSP-0625-S13-DOCS": (
        "only bounded SPINE 1.3",
        "49 READ declarations, 26 successes, and 23 failures",
        "no raw identity",
        "exact five M6.25 tool suffixes and candidate_ref prohibition",
        "READ-only",
        "base M6.25 LAB remains accepted",
    ),
    "MSP-0625-S13-SPINE": (
        "pinned minimal provenance scopes",
        "relevant 4f986b selector",
        "identifier value-type portion of 9970150",
        "SPINE 1.4 remain excluded",
        "no update-engine behavior",
    ),
    "MSP-0625-S13-EEBUS": (
        "without a new executor or namespace",
        "authorize no WRITE",
        "no SPINE 1.4",
    ),
    "MSP-0625-S13-REG": (
        "without changing its public method set",
        "every no-write stop remain unchanged and fail-closed",
        "no raw identity",
    ),
    "MSP-0625-S13-GW-LAB": (
        "exact five M6.25 tool suffixes",
        "all 49 declared READ targets",
        "all 26 baseline-success targets remain successful",
        "no HVAC description READ ends internal because of a factory type mismatch",
        "superseded scalar-versus-list or enum-versus-scaled-number model",
        "typed-empty is not silently promoted to successful non-empty data",
        "operationModeId=2 remains unlabeled",
        "raw identity remains owner-local",
        "zero remote mutation",
        "candidate_ref",
    ),
    "MSP-085-LIVE-R1": (
        "JCS digest-bound machine-checkable promoted_leaf_count greater than zero",
    ),
}
M625_TOOL_SUFFIXES = [
    "features.get",
    "features.data.get",
    "features.data.set",
    "mutations.get",
    "mutations.rollback",
]
M625_S13_ISSUE_CHAIN = [
    "Project-Helianthus/helianthus-docs-eebus#96",
    "Project-Helianthus/helianthus-spine-go#15",
    "Project-Helianthus/helianthus-eebus-go#23",
    "Project-Helianthus/helianthus-eebusreg#103",
    "Project-Helianthus/helianthus-ebusgateway#762",
]
M625_S13_IDS = (
    "MSP-0625-S13-DOCS",
    "MSP-0625-S13-SPINE",
    "MSP-0625-S13-EEBUS",
    "MSP-0625-S13-REG",
    "MSP-0625-S13-GW-LAB",
)
M625_S13_PUBLIC_BASELINE = {
    "operation": "READ",
    "declared": 49,
    "success": 26,
    "failure": 23,
    "evidence_sha256": {
        "declarations": "6ff2d9061dab29b32ed2914377aabea0b2a1dcb8c7345023f7e5870442a553b8",
        "targets": "00cd8388b5f384c0d77a56c2de59045f0514759f115c05a44544f7abbee3aa43",
        "result_table": "f106bb5ba09ff7bb14230fac48113dedce152e5887d6b2a27beaf3b0998d7cf9",
    },
    "raw_identity": "excluded",
}
M625_S13_SCOPE_PROVENANCE = {
    "specification": "SPINE 1.3",
    "included": [
        {
            "commit": "d5f89c767706ef411fc622cd6771c479b7fd1b26",
            "scope": (
                "relevant setpoint-description, selector, HVAC relation "
                "value-type, and function-data factory corrections"
            ),
        },
        {
            "commit": "a6cb0727a1509dd04454c8e8edce899f4111fb3a",
            "scope": (
                "relevant HVAC system-function selector and operation-mode "
                "relation value-type corrections"
            ),
        },
        {
            "commit": "4f986b14324a0d9ed719121b82c2621d50f58303",
            "scope": (
                "relevant HVAC system-function operation-mode selector "
                "correction only"
            ),
        },
        {
            "commit": "9970150f6d81ffa06605fecddedcdf0e38174543",
            "scope": (
                "identifier value-type portion only for setpoint description "
                "MeasurementId and TimeTableId"
            ),
        },
    ],
    "excluded": [
        '9970150 eebus:key/update-engine changes, including eebus:"key" tags',
        "9f07e2a and 06d9bf0 duplicate cherry-picks",
        "upstream dev wholesale merge",
        "SPINE 1.4",
    ],
}
M625_S13_ACCEPTANCE = {
    "MSP-0625-S13-DOCS": (
        "only bounded SPINE 1.3 value-type and function-data factory corrections are in scope; SPINE 1.4 is excluded",
        "the public baseline is exactly 49 READ declarations, 26 successes, and 23 failures with the three pinned evidence hashes",
        "public evidence contains no raw identity, endpoint, target address, payload, transcript, trust material, or restricted preimage",
        "the exact five M6.25 tool suffixes and candidate_ref prohibition remain unchanged",
        "erratum execution is READ-only and every existing no-write stop remains fail-closed",
        "base M6.25 LAB remains accepted while stable-MCP/M6.25 final closure is held by this erratum",
    ),
    "MSP-0625-S13-SPINE": (
        "implementation is derived only from the pinned minimal provenance scopes and not from wholesale cherry-picks",
        "d5f89c, a6cb072, the relevant 4f986b selector, and only the identifier value-type portion of 9970150 are covered by focused tests",
        "9970150 eebus:key/update-engine changes, duplicate 9f07e2a/06d9bf0 cherry-picks, upstream dev wholesale merge, and SPINE 1.4 remain excluded",
        "no update-engine behavior, write path, transport, SHIP, or public/raw boundary changes",
    ),
    "MSP-0625-S13-EEBUS": (
        "existing exact feature and function selection consumes the corrected SPINE 1.3 types without a new executor or namespace",
        "erratum tests perform READ only and authorize no WRITE, partial operation, selector, filterDelete, or invoke",
        "no SPINE 1.4, upstream dev wholesale merge, semantic mapping, or consumer behavior enters scope",
    ),
    "MSP-0625-S13-REG": (
        "RawFeatureRuntimeV1 represents corrected SPINE 1.3 READ results without changing its public method set",
        "existing runtime_epoch, connection_generation, read-token, JCS, and public-redaction invariants remain exact",
        "RawMutationRuntimeV1, mutation FSM, write authorization, and every no-write stop remain unchanged and fail-closed",
        "no raw identity or restricted preimage enters public evidence",
    ),
    "MSP-0625-S13-GW-LAB": (
        "the gateway uses the existing EEBusCommandRouter and exact five M6.25 tool suffixes with no added alias or namespace",
        "all 49 declared READ targets are each attempted and receive one terminal classification against the immutable 26-success and 23-failure public baseline",
        "all 26 baseline-success targets remain successful",
        "no HVAC description READ ends internal because of a factory type mismatch",
        "no setpoint-description or HVAC-relation READ fails because of the superseded scalar-versus-list or enum-versus-scaled-number model",
        "every residual result is function/correlation-bound and classified as typed-empty reply, remote rejection, unknown field, or another identified model mismatch; typed-empty is not silently promoted to successful non-empty data",
        "operationModeId=2 remains unlabeled unless its nominal description is actually read",
        "public evidence is aggregate and commitment-only; raw identity remains owner-local and absent from public output",
        "every WRITE, SET, rollback dispatch, and mutation probe remains stopped with zero remote mutation",
        "candidate_ref, semantics, GraphQL, Portal, Home Assistant, and consumer promotion remain prohibited",
    ),
}
M625_S13_SUCCESSOR = "123-w31-26-m625-spine-13-erratum.md"
IMMUTABLE_ACTIVE_SHA256 = {
    "100-topology-audit.md": (
        "b84c74551e839a3869a775c2f94c1f0121f2cfe477fe58a076e53bd57568f4d2"
    ),
    "106-ad-docs-02-integrity.json": (
        "1f9d40d669d3e3ede32b521d9338832062bb80fecd789d388f27d890ac69c25b"
    ),
}
M625_MUTATION_CORRECTION = (
    "121-w31-26-m625-raw-mutation-contract-correction.md"
)
M625_IMPLEMENTATION_RECONCILIATION = (
    "122-w31-26-m625-implementation-state-reconciliation.md"
)
M625_IMPLEMENTATION_RECEIPTS = (
    "MSP-0625-PLAN: helianthus-execution-plans PR77 fb384ab57d79f0020c54d2c66416e8a7666f0ceb; PR83 0aa8c131cbe7ea5096557f1a46ea6fa3164d143f",
    "MSP-0625-DOCS-E: helianthus-docs-eebus PR77 cedf238e34f879815ba773e9cd76b2b31c2822a3; PR85 401b46d6fd6834eeaaf861345d0392d26bfb9605; PR89 03e2b126ccfed7f3782ca5078c86a53c9ecc8fae; PR91 7e29d1253b7a6f271258e3fa319dfb26915439e; PR93 1ea36df153f9fac7cd4e17d44fd947525711ddc0",
    "MSP-0625-SPINE: helianthus-spine-go PR10 a35ec1c48a6cdd2cdcb9b6e56086360824fb21f2",
    "MSP-0625-EEBUS: helianthus-eebus-go PR20 41c2d2ed73baf887ee69a364797c1d6ff74ab426",
    "MSP-0625-REG-EXEC: helianthus-eebusreg PR84 4a0af028276db7d32a9454386b643138e84c555e; PR86 b4903d4b0020cf4651d78021e0996b3fad01932c",
    "MSP-0625-REG-MUT: helianthus-eebusreg PR88 19874f0ebd57be7d1cf3ab9b7ee7aaac175a2dd9; PR90 63e43d94024d101cea882697acb5436a3b51fc77; PR92 0f2c0d343ffd615efaa7c789b720c52bae20c337; PR94 4afad3e9083b7a6f271258e3fa319dfb26915439; PR96 5528b436f814f1867138a1d7da9354c665916f28; PR98 709a5473de26bbaaa625cdfead555872edea5cab",
    "MSP-0625-GW-ROUTER: helianthus-ebusgateway PR748 54efe461f27a0115c2a038d4c56ace1ea2c6f39e; PR750 fcad9c8c80101cb31a7707e21846bca24bbbf40a; PR752 4ffb02891ddb1b1d406c9e72a7a5ab804f11c586; PR754 dc27adf161562108c4c611bd9d2706721339281e; PR756 defe6b5d0ba0cfce4174e21429dbf23e3eae1a6a; PR757 0788ee2929d71cb4a099157f2422d26fedf6768f",
    "MSP-0625-GW-MCP: helianthus-ebusgateway PR758 335ee0a6598de44fb7ca426995afb0b24e9b7331; PR760 cbf7c8e082fc19e2f0bc652270c977e0b16ed159",
    "MSP-0625-DOCS-P: helianthus-docs-ebus PR381 fdacb676ef3ff6e25a2fa53149a18de996635d1e",
)
M625_NO_EFFECT_DTO = {
    "state": "no_effect",
    "protocol_accepted": None,
    "observed_after": "before_image",
    "error": {"code": "no_effect", "retriable": False},
    "outcome_evidence": {
        "possible_side_effect": True,
        "blind_retry_forbidden": True,
        "last_durable_state": "dispatch_intent",
        "recorded_at": "<time>",
    },
    "no_effect_verification": {
        "relation": "observed_after_equals_before",
        "verified": True,
        "equal_value_hash": "<HashV1>",
        "verified_at": "<time>",
    },
}
M625_MUTATION_CORRECTION_FRAGMENTS = (
    "ErrorV1 {code: no_effect, retriable: false}",
    "OutcomeEvidenceV1",
    "does not prove that the remote endpoint never transiently executed",
    "uncertainty evidence proves that dispatch may have occurred",
    "correlated protocol rejection remains `rejected`",
    "trustworthy third value is `conflict`",
    "untrustworthy readback remains `outcome_unknown`",
    "read-only `RawFeatureRuntimeV1` interface and existing `Runtime`",
    "separate `RawMutationRuntimeV1`",
    "explicitly assert `RawMutationRuntimeV1` capability",
    "`WriteAuthorizationV1` is distinct",
    "`mutations.get` remains read authorization",
    "does not change the M6.25 DAG",
    "does not rename or add any MCP tool",
    "No v2 or legacy interface",
    "`candidate_ref`",
    "consumer promotion",
    "helianthus-docs-eebus#78",
    "helianthus-eebusreg#85",
)
M625_RECOVERY_MATRIX = (
    (
        "Trustworthy full READ equals before-image",
        "`no_effect`",
        "`null`",
    ),
    (
        "Uncertainty evidence plus trustworthy full READ equals requested value",
        "`applied` or `probe_active`",
        "`null`",
    ),
    (
        "Trustworthy correlated rejection",
        "`rejected`",
        "`false`",
    ),
    (
        "Trustworthy full READ equals a third value",
        "`conflict`",
        "`null`",
    ),
    (
        "Readback unreadable or untrustworthy",
        "`outcome_unknown`",
        "`null`",
    ),
)
M625_MUTATION_DOC_GATE = {
    "contract_gate": {
        "prerequisite": "Project-Helianthus/helianthus-docs-eebus#78",
        "gated": "Project-Helianthus/helianthus-eebusreg#85",
        "transition": "before_strict_red_publication",
    }
}
LIVE_COMPLETION_TOKEN_CONTRACT = {
    "schema": "helianthus.m625-live-promotion",
    "version": 1,
    "milestone_id": "MSP-085-LIVE-R1",
    "canonicalization": "RFC8785_JCS",
    "digest": "SHA-256",
    "digest_bound_fields": [
        "milestone_id",
        "promoted_leaf_count",
        "promotion_dossier_root",
        "evidence_root",
    ],
    "promoted_leaf_count": {
        "type": "integer",
        "exclusive_minimum": 0,
    },
}
M9_UNLOCK_PREDICATE = {
    "completion_token": "MSP-085-LIVE-R1",
    "digest_bound": True,
    "field": "promoted_leaf_count",
    "operator": "greater_than",
    "value": 0,
}
BASE_ROW_KEYS = frozenset({"id", "title", "repo", "milestone", "complexity", "docs_owner", "doc_gate", "security_gate", "transport_gate", "rollback_ledger", "review_ledger", "tdd_mode", "smoke_scope", "acceptance_state", "requires_completion_tokens"})
NO_ACCEPTANCE = frozenset({"MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH", "MSP-DOCS-E2R-AGGREGATE"})
ROW_EXTRAS = {
    "MSP-R00": frozenset({"acceptance", "architecture_review", "coordination_note", "issue", "successor_unlocks"}),
    "MSP-R00-L": frozenset({"acceptance", "completion_note", "evidence_inputs"}),
    "DOCS-VERIFY": frozenset({"acceptance", "completion_note", "coordination_note"}),
    "MSP-DOCS-API-SCHEMA": frozenset({"acceptance", "readiness_note"}),
    "MSP-DOCS-PLATFORM": frozenset({"acceptance", "blocked_note"}),
    "MSP-DOCS-E2R-AGGREGATE": frozenset({"issue_ref"}),
    "MSP-DOCS-CANDIDATE-CLEANUP": frozenset({"acceptance", "conditional"}),
    "MSP-03D-R": frozenset({"acceptance", "evidence_inputs"}),
    "MSP-0625-GW-MCP": frozenset({"tool_suffixes"}),
    "MSP-0625-S13-DOCS": frozenset({"acceptance", "issue_ref", "public_baseline"}),
    "MSP-0625-S13-SPINE": frozenset({"acceptance", "issue_ref", "scope_provenance"}),
    "MSP-0625-S13-EEBUS": frozenset({"acceptance", "issue_ref"}),
    "MSP-0625-S13-REG": frozenset({"acceptance", "issue_ref"}),
    "MSP-0625-S13-GW-LAB": frozenset({"acceptance", "issue_ref"}),
    "MSP-085-LIVE-R1": frozenset({"completion_token_contract"}),
    "MSP-09A": frozenset({"unlock_predicate"}),
    "MSP-09B": frozenset({"unlock_predicate"}),
    "MSP-09C": frozenset({"unlock_predicate"}),
    "MSP-09D": frozenset({"unlock_predicate"}),
}
HISTORICAL_IDS = frozenset(EXACT_IDS[:17])
def readiness(matrix: dict[str, Any]) -> dict[str, list[str]]:
    """Derive dispatch from released LAB proof plus the active erratum hold."""
    state = matrix.get("lab_release_proof")
    if state not in RELEASE_PROOF_STATES:
        fail("matrix: LAB release-proof control drift")
    next_batch = RELEASE_PROOF_STATES[state]["selected_batch"]
    return {
        "historical_snapshot": list(PRESERVED_ACCEPTED_IDS),
        "logical_ready": next_batch,
        "dispatchable": next_batch,
        "selected_batch": next_batch,
    }
MATRIX_ROOT_KEYS = frozenset({
    "schema_version", "status", "plan", "baseline", "cruise_phase", "current_milestone",
    "amendment_count", "amended_on", "amendment", "accepted_through", "dirty_rescue_candidate",
    "successor_unlocks", "successor_unlock_condition", "lab_release_proof", "msp_r00_status", "msp_r00_issue",
    "msp_r00_architecture_review", "purpose", "serialization", "gate_catalog", "ownership_contract",
    "public_evidence_privacy", "issues", "routing_policy",
})
PLAN_ROOT_KEYS = frozenset({
    "slug", "title", "state", "cruise_phase", "amendment_count", "amended_on",
    "amendment", "source_discussion", "target_repos", "knowledge_repo",
    "platform_docs_owner", "protocol_knowledge_repo", "protocol_native_docs_repo",
    "cross_seed_target_repo", "canonical_file", "split_index", "started_on", "locked_on",
    "current_milestone", "lab_release_proof", "accepted_adversarial_rounds", "accepted_through", "m3_status",
    "msp_03d_status", "dirty_rescue_candidate", "successor_unlocks",
    "successor_unlock_condition", "msp_r00_status", "msp_r00_issue",
    "msp_r00_architecture_review", "initial_ready_set", "routing_policy",
})
SERIALIZATION = {
    "rule": "one_active_pr_per_repo",
    "memory_guard": "serial_execution_for_all_eebusreg_and_docs_rows_unless_initial_ready_set_says_otherwise",
    "recovery_sequence": ["MSP-R00", "MSP-R00-L", "DOCS-VERIFY", "MSP-DOCS-API-SCHEMA", "MSP-DOCS-PLATFORM", "MSP-DOCS-E2", "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH", "MSP-DOCS-E2R-AGGREGATE", "MSP-DOCS-CLEAN", "MSP-03D-R"],
    "eebusreg_sequence": ["MSP-DOCS-CLEAN", "MSP-03D-R", "MSP-035", "MSP-04A", "MSP-036", "MSP-055", "MSP-04B", "MSP-04C", "MSP-045", "MSP-05P-REG-API-V2", "MSP-05P-REG-ID", "MSP-05P-REG-RUNTIME", "MSP-05P-REG-API-V1-CLEANUP", "MSP-0625-REG-EXEC", "MSP-0625-REG-MUT", "MSP-0625-S13-REG"],
    "docs_eebus_sequence": ["DOCS-VERIFY", "MSP-DOCS-API-SCHEMA", "MSP-DOCS-E2", "MSP-DOCS-API-CANDIDATE", "MSP-DOCS-API-FREEZE", "MSP-DOCS-05P", "MSP-0625-DOCS-E", "MSP-0625-LAB", "MSP-0625-S13-DOCS"],
    "docs_ebus_sequence": ["MSP-DOCS-PLATFORM", "MSP-0625-DOCS-P"],
    "ship_go_sequence": ["MSP-05P-SHIP"],
    "eebus_go_sequence": ["MSP-05P-EEBUS", "MSP-0625-EEBUS", "MSP-0625-S13-EEBUS"],
    "spine_go_sequence": ["MSP-0625-SPINE", "MSP-0625-S13-SPINE"],
    "gateway_sequence": ["MSP-05A", "MSP-05A-R1", "MSP-05B-PLAN-R1", "MSP-05A-R2", "MSP-05B", "MSP-06", "MSP-0625-GW-ROUTER", "MSP-0625-GW-MCP", "MSP-065", "MSP-07", "MSP-08", "MSP-085", "MSP-0625-S13-GW-LAB", "MSP-065-LIVE-R1", "MSP-07-LIVE-R1", "MSP-08-LIVE-R1", "MSP-085-LIVE-R1", "MSP-09A", "MSP-09B"],
    "initial_ready_set": ["MSP-0625-S13-DOCS"],
    "dirty_code_unlocks_successors": False,
    "conditional_rows": ["MSP-DOCS-CANDIDATE-CLEANUP"],
    "pr_required_evidence": ["doc_gate_result", "rollback_ledger_entry", "relevant_transport_or_security_gate_artifact", "review_disposition_for_every_comment", "complete_milestone_architecture_review"],
}
ACTIVE_ROUTING_CONTRACT = {
    "resolver": "canonical_resolver",
    "policy_digest": "canonical_policy_digest",
    "forbidden_tier": "Ultra",
}
MATRIX_ROOT_ROUTING_POLICY = {
    "resolver": "canonical",
    "policy_digest": "required_at_dispatch",
    "forbidden_tier": "highest_reserved_tier",
}
EXPECTED_ACTIVE_SURFACES = (
    "00-canonical.md",
    "01-index.md",
    "10-platform-taxonomy-and-boundaries.md",
    "11-ebus-040-baseline-and-profile-split.md",
    "12-eebus-mcp-first-vr940f.md",
    "13-semantic-fact-graph-and-integration.md",
    "14-execution-roadmap-issues-and-gates.md",
    "90-issue-map.md",
    "91-milestone-map.md",
    "92-m0-issue-matrix.yaml",
    "99-status.md",
    "plan.yaml",
    "105-ad-docs-02-amendment.md",
    "106-ad-docs-02-integrity.json",
    "107-ad-docs-02-topology-audit.md",
    "114-w28-26-m5b-production-prerequisite-correction.md",
    "115-w28-26-pre-release-api-v1-correction.md",
    "116-w28-26-m5b-lifecycle-prerequisite-correction.md",
    "117-w30-26-original-plan-current-state-reconciliation.md",
    "118-w30-26-m625-raw-spine-feature-acquisition.md",
    "119-w30-26-post-m6-hardening-inventory.md",
    "120-w30-26-current-state-evidence.json",
    "121-w31-26-m625-raw-mutation-contract-correction.md",
    "122-w31-26-m625-implementation-state-reconciliation.md",
    "123-w31-26-m625-spine-13-erratum.md",
)
MUTABLE_PATHS = frozenset({
    "multi-runtime-semantic-platform.locked/00-canonical.md",
    "multi-runtime-semantic-platform.locked/01-index.md",
    "multi-runtime-semantic-platform.locked/10-platform-taxonomy-and-boundaries.md",
    "multi-runtime-semantic-platform.locked/11-ebus-040-baseline-and-profile-split.md",
    "multi-runtime-semantic-platform.locked/12-eebus-mcp-first-vr940f.md",
    "multi-runtime-semantic-platform.locked/13-semantic-fact-graph-and-integration.md",
    "multi-runtime-semantic-platform.locked/14-execution-roadmap-issues-and-gates.md",
    "multi-runtime-semantic-platform.locked/90-issue-map.md",
    "multi-runtime-semantic-platform.locked/91-milestone-map.md",
    "multi-runtime-semantic-platform.locked/92-m0-issue-matrix.yaml",
    "multi-runtime-semantic-platform.locked/99-status.md",
    "multi-runtime-semantic-platform.locked/plan.yaml",
    "multi-runtime-semantic-platform.locked/105-ad-docs-02-amendment.md",
    "multi-runtime-semantic-platform.locked/106-ad-docs-02-integrity.json",
    "multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md",
    "multi-runtime-semantic-platform.locked/115-w28-26-pre-release-api-v1-correction.md",
    "multi-runtime-semantic-platform.locked/116-w28-26-m5b-lifecycle-prerequisite-correction.md",
    "multi-runtime-semantic-platform.locked/114-w28-26-m5b-production-prerequisite-correction.md",
    "multi-runtime-semantic-platform.locked/117-w30-26-original-plan-current-state-reconciliation.md",
    "multi-runtime-semantic-platform.locked/118-w30-26-m625-raw-spine-feature-acquisition.md",
    "multi-runtime-semantic-platform.locked/119-w30-26-post-m6-hardening-inventory.md",
    "multi-runtime-semantic-platform.locked/120-w30-26-current-state-evidence.json",
    "multi-runtime-semantic-platform.locked/121-w31-26-m625-raw-mutation-contract-correction.md",
    "multi-runtime-semantic-platform.locked/122-w31-26-m625-implementation-state-reconciliation.md",
    "multi-runtime-semantic-platform.locked/123-w31-26-m625-spine-13-erratum.md",
    "scripts/validate_ad_docs_02.py",
    "scripts/validate_msp_r00_l_ledger.py",
    "scripts/validate_plans_repo.sh",
    "tests/test_ad_docs_02_red.py",
    "tests/test_validate_ad_docs_02.py",
    "tests/test_validate_msp_r00_l_ledger.py",
})
ISSUE_63_ALLOWED_PATHS = MUTABLE_PATHS
E2R_PREREQUISITES = (
    "MSP-DOCS-E2, MSP-DOCS-E2R-PLATFORM, MSP-DOCS-E2R-PUBLISH, "
    "MSP-DOCS-E2R-AGGREGATE, MSP-DOCS-CLEAN"
)
HTML_UNESCAPE_MAX_ITERATIONS = 8
ENTITY_LIKE_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);")
MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
MARKDOWN_REFERENCE_LINK_RE = re.compile(r"!?\[([^\]]*)\]\[[^\]]*\]")
MARKDOWN_EMPHASIS_RE = re.compile(r"(?<!\\)[*_]+")
MARKDOWN_BACKSLASH_ESCAPE_RE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")
HTML_TAG_START_RE = re.compile(r"<(?:(?:/)?[A-Za-z])")
ACTIVE_ROUTING_PIN_RE = re.compile(
    r"\bmodel[ _-]?lane\b|"
    r"\b(?:provider|vendor)\b\s*(?::|=|is\b)?\s*\b(?:openai|anthropic)\b|"
    r"\bmodel\b\s*(?::|=|is\b)?\s*\b(?:gpt|claude)[ _-]?\d|"
    r"\bclaude(?:[ _-]*(?:sonnet|opus|haiku))[ _-]*\d+(?:[._-]\d+)?(?:[ _-][a-z0-9]+)*\b|"
    r"\b(?:gpt|claude)[ _-]?\d+(?:[._-]\d+)?(?:[ _-][a-z0-9]+)*\b|"
    r"\bgpt[ _-]?5[._ -]?5\b"
)
RESTRICTED_EVIDENCE_VALUE_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]+-----|"
    r"\b(?:https?|wss?)://|"
    r"\b(?:ski|ship[ _-]?id|serial|payload|secret|bearer|token)\s*[:=]|"
    r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b|"
    r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?::[0-9]+)?\b|"
    r"(?:^|[\s\"'])/(?:Users|private|home|mnt|var)/",
    re.IGNORECASE,
)
EXPECTED_CURRENT_EVIDENCE = {
    "binary": {
        "architecture": "arm64",
        "gateway_version": "0.6.32",
        "process_file_hash_match": True,
        "proof_classification": "screen_observed_public_safe",
        "sha256": "d75f0ba8fd52671e5165f37e70bbeaa37ce27e90bd6acc8136145b08c4195cd9",
    },
    "ci": {
        "docs_ebus": "passed",
        "docs_eebus": "passed",
        "eebus_go": "passed",
        "eebusreg": "passed",
        "gateway": "passed",
        "proof_classification": "screen_observed_public_safe",
        "ship_go": "passed",
        "spine_go": "passed",
    },
    "counts": {
        "devices": 1,
        "distinct_use_case_names": 13,
        "entities": 11,
        "features": 20,
        "proof_classification": "live_topology_public_safe",
        "use_case_claims": 22,
    },
    "proof_classification": {
        "current_state": "screen_observed_requires_dispatch_reverification",
        "milestone_history": "locked_plan_and_public_repository_evidence",
        "promotion_state": "zero_promoted_leaves",
        "restricted_material": "excluded",
    },
    "repositories": [
        {
            "ci": "passed",
            "commit": "cfb9e17c3e045b2a53bd39afef2d33cd38326bc5",
            "ref": "v0.6.1-helianthus.9",
            "ref_kind": "tag",
            "repository": "Project-Helianthus/helianthus-ship-go",
        },
        {
            "ci": "passed",
            "commit": "7383c108f72309c3636d896948d7a8de6d001708",
            "ref": "v0.7.1-helianthus.4",
            "ref_kind": "tag",
            "repository": "Project-Helianthus/helianthus-spine-go",
        },
        {
            "ci": "passed",
            "commit": "298567a297eb8767f24e7ed228f979ed6500fc60",
            "ref": "v0.7.1-helianthus.9",
            "ref_kind": "tag",
            "repository": "Project-Helianthus/helianthus-eebus-go",
        },
        {
            "ci": "passed",
            "commit": "7175bf777df9013af979bf76b51daa93e55bf873",
            "ref": "v0.1.16",
            "ref_kind": "tag",
            "repository": "Project-Helianthus/helianthus-eebusreg",
        },
        {
            "ci": "passed",
            "commit": "a11a953f7392c44870374d1c29a148d4ebbc69b8",
            "ref": "main",
            "ref_kind": "branch",
            "repository": "Project-Helianthus/helianthus-eebusreg",
        },
        {
            "ci": "passed",
            "commit": "34aac6d05075fae689815d21a5dabf2c5d3e2259",
            "ref": "main",
            "ref_kind": "branch",
            "repository": "Project-Helianthus/helianthus-ebusgateway",
        },
        {
            "ci": "passed",
            "commit": "3c25767f63e8e14069f3a2308f2fd5d8998f5332",
            "ref": "main",
            "ref_kind": "branch",
            "repository": "Project-Helianthus/helianthus-docs-eebus",
        },
        {
            "ci": "passed",
            "commit": "7b0dd0abba8bc3420f1d8d2bae2db5bc229b75f3",
            "ref": "main",
            "ref_kind": "branch",
            "repository": "Project-Helianthus/helianthus-docs-ebus",
        },
    ],
    "schema": "helianthus.m625-current-state-evidence",
    "version": 1,
}
PROTECTED_EVIDENCE_PATHS = (
    f"{PLAN}/93-eebus-transport-gate-v0.md",
    f"{PLAN}/94-m1-docs-bootstrap-evidence.md",
    f"{PLAN}/95-msp-020-eebusreg-bootstrap-evidence.md",
    f"{PLAN}/96-gate-readiness-audit-2026-07-08.md",
    f"{PLAN}/97-m2-raw-contracts-architecture-review.md",
    f"{PLAN}/98-msp-03a-facade-spike-evidence.md",
    f"{PLAN}/98-msp-03b-toolchain-boundary-evidence.md",
    f"{PLAN}/98-msp-03c-ha-network-proof-gate-evidence.md",
    f"{PLAN}/98-msp-03c-ha-network-proof-lab-run.json",
    f"{PLAN}/98-msp-03c-lab-acceptance-2026-07-08.md",
    f"{PLAN}/98-msp-03c-lab-attempt-2026-07-08.md",
    f"{PLAN}/98-msp-03d-fake-peer-live-blocker-evidence.md",
    f"{PLAN}/100-topology-audit.md",
    f"{PLAN}/101-g19-canonical-evidence-template.md",
    f"{PLAN}/102-plan-lock-architecture-review.md",
    f"{PLAN}/103-ad-docs-01-amendment.md",
    f"{PLAN}/104-msp-r00-l-public-redacted-ledger.json",
    f"{PLAN}/issues/MSP-00A-control-plane-matrix.md",
    f"{PLAN}/issues/MSP-00B-model-routing.md",
    f"{PLAN}/issues/MSP-00C-eebus-transport-gate-v0.md",
    f"{PLAN}/issues/MSP-020-eebusreg-bootstrap.md",
    f"{PLAN}/issues/MSP-02A-raw-runtime-identity-contract.md",
)

def active_control_surface_paths() -> tuple[str, ...]:
    """Return the fixed active-plan projection, independent of the allowlist."""
    return tuple(f"{PLAN}/{surface}" for surface in EXPECTED_ACTIVE_SURFACES)

class ValidationError(ValueError):
    pass


class InlineHTMLRenderer(HTMLParser):
    """Render safe inline HTML to its text content, rejecting malformed tags."""

    VOID_ELEMENTS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self.open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.VOID_ELEMENTS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        return

    def handle_endtag(self, tag: str) -> None:
        if tag in self.VOID_ELEMENTS or not self.open_tags or self.open_tags[-1] != tag:
            fail("markdown: malformed inline HTML")
        self.open_tags.pop()

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_decl(self, decl: str) -> None:
        fail("markdown: unsupported HTML declaration")

    def unknown_decl(self, data: str) -> None:
        fail("markdown: unsupported HTML declaration")

    def handle_pi(self, data: str) -> None:
        fail("markdown: unsupported HTML processing instruction")


def render_inline_html(text: str) -> str:
    """Remove comments and render balanced inline HTML to text, fail-closed."""
    remaining = text
    rendered_parts: list[str] = []
    while "<!--" in remaining:
        before, comment = remaining.split("<!--", 1)
        if "-->" not in comment:
            fail("markdown: unclosed HTML comment")
        _, remaining = comment.split("-->", 1)
        rendered_parts.append(before)
    rendered_parts.append(remaining)
    renderer = InlineHTMLRenderer()
    try:
        renderer.feed("".join(rendered_parts))
        renderer.close()
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("markdown: malformed inline HTML") from exc
    if renderer.open_tags:
        fail("markdown: unclosed inline HTML")
    rendered = "".join(renderer.parts)
    if HTML_TAG_START_RE.search(rendered):
        fail("markdown: malformed inline HTML")
    return rendered


def pull_request_head_from_event(event_path: Path) -> str:
    """Read a GitHub pull_request head SHA from the structured event payload."""
    try:
        event = json.loads(event_path.read_text(encoding="utf-8"))
        head = event["pull_request"]["head"]["sha"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValidationError("invalid issue-63 pull_request event") from exc
    if not isinstance(head, str) or re.fullmatch(r"[0-9a-f]{40}", head) is None:
        fail("invalid issue-63 pull_request head")
    return head

class UniqueLoader(yaml.SafeLoader):
    pass

def fail(message: str) -> None:
    raise ValidationError(message)

def _mapping(loader: UniqueLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            fail("matrix: duplicate YAML key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)

def _json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            fail("integrity: duplicate JSON key")
        value[key] = item
    return value

def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValidationError("matrix: invalid YAML") from exc
    if not isinstance(data, dict):
        fail("matrix: expected object")
    return data

def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_json_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("integrity: invalid JSON") from exc
    if not isinstance(data, dict):
        fail("integrity: expected object")
    return data

def exact_keys(value: Any, keys: set[str], where: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        fail(f"{where}: closed schema violation")

def validate_integrity(data: dict[str, Any]) -> None:
    keys = {"schema_version", "control_plane_amendment", "e2_merge_roots", "completion_token_roots", "evidence_inputs",
            "routing_contract", "entry_kinds", "publication_entry_kinds", "eligible_channels",
            "exact_memberships", "channel_registry", "absence_constraints",
            "hermetic_git_object_evidence", "token_envelope", "readiness_categories",
            "planned_expiry", "candidate_cleanup", "process_attestation"}
    exact_keys(data, keys, "integrity")
    if data["schema_version"] != 2 or data["e2_merge_roots"] != list(E2_ROOTS):
        fail("integrity: E2 roots drift")
    exact_keys(data["control_plane_amendment"], {"id", "decision", "next_ready", "required_chain"}, "control_plane_amendment")
    if data["control_plane_amendment"] != {
        "id": "MSP-05B-LIFECYCLE-PREREQUISITE-CORRECTION",
        "decision": "gateway_lifecycle_prerequisite",
        "next_ready": "MSP-05A-R2",
        "required_chain": [
            "MSP-05B-PLAN-R1", "MSP-05A-R2", "MSP-05B",
        ],
    }:
        fail("integrity: M5 prerequisite amendment drift")
    if data["completion_token_roots"] != sorted(E2_ROOTS):
        fail("integrity: completion roots drift")
    exact_keys(data["evidence_inputs"], {"MSP-R00", "MSP-03D-G01"}, "evidence_inputs")
    if data["evidence_inputs"] != {"MSP-R00": ["Project-Helianthus/helianthus-eebusreg#14"], "MSP-03D-G01": ["MSP-03D-G01"]}:
        fail("integrity: evidence authority drift")
    exact_keys(data["routing_contract"], {"resolver", "policy_digest", "forbidden_tier"}, "routing_contract")
    reject_active_routing_pin(data["routing_contract"], "integrity.routing_contract")
    if data["routing_contract"] != ACTIVE_ROUTING_CONTRACT:
        fail("integrity: routing contract drift")
    if data["entry_kinds"] != ["eligibility", "exact_membership", "channel_registry", "absence_constraint"]:
        fail("integrity: entry kinds drift")
    if data["publication_entry_kinds"] != ["canonical_document", "canonical_collection", "summary_pointer"]:
        fail("integrity: publication entry kinds drift")
    exact_keys(data["eligible_channels"], {"stable"}, "eligible_channels")
    if data["eligible_channels"] != {"stable": ["canonical"]}:
        fail("integrity: eligibility drift")
    exact_keys(data["exact_memberships"], {"stable"}, "exact_memberships")
    exact_keys(data["exact_memberships"]["stable"], {"canonical"}, "exact_memberships.stable")
    if data["exact_memberships"] != {"stable": {"canonical": []}}:
        fail("integrity: exact memberships drift")
    exact_keys(data["channel_registry"], {"canonical"}, "channel_registry")
    exact_keys(data["channel_registry"]["canonical"], {"visibility", "owner"}, "channel_registry.canonical")
    if data["channel_registry"] != {"canonical": {"visibility": "stable", "owner": "canonical_documentation_owner"}}:
        fail("integrity: channel registry drift")
    if data["absence_constraints"] != ["candidate entries are absent from stable outputs", "summary pointers do not claim canonical membership"]:
        fail("integrity: absence constraints drift")
    exact_keys(data["hermetic_git_object_evidence"], {"required", "moving_refs_rejected"}, "hermetic_git_object_evidence")
    if set(data["hermetic_git_object_evidence"]["required"]) != {"base_oid", "head_oid", "merge_oid", "tree_oid", "evidence_core_sha256"} or data["hermetic_git_object_evidence"]["moving_refs_rejected"] is not True:
        fail("integrity: hermetic git-object evidence drift")
    exact_keys(data["token_envelope"], {"schema_version", "identity_fields", "replay_rejected", "drift_rejected"}, "token_envelope")
    if data["token_envelope"]["schema_version"] != 2 or set(data["token_envelope"]["identity_fields"]) != {"producer_id", "consumer_id", "repository", "pr", "base_oid", "head_oid", "merge_oid", "tree_oid", "evidence_core_sha256", "prior_token_digest", "observation_source"} or data["token_envelope"]["replay_rejected"] is not True or data["token_envelope"]["drift_rejected"] is not True:
        fail("integrity: token envelope identity/replay/drift drift")
    if data["readiness_categories"] != ["historical_snapshot", "logical_ready", "dispatchable", "selected_batch"]:
        fail("integrity: readiness categories drift")
    exact_keys(data["planned_expiry"], {"state", "action"}, "planned_expiry")
    exact_keys(data["candidate_cleanup"], {"state", "fail_closed", "post_consumption_rollback", "action"}, "candidate_cleanup")
    if data["planned_expiry"] != {"state": "planned", "action": "block_new_publication"}:
        fail("integrity: planned expiry drift")
    if data["candidate_cleanup"] != {"state": "candidate", "fail_closed": True, "post_consumption_rollback": "forward_fix_only", "action": "withdraw_candidate_and_require_fresh_cycle"}:
        fail("integrity: expiry/cleanup drift")
    exact_keys(data["process_attestation"], {"distinct_from"}, "process_attestation")
    if data["process_attestation"] != {"distinct_from": "technical_git_object_proof"}:
        fail("integrity: process attestation drift")

def validate_current_state_evidence(path: Path, data: dict[str, Any]) -> None:
    exact_keys(
        data,
        {"binary", "ci", "counts", "proof_classification", "repositories", "schema", "version"},
        "current_evidence",
    )
    if data["schema"] != "helianthus.m625-current-state-evidence" or data["version"] != 1:
        fail("current_evidence: schema drift")
    exact_keys(
        data["binary"],
        {
            "architecture", "gateway_version", "process_file_hash_match",
            "proof_classification", "sha256",
        },
        "current_evidence.binary",
    )
    exact_keys(
        data["counts"],
        {
            "devices", "distinct_use_case_names", "entities", "features",
            "proof_classification", "use_case_claims",
        },
        "current_evidence.counts",
    )
    if data["counts"] != {
        "devices": 1,
        "distinct_use_case_names": 13,
        "entities": 11,
        "features": 20,
        "proof_classification": "live_topology_public_safe",
        "use_case_claims": 22,
    }:
        fail("current_evidence: count drift")
    exact_keys(
        data["ci"],
        {
            "docs_ebus", "docs_eebus", "eebus_go", "eebusreg", "gateway",
            "proof_classification", "ship_go", "spine_go",
        },
        "current_evidence.ci",
    )
    exact_keys(
        data["proof_classification"],
        {"current_state", "milestone_history", "promotion_state", "restricted_material"},
        "current_evidence.proof_classification",
    )
    if not isinstance(data["repositories"], list) or len(data["repositories"]) != 8:
        fail("current_evidence: repository inventory drift")
    for index, repository in enumerate(data["repositories"]):
        exact_keys(
            repository,
            {"ci", "commit", "ref", "ref_kind", "repository"},
            f"current_evidence.repositories[{index}]",
        )
        if re.fullmatch(r"[0-9a-f]{40}", repository["commit"]) is None:
            fail("current_evidence: malformed public commit")
        if repository["ref_kind"] not in {"branch", "tag"}:
            fail("current_evidence: invalid ref kind")
    if re.fullmatch(r"[0-9a-f]{64}", data["binary"]["sha256"]) is None:
        fail("current_evidence: malformed public binary hash")
    forbidden_keys = {
        "ip", "mac", "payload", "private_path", "raw_identity", "serial",
        "ship_id", "ski", "secret", "token",
    }
    def reject_restricted_material(value: Any) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in forbidden_keys:
                    fail("current_evidence: restricted field")
                reject_restricted_material(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_restricted_material(nested)
        elif isinstance(value, str) and RESTRICTED_EVIDENCE_VALUE_RE.search(value):
            fail("current_evidence: restricted value")
    reject_restricted_material(data)
    if data != EXPECTED_CURRENT_EVIDENCE:
        fail("current_evidence: public-safe value inventory drift")
    canonical = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if path.read_text(encoding="utf-8") != canonical:
        fail("current_evidence: JSON is not canonical sorted")

def pre_m625_history_projection(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    projection: list[dict[str, Any]] = []
    for row in rows:
        projection.append({
            key: value
            for key, value in row.items()
            if key != "acceptance_state"
        })
        if row.get("id") == "MSP-06":
            return projection
    fail("matrix: missing MSP-06 history boundary")

def pre_m625_history_sha256(rows: list[dict[str, Any]]) -> str:
    encoded = json.dumps(
        pre_m625_history_projection(rows),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

def promotion_claim_sha256(claim: dict[str, Any]) -> str:
    encoded = json.dumps(
        claim,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def release_proof_projection(state: Any) -> dict[str, Any]:
    if state not in RELEASE_PROOF_STATES:
        fail("release proof: unknown canonical control state")
    return RELEASE_PROOF_STATES[state]


def render_release_projection_block(state: str) -> str:
    projection = release_proof_projection(state)
    return "\n".join((
        "<!-- M625_RELEASE_PROJECTION_BEGIN -->",
        f"Release-proof control: `{state}`",
        f"Cruise phase: `{projection['cruise_phase']}`",
        f"Current milestone: `{projection['current_milestone']}`",
        f"LAB acceptance state: `{projection['lab_acceptance_state']}`",
        f"Selected batch: `{projection['selected_batch'][0]}`",
        f"Accepted through: `{projection['accepted_through']}`",
        "<!-- M625_RELEASE_PROJECTION_END -->",
    ))


def validate_control_projection(
    plan: dict[str, Any], matrix: dict[str, Any], plan_dir: Path,
) -> None:
    state = plan.get("lab_release_proof")
    projection = release_proof_projection(state)
    if matrix.get("lab_release_proof") != state:
        fail("release proof: plan/matrix control split-brain")
    expected_common = {
        "cruise_phase": projection["cruise_phase"],
        "current_milestone": projection["current_milestone"],
        "accepted_through": projection["accepted_through"],
    }
    for surface_name, surface in (("plan", plan), ("matrix", matrix)):
        for key, expected in expected_common.items():
            if surface.get(key) != expected:
                fail(f"release proof: {surface_name}.{key} projection drift")
    if plan.get("initial_ready_set") != projection["selected_batch"]:
        fail("release proof: plan selected-batch projection drift")
    rows = matrix.get("issues", [])
    lab_rows = [row for row in rows if row.get("id") == "MSP-0625-LAB"]
    if len(lab_rows) != 1:
        fail("release proof: LAB row cardinality drift")
    if lab_rows[0].get("acceptance_state") != projection["lab_acceptance_state"]:
        fail("release proof: LAB acceptance-state projection drift")
    if readiness(matrix)["selected_batch"] != projection["selected_batch"]:
        fail("release proof: readiness projection drift")
    expected_block = render_release_projection_block(state)
    for surface in RELEASE_PROJECTION_SURFACES:
        text = (plan_dir / surface).read_text(encoding="utf-8")
        blocks = RELEASE_PROJECTION_RE.findall(text)
        if blocks != [expected_block]:
            fail(f"release proof: {surface} control projection drift")

def validate_promotion_completion_token(token: dict[str, Any]) -> None:
    exact_keys(token, {"claim", "claim_sha256"}, "promotion_token")
    claim = token["claim"]
    exact_keys(
        claim,
        {
            "milestone_id",
            "promoted_leaf_count",
            "promotion_dossier_root",
            "evidence_root",
        },
        "promotion_token.claim",
    )
    if claim["milestone_id"] != "MSP-085-LIVE-R1":
        fail("promotion_token: milestone drift")
    count = claim["promoted_leaf_count"]
    if type(count) is not int or count <= 0:
        fail("promotion_token: promoted_leaf_count must be a positive integer")
    for field in ("promotion_dossier_root", "evidence_root"):
        value = claim[field]
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            fail(f"promotion_token: malformed {field}")
    digest = token["claim_sha256"]
    if not isinstance(digest, str) or digest != promotion_claim_sha256(claim):
        fail("promotion_token: digest mismatch")

def validate_matrix(data: dict[str, Any]) -> None:
    exact_keys(data, set(MATRIX_ROOT_KEYS), "matrix")
    if data["schema_version"] != 2:
        fail("matrix: schema version drift")
    projection = release_proof_projection(data.get("lab_release_proof"))
    if (
        data["amendment_count"] != CURRENT_AMENDMENT_COUNT
        or data["amendment"] != CURRENT_AMENDMENT
        or data["successor_unlock_condition"] != CURRENT_SUCCESSOR_UNLOCK_CONDITION
    ):
        fail("matrix: current amendment projection drift")
    for key in ("cruise_phase", "current_milestone", "accepted_through"):
        if data[key] != projection[key]:
            fail(f"matrix: release-proof {key} projection drift")
    if data["serialization"] != SERIALIZATION:
        fail("matrix: serialization authority drift")
    exact_keys(data["routing_policy"], {"resolver", "policy_digest", "forbidden_tier"}, "matrix.routing_policy")
    reject_active_routing_pin(data["routing_policy"], "matrix.routing_policy")
    if data["routing_policy"] != MATRIX_ROOT_ROUTING_POLICY:
        fail("matrix: root routing policy drift")
    rows = data.get("issues")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        fail("matrix: issues must be mappings")
    if pre_m625_history_sha256(rows) != PRE_M625_HISTORY_SHA256:
        fail("matrix: protected pre-M6.25 history projection drift")
    ids = [row.get("id") for row in rows]
    if tuple(ids) != EXACT_IDS:
        fail("matrix: exact ID contract drift")
    by_id = {row["id"]: row for row in rows}
    visiting: set[str] = set()
    visited: set[str] = set()
    for row in rows:
        row_id = row["id"]
        expected_keys = BASE_ROW_KEYS | ROW_EXTRAS.get(row_id, frozenset())
        if row_id not in NO_ACCEPTANCE:
            expected_keys |= {"acceptance"}
        expected_keys |= {"routing_evidence" if row_id in HISTORICAL_IDS else "routing_contract"}
        exact_keys(row, set(expected_keys), f"matrix.{row_id}")
        if "model_lane" in row or "predecessors" in row:
            fail("matrix: active legacy routing/dependency field")
        contract, evidence = "routing_contract" in row, "routing_evidence" in row
        if contract == evidence:
            fail("matrix: exactly one routing authority required")
        if contract:
            exact_keys(row["routing_contract"], {"resolver", "policy_digest", "forbidden_tier"}, f"matrix.{row['id']}.routing_contract")
            reject_active_routing_pin(row["routing_contract"], f"matrix.{row['id']}.routing_contract")
            if row["routing_contract"] != ACTIVE_ROUTING_CONTRACT:
                fail("matrix: active routing contract drift")
        else:
            exact_keys(row["routing_evidence"], {"recorded"}, f"matrix.{row['id']}.routing_evidence")
            if row["routing_evidence"] != {"recorded": "historical_observed"}:
                fail("matrix: historical routing evidence drift")
        if row_id not in HISTORICAL_IDS:
            reject_active_row_string_pins(row, f"matrix.{row_id}")
        if row["requires_completion_tokens"] != REQUIRES_COMPLETION_TOKENS[row_id]:
            fail("matrix: completion-token authority drift")
        if row.get("evidence_inputs", []) != EVIDENCE_INPUTS[row_id]:
            fail("matrix: evidence-input authority drift")
        expected_acceptance_state = (
            projection["lab_acceptance_state"]
            if row_id == "MSP-0625-LAB"
            else ACCEPTANCE_STATES[row_id]
        )
        if row["acceptance_state"] != expected_acceptance_state:
            fail("matrix: acceptance-state authority drift")
        if row_id in LOCKED_ACCEPTANCE and row.get("acceptance") != LOCKED_ACCEPTANCE[row_id]:
            fail("matrix: locked M5 acceptance contract drift")
        for fragment in M625_ACCEPTANCE_FRAGMENTS.get(row_id, ()):
            if not any(fragment in item for item in row.get("acceptance", [])):
                fail(f"matrix: {row_id} M6.25 acceptance drift")
        if (
            row_id == "MSP-0625-GW-MCP"
            and row.get("tool_suffixes") != M625_TOOL_SUFFIXES
        ):
            fail("matrix: exact M6.25 tool suffix contract drift")
        if row_id in M625_S13_IDS:
            issue_index = M625_S13_IDS.index(row_id)
            if row.get("issue_ref") != M625_S13_ISSUE_CHAIN[issue_index]:
                fail("matrix: SPINE 1.3 erratum issue-chain drift")
            if tuple(row.get("acceptance", [])) != M625_S13_ACCEPTANCE[row_id]:
                fail("matrix: SPINE 1.3 exact acceptance contract drift")
        if (
            row_id == "MSP-0625-S13-DOCS"
            and row.get("public_baseline") != M625_S13_PUBLIC_BASELINE
        ):
            fail("matrix: SPINE 1.3 public baseline drift")
        if (
            row_id == "MSP-0625-S13-SPINE"
            and row.get("scope_provenance") != M625_S13_SCOPE_PROVENANCE
        ):
            fail("matrix: SPINE 1.3 bounded provenance drift")
        if (
            row_id == "MSP-085-LIVE-R1"
            and row.get("completion_token_contract") != LIVE_COMPLETION_TOKEN_CONTRACT
        ):
            fail("matrix: live promotion completion-token contract drift")
        if row_id.startswith("MSP-09") and row.get("unlock_predicate") != M9_UNLOCK_PREDICATE:
            fail("matrix: M9 promoted-leaf predicate drift")
    def visit(row_id: str) -> None:
        if row_id in visiting:
            fail("matrix: dependency cycle")
        if row_id in visited:
            return
        visiting.add(row_id)
        for dep in by_id[row_id].get("requires_completion_tokens", []):
            if dep not in by_id:
                fail("matrix: unknown completion token")
            visit(dep)
        visiting.remove(row_id)
        visited.add(row_id)
    for row_id in by_id:
        visit(row_id)
    if by_id["MSP-03D-R"].get("evidence_inputs") != ["MSP-03D-G01"]:
        fail("matrix: MSP-03D-G01 must remain evidence-only")
    if "MSP-DOCS-E2" in by_id["MSP-DOCS-CLEAN"].get("requires_completion_tokens", []):
        fail("matrix: direct E2-to-CLEAN path")
    preserved_nonlive = {"MSP-065", "MSP-07", "MSP-08", "MSP-085"}
    for row_id in ("MSP-065-LIVE-R1", "MSP-07-LIVE-R1", "MSP-08-LIVE-R1", "MSP-085-LIVE-R1"):
        if preserved_nonlive.intersection(by_id[row_id]["requires_completion_tokens"]):
            fail("matrix: historical synthetic row unlocks live chain")
    if "MSP-0625-DOCS-P" in by_id["MSP-0625-SPINE"]["requires_completion_tokens"]:
        fail("matrix: public methodology cross-seed blocks SPINE")
    old_live_predecessors = ["MSP-0625-LAB", "MSP-0625-DOCS-P"]
    if (
        by_id["MSP-065-LIVE-R1"]["requires_completion_tokens"][:2]
        != old_live_predecessors
        or by_id["MSP-065-LIVE-R1"]["requires_completion_tokens"][2:]
        != ["MSP-0625-S13-GW-LAB"]
    ):
        fail("matrix: erratum may only append the final LIVE-R1 predecessor")
    if any(
        row["repo"] == "helianthus-ship-go" and row["id"].startswith("MSP-0625")
        for row in rows
    ):
        fail("matrix: M6.25 changes ship-go")

def render_live_audit(matrix: dict[str, Any]) -> str:
    rows = matrix["issues"]
    current_readiness = readiness(matrix)
    snapshot = {
        "current_control": {
            "cruise_phase": matrix["cruise_phase"],
            "current_milestone": matrix["current_milestone"],
            "lab_acceptance_state": release_proof_projection(
                matrix["lab_release_proof"]
            )["lab_acceptance_state"],
            "lab_release_proof": matrix["lab_release_proof"],
            "historical_integrity_record": INTEGRITY,
            "historical_integrity_selected_batch": ["MSP-05A-R2"],
            "pre_m625_history_projection_sha256": pre_m625_history_sha256(rows),
            "selected_batch": current_readiness["selected_batch"],
        },
        "ids": [row["id"] for row in rows],
        "completion_tokens": {row["id"]: row.get("requires_completion_tokens", []) for row in rows},
        "completion_token_contracts": {
            row["id"]: row["completion_token_contract"]
            for row in rows
            if "completion_token_contract" in row
        },
        "tool_suffix_contracts": {
            row["id"]: row["tool_suffixes"]
            for row in rows
            if "tool_suffixes" in row
        },
        "routing_authority": {row["id"]: "contract" if "routing_contract" in row else "evidence" for row in rows},
        "evidence_inputs": {row["id"]: row["evidence_inputs"] for row in rows if "evidence_inputs" in row},
        "unlock_predicates": {row["id"]: row["unlock_predicate"] for row in rows if "unlock_predicate" in row},
    }
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return "\n".join((
        "# AD-DOCS-02 Live Topology Audit",
        "",
        f"Anchor: `{ANCHOR}`",
        f"Matrix snapshot SHA-256: `{digest}`",
        "",
        "```json",
        encoded,
        "```",
        "",
        "107 current integrity projection: 92-m0-issue-matrix.yaml is authoritative; 106-ad-docs-02-integrity.json is the immutable historical M5 record.",
        "requires_completion_tokens are authoritative; evidence_inputs are non-authoritative.",
        "Readiness snapshot / logical-ready / dispatchable / selected-batch categories: " + json.dumps(current_readiness, sort_keys=True, separators=(",", ":")),
        "",
    ))

def validate_live_audit(matrix: dict[str, Any], text: str) -> None:
    if text != render_live_audit(matrix):
        fail("live audit: deterministic matrix projection drift")


def render_canonical_digest(canonical_text: str, existing_surface: str) -> str:
    """Regenerate one split surface's canonical digest without rewriting prose."""
    digest = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    marker_pattern = r"Canonical-SHA256: `[0-9a-f]{64}`"
    if len(re.findall(marker_pattern, existing_surface)) != 1:
        fail("release proof: canonical digest marker missing or duplicated")
    updated = re.sub(
        marker_pattern,
        f"Canonical-SHA256: `{digest}`",
        existing_surface,
        count=1,
    )
    return updated


def replace_root_yaml_scalar(text: str, key: str, value: str) -> str:
    updated, count = re.subn(
        rf"(?m)^{re.escape(key)}:[^\n]*$",
        f"{key}: {value}",
        text,
        count=1,
    )
    if count != 1:
        fail(f"release proof: missing root YAML field {key}")
    return updated


def project_release_proof_files(root: Path, state: str) -> None:
    """Project one canonical plan control into every dependent source."""
    projection = release_proof_projection(state)
    plan_dir = root / PLAN
    plan_path = plan_dir / "plan.yaml"
    plan_text = plan_path.read_text(encoding="utf-8")
    for key, value in (
        ("lab_release_proof", state),
        ("cruise_phase", projection["cruise_phase"]),
        ("current_milestone", projection["current_milestone"]),
        ("accepted_through", projection["accepted_through"]),
    ):
        plan_text = replace_root_yaml_scalar(plan_text, key, value)
    plan_text, ready_count = re.subn(
        r"(?m)^initial_ready_set:\n(?:  - [^\n]+\n)+",
        "initial_ready_set:\n"
        + "".join(f"  - {row_id}\n" for row_id in projection["selected_batch"]),
        plan_text,
        count=1,
    )
    if ready_count != 1:
        fail("release proof: missing plan initial_ready_set")
    plan_path.write_text(plan_text, encoding="utf-8")

    matrix_path = plan_dir / MATRIX
    matrix_text = matrix_path.read_text(encoding="utf-8")
    for key, value in (
        ("lab_release_proof", state),
        ("cruise_phase", projection["cruise_phase"]),
        ("current_milestone", projection["current_milestone"]),
        ("accepted_through", projection["accepted_through"]),
    ):
        matrix_text = replace_root_yaml_scalar(matrix_text, key, value)
    matrix_text, lab_count = re.subn(
        r"(?ms)(^- id: MSP-0625-LAB\n(?:(?!^- id:).)*?^  acceptance_state: )[^\n]+$",
        rf"\g<1>{projection['lab_acceptance_state']}",
        matrix_text,
        count=1,
    )
    if lab_count != 1:
        fail("release proof: missing LAB acceptance_state")
    matrix_path.write_text(matrix_text, encoding="utf-8")

    expected_block = render_release_projection_block(state)
    for surface in RELEASE_PROJECTION_SURFACES:
        path = plan_dir / surface
        text = path.read_text(encoding="utf-8")
        updated, count = RELEASE_PROJECTION_RE.subn(expected_block, text)
        if count != 1:
            fail(f"release proof: {surface} projection marker drift")
        path.write_text(updated, encoding="utf-8")


def apply_release_proof_state(root: Path, state: str) -> None:
    """Set the canonical plan control and regenerate every dependent projection."""
    project_release_proof_files(root, state)
    plan_dir = root / PLAN
    matrix = load_yaml(plan_dir / MATRIX)
    plan = load_yaml(plan_dir / "plan.yaml")
    validate_matrix(matrix)
    validate_plan_projection(plan)
    validate_control_projection(plan, matrix, plan_dir)
    canonical_text = (plan_dir / "00-canonical.md").read_text(encoding="utf-8")
    digest_surfaces = [
        plan_dir / "01-index.md",
        *sorted(plan_dir.glob("1[0-9]-*.md")),
    ]
    for path in digest_surfaces:
        path.write_text(
            render_canonical_digest(
                canonical_text,
                path.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
    (plan_dir / "107-ad-docs-02-topology-audit.md").write_text(
        render_live_audit(matrix), encoding="utf-8"
    )


def write_generated(root: Path) -> None:
    """Regenerate all projections from the canonical plan control."""
    plan_dir = root / PLAN
    state = load_yaml(plan_dir / "plan.yaml").get("lab_release_proof")
    apply_release_proof_state(root, state)

def reject_active_routing_pin(value: Any, where: str) -> None:
    """Reject provider/model routing facts in active (not historical) contracts."""
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower()
            if any(token in lowered for token in ("model", "provider", "vendor")):
                fail(f"{where}: active routing pin")
            reject_active_routing_pin(nested, f"{where}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_active_routing_pin(nested, f"{where}[{index}]")
    elif isinstance(value, str) and ACTIVE_ROUTING_PIN_RE.search(normalize_markdown(value)):
        fail(f"{where}: active routing pin")

def reject_active_row_string_pins(value: Any, where: str) -> None:
    """Reject rendered provider/model pins in every active matrix string field."""
    if isinstance(value, dict):
        for key, nested in value.items():
            reject_active_row_string_pins(nested, f"{where}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_active_row_string_pins(nested, f"{where}[{index}]")
    elif isinstance(value, str) and ACTIVE_ROUTING_PIN_RE.search(normalize_markdown(value)):
        fail(f"{where}: active routing pin")

def validate_plan_projection(plan: dict[str, Any]) -> None:
    exact_keys(plan, set(PLAN_ROOT_KEYS), "plan")
    projection = release_proof_projection(plan.get("lab_release_proof"))
    reject_active_routing_pin(plan, "plan")
    policy = plan.get("routing_policy")
    exact_keys(policy, {"resolver", "policy_digest", "forbidden_tier"}, "plan.routing_policy")
    reject_active_routing_pin(policy, "plan.routing_policy")
    if policy != {"resolver": "canonical", "policy_digest": "required_at_dispatch", "forbidden_tier": "highest_reserved_tier"}:
        fail("plan: routing policy drift")
    if (
        plan.get("amendment_count") != CURRENT_AMENDMENT_COUNT
        or plan.get("amendment") != CURRENT_AMENDMENT
        or plan.get("successor_unlock_condition") != CURRENT_SUCCESSOR_UNLOCK_CONDITION
    ):
        fail("plan: current amendment projection drift")
    for key in ("cruise_phase", "current_milestone", "accepted_through"):
        if plan.get(key) != projection[key]:
            fail(f"plan: release-proof {key} projection drift")
    if plan.get("initial_ready_set") != projection["selected_batch"]:
        fail("plan: selected batch drift")

def canonicalize_security_symbols(text: str) -> str:
    """Preserve horizontal dependency direction and reject ambiguous symbols."""
    canonical: list[str] = []
    for character in text:
        category = unicodedata.category(character)
        if category == "Pd" or character == "\u2212":
            canonical.append("-")
        elif "ARROW" in unicodedata.name(character, ""):
            arrow_name = unicodedata.name(character)
            if "LEFT" in arrow_name and "RIGHT" in arrow_name:
                fail("markdown: bidirectional Unicode arrow in active control surface")
            if "RIGHTWARDS" in arrow_name:
                canonical.append("->")
            elif "LEFTWARDS" in arrow_name:
                canonical.append("<-")
            else:
                fail("markdown: ambiguous Unicode arrow in active control surface")
        elif not character.isascii() and category.startswith("S"):
            fail("markdown: non-ASCII symbol in active control surface")
        else:
            canonical.append(character)
    return "".join(canonical)

def render_markdown_text(text: str) -> str:
    """Render active Markdown to canonical text before evaluating its claims."""
    normalized = text
    for _ in range(HTML_UNESCAPE_MAX_ITERATIONS):
        unescaped = html.unescape(normalized)
        if unescaped == normalized:
            break
        normalized = unescaped
    else:
        fail("markdown: HTML entity decoding did not reach a fixed point")
    if ENTITY_LIKE_RE.search(normalized):
        fail("markdown: unresolved entity-like sequence")
    normalized = render_inline_html(normalized)
    normalized = unicodedata.normalize("NFKC", normalized)
    if any(unicodedata.category(character) == "Cf" for character in normalized):
        fail("markdown: Unicode format character")
    normalized = canonicalize_security_symbols(normalized)
    for _ in range(HTML_UNESCAPE_MAX_ITERATIONS):
        rendered = MARKDOWN_LINK_RE.sub(r"\1", normalized)
        rendered = MARKDOWN_REFERENCE_LINK_RE.sub(r"\1", rendered)
        if rendered == normalized:
            break
        normalized = rendered
    else:
        fail("markdown: link rendering did not reach a fixed point")
    normalized = MARKDOWN_EMPHASIS_RE.sub("", normalized)
    normalized = MARKDOWN_BACKSLASH_ESCAPE_RE.sub(r"\1", normalized)
    if any(character.isalpha() and not character.isascii() for character in normalized):
        fail("markdown: non-ASCII letter in active control surface")
    return normalized


def normalize_markdown(text: str) -> str:
    """Canonicalize active prose before evaluating its security-sensitive claims."""
    return " ".join(render_markdown_text(text).casefold().split())


def split_markdown_table_row(line: str) -> tuple[str, ...] | None:
    """Split a raw table row on unescaped pipes, with optional outer pipes."""
    stripped = line.strip()
    cells: list[str] = []
    current: list[str] = []
    slash_count = 0
    for character in stripped:
        if character == "|" and slash_count % 2 == 0:
            cells.append("".join(current))
            current = []
        else:
            current.append(character)
        slash_count = slash_count + 1 if character == "\\" else 0
    if not cells:
        return None
    cells.append("".join(current))
    if cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return tuple(cells) if len(cells) >= 3 else None


def has_forbidden_e2_clean_table_edge(text: str) -> bool:
    """Return whether a raw Markdown table contains the forbidden rendered edge."""
    forbidden_triples = {
        ("msp-docs-e2", "->", "msp-docs-clean"),
        ("msp-docs-clean", "<-", "msp-docs-e2"),
    }
    for line in text.splitlines():
        cells = split_markdown_table_row(line)
        if cells is None:
            continue
        cells = tuple(normalize_markdown(cell) for cell in cells)
        for index in range(len(cells) - 2):
            if cells[index:index + 3] in forbidden_triples:
                return True
    return False


def has_forbidden_e2_clean_dependency_claim(text: str) -> bool:
    """Reject active direct CLEAN-on-E2 dependency prose, not historical records."""
    pattern = re.compile(
        r"\bmsp-docs-clean\b\s+(?:does\s+)?depends\s*(?:-|\s)+"
        r"(?:only\s+)?on\s+\bmsp-docs-e2\b"
    )
    for match in pattern.finditer(text):
        clause_start = max(
            text.rfind(".", 0, match.start()),
            text.rfind(";", 0, match.start()),
            text.rfind("\n", 0, match.start()),
        ) + 1
        context = text[clause_start:match.start()]
        if re.search(r"\b(?:historical(?:ly)?|formerly|superseded)\b", context):
            continue
        return True
    return False

def validate_markdown_claims(plan_dir: Path, matrix: dict[str, Any]) -> None:
    current_reference = (
        "Current routing, readiness, and completion-token authority is "
        "`92-m0-issue-matrix.yaml` plus generated "
        "`107-ad-docs-02-topology-audit.md`; `106-ad-docs-02-integrity.json` "
        "is the immutable historical M5 integrity record."
    )
    historical_reference = (
        "Routing and completion-token authority is exclusively "
        "92-m0-issue-matrix.yaml plus 106-ad-docs-02-integrity.json."
    )
    historical_authority_surfaces = {
        "105-ad-docs-02-amendment.md",
        "114-w28-26-m5b-production-prerequisite-correction.md",
        "115-w28-26-pre-release-api-v1-correction.md",
        "116-w28-26-m5b-lifecycle-prerequisite-correction.md",
    }
    surfaces = tuple(
        Path(relative).name
        for relative in active_control_surface_paths()
        if relative.endswith(".md")
    )
    for surface in surfaces:
        text = (plan_dir / surface).read_text(encoding="utf-8")
        normalization_input = text
        if surface == M625_MUTATION_CORRECTION:
            normalization_input = normalization_input.replace(
                "<HashV1>", "HashV1"
            ).replace("<time>", "time")
        normalized = normalize_markdown(normalization_input)
        compact = " ".join(text.split())
        if surface != "107-ad-docs-02-topology-audit.md":
            expected_reference = (
                historical_reference
                if surface in historical_authority_surfaces
                else current_reference
            )
            if expected_reference not in compact:
                fail(f"surfaces.{surface}: missing structured routing reference")
        # Require a concrete provider/model value. This leaves canonical negative
        # and historical prose such as "does not duplicate ... provider or ..."
        # outside the active-pin grammar without relying on a bounded text window.
        if ACTIVE_ROUTING_PIN_RE.search(normalized):
            fail(f"surfaces.{surface}: active routing pin")
        if (
            re.search(r"msp-docs-e2\s*(?:->|to)\s*msp-docs-clean", normalized)
            or re.search(r"msp-docs-clean\s*<-\s*msp-docs-e2", normalized)
            or has_forbidden_e2_clean_table_edge(text)
            or has_forbidden_e2_clean_dependency_claim(normalized)
        ):
            fail(f"surfaces.{surface}: direct E2-to-CLEAN path")
        if re.search(
            r"\bmsp-docs-clean\b\s+(?:requires?|needs?)\b"
            r"(?:\s+(?:a|the))?(?:\s+completion)?(?:\s+tokens?)?.*?\bmsp-docs-e2\b",
            normalized,
        ):
            fail(f"surfaces.{surface}: CLEAN token bypass")
    m625_contract = (
        plan_dir / "118-w30-26-m625-raw-spine-feature-acquisition.md"
    ).read_text(encoding="utf-8")
    tool_suffix_matches = re.findall(
        r"^M6\.25 tool suffixes JSON: `(\[[^\r\n]+\])`$",
        m625_contract,
        re.MULTILINE,
    )
    if len(tool_suffix_matches) != 1:
        fail("surfaces.118: exact M6.25 tool suffix record missing or duplicated")
    try:
        documented_tool_suffixes = json.loads(tool_suffix_matches[0])
    except json.JSONDecodeError as exc:
        raise ValidationError(
            "surfaces.118: malformed M6.25 tool suffix JSON"
        ) from exc
    if documented_tool_suffixes != M625_TOOL_SUFFIXES:
        fail("surfaces.118: exact M6.25 tool suffix contract drift")
    correction_text = (plan_dir / M625_MUTATION_CORRECTION).read_text(
        encoding="utf-8"
    )
    no_effect_blocks = re.findall(
        r"```yaml\r?\n(state: no_effect\r?\n.*?)\r?\n```",
        correction_text,
        re.DOTALL,
    )
    if len(no_effect_blocks) != 1:
        fail("surfaces.121: exact no_effect DTO block missing or duplicated")
    try:
        no_effect_dto = yaml.safe_load(no_effect_blocks[0])
    except yaml.YAMLError as exc:
        raise ValidationError(
            "surfaces.121: malformed no_effect DTO"
        ) from exc
    if no_effect_dto != M625_NO_EFFECT_DTO:
        fail("surfaces.121: exact no_effect DTO contract drift")
    compact_correction = " ".join(correction_text.split())
    for fragment in M625_MUTATION_CORRECTION_FRAGMENTS:
        if fragment not in compact_correction:
            fail(f"surfaces.121: missing correction invariant: {fragment}")
    matrix_match = re.search(
        r"^The terminal recovery matrix is therefore:\r?\n\r?\n"
        r"((?:^\|.*\|\r?\n)+)",
        correction_text,
        re.MULTILINE,
    )
    if matrix_match is None:
        fail("surfaces.121: structured recovery matrix missing")
    matrix_rows = []
    for line in matrix_match.group(1).splitlines()[2:]:
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if len(cells) != 3:
            fail("surfaces.121: malformed recovery matrix row")
        matrix_rows.append(cells)
    if tuple(matrix_rows) != M625_RECOVERY_MATRIX:
        fail("surfaces.121: exact recovery matrix drift")
    gate_blocks = re.findall(
        r"```yaml\r?\n(contract_gate:\r?\n.*?)\r?\n```",
        correction_text,
        re.DOTALL,
    )
    if len(gate_blocks) != 1:
        fail("surfaces.121: exact mutation docs gate missing or duplicated")
    try:
        mutation_doc_gate = yaml.safe_load(gate_blocks[0])
    except yaml.YAMLError as exc:
        raise ValidationError(
            "surfaces.121: malformed mutation docs gate"
        ) from exc
    if mutation_doc_gate != M625_MUTATION_DOC_GATE:
        fail("surfaces.121: mutation docs gate direction drift")
    reconciliation_text = (plan_dir / M625_IMPLEMENTATION_RECONCILIATION).read_text(
        encoding="utf-8"
    )
    for receipt in M625_IMPLEMENTATION_RECEIPTS:
        if receipt not in reconciliation_text:
            fail("surfaces.122: published completion receipt drift")
    for fragment in (
        "terminal quarantine",
        "no auto-rollback claim",
        "promotes no mutable leaf",
        "At draft creation, release proof remained pending",
        "SHIP -> eebusreg -> gateway",
        "--set-lab-release-proof released_chain_redeployed",
        "MSP-065-LIVE-R1",
        "non-DAG hardening only",
        "No v2, legacy interface, alias, `candidate_ref`",
        "no-write stop remain fail-closed",
    ):
        if fragment not in reconciliation_text:
            fail(f"surfaces.122: missing reconciliation invariant: {fragment}")
    successor_text = (plan_dir / M625_S13_SUCCESSOR).read_text(
        encoding="utf-8"
    )
    compact_successor = " ".join(successor_text.split())
    for issue_ref in M625_S13_ISSUE_CHAIN:
        if issue_ref not in compact_successor:
            fail("surfaces.123: exact erratum issue chain drift")
    for value in M625_S13_PUBLIC_BASELINE["evidence_sha256"].values():
        if value not in compact_successor:
            fail("surfaces.123: public evidence hash drift")
    for provenance in M625_S13_SCOPE_PROVENANCE["included"]:
        if provenance["commit"] not in compact_successor:
            fail("surfaces.123: bounded provenance commit drift")
    for exclusion in (
        "9970150",
        "eebus:\"key\"",
        "update-engine",
        "9f07e2a30a0c138bbc7e13b19f61ac4981f0a68f",
        "06d9bf07e351c268656532a0b8046c79f3797d23",
        "upstream `dev`",
        "SPINE 1.4",
    ):
        if exclusion not in compact_successor:
            fail(f"surfaces.123: bounded exclusion drift: {exclusion}")
    for fragment in (
        "`lab_release_proof=released_chain_redeployed`",
        "base M6.25 LAB remains accepted",
        "Stable-MCP/M6.25 final closure is held by this bounded erratum",
        "Every pre-existing completion-token edge remains unchanged",
        "appending `MSP-0625-S13-GW-LAB` as an additional predecessor",
        "aggregate READ evidence only",
        "49 | 26 | 23",
        "No raw identity",
        "`candidate_ref` remains prohibited",
        "Erratum execution is READ-only",
        "Every existing no-write stop remains fail-closed",
        "Owner-local raw access and public redacted output remain separate",
        "all 49 target identities",
        "all 26 baseline-success targets remain successful",
        "factory type mismatch",
        "scalar-versus-list or enum-versus-scaled-number",
        "typed-empty reply is not silently promoted",
        "`operationModeId=2` remains unlabeled",
        "Any WRITE, SET, rollback dispatch, or mutation probe fails the gate",
    ):
        if fragment not in compact_successor:
            fail(f"surfaces.123: missing erratum invariant: {fragment}")
    tool_blocks = re.findall(
        r"```json\r?\n(\[[^\r\n]+\])\r?\n```",
        successor_text,
    )
    if len(tool_blocks) != 1:
        fail("surfaces.123: exact tool suffix block missing or duplicated")
    try:
        successor_tools = json.loads(tool_blocks[0])
    except json.JSONDecodeError as exc:
        raise ValidationError("surfaces.123: malformed tool suffix block") from exc
    if successor_tools != M625_TOOL_SUFFIXES:
        fail("surfaces.123: exact M6.25 tool suffix contract drift")
    roadmap = (plan_dir / "14-execution-roadmap-issues-and-gates.md").read_text(encoding="utf-8")
    for row_id, tokens in REQUIRES_COMPLETION_TOKENS.items():
        if row_id in {"MSP-DOCS-E2", "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-E2R-PUBLISH", "MSP-DOCS-E2R-AGGREGATE", "MSP-DOCS-CLEAN", "MSP-03D-R"}:
            for token in tokens:
                if token not in roadmap:
                    fail("surfaces.14: canonical completion claim drift")
    if matrix["issues"][EXACT_IDS.index("MSP-R00-L")]["acceptance_state"] == "ready":
        fail("surfaces: MSP-R00-L may not be ready")
    for surface in ("00-canonical.md", "12-eebus-mcp-first-vr940f.md"):
        text = " ".join((plan_dir / surface).read_text(encoding="utf-8").split())
        if E2R_PREREQUISITES not in text:
            fail(f"surfaces.{surface}: M3.5 E2R prerequisite drift")


def validate_immutable_active_files(plan_dir: Path) -> None:
    for name, expected in IMMUTABLE_ACTIVE_SHA256.items():
        try:
            actual = hashlib.sha256((plan_dir / name).read_bytes()).hexdigest()
        except OSError as exc:
            raise ValidationError(f"immutable active file unavailable: {name}") from exc
        if actual != expected:
            fail(f"immutable active file changed: {name}")


def validate_surfaces(root: Path) -> None:
    plan_dir = root / PLAN
    expected_paths = {f"{PLAN}/{surface}" for surface in EXPECTED_ACTIVE_SURFACES}
    mutable_projection = {
        path for path in MUTABLE_PATHS if path.startswith(PLAN + "/")
    }
    if (
        not expected_paths.issubset(MUTABLE_PATHS)
        or set(active_control_surface_paths()) != expected_paths
        or mutable_projection != expected_paths
    ):
        fail("surfaces: mutable allowlist/projection drift")
    matrix = load_yaml(plan_dir / MATRIX)
    integrity = load_json(plan_dir / INTEGRITY)
    validate_immutable_active_files(plan_dir)
    validate_matrix(matrix)
    validate_integrity(integrity)
    evidence_path = plan_dir / "120-w30-26-current-state-evidence.json"
    validate_current_state_evidence(evidence_path, load_json(evidence_path))
    plan = load_yaml(plan_dir / "plan.yaml")
    validate_plan_projection(plan)
    validate_control_projection(plan, matrix, plan_dir)
    validate_live_audit(matrix, (plan_dir / "107-ad-docs-02-topology-audit.md").read_text(encoding="utf-8"))
    validate_markdown_claims(plan_dir, matrix)

def _ensure_anchor(root: Path) -> None:
    present = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{ANCHOR}^{{commit}}"],
        text=True,
        capture_output=True,
    )
    if present.returncode != 0:
        try:
            subprocess.run(
                ["git", "-C", str(root), "fetch", "--quiet", "origin", ANCHOR],
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ValidationError("protected-path anchor is unavailable") from exc

def _ensure_commit(root: Path, revision: str, message: str) -> None:
    present = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{revision}^{{commit}}"],
        text=True,
        capture_output=True,
    )
    if present.returncode == 0:
        return
    try:
        subprocess.run(
            ["git", "-C", str(root), "fetch", "--quiet", "origin", revision],
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{revision}^{{commit}}"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValidationError(message) from exc

def _require_ancestor(root: Path, ancestor: str, descendant: str, message: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        return
    try:
        subprocess.run(
            ["git", "-C", str(root), "fetch", "--quiet", "--unshallow", "origin"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        pass
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        fail(message)

def _validate_changed_paths(
    root: Path,
    base: str,
    head: str,
    allowed_paths: frozenset[str],
) -> None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "-z", base, head, "--"],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ValidationError("protected-path anchor is unavailable") from exc
    fields = [field for field in result.stdout.split("\0") if field]
    changed_paths: list[str] = []
    index = 0
    while index < len(fields):
        status = fields[index]
        index += 1
        if status.startswith(("R", "C")):
            fail("protected path changed: rename/copy")
        if status.startswith("D"):
            fail("protected path changed: deletion")
        if index >= len(fields):
            fail("protected path changed: malformed name-status")
        path = fields[index]
        index += 1
        if status[:1] != "M" and status[:1] != "A":
            fail("protected path changed: unsupported status")
        if path not in allowed_paths:
            fail(f"protected path changed: {path}")
        changed_paths.append(path)
    for path in changed_paths:
        anchor_tree = subprocess.run(
            ["git", "-C", str(root), "ls-tree", base, "--", path],
            text=True,
            capture_output=True,
            check=True,
        )
        head_tree = subprocess.run(
            ["git", "-C", str(root), "ls-tree", head, "--", path],
            text=True,
            capture_output=True,
            check=True,
        )
        anchor_match = re.fullmatch(
            r"(100644|100755) blob [0-9a-f]{40}\t" + re.escape(path) + r"\n",
            anchor_tree.stdout,
        )
        if anchor_tree.stdout and anchor_match is None:
            fail("protected path changed: mode/type drift")
        expected_mode = anchor_match.group(1) if anchor_match else "100644"
        if not re.fullmatch(
            re.escape(expected_mode) + r" blob [0-9a-f]{40}\t" + re.escape(path) + r"\n",
            head_tree.stdout,
        ):
            fail("protected path changed: mode/type drift")

def validate_issue_63_changeset(
    root: Path = ROOT,
    issue_head: str = "",
) -> None:
    """Verify the explicit live #63 change set against the protected anchor."""
    if re.fullmatch(r"[0-9a-f]{40}", issue_head) is None:
        fail("issue changeset head must be a full lowercase SHA-1")
    _ensure_anchor(root)
    _ensure_commit(root, issue_head, "issue changeset head is unavailable")
    _require_ancestor(root, ANCHOR, issue_head, "issue changeset head does not contain anchor")
    _validate_changed_paths(root, ANCHOR, issue_head, ISSUE_63_ALLOWED_PATHS)

def validate_changed_paths(root: Path = ROOT) -> None:
    """Permanent history guard; future regular files are outside the #63 allowlist."""
    _ensure_anchor(root)
    _require_ancestor(root, ANCHOR, "HEAD", "protected-path anchor is not in HEAD history")
    for relative in PROTECTED_EVIDENCE_PATHS:
        try:
            anchor_bytes = subprocess.run(
                ["git", "-C", str(root), "show", f"{ANCHOR}:{relative}"],
                capture_output=True,
                check=True,
            ).stdout
            current_bytes = (root / relative).read_bytes()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValidationError(f"protected evidence unavailable: {relative}") from exc
        if hashlib.sha256(current_bytes).digest() != hashlib.sha256(anchor_bytes).digest() or current_bytes != anchor_bytes:
            fail(f"protected evidence changed: {relative}")

def main(argv: list[str]) -> int:
    try:
        issue_head: str | None = None
        if len(argv) == 2 and argv[1] == "--write-generated":
            write_generated(ROOT)
            print("generated AD-DOCS-02 projections")
            return 0
        if len(argv) == 3 and argv[1] == "--set-lab-release-proof":
            apply_release_proof_state(ROOT, argv[2])
            validate_surfaces(ROOT)
            print(f"set LAB release proof to {argv[2]} and regenerated projections")
            return 0
        if len(argv) == 3 and argv[1] == "--issue-63-head":
            issue_head = argv[2]
        elif len(argv) != 1:
            fail(
                "usage: validate_ad_docs_02.py [--write-generated | "
                "--set-lab-release-proof STATE | --issue-63-head SHA]"
            )
        validate_surfaces(ROOT)
        if issue_head is None:
            validate_changed_paths(ROOT)
        else:
            validate_issue_63_changeset(ROOT, issue_head)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print("validated AD-DOCS-02")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
