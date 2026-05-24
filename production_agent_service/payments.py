#!/usr/bin/env python3
"""
Stripe Payment Integration
Handles checkout sessions, payment verification, and usage credits.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

# Pricing tiers (credits = number of project appraisals)
PRICING_TIERS = {
    "starter": {"price_cents": 1900, "credits": 5, "label": "Starter — 5 Projects"},
    "pro": {"price_cents": 4900, "credits": 20, "label": "Pro — 20 Projects"},
    "enterprise": {"price_cents": 14900, "credits": 100, "label": "Enterprise — 100 Projects"},
}


try:
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    STRIPE_AVAILABLE = bool(STRIPE_SECRET_KEY)
except ImportError:
    stripe = None  # type: ignore
    STRIPE_AVAILABLE = False


@dataclass
class PaymentIntent:
    tier: str
    session_id: str
    url: str
    status: str
    credits: int


class PaymentManager:
    def __init__(self):
        self.enabled = STRIPE_AVAILABLE and stripe is not None

    def create_checkout_session(self, tier: str, success_url: str, cancel_url: str) -> Optional[PaymentIntent]:
        if not self.enabled:
            return None
        if tier not in PRICING_TIERS:
            return None
        tier_info = PRICING_TIERS[tier]
        try:
            session = stripe.checkout.Session.create(  # type: ignore
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": tier_info["label"]},
                        "unit_amount": tier_info["price_cents"],
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"tier": tier, "credits": str(tier_info["credits"])},
            )
            return PaymentIntent(
                tier=tier,
                session_id=session.id,
                url=session.url,
                status=session.status,
                credits=tier_info["credits"],
            )
        except Exception as e:
            print(f"Stripe checkout error: {e}")
            return None

    def verify_session(self, session_id: str) -> Optional[dict]:
        if not self.enabled or not stripe:
            return None
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                "id": session.id,
                "status": session.status,
                "payment_status": session.payment_status,
                "tier": session.metadata.get("tier") if session.metadata else None,
                "credits": int(session.metadata.get("credits", 0)) if session.metadata else 0,
                "amount_total": session.amount_total,
            }
        except Exception as e:
            print(f"Stripe verify error: {e}")
            return None

    def handle_webhook(self, payload: bytes, sig_header: str) -> Optional[dict]:
        if not self.enabled or not stripe:
            return None
        try:
            event = stripe.Webhook.construct_event(  # type: ignore
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                return {
                    "event": "payment_completed",
                    "session_id": session["id"],
                    "tier": session.get("metadata", {}).get("tier"),
                    "credits": int(session.get("metadata", {}).get("credits", 0)),
                }
            return {"event": event["type"], "raw": event}
        except Exception as e:
            print(f"Webhook error: {e}")
            return None


# Simple in-memory credit tracker (replace with DB in production)
_user_credits: dict = {}


def get_credits(user_id: str) -> int:
    return _user_credits.get(user_id, 0)


def add_credits(user_id: str, amount: int) -> int:
    _user_credits[user_id] = _user_credits.get(user_id, 0) + amount
    return _user_credits[user_id]


def consume_credit(user_id: str) -> bool:
    current = _user_credits.get(user_id, 0)
    if current > 0:
        _user_credits[user_id] = current - 1
        return True
    return False


def get_pricing() -> dict:
    return {
        "currency": "usd",
        "tiers": {
            k: {
                "price_usd": v["price_cents"] / 100,
                "credits": v["credits"],
                "label": v["label"],
            }
            for k, v in PRICING_TIERS.items()
        },
    }
