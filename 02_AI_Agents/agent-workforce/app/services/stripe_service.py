import stripe
from typing import Dict, List, Optional
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import StripeCheckoutRequest, StripeCheckoutResponse, BillingRecord

logger = get_logger("stripe_service")

class StripeService:
    def __init__(self):
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret

    async def create_agent_product(self, agent_id: str, name: str, description: str, price_cents: int) -> Dict:
        try:
            product = stripe.Product.create(
                name=f"Agent: {name}",
                description=description,
                metadata={"agent_id": agent_id, "type": "agent_worker"},
            )
            price = stripe.Price.create(
                product=product.id,
                unit_amount=price_cents,
                currency="usd",
                metadata={"agent_id": agent_id},
            )
            logger.info("agent_product_created", agent_id=agent_id, product_id=product.id, price_id=price.id)
            return {"product_id": product.id, "price_id": price.id, "agent_id": agent_id}
        except Exception as e:
            logger.error("create_agent_product_failed", agent_id=agent_id, error=str(e))
            raise

    async def create_checkout(self, req: StripeCheckoutRequest) -> StripeCheckoutResponse:
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"Agent Run: {req.agent_id}"},
                        "unit_amount": 100,  # $1.00 per run baseline
                    },
                    "quantity": req.quantity,
                }],
                mode="payment",
                success_url=req.success_url,
                cancel_url=req.cancel_url,
                customer_email=req.customer_email,
                metadata={"agent_id": req.agent_id},
            )
            return StripeCheckoutResponse(session_id=session.id, url=session.url)
        except Exception as e:
            logger.error("checkout_creation_failed", agent_id=req.agent_id, error=str(e))
            raise

    async def create_subscription(self, agent_id: str, customer_email: str, price_id: str, success_url: str, cancel_url: str) -> Dict:
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer_email,
                metadata={"agent_id": agent_id, "type": "subscription"},
            )
            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            logger.error("subscription_creation_failed", agent_id=agent_id, error=str(e))
            raise

    async def get_billing_records(self, customer_id: str, limit: int = 100) -> List[BillingRecord]:
        records = []
        try:
            charges = stripe.Charge.list(customer=customer_id, limit=limit)
            for ch in charges.auto_paging_iter():
                records.append(BillingRecord(
                    agent_id=ch.metadata.get("agent_id", "unknown"),
                    customer_id=customer_id,
                    amount_cents=ch.amount,
                    currency=ch.currency,
                    status=ch.status,
                    metadata={"charge_id": ch.id, "receipt_url": ch.receipt_url},
                ))
        except Exception as e:
            logger.error("billing_records_failed", customer_id=customer_id, error=str(e))
        return records

    async def process_usage_billing(self, agent_id: str, customer_id: str, usage_units: int, unit_price_cents: int = 1):
        try:
            amount = usage_units * unit_price_cents
            logger.info("usage_billed", agent_id=agent_id, customer_id=customer_id, amount_cents=amount)
            return {"billed_cents": amount, "units": usage_units}
        except Exception as e:
            logger.error("usage_billing_failed", agent_id=agent_id, error=str(e))
            raise

stripe_service = StripeService()
