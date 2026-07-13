from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "validate_ad_docs_02.py"
PLAN = ROOT / "multi-runtime-semantic-platform.locked"
spec = importlib.util.spec_from_file_location("validate_ad_docs_02", MODULE)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class AdDocs02ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = yaml.safe_load((PLAN / validator.MATRIX).read_text(encoding="utf-8"))
        self.integrity = json.loads((PLAN / validator.INTEGRITY).read_text(encoding="utf-8"))

    def rejects_matrix(self, document: dict) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.validate_matrix(document)

    def rejects_integrity(self, document: dict) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.validate_integrity(document)

    def row(self, document: dict, row_id: str) -> dict:
        return next(row for row in document["issues"] if row["id"] == row_id)

    def test_accepts_live_typed_contract(self) -> None:
        validator.validate_matrix(self.matrix)
        validator.validate_integrity(self.integrity)

    def test_rejects_self_cycle(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PLATFORM")["requires_completion_tokens"] = ["MSP-DOCS-E2R-PLATFORM"]
        self.rejects_matrix(document)

    def test_rejects_active_forbidden_tier_ultra(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["routing_contract"]["forbidden_tier"] = "ultra"
        self.rejects_matrix(document)

    def test_rejects_embedded_openai_model_resolver(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["routing_contract"]["resolver"] = "openai/gpt-5.6-sol"
        self.rejects_matrix(document)

    def test_rejects_direct_e2_to_clean(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-CLEAN")["requires_completion_tokens"] = ["MSP-DOCS-E2"]
        self.rejects_matrix(document)

    def test_rejects_combined_removed_e2_platform_edge_and_model_field(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["requires_completion_tokens"] = []
        self.row(document, "MSP-DOCS-E2")["routing_contract"]["model"] = "gpt-5.6-sol"
        self.rejects_matrix(document)

    def test_rejects_every_completion_token_map_mutation(self) -> None:
        for row_id, expected in validator.REQUIRES_COMPLETION_TOKENS.items():
            with self.subTest(row_id=row_id):
                document = copy.deepcopy(self.matrix)
                self.row(document, row_id)["requires_completion_tokens"] = expected + ["MSP-00A"]
                self.rejects_matrix(document)

    def test_rejects_every_evidence_input_map_mutation(self) -> None:
        for row_id in validator.EXACT_IDS:
            with self.subTest(row_id=row_id):
                document = copy.deepcopy(self.matrix)
                self.row(document, row_id)["evidence_inputs"] = ["untrusted"]
                self.rejects_matrix(document)

    def test_rejects_unknown_row_field(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["unreviewed"] = True
        self.rejects_matrix(document)

    def test_rejects_missing_required_serial_edge(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PUBLISH")["requires_completion_tokens"] = []
        self.rejects_matrix(document)

    def test_rejects_unknown_completion_token(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2R-PLATFORM")["requires_completion_tokens"] = ["UNKNOWN"]
        self.rejects_matrix(document)

    def test_rejects_model_lane(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-DOCS-E2")["model_lane"] = "historical-only"
        self.rejects_matrix(document)

    def test_rejects_exact_id_drift(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-09D")["id"] = "MSP-09X"
        self.rejects_matrix(document)

    def test_rejects_duplicate_integrity_key(self) -> None:
        raw = (PLAN / validator.INTEGRITY).read_text(encoding="utf-8")
        with self.assertRaises(validator.ValidationError):
            json.loads(raw[:-2] + ',"schema_version":2}', object_pairs_hook=validator._json_object)

    def test_rejects_token_root_drift(self) -> None:
        document = copy.deepcopy(self.integrity)
        document["completion_token_roots"] = document["completion_token_roots"][:1]
        self.rejects_integrity(document)

    def test_rejects_token_replay_or_drift_waiver(self) -> None:
        for field in ("replay_rejected", "drift_rejected"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.integrity)
                document["token_envelope"][field] = False
                self.rejects_integrity(document)

    def test_rejects_readiness_or_cleanup_drift(self) -> None:
        document = copy.deepcopy(self.integrity)
        document["readiness_categories"] = ["selected_batch"]
        self.rejects_integrity(document)

    def test_rejects_each_publication_contract_protected_field(self) -> None:
        mutations = (
            ("publication_entry_kinds", ["wrong"]),
            ("eligible_channels", {"stable": []}),
            ("exact_memberships", {"stable": {"canonical": ["wrong"]}}),
            ("channel_registry", {"canonical": {"visibility": "stable", "owner": "wrong"}}),
            ("absence_constraints", []),
            ("hermetic_git_object_evidence", {"required": [], "moving_refs_rejected": True}),
            ("planned_expiry", {"state": "expired", "action": "block_new_publication"}),
            ("candidate_cleanup", {"state": "candidate", "fail_closed": True, "post_consumption_rollback": "forward_fix_only", "action": "wrong"}),
            ("process_attestation", {"distinct_from": "wrong"}),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                document = copy.deepcopy(self.integrity)
                document[field] = value
                self.rejects_integrity(document)

    def test_rejects_complete_live_audit_mutation(self) -> None:
        with self.assertRaises(validator.ValidationError):
            validator.validate_live_audit(self.matrix, "# incomplete\n")
        document = copy.deepcopy(self.integrity)
        document["candidate_cleanup"]["fail_closed"] = False
        self.rejects_integrity(document)

    def test_accepts_declared_mutable_path(self) -> None:
        present = mock.Mock(returncode=0)
        changed = mock.Mock(stdout="M\0multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\0")
        raw = mock.Mock(stdout=":100644 100644 0000000000000000000000000000000000000000 0000000000000000000000000000000000000000 M\0multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\0")
        tree = mock.Mock(stdout="100644 blob 0000000000000000000000000000000000000000\tmulti-runtime-semantic-platform.locked/105-ad-docs-02-amendment.md\n")
        trees = [
            tree,
            mock.Mock(stdout="100644 blob 0000000000000000000000000000000000000000\tmulti-runtime-semantic-platform.locked/106-ad-docs-02-integrity.json\n"),
            mock.Mock(stdout="100644 blob 0000000000000000000000000000000000000000\tmulti-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\n"),
        ]
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, changed, raw, *trees]):
            validator.validate_changed_paths(ROOT)

    def test_rejects_nested_protected_issue_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/issues/MSP-00B-model-routing.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, completed]):
            with self.assertRaises(validator.ValidationError):
                validator.validate_changed_paths(ROOT)

    def test_rejects_unlisted_control_surface_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/00-unlisted-control-surface.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, completed]):
            with self.assertRaises(validator.ValidationError):
                validator.validate_changed_paths(ROOT)

    def test_rejects_active_prose_pin_and_table_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            pinned = target / "90-issue-map.md"
            pinned.write_text(pinned.read_text(encoding="utf-8") + "\nprovider: openai\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)
            pinned.write_text((PLAN / "90-issue-map.md").read_text(encoding="utf-8") + "\n| MSP-DOCS-E2 | MSP-DOCS-CLEAN |\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)
            pinned.write_text((PLAN / "90-issue-map.md").read_text(encoding="utf-8") + "\nMSP-DOCS-CLEAN requires completion token MSP-DOCS-E2.\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)

    def test_rejects_plan_provider_pin_or_ultra(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            plan = yaml.safe_load((target / "plan.yaml").read_text(encoding="utf-8"))
            plan["routing_policy"]["provider"] = "openai"
            (target / "plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)
            plan.pop("routing_policy")
            plan["routing_policy"] = {"resolver": "canonical", "policy_digest": "required_at_dispatch", "forbidden_tier": "Ultra"}
            (target / "plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)

    def test_rejects_msp_r00_l_ready_and_audit_category_drift(self) -> None:
        document = copy.deepcopy(self.matrix)
        self.row(document, "MSP-R00-L")["acceptance_state"] = "ready"
        self.rejects_matrix(document)
        with self.assertRaises(validator.ValidationError):
            validator.validate_live_audit(self.matrix, (PLAN / "107-ad-docs-02-topology-audit.md").read_text(encoding="utf-8").replace("selected_batch", "selected_batch_drift"))

    def test_rejects_delete_rename_and_type_drift(self) -> None:
        for status, raw in (
            ("D\\0multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\\0", ""),
            ("R100\\0old\\0multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\\0", ""),
            ("M\\0multi-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\\0", ":100644 120000 a b M\\0path\\0"),
        ):
            with self.subTest(status=status):
                present = mock.Mock(returncode=0)
                changed = mock.Mock(stdout=status)
                raw_result = mock.Mock(stdout=raw)
                with mock.patch.object(validator.subprocess, "run", side_effect=[present, changed, raw_result]):
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_changed_paths(ROOT)

    def test_recovers_anchor_from_local_shallow_remote(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin.git"
            work = root / "work"
            subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
            subprocess.run(["git", "init", str(work)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(work), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(work), "config", "user.name", "Test"], check=True)
            for relative in ("105-ad-docs-02-amendment.md", "106-ad-docs-02-integrity.json", "107-ad-docs-02-topology-audit.md"):
                path = work / validator.PLAN / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("anchor\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(work), "add", "."], check=True)
            subprocess.run(["git", "-C", str(work), "commit", "-m", "anchor"], check=True, capture_output=True)
            anchor = subprocess.run(["git", "-C", str(work), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
            subprocess.run(["git", "-C", str(work), "remote", "add", "origin", str(origin)], check=True)
            subprocess.run(["git", "-C", str(work), "push", "-u", "origin", "HEAD:main"], check=True, capture_output=True)
            (work / validator.PLAN / "107-ad-docs-02-topology-audit.md").write_text("head\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(work), "commit", "-am", "head"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(work), "push", "origin", "HEAD:main"], check=True, capture_output=True)
            shallow = root / "shallow"
            subprocess.run(["git", "clone", "--branch", "main", "--depth", "1", "file://" + str(origin), str(shallow)], check=True, capture_output=True)
            with mock.patch.object(validator, "ANCHOR", anchor):
                validator.validate_changed_paths(shallow)

    def test_fails_closed_when_anchor_cannot_be_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            with mock.patch.object(validator, "ANCHOR", "0" * 40):
                with self.assertRaisesRegex(validator.ValidationError, "anchor is unavailable"):
                    validator.validate_changed_paths(repo)


if __name__ == "__main__":
    unittest.main()
