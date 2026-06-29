from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VIEWPORTS = {
    "desktop": (1440, 900),
    "mobile": (390, 844),
}
ALLOWED_PRODUCT_ENV_CLASSES = {
    "production-like-static-artifact",
    "production-like-deployed",
    "deployed-production",
}
PRODUCT_ALIGNMENT_FIELDS = (
    "packet_comparison",
    "source_promise_coverage",
    "design_fit_review",
    "project_design_system_comparison",
    "professional_design_process_comparison",
    "reference_quality_comparison",
)
VISUAL_QUALITY_PASS_RESULTS = {"PASS", "PASS_WITH_RESIDUALS"}
VISUAL_QUALITY_RESIDUAL_SEVERITIES = {"low", "medium"}
REFERENCE_COMPARISON_DIMENSIONS = (
    "layout_hierarchy",
    "interaction_model",
    "state_coverage",
    "visual_language",
    "density_spacing",
)
REFERENCE_COMPARISON_ARTIFACT_TYPES = {
    "side_by_side_capture",
    "reference_snapshot",
    "design_system_component",
    "comparison_manifest",
    "bounded_equivalent",
}
BROWSER_CAPTURED_STATE_ALIASES = {
    "initial-render",
    "initial render",
    "initial_render",
    "initial",
    "loaded",
    "page-loaded",
    "page loaded",
}
BROWSER_CAPTURED_JOURNEYS = ("open target", "inspect configured viewports")
DRIVER_STEP_ACTIONS = {
    "goto",
    "click",
    "fill",
    "wait",
    "wait_for_selector",
    "assert_visible",
    "assert_text",
    "screenshot",
}
DRIVER_SELECTOR_ACTIONS = {"click", "fill", "wait_for_selector", "assert_visible", "assert_text"}


class PlaywrightUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Viewport:
    name: str
    width: int
    height: int

    @property
    def label(self) -> str:
        return f"{self.name} {self.width}x{self.height}"


class StaticHtmlSummary(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.lang = ""
        self.in_title = False
        self.tag_counts: dict[str, int] = {}
        self.images_missing_alt = 0
        self.controls_missing_name = 0
        self.disabled_controls = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        if tag == "html":
            self.lang = attrs_dict.get("lang", "")
        if tag == "title":
            self.in_title = True
        if tag == "img" and "alt" not in attrs_dict:
            self.images_missing_alt += 1
        if tag in {"button", "input", "select", "textarea"}:
            name = attrs_dict.get("aria-label") or attrs_dict.get("title") or attrs_dict.get("placeholder")
            if tag == "input":
                name = name or attrs_dict.get("name")
            if not name:
                self.controls_missing_name += 1
            if "disabled" in attrs_dict or attrs_dict.get("aria-disabled") == "true":
                self.disabled_controls += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data.strip()


def build_usage_evidence_matrix(
    *,
    viewports: list[Viewport],
    states: list[str],
    journeys: list[str],
    evidence_refs: list[str],
    data_condition: str = "configured proof data",
    a11y_status: str = "pass",
    performance_status: str = "pass",
    reviewer: str = "product-face-proof-runner",
    basis: str = "Journey, state and viewport were checked together in this Product Face proof run.",
) -> list[dict[str, Any]]:
    refs = [ref for ref in evidence_refs if str(ref).strip()] or ["external:product-face-proof-run"]
    return [
        {
            "journey": journey,
            "state": state,
            "viewport": viewport.label,
            "data_condition": data_condition,
            "evidence_refs": refs,
            "a11y_status": a11y_status,
            "performance_status": performance_status,
            "reviewer": reviewer,
            "basis": basis,
        }
        for journey in journeys
        for state in states
        for viewport in viewports
    ]


def _repo_ref_path(ref: str) -> Path | None:
    normalized = ref.strip().replace("\\", "/")
    if normalized.startswith(("http://", "https://", "external:", "repo://", "file://")):
        return None
    if Path(ref).is_absolute() or ":" in normalized.split("/", 1)[0]:
        return None
    candidate = (ROOT / normalized).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def build_visual_artifacts(
    *,
    target_ref: str,
    viewports: list[Viewport],
    states: list[str],
    screenshot_refs: list[str],
    captured_at: str | None = None,
) -> list[dict[str, Any]]:
    captured_at = captured_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    artifacts: list[dict[str, Any]] = []
    for viewport, screenshot_ref in zip(viewports, screenshot_refs):
        for state in states:
            artifact: dict[str, Any] = {
                "evidence_ref": screenshot_ref,
                "target": target_ref,
                "viewport": viewport.label,
                "state": state,
                "captured_at": captured_at,
                "freshness_status": "fresh",
                "basis": "Screenshot captured by the Product Face proof runner for this target, viewport and captured state.",
            }
            path = _repo_ref_path(screenshot_ref)
            if path is not None and path.is_file():
                artifact["sha256"] = sha256_file(path)
            else:
                artifact.update(
                    {
                        "freshness_status": "bounded_external",
                        "bounded_acceptance": True,
                        "sanitized": True,
                        "external_package_ref": "external:product-face-proof-package",
                    }
                )
            artifacts.append(artifact)
    return artifacts


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        text = str(item or "").strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            output.append(text)
    return output


def _normalized_label(value: str) -> str:
    return str(value or "").strip().lower().replace("_", " ").replace("-", " ")


def browser_capture_scope(*, states: list[str], journeys: list[str]) -> dict[str, Any]:
    declared_states = _unique_non_empty(states) or ["initial-render"]
    declared_journeys = _unique_non_empty(journeys) or list(BROWSER_CAPTURED_JOURNEYS)
    captured_states = [
        state
        for state in declared_states
        if state.strip().lower() in BROWSER_CAPTURED_STATE_ALIASES
        or _normalized_label(state) in BROWSER_CAPTURED_STATE_ALIASES
    ]
    if not captured_states:
        captured_states = ["initial-render"]
    captured_journeys = [
        journey
        for journey in declared_journeys
        if _normalized_label(journey) in {_normalized_label(item) for item in BROWSER_CAPTURED_JOURNEYS}
    ]
    if not captured_journeys:
        captured_journeys = ["open target"]
    captured_state_keys = {_normalized_label(state) for state in captured_states}
    captured_journey_keys = {_normalized_label(journey) for journey in captured_journeys}
    return {
        "mode": "browser_initial_render_only",
        "declared_states": declared_states,
        "declared_journeys": declared_journeys,
        "captured_states": captured_states,
        "captured_journeys": captured_journeys,
        "uncaptured_states": [state for state in declared_states if _normalized_label(state) not in captured_state_keys],
        "uncaptured_journeys": [journey for journey in declared_journeys if _normalized_label(journey) not in captured_journey_keys],
        "basis": (
            "The repository Product Face proof runner opens the target and captures rendered viewport evidence. "
            "It does not drive arbitrary state transitions or user journeys unless a future state driver records them."
        ),
    }


def apply_capture_scope(result: dict[str, Any], scope: dict[str, Any]) -> None:
    result["declared_states"] = list(scope.get("declared_states") or [])
    result["declared_journeys"] = list(scope.get("declared_journeys") or [])
    result["captured_states"] = list(scope.get("captured_states") or [])
    result["captured_journeys"] = list(scope.get("captured_journeys") or [])
    result["uncaptured_states"] = list(scope.get("uncaptured_states") or [])
    result["uncaptured_journeys"] = list(scope.get("uncaptured_journeys") or [])
    result["state_capture_policy"] = {
        "mode": str(scope.get("mode") or "browser_initial_render_only"),
        "cannot_claim_uncaptured_states": True,
        "basis": str(scope.get("basis") or ""),
    }
    if result["uncaptured_states"] or result["uncaptured_journeys"]:
        missing_bits = []
        if result["uncaptured_states"]:
            missing_bits.append("states: " + ", ".join(result["uncaptured_states"]))
        if result["uncaptured_journeys"]:
            missing_bits.append("journeys: " + ", ".join(result["uncaptured_journeys"]))
        result["result"] = "WAIVED"
        result["blocking_findings"] = True
        result["findings_summary"] = (
            str(result.get("findings_summary") or "Product Face proof captured.")
            + " Declared Product Face coverage was not executed by this runner: "
            + "; ".join(missing_bits)
            + "."
        )
        result["next_action"] = (
            "Provide Product Face state/journey drivers or separate proof artifacts for uncaptured coverage, "
            "then rerun before product acceptance."
        )
    else:
        result["checked_states"] = result["captured_states"] or result["checked_states"]
        result["user_journeys_checked"] = result["captured_journeys"] or result["user_journeys_checked"]
        result["journeys"] = result["user_journeys_checked"]


def load_state_journey_driver(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    driver = load_json_like(path)
    validate_state_journey_driver(driver)
    driver["_driver_ref"] = repo_ref(path)
    return driver


def validate_state_journey_driver(driver: Any) -> None:
    if not isinstance(driver, dict):
        raise ValueError("Product Face state/journey driver must be a JSON object")
    if driver.get("record_type") != "product_face_state_journey_driver":
        raise ValueError("Product Face state/journey driver record_type must be product_face_state_journey_driver")
    journeys = driver.get("journeys")
    if not isinstance(journeys, list) or not journeys:
        raise ValueError("Product Face state/journey driver requires at least one journey")
    for journey_index, journey in enumerate(journeys):
        if not isinstance(journey, dict):
            raise ValueError(f"driver.journeys[{journey_index}] must be an object")
        for field in ("name", "state"):
            if not str(journey.get(field) or "").strip():
                raise ValueError(f"driver.journeys[{journey_index}].{field} is required")
        for block_name in ("state_setup", "steps"):
            steps = journey.get(block_name, [])
            if block_name == "steps" and not steps:
                raise ValueError(f"driver.journeys[{journey_index}].steps requires at least one step")
            if not isinstance(steps, list):
                raise ValueError(f"driver.journeys[{journey_index}].{block_name} must be a list")
            for step_index, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(f"driver.journeys[{journey_index}].{block_name}[{step_index}] must be an object")
                action = str(step.get("action") or "").strip()
                if action not in DRIVER_STEP_ACTIONS:
                    raise ValueError(
                        f"driver.journeys[{journey_index}].{block_name}[{step_index}].action "
                        f"must be one of: {', '.join(sorted(DRIVER_STEP_ACTIONS))}"
                    )
                if action in DRIVER_SELECTOR_ACTIONS and not str(step.get("selector") or "").strip():
                    raise ValueError(
                        f"driver.journeys[{journey_index}].{block_name}[{step_index}].selector is required for {action}"
                    )
                if action == "fill" and "value" not in step:
                    raise ValueError(f"driver.journeys[{journey_index}].{block_name}[{step_index}].value is required")
                if action == "assert_text" and not str(step.get("text") or "").strip():
                    raise ValueError(f"driver.journeys[{journey_index}].{block_name}[{step_index}].text is required")
                if action == "goto" and not str(step.get("url") or "").strip():
                    raise ValueError(f"driver.journeys[{journey_index}].{block_name}[{step_index}].url is required")


def driver_capture_scope(
    *,
    states: list[str],
    journeys: list[str],
    driver: dict[str, Any],
    executions: list[dict[str, Any]],
) -> dict[str, Any]:
    driver_journeys = [
        str(journey.get("name") or "").strip()
        for journey in driver.get("journeys", [])
        if isinstance(journey, dict)
    ]
    driver_states = [
        str(journey.get("state") or "").strip()
        for journey in driver.get("journeys", [])
        if isinstance(journey, dict)
    ]
    declared_states = _unique_non_empty(states) or _unique_non_empty(driver_states) or ["initial-render"]
    declared_journeys = _unique_non_empty(journeys) or _unique_non_empty(driver_journeys)
    passed = [execution for execution in executions if execution.get("status") == "PASS"]
    captured_states = _unique_non_empty([str(execution.get("state") or "") for execution in passed])
    captured_journeys = _unique_non_empty([str(execution.get("journey") or "") for execution in passed])
    captured_state_keys = {_normalized_label(state) for state in captured_states}
    captured_journey_keys = {_normalized_label(journey) for journey in captured_journeys}
    return {
        "mode": "product_face_state_journey_driver",
        "declared_states": declared_states,
        "declared_journeys": declared_journeys,
        "captured_states": captured_states,
        "captured_journeys": captured_journeys,
        "uncaptured_states": [state for state in declared_states if _normalized_label(state) not in captured_state_keys],
        "uncaptured_journeys": [
            journey for journey in declared_journeys if _normalized_label(journey) not in captured_journey_keys
        ],
        "basis": "Product Face state/journey driver executed named journeys, setup steps and assertions in the browser.",
    }


def state_journey_driver_status(executions: list[dict[str, Any]], capture_scope: dict[str, Any]) -> str:
    if (
        not executions
        or any(item.get("status") != "PASS" for item in executions)
        or capture_scope["uncaptured_states"]
        or capture_scope["uncaptured_journeys"]
    ):
        return "FAIL"
    return "PASS"


def run_driver_step(page: Any, step: dict[str, Any], *, timeout_ms: int, screenshot_path: Path | None = None) -> None:
    action = str(step.get("action") or "").strip()
    selector = str(step.get("selector") or "").strip()
    if action == "goto":
        page.goto(str(step.get("url") or ""), wait_until="networkidle", timeout=timeout_ms)
    elif action == "click":
        page.locator(selector).click(timeout=timeout_ms)
    elif action == "fill":
        page.locator(selector).fill(str(step.get("value") or ""), timeout=timeout_ms)
    elif action == "wait":
        page.wait_for_timeout(int(step.get("ms") or 250))
    elif action == "wait_for_selector":
        page.wait_for_selector(selector, timeout=timeout_ms)
    elif action == "assert_visible":
        page.wait_for_selector(selector, state="visible", timeout=timeout_ms)
    elif action == "assert_text":
        page.wait_for_selector(selector, timeout=timeout_ms)
        actual = str(page.locator(selector).text_content(timeout=timeout_ms) or "")
        expected = str(step.get("text") or "")
        if expected not in actual:
            raise AssertionError(f"selector {selector!r} text did not contain {expected!r}")
    elif action == "screenshot":
        if screenshot_path is None:
            raise ValueError("screenshot step requires a screenshot path")
        page.screenshot(path=str(screenshot_path), full_page=bool(step.get("full_page", True)))
    else:
        raise ValueError(f"unsupported Product Face driver action: {action}")


def execute_state_journey_driver(
    *,
    page: Any,
    driver: dict[str, Any],
    viewport: Viewport,
    screenshot_dir: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    executions: list[dict[str, Any]] = []
    screenshot_refs: list[str] = []
    default_timeout = int(driver.get("timeout_ms") or 5000)
    for journey_index, journey in enumerate(driver.get("journeys", [])):
        viewport_names = {str(item).strip() for item in journey.get("viewport_names", []) if str(item).strip()}
        if viewport_names and viewport.name not in viewport_names and viewport.label not in viewport_names:
            continue
        journey_name = str(journey.get("name") or "").strip()
        state_name = str(journey.get("state") or "").strip()
        timeout_ms = int(journey.get("timeout_ms") or default_timeout)
        execution: dict[str, Any] = {
            "journey": journey_name,
            "state": state_name,
            "viewport": viewport.label,
            "data_condition": str(journey.get("data_condition") or "driver-controlled proof data"),
            "status": "PASS",
            "steps": [],
            "evidence_refs": list(journey.get("evidence_refs") or []),
        }
        try:
            for block_name in ("state_setup", "steps"):
                for step_index, step in enumerate(journey.get(block_name, [])):
                    step_action = str(step.get("action") or "").strip()
                    step_record = {
                        "block": block_name,
                        "index": step_index,
                        "action": step_action,
                        "selector": str(step.get("selector") or ""),
                    }
                    screenshot_path = None
                    if step_action == "screenshot":
                        safe_journey = re.sub(r"[^a-zA-Z0-9_-]+", "-", journey_name.lower()).strip("-") or "journey"
                        screenshot_path = screenshot_dir / f"driver-{viewport.name}-{journey_index}-{safe_journey}-{step_index}.png"
                    run_driver_step(page, step, timeout_ms=timeout_ms, screenshot_path=screenshot_path)
                    if screenshot_path is not None:
                        ref = repo_ref(screenshot_path)
                        screenshot_refs.append(ref)
                        execution["evidence_refs"].append(ref)
                        step_record["evidence_ref"] = ref
                    execution["steps"].append(step_record)
        except Exception as exc:
            execution["status"] = "FAIL"
            execution["failure"] = redact_text(str(exc)[:1000])
        executions.append(execution)
    return executions, screenshot_refs


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def parse_viewport(raw: str) -> Viewport:
    if "=" in raw:
        name, size = raw.split("=", 1)
    else:
        name, size = raw, raw
    if "x" not in size.lower():
        raise ValueError(f"viewport must use NAME=WIDTHxHEIGHT, got {raw!r}")
    width_raw, height_raw = size.lower().split("x", 1)
    width = int(width_raw)
    height = int(height_raw)
    if width < 1 or height < 1:
        raise ValueError(f"viewport dimensions must be positive, got {raw!r}")
    return Viewport(name=name.strip() or f"{width}x{height}", width=width, height=height)


def parse_reference_dimension(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError("--reference-comparison-dimension must be DIMENSION=BASIS")
    dimension, basis = raw.split("=", 1)
    dimension = dimension.strip()
    basis = basis.strip()
    if dimension not in REFERENCE_COMPARISON_DIMENSIONS:
        allowed = ", ".join(REFERENCE_COMPARISON_DIMENSIONS)
        raise ValueError(f"--reference-comparison-dimension dimension must be one of: {allowed}")
    if not basis:
        raise ValueError("--reference-comparison-dimension basis must be non-empty")
    return dimension, basis


def parse_reference_comparison_artifact(raw: str, compared_source_ids: list[str]) -> dict[str, Any]:
    if "=" in raw:
        artifact_type, artifact_ref = raw.split("=", 1)
    else:
        artifact_type, artifact_ref = "side_by_side_capture", raw
    artifact_type = artifact_type.strip()
    artifact_ref = artifact_ref.strip()
    if artifact_type not in REFERENCE_COMPARISON_ARTIFACT_TYPES:
        allowed = ", ".join(sorted(REFERENCE_COMPARISON_ARTIFACT_TYPES))
        raise ValueError(f"--reference-comparison-artifact type must be one of: {allowed}")
    if not artifact_ref:
        raise ValueError("--reference-comparison-artifact artifact ref must be non-empty")
    artifact = {
        "artifact_ref": artifact_ref,
        "artifact_type": artifact_type,
        "compared_source_ids": compared_source_ids,
        "basis": "Material comparison artifact supplied with Product Face reference-quality review.",
    }
    if artifact_ref.startswith(("http://", "https://", "external:", "repo://")):
        artifact["bounded_acceptance"] = True
        artifact["sanitized"] = True
    return artifact


def resolve_target(target: str, *, allow_external_file: bool = False) -> tuple[str, Path | None]:
    if target.startswith(("http://", "https://")):
        return target, None
    path = Path(target)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        if not allow_external_file:
            raise ValueError("file targets must be repo-relative unless --allow-external-file is set")
    return path.as_uri(), path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_public_artifact(data), indent=2, sort_keys=False) + "\n", encoding="utf-8")


def load_json_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return json.loads(stripped)


def card_ref_from_card(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id"),
        "slice_id": card.get("slice_id"),
        "phase": card.get("phase"),
        "risk_effective": card.get("risk_effective"),
        "surfaces": card.get("surfaces", []),
        "executor_identity": card.get("executor_identity"),
        "reviewer_identity": card.get("reviewer_identity"),
    }


def redact_text(value: str) -> str:
    redacted = value.replace(str(ROOT), "<repo-root>")
    redacted = redacted.replace(str(ROOT).replace("\\", "/"), "<repo-root>")
    redacted = redacted.replace(ROOT.as_uri(), "repo://")
    try:
        home = str(Path.home())
    except RuntimeError:
        home = ""
    if home:
        redacted = redacted.replace(home, "<home>")
        redacted = redacted.replace(home.replace("\\", "/"), "<home>")
    redacted = re.sub(r"file:///[A-Za-z]:/Users/[^\s\"')<]+", "file:///<redacted-local-file>", redacted)
    redacted = re.sub(r"[A-Za-z]:[/\\]+Users[/\\]+[^\s\"')<]+", "<redacted-local-path>", redacted)
    redacted = re.sub(r"/home/[^\\s\"')<]+", "<redacted-local-path>", redacted)
    redacted = re.sub(r"/" + r"tmp/[^\s\"')<]+", "<redacted-temp-path>", redacted)
    private_workspace_marker = "".join(["K", "axis%20", "V", "M"])
    redacted = redacted.replace(private_workspace_marker, "workspace")
    return redacted


def redact_public_artifact(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_public_artifact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_public_artifact(item) for key, item in value.items()}
    return value


def summarize_static_html(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "$schema": "https://overkill-factory.dev/schemas/product-face-static-summary.schema.json",
            "mode": "remote-url",
            "note": "static fallback cannot read remote DOM",
        }
    if not path.exists():
        return {
            "$schema": "https://overkill-factory.dev/schemas/product-face-static-summary.schema.json",
            "mode": "missing-file",
            "target": repo_ref(path),
        }
    summary = StaticHtmlSummary()
    text = path.read_text(encoding="utf-8", errors="replace")
    summary.feed(text)
    return {
        "$schema": "https://overkill-factory.dev/schemas/product-face-static-summary.schema.json",
        "mode": "static-file",
        "target": repo_ref(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "title": summary.title,
        "lang": summary.lang,
        "tag_counts": summary.tag_counts,
        "images_missing_alt": summary.images_missing_alt,
        "controls_missing_name": summary.controls_missing_name,
        "disabled_controls": summary.disabled_controls,
    }


def build_fallback_result(
    *,
    target_ref: str,
    target_path: Path | None,
    output_dir: Path,
    viewports: list[Viewport],
    states: list[str],
    journeys: list[str],
    reason: str,
) -> dict[str, Any]:
    static_summary = summarize_static_html(target_path)
    summary_path = output_dir / "static-summary.json"
    write_json(summary_path, static_summary)
    note_path = output_dir / "fallback-limit.md"
    note_path.write_text(
        "# Product Face Proof Fallback\n\n"
        f"Target: `{target_ref}`\n\n"
        f"Reason: {reason}\n\n"
        "No browser render, screenshot, console, layout, accessibility tree or runtime performance "
        "claim was captured. This is a bounded registration only.\n",
        encoding="utf-8",
    )
    result = base_result(
        target_ref=target_ref,
        viewports=viewports,
        states=states,
        journeys=journeys,
        tool_or_profile="static-html-fallback-no-playwright",
    )
    result.update(
        {
            "result": "WAIVED",
            "blocking_findings": True,
            "findings_summary": "Playwright proof did not run; static target metadata was registered only.",
            "screenshots": [f"not-captured: {reason}"],
            "a11y": {
                "status": "fail",
                "reason": reason,
                "static_summary_ref": repo_ref(summary_path),
            },
            "overlap_check": {
                "status": "fail",
                "reason": reason,
            },
            "console": {
                "status": "fail",
                "reason": reason,
            },
            "performance_note": "not measured; browser proof did not run",
            "evidence_refs": [repo_ref(summary_path), repo_ref(note_path)],
            "next_action": "Install Playwright and rerun the Product Face proof before treating the UI as visually verified.",
        }
    )
    return result


def build_waiver(result: dict[str, Any]) -> dict[str, Any]:
    evidence_refs = [str(ref) for ref in result.get("evidence_refs", []) if str(ref).strip()]
    if not evidence_refs:
        evidence_refs = ["external:product-face-waiver-boundary"]
    return {
        "owner": "product-face-validator",
        "reason": str(
            result.get("findings_summary")
            or result.get("next_action")
            or "Product Face proof was waived."
        ),
        "expires_at": "before-product-approval",
        "reviewer_or_human_gate_ref": "human-gate-required:product-face-proof-rerun",
        "compensating_controls": [
            "result is marked not reusable for product approval",
            "rerun Product Face proof with browser screenshots before promotion",
        ],
        "evidence_refs": evidence_refs,
    }


def base_result(
    *,
    target_ref: str,
    viewports: list[Viewport],
    states: list[str],
    journeys: list[str],
    tool_or_profile: str,
    card_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/product-face-result.schema.json",
        "record_type": "product_face_result",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "worker": {
            "id": "product-face",
            "name": "Product Face Validator",
            "factory_phase": "F5/F13",
        },
        "card_ref": card_ref or {
            "card_id": "PRODUCT-FACE-PROOF",
            "phase": "F5",
            "risk_effective": "R2",
            "surfaces": ["ux", "frontend", "mobile", "product-face"],
        },
        "target": target_ref,
        "result": "PASS",
        "blocking_findings": False,
        "findings_summary": "Product Face browser proof captured.",
        "tool_or_profile": tool_or_profile,
        "executed_by": "product-face-proof-runner",
        "surface_evidence_profile": {
            "profile_id": "web_visual_ui",
            "surface": "web_app",
            "evidence_kind": "visual_ui",
        },
        "surface_evidence_profiles": [
            {
                "profile_id": "web_visual_ui",
                "surface": "web_app",
                "evidence_kind": "visual_ui",
            }
        ],
        "screenshots": [],
        "viewports": [viewport.label for viewport in viewports],
        "checked_states": states,
        "user_journeys_checked": journeys,
        "journeys": journeys,
        "usage_evidence_matrix": build_usage_evidence_matrix(
            viewports=viewports,
            states=states,
            journeys=journeys,
            evidence_refs=[target_ref],
            data_condition="configured proof target",
        ),
        "a11y": {},
        "accessibility": {},
        "overlap_check": {},
        "overlap": {},
        "performance_note": "",
        "packet_ref": "",
        "packet_comparison": {
            "status": "pending",
            "basis": "Browser proof captured render evidence only; compare against Product Face Packet before completion.",
        },
        "source_promise_coverage": {
            "status": "pending",
            "basis": "Browser proof does not by itself prove fit to the original product promise.",
        },
        "design_fit_review": {
            "status": "pending",
            "basis": "Visual/product-fit review must be recorded by Product Face reviewer before promotion.",
        },
        "project_design_system_ref": "",
        "project_design_system_comparison": {
            "status": "pending",
            "basis": "Product Face proof must compare the result against the project design system before promotion.",
        },
        "professional_design_process_ref": "",
        "professional_design_process_comparison": {
            "status": "pending",
            "basis": "Product Face proof must compare the result against the professional design process before promotion.",
        },
        "reference_quality_comparison": {
            "status": "pending",
            "basis": "Product Face proof must compare the implemented surface against selected design-library references before promotion.",
            "reference_set_ref": "",
            "compared_source_ids": [],
            "reviewer_independent_from_implementation": False,
            "dimensions": {
                dimension: {
                    "status": "pending",
                    "basis": "Reference comparison not recorded.",
                }
                for dimension in REFERENCE_COMPARISON_DIMENSIONS
            },
        },
        "visual_quality_result": {
            "status": "BLOCK",
            "reviewer": "product-face-proof-runner",
            "basis": "Mechanical browser proof is necessary but not sufficient for professional visual approval.",
            "reference_quality_bar_checked": False,
            "ai_generic_symptoms": ["visual quality review not recorded"],
            "residuals": [],
        },
        "evidence_refs": [],
        "evidence_kind": "real",
        "reusable_for_product": False,
        "next_action": "Attach product_face_result to the completion receipt.",
    }


def validate_reusable_product_scope(
    *,
    result: dict[str, Any],
    target_ref: str,
    target_path: Path | None,
    product_id: str | None,
    environment_class: str | None,
    approval_scope: str | None,
) -> None:
    if result.get("result") != "PASS" or result.get("blocking_findings") is True:
        raise ValueError("reusable Product Face evidence requires a PASS result with no blocking findings")
    if not product_id or len(product_id.strip()) < 3:
        raise ValueError("--reusable-for-product requires --product-id")
    if not environment_class or environment_class not in ALLOWED_PRODUCT_ENV_CLASSES:
        allowed = ", ".join(sorted(ALLOWED_PRODUCT_ENV_CLASSES))
        raise ValueError(f"--reusable-for-product requires --environment-class in: {allowed}")
    if not approval_scope or len(approval_scope.strip()) < 10:
        raise ValueError("--reusable-for-product requires a specific --approval-scope")
    if environment_class == "production-like-static-artifact" and target_path is None:
        raise ValueError("production-like-static-artifact requires a repo file target so the artifact hash can be recorded")
    if environment_class == "deployed-production" and target_ref.startswith("file://"):
        raise ValueError("deployed-production requires an http(s) target, not a local file target")
    if not product_alignment_passes(result):
        raise ValueError(
            "--reusable-for-product requires Product Face alignment: packet_ref, "
            "packet_comparison=pass, source_promise_coverage=pass, design_fit_review=pass, "
            "project_design_system_comparison=pass, professional_design_process_comparison=pass, "
            "reference_quality_comparison=pass"
        )
    visual_quality = result.get("visual_quality_result") if isinstance(result.get("visual_quality_result"), dict) else {}
    if visual_quality.get("status") not in VISUAL_QUALITY_PASS_RESULTS or visual_quality.get("reference_quality_bar_checked") is not True:
        raise ValueError("reusable Product Face evidence requires visual_quality_result PASS or PASS_WITH_RESIDUALS")
    if not reference_quality_passes(result):
        raise ValueError("reusable Product Face evidence requires dimensioned reference_quality_comparison PASS")


def product_alignment_passes(result: dict[str, Any]) -> bool:
    if not str(result.get("packet_ref") or "").strip():
        return False
    if not str(result.get("project_design_system_ref") or "").strip():
        return False
    for field in PRODUCT_ALIGNMENT_FIELDS:
        value = result.get(field)
        if not isinstance(value, dict) or value.get("status") != "pass":
            return False
        if not str(value.get("basis") or "").strip():
            return False
    return True


def visual_quality_passes(result: dict[str, Any]) -> bool:
    visual_quality = result.get("visual_quality_result")
    if not isinstance(visual_quality, dict):
        return False
    if visual_quality.get("status") not in VISUAL_QUALITY_PASS_RESULTS:
        return False
    if visual_quality.get("reference_quality_bar_checked") is not True:
        return False
    if not str(visual_quality.get("reviewer") or "").strip():
        return False
    if not str(visual_quality.get("basis") or "").strip():
        return False
    if visual_quality.get("status") == "PASS_WITH_RESIDUALS":
        residuals = visual_quality.get("residuals")
        if not isinstance(residuals, list) or not residuals:
            return False
        for residual in residuals:
            if not visual_quality_residual_is_bounded(residual):
                return False
    return True


def parse_iso_timestamp(value: str) -> datetime | None:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def visual_quality_residual_is_bounded(residual: Any) -> bool:
    if not isinstance(residual, dict):
        return False
    for field in ("id", "description", "severity", "owner", "expires_at", "accepted_scope"):
        if not str(residual.get(field) or "").strip():
            return False
    if str(residual.get("severity") or "").strip().lower() not in VISUAL_QUALITY_RESIDUAL_SEVERITIES:
        return False
    expires_at = parse_iso_timestamp(str(residual.get("expires_at") or ""))
    if expires_at is None or expires_at <= datetime.now(timezone.utc):
        return False
    if residual.get("blocks_full_acceptance") is not False:
        return False
    proof_refs = residual.get("proof_refs")
    if not isinstance(proof_refs, list) or not any(str(item).strip() for item in proof_refs):
        return False
    return True


def parse_visual_quality_residual(raw: str) -> dict[str, Any]:
    parts = [part.strip() for part in str(raw or "").split("|", 6)]
    if len(parts) != 7:
        raise ValueError(
            "--visual-quality-residual must use "
            "ID|SEVERITY|OWNER|EXPIRES_AT|ACCEPTED_SCOPE|PROOF_REF[,PROOF_REF]|DESCRIPTION"
        )
    residual_id, severity, owner, expires_at, accepted_scope, proof_refs_raw, description = parts
    proof_refs = [item.strip() for item in proof_refs_raw.split(",") if item.strip()]
    residual = {
        "id": residual_id,
        "description": description,
        "severity": severity.lower(),
        "owner": owner,
        "expires_at": expires_at,
        "accepted_scope": accepted_scope,
        "proof_refs": proof_refs,
        "blocks_full_acceptance": False,
    }
    if not visual_quality_residual_is_bounded(residual):
        raise ValueError("--visual-quality-residual must describe a bounded low/medium non-blocking residual with proof refs")
    return residual


def reference_quality_passes(result: dict[str, Any]) -> bool:
    comparison = result.get("reference_quality_comparison")
    if not isinstance(comparison, dict):
        return False
    if comparison.get("status") != "pass":
        return False
    if not str(comparison.get("basis") or "").strip():
        return False
    if not str(comparison.get("reference_set_ref") or "").strip():
        return False
    if len([item for item in comparison.get("compared_source_ids") or [] if str(item).strip()]) < 3:
        return False
    if comparison.get("reviewer_independent_from_implementation") is not True:
        return False
    dimensions = comparison.get("dimensions")
    if not isinstance(dimensions, dict):
        return False
    for dimension in REFERENCE_COMPARISON_DIMENSIONS:
        verdict = dimensions.get(dimension)
        if not isinstance(verdict, dict):
            return False
        if verdict.get("status") != "pass":
            return False
        if not str(verdict.get("basis") or "").strip():
            return False
    compared_source_ids = {str(item).strip() for item in comparison.get("compared_source_ids") or [] if str(item).strip()}
    artifact_coverage: set[str] = set()
    artifacts = comparison.get("comparison_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return False
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            return False
        artifact_ref = str(artifact.get("artifact_ref") or "").strip()
        if not artifact_ref:
            return False
        if artifact.get("artifact_type") not in REFERENCE_COMPARISON_ARTIFACT_TYPES:
            return False
        if not str(artifact.get("basis") or "").strip():
            return False
        if artifact_ref.startswith(("http://", "https://", "external:", "repo://")) and (
            artifact.get("bounded_acceptance") is not True or artifact.get("sanitized") is not True
        ):
            return False
        artifact_source_ids = {str(item).strip() for item in artifact.get("compared_source_ids") or [] if str(item).strip()}
        if not artifact_source_ids:
            return False
        if artifact_source_ids - compared_source_ids:
            return False
        artifact_coverage.update(artifact_source_ids)
    if compared_source_ids - artifact_coverage:
        return False
    return True


def apply_product_alignment(
    *,
    result: dict[str, Any],
    packet_ref: str | None,
    packet_comparison_basis: str | None,
    source_promise_coverage_basis: str | None,
    design_fit_review_basis: str | None,
    project_design_system_ref: str | None,
    project_design_system_comparison_basis: str | None,
    professional_design_process_ref: str | None,
    professional_design_process_comparison_basis: str | None,
    reference_quality_ref: str | None,
    reference_quality_comparison_basis: str | None,
    compared_reference_ids: list[str] | None,
    reference_quality_dimensions: dict[str, str] | None,
    reference_comparison_artifacts: list[dict[str, Any]] | None = None,
) -> None:
    values = {
        "packet_ref": packet_ref,
        "packet_comparison": packet_comparison_basis,
        "source_promise_coverage": source_promise_coverage_basis,
        "design_fit_review": design_fit_review_basis,
        "project_design_system_ref": project_design_system_ref,
        "project_design_system_comparison": project_design_system_comparison_basis,
        "professional_design_process_ref": professional_design_process_ref,
        "professional_design_process_comparison": professional_design_process_comparison_basis,
        "reference_quality_ref": reference_quality_ref,
        "reference_quality_comparison": reference_quality_comparison_basis,
    }
    supplied = {field for field, value in values.items() if str(value or "").strip()}
    if compared_reference_ids:
        supplied.add("compared_reference_ids")
    if reference_quality_dimensions:
        supplied.add("reference_quality_dimensions")
    if reference_comparison_artifacts:
        supplied.add("reference_comparison_artifacts")
    if not supplied:
        return
    missing = [field for field, value in values.items() if not str(value or "").strip()]
    if not compared_reference_ids or len([item for item in compared_reference_ids if str(item).strip()]) < 3:
        missing.append("compared_reference_ids")
    missing_dimensions = [
        dimension
        for dimension in REFERENCE_COMPARISON_DIMENSIONS
        if not str((reference_quality_dimensions or {}).get(dimension) or "").strip()
    ]
    if missing_dimensions:
        missing.extend(f"reference_comparison_dimension:{dimension}" for dimension in missing_dimensions)
    if not reference_comparison_artifacts:
        missing.append("reference_comparison_artifacts")
    if missing:
        raise ValueError("Product Face alignment is incomplete: missing " + ", ".join(missing))
    result["packet_ref"] = str(packet_ref).strip()
    result["packet_comparison"] = {
        "status": "pass",
        "basis": str(packet_comparison_basis).strip(),
    }
    result["source_promise_coverage"] = {
        "status": "pass",
        "basis": str(source_promise_coverage_basis).strip(),
    }
    result["design_fit_review"] = {
        "status": "pass",
        "basis": str(design_fit_review_basis).strip(),
    }
    result["project_design_system_ref"] = str(project_design_system_ref).strip()
    result["project_design_system_comparison"] = {
        "status": "pass",
        "basis": str(project_design_system_comparison_basis).strip(),
    }
    result["professional_design_process_ref"] = str(professional_design_process_ref).strip()
    result["professional_design_process_comparison"] = {
        "status": "pass",
        "basis": str(professional_design_process_comparison_basis).strip(),
    }
    result["reference_quality_comparison"] = {
        "status": "pass",
        "basis": str(reference_quality_comparison_basis).strip(),
        "reference_set_ref": str(reference_quality_ref).strip(),
        "compared_source_ids": [str(item).strip() for item in compared_reference_ids or [] if str(item).strip()],
        "reviewer_independent_from_implementation": True,
        "comparison_artifacts": reference_comparison_artifacts or [],
        "dimensions": {
            dimension: {
                "status": "pass",
                "basis": str((reference_quality_dimensions or {}).get(dimension)).strip(),
            }
            for dimension in REFERENCE_COMPARISON_DIMENSIONS
        },
    }


def apply_visual_quality_review(
    *,
    result: dict[str, Any],
    status: str | None,
    reviewer: str | None,
    basis: str | None,
    residuals: list[dict[str, Any]] | None = None,
) -> None:
    supplied = any(str(value or "").strip() for value in (status, reviewer, basis)) or bool(residuals)
    if not supplied:
        return
    normalized_status = str(status or "").strip().upper()
    if normalized_status not in {"PASS", "BLOCK", "PASS_WITH_RESIDUALS"}:
        raise ValueError("--visual-quality-status must be PASS, BLOCK or PASS_WITH_RESIDUALS")
    missing = []
    if not str(reviewer or "").strip():
        missing.append("visual-quality-reviewer")
    if not str(basis or "").strip():
        missing.append("visual-quality-basis")
    if normalized_status == "PASS_WITH_RESIDUALS" and not residuals:
        missing.append("visual-quality-residual")
    if residuals and any(not visual_quality_residual_is_bounded(residual) for residual in residuals):
        missing.append("bounded-visual-quality-residual")
    if missing:
        raise ValueError("Visual quality review is incomplete: missing " + ", ".join(missing))
    result["visual_quality_result"] = {
        "status": normalized_status,
        "reviewer": str(reviewer).strip(),
        "basis": str(basis).strip(),
        "reference_quality_bar_checked": normalized_status in VISUAL_QUALITY_PASS_RESULTS,
        "ai_generic_symptoms": [] if normalized_status in VISUAL_QUALITY_PASS_RESULTS else ["reviewer-blocked-visual-quality"],
        "residuals": residuals or [],
    }


def enforce_visual_quality_gate(result: dict[str, Any]) -> None:
    if result.get("result") == "PASS" and (not visual_quality_passes(result) or not reference_quality_passes(result)):
        result["result"] = "WAIVED"
        result["blocking_findings"] = True
        result["findings_summary"] = (
            "Mechanical Product Face proof ran, but professional visual/reference quality approval is missing or blocked."
        )
        result["next_action"] = (
            "Record visual_quality_result and dimensioned reference_quality_comparison PASS from an independent Product Face reviewer before promotion."
        )


def apply_product_reuse_scope(
    *,
    result: dict[str, Any],
    target_ref: str,
    target_path: Path | None,
    product_id: str | None,
    environment_class: str | None,
    approval_scope: str | None,
) -> None:
    validate_reusable_product_scope(
        result=result,
        target_ref=target_ref,
        target_path=target_path,
        product_id=product_id,
        environment_class=environment_class,
        approval_scope=approval_scope,
    )
    product_target: dict[str, Any] = {
        "product_id": product_id.strip() if product_id else "",
        "environment_class": environment_class,
        "target": target_ref,
        "approval_scope": approval_scope.strip() if approval_scope else "",
        "production_like": environment_class in {"production-like-static-artifact", "production-like-deployed"},
        "deployed_production": environment_class == "deployed-production",
        "reusability_boundary": (
            "Reusable only for the named product target and approval scope; "
            "other products, releases, deploys, onchain code or human gates must rerun their own evidence."
        ),
    }
    if target_path is not None:
        product_target["target_artifact_ref"] = repo_ref(target_path)
        product_target["target_sha256"] = sha256_file(target_path)
    result["product_target"] = product_target
    result["reusable_for_product"] = True
    result["next_action"] = "Attach this product-specific Product Face result to the production Product Face lane."


def launch_chromium_browser(chromium: Any) -> Any:
    """Launch Chromium, falling back to the system Chrome channel when needed."""
    launch_errors: list[str] = []
    for launch_kwargs in ({}, {"channel": "chrome"}):
        try:
            return chromium.launch(**launch_kwargs)
        except Exception as exc:  # pragma: no cover - exercised with fakes/unit tests.
            label = "default" if not launch_kwargs else "chrome channel"
            launch_errors.append(f"{label}: {exc}")
    raise PlaywrightUnavailable("Playwright browser is not available: " + "; ".join(launch_errors))


def run_playwright(
    *,
    target_url: str,
    target_ref: str,
    output_dir: Path,
    viewports: list[Viewport],
    states: list[str],
    journeys: list[str],
    strict: bool,
    state_journey_driver: dict[str, Any] | None = None,
    card_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PlaywrightUnavailable("python Playwright package is not installed") from exc

    capture_scope = browser_capture_scope(states=states, journeys=journeys)
    captured_states = list(capture_scope["captured_states"])
    captured_journeys = list(capture_scope["captured_journeys"])
    screenshots: list[str] = []
    console_messages: list[dict[str, str]] = []
    page_errors: list[str] = []
    viewport_results: dict[str, Any] = {}
    driver_executions: list[dict[str, Any]] = []
    driver_screenshots: list[str] = []
    screenshot_dir = output_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = launch_chromium_browser(playwright.chromium)
        try:
            for viewport in viewports:
                page_console: list[dict[str, str]] = []
                context = browser.new_context(viewport={"width": viewport.width, "height": viewport.height})
                page = context.new_page()
                page.on(
                    "console",
                    lambda msg, bucket=page_console: bucket.append(
                        {"type": msg.type, "text": msg.text[:1000]}
                    ),
                )
                page.on("pageerror", lambda err: page_errors.append(str(err)[:1000]))
                page.goto(target_url, wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(250)
                if state_journey_driver is not None:
                    executions, driver_refs = execute_state_journey_driver(
                        page=page,
                        driver=state_journey_driver,
                        viewport=viewport,
                        screenshot_dir=screenshot_dir,
                    )
                    driver_executions.extend(executions)
                    driver_screenshots.extend(driver_refs)
                screenshot_path = screenshot_dir / f"{viewport.name}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshots.append(repo_ref(screenshot_path))
                console_messages.extend({"viewport": viewport.name, **item} for item in page_console)
                viewport_results[viewport.name] = collect_browser_checks(page)
                context.close()
        finally:
            browser.close()

    if state_journey_driver is not None:
        capture_scope = driver_capture_scope(
            states=states,
            journeys=journeys,
            driver=state_journey_driver,
            executions=driver_executions,
        )
        captured_states = list(capture_scope["captured_states"])
        captured_journeys = list(capture_scope["captured_journeys"])

    captured_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    console_path = output_dir / "console.json"
    state_path = output_dir / "state.json"
    driver_path = output_dir / "state-journey-driver-execution.json"
    write_json(
        console_path,
        {
            "$schema": "https://overkill-factory.dev/schemas/product-face-console.schema.json",
            "messages": console_messages,
            "page_errors": page_errors,
        },
    )
    write_json(
        state_path,
        {
            "$schema": "https://overkill-factory.dev/schemas/product-face-state.schema.json",
            "viewports": viewport_results,
        },
    )

    a11y_issues = []
    overlap_issues = []
    perf_notes = []
    for viewport_name, checks in viewport_results.items():
        a11y_issues.extend(f"{viewport_name}: {issue}" for issue in checks["a11y"]["issues"])
        overlap_issues.extend(f"{viewport_name}: {item['summary']}" for item in checks["overlap"]["items"])
        perf = checks["performance"]
        perf_notes.append(
            f"{viewport_name} render duration {perf.get('duration_ms', 'n/a')} ms, "
            f"dom nodes {perf.get('dom_nodes', 'n/a')}"
        )

    console_errors = [
        item for item in console_messages if item.get("type") in {"error", "assert"}
    ]
    blocking = bool(page_errors or console_errors or a11y_issues or overlap_issues)
    if any(execution.get("status") != "PASS" for execution in driver_executions):
        blocking = True
    result = base_result(
        target_ref=target_ref,
        viewports=viewports,
        states=captured_states,
        journeys=captured_journeys,
        tool_or_profile="playwright-static-product-face-proof",
        card_ref=card_ref,
    )
    result.update(
        {
            "result": "WAIVED" if blocking else "PASS",
            "blocking_findings": blocking,
            "findings_summary": (
                "Browser proof captured with blocking findings."
                if blocking
                else "Browser proof captured for screenshots, console, DOM state, a11y basics, overlap and performance note."
            ),
            "screenshots": screenshots,
            "visual_artifacts": build_visual_artifacts(
                target_ref=target_ref,
                viewports=viewports,
                states=captured_states,
                screenshot_refs=[*screenshots, *driver_screenshots],
                captured_at=captured_at,
            ),
            "a11y": {
                "status": "warn" if a11y_issues else "pass",
                "issues": a11y_issues,
                "basis": "DOM-level accessible-name, title, lang, image alt and landmark checks; not a full WCAG audit.",
            },
            "accessibility": {
                "status": "warn" if a11y_issues else "pass",
                "issues": a11y_issues,
                "basis": "DOM-level accessible-name, title, lang, image alt and landmark checks; not a full WCAG audit.",
            },
            "overlap_check": {
                "status": "warn" if overlap_issues else "pass",
                "issues": overlap_issues[:25],
                "basis": "DOM rectangle intersection scan; nested parent-child overlaps are ignored.",
            },
            "overlap": {
                "status": "warn" if overlap_issues else "pass",
                "issues": overlap_issues[:25],
                "basis": "DOM rectangle intersection scan; nested parent-child overlaps are ignored.",
            },
            "console": {
                "status": "fail" if page_errors or console_errors else "pass",
                "messages_ref": repo_ref(console_path),
                "error_count": len(console_errors),
                "page_error_count": len(page_errors),
            },
            "performance_note": "; ".join(perf_notes)
            + "; browser-local static proof only, not a production performance benchmark",
            "evidence_refs": [repo_ref(state_path), repo_ref(console_path), *screenshots, *driver_screenshots],
            "usage_evidence_matrix": build_usage_evidence_matrix(
                viewports=viewports,
                states=captured_states,
                journeys=captured_journeys,
                evidence_refs=[repo_ref(state_path), repo_ref(console_path), *screenshots, *driver_screenshots],
                data_condition="browser-local rendered state fixture",
                a11y_status="warn" if a11y_issues else "pass",
                performance_status="pass",
            ),
            "next_action": (
                "Fix blocking browser findings and rerun Product Face proof."
                if blocking
                else "Attach product_face_result to the completion receipt."
            ),
        }
    )
    if state_journey_driver is not None:
        driver_record = {
            "$schema": "https://overkill-factory.dev/schemas/product-face-state-journey-driver-execution.schema.json",
            "record_type": "product_face_state_journey_driver_execution",
            "driver_ref": state_journey_driver.get("_driver_ref", "external:product-face-state-journey-driver"),
            "executions": driver_executions,
        }
        write_json(driver_path, driver_record)
        result["state_journey_driver"] = {
            "driver_ref": state_journey_driver.get("_driver_ref", "external:product-face-state-journey-driver"),
            "status": state_journey_driver_status(driver_executions, capture_scope),
            "execution_ref": repo_ref(driver_path),
            "journeys_executed": captured_journeys,
            "states_executed": captured_states,
        }
        result["driver_execution"] = driver_record
        result["evidence_refs"] = [*result["evidence_refs"], repo_ref(driver_path)]
        result["usage_evidence_matrix"] = build_usage_evidence_matrix(
            viewports=viewports,
            states=captured_states,
            journeys=captured_journeys,
            evidence_refs=[repo_ref(driver_path), *driver_screenshots],
            data_condition="driver-controlled proof data",
            a11y_status="warn" if a11y_issues else "pass",
            performance_status="pass",
            basis="Journey, state and viewport were executed through the Product Face state/journey driver.",
        )
    apply_capture_scope(result, capture_scope)
    return result


def collect_browser_checks(page: Any) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const visible = (el) => {
            const style = window.getComputedStyle(el);
            const rect = el.getBoundingClientRect();
            return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
          };
          const nameOf = (el) => (
            el.getAttribute('aria-label') || el.getAttribute('title') || el.innerText ||
            el.getAttribute('alt') || el.getAttribute('placeholder') || el.getAttribute('name') || ''
          ).trim();
          const controls = Array.from(document.querySelectorAll('button, input, select, textarea, a[href]'));
          const images = Array.from(document.images);
          const issues = [];
          if (!document.title.trim()) issues.push('missing document title');
          if (!document.documentElement.lang) issues.push('missing html lang');
          if (!document.querySelector('main')) issues.push('missing main landmark');
          controls.forEach((el) => {
            if (visible(el) && !nameOf(el)) issues.push(`${el.tagName.toLowerCase()} missing accessible name`);
          });
          images.forEach((el) => {
            if (visible(el) && !el.hasAttribute('alt')) issues.push('visible image missing alt text');
          });

          const candidates = Array.from(document.querySelectorAll('body *'))
            .filter(visible)
            .map((el) => ({ el, rect: el.getBoundingClientRect(), tag: el.tagName.toLowerCase(), text: nameOf(el).slice(0, 60) }))
            .filter((item) => item.rect.width * item.rect.height >= 64);
          const overlaps = [];
          for (let i = 0; i < candidates.length; i += 1) {
            for (let j = i + 1; j < candidates.length; j += 1) {
              const a = candidates[i];
              const b = candidates[j];
              if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
              const left = Math.max(a.rect.left, b.rect.left);
              const right = Math.min(a.rect.right, b.rect.right);
              const top = Math.max(a.rect.top, b.rect.top);
              const bottom = Math.min(a.rect.bottom, b.rect.bottom);
              const width = right - left;
              const height = bottom - top;
              if (width <= 1 || height <= 1) continue;
              const intersection = width * height;
              const minArea = Math.min(a.rect.width * a.rect.height, b.rect.width * b.rect.height);
              if (intersection / minArea > 0.12) {
                overlaps.push({ summary: `${a.tag} "${a.text}" overlaps ${b.tag} "${b.text}"` });
              }
              if (overlaps.length >= 25) break;
            }
            if (overlaps.length >= 25) break;
          }
          const navigation = performance.getEntriesByType('navigation')[0] || {};
          return {
            page: {
              title: document.title,
              lang: document.documentElement.lang || '',
              url: location.href,
              headings: Array.from(document.querySelectorAll('h1,h2')).map((el) => el.innerText.trim()).filter(Boolean).slice(0, 20),
              disabled_controls: controls.filter((el) => el.disabled || el.getAttribute('aria-disabled') === 'true').length,
              status_nodes: Array.from(document.querySelectorAll('[role=status], [aria-live], .status, .chip, .tag')).map((el) => el.innerText.trim()).filter(Boolean).slice(0, 30)
            },
            a11y: { issues },
            overlap: { items: overlaps },
            performance: {
              duration_ms: Math.round(navigation.duration || 0),
              dom_content_loaded_ms: Math.round(navigation.domContentLoadedEventEnd || 0),
              load_event_ms: Math.round(navigation.loadEventEnd || 0),
              dom_nodes: document.querySelectorAll('*').length
            }
          };
        }"""
    )


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Product Face Proof Result",
        "",
        f"Result: `{result['result']}`",
        f"Target: `{result['target']}`",
        f"Tool: `{result['tool_or_profile']}`",
        "",
        "## Evidence",
        "",
    ]
    lines.extend(f"- `{ref}`" for ref in result["evidence_refs"])
    lines.extend(
        [
            "",
            "## Findings",
            "",
            f"- Blocking findings: `{str(result['blocking_findings']).lower()}`",
            f"- A11y: `{result['a11y'].get('status', 'unknown')}`",
            f"- Overlap: `{result['overlap_check'].get('status', 'unknown')}`",
            f"- Console: `{result.get('console', {}).get('status', 'unknown')}`",
            f"- Performance: {result['performance_note']}",
            "",
            "## Next Action",
            "",
            result["next_action"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_product_face_proof(
    *,
    target: str,
    out: Path,
    viewports: list[Viewport] | None = None,
    states: list[str] | None = None,
    journeys: list[str] | None = None,
    strict: bool = True,
    force_fallback: bool = False,
    allow_external_file: bool = False,
    driver: Path | None = None,
    card: Path | None = None,
    reusable_for_product: bool = False,
    product_id: str | None = None,
    environment_class: str | None = None,
    approval_scope: str | None = None,
    packet_ref: str | None = None,
    packet_comparison_basis: str | None = None,
    source_promise_coverage_basis: str | None = None,
    design_fit_review_basis: str | None = None,
    project_design_system_ref: str | None = None,
    project_design_system_comparison_basis: str | None = None,
    professional_design_process_ref: str | None = None,
    professional_design_process_comparison_basis: str | None = None,
    reference_quality_ref: str | None = None,
    reference_quality_comparison_basis: str | None = None,
    compared_reference_ids: list[str] | None = None,
    reference_quality_dimensions: dict[str, str] | None = None,
    reference_comparison_artifacts: list[dict[str, Any]] | None = None,
    visual_quality_status: str | None = None,
    visual_quality_reviewer: str | None = None,
    visual_quality_basis: str | None = None,
    visual_quality_residuals: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    output_dir = out if out.suffix == "" else out.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    viewports = viewports or [Viewport(name, *size) for name, size in DEFAULT_VIEWPORTS.items()]
    state_journey_driver = load_state_journey_driver(driver)
    if state_journey_driver is None:
        states = states or ["initial-render"]
        journeys = journeys or ["open target", "inspect configured viewports"]
    else:
        states = states or []
        journeys = journeys or []
    target_url, target_path = resolve_target(target, allow_external_file=allow_external_file)
    target_ref = repo_ref(target_path) if target_path else target
    card_ref = card_ref_from_card(load_json_like(card)) if card else None

    if force_fallback:
        result = build_fallback_result(
            target_ref=target_ref,
            target_path=target_path,
            output_dir=output_dir,
            viewports=viewports,
            states=states,
            journeys=journeys,
            reason="forced fallback",
        )
        if card_ref:
            result["card_ref"] = card_ref
    else:
        try:
            result = run_playwright(
                target_url=target_url,
                target_ref=target_ref,
                output_dir=output_dir,
                viewports=viewports,
                states=states,
                journeys=journeys,
                strict=strict,
                state_journey_driver=state_journey_driver,
                card_ref=card_ref,
            )
        except PlaywrightUnavailable as exc:
            result = build_fallback_result(
                target_ref=target_ref,
                target_path=target_path,
                output_dir=output_dir,
                viewports=viewports,
                states=states,
                journeys=journeys,
                reason=str(exc),
            )
            if card_ref:
                result["card_ref"] = card_ref

    result_path = out if out.suffix else output_dir / "product-face-result.json"
    report_path = output_dir / "product-face-report.md"
    result["journeys"] = result.get("user_journeys_checked", [])
    result["accessibility"] = result.get("a11y", {})
    result["overlap"] = result.get("overlap_check", {})
    apply_product_alignment(
        result=result,
        packet_ref=packet_ref,
        packet_comparison_basis=packet_comparison_basis,
        source_promise_coverage_basis=source_promise_coverage_basis,
        design_fit_review_basis=design_fit_review_basis,
        project_design_system_ref=project_design_system_ref,
        project_design_system_comparison_basis=project_design_system_comparison_basis,
        professional_design_process_ref=professional_design_process_ref,
        professional_design_process_comparison_basis=professional_design_process_comparison_basis,
        reference_quality_ref=reference_quality_ref,
        reference_quality_comparison_basis=reference_quality_comparison_basis,
        compared_reference_ids=compared_reference_ids,
        reference_quality_dimensions=reference_quality_dimensions,
        reference_comparison_artifacts=reference_comparison_artifacts,
    )
    apply_visual_quality_review(
        result=result,
        status=visual_quality_status,
        reviewer=visual_quality_reviewer,
        basis=visual_quality_basis,
        residuals=visual_quality_residuals,
    )
    enforce_visual_quality_gate(result)
    if reusable_for_product:
        apply_product_reuse_scope(
            result=result,
            target_ref=target_ref,
            target_path=target_path,
            product_id=product_id,
            environment_class=environment_class,
            approval_scope=approval_scope,
        )
    result["evidence_refs"] = [*result["evidence_refs"], repo_ref(report_path), repo_ref(result_path)]
    profile_refs = result["evidence_refs"]
    if isinstance(result.get("surface_evidence_profile"), dict):
        result["surface_evidence_profile"]["evidence_refs"] = profile_refs
    for profile in result.get("surface_evidence_profiles") or []:
        if isinstance(profile, dict):
            profile["evidence_refs"] = profile_refs
    if result.get("result") == "WAIVED":
        result["waiver"] = build_waiver(result)
    write_json(result_path, result)
    write_report(report_path, result)
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal Product Face proof against a local HTML file or URL.")
    parser.add_argument("--target", required=True, help="Repo-relative HTML path or http(s) URL.")
    parser.add_argument("--out", default=".tmp/factory-runs/product-face/product-face-result.json", help="Output JSON path or directory.")
    parser.add_argument("--viewport", action="append", default=[], help="Viewport as NAME=WIDTHxHEIGHT. Can be repeated.")
    parser.add_argument("--state", action="append", default=[], help="Checked state label. Can be repeated.")
    parser.add_argument("--journey", action="append", default=[], help="Checked user journey label. Can be repeated.")
    parser.add_argument("--strict", action="store_true", default=True, help="Treat a11y and overlap warnings as blocking findings. Enabled by default.")
    parser.add_argument("--force-fallback", action="store_true", help="Skip Playwright and write bounded static fallback evidence.")
    parser.add_argument("--allow-external-file", action="store_true", help="Allow absolute file targets outside this repo; output is redacted.")
    parser.add_argument("--driver", type=Path, help="Product Face state/journey driver JSON for executable journeys.")
    parser.add_argument("--card", type=Path, help="Factory card to bind this Product Face result to.")
    parser.add_argument("--reusable-for-product", action="store_true", help="Mark this PASS proof reusable for the named product scope.")
    parser.add_argument("--product-id", help="Stable product id required with --reusable-for-product.")
    parser.add_argument(
        "--environment-class",
        choices=sorted(ALLOWED_PRODUCT_ENV_CLASSES),
        help="Target environment class required with --reusable-for-product.",
    )
    parser.add_argument("--approval-scope", help="Specific approval scope required with --reusable-for-product.")
    parser.add_argument("--packet-ref", help="Product Face Packet reference used for product approval alignment.")
    parser.add_argument("--packet-comparison-basis", help="Why this proof matches the Product Face Packet.")
    parser.add_argument("--source-promise-coverage-basis", help="Why this proof covers the source/product promise.")
    parser.add_argument("--design-fit-review-basis", help="Why this proof fits the intended product/design direction.")
    parser.add_argument("--project-design-system-ref", help="Project design system / DESIGN.md contract used for Product Face approval.")
    parser.add_argument("--project-design-system-comparison-basis", help="Why this proof satisfies the project design system contract.")
    parser.add_argument("--professional-design-process-ref", help="Professional Design Process packet used for Product Face approval.")
    parser.add_argument("--professional-design-process-comparison-basis", help="Why this proof satisfies the professional design process.")
    parser.add_argument("--reference-quality-ref", help="Reference research packet/set used for dimensioned Product Face comparison.")
    parser.add_argument("--reference-quality-comparison-basis", help="Why this proof matches the selected professional references.")
    parser.add_argument("--compared-reference-id", action="append", help="Reference source id used in the side-by-side comparison. Repeat at least 3 times.")
    parser.add_argument(
        "--reference-comparison-dimension",
        action="append",
        help="Dimension comparison as DIMENSION=BASIS. Required dimensions: layout_hierarchy, interaction_model, state_coverage, visual_language, density_spacing.",
    )
    parser.add_argument(
        "--reference-comparison-artifact",
        action="append",
        help="Material comparison artifact as TYPE=REF. TYPE can be side_by_side_capture, reference_snapshot, design_system_component, comparison_manifest or bounded_equivalent.",
    )
    parser.add_argument("--visual-quality-status", choices=["PASS", "BLOCK", "PASS_WITH_RESIDUALS"], help="Professional visual quality verdict.")
    parser.add_argument("--visual-quality-reviewer", help="Reviewer empowered to block visually unacceptable UI.")
    parser.add_argument("--visual-quality-basis", help="Why the surface meets or fails the product-specific quality bar.")
    parser.add_argument(
        "--visual-quality-residual",
        action="append",
        help=(
            "Bounded residual when status is PASS_WITH_RESIDUALS, as "
            "ID|SEVERITY|OWNER|EXPIRES_AT|ACCEPTED_SCOPE|PROOF_REF[,PROOF_REF]|DESCRIPTION."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        viewports = [parse_viewport(raw) for raw in args.viewport] if args.viewport else None
        reference_dimensions = {
            dimension: basis
            for dimension, basis in (
                parse_reference_dimension(raw) for raw in args.reference_comparison_dimension or []
            )
        }
        compared_ids = [str(item).strip() for item in args.compared_reference_id or [] if str(item).strip()]
        reference_artifacts = [
            parse_reference_comparison_artifact(raw, compared_ids)
            for raw in args.reference_comparison_artifact or []
        ]
        visual_quality_residuals = [
            parse_visual_quality_residual(raw)
            for raw in args.visual_quality_residual or []
        ]
        result = build_product_face_proof(
            target=args.target,
            out=Path(args.out),
            viewports=viewports,
            states=args.state or None,
            journeys=args.journey or None,
            strict=args.strict,
            force_fallback=args.force_fallback,
            allow_external_file=args.allow_external_file,
            driver=args.driver,
            card=args.card,
            reusable_for_product=args.reusable_for_product,
            product_id=args.product_id,
            environment_class=args.environment_class,
            approval_scope=args.approval_scope,
            packet_ref=args.packet_ref,
            packet_comparison_basis=args.packet_comparison_basis,
            source_promise_coverage_basis=args.source_promise_coverage_basis,
            design_fit_review_basis=args.design_fit_review_basis,
            project_design_system_ref=args.project_design_system_ref,
            project_design_system_comparison_basis=args.project_design_system_comparison_basis,
            professional_design_process_ref=args.professional_design_process_ref,
            professional_design_process_comparison_basis=args.professional_design_process_comparison_basis,
            reference_quality_ref=args.reference_quality_ref,
            reference_quality_comparison_basis=args.reference_quality_comparison_basis,
            compared_reference_ids=args.compared_reference_id,
            reference_quality_dimensions=reference_dimensions,
            reference_comparison_artifacts=reference_artifacts,
            visual_quality_status=args.visual_quality_status,
            visual_quality_reviewer=args.visual_quality_reviewer,
            visual_quality_basis=args.visual_quality_basis,
            visual_quality_residuals=visual_quality_residuals,
        )
    except Exception as exc:
        print(f"product_face_proof failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"result": result["result"], "blocking_findings": result["blocking_findings"], "evidence_refs": result["evidence_refs"]}, indent=2))
    return 1 if result["blocking_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
