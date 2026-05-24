use anchor_lang::prelude::*;

#[error_code]
pub enum MembraError {
    #[msg("Artifact ID is too long (max 200 chars)")]
    ArtifactIdTooLong,
    #[msg("Terms URI is too long (max 200 chars)")]
    TermsUriTooLong,
    #[msg("Initial rebate must not exceed 5000 bps (50%)")]
    RebateTooHigh,
    #[msg("Floor rebate must not exceed initial rebate")]
    FloorRebateExceedsInitial,
    #[msg("Terms hash mismatch — supporter must accept current terms")]
    TermsHashMismatch,
    #[msg("Support amount must be greater than zero")]
    SupportAmountZero,
    #[msg("Artifact support cap exceeded")]
    SupportCapExceeded,
    #[msg("Artifact is paused and not accepting support")]
    ArtifactPaused,
    #[msg("Only the artifact creator can update status")]
    UnauthorizedUpdate,
    #[msg("Arithmetic overflow")]
    MathOverflow,
    #[msg("Support receipt index overflow")]
    ReceiptIndexOverflow,
}
