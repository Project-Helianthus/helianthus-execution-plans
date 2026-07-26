from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_modbus_docs_trust.py"
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
            content = (
                "python3 anchor/scripts/validate_modbus_docs_trust.py\n"
                if relative == PROTECTED[0]
                else f"{relative.as_posix()} fixture\n"
            )
            target.write_text(content, encoding="utf-8")
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
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(VALIDATOR),
                "--prior-root",
                str(prior),
                "--current-root",
                str(current),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_bootstrap_introduction_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            prior = root / "prior"
            prior.mkdir()
            current = self.materialize(root / "current")
            result = self.run_validator(prior, current)
            self.assertEqual(result.returncode, 0, result.stderr)

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
            result = self.run_validator(prior, current)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("protected path is immutable", result.stderr)

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
            result = self.run_validator(prior, current)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("protected path is immutable", result.stderr)

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
            result = self.run_validator(prior, current)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("require exactly the next", result.stderr)


if __name__ == "__main__":
    unittest.main()
