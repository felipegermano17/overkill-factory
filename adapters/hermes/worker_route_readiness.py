#!/usr/bin/env python3
"""Check whether Hermes worker routes are ready to spawn real workers.

This is a conservative preflight for Overkill Factory vFinal. It does not read
or print secret values. It only checks whether each ledger worker has enough
runtime shape to be allowed out of the safe blocked state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]

PLACEHOLDER_VALUES = {
    "",
    "auto",
    "your-key-here",
    "changeme",
    "change-me",
    "none",
    "null",
}

PROVIDER_ENV_HINTS = {
    "anthropic": ["ANTHROPIC_API_KEY", "ANTHROPIC_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"],
    "openrouter": ["OPENROUTER_API_KEY", "OPENAI_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "openai-codex": [],
    "codex": [],
    "nous": [],
    "nous-api": ["NOUS_API_KEY"],
    "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "xai": ["XAI_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "together": ["TOGETHER_API_KEY"],
    "fireworks": ["FIREWORKS_API_KEY"],
    "nvidia": ["NVIDIA_API_KEY"],
    "huggingface": ["HF_TOKEN", "HUGGINGFACE_API_KEY"],
    "ollama-cloud": ["OLLAMA_API_KEY"],
    "kimi-coding": ["KIMI_API_KEY"],
    "minimax": ["MINIMAX_API_KEY"],
    "minimax-cn": ["MINIMAX_CN_API_KEY"],
    "zai": ["GLM_API_KEY"],
    "custom": ["OPENAI_API_KEY"],
    "lmstudio": [],
}

LOCAL_PROVIDERS = {"lmstudio"}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _non_placeholder(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return text.casefold() not in PLACEHOLDER_VALUES


def _is_local_base_url(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return (
        text.startswith("http://127.0.0.1")
        or text.startswith("http://localhost")
        or text.startswith("http://[::1]")
    )


def _local_endpoint_reachable(value: Any) -> bool:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((parsed.hostname, port), timeout=0.75):
            return True
    except OSError:
        return False


def _local_endpoint_model_status(value: Any, model: str) -> tuple[bool, str]:
    if not _local_endpoint_reachable(value):
        return False, "local_endpoint_unreachable"
    parsed = urlparse(str(value or "").strip())
    models_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/models"
    try:
        req = Request(models_url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace") or "{}")
    except Exception:
        return False, "local_endpoint_models_unavailable"
    candidates: set[str] = set()
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and _non_placeholder(item.get("id")):
                candidates.add(str(item["id"]).strip())
            elif _non_placeholder(item):
                candidates.add(str(item).strip())
    elif isinstance(payload, dict):
        for key in ("id", "model", "name"):
            if _non_placeholder(payload.get(key)):
                candidates.add(str(payload[key]).strip())
    if model in candidates:
        return True, "local_endpoint_model_listed"
    return False, "local_endpoint_model_missing"


def _extract_model_section_without_yaml(text: str) -> dict[str, Any]:
    """Best-effort YAML subset parser for the top-level `model:` section."""
    model: dict[str, Any] = {}
    in_model = False
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not raw_line.startswith((" ", "\t")):
            key = line.split(":", 1)[0].strip()
            in_model = key == "model"
            continue
        if not in_model:
            continue
        match = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        model[key] = value.strip().strip("'\"")
    return model


def _load_profile_config(profile_dir: Path) -> tuple[dict[str, Any], str | None]:
    config_path = profile_dir / "config.yaml"
    if not config_path.is_file():
        return {}, None
    text = config_path.read_text(encoding="utf-8", errors="replace")
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(text) or {}
        if isinstance(parsed, dict):
            return parsed, _repo_relative(config_path)
    except Exception:
        pass
    return {"model": _extract_model_section_without_yaml(text)}, _repo_relative(config_path)


def _model_value(config: dict[str, Any]) -> str:
    model_section = config.get("model") if isinstance(config.get("model"), dict) else {}
    value = model_section.get("default") or model_section.get("model") or config.get("model")
    return str(value or "").strip()


def _provider_value(config: dict[str, Any]) -> str:
    model_section = config.get("model") if isinstance(config.get("model"), dict) else {}
    value = model_section.get("provider") or config.get("provider")
    return str(value or "").strip().lower()


def _base_url_value(config: dict[str, Any]) -> str:
    model_section = config.get("model") if isinstance(config.get("model"), dict) else {}
    value = model_section.get("base_url") or config.get("base_url")
    return str(value or "").strip()


def _config_has_inline_key(config: dict[str, Any]) -> bool:
    model_section = config.get("model") if isinstance(config.get("model"), dict) else {}
    return _non_placeholder(model_section.get("api_key") or config.get("api_key"))


def _auth_file_present(profile_dir: Path, hermes_home: Path, provider: str) -> bool:
    auth_candidates = [
        profile_dir / "auth.json",
        hermes_home / "auth.json",
        hermes_home / "shared" / "nous_auth.json",
    ]
    for candidate in auth_candidates:
        if not candidate.is_file():
            continue
        if provider in {"", "auto"}:
            return True
        try:
            data = _load_json(candidate)
        except Exception:
            return True
        blob = json.dumps(data).lower()
        if provider in blob or "active_provider" in blob or "credential_pool" in blob:
            return True
    return False


def _env_hint_present(provider: str) -> list[str]:
    names = PROVIDER_ENV_HINTS.get(provider, [])
    return [name for name in names if _non_placeholder(os.environ.get(name))]


def _credential_status(
    *,
    provider: str,
    config: dict[str, Any],
    profile_dir: Path,
    hermes_home: Path,
) -> tuple[str, list[str]]:
    model = _model_value(config)
    base_url = _base_url_value(config)
    if provider in LOCAL_PROVIDERS and _is_local_base_url(base_url):
        ok, evidence = _local_endpoint_model_status(base_url, model)
        return ("pass" if ok else "fail", [evidence])
    if provider == "custom" and _is_local_base_url(base_url):
        ok, evidence = _local_endpoint_model_status(base_url, model)
        if ok:
            return "pass", ["local_custom_endpoint_model_listed"]
        return "fail", [f"local_custom_{evidence.removeprefix('local_')}"]
    if _config_has_inline_key(config):
        return "pass", ["config_api_key_present"]
    env_hits = _env_hint_present(provider)
    if env_hits:
        return "pass", [f"env:{name}" for name in env_hits]
    if _auth_file_present(profile_dir, hermes_home, provider):
        return "pass", ["auth_store_present"]
    if provider in {"", "auto"}:
        return "fail", ["provider_auto_without_detectable_auth"]
    return "fail", ["no_detectable_auth_or_local_endpoint"]


def _extract_tasks(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    raw_tasks = ledger.get("tasks")
    if isinstance(raw_tasks, dict):
        return [task for task in raw_tasks.values() if isinstance(task, dict)]
    if isinstance(raw_tasks, list):
        return [task for task in raw_tasks if isinstance(task, dict)]
    return []


def _profile_dir(hermes_home: Path, worker_id: str) -> Path:
    if worker_id == "default":
        return hermes_home
    return hermes_home / "profiles" / worker_id


def check_readiness(
    *,
    ledger_path: Path,
    hermes_home: Path,
    require_credentials: bool = True,
) -> dict[str, Any]:
    ledger = _load_json(ledger_path)
    tasks = _extract_tasks(ledger)
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    for task in sorted(tasks, key=lambda item: str(item.get("worker_id") or "")):
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id:
            continue
        profile_dir = _profile_dir(hermes_home, worker_id)
        profile_exists = profile_dir.is_dir()
        config, config_ref = _load_profile_config(profile_dir) if profile_exists else ({}, None)
        provider = _provider_value(config)
        model = _model_value(config)
        model_ok = _non_placeholder(model)
        provider_ok = _non_placeholder(provider)
        credential_status, credential_evidence = (
            _credential_status(
                provider=provider,
                config=config,
                profile_dir=profile_dir,
                hermes_home=hermes_home,
            )
            if profile_exists and config
            else ("fail", ["profile_or_config_missing"])
        )

        reasons: list[str] = []
        if not profile_exists:
            reasons.append("profile_missing")
        if profile_exists and not config_ref:
            reasons.append("config_missing")
        if config_ref and not model_ok:
            reasons.append("model_missing")
        if config_ref and not provider_ok:
            reasons.append("provider_missing")
        if require_credentials and credential_status != "pass":
            reasons.extend(credential_evidence)

        status = "ready" if not reasons else "blocked"
        if status == "blocked":
            blockers.append(worker_id)
        checks.append(
            {
                "worker_id": worker_id,
                "task_id": str(task.get("task_id") or ""),
                "required_before": task.get("required_before"),
                "queue_class": task.get("queue_class"),
                "status": status,
                "profile_exists": profile_exists,
                "config_ref": config_ref,
                "model_configured": model_ok,
                "provider_configured": provider_ok,
                "credential_status": credential_status,
                "credential_evidence": credential_evidence,
                "blocked_reasons": reasons,
            }
        )

    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-worker-route-readiness.schema.json",
        "schema": "overkill_factory_hermes_worker_route_readiness.v1",
        "ledger_ref": _repo_relative(ledger_path),
        "hermes_home_ref": "redacted-hermes-home",
        "result": "PASS" if not blockers else "BLOCKED",
        "worker_count": len(checks),
        "blocked_worker_count": len(blockers),
        "blocked_workers": blockers,
        "checks": checks,
        "production_rule": (
            "Do not set OVERKILL_FACTORY_WORKER_TASK_STATUS=ready in production "
            "while result is BLOCKED."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    env_hermes_home = os.environ.get("HERMES_HOME")
    parser.add_argument("--hermes-home", type=Path, default=Path(env_hermes_home) if env_hermes_home else None)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--no-require-credentials",
        action="store_true",
        help="Only check profile/config shape; do not require auth/reachable local endpoint evidence.",
    )
    args = parser.parse_args(argv)

    if args.hermes_home is None:
        raise SystemExit("--hermes-home is required when HERMES_HOME is not set")
    receipt = check_readiness(
        ledger_path=args.ledger.expanduser().resolve(),
        hermes_home=args.hermes_home.expanduser().resolve(),
        require_credentials=not args.no_require_credentials,
    )
    if args.out:
        out = args.out
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
