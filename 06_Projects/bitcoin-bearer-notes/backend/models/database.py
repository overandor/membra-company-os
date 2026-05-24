from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

from core.config import settings

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=30,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class VaultState(Base):
    __tablename__ = "vault_states"

    id = Column(Integer, primary_key=True)
    authority = Column(String(44), nullable=False, index=True)
    total_btc_reserved = Column(BigInteger, default=0)  # satoshis
    total_notes_minted = Column(BigInteger, default=0)
    total_notes_redeemed = Column(BigInteger, default=0)
    paused = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NoteRecord(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)
    serial_number = Column(BigInteger, nullable=False, unique=True, index=True)
    denomination = Column(BigInteger, nullable=False)  # satoshis
    mint_authority = Column(String(44), nullable=False, index=True)
    current_holder = Column(String(44), nullable=False, index=True)
    original_holder = Column(String(44), nullable=False)
    metadata_uri = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    redeemed = Column(Boolean, default=False, index=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    btc_receiving_address = Column(String(100), nullable=True)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    claim_id = Column(String(64), nullable=True, index=True)
    tx_signature = Column(String(100), nullable=True)

    __table_args__ = (
        Index('idx_notes_holder_redeemed', 'current_holder', 'redeemed'),
        Index('idx_notes_created', 'created_at'),
    )


class ClaimBundle(Base):
    __tablename__ = "claim_bundles"

    id = Column(Integer, primary_key=True)
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    claim_hash = Column(String(64), nullable=False)  # HMAC of claim_id for integrity
    creator = Column(String(44), nullable=False, index=True)
    asset_types = Column(JSON, nullable=False)  # ["BTC", "USDC", "SOL"]
    amounts = Column(JSON, nullable=False)  # [0.0001, 5.0, 0.1]
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    pin_hash = Column(String(64), nullable=False)
    pin_salt = Column(String(32), nullable=False)  # Per-claim salt for PIN
    claimed = Column(Boolean, default=False, index=True)
    claimer = Column(String(44), nullable=True, index=True)
    claimed_by_wallet = Column(String(44), nullable=True)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    device_fingerprint = Column(String(128), nullable=True)
    device_fingerprint_hash = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, default=0)
    proof_hash = Column(String(64), nullable=True)  # Audit trail hash
    encrypted_payload = Column(Text, nullable=True)  # Encrypted claim metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    delivery_method = Column(String(20), default="link")  # sms, email, qr, nfc
    delivery_address = Column(String(255), nullable=True)

    __table_args__ = (
        Index('idx_claims_expires', 'expires_at', 'claimed'),
    )


class ClaimAttempt(Base):
    __tablename__ = "claim_attempts"

    id = Column(Integer, primary_key=True)
    claim_id = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(255), nullable=True)
    device_fingerprint = Column(String(128), nullable=True)
    attempted_at = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean, default=False)
    failure_reason = Column(String(50), nullable=True)  # expired, invalid_pin, already_claimed
    pin_attempt = Column(String(10), nullable=True)

    __table_args__ = (
        Index('idx_attempts_claim', 'claim_id', 'attempted_at'),
    )


class RedemptionRequest(Base):
    __tablename__ = "redemption_requests"

    id = Column(Integer, primary_key=True)
    serial_number = Column(BigInteger, nullable=False, index=True)
    holder = Column(String(44), nullable=False, index=True)
    btc_address = Column(String(100), nullable=False)
    denomination = Column(BigInteger, nullable=False)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    txid = Column(String(100), nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_fee = Column(BigInteger, nullable=True)  # satoshis
    actual_fee = Column(BigInteger, nullable=True)
    error_message = Column(Text, nullable=True)


class BTCReserveBalance(Base):
    __tablename__ = "btc_reserve_balances"

    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(100), nullable=False, index=True)
    balance_sats = Column(BigInteger, default=0)
    confirmed_balance = Column(BigInteger, default=0)
    pending_balance = Column(BigInteger, default=0)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now())
    block_height = Column(Integer, nullable=True)


class ReserveAccount(Base):
    __tablename__ = "reserve_accounts"

    id = Column(Integer, primary_key=True)
    chain = Column(String(20), nullable=False, default="BTC")  # BTC, SOL, ETH
    asset = Column(String(20), nullable=False, default="BTC")
    address = Column(String(100), nullable=False, index=True)
    wallet_type = Column(
        String(20),
        nullable=False,
        default="multisig"
    )  # custodian | multisig | federation | wrapped_provider
    required_confirmations = Column(Integer, default=2)
    status = Column(String(20), default="active")  # active | frozen | deprecated
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReserveSnapshot(Base):
    __tablename__ = "reserve_snapshots"

    id = Column(Integer, primary_key=True)
    reserve_account_id = Column(Integer, ForeignKey("reserve_accounts.id"), nullable=False)
    observed_balance_sats = Column(BigInteger, nullable=False)
    liabilities_sats = Column(BigInteger, nullable=False)
    reserve_ratio_bps = Column(BigInteger, nullable=False)  # basis points (10000 = 100%)
    block_height = Column(Integer, nullable=True)
    source = Column(String(50), nullable=False)  # mempool.space, blockchain.info
    proof_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_snapshots_account', 'reserve_account_id', 'created_at'),
    )


class Liability(Base):
    __tablename__ = "liabilities"

    id = Column(Integer, primary_key=True)
    note_id = Column(BigInteger, nullable=False, index=True)
    asset = Column(String(20), nullable=False, default="BTC")
    amount_sats_or_units = Column(BigInteger, nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default="outstanding"
    )  # outstanding | redeemed | expired | revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_liabilities_status', 'status', 'asset'),
    )


class RiskDisclosureAcceptance(Base):
    __tablename__ = "risk_disclosure_acceptances"

    id = Column(Integer, primary_key=True)
    wallet_address = Column(String(44), nullable=False, index=True)
    claim_id = Column(String(64), nullable=True, index=True)
    disclosure_version = Column(String(20), nullable=False)
    disclosure_hash = Column(String(64), nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_hash = Column(String(64), nullable=True)
    user_agent_hash = Column(String(64), nullable=True)
    proof_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index('idx_disclosure_wallet', 'wallet_address', 'accepted_at'),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    event_type = Column(String(50), nullable=False, index=True)
    wallet_address = Column(String(44), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_audit_wallet_time', 'wallet_address', 'created_at'),
    )


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
