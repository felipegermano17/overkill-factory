#!/usr/bin/env python3
"""Build and test a product-like Quasar target in a clean Docker container."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
QUASAR_SOURCE = "github:blueshift-gg/quasar"
QUASAR_SOURCE_REPOSITORY = "https://github.com/blueshift-gg/quasar.git"
QUASAR_SOURCE_HEAD = "a89a9329f05740a20520607608b2b3b78c74f7c4"
QUASAR_SOURCE_REF = QUASAR_SOURCE_HEAD
RUST_CONTAINER_IMAGE = "rust:1.91.0-bookworm@sha256:e187887ec511b3d93e45c0231d2f0fd59f1347526c58aa86343aa83c74f3e1a9"
SOLANA_RELEASE = "v4.0.2"
SOLANA_INSTALL_URL = f"https://release.anza.xyz/{SOLANA_RELEASE}/install"
PUBLIC_QVG_SOURCE_DIR = ROOT / "products" / "qvg-public-validation-product" / "onchain" / "quasar" / "src"
PROJECT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def redact_text(text: str, source_dir: Path, work_dir: Path) -> str:
    redacted = text
    replacements = {
        str(ROOT): "<repo-root>",
        str(ROOT).replace("\\", "/"): "<repo-root>",
        str(source_dir): "<source-dir>",
        str(source_dir).replace("\\", "/"): "<source-dir>",
        str(work_dir): "<work-dir>",
        str(work_dir).replace("\\", "/"): "<work-dir>",
        "/tmp/quasar": "<container-quasar-src>",
        "/tmp/qvg-product-like": "<container-project>",
    }
    for before, after in replacements.items():
        redacted = redacted.replace(before, after)
    redacted = re.sub(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s\"')<]+", "<redacted-local-path>", redacted)
    redacted = re.sub(r"/(?:Users|home|srv|tmp)/[^\s\"')<]+", "<redacted-local-path>", redacted)
    return redacted


def sha256_sources(source_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(source_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(source_dir).as_posix()
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def read_marker(work_dir: Path, name: str) -> str:
    path = work_dir / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def docker_script(project_name: str) -> str:
    return f"""set -eux
export DEBIAN_FRONTEND=noninteractive
readonly SOLANA_INSTALL_URL="{SOLANA_INSTALL_URL}"
readonly QUASAR_SOURCE_REPOSITORY="{QUASAR_SOURCE_REPOSITORY}"
readonly QUASAR_SOURCE_REF="{QUASAR_SOURCE_REF}"
readonly QUASAR_SOURCE_HEAD="{QUASAR_SOURCE_HEAD}"
apt-get update
apt-get install -y --no-install-recommends git ca-certificates curl pkg-config libssl-dev perl make clang llvm-dev libclang-dev protobuf-compiler
cd /tmp
curl -sSfL "$SOLANA_INSTALL_URL" | sh
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
solana --version | tee /out/solana.txt
git init /tmp/quasar
cd /tmp/quasar
git remote add origin "$QUASAR_SOURCE_REPOSITORY"
git fetch --depth 1 origin "$QUASAR_SOURCE_REF"
git checkout --detach FETCH_HEAD
resolved_quasar_head="$(git rev-parse HEAD)"
printf '%s\\n' "$QUASAR_SOURCE_REF" | tee /out/quasar_ref.txt
printf '%s\\n' "$QUASAR_SOURCE_HEAD" | tee /out/quasar_expected_head.txt
printf '%s\\n' "$resolved_quasar_head" | tee /out/quasar_head.txt
test "$resolved_quasar_head" = "$QUASAR_SOURCE_HEAD"
cargo install --path cli --locked
cd /tmp
quasar init {project_name} --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git --verbose
rm -rf /tmp/{project_name}/src
mkdir -p /tmp/{project_name}/src
cp -R /repo-src/. /tmp/{project_name}/src/
cd /tmp/{project_name}
find src -maxdepth 3 -type f | sort > /out/source_files.txt
quasar build
printf PASS > /out/build_status.txt
quasar test
printf PASS > /out/test_status.txt
rustc --version | tee /out/rustc.txt
cargo --version | tee /out/cargo.txt
quasar --version | tee /out/quasar.txt
"""


def run_container(source_dir: Path, work_dir: Path, timeout: int, project_name: str) -> subprocess.CompletedProcess[str]:
    script = work_dir / "run-quasar-proof.sh"
    script.write_text(docker_script(project_name), encoding="utf-8")
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{source_dir.resolve()}:/repo-src:ro",
        "-v",
        f"{work_dir.resolve()}:/out",
        RUST_CONTAINER_IMAGE,
        "bash",
        "/out/run-quasar-proof.sh",
    ]
    return subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)


def build_result(
    *,
    source_dir: Path,
    out: Path,
    work_dir: Path,
    completed: subprocess.CompletedProcess[str],
    started_at: str,
    ended_at: str,
    project_name: str,
    proof_kind: str,
    evidence_boundary: str,
    policy_decision: str,
) -> dict[str, Any]:
    build_status = read_marker(work_dir, "build_status.txt")
    test_status = read_marker(work_dir, "test_status.txt")
    quasar_source_head = read_marker(work_dir, "quasar_head.txt")
    source_head_matches = quasar_source_head == QUASAR_SOURCE_HEAD
    result = (
        "PASS"
        if completed.returncode == 0 and build_status == "PASS" and test_status == "PASS" and source_head_matches
        else "FAIL"
    )
    source_files = [
        repo_ref(path)
        for path in sorted(source_dir.rglob("*"))
        if path.is_file()
    ]
    stdout_tail = redact_text(completed.stdout[-6000:], source_dir, work_dir)
    stderr_tail = redact_text(completed.stderr[-6000:], source_dir, work_dir)
    return {
        "$schema": "https://overkill-factory.dev/schemas/quasar-runtime-proof.schema.json",
        "result": result,
        "proof_kind": proof_kind,
        "created_at": ended_at,
        "started_at": started_at,
        "source_target": repo_ref(source_dir),
        "source_files": source_files,
        "source_sha256": sha256_sources(source_dir),
        "install_source": QUASAR_SOURCE,
        "source_ref": read_marker(work_dir, "quasar_ref.txt") or QUASAR_SOURCE_REF,
        "source_head_expected": QUASAR_SOURCE_HEAD,
        "source_head": quasar_source_head,
        "source_head_matches": source_head_matches,
        "container_image": RUST_CONTAINER_IMAGE,
        "solana_release": SOLANA_RELEASE,
        "solana_install_url": SOLANA_INSTALL_URL,
        "rustc": read_marker(work_dir, "rustc.txt"),
        "cargo": read_marker(work_dir, "cargo.txt"),
        "solana": read_marker(work_dir, "solana.txt"),
        "quasar": read_marker(work_dir, "quasar.txt"),
        "init_command": f"quasar init {project_name} --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git --verbose",
        "build_command": "quasar build",
        "build_status": build_status or "FAIL",
        "test_command": "quasar test",
        "test_status": test_status or "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "evidence_boundary": evidence_boundary,
        "policy_decision": policy_decision,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run product-like Quasar build/test proof in Docker.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=PUBLIC_QVG_SOURCE_DIR,
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".tmp" / "factory-runs" / "quasar-product-like-proof" / "qvg-quasar-runtime-proof.json",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--project-name", default="qvg-public-validation-product")
    parser.add_argument("--proof-kind", default="containerized_product_like_quasar_build_test")
    parser.add_argument(
        "--evidence-boundary",
        default=(
            "Proves a public product-like QVG Quasar target can build and test in a clean Docker container. "
            "It does not prove production safety, deploy readiness, funds handling or mainnet/devnet authority."
        ),
    )
    parser.add_argument(
        "--policy-decision",
        default="Use this product-like proof as stronger Auditor input than generated-minimal Quasar proof, while keeping production promotion gated.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir = args.source_dir if args.source_dir.is_absolute() else ROOT / args.source_dir
    source_dir = source_dir.resolve()
    if not source_dir.exists():
        raise SystemExit(f"source dir does not exist: {repo_ref(source_dir)}")
    if not PROJECT_NAME_RE.fullmatch(args.project_name):
        raise SystemExit("--project-name must be 3-64 chars of lowercase letters, numbers or hyphens")
    out = args.out if args.out.is_absolute() else ROOT / args.out
    started_at = utc_now()
    with tempfile.TemporaryDirectory(prefix="of-quasar-product-like-") as tmp:
        work_dir = Path(tmp)
        completed = run_container(source_dir, work_dir, args.timeout_seconds, args.project_name)
        ended_at = utc_now()
        result = build_result(
            source_dir=source_dir,
            out=out,
            work_dir=work_dir,
            completed=completed,
            started_at=started_at,
            ended_at=ended_at,
            project_name=args.project_name,
            proof_kind=args.proof_kind,
            evidence_boundary=args.evidence_boundary,
            policy_decision=args.policy_decision,
        )
    write_json(out, result)
    print(json.dumps({"result": result["result"], "out": repo_ref(out), "returncode": result["returncode"]}, indent=2))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
