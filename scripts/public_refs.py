"""Public-safe reference helpers for generated factory artifacts."""

from __future__ import annotations

import re
from typing import Any


PUBLIC_SAFE_KANBAN_REF = "kanban:<redacted>"
PRIVATE_KANBAN_TASK_MARKER_PATTERN = r"\bt_(?:[A-Fa-f0-9]{8,}|(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9][A-Za-z0-9_-]{5,})\b"
PRIVATE_KANBAN_TASK_MARKER_RE = re.compile(PRIVATE_KANBAN_TASK_MARKER_PATTERN)
PRIVATE_KANBAN_TASK_MARKER_BYTES_RE = re.compile(PRIVATE_KANBAN_TASK_MARKER_PATTERN.encode("ascii"))


def public_safe_kanban_ref(value: str | None) -> str | None:
    if value is None:
        return None
    return PRIVATE_KANBAN_TASK_MARKER_RE.sub(PUBLIC_SAFE_KANBAN_REF, value)


def contains_private_kanban_task_marker(value: Any) -> bool:
    return PRIVATE_KANBAN_TASK_MARKER_RE.search(str(value or "")) is not None


def sanitize_public_refs(value: Any) -> Any:
    if isinstance(value, str):
        return public_safe_kanban_ref(value)
    if isinstance(value, list):
        return [sanitize_public_refs(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_public_refs(item) for key, item in value.items()}
    return value
