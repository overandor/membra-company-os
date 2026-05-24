use anchor_lang::prelude::*;
use anchor_lang::solana_program::{
    program::invoke,
    system_instruction,
};
use std::mem::size_of;

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcfkgP6PdGi3sFJ");

#[program]
pub mod membra_dns {
    use super::*;

    /// Initialize the DNS registry with admin authority
    pub fn initialize(ctx: Context<Initialize>, admin: Pubkey) -> Result<()> {
        let registry = &mut ctx.accounts.registry;
        registry.admin = admin;
        registry.total_zones = 0;
        registry.total_records = 0;
        registry.is_paused = false;
        registry.bump = ctx.bumps.registry;
        
        msg!("DNS Registry initialized with admin: {}", admin);
        Ok(())
    }
    
    /// Register a new DNS zone owned by a DID
    pub fn register_zone(
        ctx: Context<RegisterZone>,
        did: String,
        domain: String,
        owner: Pubkey,
    ) -> Result<()> {
        let registry = &ctx.accounts.registry;
        
        // Check if paused
        require!(!registry.is_paused, ErrorCode::RegistryPaused);
        
        // Validate inputs
        require!(did.len() <= 256, ErrorCode::DIDTooLong);
        require!(domain.len() <= 253, ErrorCode::DomainTooLong);
        require!(did.starts_with("did:"), ErrorCode::InvalidDIDFormat);
        
        let zone = &mut ctx.accounts.zone;
        
        // Check if zone already exists
        require!(zone.owner == Pubkey::default(), ErrorCode::ZoneAlreadyExists);
        
        // Initialize zone
        zone.did = did;
        zone.domain = domain;
        zone.owner = owner;
        zone.created_at = Clock::get()?.unix_timestamp;
        zone.updated_at = Clock::get()?.unix_timestamp;
        zone.record_count = 0;
        zone.bump = ctx.bumps.zone;
        
        // Update registry stats
        registry.total_zones += 1;
        
        emit!(ZoneRegistered {
            did: zone.did.clone(),
            domain: zone.domain.clone(),
            owner,
            timestamp: zone.created_at,
        });
        
        msg!("Zone registered: {} owned by DID: {}", zone.domain, zone.did);
        Ok(())
    }
    
    /// Add a DNS record to a zone
    pub fn add_record(
        ctx: Context<AddRecord>,
        record_name: String,
        record_type: u8,
        value: String,
        ttl: u32,
    ) -> Result<()> {
        let registry = &ctx.accounts.registry;
        
        // Check if paused
        require!(!registry.is_paused, ErrorCode::RegistryPaused);
        
        // Validate inputs
        require!(record_name.len() <= 253, ErrorCode::RecordNameTooLong);
        require!(value.len() <= 65535, ErrorCode::RecordValueTooLong);
        require!(ttl > 0 && ttl <= 86400, ErrorCode::InvalidTTL);
        require!(record_type >= 1 && record_type <= 33, ErrorCode::InvalidRecordType);
        
        let zone = &mut ctx.accounts.zone;
        let record = &mut ctx.accounts.record;
        
        // Verify zone ownership
        require!(zone.owner == ctx.accounts.owner.key(), ErrorCode::NotZoneOwner);
        
        // Check if record already exists
        require!(record.value.is_empty(), ErrorCode::RecordAlreadyExists);
        
        // Initialize record
        record.zone = zone.domain.clone();
        record.record_name = record_name.clone();
        record.record_type = record_type;
        record.value = value.clone();
        record.ttl = ttl;
        record.created_at = Clock::get()?.unix_timestamp;
        record.updated_at = Clock::get()?.unix_timestamp;
        record.bump = ctx.bumps.record;
        
        // Update zone stats
        zone.record_count += 1;
        zone.updated_at = Clock::get()?.unix_timestamp;
        
        // Update registry stats
        registry.total_records += 1;
        
        emit!(RecordAdded {
            zone: zone.domain.clone(),
            record_name,
            record_type,
            value,
            ttl,
            timestamp: record.created_at,
        });
        
        msg!("Record added: {} to zone: {}", record.record_name, zone.domain);
        Ok(())
    }
    
    /// Update a DNS record
    pub fn update_record(
        ctx: Context<UpdateRecord>,
        new_value: String,
        new_ttl: u32,
    ) -> Result<()> {
        let registry = &ctx.accounts.registry;
        
        // Check if paused
        require!(!registry.is_paused, ErrorCode::RegistryPaused);
        
        // Validate inputs
        require!(new_value.len() <= 65535, ErrorCode::RecordValueTooLong);
        require!(new_ttl > 0 && new_ttl <= 86400, ErrorCode::InvalidTTL);
        
        let zone = &mut ctx.accounts.zone;
        let record = &mut ctx.accounts.record;
        
        // Verify zone ownership
        require!(zone.owner == ctx.accounts.owner.key(), ErrorCode::NotZoneOwner);
        
        // Update record
        record.value = new_value.clone();
        record.ttl = new_ttl;
        record.updated_at = Clock::get()?.unix_timestamp;
        
        // Update zone timestamp
        zone.updated_at = Clock::get()?.unix_timestamp;
        
        emit!(RecordUpdated {
            zone: zone.domain.clone(),
            record_name: record.record_name.clone(),
            record_type: record.record_type,
            new_value,
            new_ttl,
            timestamp: record.updated_at,
        });
        
        msg!("Record updated: {} in zone: {}", record.record_name, zone.domain);
        Ok(())
    }
    
    /// Delete a DNS record
    pub fn delete_record(ctx: Context<DeleteRecord>) -> Result<()> {
        let registry = &ctx.accounts.registry;
        
        // Check if paused
        require!(!registry.is_paused, ErrorCode::RegistryPaused);
        
        let zone = &mut ctx.accounts.zone;
        
        // Verify zone ownership
        require!(zone.owner == ctx.accounts.owner.key(), ErrorCode::NotZoneOwner);
        
        let record = &ctx.accounts.record;
        
        emit!(RecordDeleted {
            zone: zone.domain.clone(),
            record_name: record.record_name.clone(),
            record_type: record.record_type,
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        // Close the record account to reclaim rent
        let record_key = ctx.accounts.record.key();
        let owner_key = ctx.accounts.owner.key();
        
        **ctx.accounts.record.to_account_info().lamports.borrow_mut() -= 1;
        **ctx.accounts.owner.to_account_info().lamports.borrow_mut() += 1;
        
        // Update stats
        zone.record_count -= 1;
        zone.updated_at = Clock::get()?.unix_timestamp;
        registry.total_records -= 1;
        
        msg!("Record deleted: {} from zone: {}", record.record_name, zone.domain);
        Ok(())
    }
    
    /// Transfer zone ownership
    pub fn transfer_zone(ctx: Context<TransferZone>, new_owner: Pubkey) -> Result<()> {
        let registry = &ctx.accounts.registry;
        
        // Check if paused
        require!(!registry.is_paused, ErrorCode::RegistryPaused);
        
        let zone = &mut ctx.accounts.zone;
        
        // Verify current ownership
        require!(zone.owner == ctx.accounts.owner.key(), ErrorCode::NotZoneOwner);
        
        // Transfer ownership
        zone.owner = new_owner;
        zone.updated_at = Clock::get()?.unix_timestamp;
        
        emit!(ZoneTransferred {
            domain: zone.domain.clone(),
            old_owner: ctx.accounts.owner.key(),
            new_owner,
            timestamp: zone.updated_at,
        });
        
        msg!("Zone transferred: {} to new owner: {}", zone.domain, new_owner);
        Ok(())
    }
    
    /// Pause/unpause the registry (admin only)
    pub fn set_pause_state(ctx: Context<SetPauseState>, paused: bool) -> Result<()> {
        let registry = &mut ctx.accounts.registry;
        
        // Verify admin authority
        require!(registry.admin == ctx.accounts.admin.key(), ErrorCode::NotAdmin);
        
        registry.is_paused = paused;
        
        emit!(PauseStateChanged {
            paused,
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Registry pause state changed to: {}", paused);
        Ok(())
    }
    
    /// Update admin authority (admin only)
    pub fn update_admin(ctx: Context<UpdateAdmin>, new_admin: Pubkey) -> Result<()> {
        let registry = &mut ctx.accounts.registry;
        
        // Verify current admin
        require!(registry.admin == ctx.accounts.admin.key(), ErrorCode::NotAdmin);
        
        registry.admin = new_admin;
        
        emit!(AdminUpdated {
            old_admin: ctx.accounts.admin.key(),
            new_admin,
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Admin updated from {} to {}", ctx.accounts.admin.key(), new_admin);
        Ok(())
    }
}

// Account structures

#[account]
pub struct DnsRegistry {
    pub admin: Pubkey,
    pub total_zones: u64,
    pub total_records: u64,
    pub is_paused: bool,
    pub bump: u8,
}

#[account]
pub struct DnsZone {
    pub did: String,
    pub domain: String,
    pub owner: Pubkey,
    pub created_at: i64,
    pub updated_at: i64,
    pub record_count: u64,
    pub bump: u8,
}

#[account]
pub struct DnsRecord {
    pub zone: String,
    pub record_name: String,
    pub record_type: u8,
    pub value: String,
    pub ttl: u32,
    pub created_at: i64,
    pub updated_at: i64,
    pub bump: u8,
}

// Instruction contexts

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + size_of::<DnsRegistry>(),
        seeds = [b"registry"],
        bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterZone<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(
        init,
        payer = payer,
        space = 8 + 256 + 253 + 32 + 16 + 16 + 8 + 1, // max sizes
        seeds = [b"zone", domain.as_bytes()],
        bump
    )]
    pub zone: Account<'info, DnsZone>,
    
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AddRecord<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(
        mut,
        seeds = [b"zone", zone.domain.as_bytes()],
        bump = zone.bump,
        has_one = owner
    )]
    pub zone: Account<'info, DnsZone>,
    
    #[account(
        init,
        payer = payer,
        space = 8 + 253 + 253 + 1 + 65535 + 4 + 16 + 16 + 1,
        seeds = [b"record", zone.domain.as_bytes(), record_name.as_bytes()],
        bump
    )]
    pub record: Account<'info, DnsRecord>,
    
    pub owner: Signer<'info>,
    
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateRecord<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(
        mut,
        seeds = [b"zone", zone.domain.as_bytes()],
        bump = zone.bump,
        has_one = owner
    )]
    pub zone: Account<'info, DnsZone>,
    
    #[account(
        mut,
        seeds = [b"record", zone.domain.as_bytes(), record.record_name.as_bytes()],
        bump = record.bump
    )]
    pub record: Account<'info, DnsRecord>,
    
    pub owner: Signer<'info>,
}

#[derive(Accounts)]
pub struct DeleteRecord<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(
        mut,
        seeds = [b"zone", zone.domain.as_bytes()],
        bump = zone.bump,
        has_one = owner
    )]
    pub zone: Account<'info, DnsZone>,
    
    #[account(
        mut,
        close = owner,
        seeds = [b"record", zone.domain.as_bytes(), record.record_name.as_bytes()],
        bump = record.bump
    )]
    pub record: Account<'info, DnsRecord>,
    
    pub owner: Signer<'info>,
}

#[derive(Accounts)]
pub struct TransferZone<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    #[account(
        mut,
        seeds = [b"zone", zone.domain.as_bytes()],
        bump = zone.bump,
        has_one = owner
    )]
    pub zone: Account<'info, DnsZone>,
    
    pub owner: Signer<'info>,
}

#[derive(Accounts)]
pub struct SetPauseState<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    pub admin: Signer<'info>,
}

#[derive(Accounts)]
pub struct UpdateAdmin<'info> {
    #[account(
        mut,
        seeds = [b"registry"],
        bump = registry.bump
    )]
    pub registry: Account<'info, DnsRegistry>,
    
    pub admin: Signer<'info>,
}

// Events

#[event]
pub struct ZoneRegistered {
    pub did: String,
    pub domain: String,
    pub owner: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct RecordAdded {
    pub zone: String,
    pub record_name: String,
    pub record_type: u8,
    pub value: String,
    pub ttl: u32,
    pub timestamp: i64,
}

#[event]
pub struct RecordUpdated {
    pub zone: String,
    pub record_name: String,
    pub record_type: u8,
    pub new_value: String,
    pub new_ttl: u32,
    pub timestamp: i64,
}

#[event]
pub struct RecordDeleted {
    pub zone: String,
    pub record_name: String,
    pub record_type: u8,
    pub timestamp: i64,
}

#[event]
pub struct ZoneTransferred {
    pub domain: String,
    pub old_owner: Pubkey,
    pub new_owner: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct PauseStateChanged {
    pub paused: bool,
    pub timestamp: i64,
}

#[event]
pub struct AdminUpdated {
    pub old_admin: Pubkey,
    pub new_admin: Pubkey,
    pub timestamp: i64,
}

// Error codes

#[error_code]
pub enum ErrorCode {
    #[msg("Registry is currently paused")]
    RegistryPaused,
    #[msg("DID is too long (max 256 characters)")]
    DIDTooLong,
    #[msg("Domain is too long (max 253 characters)")]
    DomainTooLong,
    #[msg("Invalid DID format (must start with 'did:')")]
    InvalidDIDFormat,
    #[msg("Zone already exists")]
    ZoneAlreadyExists,
    #[msg("Record name is too long (max 253 characters)")]
    RecordNameTooLong,
    #[msg("Record value is too long (max 65535 characters)")]
    RecordValueTooLong,
    #[msg("Invalid TTL (must be 1-86400 seconds)")]
    InvalidTTL,
    #[msg("Invalid record type (must be 1-33)")]
    InvalidRecordType,
    #[msg("Record already exists")]
    RecordAlreadyExists,
    #[msg("Not the zone owner")]
    NotZoneOwner,
    #[msg("Not the registry admin")]
    NotAdmin,
}