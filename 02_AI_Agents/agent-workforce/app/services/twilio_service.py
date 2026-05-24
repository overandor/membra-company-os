from typing import Optional
from twilio.rest import Client
from app.core.config import settings
from app.core.logging import get_logger
from app.models.schemas import TwilioNotificationRequest

logger = get_logger("twilio_service")

class TwilioService:
    def __init__(self):
        self.client: Optional[Client] = None
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_number = settings.twilio_phone_number

    async def send_sms(self, req: TwilioNotificationRequest) -> dict:
        if not self.client:
            logger.warning("twilio_not_configured")
            return {"status": "skipped", "reason": "twilio_not_configured"}
        try:
            message = self.client.messages.create(
                to=req.to,
                from_=self.from_number,
                body=req.message,
                media_url=req.media_url,
            )
            logger.info("sms_sent", to=req.to, sid=message.sid, agent_id=req.agent_id)
            return {"status": "sent", "sid": message.sid, "to": req.to}
        except Exception as e:
            logger.error("sms_send_failed", to=req.to, error=str(e))
            return {"status": "error", "error": str(e)}

    async def send_voice(self, to: str, message: str, agent_id: Optional[str] = None) -> dict:
        if not self.client:
            return {"status": "skipped", "reason": "twilio_not_configured"}
        try:
            # Use TwiML to say the message
            from twilio.twiml.voice_response import VoiceResponse
            twiml = VoiceResponse()
            twiml.say(message, voice="Polly.Joanna")
            call = self.client.calls.create(
                to=to,
                from_=self.from_number,
                twiml=str(twiml),
            )
            logger.info("voice_call_initiated", to=to, sid=call.sid, agent_id=agent_id)
            return {"status": "initiated", "sid": call.sid, "to": to}
        except Exception as e:
            logger.error("voice_call_failed", to=to, error=str(e))
            return {"status": "error", "error": str(e)}

    async def lookup_phone(self, phone: str) -> dict:
        if not self.client:
            return {"status": "skipped"}
        try:
            info = self.client.lookups.v2.phone_numbers(phone).fetch()
            return {"phone": phone, "valid": info.valid, "carrier": info.carrier, "type": info.line_type_intelligence}
        except Exception as e:
            return {"phone": phone, "valid": False, "error": str(e)}

twilio_service = TwilioService()
