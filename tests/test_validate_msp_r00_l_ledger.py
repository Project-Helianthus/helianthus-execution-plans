from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_msp_r00_l_ledger.py"
VALIDATE_REPO_SCRIPT = ROOT / "scripts" / "validate_plans_repo.sh"

spec = importlib.util.spec_from_file_location("validate_msp_r00_l_ledger", MODULE_PATH)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

LEDGER_PATH = validator.resolve_default_ledger(ROOT)


class MspR00LLedgerValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        self.ledger_bytes = LEDGER_PATH.read_bytes()

    def write_temp_ledger(self, root: Path, state: str) -> Path:
        plan_dir = root / f"{validator.PLAN_SLUG}.{state}"
        plan_dir.mkdir()
        ledger_path = plan_dir / validator.LEDGER_FILENAME
        ledger_path.write_bytes(self.ledger_bytes)
        return ledger_path

    def assert_rejects(self, mutated: dict) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
            json.dump(mutated, handle)
            handle.flush()
            with self.assertRaises(validator.ValidationError):
                validator.validate_ledger(Path(handle.name))

    def assert_raw_rejects(self, raw_json: str) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json") as handle:
            handle.write(raw_json)
            handle.flush()
            with self.assertRaises(validator.ValidationError):
                validator.validate_ledger(Path(handle.name))

    def valid_entry_json(self) -> str:
        return json.dumps(self.ledger["entries"][0], indent=6)

    def test_accepts_public_redacted_ledger(self) -> None:
        validator.validate_ledger(LEDGER_PATH)

    def test_accepts_synchronized_msp_r00_l_state_surfaces(self) -> None:
        validator.validate_plan_state_surfaces(ROOT)

    def copy_state_surfaces(self, root: Path) -> Path:
        self.write_temp_ledger(root, "locked")
        plan_dir = root / f"{validator.PLAN_SLUG}.locked"
        for name in (
            validator.MATRIX_FILENAME,
            validator.ISSUE_MAP_FILENAME,
            validator.STATUS_FILENAME,
            validator.TOPOLOGY_FILENAME,
        ):
            source = LEDGER_PATH.parent / name
            target = plan_dir / name
            target.write_bytes(source.read_bytes())
        return plan_dir

    def test_explicit_cli_path_validation_preserves_ledger_bytes(self) -> None:
        before = LEDGER_PATH.read_bytes()
        validator.validate_ledger(LEDGER_PATH)
        self.assertEqual(before, LEDGER_PATH.read_bytes())

    def test_rejects_msp_r00_l_matrix_state_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                matrix.read_text(encoding="utf-8").replace(
                    "  - id: MSP-R00-L\n"
                    "    title: Review and publish the redacted recovery ledger",
                    "  - id: MSP-R00-L\n"
                    "    title: Review and publish the redacted recovery ledger\n"
                    "    acceptance_state: ready",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_docs_verify_state_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                matrix.read_text(encoding="utf-8").replace(
                    "  - id: DOCS-VERIFY\n"
                    "    title: Verify docs ownership, license, template, and path layout\n"
                    "    repo: helianthus-docs-eebus\n"
                    "    milestone: RECOVERY_RECONCILIATION\n"
                    "    complexity: 4\n"
                    "    model_lane: gpt-5.4-mini\n"
                    "    predecessors: []\n"
                    "    docs_owner: helianthus-docs-ebus/docs/platform\n"
                    "    doc_gate: verify\n"
                    "    transport_gate: none\n"
                    "    security_gate: required\n"
                    "    rollback_ledger: revert verification row only\n"
                    "    review_ledger: docs ownership and public-source review\n"
                    "    tdd_mode: docs_checklist\n"
                    "    smoke_scope: license, owners, issue template, path layout, cross-seeding\n"
                    "    acceptance_state: accepted\n"
                    "    completion_note: completed by Project-Helianthus/helianthus-docs-eebus PR #5 at 954b6353",
                    "  - id: DOCS-VERIFY\n"
                    "    title: Verify docs ownership, license, template, and path layout\n"
                    "    repo: helianthus-docs-eebus\n"
                    "    milestone: RECOVERY_RECONCILIATION\n"
                    "    complexity: 4\n"
                    "    model_lane: gpt-5.4-mini\n"
                    "    predecessors: []\n"
                    "    docs_owner: helianthus-docs-ebus/docs/platform\n"
                    "    doc_gate: verify\n"
                    "    transport_gate: none\n"
                    "    security_gate: required\n"
                    "    rollback_ledger: revert verification row only\n"
                    "    review_ledger: docs ownership and public-source review\n"
                    "    tdd_mode: docs_checklist\n"
                    "    smoke_scope: license, owners, issue template, path layout, cross-seeding\n"
                    "    acceptance_state: ready\n"
                    "    completion_note: completed by Project-Helianthus/helianthus-docs-eebus PR #5 at 954b6353",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_api_schema_state_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                matrix.read_text(encoding="utf-8").replace(
                    "    acceptance_state: ready\n"
                    "    readiness_note: ready after execution-plans PR #62 merges;",
                    "    acceptance_state: proposed\n"
                    "    readiness_note: ready after execution-plans PR #62 merges;",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_duplicate_api_schema_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                matrix.read_text(encoding="utf-8").replace(
                    "  - id: MSP-DOCS-API-SCHEMA\n"
                    "    title: Freeze eeBUS Go public API schema inputs",
                    "  - id: MSP-DOCS-API-SCHEMA\n"
                    "    title: Freeze eeBUS Go public API schema inputs\n"
                    "    acceptance_state: accepted",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_invalid_matrix_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                "invalid: [\n" + matrix.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_complexity_outside_model_lane_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            text = matrix.read_text(encoding="utf-8").replace(
                "    complexity: 7\n"
                "    model_lane: GPT-5.5 high\n"
                "    predecessors: [DOCS-VERIFY]",
                "    complexity: 11\n"
                "    model_lane: GPT-5.5 xhigh\n"
                "    predecessors: [DOCS-VERIFY]",
                1,
            )
            matrix.write_text(text, encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_accepts_monotonic_downstream_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            text = matrix.read_text(encoding="utf-8")
            text = text.replace(
                "    acceptance_state: ready\n"
                "    readiness_note: ready after execution-plans PR #62 merges;",
                "    acceptance_state: accepted\n"
                "    readiness_note: ready after execution-plans PR #62 merges;",
                1,
            )
            text = text.replace(
                "    acceptance_state: proposed\n"
                "    blocked_note: after execution-plans PR #62 merges, MSP-R00-L is satisfied",
                "    acceptance_state: ready\n"
                "    blocked_note: after execution-plans PR #62 merges, MSP-R00-L is satisfied",
                1,
            )
            matrix.write_text(text, encoding="utf-8")
            topology = plan_dir / validator.TOPOLOGY_FILENAME
            topology.write_text(
                topology.read_text(encoding="utf-8").replace(
                    '- Current ready set: `["MSP-DOCS-API-SCHEMA"]`',
                    '- Current ready set: `["MSP-DOCS-PLATFORM"]`',
                    1,
                ),
                encoding="utf-8",
            )
            validator.validate_plan_state_surfaces(root)

    def test_rejects_stale_topology_ready_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            topology = plan_dir / validator.TOPOLOGY_FILENAME
            topology.write_text(
                topology.read_text(encoding="utf-8").replace(
                    '- Current ready set: `["MSP-DOCS-API-SCHEMA"]`',
                    '- Current ready set: `["MSP-R00-L", "DOCS-VERIFY"]`',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_rejects_stale_topology_results(self) -> None:
        mutations = (
            ("- Row count: `43`", "- Row count: `42`"),
            ("- Unique IDs: `43`", "- Unique IDs: `42`"),
            ("- Missing predecessor references: `[]`", '- Missing predecessor references: `[["MSP-X", "MSP-Y"]]`'),
            ("- Cycles: `[]`", '- Cycles: `[["MSP-X", "MSP-X"]]`'),
            ("- Model-lane mismatches: `[]`", '- Model-lane mismatches: `[["MSP-X", "wrong", "expected"]]`'),
            ("  `MSP-DOCS-CANDIDATE-CLEANUP`", "  `MSP-DOCS-CANDIDATE-CLEANUP-STALE`"),
        )
        for original, replacement in mutations:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plan_dir = self.copy_state_surfaces(root)
                topology = plan_dir / validator.TOPOLOGY_FILENAME
                topology.write_text(
                    topology.read_text(encoding="utf-8").replace(original, replacement, 1),
                    encoding="utf-8",
                )
                with self.assertRaises(validator.ValidationError):
                    validator.validate_plan_state_surfaces(root)

    def test_rejects_cleanup_activation_or_preemption_drift(self) -> None:
        mutations = (
            (
                "      activates_when: candidate expires or source PR closes unmerged",
                "      activates_when: never",
            ),
            (
                "      preempts_same_repo_successors: true",
                "      preempts_same_repo_successors: false",
            ),
        )
        for original, replacement in mutations:
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                plan_dir = self.copy_state_surfaces(root)
                matrix = plan_dir / validator.MATRIX_FILENAME
                matrix.write_text(
                    matrix.read_text(encoding="utf-8").replace(original, replacement, 1),
                    encoding="utf-8",
                )
                with self.assertRaises(validator.ValidationError):
                    validator.validate_plan_state_surfaces(root)

    def test_rejects_platform_advance_before_api_schema_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan_dir = self.copy_state_surfaces(root)
            matrix = plan_dir / validator.MATRIX_FILENAME
            matrix.write_text(
                matrix.read_text(encoding="utf-8").replace(
                    "    acceptance_state: proposed\n"
                    "    blocked_note: after execution-plans PR #62 merges, MSP-R00-L is satisfied",
                    "    acceptance_state: ready\n"
                    "    blocked_note: after execution-plans PR #62 merges, MSP-R00-L is satisfied",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_plan_state_surfaces(root)

    def test_repo_validator_disables_python_bytecode_before_python_invocations(self) -> None:
        lines = VALIDATE_REPO_SCRIPT.read_text(encoding="utf-8").splitlines()
        export_index = lines.index("export PYTHONDONTWRITEBYTECODE=1")
        python_invocations = [
            index
            for index, line in enumerate(lines)
            if line.startswith("python3 ") or '"$TOKEN_VENV/bin/python"' in line
        ]
        self.assertGreaterEqual(len(python_invocations), 2)
        self.assertLess(export_index, min(python_invocations))

    def test_success_output_does_not_expose_checkout_path(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = validator.main([str(MODULE_PATH), str(LEDGER_PATH)])
        self.assertEqual(result, 0)
        self.assertEqual(output.getvalue(), f"validated {validator.ARTIFACT_KIND}\n")
        self.assertNotIn(str(ROOT), output.getvalue())

    def test_failure_output_does_not_expose_validation_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid-ledger.json"
            path.write_text("{", encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = validator.main([str(MODULE_PATH), str(path)])
            self.assertEqual(result, 1)
            self.assertIn("ledger: invalid JSON", error.getvalue())
            self.assertNotIn(str(path.parent), error.getvalue())

    def test_missing_ledger_output_does_not_expose_validation_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing-ledger.json"
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = validator.main([str(MODULE_PATH), str(path)])
            self.assertEqual(result, 1)
            self.assertIn("ledger: unable to read UTF-8 input", error.getvalue())
            self.assertNotIn(str(path.parent), error.getvalue())

    def test_unknown_key_output_does_not_echo_candidate_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid-ledger.json"
            mutated = copy.deepcopy(self.ledger)
            candidate = "/Users/alice/private/raw-capture"
            mutated[candidate] = "redacted"
            path.write_text(json.dumps(mutated), encoding="utf-8")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = validator.main([str(MODULE_PATH), str(path)])
            self.assertEqual(result, 1)
            self.assertNotIn(candidate, error.getvalue())

    def test_invalid_utf8_output_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid-ledger.json"
            path.write_bytes(b"\xff")
            error = io.StringIO()
            with contextlib.redirect_stderr(error):
                result = validator.main([str(MODULE_PATH), str(path)])
            self.assertEqual(result, 1)
            self.assertEqual(error.getvalue(), "ledger: unable to read UTF-8 input\n")
            self.assertNotIn(str(path.parent), error.getvalue())

    def test_rejects_extra_cli_arguments(self) -> None:
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            result = validator.main([str(MODULE_PATH), str(LEDGER_PATH), "extra"])
        self.assertEqual(result, 1)
        self.assertEqual(
            error.getvalue(),
            "usage: validate_msp_r00_l_ledger.py [ledger.json]\n",
        )

    def test_discovers_default_locked_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "locked")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_discovers_default_implementing_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "implementing")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_discovers_default_maintenance_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = self.write_temp_ledger(root, "maintenance")
            self.assertEqual(validator.resolve_default_ledger(root), expected)
            validator.validate_ledger(root=root)

    def test_temp_ledger_helper_supports_non_locked_lifecycle_states(self) -> None:
        for state in ("implementing", "maintenance"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                expected = self.write_temp_ledger(root, state)
                self.assertEqual(
                    expected,
                    root / f"{validator.PLAN_SLUG}.{state}" / validator.LEDGER_FILENAME,
                )
                self.assertEqual(validator.resolve_default_ledger(root), expected)
                validator.validate_ledger(root=root)

    def test_rejects_missing_default_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(Path(tmp))

    def test_rejects_active_directory_without_default_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / f"{validator.PLAN_SLUG}.locked").mkdir()
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(root)

    def test_rejects_ambiguous_default_ledgers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_temp_ledger(root, "locked")
            self.write_temp_ledger(root, "implementing")
            with self.assertRaises(validator.ValidationError):
                validator.resolve_default_ledger(root)

    def test_rejects_extra_root_key(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["unexpected"] = "redacted"
        self.assert_rejects(mutated)

    def test_rejects_non_v4_uuid(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["opaque_public_id"] = "845fdc27-ae1c-1989-9cd5-4139f989410d"
        self.assert_rejects(mutated)

    def test_rejects_wrong_issue_ref(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["clean_main_issue_ref"] = "Project-Helianthus/helianthus-eebusreg#15"
        self.assert_rejects(mutated)

    def test_rejects_unknown_enum(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["disposition"] = "accepted"
        self.assert_rejects(mutated)

    def test_rejects_class_disposition_mismatch(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["disposition"] = "private_restricted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_extra_key(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["local_hash"] = "redacted"
        self.assert_rejects(mutated)

    def test_rejects_forbidden_value_pattern(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["entries"][0]["redaction_categories"]["origin_locator"] = "2026-01-01"
        self.assert_rejects(mutated)

    def test_rejects_duplicate_root_key_before_hidden_value_is_overwritten(self) -> None:
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": "commit",
  "entries": [
    {self.valid_entry_json()}
  ]
}}"""
        )

    def test_rejects_duplicate_entry_key_before_hidden_value_is_overwritten(self) -> None:
        entry = self.ledger["entries"][0]
        redaction = json.dumps(entry["redaction_categories"], indent=6)
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": [
    {{
      "opaque_public_id": "{entry["opaque_public_id"]}",
      "clean_main_issue_ref": "{entry["clean_main_issue_ref"]}",
      "public_class": "commit",
      "public_class": "{entry["public_class"]}",
      "disposition": "{entry["disposition"]}",
      "redaction_categories": {redaction}
    }}
  ]
}}"""
        )

    def test_rejects_duplicate_nested_key_before_hidden_value_is_overwritten(self) -> None:
        entry = self.ledger["entries"][0]
        self.assert_raw_rejects(
            f"""{{
  "artifact_kind": "msp_r00_l_public_redacted_recovery_ledger",
  "entries": [
    {{
      "opaque_public_id": "{entry["opaque_public_id"]}",
      "clean_main_issue_ref": "{entry["clean_main_issue_ref"]}",
      "public_class": "{entry["public_class"]}",
      "disposition": "{entry["disposition"]}",
      "redaction_categories": {{
        "origin_locator": "commit",
        "origin_locator": "redacted",
        "runtime_identity": "redacted",
        "evidence_payload": "redacted",
        "integrity_preimage": "redacted",
        "quantity_observation": "redacted",
        "temporal_observation": "redacted"
      }}
    }}
  ]
}}"""
        )


if __name__ == "__main__":
    unittest.main()
