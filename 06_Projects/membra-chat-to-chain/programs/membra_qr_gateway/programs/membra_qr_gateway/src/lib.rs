use anchor_lang::prelude::*;

pub mod state;
pub mod errors;
pub mod events;
pub mod instructions;

use instructions::*;

declare_id!("membraQRGateway11111111111111111111111111111");

#[program]
pub mod membra_qr_gateway {
    use super::*;

    pub fn initialize_artifact(
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
        instructions::initialize_artifact::handler(
            ctx,
            artifact_id,
            proof_hash,
            terms_hash,
            terms_uri,
            initial_rebate_bps,
            floor_rebate_bps,
            decay_per_support_bps,
            max_support_lamports,
        )
    }

    pub fn support_artifact(
        ctx: Context<SupportArtifact>,
        amount_lamports: u64,
        accepted_terms_hash: [u8; 32],
        client_reference_hash: [u8; 32],
    ) -> Result<()> {
        instructions::support_artifact::handler(
            ctx,
            amount_lamports,
            accepted_terms_hash,
            client_reference_hash,
        )
    }

    pub fn update_artifact_status(ctx: Context<UpdateArtifactStatus>, paused: bool) -> Result<()> {
        instructions::update_artifact::handler(ctx, paused)
    }
}
