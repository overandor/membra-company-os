"""Backend API endpoint tests using FastAPI TestClient with mocked DB."""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from main import app
from models.database import get_db
from services.btc_reserve import btc_reserve_service


# Override DB dependency with a mock so no real PostgreSQL is needed
mock_db = AsyncMock()
app.dependency_overrides[get_db] = lambda: mock_db

client = TestClient(app)


class TestHealthEndpoints:
    """Tests for /health and /ready."""

    def test_health(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready(self):
        response = client.get("/api/v1/ready")
        assert response.status_code in (200, 503)
        data = response.json()
        assert "status" in data


class TestNotesEndpoints:
    """Tests for note management endpoints."""

    def test_list_notes_empty(self):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        response = client.get("/api/v1/notes")
        assert response.status_code == 200
        assert "notes" in response.json()

    def test_get_note_not_found(self):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        response = client.get("/api/v1/notes/999999999")
        assert response.status_code == 404


class TestReserveEndpoints:
    """Tests for reserve/proof endpoints."""

    def test_get_reserves(self):
        with patch.object(
            btc_reserve_service,
            "get_latest_proof",
            return_value={
                "asset": "BTC",
                "reserve_balance_sats": 100000000,
                "outstanding_liabilities_sats": 50000000,
                "reserve_ratio_bps": 20000,
                "fully_backed": True,
                "can_mint_new_notes": True,
                "degraded_source": False,
                "snapshots": [],
                "disclaimer": "Test disclaimer",
            },
        ):
            response = client.get("/api/v1/reserves")
        assert response.status_code == 200
        data = response.json()
        assert "disclaimer" in data
        assert data["asset"] == "BTC"
        assert data["reserve_ratio_bps"] == 20000

    def test_get_reserve_proof(self):
        with patch.object(
            btc_reserve_service,
            "get_latest_proof",
            return_value={
                "asset": "BTC",
                "reserve_ratio_bps": 15000,
                "can_mint_new_notes": True,
                "fully_backed": True,
                "disclaimer": "Test",
            },
        ):
            response = client.get("/api/v1/reserves/proof")
        assert response.status_code == 200
        data = response.json()
        assert "reserve_ratio_bps" in data
        assert "can_mint_new_notes" in data


class TestRiskDisclosureEndpoints:
    """Tests for risk disclosure endpoints."""

    def test_get_current_risk_disclosure(self):
        response = client.get("/api/v1/risk-disclosures/current")
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "hash" in data
        assert "version" in data

    def test_accept_risk_disclosure_validation(self):
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        response = client.post("/api/v1/risk-disclosures/accept", json={
            "wallet_address": "test_wallet",
            "accepted": True,
        })
        assert response.status_code in (200, 422)


class TestAuditEndpoints:
    """Tests for audit log endpoints."""

    def test_list_audit_events(self):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        response = client.get("/api/v1/audit/events?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "count" in data


class TestStatsEndpoint:
    """Tests for stats endpoint."""

    def test_get_stats(self):
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalar.return_value = 0
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_notes" in data
        assert "redeemed_notes" in data
        assert "timestamp" in data
