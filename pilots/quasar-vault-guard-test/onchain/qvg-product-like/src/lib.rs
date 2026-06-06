#![no_std]
#![allow(dead_code)]

use quasar_lang::prelude::*;

#[cfg(all(test, not(feature = "idl-build")))]
mod tests;

declare_id!("55555555555555555555555555555555555555555555");

#[derive(Seeds)]
#[seeds(b"vault", operator: Address)]
pub struct VaultStatePda;

#[derive(Seeds)]
#[seeds(b"pending", vault_state: Address)]
pub struct PendingInstructionPda;

#[derive(Seeds)]
#[seeds(b"audit", vault_state: Address)]
pub struct AuditReceiptPda;

#[inline(always)]
fn ensure_nonzero_hash(hash: [u8; 32]) -> Result<(), ProgramError> {
    if hash == [0; 32] {
        return Err(ProgramError::InvalidInstructionData);
    }
    Ok(())
}

#[inline(always)]
fn ensure_nonzero_reason(reason_code: u8) -> Result<(), ProgramError> {
    if reason_code == 0 {
        return Err(ProgramError::InvalidInstructionData);
    }
    Ok(())
}

#[derive(Accounts)]
pub struct ReviewVaultInstructionAccounts {
    #[account(mut)]
    pub operator: Signer,
    #[account(address = VaultStatePda::seeds(operator.address()))]
    pub vault_state: UncheckedAccount,
    #[account(address = PendingInstructionPda::seeds(vault_state.address()))]
    pub pending_instruction: UncheckedAccount,
    #[account(address = AuditReceiptPda::seeds(vault_state.address()))]
    pub audit_receipt: UncheckedAccount,
}

impl ReviewVaultInstructionAccounts {
    #[inline(always)]
    pub fn review(&self, instruction_hash: [u8; 32]) -> Result<(), ProgramError> {
        ensure_nonzero_hash(instruction_hash)
    }
}

#[derive(Accounts)]
pub struct RecordAuditReceiptAccounts {
    #[account(mut)]
    pub operator: Signer,
    #[account(address = VaultStatePda::seeds(operator.address()))]
    pub vault_state: UncheckedAccount,
    #[account(address = AuditReceiptPda::seeds(vault_state.address()))]
    pub audit_receipt: UncheckedAccount,
}

impl RecordAuditReceiptAccounts {
    #[inline(always)]
    pub fn record(&self, receipt_hash: [u8; 32]) -> Result<(), ProgramError> {
        ensure_nonzero_hash(receipt_hash)
    }
}

#[derive(Accounts)]
pub struct BlockInstructionAccounts {
    #[account(mut)]
    pub operator: Signer,
    #[account(address = VaultStatePda::seeds(operator.address()))]
    pub vault_state: UncheckedAccount,
    #[account(address = PendingInstructionPda::seeds(vault_state.address()))]
    pub pending_instruction: UncheckedAccount,
}

impl BlockInstructionAccounts {
    #[inline(always)]
    pub fn block(&self, reason_code: u8) -> Result<(), ProgramError> {
        ensure_nonzero_reason(reason_code)
    }
}

#[program]
mod qvg_product_like {
    use super::*;

    #[instruction(discriminator = 0)]
    pub fn review_vault_instruction(
        ctx: Ctx<ReviewVaultInstructionAccounts>,
        instruction_hash: [u8; 32],
    ) -> Result<(), ProgramError> {
        ctx.accounts.review(instruction_hash)
    }

    #[instruction(discriminator = 1)]
    pub fn record_audit_receipt(
        ctx: Ctx<RecordAuditReceiptAccounts>,
        receipt_hash: [u8; 32],
    ) -> Result<(), ProgramError> {
        ctx.accounts.record(receipt_hash)
    }

    #[instruction(discriminator = 2)]
    pub fn block_instruction(
        ctx: Ctx<BlockInstructionAccounts>,
        reason_code: u8,
    ) -> Result<(), ProgramError> {
        ctx.accounts.block(reason_code)
    }
}
