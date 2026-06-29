import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts import supply_chain_proof as proof


class SupplyChainProofTests(unittest.TestCase):
    def test_current_workflow_is_pinned_and_least_privilege(self):
        result = proof.validate_workflows()

        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["findings"], [])
        actions = [
            action
            for workflow in result["workflows"]
            for action in workflow["actions"]
            if action["pin_status"] == "pinned-sha"
        ]
        self.assertGreaterEqual(len(actions), 2)

    def test_unpinned_action_fails(self):
        with TemporaryDirectory() as tmpdir:
            workflow = Path(tmpdir) / "bad.yml"
            workflow.write_text(
                "name: bad\n"
                "on: push\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v4\n",
                encoding="utf-8",
            )

            result = proof.validate_workflow(workflow)

            self.assertEqual(result["result"], "FAIL")
            self.assertIn("not pinned", result["findings"][0])

    def test_pinned_official_subaction_passes(self):
        with TemporaryDirectory() as tmpdir:
            workflow = Path(tmpdir) / "codeql.yml"
            workflow.write_text(
                "name: codeql\n"
                "on: push\n"
                "permissions:\n"
                "  contents: read\n"
                "  security-events: write\n"
                "jobs:\n"
                "  analyze:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: github/codeql-action/init@411bbbe57033eedfc1a82d68c01345aa96c737d7\n"
                "      - uses: github/codeql-action/analyze@411bbbe57033eedfc1a82d68c01345aa96c737d7\n",
                encoding="utf-8",
            )

            result = proof.validate_workflow(workflow)

            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["findings"], [])

    def test_pull_request_target_fails(self):
        with TemporaryDirectory() as tmpdir:
            workflow = Path(tmpdir) / "bad.yml"
            workflow.write_text(
                "name: bad\n"
                "on:\n"
                "  pull_request_target:\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs: {}\n",
                encoding="utf-8",
            )

            result = proof.validate_workflow(workflow)

            self.assertEqual(result["result"], "FAIL")
            self.assertIn("pull_request_target is forbidden", result["findings"][0])

    def test_build_outputs_produces_worker_result_and_sbom(self):
        with TemporaryDirectory() as tmpdir:
            result, sbom = proof.build_outputs(Path(tmpdir))

            self.assertEqual(result["result"], "PASS")
            self.assertEqual(result["record_type"], "supply_chain_result")
            self.assertFalse(result["reusable_for_product"])
            self.assertTrue(result["reusable_for_public_repo_release"])
            self.assertEqual(sbom["spdxVersion"], "SPDX-2.3")
            json.dumps(result)
            json.dumps(sbom)

    def test_source_inventory_excludes_tmp_runtime_artifacts(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".tmp" / "factory-runs").mkdir(parents=True)
            (root / ".tmp" / "factory-runs" / "transient.json").write_text("{}", encoding="utf-8")
            (root / "public.txt").write_text("public\n", encoding="utf-8")

            with mock.patch.object(proof, "ROOT", root):
                refs = [proof.repo_ref(path) for path in proof.iter_repo_files()]

        self.assertEqual(refs, ["public.txt"])

    def test_source_inventory_tolerates_missing_root(self):
        with TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "already-gone"

        with mock.patch.object(proof, "ROOT", missing):
            self.assertEqual(proof.iter_repo_files(), [])

    def test_dependency_manifest_requires_followup(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")

            with mock.patch.object(proof, "ROOT", root):
                posture = proof.dependency_posture()

        self.assertTrue(posture["requires_followup"])
        self.assertEqual(posture["detected_manifests"], ["requirements.txt"])

    def test_docs_optional_dependency_does_not_count_as_runtime_dependency(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                "[project]\n"
                'name = "fixture"\n'
                "[project.optional-dependencies]\n"
                'docs = ["mkdocs>=1.6,<2"]\n',
                encoding="utf-8",
            )

            with mock.patch.object(proof, "ROOT", root):
                posture = proof.dependency_posture()

        self.assertFalse(posture["requires_followup"])
        self.assertEqual(posture["detected_manifests"], ["pyproject.toml"])

    def test_runtime_optional_dependency_requires_followup(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pyproject.toml").write_text(
                "[project]\n"
                'name = "fixture"\n'
                "[project.optional-dependencies]\n"
                'postgres = ["psycopg[binary]>=3"]\n',
                encoding="utf-8",
            )

            with mock.patch.object(proof, "ROOT", root):
                posture = proof.dependency_posture()

        self.assertTrue(posture["requires_followup"])
        self.assertEqual(posture["detected_manifests"], ["pyproject.toml"])

    def test_no_dependency_manifest_is_current_public_pass(self):
        with mock.patch.object(proof, "ROOT", Path(__file__).resolve().parents[1]):
            posture = proof.dependency_posture()

        self.assertFalse(posture["requires_followup"])


if __name__ == "__main__":
    unittest.main()
