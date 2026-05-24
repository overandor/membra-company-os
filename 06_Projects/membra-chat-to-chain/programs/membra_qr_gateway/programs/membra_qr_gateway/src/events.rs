use anchor_lang::prelude::*;

#[event]
pub struct ArtifactInitialized {
    pub artifact: Pubkey,
    pub creator: Pubkey,
    pub artifact_id: String,
    pub proof_hash: [u8; 32],
    pub terms_hash: [u8; 32],
    pub initial_rebate_bps: u16,
    pub floor_rebate_bps: u16,
    pub max_support_lamports: u64,
    pub timestamp: i64,
}

#[event]
pub struct ArtifactSupported {
    pub artifact: Pubkey,
    pub supporter: Pubkey,
    pub creator: Pubkey,
    pub amount_lamports: u64,
    pub rebate_lamports: u64,
    pub creator_lamports: u64,
    pub rebate_bps: u16,
    pub receipt_index: u64,
    pub timestamp: i64,
}

#[event]
pub struct ArtifactStatusUpdated {
    pub artifact: Pubkey,
    pub paused: bool,
    pub timestamp: i64,
}
