"""Backend pytest tests for Membra Money services."""
import pytest
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from services.claim_service import ClaimService
from services.btc_reserve import BTCReserveService, RedemptionProcessor
from services.risk_disclosure import RiskDisclosureService, get_disclosure_hash
from core.config import settings


class TestClaimService:
    """Tests for claim link security: PIN salt, constant-time verify, cooldown, claim hash."""

    def test_pin_hash_uses_salt_and_pepper(self):
        cs = ClaimService()
        salt = "abcd1234"
        pin = "123456"
        h1 = cs._hash_pin(pin, salt)
        h2 = cs._hash_pin(pin, salt)
        assert h1 == h2
        assert len(h1) == 64  # sha256 hex

    def test_different_pins_produce_different_hashes(self):
        cs = ClaimService()
        salt = "abcd1234"
        assert cs._hash_pin("123456", salt) != cs._hash_pin("111111", salt)

    def test_different_salts_produce_different_hashes(self):
        cs = ClaimService()
        pin = "123456"
        assert cs._hash_pin(pin, "salt1") != cs._hash_pin(pin, "salt2")

    def test_claim_hash_is_hmac(self):
        cs = ClaimService()
        cid = "a" * 64
        h = cs._generate_claim_hash(cid)
        expected = hmac.new(
            settings.CLAIM_LINK_SECRET.encode(),
            cid.encode(),
            hashlib.sha256,
        ).hexdigest()
        assert h == expected

    def test_legacy_pin_hash(self):
        cs = ClaimService()
        pin = "123456"
        legacy = cs._hash_pin_legacy(pin)
        assert len(legacy) == 64
        assert legacy != cs._hash_pin(pin, "salt")

    def test_masked_claim_url(self):
        cs = ClaimService()
        url = "https://membra.io/claim/abcd1234abcd1234abcd1234abcd1234"
        masked = cs._mask_claim_url(url)
        assert "**REDacted**" in masked
        assert "abcd1234" not in masked
        assert cs._mask_claim_url("") == ""
        assert cs._mask_claim_url(None) == None

    @pytest.mark.asyncio
    async def test_validate_claim_rejects_wrong_pin(self):
        cs = ClaimService()
        mock_db = AsyncMock()
        mock_claim = MagicMock()
        mock_claim.claimed = False
        mock_claim.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_claim.pin_hash = cs._hash_pin("123456", "salt")
        mock_claim.pin_salt = "salt"
        mock_claim.attempt_count = 0
        mock_claim.last_attempt_at = None

        cs.get_claim = AsyncMock(return_value=mock_claim)

        result = await cs.validate_claim(
            db=mock_db,
            claim_id="test",
            pin="000000",
            device_fingerprint="fp",
            ip_address="127.0.0.1",
        )
        assert result["valid"] is False
        assert result["error"] == "invalid_pin"

    @pytest.mark.asyncio
    async def test_validate_claim_rejects_expired(self):
        cs = ClaimService()
        mock_db = AsyncMock()
        mock_claim = MagicMock()
        mock_claim.claimed = False
        mock_claim.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_claim.pin_hash = cs._hash_pin("123456", "salt")
        mock_claim.pin_salt = "salt"
        mock_claim.attempt_count = 0
        mock_claim.last_attempt_at = None

        cs.get_claim = AsyncMock(return_value=mock_claim)

        result = await cs.validate_claim(
            db=mock_db,
            claim_id="test",
            pin="123456",
            device_fingerprint="fp",
            ip_address="127.0.0.1",
        )
        assert result["valid"] is False
        assert result["error"] == "expired"

    @pytest.mark.asyncio
    async def test_validate_claim_rejects_already_claimed(self):
        cs = ClaimService()
        mock_db = AsyncMock()
        mock_claim = MagicMock()
        mock_claim.claimed = True
        mock_claim.claimed_at = datetime.now(timezone.utc)
        mock_claim.pin_hash = cs._hash_pin("123456", "salt")
        mock_claim.pin_salt = "salt"
        mock_claim.attempt_count = 0
        mock_claim.last_attempt_at = None

        cs.get_claim = AsyncMock(return_value=mock_claim)

        result = await cs.validate_claim(
            db=mock_db,
            claim_id="test",
            pin="123456",
            device_fingerprint="fp",
            ip_address="127.0.0.1",
        )
        assert result["valid"] is False
        assert result["error"] == "already_claimed"

    @pytest.mark.asyncio
    async def test_validate_claim_success(self):
        cs = ClaimService()
        mock_db = AsyncMock()
        mock_claim = MagicMock()
        mock_claim.claimed = False
        mock_claim.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_claim.pin_hash = cs._hash_pin("123456", "salt")
        mock_claim.pin_salt = "salt"
        mock_claim.attempt_count = 0
        mock_claim.last_attempt_at = None
        mock_claim.asset_types = ["BTC"]
        mock_claim.amounts = [0.0001]

        cs.get_claim = AsyncMock(return_value=mock_claim)

        result = await cs.validate_claim(
            db=mock_db,
            claim_id="test",
            pin="123456",
            device_fingerprint="fp",
            ip_address="127.0.0.1",
            wallet_address="wallet123",
        )
        assert result["valid"] is True
        assert "proof_hash" in result

    @pytest.mark.asyncio
    async def test_brute_force_lockout(self):
        cs = ClaimService()
        mock_db = AsyncMock()
        mock_claim = MagicMock()
        mock_claim.claimed = False
        mock_claim.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_claim.pin_hash = cs._hash_pin("123456", "salt")
        mock_claim.pin_salt = "salt"
        mock_claim.attempt_count = settings.PIN_MAX_ATTEMPTS + 1
        mock_claim.last_attempt_at = datetime.now(timezone.utc)

        cs.get_claim = AsyncMock(return_value=mock_claim)

        result = await cs.validate_claim(
            db=mock_db,
            claim_id="test",
            pin="123456",
            device_fingerprint="fp",
            ip_address="127.0.0.1",
        )
        assert result["valid"] is False
        assert result["error"] == "too_many_attempts"


class TestBTCReserveService:
    """Tests for reserve model and proof-of-reserves."""

    def test_generate_proof_of_reserves(self):
        rs = BTCReserveService()
        h = rs.generate_proof_of_reserves(["addr1", "addr2"], "msg")
        assert len(h) == 64

    def test_verify_proof(self):
        rs = BTCReserveService()
        h = rs.generate_proof_of_reserves(["addr1", "addr2"], "msg")
        assert rs.verify_proof("msg", ["addr1", "addr2"], h) is True
        assert rs.verify_proof("msg", ["addr1", "addr2"], h + "x") is False

    @pytest.mark.asyncio
    async def test_validate_btc_address(self):
        rp = RedemptionProcessor()
        assert await rp.validate_btc_address("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh") is True
        assert await rp.validate_btc_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa") is True
        assert await rp.validate_btc_address("invalid") is False


class TestRiskDisclosureService:
    """Tests for risk disclosure acceptance tracking."""

    def test_disclosure_hash_is_stable(self):
        h1 = get_disclosure_hash()
        h2 = get_disclosure_hash()
        assert h1 == h2
        assert len(h1) == 64

    def test_current_version_exists(self):
        rs = RiskDisclosureService()
        assert rs.current_version() != ""
