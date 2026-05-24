use anchor_lang::prelude::*;
use crate::state::{Artifact, SupportReceipt};
use crate::errors::MembraError;
use crate::events::ArtifactSupported;

#[derive(Accounts)]
#[instruction(
    amount_lamports: u64,
    accepted_terms_hash: [u8; 32],
    client_reference_hash: [u8; 32],
)]
pub struct SupportArtifact<'info> {
    #[account(mut)]
    pub supporter: Signer<'info>,

    #[account(
        mut,
        seeds = [
            b"artifact",
            artifact.creator.as_ref(),
            artifact.artifact_id.as_bytes(),
        ],
        bump = artifact.bump,
    )]
    pub artifact: Account<'info, Artifact>,

    /// CHECK: creator receives allocation from support
    #[account(mut)]
    pub creator: UncheckedAccount<'info>,

    #[account(
        init,
        payer = supporter,
        space = SupportReceipt::LEN,
        seeds = [
            b"receipt",
            artifact.key().as_ref(),
            &artifact.support_count.to_le_bytes(),
        ],
        bump
    )]
    pub receipt: Account<'info, SupportReceipt>,

    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<SupportArtifact>,
    amount_lamports: u64,
    accepted_terms_hash: [u8; 32],
    client_reference_hash: [u8; 32],
) -> Result<()> {
    let artifact = &mut ctx.accounts.artifact;

    require!(amount_lamports > 0, MembraError::SupportAmountZero);
    require!(!artifact.paused, MembraError::ArtifactPaused);
    require!(
        accepted_terms_hash == artifact.terms_hash,
        MembraError::TermsHashMismatch
    );

    if artifact.max_support_lamports > 0 {
        require!(
            artifact
                .total_support_lamports
                .checked_add(amount_lamports)
                .ok_or(MembraError::MathOverflow)?
                <= artifact.max_support_lamports,
            MembraError::SupportCapExceeded
        );
    }

    let current_rebate_bps = artifact.current_rebate_bps();
    let rebate_lamports = amount_lamports
        .checked_mul(current_rebate_bps as u64)
        .ok_or(MembraError::MathOverflow)?
        .checked_div(10000)
        .ok_or(MembraError::MathOverflow)?;

    let creator_lamports = amount_lamports
        .checked_sub(rebate_lamports)
        .ok_or(MembraError::MathOverflow)?;

    let receipt_index = artifact.support_count;
    artifact.support_count = artifact
        .support_count
        .checked_add(1)
        .ok_or(MembraError::ReceiptIndexOverflow)?;
    artifact.total_support_lamports = artifact
        .total_support_lamports
        .checked_add(amount_lamports)
        .ok_or(MembraError::MathOverflow)?;

    let clock = Clock::get()?;

    let receipt = &mut ctx.accounts.receipt;
    receipt.artifact = artifact.key();
    receipt.supporter = ctx.accounts.supporter.key();
    receipt.creator = ctx.accounts.creator.key();
    receipt.amount_lamports = amount_lamports;
    receipt.rebate_lamports = rebate_lamports;
    receipt.creator_lamports = creator_lamports;
    receipt.rebate_bps = current_rebate_bps;
    receipt.accepted_terms_hash = accepted_terms_hash;
    receipt.artifact_proof_hash = artifact.proof_hash;
    receipt.client_reference_hash = client_reference_hash;
    receipt.created_at = clock.unix_timestamp;
    receipt.receipt_index = receipt_index;
    receipt.bump = ctx.bumps.receipt;

    // Transfer SOL: supporter -> creator (creator_lamports)
    // Transfer SOL: supporter -> supporter (rebate_lamports kept by supporter)
    // Net: supporter sends amount_lamports, creator gets creator_lamports
    let cpi_context = CpiContext::new(
        ctx.accounts.system_program.to_account_info(),
        anchor_lang::system_program::Transfer {
            from: ctx.accounts.supporter.to_account_info(),
            to: ctx.accounts.creator.to_account_info(),
        },
    );
    anchor_lang::system_program::transfer(cpi_context, creator_lamports)?;

    emit!(ArtifactSupported {
        artifact: artifact.key(),
        supporter: ctx.accounts.supporter.key(),
        creator: ctx.accounts.creator.key(),
        amount_lamports,
        rebate_lamports,
        creator_lamports,
        rebate_bps: current_rebate_bps,
        receipt_index,
        timestamp: clock.unix_timestamp,
    });

    Ok(())
}
