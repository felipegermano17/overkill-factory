#!/usr/bin/env python3
"""Render a human gate decision package to an operator-readable fallback.

The production path may attach a PDF renderer later, but this script already
creates the required Telegram/Desktop-safe artifact-first fallback from the same
schema-backed package. It refuses raw JSON-only gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "templates" / "human-gate-decision-package.json"
DEFAULT_OUT = ROOT / ".tmp" / "human-gate-decision-package.txt"
DEFAULT_PDF_OUT = ROOT / ".tmp" / "human-gate-decision-package.pdf"


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _latin1(text: str) -> str:
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_simple_pdf(text: str, path: Path) -> None:
    """Write a small valid PDF without third-party dependencies.

    It is intentionally plain: artifact-first human gates need a portable PDF
    attachment plus a text fallback, not layout magic. Long text is paginated.
    """
    lines = [_latin1(line[:96]) for line in text.splitlines()]
    pages: list[list[str]] = []
    chunk: list[str] = []
    for line in lines:
        chunk.append(line)
        if len(chunk) >= 42:
            pages.append(chunk)
            chunk = []
    if chunk or not pages:
        pages.append(chunk)

    objects: list[bytes] = [b""]
    page_object_ids: list[int] = []
    content_object_ids: list[int] = []
    for page_lines in pages:
        content_lines = ["BT", "/F1 11 Tf", "50 780 Td", "14 TL"]
        first = True
        for line in page_lines:
            if first:
                content_lines.append(f"({_pdf_escape(line)}) Tj")
                first = False
            else:
                content_lines.append(f"T* ({_pdf_escape(line)}) Tj")
        content_lines.append("ET")
        stream = "\n".join(content_lines).encode("latin-1", errors="replace")
        content_id = len(objects)
        objects.append(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
        page_id = len(objects)
        objects.append(b"")
        content_object_ids.append(content_id)
        page_object_ids.append(page_id)
    pages_id = len(objects)
    kids = " ".join(f"{pid} 0 R" for pid in page_object_ids)
    objects.append(f"<< /Type /Pages /Count {len(page_object_ids)} /Kids [{kids}] >>".encode("ascii"))
    catalog_id = len(objects)
    objects.append(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))
    font_id = len(objects)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for page_id, content_id in zip(page_object_ids, content_object_ids):
        objects[page_id] = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj_id in range(1, len(objects)):
        offsets.append(len(out))
        out.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        out.extend(objects[obj_id])
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def render(package: dict) -> str:
    options = package.get("options", [])
    lines = [
        "DECISÃO HUMANA NECESSÁRIA",
        "",
        package["executive_summary"],
        "",
        "Contexto:",
        package["context"],
        "",
        "Decisão pedida:",
        package["decision_requested"],
        "",
        "Opções:",
    ]
    for option in options:
        lines.append(f"- {option['label']}: {option['consequence']} Próximo passo: {option['next_action']}")
    lines.extend([
        "",
        "Escopo aprovado:",
        *[f"- {item}" for item in package.get("approved_scope", [])],
        "",
        "Escopo proibido:",
        *[f"- {item}" for item in package.get("forbidden_scope", [])],
        "",
        "Próxima ação segura:",
        package["next_safe_action"],
        "",
        "Fallback Telegram:",
        package["telegram_fallback"],
    ])
    return "\n".join(lines) + "\n"


def validate(package: dict) -> list[str]:
    errors: list[str] = []
    if package.get("record_type") != "human_gate_decision_package":
        errors.append("record_type must be human_gate_decision_package")
    if package.get("operator_language") != "pt-BR-simple":
        errors.append("operator language must be pt-BR-simple")
    if len(package.get("options", [])) < 2:
        errors.append("at least two options are required")
    for key in ("executive_summary", "context", "decision_requested", "next_safe_action", "telegram_fallback"):
        if len(str(package.get(key, "")).strip()) < 10:
            errors.append(f"{key} is missing or too short")
    if package.get("delivery_receipt_required") is not True:
        errors.append("delivery receipt is required")
    raw = json.dumps(package, ensure_ascii=False).lower()
    if "approve?" in raw or "aprova?" in raw:
        errors.append("approval-first prompt detected")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--pdf-out", type=Path, default=DEFAULT_PDF_OUT)
    parser.add_argument("--no-pdf", action="store_true", help="Write only the text fallback.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    package = json.loads(args.package.read_text())
    errors = validate(package)
    if errors:
        for error in errors:
            print(error)
        print("FAIL")
        return 1
    if not args.check:
        rendered = render(package)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered)
        print(f"Wrote {args.out}")
        if not args.no_pdf:
            write_simple_pdf(rendered, args.pdf_out)
            print(f"Wrote {args.pdf_out}")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
