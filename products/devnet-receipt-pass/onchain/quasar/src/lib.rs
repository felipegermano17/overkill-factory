//! Devnet Receipt Pass Quasar-oriented program outline.
//!
//! This file is intentionally a public validation target, not a production
//! deployment claim. The pilot has no local Quasar/Rust/Solana toolchain gate,
//! so Auditor may only produce preflight evidence until a real code audit runs.

pub const PROGRAM_PURPOSE: &str = "read-only receipt pilot work package";
pub const RECEIPT_SEED: &[u8] = b"receipt";
pub const EVENT_SEED: &[u8] = b"receipt-event";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReceiptState {
    pub operator: [u8; 32],
    pub receipt_hash: [u8; 32],
    pub created_slot: u64,
    pub closed: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ReceiptEvent {
    pub receipt_hash: [u8; 32],
    pub event_hash: [u8; 32],
    pub observed_slot: u64,
}

pub fn derive_receipt_seed(operator: &[u8; 32], receipt_hash: &[u8; 32]) -> Vec<Vec<u8>> {
    vec![
        RECEIPT_SEED.to_vec(),
        operator.to_vec(),
        receipt_hash.to_vec(),
    ]
}

pub fn validate_event_bounds(event_hash: &[u8; 32], observed_slot: u64) -> Result<(), &'static str> {
    if observed_slot == 0 {
        return Err("observed_slot must be non-zero");
    }
    if event_hash.iter().all(|byte| *byte == 0) {
        return Err("event_hash must be non-zero");
    }
    Ok(())
}

pub fn init_receipt(
    operator: [u8; 32],
    receipt_hash: [u8; 32],
    created_slot: u64,
) -> Result<ReceiptState, &'static str> {
    if receipt_hash.iter().all(|byte| *byte == 0) {
        return Err("receipt_hash must be non-zero");
    }
    if created_slot == 0 {
        return Err("created_slot must be non-zero");
    }
    Ok(ReceiptState {
        operator,
        receipt_hash,
        created_slot,
        closed: false,
    })
}

pub fn append_receipt_event(
    state: &ReceiptState,
    event_hash: [u8; 32],
    observed_slot: u64,
) -> Result<ReceiptEvent, &'static str> {
    if state.closed {
        return Err("receipt is closed");
    }
    validate_event_bounds(&event_hash, observed_slot)?;
    Ok(ReceiptEvent {
        receipt_hash: state.receipt_hash,
        event_hash,
        observed_slot,
    })
}

pub fn close_receipt(state: &mut ReceiptState) -> Result<(), &'static str> {
    if state.closed {
        return Err("receipt already closed");
    }
    state.closed = true;
    Ok(())
}
