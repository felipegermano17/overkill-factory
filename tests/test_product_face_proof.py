from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "product_face_proof.py"
SPEC = importlib.util.spec_from_file_location("product_face_proof", MODULE_PATH)
assert SPEC is not None
product_face_proof = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["product_face_proof"] = product_face_proof
SPEC.loader.exec_module(product_face_proof)

FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl", ROOT / "scripts" / "factoryctl.py")
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)


def reference_dimension_basis() -> dict[str, str]:
    return {
        dimension: f"Unit proof compares {dimension} against selected professional references."
        for dimension in product_face_proof.REFERENCE_COMPARISON_DIMENSIONS
    }


def valid_driver() -> dict:
    return {
        "$schema": "https://overkill-factory.dev/schemas/product-face-state-journey-driver.schema.json",
        "record_type": "product_face_state_journey_driver",
        "target_binding": {"target_ref": "external:unit-target"},
        "timeout_ms": 1000,
        "public_artifact_policy": {
            "no_private_screenshots_in_repo": True,
            "no_secrets_in_values": True,
            "proof_output_location": ".tmp/factory-runs/product-face",
        },
        "journeys": [
            {
                "journey_id": "login-success",
                "name": "login success",
                "state": "success",
                "required_for_pass": True,
                "data_condition": "public fixture user",
                "state_setup": [{"action": "wait_for_selector", "selector": "#email"}],
                "steps": [
                    {"action": "fill", "selector": "#email", "value": "operator@example.com"},
                    {"action": "click", "selector": "#submit"},
                    {"action": "assert_text", "selector": "#status", "text": "Ready"},
                    {"action": "screenshot", "full_page": True},
                ],
            }
        ],
    }


class FakeLocator:
    def __init__(self, page: "FakeDriverPage", selector: str) -> None:
        self.page = page
        self.selector = selector

    def click(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.page.calls.append(("click", self.selector))

    def fill(self, value: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.page.calls.append(("fill", self.selector, value))

    def text_content(self, **kwargs) -> str:  # type: ignore[no-untyped-def]
        return self.page.text_by_selector.get(self.selector, "")


class FakeDriverPage:
    def __init__(self, *, fail_selectors: set[str] | None = None) -> None:
        self.calls: list[tuple] = []
        self.fail_selectors = fail_selectors or set()
        self.text_by_selector = {"#status": "Ready"}

    def locator(self, selector: str) -> FakeLocator:
        return FakeLocator(self, selector)

    def wait_for_selector(self, selector: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.calls.append(("wait_for_selector", selector))
        if selector in self.fail_selectors:
            raise TimeoutError(f"missing selector {selector}")

    def wait_for_timeout(self, ms: int) -> None:
        self.calls.append(("wait", ms))

    def goto(self, url: str, **kwargs) -> None:  # type: ignore[no-untyped-def]
        self.calls.append(("goto", url))

    def screenshot(self, *, path: str, full_page: bool = True) -> None:
        self.calls.append(("screenshot", path, full_page))
        Path(path).write_bytes(b"fake-png")


class ProductFaceProofTest(unittest.TestCase):
    def test_public_product_face_result_template_validates_semantically(self) -> None:
        result = json.loads((ROOT / "templates" / "product-face-result.json").read_text(encoding="utf-8"))

        errors = factoryctl.validate_product_face_result(result)

        self.assertEqual(errors, [])
        self.assertEqual(result["record_type"], "product_face_result")
        self.assertFalse(result["reusable_for_product"])
        self.assertTrue(result["product_acceptance_boundary"]["cannot_satisfy_product_acceptance"])

    def test_parse_viewport_accepts_named_size(self) -> None:
        viewport = product_face_proof.parse_viewport("tablet=768x1024")

        self.assertEqual(viewport.name, "tablet")
        self.assertEqual(viewport.width, 768)
        self.assertEqual(viewport.height, 1024)
        self.assertEqual(viewport.label, "tablet 768x1024")

    def test_launch_chromium_falls_back_to_system_chrome_channel(self) -> None:
        class FakeBrowserType:
            def __init__(self) -> None:
                self.calls: list[dict[str, str]] = []

            def launch(self, **kwargs):  # type: ignore[no-untyped-def]
                self.calls.append(kwargs)
                if not kwargs:
                    raise RuntimeError("bundled browser missing")
                return "browser"

        fake = FakeBrowserType()

        self.assertEqual(product_face_proof.launch_chromium_browser(fake), "browser")
        self.assertEqual(fake.calls, [{}, {"channel": "chrome"}])

    def test_forced_fallback_writes_compatible_honest_result(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "prototype.html"
            html_path.write_text(
                "<!doctype html><html lang='en'><head><title>Proof</title></head>"
                "<body><main><h1>Proof</h1><button aria-label='Save' disabled>Save</button></main></body></html>",
                encoding="utf-8",
            )
            out_path = tmp_path / "proof" / "product-face-result.json"

            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=out_path,
                force_fallback=True,
            )

            written = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result["record_type"], "product_face_result")
        self.assertEqual(written["result"], "WAIVED")
        self.assertTrue(written["blocking_findings"])
        self.assertIn("not-captured", written["screenshots"][0])
        self.assertEqual(written["a11y"]["status"], "fail")
        self.assertEqual(written["overlap_check"]["status"], "fail")
        self.assertIn("waiver", written)
        self.assertTrue(written["waiver"]["compensating_controls"])
        self.assertTrue(written["evidence_refs"])
        serialized = json.dumps(written)
        self.assertNotIn("C:\\Users", serialized)
        self.assertNotIn("OneDrive", serialized)

    def test_forced_fallback_matches_factory_product_face_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            html_path = Path(tmp) / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")
            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=Path(tmp) / "result.json",
                force_fallback=True,
            )

        required = {
            "result",
            "tool_or_profile",
            "executed_by",
            "screenshots",
            "viewports",
            "checked_states",
            "user_journeys_checked",
            "usage_evidence_matrix",
            "a11y",
            "overlap_check",
            "performance_note",
            "packet_comparison",
            "source_promise_coverage",
            "design_fit_review",
            "professional_design_process_ref",
            "professional_design_process_comparison",
            "reference_quality_comparison",
            "visual_quality_result",
            "blocking_findings",
            "evidence_refs",
            "next_action",
        }
        self.assertLessEqual(required, set(result))
        self.assertIn(result["result"], {"PASS", "WAIVED"})
        for field in ("screenshots", "viewports", "checked_states", "user_journeys_checked", "evidence_refs"):
            self.assertTrue(result[field])
        self.assertTrue(result["usage_evidence_matrix"])
        first_matrix_entry = result["usage_evidence_matrix"][0]
        for field in ("journey", "state", "viewport", "data_condition", "evidence_refs", "a11y_status", "performance_status"):
            self.assertIn(field, first_matrix_entry)
        self.assertTrue(result["a11y"])
        self.assertTrue(result["overlap_check"])
        self.assertIn(result["visual_quality_result"]["status"], {"BLOCK", "PASS", "PASS_WITH_RESIDUALS"})

    def test_card_binding_and_factory_alias_fields_are_present(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")
            card_path = tmp_path / "card.md"
            card_path.write_text(
                "```json\n"
                + json.dumps(
                    {
                        "card_id": "CARD-001",
                        "slice_id": "SLICE-001",
                        "phase": "F13",
                        "risk_effective": "R2",
                        "surfaces": ["frontend"],
                        "executor_identity": "executor",
                        "reviewer_identity": "reviewer",
                    }
                )
                + "\n```\n",
                encoding="utf-8",
            )

            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=tmp_path / "result.json",
                force_fallback=True,
                card=card_path,
            )

        self.assertEqual(result["card_ref"]["card_id"], "CARD-001")
        self.assertEqual(result["card_ref"]["slice_id"], "SLICE-001")
        self.assertEqual(result["surface_evidence_profile"]["profile_id"], "web_visual_ui")
        self.assertEqual(result["surface_evidence_profiles"][0]["profile_id"], "web_visual_ui")
        self.assertEqual(result["journeys"], result["user_journeys_checked"])
        self.assertEqual(result["accessibility"], result["a11y"])
        self.assertEqual(result["overlap"], result["overlap_check"])
        self.assertEqual(result["evidence_kind"], "real")
        self.assertFalse(result["reusable_for_product"])

    def test_browser_capture_scope_does_not_claim_uncaptured_declared_states(self) -> None:
        scope = product_face_proof.browser_capture_scope(
            states=["initial-render", "loading", "error"],
            journeys=["open target", "checkout happy path"],
        )

        self.assertEqual(scope["declared_states"], ["initial-render", "loading", "error"])
        self.assertEqual(scope["captured_states"], ["initial-render"])
        self.assertEqual(scope["uncaptured_states"], ["loading", "error"])
        self.assertEqual(scope["captured_journeys"], ["open target"])
        self.assertEqual(scope["uncaptured_journeys"], ["checkout happy path"])

    def test_capture_scope_turns_declared_overclaim_into_waived_result(self) -> None:
        scope = product_face_proof.browser_capture_scope(
            states=["loading", "success"],
            journeys=["purchase flow"],
        )
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=scope["captured_states"],
            journeys=scope["captured_journeys"],
            tool_or_profile="unit-test",
        )

        product_face_proof.apply_capture_scope(result, scope)

        self.assertEqual(result["result"], "WAIVED")
        self.assertTrue(result["blocking_findings"])
        self.assertEqual(result["checked_states"], ["initial-render"])
        self.assertEqual(result["user_journeys_checked"], ["open target"])
        self.assertEqual(result["uncaptured_states"], ["loading", "success"])
        self.assertEqual(result["uncaptured_journeys"], ["purchase flow"])
        self.assertIn("state/journey drivers", result["next_action"])

    def test_state_journey_driver_executes_valid_journey(self) -> None:
        driver = valid_driver()
        product_face_proof.validate_state_journey_driver(driver)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            executions, screenshots = product_face_proof.execute_state_journey_driver(
                page=FakeDriverPage(),
                driver=driver,
                viewport=product_face_proof.Viewport("desktop", 1440, 900),
                screenshot_dir=Path(tmp),
            )

        scope = product_face_proof.driver_capture_scope(
            states=[],
            journeys=[],
            driver=driver,
            executions=executions,
        )

        self.assertEqual(executions[0]["status"], "PASS")
        self.assertEqual(scope["captured_states"], ["success"])
        self.assertEqual(scope["captured_journeys"], ["login success"])
        self.assertTrue(screenshots)

    def test_state_journey_driver_rejects_missing_selector_action(self) -> None:
        driver = valid_driver()
        driver["journeys"][0]["steps"][1] = {"action": "click"}

        with self.assertRaisesRegex(ValueError, "selector is required"):
            product_face_proof.validate_state_journey_driver(driver)

    def test_state_journey_driver_failure_blocks_capture(self) -> None:
        driver = valid_driver()
        driver["journeys"][0]["steps"][2] = {"action": "assert_visible", "selector": "#never"}
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            executions, _ = product_face_proof.execute_state_journey_driver(
                page=FakeDriverPage(fail_selectors={"#never"}),
                driver=driver,
                viewport=product_face_proof.Viewport("desktop", 1440, 900),
                screenshot_dir=Path(tmp),
            )

        scope = product_face_proof.driver_capture_scope(
            states=["success"],
            journeys=["login success"],
            driver=driver,
            executions=executions,
        )
        result = product_face_proof.base_result(
            target_ref="external:unit-target",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=scope["captured_states"],
            journeys=scope["captured_journeys"],
            tool_or_profile="unit-test",
        )
        result["state_journey_driver"] = {
            "driver_ref": "templates/product-face-state-journey-driver.json",
            "status": "FAIL",
            "execution_ref": "external:driver-execution",
            "journeys_executed": scope["captured_journeys"],
            "states_executed": scope["captured_states"],
        }

        product_face_proof.apply_capture_scope(result, scope)

        self.assertEqual(executions[0]["status"], "FAIL")
        self.assertEqual(result["result"], "WAIVED")
        self.assertTrue(result["blocking_findings"])

    def test_state_journey_driver_state_setup_failure_blocks_capture(self) -> None:
        driver = valid_driver()
        driver["journeys"][0]["state_setup"] = [{"action": "wait_for_selector", "selector": "#missing-setup"}]
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            executions, _ = product_face_proof.execute_state_journey_driver(
                page=FakeDriverPage(fail_selectors={"#missing-setup"}),
                driver=driver,
                viewport=product_face_proof.Viewport("desktop", 1440, 900),
                screenshot_dir=Path(tmp),
            )

        self.assertEqual(executions[0]["status"], "FAIL")
        self.assertIn("missing-setup", executions[0]["failure"])

    def test_declared_driver_journey_cannot_pass_without_execution(self) -> None:
        driver = valid_driver()
        scope = product_face_proof.driver_capture_scope(
            states=["success"],
            journeys=["login success"],
            driver=driver,
            executions=[],
        )
        result = product_face_proof.base_result(
            target_ref="external:unit-target",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=[],
            journeys=[],
            tool_or_profile="unit-test",
        )

        product_face_proof.apply_capture_scope(result, scope)

        self.assertEqual(result["result"], "WAIVED")
        self.assertEqual(result["uncaptured_states"], ["success"])
        self.assertEqual(result["uncaptured_journeys"], ["login success"])
        self.assertEqual(product_face_proof.state_journey_driver_status([], scope), "FAIL")

    def test_visual_artifacts_are_emitted_only_for_captured_states(self) -> None:
        scope = product_face_proof.browser_capture_scope(
            states=["initial-render", "loading"],
            journeys=["open target"],
        )

        artifacts = product_face_proof.build_visual_artifacts(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=scope["captured_states"],
            screenshot_refs=["external:desktop-proof.png"],
            captured_at="2026-06-16T00:00:00+00:00",
        )

        self.assertEqual([artifact["state"] for artifact in artifacts], ["initial-render"])

    def test_reusable_for_product_requires_pass_result(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            html_path = Path(tmp) / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "requires a PASS result"):
                product_face_proof.build_product_face_proof(
                    target=str(html_path),
                    out=Path(tmp) / "result.json",
                    force_fallback=True,
                    reusable_for_product=True,
                    product_id="qvg-public-validation-product",
                    environment_class="production-like-static-artifact",
                    approval_scope="Product Face lane for the QVG public validation product",
                )

    def test_reusable_for_product_scope_adds_target_hash(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            html_path = Path(tmp) / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")
            expected_sha256 = product_face_proof.sha256_file(html_path)
            result = product_face_proof.base_result(
                target_ref=product_face_proof.repo_ref(html_path),
                viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
                states=["initial-render"],
                journeys=["open target"],
                tool_or_profile="unit-test",
            )
            product_face_proof.apply_product_alignment(
                result=result,
                packet_ref="templates/product-face-packet.json",
                packet_comparison_basis="Unit proof is explicitly matched to the packet.",
                source_promise_coverage_basis="Unit proof covers the named product promise.",
                design_fit_review_basis="Unit proof includes an explicit design-fit review.",
                professional_design_process_ref="templates/professional-design-process.json",
                professional_design_process_comparison_basis="Unit proof satisfies the professional design process gates.",
                reference_quality_ref="templates/professional-design-process.json#reference_research",
                reference_quality_comparison_basis="Unit proof compares against selected professional design references.",
                compared_reference_ids=[
                    "21st-dev-components",
                    "mobbin-workflow-patterns",
                    "pageflows-review-approval",
                ],
                reference_quality_dimensions=reference_dimension_basis(),
                reference_comparison_artifacts=[
                    {
                        "artifact_ref": "external:unit-reference-comparison",
                        "artifact_type": "side_by_side_capture",
                        "compared_source_ids": [
                            "21st-dev-components",
                            "mobbin-workflow-patterns",
                            "pageflows-review-approval",
                        ],
                        "basis": "Unit fixture supplies a bounded material comparison artifact.",
                        "bounded_acceptance": True,
                        "sanitized": True,
                    }
                ],
            )
            product_face_proof.apply_visual_quality_review(
                result=result,
                status="PASS",
                reviewer="product-face-reviewer",
                basis="Unit proof meets the reference quality bar for this bounded fixture.",
            )

            product_face_proof.apply_product_reuse_scope(
                result=result,
                target_ref=product_face_proof.repo_ref(html_path),
                target_path=html_path,
                product_id="qvg-public-validation-product",
                environment_class="production-like-static-artifact",
                approval_scope="Product Face lane for the QVG public validation product",
            )

        self.assertTrue(result["reusable_for_product"])
        self.assertEqual(result["product_target"]["product_id"], "qvg-public-validation-product")
        self.assertEqual(result["product_target"]["environment_class"], "production-like-static-artifact")
        self.assertEqual(result["product_target"]["target_sha256"], expected_sha256)
        self.assertIn("Product Face lane", result["product_target"]["approval_scope"])

    def test_product_alignment_requires_reference_comparison_artifact(self) -> None:
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=["initial-render"],
            journeys=["open target"],
            tool_or_profile="unit-test",
        )

        with self.assertRaisesRegex(ValueError, "reference_comparison_artifacts"):
            product_face_proof.apply_product_alignment(
                result=result,
                packet_ref="templates/product-face-packet.json",
                packet_comparison_basis="Unit proof is explicitly matched to the packet.",
                source_promise_coverage_basis="Unit proof covers the named product promise.",
                design_fit_review_basis="Unit proof includes an explicit design-fit review.",
                professional_design_process_ref="templates/professional-design-process.json",
                professional_design_process_comparison_basis="Unit proof satisfies the professional design process gates.",
                reference_quality_ref="templates/professional-design-process.json#reference_research",
                reference_quality_comparison_basis="Unit proof compares against selected professional design references.",
                compared_reference_ids=[
                    "21st-dev-components",
                    "mobbin-workflow-patterns",
                    "pageflows-review-approval",
                ],
                reference_quality_dimensions=reference_dimension_basis(),
            )

    def test_visual_quality_residual_parser_requires_bounded_structured_input(self) -> None:
        residual = product_face_proof.parse_visual_quality_residual(
            "residual-minor-spacing|low|product-face-reviewer|2099-01-01T00:00:00+00:00|"
            "Accepted only for this bounded Product Face validation|external:residual-proof|"
            "Minor spacing variance remains after review."
        )

        self.assertEqual(residual["id"], "residual-minor-spacing")
        self.assertEqual(residual["severity"], "low")
        self.assertFalse(residual["blocks_full_acceptance"])
        self.assertEqual(residual["proof_refs"], ["external:residual-proof"])

    def test_visual_quality_review_rejects_unstructured_residuals(self) -> None:
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=["initial-render"],
            journeys=["open target"],
            tool_or_profile="unit-test",
        )

        with self.assertRaisesRegex(ValueError, "bounded-visual-quality-residual"):
            product_face_proof.apply_visual_quality_review(
                result=result,
                status="PASS_WITH_RESIDUALS",
                reviewer="product-face-reviewer",
                basis="Residual is accepted.",
                residuals=["minor issue"],  # type: ignore[list-item]
            )

    def test_visual_quality_review_accepts_bounded_structured_residuals(self) -> None:
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=["initial-render"],
            journeys=["open target"],
            tool_or_profile="unit-test",
        )
        residual = product_face_proof.parse_visual_quality_residual(
            "residual-minor-spacing|medium|product-face-reviewer|2099-01-01T00:00:00+00:00|"
            "Accepted only for this bounded Product Face validation|external:residual-proof|"
            "Minor non-blocking performance variance remains after review."
        )

        product_face_proof.apply_visual_quality_review(
            result=result,
            status="PASS_WITH_RESIDUALS",
            reviewer="product-face-reviewer",
            basis="Residual is bounded, owned and expires.",
            residuals=[residual],
        )

        self.assertTrue(product_face_proof.visual_quality_passes(result))
        self.assertEqual(result["visual_quality_result"]["residuals"], [residual])

    def test_reusable_for_product_requires_packet_alignment(self) -> None:
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=["initial-render"],
            journeys=["open target"],
            tool_or_profile="unit-test",
        )

        with self.assertRaisesRegex(ValueError, "requires Product Face alignment"):
            product_face_proof.apply_product_reuse_scope(
                result=result,
                target_ref=result["target"],
                target_path=ROOT / "pilots" / "quasar-vault-guard-test" / "product-face" / "prototype.html",
                product_id="qvg-public-validation-product",
                environment_class="production-like-static-artifact",
                approval_scope="Product Face lane for the QVG public validation product",
            )

    def test_reusable_for_product_requires_scope_metadata(self) -> None:
        result = product_face_proof.base_result(
            target_ref="examples/minimal-hermes-project",
            viewports=[product_face_proof.Viewport("desktop", 1440, 900)],
            states=["initial-render"],
            journeys=["open target"],
            tool_or_profile="unit-test",
        )

        with self.assertRaisesRegex(ValueError, "requires --product-id"):
            product_face_proof.apply_product_reuse_scope(
                result=result,
                target_ref=result["target"],
                target_path=ROOT / "pilots" / "quasar-vault-guard-test" / "product-face" / "prototype.html",
                product_id=None,
                environment_class="production-like-static-artifact",
                approval_scope="Product Face lane for the QVG public validation product",
            )


if __name__ == "__main__":
    unittest.main()
