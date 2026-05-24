use anchor_lang::prelude::*;
use crate::state::Artifact;
use crate::errors::MembraError;
use crate::events::ArtifactInitialized;

#[derive(Accounts)]
#[instruction(
    artifact_id: String,
    proof_hash: [u8; 32],
    terms_hash: [u8; 32],
)]
pub struct InitializeArtifact<'info> {
    #[account(mut)]
    pub creator: Signer<'info>,

    #[account(
        init,
        payer = creator,
        space = Artifact::LEN,
        seeds = [
            b"artifact",
            creator.key().as_ref(),
            artifact_id.as_bytes(),
        ],
        bump
    )]
    pub artifact: Account<'info, Artifact>,

    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<InitializeArtifact>,
    artifact_id: String,
    proof_hash: [u8; 32],
    terms_hash: [u8; 32],
    terms_uri: String,
    initial_rebate_bps: u16,
    floor_rebate_bps: u16,
    decay_per_support_bps: u16,
    max_support_lamports: u64,
) -> Result<()> {
    require!(artifact_id.len() <= 200, MembraError::ArtifactIdTooLong);
    require!(terms_uri.len() <= 200, MembraError::TermsUriTooLong);
    require!(initial_rebate_bps <= 5000, MembraError::RebateTooHigh);
    require!(
        floor_rebate_bps <= initial_rebate_bps,
        MembraError::FloorRebateExceedsInitial
    );

    let artifact = &mut ctx.accounts.artifact;
    let clock = Clock::get()?;

    artifact.creator = ctx.accounts.creator.key();
    artifact.artifact_id = artifact_id.clone();
    artifact.proof_hash = proof_hash;
    artifact.terms_hash = terms_hash;
    artifact.terms_uri = terms_uri;
    artifact.total_support_lamports = 0;
    artifact.support_count = 0;
    artifact.max_support_lamports = max_support_lamports;
    artifact.initial_rebate_bps = initial_rebate_bps;
    artifact.floor_rebate_bps = floor_rebate_bps;
    artifact.decay_per_support_bps = decay_per_support_bps;
    artifact.paused = false;
    artifact.created_at = clock.unix_timestamp;
    artifact.bump = ctx.bumps.artifact;
    artifact.vault_bump = 0;

    emit!(ArtifactInitialized {
        artifact: artifact.key(),
        creator: ctx.accounts.creator.key(),
        artifact_id,
        proof_hash,
        terms_hash,
        initial_rebate_bps,
        floor_rebate_bps,
        max_support_lamports,
        timestamp: clock.unix_timestamp,
    });

    Ok(())
}
