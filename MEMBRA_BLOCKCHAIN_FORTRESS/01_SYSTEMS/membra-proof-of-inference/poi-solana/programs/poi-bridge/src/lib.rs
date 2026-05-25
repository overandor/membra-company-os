use anchor_lang::prelude::*;

declare_id!("PoiBridge1111111111111111111111111111111111");

#[program]
pub mod poi_bridge {
    use super::*;

    /// Initialize the PoI bridge
    pub fn initialize(ctx: Context<Initialize>, authority: Pubkey) -> Result<()> {
        let bridge = &mut ctx.accounts.bridge;
        bridge.authority = authority;
        bridge.proof_count = 0;
        bridge.emitter_chain = "poi-network".to_string();
        Ok(())
    }

    /// Register a proof from PoI network
    pub fn register_proof(
        ctx: Context<RegisterProof>,
        inference_id: String,
        model_cid: String,
        prompt_hash: [u8; 32],
        token_hash: [u8; 32],
        timestamp: i64,
        signature: Vec<u8>,
    ) -> Result<()> {
        let bridge = &mut ctx.accounts.bridge;
        let proof = &mut ctx.accounts.proof;

        proof.inference_id = inference_id;
        proof.model_cid = model_cid;
        proof.prompt_hash = prompt_hash;
        proof.token_hash = token_hash;
        proof.timestamp = timestamp;
        proof.signature = signature;
        proof.registered_at = Clock::get()?.unix_timestamp;
        proof.verified = false;

        bridge.proof_count += 1;
        msg!("Proof registered: {}", proof.inference_id);
        Ok(())
    }

    /// Verify a proof
    pub fn verify_proof(ctx: Context<VerifyProof>, inference_id: String) -> Result<()> {
        let proof = &mut ctx.accounts.proof;
        require!(proof.inference_id == inference_id, ErrorCode::InvalidProofId);
        proof.verified = true;
        msg!("Proof verified: {}", inference_id);
        Ok(())
    }

    /// Update bridge authority
    pub fn update_authority(ctx: Context<UpdateAuthority>, new_authority: Pubkey) -> Result<()> {
        let bridge = &mut ctx.accounts.bridge;
        require!(ctx.accounts.authority.key() == bridge.authority, ErrorCode::Unauthorized);
        bridge.authority = new_authority;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + BridgeState::SPACE,
        seeds = [b"bridge"],
        bump
    )]
    pub bridge: Account<'info, BridgeState>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(inference_id: String)]
pub struct RegisterProof<'info> {
    #[account(
        mut,
        seeds = [b"bridge"],
        bump
    )]
    pub bridge: Account<'info, BridgeState>,
    #[account(
        init,
        payer = payer,
        space = 8 + ProofRecord::SPACE,
        seeds = [b"proof", inference_id.as_bytes()],
        bump
    )]
    pub proof: Account<'info, ProofRecord>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(inference_id: String)]
pub struct VerifyProof<'info> {
    #[account(
        mut,
        seeds = [b"proof", inference_id.as_bytes()],
        bump
    )]
    pub proof: Account<'info, ProofRecord>,
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateAuthority<'info> {
    #[account(
        mut,
        seeds = [b"bridge"],
        bump
    )]
    pub bridge: Account<'info, BridgeState>,
    pub authority: Signer<'info>,
}

#[account]
pub struct BridgeState {
    pub authority: Pubkey,
    pub proof_count: u64,
    pub emitter_chain: String,
}

impl BridgeState {
    pub const SPACE: usize = 32 + 8 + 50; // authority + count + emitter_chain
}

#[account]
pub struct ProofRecord {
    pub inference_id: String,
    pub model_cid: String,
    pub prompt_hash: [u8; 32],
    pub token_hash: [u8; 32],
    pub timestamp: i64,
    pub signature: Vec<u8>,
    pub registered_at: i64,
    pub verified: bool,
}

impl ProofRecord {
    pub const SPACE: usize = 100 + 100 + 32 + 32 + 8 + 64 + 8 + 1; // inference_id + model_cid + hashes + timestamp + signature + registered_at + verified
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid proof ID")]
    InvalidProofId,
    #[msg("Unauthorized")]
    Unauthorized,
}
