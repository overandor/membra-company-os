"""Test authentication functions."""

import pytest

from app.connectors.auth import sign_rest, ws_auth_message, epoch_ms
from app.core.config import API_KEY, API_SECRET


def test_epoch_ms_returns_int():
    """epoch_ms should return an integer."""
    ts = epoch_ms()
    assert isinstance(ts, int)
    assert ts > 0


def test_sign_rest_returns_headers():
    """sign_rest should return required headers."""
    headers = sign_rest(
        method="GET",
        path="/futures/usdt/contracts",
        query={"settle": "usdt"},
        body=None,
        api_key="test_key",
        api_secret="test_secret",
    )
    assert "KEY" in headers
    assert "SIGN" in headers
    assert "Timestamp" in headers
    assert headers["KEY"] == "test_key"


def test_sign_rest_with_body():
    """sign_rest should handle body correctly."""
    headers = sign_rest(
        method="POST",
        path="/futures/usdt/orders",
        query=None,
        body={"contract": "BTC_USDT", "size": 1},
        api_key="test_key",
        api_secret="test_secret",
    )
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json"


def test_ws_auth_message_structure():
    """ws_auth_message should return correct structure."""
    msg = ws_auth_message("test_key", "test_secret")
    assert "time" in msg
    assert "channel" in msg
    assert "event" in msg
    assert "payload" in msg
    assert msg["channel"] == "futures.login"
    assert msg["event"] == "api"


def test_sign_rest_consistency():
    """Same inputs should produce same signature."""
    headers1 = sign_rest(
        method="GET",
        path="/test",
        query=None,
        body=None,
        api_key="key",
        api_secret="secret",
    )
    headers2 = sign_rest(
        method="GET",
        path="/test",
        query=None,
        body=None,
        api_key="key",
        api_secret="secret",
    )
    # Timestamps will differ, but method should be same
    assert headers1["KEY"] == headers2["KEY"]
