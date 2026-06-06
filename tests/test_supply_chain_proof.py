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

    def test_dependency_manifest_requires_followup(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "requirements.txt").write_text("requests==2.32.0\n", encoding="utf-8")

            with mock.patch.object(proof, "ROOT", root):
                posture = proof.dependency_posture()

        self.assertTrue(posture["requires_followup"])
        self.assertEqual(posture["detected_manifests"], ["requirements.txt"])

    def test_no_dependency_manifest_is_current_public_pass(self):
        with mock.patch.object(proof, "ROOT", Path(__file__).resolve().parents[1]):
            posture = proof.dependency_posture()

        self.assertFalse(posture["requires_followup"])


if __name__ == "__main__":
    unittest.main()
