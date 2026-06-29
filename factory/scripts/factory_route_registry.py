"""Canonical route registry for Overkill Factory public contracts."""

from __future__ import annotations

import json
import sysconfig
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROUTE_REGISTRY_PATH = ROOT / "templates" / "factory-route-registry.json"


def route_registry_candidates() -> list[Path]:
    data_root = Path(sysconfig.get_path("data") or "")
    return [
        DEFAULT_ROUTE_REGISTRY_PATH,
        ROOT / "share" / "overkill-factory" / "templates" / "factory-route-registry.json",
        data_root / "share" / "overkill-factory" / "templates" / "factory-route-registry.json",
    ]


def load_route_registry(path: Path | None = None) -> dict[str, Any]:
    if path is not None:
        registry_path = path
    else:
        registry_path = next(
            (candidate for candidate in route_registry_candidates() if candidate.exists()),
            DEFAULT_ROUTE_REGISTRY_PATH,
        )
    return json.loads(registry_path.read_text(encoding="utf-8"))


def registry_routes(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = registry or load_route_registry()
    routes = data.get("routes") if isinstance(data.get("routes"), list) else []
    return {
        str(route.get("route_class")): route
        for route in routes
        if isinstance(route, dict) and str(route.get("route_class") or "").strip()
    }


def route_required_artifacts(registry: dict[str, Any] | None = None) -> dict[str, set[str]]:
    return {
        route_class: {
            str(item)
            for item in route.get("required_artifacts", [])
            if str(item).strip()
        }
        for route_class, route in registry_routes(registry).items()
    }


def route_request_types(registry: dict[str, Any] | None = None) -> dict[str, set[str]]:
    return {
        route_class: {
            str(item)
            for item in route.get("request_types", [])
            if str(item).strip()
        }
        for route_class, route in registry_routes(registry).items()
    }


def route_signal_types(registry: dict[str, Any] | None = None) -> dict[str, set[str]]:
    return {
        route_class: {
            str(item)
            for item in route.get("signal_types", [])
            if str(item).strip()
        }
        for route_class, route in registry_routes(registry).items()
    }


def route_method_families(registry: dict[str, Any] | None = None) -> dict[str, str]:
    return {
        route_class: str(route.get("selected_method_family") or "")
        for route_class, route in registry_routes(registry).items()
    }


def route_required_gates(registry: dict[str, Any] | None = None) -> dict[str, list[str]]:
    return {
        route_class: [str(item) for item in route.get("required_gates", []) if str(item).strip()]
        for route_class, route in registry_routes(registry).items()
    }


def route_required_workers(registry: dict[str, Any] | None = None) -> dict[str, list[str]]:
    return {
        route_class: [str(item) for item in route.get("required_workers", []) if str(item).strip()]
        for route_class, route in registry_routes(registry).items()
    }
