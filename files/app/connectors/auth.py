"""
auth.py — HMAC-SHA512 authentication helper.

Gate.io futures uses the same signature scheme for:
  • REST   — headers: KEY / SIGN / Timestamp
  • WS     — sign channel subscription payload with same function
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode


def _epoch_ms() -> int:
    return int(time.time() * 1000)


def _epoch_s() -> int:
    return int(time.time())


def epoch_ms() -> int:
    """Public epoch_ms function."""
    return _epoch_ms()


def sign_rest(
    method: str,
    path: str,
    query: Optional[Dict[str, Any]],
    body: Optional[Dict[str, Any]],
    api_key: str,
    api_secret: str,
) -> Dict[str, str]:
    """
    Build Gate.io REST auth headers.

    Signature input:
        "{METHOD}\n{PATH}\n{QUERY_STRING}\n{BODY_SHA512_HEX}\n{TIMESTAMP}"

    Returns dict of headers to merge into the request.
    """
    ts = str(_epoch_s())

    query_str   = urlencode(query) if query else ""
    body_str    = json.dumps(body, separators=(",", ":")) if body else ""
    body_hash   = hashlib.sha512(body_str.encode()).hexdigest()

    payload = f"{method}\n{path}\n{query_str}\n{body_hash}\n{ts}"
    signature = hmac.new(
        api_secret.encode(),
        payload.encode(),
        hashlib.sha512,
    ).hexdigest()

    return {
        "KEY":       api_key,
        "SIGN":      signature,
        "Timestamp": ts,
        "Content-Type": "application/json",
        "Accept":       "application/json",
    }


def sign_ws_channel(
    channel: str,
    event: str,
    api_key: str,
    api_secret: str,
) -> Dict[str, Any]:
    """
    Build Gate.io WS authentication message.

    Gate.io WS private auth:
        sign("channel={channel}\nevent={event}\ntime={ts}")
    """
    ts = _epoch_s()
    payload = f"channel={channel}\nevent={event}\ntime={ts}"
    signature = hmac.new(
        api_secret.encode(),
        payload.encode(),
        hashlib.sha512,
    ).hexdigest()

    return {
        "method": "api_key",
        "KEY":    api_key,
        "SIGN":   signature,
        "time":   ts,
    }


def ws_auth_message(api_key: str, api_secret: str) -> Dict[str, Any]:
    """
    Full WS login frame expected by Gate.io.

    Send once after connection is established, before subscribing to
    private channels (futures.orders, futures.usertrades, etc.).
    """
    ts = _epoch_s()
    payload = f"api_key={api_key}\nchannel=futures.orders\nevent=subscribe\ntime={ts}"
    signature = hmac.new(
        api_secret.encode(),
        payload.encode(),
        hashlib.sha512,
    ).hexdigest()

    return {
        "time":    ts,
        "channel": "futures.login",
        "event":   "api",
        "payload": {
            "api_key":  api_key,
            "signature": signature,
            "timestamp": str(ts),
        },
    }
