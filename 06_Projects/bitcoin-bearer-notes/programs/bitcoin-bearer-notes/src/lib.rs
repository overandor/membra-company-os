use anchor_lang::prelude::*;

// Program ID - replace with actual deployment
// declare_id!("BBNote11111111111111111111111111111111111111");

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

// Fixed denominations in satoshis (1 BTC = 100_000_000 satoshis)
pub const DENOM_10: u64 = 10 * 100_000_000;     // $10 equivalent
pub const DENOM_50: u64 = 50 * 100_000_000;     // $50 equivalent
pub const DENOM_100: u64 = 100 * 100_000_000;   // $100 equivalent
pub const DENOM_500: u64 = 500 * 100_000_000;   // $500 equivalent

// Seed constants
pub const VAULT_SEED: &[u8] = b"vault";
pub const NOTE_SEED: &[u8] = b"note";
pub const CLAIM_SEED: &[u8] = b"claim";
pub const MINT_AUTHORITY_SEED: &[u8] = b"mint_authority";

#[program]
pub mod bitcoin_bearer_notes {
    use super::*;

    /// Initialize the protocol vault and note registry
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        vault.authority = ctx.accounts.authority.key();
        vault.total_btc_reserved = 0;
        vault.total_notes_minted = 0;
        vault.total_notes_redeemed = 0;
        vault.paused = false;
        vault.bump = ctx.bumps.vault;

        emit!(VaultInitialized {
            authority: vault.authority,
            vault: vault.key(),
        });

        Ok(())
    }

    /// Mint a new denominated bearer note
    /// Serial number must be vault.total_notes_minted + 1 for uniqueness.
    pub fn mint_note(
        ctx: Context<MintNote>,
        serial_number: u64,
        denomination: u64,
        metadata_uri: String,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);
        require!(
            is_valid_denomination(denomination),
            ErrorCode::InvalidDenomination
        );
        require!(metadata_uri.len() <= 200, ErrorCode::MetadataTooLong);

        let vault = &mut ctx.accounts.vault;
        let note = &mut ctx.accounts.note;

        // Validate serial_number is the next expected value to ensure
        // globally unique, monotonic serial assignment.
        let expected_serial = vault
            .total_notes_minted
            .checked_add(1)
            .ok_or(ErrorCode::MathOverflow)?;
        require!(
            serial_number == expected_serial,
            ErrorCode::InvalidSerialNumber
        );

        vault.total_notes_minted = expected_serial;

        // Initialize note state
        note.serial_number = serial_number;
        note.denomination = denomination;
        note.mint_authority = ctx.accounts.mint_authority.key();
        note.current_holder = ctx.accounts.holder.key();
        note.original_holder = ctx.accounts.holder.key();
        note.metadata_uri = metadata_uri;
        note.created_at = Clock::get()?.unix_timestamp;
        note.expires_at = None;
        note.redeemed = false;
        note.revoked = false;
        note.claim_id = None;
        note.bump = ctx.bumps.note;

        // Update vault reserves
        vault.total_btc_reserved = vault.total_btc_reserved
            .checked_add(denomination)
            .ok_or(ErrorCode::MathOverflow)?;

        emit!(NoteMinted {
            serial_number,
            denomination,
            holder: note.current_holder,
            mint_authority: note.mint_authority,
        });

        Ok(())
    }

    /// Transfer a note to a new holder
    /// SECURITY: Transfers require the current holder's wallet signature.
    /// A note transfer must require one of:
    /// 1. holder wallet signature (this implementation), or
    /// 2. valid bearer claim secret + unused status + expiration check (future), or
    /// 3. governed admin recovery path (future).
    /// Serial number alone is NEVER authority.
    pub fn transfer_note(
        ctx: Context<TransferNote>,
        serial_number: u64,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);

        let note = &mut ctx.accounts.note;

        require!(!note.redeemed, ErrorCode::NoteAlreadyRedeemed);
        require!(!note.revoked, ErrorCode::NoteRevoked);
        require!(
            note.serial_number == serial_number,
            ErrorCode::InvalidSerialNumber
        );
        require!(
            note.current_holder == ctx.accounts.holder.key(),
            ErrorCode::NotNoteHolder
        );

        let previous_holder = note.current_holder;
        note.current_holder = ctx.accounts.new_holder.key();

        emit!(NoteTransferred {
            serial_number,
            from: previous_holder,
            to: note.current_holder,
        });

        Ok(())
    }

    /// Burn a note to redeem BTC (on-chain settlement)
    pub fn burn_and_redeem(
        ctx: Context<BurnAndRedeem>,
        serial_number: u64,
        btc_receiving_address: String,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);
        require!(
            btc_receiving_address.len() >= 26 && btc_receiving_address.len() <= 74,
            ErrorCode::InvalidBtcAddress
        );

        let vault = &mut ctx.accounts.vault;
        let note = &mut ctx.accounts.note;

        require!(!note.redeemed, ErrorCode::NoteAlreadyRedeemed);
        require!(!note.revoked, ErrorCode::NoteRevoked);
        require!(
            note.serial_number == serial_number,
            ErrorCode::InvalidSerialNumber
        );
        require!(
            note.current_holder == ctx.accounts.holder.key(),
            ErrorCode::NotNoteHolder
        );

        let denomination = note.denomination;

        // Mark as redeemed - anti-double-spend
        note.redeemed = true;
        note.redeemed_at = Some(Clock::get()?.unix_timestamp);
        note.btc_receiving_address = Some(btc_receiving_address.clone());

        // Update vault
        vault.total_notes_redeemed = vault.total_notes_redeemed
            .checked_add(1)
            .ok_or(ErrorCode::MathOverflow)?;
        vault.total_btc_reserved = vault.total_btc_reserved
            .checked_sub(denomination)
            .ok_or(ErrorCode::MathOverflow)?;

        emit!(NoteRedeemed {
            serial_number,
            holder: ctx.accounts.holder.key(),
            btc_address: btc_receiving_address,
            denomination,
        });

        Ok(())
    }

    /// Revoke a note (admin/emergency only)
    pub fn revoke_note(
        ctx: Context<RevokeNote>,
        serial_number: u64,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);

        let note = &mut ctx.accounts.note;

        require!(
            note.serial_number == serial_number,
            ErrorCode::InvalidSerialNumber
        );
        require!(!note.redeemed, ErrorCode::NoteAlreadyRedeemed);

        note.revoked = true;
        note.revoked_at = Some(Clock::get()?.unix_timestamp);

        emit!(NoteRevoked {
            serial_number,
            authority: ctx.accounts.authority.key(),
        });

        Ok(())
    }

    /// Set expiration on a note (optional time limit)
    pub fn set_expiration(
        ctx: Context<SetExpiration>,
        expires_at: i64,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);

        let note = &mut ctx.accounts.note;

        require!(!note.redeemed, ErrorCode::NoteAlreadyRedeemed);
        require!(
            expires_at > Clock::get()?.unix_timestamp,
            ErrorCode::InvalidExpiration
        );

        note.expires_at = Some(expires_at);

        emit!(ExpirationSet {
            serial_number: note.serial_number,
            expires_at,
        });

        Ok(())
    }

    /// Emergency pause/unpause
    pub fn set_paused(ctx: Context<SetPaused>, paused: bool) -> Result<()> {
        ctx.accounts.vault.paused = paused;

        emit!(VaultPauseChanged {
            paused,
            authority: ctx.accounts.authority.key(),
        });

        Ok(())
    }

    // ============== CoinPack Multi-Asset Claim ==============

    /// Create a multi-asset claim bundle
    pub fn create_claim_bundle(
        ctx: Context<CreateClaimBundle>,
        claim_id: [u8; 32],
        asset_types: Vec<String>,
        amounts: Vec<u64>,
        expires_at: i64,
        pin_hash: [u8; 32],
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);
        require!(
            asset_types.len() == amounts.len(),
            ErrorCode::MismatchedAssets
        );
        require!(
            asset_types.len() > 0 && asset_types.len() <= 10,
            ErrorCode::TooManyAssets
        );
        require!(
            expires_at > Clock::get()?.unix_timestamp,
            ErrorCode::InvalidExpiration
        );

        let claim = &mut ctx.accounts.claim_bundle;
        claim.claim_id = claim_id;
        claim.creator = ctx.accounts.creator.key();
        claim.asset_types = asset_types;
        claim.amounts = amounts;
        claim.expires_at = expires_at;
        claim.pin_hash = pin_hash;
        claim.claimed = false;
        claim.claimer = None;
        claim.claimed_at = None;
        claim.device_fingerprint = None;
        claim.bump = ctx.bumps.claim_bundle;

        emit!(ClaimBundleCreated {
            claim_id: claim_id.to_vec(),
            creator: claim.creator,
            asset_count: claim.asset_types.len() as u8,
            expires_at,
        });

        Ok(())
    }

    /// Claim a CoinPack bundle
    pub fn claim_bundle(
        ctx: Context<ClaimBundleAccounts>,
        claim_id: [u8; 32],
        pin: String,
        device_fingerprint: String,
    ) -> Result<()> {
        require!(!ctx.accounts.vault.paused, ErrorCode::VaultPaused);

        let claim = &mut ctx.accounts.claim_bundle;

        require!(!claim.claimed, ErrorCode::AlreadyClaimed);
        require!(
            Clock::get()?.unix_timestamp < claim.expires_at,
            ErrorCode::ClaimExpired
        );
        require!(
            hash_pin(&pin) == claim.pin_hash,
            ErrorCode::InvalidPin
        );

        // Anti-double-claim: mark immediately
        claim.claimed = true;
        claim.claimer = Some(ctx.accounts.claimer.key());
        claim.claimed_at = Some(Clock::get()?.unix_timestamp);
        claim.device_fingerprint = Some(device_fingerprint);

        emit!(ClaimBundleClaimed {
            claim_id: claim_id.to_vec(),
            claimer: ctx.accounts.claimer.key(),
            assets: claim.asset_types.clone(),
            amounts: claim.amounts.clone(),
        });

        Ok(())
    }
}

// ============== Helper Functions ==============

fn is_valid_denomination(denomination: u64) -> bool {
    denomination == DENOM_10
        || denomination == DENOM_50
        || denomination == DENOM_100
        || denomination == DENOM_500
}

fn hash_pin(pin: &str) -> [u8; 32] {
    anchor_lang::solana_program::hash::hash(pin.as_bytes()).to_bytes()
}

// ============== Account Structs ==============

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Vault::SIZE,
        seeds = [VAULT_SEED],
        bump
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(serial_number: u64, denomination: u64, metadata_uri: String)]
pub struct MintNote<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + Note::SIZE,
        seeds = [NOTE_SEED, serial_number.to_le_bytes().as_ref()],
        bump
    )]
    pub note: Account<'info, Note>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump,
        constraint = vault.authority == authority.key() @ ErrorCode::Unauthorized
    )]
    pub vault: Account<'info, Vault>,

    /// CHECK: This is the mint authority PDA for the SPL token mint
    #[account(
        seeds = [MINT_AUTHORITY_SEED],
        bump
    )]
    pub mint_authority: AccountInfo<'info>,

    /// CHECK: The holder receiving the note
    pub holder: AccountInfo<'info>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(serial_number: u64)]
pub struct TransferNote<'info> {
    #[account(
        mut,
        seeds = [NOTE_SEED, serial_number.to_le_bytes().as_ref()],
        bump = note.bump,
        constraint = note.current_holder == holder.key() @ ErrorCode::NotNoteHolder
    )]
    pub note: Account<'info, Note>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,

    /// CHECK: New holder
    pub new_holder: AccountInfo<'info>,

    #[account(mut)]
    pub holder: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(serial_number: u64, btc_receiving_address: String)]
pub struct BurnAndRedeem<'info> {
    #[account(
        mut,
        seeds = [NOTE_SEED, serial_number.to_le_bytes().as_ref()],
        bump = note.bump,
        constraint = note.current_holder == holder.key() @ ErrorCode::NotNoteHolder
    )]
    pub note: Account<'info, Note>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub holder: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(serial_number: u64)]
pub struct RevokeNote<'info> {
    #[account(
        mut,
        seeds = [NOTE_SEED, serial_number.to_le_bytes().as_ref()],
        bump = note.bump,
    )]
    pub note: Account<'info, Note>,

    #[account(
        seeds = [VAULT_SEED],
        bump = vault.bump,
        constraint = vault.authority == authority.key() @ ErrorCode::Unauthorized
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub authority: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct SetExpiration<'info> {
    #[account(
        mut,
        constraint = note.current_holder == holder.key() @ ErrorCode::NotNoteHolder
    )]
    pub note: Account<'info, Note>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub holder: Signer<'info>,
}

#[derive(Accounts)]
pub struct SetPaused<'info> {
    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump,
        constraint = vault.authority == authority.key() @ ErrorCode::Unauthorized
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(claim_id: [u8; 32])]
pub struct CreateClaimBundle<'info> {
    #[account(
        init,
        payer = creator,
        space = 8 + ClaimBundle::MAX_SIZE,
        seeds = [CLAIM_SEED, &claim_id],
        bump
    )]
    pub claim_bundle: Account<'info, ClaimBundle>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub creator: Signer<'info>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(claim_id: [u8; 32], pin: String, device_fingerprint: String)]
pub struct ClaimBundleAccounts<'info> {
    #[account(
        mut,
        seeds = [CLAIM_SEED, &claim_id],
        bump = claim_bundle.bump,
    )]
    pub claim_bundle: Account<'info, ClaimBundle>,

    #[account(
        mut,
        seeds = [VAULT_SEED],
        bump = vault.bump
    )]
    pub vault: Account<'info, Vault>,

    #[account(mut)]
    pub claimer: Signer<'info>,

    pub system_program: Program<'info, System>,
}

// ============== Data Structures ==============

#[account]
pub struct Vault {
    pub authority: Pubkey,
    pub total_btc_reserved: u64,     // Total BTC in satoshis
    pub total_notes_minted: u64,
    pub total_notes_redeemed: u64,
    pub paused: bool,
    pub bump: u8,
}

impl Vault {
    pub const SIZE: usize = 32 + 8 + 8 + 8 + 1 + 1;
}

#[account]
pub struct Note {
    pub serial_number: u64,
    pub denomination: u64,           // In satoshis
    pub mint_authority: Pubkey,
    pub current_holder: Pubkey,
    pub original_holder: Pubkey,
    pub metadata_uri: String,        // IPFS/metadata URI (max 200 chars)
    pub created_at: i64,
    pub expires_at: Option<i64>,
    pub redeemed: bool,
    pub redeemed_at: Option<i64>,
    pub btc_receiving_address: Option<String>,
    pub revoked: bool,
    pub revoked_at: Option<i64>,
    pub claim_id: Option<[u8; 32]>,  // Link to CoinPack claim
    pub bump: u8,
}

impl Note {
    // Borsh layout:
    // serial_number: u64 = 8
    // denomination: u64 = 8
    // mint_authority: Pubkey = 32
    // current_holder: Pubkey = 32
    // original_holder: Pubkey = 32
    // metadata_uri: String = 4 + 200
    // created_at: i64 = 8
    // expires_at: Option<i64> = 1 + 8
    // redeemed: bool = 1
    // redeemed_at: Option<i64> = 1 + 8
    // btc_receiving_address: Option<String> = 1 + 4 + 74
    // revoked: bool = 1
    // revoked_at: Option<i64> = 1 + 8
    // claim_id: Option<[u8; 32]> = 1 + 32
    // bump: u8 = 1
    pub const SIZE: usize = 8 + 8 + 32 + 32 + 32 + 4 + 200 + 8 + (1 + 8) + 1 + (1 + 8) + (1 + 4 + 74) + 1 + (1 + 8) + (1 + 32) + 1;
}

#[account]
pub struct ClaimBundle {
    pub claim_id: [u8; 32],
    pub creator: Pubkey,
    pub asset_types: Vec<String>,    // e.g. ["BTC", "USDC", "SOL"]
    pub amounts: Vec<u64>,           // In smallest units
    pub expires_at: i64,
    pub pin_hash: [u8; 32],          // SHA256 of PIN
    pub claimed: bool,
    pub claimer: Option<Pubkey>,
    pub claimed_at: Option<i64>,
    pub device_fingerprint: Option<String>,
    pub bump: u8,
}

impl ClaimBundle {
    pub const MAX_SIZE: usize = 32 + 32 + 4 + (10 * (4 + 10)) + 4 + (10 * 8) + 8 + 32 + 1 + 1 + 32 + 1 + 8 + 1 + 4 + 64 + 1;
}

// ============== Events ==============

#[event]
pub struct VaultInitialized {
    pub authority: Pubkey,
    pub vault: Pubkey,
}

#[event]
pub struct NoteMinted {
    pub serial_number: u64,
    pub denomination: u64,
    pub holder: Pubkey,
    pub mint_authority: Pubkey,
}

#[event]
pub struct NoteTransferred {
    pub serial_number: u64,
    pub from: Pubkey,
    pub to: Pubkey,
}

#[event]
pub struct NoteRedeemed {
    pub serial_number: u64,
    pub holder: Pubkey,
    pub btc_address: String,
    pub denomination: u64,
}

#[event]
pub struct NoteRevoked {
    pub serial_number: u64,
    pub authority: Pubkey,
}

#[event]
pub struct ExpirationSet {
    pub serial_number: u64,
    pub expires_at: i64,
}

#[event]
pub struct VaultPauseChanged {
    pub paused: bool,
    pub authority: Pubkey,
}

#[event]
pub struct ClaimBundleCreated {
    pub claim_id: Vec<u8>,
    pub creator: Pubkey,
    pub asset_count: u8,
    pub expires_at: i64,
}

#[event]
pub struct ClaimBundleClaimed {
    pub claim_id: Vec<u8>,
    pub claimer: Pubkey,
    pub assets: Vec<String>,
    pub amounts: Vec<u64>,
}

// ============== Errors ==============

#[error_code]
pub enum ErrorCode {
    #[msg("Vault is paused")]
    VaultPaused,
    #[msg("Invalid denomination")]
    InvalidDenomination,
    #[msg("Note already redeemed")]
    NoteAlreadyRedeemed,
    #[msg("Note has been revoked")]
    NoteRevoked,
    #[msg("Invalid serial number")]
    InvalidSerialNumber,
    #[msg("Not the note holder")]
    NotNoteHolder,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Math overflow")]
    MathOverflow,
    #[msg("Invalid BTC address")]
    InvalidBtcAddress,
    #[msg("Metadata URI too long")]
    MetadataTooLong,
    #[msg("Invalid expiration")]
    InvalidExpiration,
    #[msg("Already claimed")]
    AlreadyClaimed,
    #[msg("Claim expired")]
    ClaimExpired,
    #[msg("Invalid PIN")]
    InvalidPin,
    #[msg("Mismatched asset arrays")]
    MismatchedAssets,
    #[msg("Too many assets")]
    TooManyAssets,
}
