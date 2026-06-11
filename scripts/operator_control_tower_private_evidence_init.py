#!/usr/bin/env python3
"""Initialize a private Operator Control Tower evidence bundle.

This creates the private JSON files expected by
operator_control_tower_proof.py and the owner setup doctor. It refuses to write inside the public
repository and intentionally leaves placeholder values that the doctor will
block until replaced with real cockpit/runtime evidence.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def write_json(path: Path, data: dict[str, Any], *, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path.name} already exists; rerun with --force to overwrite")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def mapping_template(created_at: str) -> dict[str, Any]:
    data = json.loads((TEMPLATES / "discord-control-tower-mapping.json").read_text(encoding="utf-8"))
    data.update(
        {
            "project_id": "todo",
            "runtime": "hermes",
            "board_ref": "todo",
            "guild_ref": "todo",
            "dashboard_channel_ref": "todo",
            "dashboard_message_ref": "todo",
            "approval_channel_ref": "todo",
            "project_thread_ref": "todo",
            "evidence_channel_ref": "todo",
            "bot_health_channel_ref": "todo",
            "last_synced_at": created_at,
        }
    )
    return data


def owner_setup_template(created_at: str) -> dict[str, Any]:
    data = json.loads((TEMPLATES / "discord-control-tower-owner-setup.json").read_text(encoding="utf-8"))
    data.update(
        {
            "created_at": created_at,
            "result": "BLOCKED",
            "project_id": "todo",
            "checks": {
                "server_exists": False,
                "bot_application_created": False,
                "bot_invited_to_server": False,
                "message_content_intent_enabled": False,
                "server_members_intent_enabled": False,
                "owner_user_allowlisted": False,
                "required_channels_exist": False,
                "owner_approval_channel_restricted": False,
                "bot_health_channel_available": False,
                "least_privilege_permissions_reviewed": False,
                "token_stored_outside_public_repo": True,
                "offboarding_plan_ready": False,
            },
            "required_channels": {
                "dashboard": "todo",
                "intake": "todo",
                "owner_approvals": "todo",
                "access_requests": "todo",
                "blockers": "todo",
                "evidence_feed": "todo",
                "release_room": "todo",
                "bot_health": "todo",
                "projects_area": "todo",
            },
            "evidence_refs": ["todo"],
            "limits": [
                "Private placeholder. Replace with real Discord owner setup evidence before running the owner setup doctor."
            ],
        }
    )
    return data


def runtime_event_template(created_at: str) -> dict[str, Any]:
    data = json.loads((TEMPLATES / "control-tower-event.json").read_text(encoding="utf-8"))
    data.update(
        {
            "event_id": "todo",
            "event_type": "approval_recorded",
            "severity": "P2",
            "project_id": "todo",
            "task_id": "todo",
            "source": "bridge",
            "summary": "Replace this with the real owner approval registered in the runtime.",
            "details": "Placeholder only. The private evidence doctor must remain blocked until this file is filled from real evidence.",
            "action_required": False,
            "owner_role": "Factory Owner",
            "evidence_refs": ["todo"],
            "discord_target": "todo",
            "created_at": created_at,
        }
    )
    return data


def bridge_health_template(created_at: str) -> dict[str, Any]:
    data = json.loads((TEMPLATES / "operator-control-tower-bridge-health.json").read_text(encoding="utf-8"))
    data.update(
        {
            "created_at": created_at,
            "result": "BLOCKED",
            "checks": {
                "bot_reachable": False,
                "bridge_reachable": False,
                "runtime_readback_reachable": False,
                "approval_registration_path_reachable": False,
                "no_discord_source_of_truth": True,
                "no_private_material_in_public_receipt": True,
            },
            "evidence_refs": ["todo"],
            "limits": [
                "Private placeholder. Replace with real bridge-health evidence before running the production proof."
            ],
        }
    )
    return data


def readme_text() -> str:
    return """# Operator Control Tower Private Evidence

This folder is intentionally outside the public repository.

Fill these files from the real cockpit/runtime evidence:

- `discord-owner-setup.json`
- `discord-control-tower-mapping.json`
- `runtime-approval-event.json`
- `bridge-health.json`

First run:

```bash
python scripts/operator_control_tower_owner_setup_doctor.py \
  --owner-setup <this-folder>/discord-owner-setup.json
```

Then run:

```bash
python scripts/operator_control_tower_private_evidence_doctor.py \\
  --mapping <this-folder>/discord-control-tower-mapping.json \\
  --runtime-registration-event <this-folder>/runtime-approval-event.json \\
  --bridge-health <this-folder>/bridge-health.json
```

Only after the doctor passes, run `scripts/operator_control_tower_proof.py`.
"""


def init_bundle(out_dir: Path, *, force: bool = False, created_at: str | None = None) -> dict[str, Any]:
    if is_inside_repo(out_dir):
        raise ValueError("private evidence bundle must be outside the public repository")
    timestamp = created_at or utc_now()
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "discord-owner-setup.json", owner_setup_template(timestamp), force=force)
    write_json(out_dir / "discord-control-tower-mapping.json", mapping_template(timestamp), force=force)
    write_json(out_dir / "runtime-approval-event.json", runtime_event_template(timestamp), force=force)
    write_json(out_dir / "bridge-health.json", bridge_health_template(timestamp), force=force)
    readme = out_dir / "README.md"
    if readme.exists() and not force:
        raise FileExistsError("README.md already exists; rerun with --force to overwrite")
    readme.write_text(readme_text(), encoding="utf-8")

    return {
        "result": "initialized",
        "files": [
            "discord-owner-setup.json",
            "discord-control-tower-mapping.json",
            "runtime-approval-event.json",
            "bridge-health.json",
            "README.md",
        ],
        "doctor_expected_result_before_real_values": "BLOCKED",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = init_bundle(args.out_dir, force=args.force)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
