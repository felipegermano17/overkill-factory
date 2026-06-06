extern crate std;

use std::println;

use qvg_public_validation_product_client::{
    Block_instructionInstruction,
    Record_audit_receiptInstruction,
    Review_vault_instructionInstruction,
};
use quasar_svm::{Account, ExecutionStatus, Instruction, Pubkey, QuasarSvm};
use solana_address::Address;

const OPERATOR_LAMPORTS: u64 = 10_000_000_000;

fn setup() -> QuasarSvm {
    let elf = include_bytes!("../target/deploy/qvg_public_validation_product.so");
    QuasarSvm::new()
        .with_program(&Pubkey::from(crate::ID), elf)
        .with_compute_budget(200000)
}

fn addresses() -> (Pubkey, Address, Address, Address, Address) {
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
}

fn system_accounts(operator: Pubkey) -> [Account; 1] {
    [quasar_svm::token::create_keyed_system_account(&operator, OPERATOR_LAMPORTS)]
}

macro_rules! assert_success_without_economic_mutation {
    ($label:expr, $result:expr, $operator:expr, $vault_state:expr, $pending_instruction:expr, $audit_receipt:expr $(,)?) => {
        match $result.status() {
            ExecutionStatus::Success => {}
            ExecutionStatus::Err(err) => panic!("{} failed: {:?}\n{:?}", $label, err, $result.logs),
        }
        let operator_after = $result.account(&$operator).expect("operator account returned");
        assert_eq!(operator_after.lamports, OPERATOR_LAMPORTS);
        for address in [$vault_state, $pending_instruction, $audit_receipt] {
            if let Some(account) = $result.account(&Pubkey::from(address)) {
                assert_eq!(account.lamports, 0, "{} moved lamports into a PDA", $label);
                assert_eq!(account.data.len(), 0, "{} wrote persistent PDA data", $label);
            }
        }
    };
}

macro_rules! assert_negative_case {
    ($label:expr, $result:expr $(,)?) => {
        match $result.status() {
            ExecutionStatus::Err(_) => println!("OF_SVM_NEGATIVE {} PASS", $label),
            ExecutionStatus::Success => {
                println!("OF_SVM_NEGATIVE {} FAIL", $label);
                panic!("{} unexpectedly succeeded", $label);
            }
        }
    };
}

#[test]
fn production_svm_success_and_failure_matrix() {
    let (operator, operator_address, vault_state, pending_instruction, audit_receipt) = addresses();

    let review_ix: Instruction = Review_vault_instructionInstruction {
        operator: operator_address,
        vault_state,
        pending_instruction,
        audit_receipt,
        instruction_hash: [7; 32],
    }
    .into();
    let record_ix: Instruction = Record_audit_receiptInstruction {
        operator: operator_address,
        vault_state,
        audit_receipt,
        receipt_hash: [9; 32],
    }
    .into();
    let block_ix: Instruction = Block_instructionInstruction {
        operator: operator_address,
        vault_state,
        pending_instruction,
        reason_code: 3,
    }
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
    println!("OF_SVM_CU review_vault_instruction {}", review_result.compute_units_consumed);
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
    println!("OF_SVM_CU record_audit_receipt {}", record_result.compute_units_consumed);
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
    println!("OF_SVM_CU block_instruction {}", block_result.compute_units_consumed);
    println!("OF_SVM_FLOW block_instruction PASS");
    println!("OF_SVM_FLOW sequential_review_record_block PASS");
    println!("OF_SVM_ECONOMIC lamports_unchanged PASS");
    println!("OF_SVM_ECONOMIC pda_data_unchanged PASS");

    let zero_review_ix: Instruction = Review_vault_instructionInstruction {
        operator: operator_address,
        vault_state,
        pending_instruction,
        audit_receipt,
        instruction_hash: [0; 32],
    }
    .into();
    assert_negative_case!(
        "review_zero_hash",
        svm.process_instruction(&zero_review_ix, &system_accounts(operator)),
    );

    let zero_record_ix: Instruction = Record_audit_receiptInstruction {
        operator: operator_address,
        vault_state,
        audit_receipt,
        receipt_hash: [0; 32],
    }
    .into();
    assert_negative_case!(
        "record_zero_hash",
        svm.process_instruction(&zero_record_ix, &system_accounts(operator)),
    );

    let zero_block_ix: Instruction = Block_instructionInstruction {
        operator: operator_address,
        vault_state,
        pending_instruction,
        reason_code: 0,
    }
    .into();
    assert_negative_case!(
        "block_zero_reason",
        svm.process_instruction(&zero_block_ix, &system_accounts(operator)),
    );
}
