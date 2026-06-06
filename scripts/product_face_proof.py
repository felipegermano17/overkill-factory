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
        "screenshots": [],
        "viewports": [viewport.label for viewport in viewports],
        "checked_states": states,
        "user_journeys_checked": journeys,
        "journeys": journeys,
        "a11y": {},
        "accessibility": {},
        "overlap_check": {},
        "overlap": {},
        "performance_note": "",
        "evidence_refs": [],
        "evidence_kind": "real",
        "reusable_for_product": False,
        "next_action": "Attach product_face_result to the completion receipt.",
    }


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
    card_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PlaywrightUnavailable("python Playwright package is not installed") from exc

    screenshots: list[str] = []
    console_messages: list[dict[str, str]] = []
    page_errors: list[str] = []
    viewport_results: dict[str, Any] = {}
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
                screenshot_path = screenshot_dir / f"{viewport.name}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                screenshots.append(repo_ref(screenshot_path))
                console_messages.extend({"viewport": viewport.name, **item} for item in page_console)
                viewport_results[viewport.name] = collect_browser_checks(page)
                context.close()
        finally:
            browser.close()

    console_path = output_dir / "console.json"
    state_path = output_dir / "state.json"
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
    result = base_result(
        target_ref=target_ref,
        viewports=viewports,
        states=states,
        journeys=journeys,
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
            "evidence_refs": [repo_ref(state_path), repo_ref(console_path), *screenshots],
            "next_action": (
                "Fix blocking browser findings and rerun Product Face proof."
                if blocking
                else "Attach product_face_result to the completion receipt."
            ),
        }
    )
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
    card: Path | None = None,
) -> dict[str, Any]:
    output_dir = out if out.suffix == "" else out.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    viewports = viewports or [Viewport(name, *size) for name, size in DEFAULT_VIEWPORTS.items()]
    states = states or ["initial-render"]
    journeys = journeys or ["open target", "inspect configured viewports"]
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
    result["evidence_refs"] = [*result["evidence_refs"], repo_ref(report_path), repo_ref(result_path)]
    if result.get("result") == "WAIVED":
        result["waiver"] = build_waiver(result)
    write_json(result_path, result)
    write_report(report_path, result)
    return result


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal Product Face proof against a local HTML file or URL.")
    parser.add_argument("--target", required=True, help="Repo-relative HTML path or http(s) URL.")
    parser.add_argument("--out", default="validation/product-face/product-face-result.json", help="Output JSON path or directory.")
    parser.add_argument("--viewport", action="append", default=[], help="Viewport as NAME=WIDTHxHEIGHT. Can be repeated.")
    parser.add_argument("--state", action="append", default=[], help="Checked state label. Can be repeated.")
    parser.add_argument("--journey", action="append", default=[], help="Checked user journey label. Can be repeated.")
    parser.add_argument("--strict", action="store_true", default=True, help="Treat a11y and overlap warnings as blocking findings. Enabled by default.")
    parser.add_argument("--force-fallback", action="store_true", help="Skip Playwright and write bounded static fallback evidence.")
    parser.add_argument("--allow-external-file", action="store_true", help="Allow absolute file targets outside this repo; output is redacted.")
    parser.add_argument("--card", type=Path, help="Factory card to bind this Product Face result to.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        viewports = [parse_viewport(raw) for raw in args.viewport] if args.viewport else None
        result = build_product_face_proof(
            target=args.target,
            out=Path(args.out),
            viewports=viewports,
            states=args.state or None,
            journeys=args.journey or None,
            strict=args.strict,
            force_fallback=args.force_fallback,
            allow_external_file=args.allow_external_file,
            card=args.card,
        )
    except Exception as exc:
        print(f"product_face_proof failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"result": result["result"], "blocking_findings": result["blocking_findings"], "evidence_refs": result["evidence_refs"]}, indent=2))
    return 1 if result["blocking_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
