from __future__ import annotations

import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GATE = ROOT / "runtime-gates/fronius-modbus-m1-admission.json"
EXPECTED_KEYS = {
    "branch_protection_evidence_url",
    "docs_merge_sha",
    "docs_pr",
    "docs_repository",
    "required_check",
    "required_check_run_url",
    "required_check_verified_at",
    "schema",
    "state",
    "trust_anchor_commit",
    "trust_anchor_repository",
    "verification_head_sha",
    "verification_pr",
    "version",
}


def validate_gate(require_open: bool) -> list[str]:
    errors: list[str] = []
    value = json.loads(GATE.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != EXPECTED_KEYS:
        return ["gate keys must match the closed schema"]
    if value["schema"] != "helianthus.execution.modbus-m1-admission":
        errors.append("gate schema mismatch")
    if value["version"] != 1 or type(value["version"]) is not int:
        errors.append("gate version mismatch")
    if value["docs_repository"] != (
        "Project-Helianthus/helianthus-docs-ebus"
    ):
        errors.append("docs repository mismatch")
    if value["docs_pr"] != 376 or type(value["docs_pr"]) is not int:
        errors.append("docs PR mismatch")
    if value["trust_anchor_repository"] != (
        "Project-Helianthus/helianthus-execution-plans"
    ):
        errors.append("trust anchor repository mismatch")
    if value["required_check"] != "Modbus Trusted Revision":
        errors.append("required check mismatch")
    if value["state"] == "BLOCKED_PENDING_DOCS_TRUST":
        for key in (
            "branch_protection_evidence_url",
            "docs_merge_sha",
            "required_check_verified_at",
            "required_check_run_url",
            "trust_anchor_commit",
            "verification_head_sha",
            "verification_pr",
        ):
            if value[key] is not None:
                errors.append(f"blocked gate {key} must be null")
        if require_open:
            errors.append("Modbus M1 admission gate is not OPEN")
    elif value["state"] == "OPEN":
        for key in ("docs_merge_sha", "trust_anchor_commit"):
            if not isinstance(value[key], str) or re.fullmatch(
                r"[0-9a-f]{40}", value[key]
            ) is None:
                errors.append(f"open gate {key} must be full lowercase SHA")
        if not isinstance(value["branch_protection_evidence_url"], str):
            errors.append("open gate requires branch-protection evidence")
        if not isinstance(value["required_check_verified_at"], str):
            errors.append("open gate requires verification timestamp")
        if not isinstance(value["required_check_run_url"], str):
            errors.append("open gate requires required-check run URL")
        if not isinstance(value["verification_pr"], int):
            errors.append("open gate requires verification PR")
        if not isinstance(value["verification_head_sha"], str) or re.fullmatch(
            r"[0-9a-f]{40}", value["verification_head_sha"]
        ) is None:
            errors.append("open gate requires verification head SHA")
    else:
        errors.append("unknown gate state")
    return errors


class ModbusM1AdmissionGateTests(unittest.TestCase):
    def test_gate_schema_is_valid(self) -> None:
        self.assertEqual(validate_gate(require_open=False), [])

    def test_m1_admission_is_open_with_closed_evidence_schema(self) -> None:
        self.assertEqual(validate_gate(require_open=True), [])


if __name__ == "__main__":
    unittest.main()
