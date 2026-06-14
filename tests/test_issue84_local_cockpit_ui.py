from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_BUILDER_PATH = ROOT / "scripts" / "issue84" / "build_local_cockpit_data.py"
UI_DIR = ROOT / "ui" / "issue-84-local-cockpit"
FIXTURES = ROOT / "fixtures" / "issue-84" / "status-snapshot-v0"

REQUIRED_PACKET_STATES = {
    "loading_snapshot",
    "empty_no_snapshots",
    "success_current_snapshot",
    "input_error_or_parse_failure",
    "blocked_gate",
    "stale_snapshot",
    "contradictory_state",
    "private_evidence_unavailable",
    "review_pending_failed_passed",
    "long_dense_data",
}

REQUIRED_CURRENT_STATES = {
    "success",
    "empty",
    "loading",
    "error",
    "blocked",
    "stale",
    "missing",
    "contradictory",
    "private_unavailable",
    "superseded",
}

def private_marker_patterns() -> list[re.Pattern[str]]:
    runtime_root = "/" + "srv" + "/" + "hermes"
    product_marker = "K" + "AXIS"
    owner_marker = "Fel" + "ipe"
    windows_root = "C:" + "\\" + "Users"
    return [
        re.compile(re.escape(runtime_root)),
        re.compile(r"file://"),
        re.compile(r"\bt_[a-f0-9]{8}\b"),
        re.compile(r"\b" + re.escape(product_marker) + r"\b"),
        re.compile(r"\b" + re.escape(owner_marker) + r"\b"),
        re.compile(re.escape(windows_root)),
    ]


FORBIDDEN_PUBLIC_PATTERNS = private_marker_patterns()


def load_data_builder():
    spec = importlib.util.spec_from_file_location("issue84_build_local_cockpit_data", DATA_BUILDER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["issue84_build_local_cockpit_data"] = module
    spec.loader.exec_module(module)
    return module


def sample_product_face_packet(tmp_path: Path) -> Path:
    payload = {
        "record_type": "product_face_packet_result",
        "product_face_packet": {
            "surface": "local-first web cockpit",
            "mode": "greenfield planning packet for issue 84 only",
            "user": "Open-source operator supervising product-production work from local structured snapshots.",
            "job_to_be_done": "Understand phase, blockers, evidence refs and next safe action without private runtime.",
            "required_states": sorted(REQUIRED_PACKET_STATES),
            "device_or_viewport_scope": ["desktop_1440x900", "mobile_390x844"],
            "proof_required": ["desktop screenshot", "mobile screenshot", "console error check"],
            "design_direction": {
                "visual_tone": "serious, calm, exacting operations cockpit",
                "density": "high-density desktop; mobile triage-first cards",
                "interaction_style": "read-only inspection, drill-down, filter/search, timeline replay and evidence-ref expansion",
            },
        },
        "visual_quality_bar": {
            "must_have": [
                "visible source refs/provenance",
                "clear next safe action",
                "separate review/approval/done/release semantics",
            ],
            "must_not_have": [
                "decorative KPIs",
                "generic admin-dashboard labels",
                "fake data implying gates passed",
            ],
        },
        "anti_generic_ai_dashboard_criteria": [
            "Every visible metric/card must tie to a factory object, gate, worker, receipt, evidence ref or next safe action.",
            "No fake data that implies gates passed, evidence exists or issue completion.",
        ],
        "reference_quality_packet": {
            "accepted_reference_directions": [
                {"id": "AR01", "direction": "serious operations cockpit", "use": "compact hierarchy"}
            ],
            "rejected_reference_directions": [
                {"id": "RR01", "direction": "generic AI dashboard", "reason": "not product-specific"}
            ],
        },
    }
    path = tmp_path / "product-face-packet.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def sample_product_face_review(tmp_path: Path) -> Path:
    payload = {
        "record_type": "independent_review_result",
        "verdict": "PASS",
        "allowed_next_action": {
            "may_consume_product_face_packet": True,
            "consume_scope": "bounded local cockpit implementation only",
            "still_blocked": ["Product Face Result evidence", "release", "issue completion"],
        },
        "findings_summary": "Packet may be consumed for bounded implementation; this is not visual approval.",
    }
    path = tmp_path / "product-face-review.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class Issue84LocalCockpitUITest(unittest.TestCase):
    def test_builder_generates_public_safe_cockpit_data_from_fixtures_and_packet_summary(self) -> None:
        builder = load_data_builder()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = builder.build_cockpit_data(
                ROOT,
                product_face_packet_path=sample_product_face_packet(tmp_path),
                product_face_review_path=sample_product_face_review(tmp_path),
            )

        self.assertEqual(data["record_type"], "issue_84_local_cockpit_ui_data")
        self.assertTrue(data["policy"]["projection_only"])
        self.assertFalse(data["policy"]["product_face_result_self_acceptance"])
        self.assertIn("gate_approval", data["policy"]["forbidden_actions"])
        self.assertGreaterEqual(data["metrics"]["total_snapshots"], 18)
        self.assertEqual(data["metrics"]["adapter_report_projections"], 0)
        self.assertGreaterEqual(data["metrics"]["status_fixture_projections"], 18)
        self.assertTrue(REQUIRED_PACKET_STATES.issubset({item["id"] for item in data["state_registry"]}))
        self.assertTrue(REQUIRED_CURRENT_STATES.issubset(set(data["metrics"]["current_state_counts"])))
        self.assertIn("serious, calm", data["product_face"]["visual_tone"])
        self.assertEqual(data["product_face_review"]["verdict"], "PASS")
        self.assertFalse(data["product_face_review"]["is_product_face_result"])

        serialized = json.dumps(data, sort_keys=True)
        for pattern in FORBIDDEN_PUBLIC_PATTERNS:
            self.assertIsNone(pattern.search(serialized), pattern.pattern)

    def test_static_ui_uses_semantic_dom_local_data_and_text_only_rendering(self) -> None:
        html = (UI_DIR / "index.html").read_text(encoding="utf-8")
        script = (UI_DIR / "app.js").read_text(encoding="utf-8")
        styles = (UI_DIR / "styles.css").read_text(encoding="utf-8")

        self.assertIn("<main", html)
        self.assertIn("data-cockpit-root", html)
        self.assertIn("aria-live=\"polite\"", html)
        self.assertIn("data/status-cockpit.json", script)
        self.assertNotIn("innerHTML", script)
        self.assertIn("textContent", script)
        self.assertNotRegex(script, r"https?://")
        self.assertNotIn("Approve gate", html + script)
        self.assertNotIn("Release now", html + script)
        self.assertNotIn("Complete issue", html + script)

        for state in REQUIRED_PACKET_STATES:
            self.assertIn(f"[data-state-ui=\"{state}\"]", styles)
        for current_state in REQUIRED_CURRENT_STATES:
            self.assertIn(f"[data-current-state=\"{current_state}\"]", styles)

    def test_builder_writes_json_for_the_local_browser_surface(self) -> None:
        builder = load_data_builder()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "status-cockpit.json"
            result_path = builder.write_cockpit_data(
                ROOT,
                output,
                product_face_packet_path=sample_product_face_packet(tmp_path),
                product_face_review_path=sample_product_face_review(tmp_path),
            )
            data = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(result_path, output)
        self.assertEqual(data["source_inputs"]["normal_fetch_scope"], "local-relative-json-only")
        self.assertEqual(data["source_inputs"]["status_snapshot_fixture_count"], 18)
        self.assertIn("desktop_1440x900", data["product_face"]["viewports"])
        self.assertIn("mobile_390x844", data["product_face"]["viewports"])
        self.assertTrue(any(snapshot["state_ui"] == "success_current_snapshot" for snapshot in data["snapshots"]))
        self.assertTrue(any(snapshot["state_ui"] == "private_evidence_unavailable" for snapshot in data["snapshots"]))

    def test_server_defaults_to_loopback_and_rejects_public_binding(self) -> None:
        server_path = ROOT / "scripts" / "issue84" / "serve_local_cockpit.py"
        spec = importlib.util.spec_from_file_location("issue84_serve_local_cockpit", server_path)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules["issue84_serve_local_cockpit"] = module
        spec.loader.exec_module(module)

        self.assertEqual(module.DEFAULT_HOST, "127.0.0.1")
        self.assertTrue(module.is_loopback_host("127.0.0.1"))
        self.assertTrue(module.is_loopback_host("localhost"))
        self.assertFalse(module.is_loopback_host("0.0.0.0"))
        self.assertFalse(module.is_loopback_host("192.168.1.20"))


if __name__ == "__main__":
    unittest.main()
