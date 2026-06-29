from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class CliPublicStdoutHygieneTests(unittest.TestCase):
    def assert_no_private_path(self, text: str, private_path: Path | None = None) -> None:
        if private_path is not None:
            self.assertNotIn(str(private_path), text)
            self.assertNotIn(str(private_path).replace("\\", "/"), text)
        self.assertNotIn("C:\\Users", text)
        self.assertNotIn("OneDrive", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("/home/", text)
        self.assertNotIn("/srv/", text)
        self.assertNotIn("/tmp/", text)

    def test_write_helpers_print_public_refs_for_external_outputs(self) -> None:
        factoryctl = load_script("factoryctl")
        self_improvement = load_script("factory_self_improvement")
        bridge = load_script("factory_concierge_discord_bridge")

        with tempfile.TemporaryDirectory() as tmp:
            private_out = Path(tmp) / "private-output.json"
            for module in (factoryctl, self_improvement, bridge):
                with self.subTest(module=module.__name__):
                    stdout = io.StringIO()
                    with contextlib.redirect_stdout(stdout):
                        module.write_json(private_out, {"result": "PASS"})

                    printed = stdout.getvalue()
                    self.assertIn("Wrote external:private-output.json", printed)
                    self.assert_no_private_path(printed, private_out)

    def test_factory_battery_summary_uses_public_output_ref(self) -> None:
        battery = load_script("factory_battery")
        readonly = load_script("control_tower_readonly_smoke")
        approval = load_script("control_tower_approval_registration_smoke")

        with tempfile.TemporaryDirectory() as tmp:
            private_out = Path(tmp) / "battery.json"

            self.assertEqual(battery.public_path_ref(private_out), "external:battery.json")
            self.assertEqual(readonly.public_path_ref(private_out), "external:battery.json")
            self.assertEqual(approval.public_path_ref(private_out), "external:battery.json")

    def test_factoryctl_init_error_uses_public_workspace_ref(self) -> None:
        factoryctl = load_script("factoryctl")

        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "operator-workspace"
            workspace.mkdir()
            (workspace / "already-here.txt").write_text("busy", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                exit_code = factoryctl.main_with_args_for_test(
                    ["init", "--out", str(workspace), "--project-name", "private-product"]
                )

            printed = stderr.getvalue()
            self.assertEqual(exit_code, 1)
            self.assertIn("external:operator-workspace is not empty", printed)
            self.assert_no_private_path(printed, workspace)

    def test_quasar_missing_inputs_use_public_refs(self) -> None:
        container = load_script("quasar_product_like_container_proof")
        svm = load_script("qvg_quasar_cu_svm_economic_proof")
        fuzz = load_script("qvg_quasar_cu_fuzz_property_proof")

        with tempfile.TemporaryDirectory() as tmp:
            missing_source = Path(tmp) / "missing-source"
            missing_runtime = Path(tmp) / "missing-runtime.json"
            existing_source = Path(tmp) / "src"
            existing_source.mkdir()

            for module, argv, expected in (
                (container, ["--source-dir", str(missing_source)], "source dir does not exist: external:missing-source"),
                (svm, ["--source-dir", str(missing_source)], "source dir does not exist: external:missing-source"),
                (
                    fuzz,
                    ["--source-dir", str(existing_source), "--runtime-proof", str(missing_runtime)],
                    "runtime proof does not exist: external:missing-runtime.json",
                ),
            ):
                with self.subTest(module=module.__name__):
                    with self.assertRaises(SystemExit) as raised:
                        module.main(argv)
                    message = str(raised.exception)
                    self.assertIn(expected, message)
                    self.assert_no_private_path(message, missing_source)
                    self.assert_no_private_path(message, missing_runtime)

    def test_subprocess_tail_redactors_remove_private_paths(self) -> None:
        release_gate = load_script("production_release_gate")
        remote_probe = load_script("managed_remote_proof_probe")
        remote_smoke = load_script("remote_proof_smoke")
        whimsical = load_script("whimsical_mcp")

        drive_path = "C:" + "\\Users\\example\\Workspace\\file.txt"
        temp_path = "/" + "tmp" + "/workspace/file.txt"
        home_path = "/" + "home" + "/example/workspace.txt"
        service_path = "/" + "srv" + "/runtime/x"
        sample = f"{drive_path} {temp_path} {home_path} {service_path}"

        redacted_samples = [
            release_gate.redact_public_text(sample),
            remote_probe.redact(sample),
            remote_smoke.redact_output(sample),
            whimsical.redact(sample),
            whimsical.redact(sample, include_private_content=False),
        ]
        for redacted in redacted_samples:
            self.assert_no_private_path(str(redacted))

        self.assertEqual(whimsical.public_path_ref(Path("C:" + "\\Users\\example\\shot.png")), "external:shot.png")


if __name__ == "__main__":
    unittest.main()
