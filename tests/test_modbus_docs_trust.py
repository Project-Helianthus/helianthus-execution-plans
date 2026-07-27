from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import validate_modbus_docs_trust as trust_validator


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_modbus_docs_trust.py"
FROZEN_SEMANTIC_VALIDATOR = (
    ROOT / "tests/fixtures/modbus_companion_v1.py"
)
ANCHOR_SHA = "c" * 40
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
PROTECTED = (
    pathlib.Path(".github/workflows/modbus-trusted-revision.yml"),
    pathlib.Path("scripts/validate_modbus_revision_transition.py"),
    pathlib.Path("scripts/validate_modbus_companion.py"),
)
SEMANTIC_VALIDATOR_BYTES = b"frozen semantic validator fixture\n"
ARTIFACTS = {
    "consumer_lock_schema": (
        "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json"
    ),
    "policy": "docs/platform/modbus-foundation-profile-contract-v1.md",
    "trusted_revision_validator": (
        "scripts/validate_modbus_revision_transition.py"
    ),
    "trusted_revision_workflow": (
        ".github/workflows/modbus-trusted-revision.yml"
    ),
    "wire": "protocols/modbus/modbus-phase-one-wire-v1.md",
}


class ModbusDocsTrustTests(unittest.TestCase):
    def test_frozen_semantic_validator_digest_is_real(self) -> None:
        self.assertEqual(
            hashlib.sha256(FROZEN_SEMANTIC_VALIDATOR.read_bytes()).hexdigest(),
            trust_validator.V1_SEMANTIC_VALIDATOR_SHA256,
        )

    def materialize(self, root: pathlib.Path) -> pathlib.Path:
        hashes: dict[str, str] = {}
        for key, raw_path in ARTIFACTS.items():
            relative = pathlib.Path(raw_path)
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"{key} fixture\n", encoding="utf-8")
            hashes[key] = hashlib.sha256(target.read_bytes()).hexdigest()
        for relative in PROTECTED:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative == PROTECTED[0]:
                target.write_text(
                    json.dumps(
                        trust_validator.expected_workflow(ANCHOR_SHA),
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            elif relative == PROTECTED[1]:
                target.write_bytes(VALIDATOR.read_bytes())
            else:
                target.write_bytes(SEMANTIC_VALIDATOR_BYTES)
        hashes = {
            key: hashlib.sha256((root / raw_path).read_bytes()).hexdigest()
            for key, raw_path in ARTIFACTS.items()
        }
        manifest = {
            "artifact_sha256": hashes,
            "artifacts": ARTIFACTS,
            "consumer_pin": {"content_revision": 1},
            "content_revision": 1,
            "repository": "Project-Helianthus/helianthus-docs-ebus",
            "schema": "helianthus.modbus.foundation-profile-companion",
            "source_policy": {
                "restricted_source_copy": "forbidden",
            },
            "trust_anchor": {
                "commit_sha": ANCHOR_SHA,
                "local_mirror": PROTECTED[1].as_posix(),
                "m1_admission_gate": (
                    "runtime-gates/fronius-modbus-m1-admission.json"
                ),
                "repository": (
                    "Project-Helianthus/helianthus-execution-plans"
                ),
                "workflow": PROTECTED[0].as_posix(),
            },
            "version": 1,
        }
        target = root / MANIFEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        normalized_digest = trust_validator._normalized_manifest_digest(manifest)
        assert normalized_digest is not None
        self.normalized_manifest_digest = normalized_digest
        return root

    def run_validator(
        self,
        prior: pathlib.Path,
        current: pathlib.Path,
    ) -> list[str]:
        with (
            mock.patch.object(
                trust_validator,
                "V1_SEMANTIC_VALIDATOR_SHA256",
                hashlib.sha256(SEMANTIC_VALIDATOR_BYTES).hexdigest(),
            ),
            mock.patch.object(
                trust_validator,
                "V1_NORMALIZED_MANIFEST_SHA256",
                self.normalized_manifest_digest,
            ),
        ):
            return trust_validator.validate_transition(
                prior.resolve(),
                current.resolve(),
                ANCHOR_SHA,
            )

    def test_bootstrap_introduction_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            self.assertEqual(self.run_validator(prior, current), [])

    def test_bootstrap_rejects_weakened_transition_mirror(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            (current / PROTECTED[1]).write_text(
                "# permissive mirror\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertIn(
                "bootstrap transition mirror must equal the trust anchor",
                errors,
            )

    def test_bootstrap_rejects_unpinned_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            workflow = current / PROTECTED[0]
            value = json.loads(workflow.read_text(encoding="utf-8"))
            value["jobs"]["trusted-revision"]["steps"][0]["with"]["ref"] = "main"
            workflow.write_text(
                json.dumps(value, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertIn(
                "bootstrap trusted workflow structure is not exact",
                errors,
            )

    def test_bootstrap_rejects_comment_only_noop_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            workflow = current / PROTECTED[0]
            workflow.write_text(
                json.dumps(
                    {
                        "jobs": {
                            "noop": {
                                "runs-on": "ubuntu-latest",
                                "steps": [{"run": "true"}],
                            }
                        },
                        "name": "Modbus Trusted Revision",
                        "on": {"push": {}},
                        "_comments": trust_validator.expected_workflow(ANCHOR_SHA),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertIn(
                "bootstrap trusted workflow structure is not exact",
                errors,
            )

    def test_two_pr_validator_weakening_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = self.materialize(root / "prior")
            current = self.materialize(root / "current")
            validator = current / PROTECTED[1]
            validator.write_text(
                validator.read_text(encoding="utf-8")
                + "\n# weakened in intermediate PR\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertTrue(
                any("protected path is immutable" in error for error in errors)
            )

    def test_two_pr_workflow_repin_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = self.materialize(root / "prior")
            current = self.materialize(root / "current")
            workflow = current / PROTECTED[0]
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    "validate_modbus_docs_trust.py",
                    "weakened_validator.py",
                ),
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertTrue(
                any("protected path is immutable" in error for error in errors)
            )

    def test_two_pr_semantic_validator_weakening_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = self.materialize(root / "prior")
            current = self.materialize(root / "current")
            validator = current / PROTECTED[2]
            validator.write_text("# permissive semantic validator\n")
            errors = self.run_validator(prior, current)
            self.assertTrue(
                any("protected path is immutable" in error for error in errors)
            )

    def test_revision_bump_cannot_mutate_frozen_v1_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = self.materialize(root / "prior")
            current = self.materialize(root / "current")
            manifest_path = current / MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["content_revision"] = 2
            manifest["consumer_pin"]["content_revision"] = 2
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertIn(
                "current manifest is not the independently frozen V1 contract",
                errors,
            )

    def test_manifest_anchor_must_match_executing_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            manifest_path = current / MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["trust_anchor"]["commit_sha"] = "d" * 40
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertIn(
                "current manifest trust anchor does not match the executing "
                "anchor",
                errors,
            )

    def test_semantic_manifest_change_requires_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = self.materialize(root / "prior")
            current = self.materialize(root / "current")
            manifest_path = current / MANIFEST
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["source_policy"]["restricted_source_copy"] = "allowed"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertTrue(
                any("require exactly the next" in error for error in errors)
            )


if __name__ == "__main__":
    unittest.main()
