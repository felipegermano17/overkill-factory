#!/usr/bin/env python3
"""Safe subprocess helper for factory worker packets.

The helper only accepts argv lists. It is intentionally small so worker packets
can cite it when a shell string, heredoc, pipe, or sandbox-specific launcher
would make evidence ambiguous.
"""

from __future__ import annotations

import subprocess  # nosec B404
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SafeCommandResult:
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    remediation: str | None = None


def run_command(
    argv: list[str],
    *,
    cwd: Path,
    timeout_seconds: int = 120,
    allowed_executables: set[str] | None = None,
) -> SafeCommandResult:
    if not argv or not all(isinstance(part, str) and part.strip() for part in argv):
        raise ValueError("argv must be a non-empty list of non-empty strings")
    executable = Path(argv[0]).name.lower()
    if allowed_executables is not None and executable not in {item.lower() for item in allowed_executables}:
        raise ValueError(f"executable is not allowed for this worker packet: {argv[0]}")
    try:
        completed = subprocess.run(  # nosec B603
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except OSError as exc:
        message = str(exc)
        if "CreateProcessAsUserW failed: 5" in message:
            return SafeCommandResult(
                status="BLOCKED",
                returncode=None,
                stdout="",
                stderr=message,
                remediation="Use the operator-approved fallback runner or rerun the same argv on an authorized local shell.",
            )
        raise
    except subprocess.TimeoutExpired as exc:
        return SafeCommandResult(
            status="BLOCKED",
            returncode=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            remediation="Increase timeout only after checking the command is expected to run longer.",
        )
    return SafeCommandResult(
        status="PASS" if completed.returncode == 0 else "BLOCKED",
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        remediation=None if completed.returncode == 0 else "Inspect stderr and rerun after fixing the blocking condition.",
    )
