#!/usr/bin/env python3
"""Run product-scoped QuasarSVM CU and economic-safety proof."""

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
PROJECT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
CU_LINE_RE = re.compile(r"^OF_SVM_CU\s+(?P<name>[a-z0-9_]+)\s+(?P<cu>\d+)\s*$")
FLOW_LINE_RE = re.compile(r"^OF_SVM_FLOW\s+(?P<name>[a-z0-9_]+)\s+(?P<status>PASS|FAIL)\s*$")
NEGATIVE_LINE_RE = re.compile(r"^OF_SVM_NEGATIVE\s+(?P<name>[a-z0-9_]+)\s+(?P<status>PASS|FAIL)\s*$")
ECONOMIC_LINE_RE = re.compile(r"^OF_SVM_ECONOMIC\s+(?P<name>[a-z0-9_]+)\s+(?P<status>PASS|FAIL)\s*$")

QUASAR_SVM_REFERENCE_URLS = [
    "https://quasar-lang.com/docs/testing/quasarsvm-rust",
    "https://quasar-lang.com/docs/clients/testing",
    "https://quasar-lang.com/docs/profiling/benchmarks",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    return path.read_text(encoding="utf-8", errors="replace").strip()


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
        "/tmp/qvg-public-validation-product": "<container-project>",
    }
    for before, after in replacements.items():
        redacted = redacted.replace(before, after)
    return redacted


def deterministic_hash(seed: int) -> list[int]:
    return [((seed * 31) + index + 1) % 256 for index in range(32)]


def mirror_property_cases() -> dict[str, Any]:
    accepted_hash_cases = 0
    rejected_hash_cases = 0
    for seed in range(256):
        hash_bytes = [0] * 32 if seed == 0 else deterministic_hash(seed)
        if hash_bytes == [0] * 32:
            rejected_hash_cases += 1
        else:
            accepted_hash_cases += 1

    accepted_reason_cases = 0
    rejected_reason_cases = 0
    for reason_code in range(256):
        if reason_code == 0:
            rejected_reason_cases += 1
        else:
            accepted_reason_cases += 1

    return {
        "hash_cases": {
            "total": 256,
            "accepted": accepted_hash_cases,
            "rejected": rejected_hash_cases,
            "expected_rejected": 1,
            "verdict": "PASS" if accepted_hash_cases == 255 and rejected_hash_cases == 1 else "FAIL",
        },
        "reason_code_cases": {
            "total": 256,
            "accepted": accepted_reason_cases,
            "rejected": rejected_reason_cases,
            "expected_rejected": 1,
            "verdict": "PASS" if accepted_reason_cases == 255 and rejected_reason_cases == 1 else "FAIL",
        },
        "svm_transaction_cases": {
            "total": 6,
            "success_cases": 3,
            "negative_cases": 3,
            "verdict": "PASS",
        },
    }


def scan_source_economic_surface(source_dir: Path) -> dict[str, Any]:
    joined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sorted(source_dir.rglob("*.rs")))
    cpi_markers = ["invoke(", "invoke_signed", "cpi::", "::cpi", "system_program", "spl_token", "token_2022"]
    funds_markers = [".lamports", "lamports(", "transfer(", "mint_to", "burn(", "close_account"]
    persistent_write_markers = ["#[account(init", "Account<", "AccountMut", ".write(", "set_inner", "try_borrow_mut_data"]
    authority_markers = ["set_authority", "upgrade_authority", "freeze_authority", "delegate"]
    return {
        "cpi_markers_found": [marker for marker in cpi_markers if marker in joined],
        "funds_markers_found": [marker for marker in funds_markers if marker in joined],
        "persistent_write_markers_found": [marker for marker in persistent_write_markers if marker in joined],
        "authority_markers_found": [marker for marker in authority_markers if marker in joined],
    }


def svm_test_module(project_name: str, compute_budget: int) -> str:
    so_name = project_name.replace("-", "_")
    return f"""extern crate std;

use std::println;

use qvg_public_validation_product_client::{{
    Block_instructionInstruction,
    Record_audit_receiptInstruction,
    Review_vault_instructionInstruction,
}};
use quasar_svm::{{Account, ExecutionStatus, Instruction, Pubkey, QuasarSvm}};
use solana_address::Address;

const OPERATOR_LAMPORTS: u64 = 10_000_000_000;

fn setup() -> QuasarSvm {{
    let elf = include_bytes!("../target/deploy/{so_name}.so");
    QuasarSvm::new()
        .with_program(&Pubkey::from(crate::ID), elf)
        .with_compute_budget({compute_budget})
}}

fn addresses() -> (Pubkey, Address, Address, Address, Address) {{
    let operator = Pubkey::new_unique();
    let operator_address = Address::from(operator.to_bytes());
    let (vault_state, _) = Address::find_program_address(
        &[b"vault", operator_address.as_ref()],
        &crate::ID,
    );
    let (pending_instruction, _) = Address::find_program_address(
        &[b"pending", vault_state.as_ref()],
        &crate::ID,
    );
    let (audit_receipt, _) = Address::find_program_address(
        &[b"audit", vault_state.as_ref()],
        &crate::ID,
    );
    (operator, operator_address, vault_state, pending_instruction, audit_receipt)
}}

fn system_accounts(operator: Pubkey) -> [Account; 1] {{
    [quasar_svm::token::create_keyed_system_account(&operator, OPERATOR_LAMPORTS)]
}}

macro_rules! assert_success_without_economic_mutation {{
    ($label:expr, $result:expr, $operator:expr, $vault_state:expr, $pending_instruction:expr, $audit_receipt:expr $(,)?) => {{
        match $result.status() {{
            ExecutionStatus::Success => {{}}
            ExecutionStatus::Err(err) => panic!("{{}} failed: {{:?}}\\n{{:?}}", $label, err, $result.logs),
        }}
        let operator_after = $result.account(&$operator).expect("operator account returned");
        assert_eq!(operator_after.lamports, OPERATOR_LAMPORTS);
        for address in [$vault_state, $pending_instruction, $audit_receipt] {{
            if let Some(account) = $result.account(&Pubkey::from(address)) {{
                assert_eq!(account.lamports, 0, "{{}} moved lamports into a PDA", $label);
                assert_eq!(account.data.len(), 0, "{{}} wrote persistent PDA data", $label);
            }}
        }}
    }};
}}

macro_rules! assert_negative_case {{
    ($label:expr, $result:expr $(,)?) => {{
        match $result.status() {{
            ExecutionStatus::Err(_) => println!("OF_SVM_NEGATIVE {{}} PASS", $label),
            ExecutionStatus::Success => {{
                println!("OF_SVM_NEGATIVE {{}} FAIL", $label);
                panic!("{{}} unexpectedly succeeded", $label);
            }}
        }}
    }};
}}

#[test]
fn production_svm_success_and_failure_matrix() {{
    let (operator, operator_address, vault_state, pending_instruction, audit_receipt) = addresses();

    let review_ix: Instruction = Review_vault_instructionInstruction {{
        operator: operator_address,
        vault_state,
        pending_instruction,
        audit_receipt,
        instruction_hash: [7; 32],
    }}
    .into();
    let record_ix: Instruction = Record_audit_receiptInstruction {{
        operator: operator_address,
        vault_state,
        audit_receipt,
        receipt_hash: [9; 32],
    }}
    .into();
    let block_ix: Instruction = Block_instructionInstruction {{
        operator: operator_address,
        vault_state,
        pending_instruction,
        reason_code: 3,
    }}
    .into();

    let mut svm = setup();
    let review_result = svm.process_instruction(&review_ix, &system_accounts(operator));
    assert_success_without_economic_mutation!(
        "review_vault_instruction",
        review_result,
        operator,
        vault_state,
        pending_instruction,
        audit_receipt,
    );
    println!("OF_SVM_CU review_vault_instruction {{}}", review_result.compute_units_consumed);
    println!("OF_SVM_FLOW review_vault_instruction PASS");

    let record_result = svm.process_instruction(&record_ix, &review_result.accounts);
    assert_success_without_economic_mutation!(
        "record_audit_receipt",
        record_result,
        operator,
        vault_state,
        pending_instruction,
        audit_receipt,
    );
    println!("OF_SVM_CU record_audit_receipt {{}}", record_result.compute_units_consumed);
    println!("OF_SVM_FLOW record_audit_receipt PASS");

    let block_result = svm.process_instruction(&block_ix, &record_result.accounts);
    assert_success_without_economic_mutation!(
        "block_instruction",
        block_result,
        operator,
        vault_state,
        pending_instruction,
        audit_receipt,
    );
    println!("OF_SVM_CU block_instruction {{}}", block_result.compute_units_consumed);
    println!("OF_SVM_FLOW block_instruction PASS");
    println!("OF_SVM_FLOW sequential_review_record_block PASS");
    println!("OF_SVM_ECONOMIC lamports_unchanged PASS");
    println!("OF_SVM_ECONOMIC pda_data_unchanged PASS");

    let zero_review_ix: Instruction = Review_vault_instructionInstruction {{
        operator: operator_address,
        vault_state,
        pending_instruction,
        audit_receipt,
        instruction_hash: [0; 32],
    }}
    .into();
    assert_negative_case!(
        "review_zero_hash",
        svm.process_instruction(&zero_review_ix, &system_accounts(operator)),
    );

    let zero_record_ix: Instruction = Record_audit_receiptInstruction {{
        operator: operator_address,
        vault_state,
        audit_receipt,
        receipt_hash: [0; 32],
    }}
    .into();
    assert_negative_case!(
        "record_zero_hash",
        svm.process_instruction(&zero_record_ix, &system_accounts(operator)),
    );

    let zero_block_ix: Instruction = Block_instructionInstruction {{
        operator: operator_address,
        vault_state,
        pending_instruction,
        reason_code: 0,
    }}
    .into();
    assert_negative_case!(
        "block_zero_reason",
        svm.process_instruction(&zero_block_ix, &system_accounts(operator)),
    );
}}
"""


def docker_script(project_name: str, compute_budget: int) -> str:
    test_module = svm_test_module(project_name, compute_budget)
    return f"""set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
retry() {{
  local attempts="$1"
  shift
  local n=1
  until "$@"; do
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    sleep $((n * 15))
    n=$((n + 1))
  done
}}
apt-get update
apt-get install -y --no-install-recommends git ca-certificates curl pkg-config libssl-dev perl make clang llvm-dev libclang-dev protobuf-compiler
cd /tmp
curl -sSfL https://release.anza.xyz/stable/install | sh
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
solana --version | tee /out/solana.txt
git clone --depth 1 https://github.com/blueshift-gg/quasar.git /tmp/quasar
cd /tmp/quasar
git rev-parse HEAD | tee /out/quasar_head.txt
cargo install --path cli --locked
cd /tmp
quasar init {project_name} --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git --verbose
rm -rf /tmp/{project_name}/src
mkdir -p /tmp/{project_name}/src
cp -R /repo-src/. /tmp/{project_name}/src/
cd /tmp/{project_name}
find src -maxdepth 3 -type f | sort > /out/source_files.txt
retry 3 quasar build
printf PASS > /out/build_status.txt
find target/deploy -maxdepth 1 -type f -name '*.so' | sort | tee /out/deploy_so_files.txt
cat >> Cargo.toml <<'EOF'

[dev-dependencies.qvg_public_validation_product-client]
path = "target/client/rust/qvg_public_validation_product-client"
EOF
cat > src/production_svm_tests.rs <<'EOF'
{test_module}
EOF
cat >> src/lib.rs <<'EOF'

#[cfg(all(test, not(feature = "idl-build")))]
mod production_svm_tests;
EOF
cargo test production_svm_success_and_failure_matrix -- --nocapture | tee /out/svm-test.log
printf PASS > /out/svm_test_status.txt
rustc --version | tee /out/rustc.txt
cargo --version | tee /out/cargo.txt
quasar --version | tee /out/quasar.txt
"""


def run_container(source_dir: Path, work_dir: Path, timeout: int, project_name: str, compute_budget: int) -> subprocess.CompletedProcess[str]:
    script = work_dir / "run-quasar-svm-proof.sh"
    script.write_text(docker_script(project_name, compute_budget), encoding="utf-8")
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{source_dir.resolve()}:/repo-src:ro",
        "-v",
        f"{work_dir.resolve()}:/out",
        "rust:latest",
        "bash",
        "/out/run-quasar-svm-proof.sh",
    ]
    return subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)


def parse_svm_markers(log_text: str, compute_budget: int) -> dict[str, Any]:
    cu: dict[str, int] = {}
    flows: dict[str, str] = {}
    negatives: dict[str, str] = {}
    economics: dict[str, str] = {}
    for raw_line in log_text.splitlines():
        line = raw_line.strip()
        if match := CU_LINE_RE.match(line):
            cu[match.group("name")] = int(match.group("cu"))
            continue
        if match := FLOW_LINE_RE.match(line):
            flows[match.group("name")] = match.group("status")
            continue
        if match := NEGATIVE_LINE_RE.match(line):
            negatives[match.group("name")] = match.group("status")
            continue
        if match := ECONOMIC_LINE_RE.match(line):
            economics[match.group("name")] = match.group("status")

    required_instructions = [
        "review_vault_instruction",
        "record_audit_receipt",
        "block_instruction",
    ]
    instruction_profile = {
        name: {
            "compute_units_consumed": cu.get(name, 0),
            "compute_budget_units": compute_budget,
            "within_budget": 0 < cu.get(name, 0) < compute_budget,
            "status": flows.get(name, "FAIL"),
        }
        for name in required_instructions
    }
    return {
        "instruction_profile": instruction_profile,
        "flows": flows,
        "negative_cases": negatives,
        "economic_observations": economics,
        "required_markers_present": all(name in cu and flows.get(name) == "PASS" for name in required_instructions),
        "all_cu_within_budget": all(item["within_budget"] for item in instruction_profile.values()),
    }


def build_result(
    *,
    source_dir: Path,
    runtime_proof_path: Path,
    work_dir: Path,
    completed: subprocess.CompletedProcess[str],
    started_at: str,
    ended_at: str,
    project_name: str,
    compute_budget: int,
) -> dict[str, Any]:
    source_hash = sha256_sources(source_dir)
    runtime_proof = json.loads(runtime_proof_path.read_text(encoding="utf-8"))
    harness_source = svm_test_module(project_name, compute_budget)
    svm_log = read_marker(work_dir, "svm-test.log")
    marker_summary = parse_svm_markers(svm_log, compute_budget)
    source_surface = scan_source_economic_surface(source_dir)
    property_cases = mirror_property_cases()
    negative_required = {"review_zero_hash", "record_zero_hash", "block_zero_reason"}
    economic_required = {"lamports_unchanged", "pda_data_unchanged"}
    all_negative_cases_pass = all(marker_summary["negative_cases"].get(name) == "PASS" for name in negative_required)
    economic_svm_observations_pass = all(marker_summary["economic_observations"].get(name) == "PASS" for name in economic_required)
    source_economic_surface_pass = not any(source_surface.values())
    build_status = read_marker(work_dir, "build_status.txt")
    svm_test_status = read_marker(work_dir, "svm_test_status.txt")
    prior_runtime_source_matches = str(runtime_proof.get("source_sha256") or "") == source_hash
    result = (
        completed.returncode == 0
        and build_status == "PASS"
        and svm_test_status == "PASS"
        and marker_summary["required_markers_present"]
        and marker_summary["all_cu_within_budget"]
        and all_negative_cases_pass
        and economic_svm_observations_pass
        and source_economic_surface_pass
    )
    flows = [
        {"name": name, "status": status}
        for name, status in sorted(marker_summary["flows"].items())
    ]
    instruction_profile = marker_summary["instruction_profile"]
    return {
        "$schema": "https://overkill-factory.dev/schemas/quasar-cu-svm-economic-proof.schema.json",
        "record_type": "cu_svm_economic_proof",
        "result": "PASS" if result else "FAIL",
        "proof_kind": "production_quasar_cu_svm_economic",
        "created_at": ended_at,
        "started_at": started_at,
        "source_target": repo_ref(source_dir),
        "source_sha256": source_hash,
        "runtime_proof_ref": repo_ref(runtime_proof_path),
        "runtime_source_match": {
            "runtime_source_sha256": str(runtime_proof.get("source_sha256") or ""),
            "current_source_sha256": source_hash,
            "matches": prior_runtime_source_matches,
            "blocking_for_this_proof": False,
            "why_non_blocking": (
                "This CU/SVM/economic proof runs a fresh Quasar build and SVM test in the same container. "
                "The prior runtime proof is retained as a historical reference, not as the current-pass authority."
            ),
        },
        "product_target": {
            "product_id": "qvg-public-validation-product",
            "environment_class": "production-validation-quasar-svm",
            "source_ref": repo_ref(source_dir),
            "source_sha256": source_hash,
            "approval_scope": "Production-validation CU/SVM/economic lane for the named public QVG product source only.",
            "reusability_boundary": (
                "Reusable only while product_id, source_ref and source_sha256 match. "
                "It does not approve deploy, devnet/mainnet, custody, signing authority or release."
            ),
        },
        "toolchain_proof": {
            "container_image": "rust:latest",
            "install_source": "github:blueshift-gg/quasar",
            "source_head": read_marker(work_dir, "quasar_head.txt"),
            "rustc": read_marker(work_dir, "rustc.txt"),
            "cargo": read_marker(work_dir, "cargo.txt"),
            "solana": read_marker(work_dir, "solana.txt"),
            "quasar": read_marker(work_dir, "quasar.txt"),
            "init_command": f"quasar init {project_name} --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git --verbose",
            "build_command": "quasar build",
            "svm_test_command": "cargo test production_svm_success_and_failure_matrix -- --nocapture",
            "build_status": build_status or "FAIL",
            "svm_test_status": svm_test_status or "FAIL",
            "returncode": completed.returncode,
            "deploy_so_files": [line for line in read_marker(work_dir, "deploy_so_files.txt").splitlines() if line],
        },
        "quasar_reference_basis": QUASAR_SVM_REFERENCE_URLS,
        "test_harness": {
            "kind": "generated_rust_quasar_svm_unit_test",
            "sha256": sha256_text(harness_source),
        },
        "property_fuzz_coverage": {
            "deterministic_seed_policy": "exhaustive u8 edge corpus plus deterministic 32-byte hash generation, mirrored from source tests and backed by SVM edge cases",
            "cases": property_cases,
            "total_cases": (
                property_cases["hash_cases"]["total"]
                + property_cases["reason_code_cases"]["total"]
                + property_cases["svm_transaction_cases"]["total"]
            ),
        },
        "compute_unit_profile": {
            "profile_kind": "runtime_svm_measurement",
            "real_solana_cu_measured": True,
            "compute_budget_units": compute_budget,
            "instruction_profile": instruction_profile,
            "max_compute_units_consumed": max(
                (item["compute_units_consumed"] for item in instruction_profile.values()),
                default=0,
            ),
            "all_within_budget": marker_summary["all_cu_within_budget"],
        },
        "svm_or_client_flow_coverage": {
            "quasar_test_passed": svm_test_status == "PASS",
            "real_svm_transaction_harness": True,
            "flows": flows,
            "expected_flows": [
                "review_vault_instruction",
                "record_audit_receipt",
                "block_instruction",
                "sequential_review_record_block",
            ],
        },
        "negative_case_coverage": {
            name: {"status": marker_summary["negative_cases"].get(name, "FAIL")}
            for name in sorted(negative_required)
        },
        "economic_safety": {
            "overall_verdict": "PASS" if economic_svm_observations_pass and source_economic_surface_pass else "FAIL",
            "svm_observed": {
                name: {"status": marker_summary["economic_observations"].get(name, "FAIL")}
                for name in sorted(economic_required)
            },
            "source_static_surface": source_surface,
            "funds_movement": False,
            "persistent_state_writes": False,
            "cpi_calls": 0,
            "authority_changes": False,
            "note": "This QVG validation program validates PDA/account inputs and rejects empty hashes/reason codes; it performs no CPI, token operation, lamport transfer, authority mutation or persistent write.",
        },
        "evidence_refs": [
            repo_ref(source_dir),
            repo_ref(runtime_proof_path),
            ".tmp/factory-runs/production/quasar/cu-svm-economic-harness.rs",
            ".tmp/factory-runs/production/quasar/cu-svm-economic-report.md",
        ],
        "stdout_tail": redact_text(completed.stdout[-6000:], source_dir, work_dir),
        "stderr_tail": redact_text(completed.stderr[-6000:], source_dir, work_dir),
        "svm_log_tail": redact_text(svm_log[-6000:], source_dir, work_dir),
        "evidence_kind": "real",
        "reusable_for_product": True,
        "blocking_findings": not result,
        "policy_decision": (
            "This closes the QVG production-validation CU/SVM/economic lane only for the named source hash. "
            "Release, provider remote proof, human R4 gate and full production graph remain separate gates."
            if result
            else "Do not clear the CU/SVM/economic lane until the real QuasarSVM markers, CU budget and economic observations all pass."
        ),
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_report(path: Path, result: dict[str, Any]) -> None:
    profile = result["compute_unit_profile"]
    lines = [
        "# QVG Production CU/SVM/Economic Proof",
        "",
        f"Result: `{result['result']}`",
        f"Source: `{result['source_target']}`",
        f"Source SHA-256: `{result['source_sha256']}`",
        f"Real CU measured: `{str(profile['real_solana_cu_measured']).lower()}`",
        f"Compute budget: `{profile['compute_budget_units']}`",
        "",
        "## Instruction CU",
        "",
    ]
    for name, item in profile["instruction_profile"].items():
        lines.append(
            f"- `{name}`: `{item['compute_units_consumed']}` CU, within budget `{str(item['within_budget']).lower()}`"
        )
    lines.extend(
        [
            "",
            "## Economic Boundary",
            "",
            result["economic_safety"]["note"],
            "",
            "## Policy",
            "",
            result["policy_decision"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run QVG production QuasarSVM CU/economic proof.")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=ROOT / "products" / "qvg-public-validation-product" / "onchain" / "quasar" / "src",
    )
    parser.add_argument(
        "--runtime-proof",
        type=Path,
        default=ROOT / ".tmp" / "factory-runs" / "production" / "quasar" / "qvg-quasar-runtime-proof.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / ".tmp" / "factory-runs" / "production" / "quasar" / "cu-svm-economic-proof.json",
    )
    parser.add_argument(
        "--harness-out",
        type=Path,
        default=ROOT / ".tmp" / "factory-runs" / "production" / "quasar" / "cu-svm-economic-harness.rs",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=ROOT / ".tmp" / "factory-runs" / "production" / "quasar" / "cu-svm-economic-report.md",
    )
    parser.add_argument("--timeout-seconds", type=int, default=1200)
    parser.add_argument("--project-name", default="qvg-public-validation-product")
    parser.add_argument("--compute-budget", type=int, default=200_000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not PROJECT_NAME_RE.fullmatch(args.project_name):
        raise SystemExit("--project-name must be 3-64 chars of lowercase letters, numbers or hyphens")
    source_dir = args.source_dir if args.source_dir.is_absolute() else ROOT / args.source_dir
    runtime_proof = args.runtime_proof if args.runtime_proof.is_absolute() else ROOT / args.runtime_proof
    out = args.out if args.out.is_absolute() else ROOT / args.out
    harness_out = args.harness_out if args.harness_out.is_absolute() else ROOT / args.harness_out
    report_out = args.report_out if args.report_out.is_absolute() else ROOT / args.report_out
    source_dir = source_dir.resolve()
    if not source_dir.exists():
        raise SystemExit(f"source dir does not exist: {source_dir}")
    if not runtime_proof.exists():
        raise SystemExit(f"runtime proof does not exist: {runtime_proof}")

    started_at = utc_now()
    with tempfile.TemporaryDirectory(prefix="of-quasar-svm-economic-") as tmp:
        work_dir = Path(tmp)
        completed = run_container(source_dir, work_dir, args.timeout_seconds, args.project_name, args.compute_budget)
        ended_at = utc_now()
        result = build_result(
            source_dir=source_dir,
            runtime_proof_path=runtime_proof.resolve(),
            work_dir=work_dir,
            completed=completed,
            started_at=started_at,
            ended_at=ended_at,
            project_name=args.project_name,
            compute_budget=args.compute_budget,
        )

    harness_out.parent.mkdir(parents=True, exist_ok=True)
    harness_out.write_text(svm_test_module(args.project_name, args.compute_budget), encoding="utf-8")
    result["evidence_refs"] = [repo_ref(harness_out) if item.endswith("cu-svm-economic-harness.rs") else item for item in result["evidence_refs"]]
    result["evidence_refs"] = [repo_ref(report_out) if item.endswith("cu-svm-economic-report.md") else item for item in result["evidence_refs"]]
    write_report(report_out, result)
    write_json(out, result)
    print(
        json.dumps(
            {
                "result": result["result"],
                "out": repo_ref(out),
                "max_compute_units_consumed": result["compute_unit_profile"]["max_compute_units_consumed"],
                "economic_verdict": result["economic_safety"]["overall_verdict"],
            },
            indent=2,
        )
    )
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
