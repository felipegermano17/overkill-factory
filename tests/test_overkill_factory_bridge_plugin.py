from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "plugins" / "overkill-factory-bridge"


def load_plugin_hook():
    hook_path = PLUGIN_ROOT / "hooks" / "overkill_factory_bridge_hook.py"
    spec = importlib.util.spec_from_file_location("overkill_factory_bridge_plugin_hook", hook_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with patch.dict(os.environ, {"PLUGIN_ROOT": str(PLUGIN_ROOT)}):
        sys.modules["overkill_factory_bridge_plugin_hook"] = module
        spec.loader.exec_module(module)
    return module


class OverkillFactoryBridgePluginTest(unittest.TestCase):
    def test_plugin_manifest_and_marketplace_are_repo_local(self) -> None:
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "overkill-factory-bridge")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("hooks", manifest)
        self.assertEqual(marketplace["name"], "overkill-factory")
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"],
            "./plugins/overkill-factory-bridge",
        )

    def test_plugin_packages_skill_reference_hooks_and_scripts(self) -> None:
        skill = PLUGIN_ROOT / "skills" / "overkill-factory-bridge" / "SKILL.md"
        reference = PLUGIN_ROOT / "skills" / "overkill-factory-bridge" / "references" / "overkill-factory-bridge.md"
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))

        self.assertTrue(skill.is_file())
        self.assertTrue(reference.is_file())
        self.assertTrue((PLUGIN_ROOT / "scripts" / "factory_bridge.py").is_file())
        self.assertIn("SessionStart", hooks["hooks"])
        self.assertIn("UserPromptSubmit", hooks["hooks"])
        self.assertIn("${PLUGIN_ROOT}", json.dumps(hooks))
        self.assertIn("do not approve human gates", (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("factory_bridge_start_request", skill.read_text(encoding="utf-8"))
        self.assertIn("overkill-factory-gerente", reference.read_text(encoding="utf-8"))
        self.assertIn("The bridge does not create Hermes boards or cards", reference.read_text(encoding="utf-8"))

    def test_plugin_hook_resolves_workspace_inbox_without_git_shell_dependency(self) -> None:
        hook = load_plugin_hook()
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / ".tmp").mkdir()

            inbox = hook.default_inbox_dir({"cwd": str(workspace)})

        self.assertEqual(inbox, workspace / ".tmp" / "factory-runs" / "operator-inbox")

    def test_plugin_hook_resolves_single_child_factory_inbox_from_parent_workspace(self) -> None:
        hook = load_plugin_hook()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            factory = parent / "overkill-factory-checkout"
            marketplace = factory / ".agents" / "plugins"
            inbox = factory / ".tmp" / "factory-runs" / "operator-inbox"
            marketplace.mkdir(parents=True)
            inbox.mkdir(parents=True)
            (marketplace / "marketplace.json").write_text(
                json.dumps({"name": "overkill-factory", "plugins": []}),
                encoding="utf-8",
            )
            (inbox / "pending.jsonl").write_text("", encoding="utf-8")

            resolved = hook.default_inbox_dir({"cwd": str(parent)})

        self.assertEqual(resolved, inbox)

    def test_plugin_hook_honors_explicit_factory_root(self) -> None:
        hook = load_plugin_hook()
        with tempfile.TemporaryDirectory() as tmp:
            factory = Path(tmp) / "factory"
            with patch.dict(os.environ, {"OVERKILL_FACTORY_ROOT": str(factory)}):
                resolved = hook.default_inbox_dir({"cwd": str(Path(tmp) / "elsewhere")})

        self.assertEqual(resolved, factory / ".tmp" / "factory-runs" / "operator-inbox")

    def test_plugin_bridge_classifies_status_prompt_without_factory_authority(self) -> None:
        hook = load_plugin_hook()
        bridge = hook.load_bridge()
        with tempfile.TemporaryDirectory() as tmp:
            response = bridge.codex_hook_response(
                {"hook_event_name": "UserPromptSubmit", "prompt": "status da fabrica"},
                inbox_dir=Path(tmp) / "inbox",
            )

        context = response["hookSpecificOutput"]["additionalContext"]
        self.assertIn("status_bridge", context)
        self.assertIn("explicit factory runtime target", context)
        self.assertIn("ambient/default Hermes store", context)
        self.assertIn("must not close gates, execute factory work or auto-approve human gates", context)
        self.assertIn("factory_bridge_start_request", context)
        self.assertIn("the bridge must not create Hermes boards or cards", context)

    def test_plugin_bridge_new_project_contract_is_gateway_handoff_only(self) -> None:
        hook = load_plugin_hook()
        bridge = hook.load_bridge()

        start = bridge.build_start_request(
            run_id="plugin-run",
            operator_goal="Start a new product project.",
            project_mode="new_project",
            source_envelope_ref="external:operator:source-envelope",
        )

        self.assertEqual(start["handoff_to_factory"]["gateway_profile"], "overkill-factory-gerente")
        self.assertEqual(start["handoff_to_factory"]["orchestrator_worker"], "factory-orchestrator")
        self.assertTrue(start["bridge_limits"]["bridge_must_not_create_hermes_board"])
        self.assertTrue(start["bridge_limits"]["bridge_must_not_create_hermes_cards"])
        self.assertEqual(start["target_board_policy"]["policy"], "factory_must_create_new_board")


if __name__ == "__main__":
    unittest.main()
