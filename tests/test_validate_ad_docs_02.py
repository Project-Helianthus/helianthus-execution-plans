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

    def _assert_markdown_claim_rejected(self, appended: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n" + appended, encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def _assert_markdown_claim_accepted(self, appended: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n" + appended, encoding="utf-8")
            validator.validate_markdown_claims(target, self.matrix)

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

    def test_rejects_active_row_string_field_routing_pins_after_markdown_rendering(self) -> None:
        for row_id, field, value in (
            ("MSP-DOCS-E2", "title", "pro<span>vid</span>er: OpenAI"),
            ("MSP-DOCS-E2", "acceptance", ["bare GPT\\-5.5 routing pin"]),
            ("MSP-DOCS-E2", "routing_contract", {
                "resolver": "canonical_resolver",
                "policy_digest": "canonical_policy_digest",
                "forbidden_tier": "gpt&#45;5.5",
            }),
        ):
            with self.subTest(row_id=row_id, field=field):
                document = copy.deepcopy(self.matrix)
                self.row(document, row_id)[field] = value
                self.rejects_matrix(document)

    def test_rejects_matrix_root_or_serialization_drift(self) -> None:
        for mutate in (
            lambda document: document.__setitem__("unexpected", True),
            lambda document: document["serialization"].__setitem__("unexpected", True),
            lambda document: document["serialization"].__setitem__("initial_ready_set", ["MSP-DOCS-CLEAN"]),
        ):
            with self.subTest(mutate=mutate):
                document = copy.deepcopy(self.matrix)
                mutate(document)
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
        tree = mock.Mock(stdout="100644 blob 0000000000000000000000000000000000000000\tmulti-runtime-semantic-platform.locked/107-ad-docs-02-topology-audit.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, mock.Mock(returncode=0), mock.Mock(returncode=0), changed, tree, tree]):
            validator.validate_issue_63_changeset(ROOT, "0" * 40)

    def test_retains_only_anchor_canonical_executable_mode(self) -> None:
        present = mock.Mock(returncode=0)
        path = "scripts/validate_plans_repo.sh"
        changed = mock.Mock(stdout=f"M\0{path}\0")
        tree = mock.Mock(stdout=f"100755 blob {'0' * 40}\t{path}\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, mock.Mock(returncode=0), mock.Mock(returncode=0), changed, tree, tree]):
            validator.validate_issue_63_changeset(ROOT, "0" * 40)

    def test_rejects_nested_protected_issue_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/issues/MSP-00B-model-routing.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, mock.Mock(returncode=0), mock.Mock(returncode=0), completed]):
            with self.assertRaises(validator.ValidationError):
                validator.validate_issue_63_changeset(ROOT, "HEAD")

    def test_rejects_unlisted_control_surface_path(self) -> None:
        present = mock.Mock(returncode=0)
        completed = mock.Mock(stdout="multi-runtime-semantic-platform.locked/00-unlisted-control-surface.md\n")
        with mock.patch.object(validator.subprocess, "run", side_effect=[present, mock.Mock(returncode=0), mock.Mock(returncode=0), completed]):
            with self.assertRaises(validator.ValidationError):
                validator.validate_issue_63_changeset(ROOT, "HEAD")

    def test_default_history_guard_accepts_future_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "anchor.md").write_text("anchor\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "anchor"], check=True, capture_output=True)
            anchor = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
            (repo / "future-plan.md").write_text("future\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "future"], check=True, capture_output=True)
            with mock.patch.object(validator, "ANCHOR", anchor):
                validator.validate_changed_paths(repo)
                with self.assertRaises(validator.ValidationError):
                    validator.validate_issue_63_changeset(repo, "HEAD")

    def test_issue_changeset_rejects_unauthorized_final_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            (repo / "allowed.txt").write_text("anchor\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "anchor"], check=True, capture_output=True)
            anchor = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
            (repo / "allowed.txt").write_text("allowed\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "commit", "-am", "allowed"], check=True, capture_output=True)
            (repo / "unauthorized.txt").write_text("final commit\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-m", "unauthorized final commit"], check=True, capture_output=True)
            head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
            with mock.patch.object(validator, "ANCHOR", anchor), mock.patch.object(validator, "ISSUE_63_ALLOWED_PATHS", frozenset({"allowed.txt"})):
                with self.assertRaisesRegex(validator.ValidationError, "unauthorized.txt"):
                    validator.validate_issue_63_changeset(repo, head)

    def test_cli_passes_current_live_head_to_explicit_changeset_validator(self) -> None:
        live_head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
        with mock.patch.object(validator, "validate_surfaces"), mock.patch.object(validator, "validate_issue_63_changeset") as changeset:
            self.assertEqual(validator.main([str(MODULE), "--issue-63-head", live_head]), 0)
        changeset.assert_called_once_with(validator.ROOT, live_head)

    def test_cli_rejects_missing_or_malformed_explicit_issue_head(self) -> None:
        with mock.patch.object(validator, "validate_surfaces"), mock.patch.object(validator, "validate_changed_paths"):
            self.assertEqual(validator.main([str(MODULE), "--issue-63-head"]), 1)
        with self.assertRaisesRegex(validator.ValidationError, "full lowercase"):
            validator.validate_issue_63_changeset(ROOT, "not-a-sha")

    def test_pull_request_event_uses_live_head_and_fails_closed_when_invalid(self) -> None:
        live_head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
        with tempfile.TemporaryDirectory() as tmp:
            event_path = Path(tmp) / "event.json"
            event_path.write_text(json.dumps({"pull_request": {"head": {"sha": live_head}}}), encoding="utf-8")
            self.assertEqual(validator.pull_request_head_from_event(event_path), live_head)
            for raw in ("{", json.dumps({"pull_request": {"head": {}}})):
                with self.subTest(raw=raw):
                    event_path.write_text(raw, encoding="utf-8")
                    with self.assertRaises(validator.ValidationError):
                        validator.pull_request_head_from_event(event_path)
            with self.assertRaises(validator.ValidationError):
                validator.pull_request_head_from_event(Path(tmp) / "missing-event.json")

    def test_explicit_issue_head_is_fetched_when_pr_checkout_lacks_it(self) -> None:
        head = "1" * 40
        missing = mock.Mock(returncode=1)
        fetched = mock.Mock(returncode=0)
        present = mock.Mock(returncode=0)
        with mock.patch.object(validator.subprocess, "run", side_effect=[missing, fetched, present]) as run:
            validator._ensure_commit(ROOT, head, "unavailable")
        self.assertEqual(run.call_args_list[1].args[0][-1], head)

    def test_rejects_active_prose_pin_and_table_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            pinned = target / "90-issue-map.md"
            pinned.write_text(pinned.read_text(encoding="utf-8") + "\nprovider: openai\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)
            pinned.write_text((PLAN / "90-issue-map.md").read_text(encoding="utf-8") + "\n| MSP-DOCS-E2 | → | MSP-DOCS-CLEAN |\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)
            pinned.write_text((PLAN / "90-issue-map.md").read_text(encoding="utf-8") + "\nMSP-DOCS-CLEAN requires completion token MSP-DOCS-E2.\n", encoding="utf-8")
            with self.assertRaises(validator.ValidationError):
                validator.validate_surfaces(root)

    def test_rejects_bypass_or_pin_mutation_for_every_active_control_surface(self) -> None:
        for relative in validator.active_control_surface_paths():
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    target = root / validator.PLAN
                    shutil.copytree(PLAN, target)
                    path = root / relative
                    if path.suffix == ".md":
                        path.write_text(
                            path.read_text(encoding="utf-8") + "\nprovider: openai\n",
                            encoding="utf-8",
                        )
                    elif path.name == validator.MATRIX:
                        document = yaml.safe_load(path.read_text(encoding="utf-8"))
                        self.row(document, "MSP-DOCS-CLEAN")["requires_completion_tokens"] = ["MSP-DOCS-E2"]
                        path.write_text(yaml.safe_dump(document), encoding="utf-8")
                    elif path.name == validator.INTEGRITY:
                        document = json.loads(path.read_text(encoding="utf-8"))
                        document["routing_contract"]["resolver"] = "openai/gpt-5.6-sol"
                        path.write_text(json.dumps(document), encoding="utf-8")
                    elif path.name == "plan.yaml":
                        document = yaml.safe_load(path.read_text(encoding="utf-8"))
                        document["routing_policy"]["provider"] = "openai"
                        path.write_text(yaml.safe_dump(document), encoding="utf-8")
                    else:
                        path.write_text(
                            path.read_text(encoding="utf-8").replace(
                                "MSP-DOCS-E2R-PLATFORM", "MSP-DOCS-CLEAN", 1
                            ),
                            encoding="utf-8",
                        )
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_surfaces(root)

    def test_active_control_surface_projection_matches_fixed_expected_set(self) -> None:
        self.assertEqual(
            validator.EXPECTED_ACTIVE_SURFACES,
            (
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
            ),
        )
        self.assertEqual(
            set(validator.active_control_surface_paths()),
            {
                f"{validator.PLAN}/{surface}"
                for surface in validator.EXPECTED_ACTIVE_SURFACES
            },
        )

    def test_rejects_fixed_surface_missing_from_mutable_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(PLAN, root / validator.PLAN)
            missing = f"{validator.PLAN}/01-index.md"
            with mock.patch.object(validator, "MUTABLE_PATHS", validator.MUTABLE_PATHS - {missing}):
                with self.assertRaises(validator.ValidationError):
                    validator.validate_surfaces(root)

    def test_rejects_normalized_routing_pin_on_every_markdown_active_surface(self) -> None:
        for relative in validator.active_control_surface_paths():
            if not relative.endswith(".md"):
                continue
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    target = root / validator.PLAN
                    shutil.copytree(PLAN, target)
                    path = root / relative
                    path.write_text(
                        path.read_text(encoding="utf-8") + "\nprovider OpenAI; model gpt 5.6\n",
                        encoding="utf-8",
                    )
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_markdown_claims(target, self.matrix)

    def test_rejects_long_distance_clean_token_bypass_after_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nMSP-DOCS-CLEAN requires completion token "
                + ("filler " * 50)
                + "MSP-DOCS-E2.\n",
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def test_rejects_html_entity_provider_and_model_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nprovider: Open&#65;I; model: gpt&#45;5.6\n",
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def test_rejects_html_comment_split_provider_pin(self) -> None:
        self._assert_markdown_claim_rejected("pro<!-- inactive -->vider: OpenAI\n")

    def test_renders_inline_html_before_evaluating_provider_pin(self) -> None:
        self.assertEqual(validator.render_inline_html("pro<span>vid</span>er"), "provider")
        self._assert_markdown_claim_rejected("pro<span>vid</span>er: OpenAI\n")

    def test_renders_empty_inline_html_before_e2_arrow_check(self) -> None:
        self.assertEqual(validator.render_inline_html("MSP-DOCS-E2<span></span> → MSP-DOCS-CLEAN"), "MSP-DOCS-E2 → MSP-DOCS-CLEAN")
        self._assert_markdown_claim_rejected("MSP-DOCS-E2<span></span> → MSP-DOCS-CLEAN\n")

    def test_rejects_malformed_or_unclosed_active_inline_html(self) -> None:
        for text in ("pro<span>vider", "pro</span>vider", "pro<span><em>vider</span></em>", "pro<!-- incomplete"):
            with self.subTest(text=text):
                with self.assertRaises(validator.ValidationError):
                    validator.render_inline_html(text)

    def test_rejects_bold_split_provider_pin(self) -> None:
        self._assert_markdown_claim_rejected("pro**vid**er: OpenAI\n")

    def test_rejects_link_rendered_e2_to_clean_arrow(self) -> None:
        self._assert_markdown_claim_rejected("[MSP-DOCS-E2](https://example.invalid) → [MSP-DOCS-CLEAN](https://example.invalid)\n")

    def test_rejects_cyrillic_lookalike_pin(self) -> None:
        self._assert_markdown_claim_rejected("pr\u043evider: OpenAI\n")

    def test_rejects_zero_width_provider_and_model_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\npro\u200bvider: OpenAI; mo\u200bdel: gpt-5.6\n",
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def test_rejects_html_entity_direct_e2_to_clean_arrow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nMSP-DOCS-E2 &#x2192; MSP-DOCS-CLEAN\n",
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def test_rejects_long_rightward_arrow_e2_to_clean_bypass(self) -> None:
        self._assert_markdown_claim_rejected("MSP‐DOCS‐E2 \u27f6 MSP‐DOCS‐CLEAN\n")

    def test_rejects_normalized_table_direct_e2_to_clean_bypasses(self) -> None:
        for row in (
            "| MSP‐DOCS‐E2 | → | MSP‐DOCS‐CLEAN |",
            "| MSP&#45;DOCS&#45;E2 | &#x2192; | MSP&#45;DOCS&#45;CLEAN |",
            "| <span>MSP‐DOCS‐E2</span> | <em>→</em> | <em>MSP&#45;DOCS&#45;CLEAN</em> |",
            "| MSP‐DOCS‐CLEAN | ← | MSP‐DOCS‐E2 |",
        ):
            with self.subTest(row=row):
                self._assert_markdown_claim_rejected(row + "\n")

    def test_parses_outerless_and_escaped_pipe_table_edges(self) -> None:
        for row in (
            "MSP-DOCS-E2|->|MSP-DOCS-CLEAN",
            "MSP-DOCS-CLEAN|<-|MSP-DOCS-E2",
            "MSP-DOCS-E2|\\->|MSP-DOCS-CLEAN\\|",
        ):
            with self.subTest(row=row):
                self._assert_markdown_claim_rejected(row + "\n")

    def test_accepts_outerless_reverse_and_descriptive_table_rows(self) -> None:
        for row in (
            "MSP-DOCS-E2|<-|MSP-DOCS-CLEAN",
            "MSP-DOCS-CLEAN|->|MSP-DOCS-E2",
            "MSP-DOCS-E2|descriptive non-edge cell|MSP-DOCS-CLEAN",
        ):
            with self.subTest(row=row):
                self._assert_markdown_claim_accepted(row + "\n")

    def test_accepts_reverse_or_non_edge_table_cell_sequences(self) -> None:
        for row in (
            "| MSP-DOCS-E2 | ← | MSP-DOCS-CLEAN |",
            "| MSP-DOCS-CLEAN | → | MSP-DOCS-E2 |",
            "| MSP-DOCS-E2 | descriptive non-edge cell | MSP-DOCS-CLEAN |",
        ):
            with self.subTest(row=row):
                self._assert_markdown_claim_accepted(row + "\n")

    def test_rejects_leftward_spelling_of_forbidden_e2_to_clean_edge(self) -> None:
        self.assertEqual(
            validator.normalize_markdown("MSP-DOCS-CLEAN ← MSP-DOCS-E2"),
            "msp-docs-clean <- msp-docs-e2",
        )
        self._assert_markdown_claim_rejected("MSP-DOCS-CLEAN ← MSP-DOCS-E2\n")

    def test_preserves_non_forbidden_leftward_e2_to_clean_spelling(self) -> None:
        # `E2 ← CLEAN` means CLEAN feeds E2, not the forbidden E2-to-CLEAN edge.
        self.assertEqual(
            validator.normalize_markdown("MSP-DOCS-E2 ← MSP-DOCS-CLEAN"),
            "msp-docs-e2 <- msp-docs-clean",
        )
        self._assert_markdown_claim_accepted("MSP-DOCS-E2 ← MSP-DOCS-CLEAN\n")

    def test_preserves_ascii_leftward_text_as_direction_not_html(self) -> None:
        self.assertEqual(
            validator.normalize_markdown("MSP-DOCS-E2 <- MSP-DOCS-CLEAN"),
            "msp-docs-e2 <- msp-docs-clean",
        )
        self._assert_markdown_claim_accepted("MSP-DOCS-E2 <- MSP-DOCS-CLEAN\n")
        self._assert_markdown_claim_rejected("MSP-DOCS-CLEAN <- MSP-DOCS-E2\n")

    def test_rejects_bidirectional_unicode_arrows_fail_closed(self) -> None:
        for arrow in ("↔", "⇔", "⟷"):
            with self.subTest(arrow=arrow):
                with self.assertRaisesRegex(validator.ValidationError, "bidirectional Unicode arrow"):
                    validator.normalize_markdown(f"MSP-DOCS-E2 {arrow} MSP-DOCS-CLEAN")

    def test_canonicalizes_representative_unicode_dash_and_arrow_variants(self) -> None:
        self.assertEqual(
            validator.normalize_markdown("MSP‐DOCS–E2 ⇒ MSP−DOCS-CLEAN ⟶ MSP-DOCS-CLEAN"),
            "msp-docs-e2 -> msp-docs-clean -> msp-docs-clean",
        )
        self.assertEqual(validator.normalize_markdown("‐‑‒–—―−"), "-------")
        self.assertEqual(validator.normalize_markdown("→⟶⇒"), "->->->")

    def test_rejects_other_non_ascii_symbol_confusables(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "non-ASCII symbol"):
            validator.normalize_markdown("MSP-DOCS-E2 ∴ MSP-DOCS-CLEAN")

    def test_rejects_long_clean_token_bypass_with_html_entity_e2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / validator.PLAN
            shutil.copytree(PLAN, target)
            path = target / "90-issue-map.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nMSP-DOCS-CLEAN requires completion token "
                + ("filler " * 50)
                + "MSP-DOCS-&#69;2.\n",
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationError):
                validator.validate_markdown_claims(target, self.matrix)

    def test_m35_prerequisites_name_the_complete_e2r_chain(self) -> None:
        expected = "MSP-DOCS-E2, MSP-DOCS-E2R-PLATFORM, MSP-DOCS-E2R-PUBLISH, MSP-DOCS-E2R-AGGREGATE, MSP-DOCS-CLEAN"
        for surface in ("00-canonical.md", "12-eebus-mcp-first-vr940f.md"):
            with self.subTest(surface=surface):
                self.assertIn(expected, " ".join((PLAN / surface).read_text(encoding="utf-8").split()))

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
                with mock.patch.object(validator.subprocess, "run", side_effect=[present, mock.Mock(returncode=0), mock.Mock(returncode=0), changed, raw_result]):
                    with self.assertRaises(validator.ValidationError):
                        validator.validate_issue_63_changeset(ROOT, "HEAD")

    def test_rejects_executable_mode_for_each_ad_docs_artifact(self) -> None:
        for artifact in (
            "105-ad-docs-02-amendment.md",
            "106-ad-docs-02-integrity.json",
            "107-ad-docs-02-topology-audit.md",
        ):
            with self.subTest(artifact=artifact):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
                    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
                    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
                    path = repo / validator.PLAN / artifact
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("anchor\n", encoding="utf-8")
                    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                    subprocess.run(["git", "-C", str(repo), "commit", "-m", "anchor"], check=True, capture_output=True)
                    anchor = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
                    path.chmod(0o755)
                    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
                    subprocess.run(["git", "-C", str(repo), "commit", "-m", "make executable"], check=True, capture_output=True)
                    with mock.patch.object(validator, "ANCHOR", anchor):
                        with self.assertRaises(validator.ValidationError):
                            validator.validate_issue_63_changeset(repo, "HEAD")

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
