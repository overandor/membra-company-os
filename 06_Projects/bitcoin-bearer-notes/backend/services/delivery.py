"""SMS/Email delivery provider abstraction for CoinPack claim links."""
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional

from core.config import settings

logger = logging.getLogger(__name__)


class DeliveryProvider(ABC):
    """Abstract base for claim link delivery."""

    @abstractmethod
    async def send_sms(self, to: str, message: str) -> dict:
        pass

    @abstractmethod
    async def send_email(self, to: str, subject: str, html: str) -> dict:
        pass

    async def send_claim_link(
        self, destination: str, claim_url: str, pin: str, expires_at: str, assets: list
    ) -> dict:
        """Send a CoinPack claim link via the appropriate channel."""
        asset_summary = ", ".join(f"{a['amount']} {a['type']}" for a in assets)
        message = (
            f"You received a CoinPack: {asset_summary}. "
            f"Claim at: {claim_url} | PIN: {pin} | Expires: {expires_at}"
        )
        if "@" in destination:
            return await self.send_email(
                to=destination,
                subject="Your Membra CoinPack",
                html=f"<p>{message}</p><p><a href='{claim_url}'>Claim Now</a></p>",
            )
        return await self.send_sms(to=destination, message=message)


class ConsoleProvider(DeliveryProvider):
    """Development-only provider that logs to console."""

    async def send_sms(self, to: str, message: str) -> dict:
        masked = message
        if len(message) > 80:
            masked = message[:40] + "..." + message[-20:]
        logger.info("[DEV SMS] to=%s msg=%s", to, masked)
        return {"status": "sent", "channel": "console", "to": to}

    async def send_email(self, to: str, subject: str, html: str) -> dict:
        logger.info("[DEV EMAIL] to=%s subject=%s", to, subject)
        return {"status": "sent", "channel": "console", "to": to}


class TwilioProvider(DeliveryProvider):
    """Twilio SMS provider."""

    def __init__(self):
        from twilio.rest import Client as TwilioClient
        self.client = TwilioClient(
            settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_FROM_NUMBER

    async def send_sms(self, to: str, message: str) -> dict:
        try:
            msg = self.client.messages.create(body=message, from_=self.from_number, to=to)
            return {"status": "sent", "channel": "twilio", "sid": msg.sid}
        except Exception as e:
            logger.error("Twilio SMS failed: %s", e)
            return {"status": "failed", "error": str(e)}

    async def send_email(self, to: str, subject: str, html: str) -> dict:
        return {"status": "skipped", "reason": "Twilio does not support email"}


class SendGridProvider(DeliveryProvider):
    """SendGrid email provider."""

    def __init__(self):
        from sendgrid import SendGridAPIClient
        self.sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    async def send_sms(self, to: str, message: str) -> dict:
        return {"status": "skipped", "reason": "SendGrid does not support SMS"}

    async def send_email(self, to: str, subject: str, html: str) -> dict:
        from sendgrid.helpers.mail import Mail
        try:
            mail = Mail(from_email="noreply@membra.io", to_emails=to, subject=subject, html_content=html)
            response = self.sg.send(mail)
            return {"status": "sent", "channel": "sendgrid", "status_code": response.status_code}
        except Exception as e:
            logger.error("SendGrid email failed: %s", e)
            return {"status": "failed", "error": str(e)}


def get_delivery_provider() -> DeliveryProvider:
    """Factory: returns the first configured provider, falling back to Console."""
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_NUMBER:
        return TwilioProvider()
    if settings.SENDGRID_API_KEY:
        return SendGridProvider()
    return ConsoleProvider()
