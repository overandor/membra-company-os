use anchor_lang::prelude::*;

#[account]
pub struct Artifact {
    pub creator: Pubkey,
    pub artifact_id: String,
    pub proof_hash: [u8; 32],
    pub terms_hash: [u8; 32],
    pub terms_uri: String,
    pub total_support_lamports: u64,
    pub support_count: u64,
    pub max_support_lamports: u64,
    pub initial_rebate_bps: u16,
    pub floor_rebate_bps: u16,
    pub decay_per_support_bps: u16,
    pub paused: bool,
    pub created_at: i64,
    pub bump: u8,
    pub vault_bump: u8,
}

impl Artifact {
    pub const LEN: usize = 8 + 32 + 200 + 32 + 32 + 200 + 8 + 8 + 8 + 2 + 2 + 2 + 1 + 8 + 1 + 1 + 256;

    pub fn current_rebate_bps(&self) -> u16 {
        let decayed = self
            .initial_rebate_bps
            .saturating_sub(self.decay_per_support_bps.saturating_mul(self.support_count as u16));
        std::cmp::max(decayed, self.floor_rebate_bps)
    }
}

#[account]
pub struct SupportReceipt {
    pub artifact: Pubkey,
    pub supporter: Pubkey,
    pub creator: Pubkey,
    pub amount_lamports: u64,
    pub rebate_lamports: u64,
    pub creator_lamports: u64,
    pub rebate_bps: u16,
    pub accepted_terms_hash: [u8; 32],
    pub artifact_proof_hash: [u8; 32],
    pub client_reference_hash: [u8; 32],
    pub created_at: i64,
    pub receipt_index: u64,
    pub bump: u8,
}

impl SupportReceipt {
    pub const LEN: usize = 8 + 32 + 32 + 32 + 8 + 8 + 8 + 2 + 32 + 32 + 32 + 8 + 8 + 1 + 128;
}
