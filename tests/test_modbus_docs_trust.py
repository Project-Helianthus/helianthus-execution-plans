from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest

from scripts import validate_modbus_docs_trust as trust_validator


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_modbus_docs_trust.py"
ANCHOR_SHA = "c" * 40
MANIFEST = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
PROTECTED = (
    pathlib.Path(".github/workflows/modbus-trusted-revision.yml"),
    pathlib.Path("scripts/validate_modbus_revision_transition.py"),
)
ARTIFACTS = {
    "consumer_lock_schema": (
        "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json"
    ),
    "policy": "docs/platform/modbus-foundation-profile-contract-v1.md",
    "wire": "protocols/modbus/modbus-phase-one-wire-v1.md",
}


class ModbusDocsTrustTests(unittest.TestCase):
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
                    "pull_request_target:\n"
                    "repository: Project-Helianthus/helianthus-execution-plans\n"
                    f"ref: {ANCHOR_SHA}\n"
                    "python3 anchor/scripts/validate_modbus_docs_trust.py "
                    f"--trust-anchor-sha {ANCHOR_SHA}\n"
                    "ref: ${{ github.event.pull_request.base.sha }}\n"
                    "ref: ${{ github.event.pull_request.head.sha }}\n"
                    "persist-credentials: false\n",
                    encoding="utf-8",
                )
            else:
                target.write_bytes(VALIDATOR.read_bytes())
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
            "version": 1,
        }
        target = root / MANIFEST
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return root

    def run_validator(
        self,
        prior: pathlib.Path,
        current: pathlib.Path,
    ) -> list[str]:
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
            workflow.write_text(
                workflow.read_text(encoding="utf-8").replace(
                    f"ref: {ANCHOR_SHA}",
                    "ref: main",
                ),
                encoding="utf-8",
            )
            errors = self.run_validator(prior, current)
            self.assertTrue(
                any("bootstrap trusted workflow missing" in error for error in errors)
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
