use anchor_lang::prelude::*;
use crate::state::Artifact;
use crate::errors::MembraError;
use crate::events::ArtifactStatusUpdated;

#[derive(Accounts)]
pub struct UpdateArtifactStatus<'info> {
    #[account(mut)]
    pub creator: Signer<'info>,

    #[account(
        mut,
        seeds = [
            b"artifact",
            creator.key().as_ref(),
            artifact.artifact_id.as_bytes(),
        ],
        bump = artifact.bump,
        constraint = artifact.creator == creator.key() @ MembraError::UnauthorizedUpdate,
    )]
    pub artifact: Account<'info, Artifact>,
}

pub fn handler(ctx: Context<UpdateArtifactStatus>, paused: bool) -> Result<()> {
    let artifact = &mut ctx.accounts.artifact;
    artifact.paused = paused;

    let clock = Clock::get()?;

    emit!(ArtifactStatusUpdated {
        artifact: artifact.key(),
        paused,
        timestamp: clock.unix_timestamp,
    });

    Ok(())
}
