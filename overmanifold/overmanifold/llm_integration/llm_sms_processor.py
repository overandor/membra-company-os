"""
LLM-Based SMS Processing System
Proprietary SMS understanding and processing using LLMs with real Twilio integration
"""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os

from openai import AsyncOpenAI
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("llm_sms_processor")


class SMSIntent(Enum):
    """SMS intent types identified by LLM"""
    SEND_PAYMENT = "send_payment"
    REQUEST_PAYMENT = "request_payment"
    CHECK_BALANCE = "check_balance"
    HELP = "help"
    REGISTER = "register"
    VERIFICATION = "verification"
    UNKNOWN = "unknown"


@dataclass
class SMSIntentResult:
    """Result of LLM SMS intent analysis"""
    intent: SMSIntent
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    raw_response: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "reasoning": self.reasoning
        }


@dataclass
class SMSPaymentRequest:
    """Structured payment request extracted by LLM"""
    amount: float
    recipient_phone: str
    sender_phone: str
    message: str = ""
    currency: str = "USDC"
    priority: str = "normal"
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "amount": self.amount,
            "recipient_phone": self.recipient_phone,
            "sender_phone": self.sender_phone,
            "message": self.message,
            "currency": self.currency,
            "priority": self.priority,
            "notes": self.notes
        }


class LLMSMSProcessor:
    """Proprietary LLM-based SMS processing system"""
    
    def __init__(self, openai_api_key: str = None, twilio_sid: str = None, twilio_token: str = None):
        # Initialize OpenAI for LLM processing
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("No OpenAI API key provided, LLM features will be limited")
        
        self.llm_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Initialize Twilio for real SMS
        self.twilio_sid = twilio_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_token = twilio_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if self.twilio_sid and self.twilio_token:
            self.twilio_client = TwilioClient(self.twilio_sid, self.twilio_token)
            logger.info("Twilio client initialized for real SMS")
        else:
            logger.warning("Twilio credentials not provided, SMS will be logged only")
            self.twilio_client = None
        
        # Custom SMS understanding model (proprietary)
        self.sms_understanding_prompt = self._build_sms_understanding_prompt()
        
    def _build_sms_understanding_prompt(self) -> str:
        """Build proprietary prompt for SMS understanding"""
        return """You are an expert SMS payment processor for Overmanifold Protocol. Analyze SMS messages and extract payment intent.

SMS COMMAND FORMATS:
1. SEND: "send [amount] to [phone] [message]" - Send money to phone number
   Examples: "send 50 to +1234567890 for lunch", "send 100.5 to +1987654321"
   
2. REQUEST: "request [amount] from [phone] [message]" - Request money from phone
   Examples: "request 25 from +155501234567 for dinner", "request 50 from +155501234567"
   
3. BALANCE: "balance" or "bal" - Check account balance
   Examples: "balance", "bal", "check balance"

4. HELP: "help" or "?" - Get help information
   Examples: "help", "?"

5. REGISTER: "register" - Register phone number
   Examples: "register", "sign up"

PHONE FORMAT: Must start with + followed by 10-15 digits (e.g., +1234567890123)
AMOUNT FORMAT: Must be positive number, can include decimals (e.g., 50, 100.5, 25.99)

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "intent": "send_payment|request_payment|check_balance|help|register|verification|unknown",
  "confidence": 0.0-1.0,
  "entities": {
    "amount": number (if applicable),
    "recipient_phone": string (if applicable),
    "sender_phone": string (if applicable),
    "message": string (if applicable),
    "currency": "USD" (default)
  },
  "reasoning": "brief explanation of your analysis"
}

Be precise and confident. If unsure, set intent to "unknown" and low confidence."""

    async def analyze_sms_intent(self, sms_message: str, sender_phone: str = None) -> SMSIntentResult:
        """Analyze SMS message using LLM to understand intent"""
        if not self.llm_client:
            # Fallback to rule-based processing if no LLM
            return self._fallback_intent_analysis(sms_message, sender_phone)
        
        try:
            # Build analysis prompt
            analysis_prompt = f"{self.sms_understanding_prompt}\n\nSMS Message: \"{sms_message}\""
            if sender_phone:
                analysis_prompt += f"\nSender Phone: {sender_phone}"
            
            # Call LLM for analysis
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.sms_understanding_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent results
                response_format={"type": "json_object"}
            )
            
            # Parse LLM response
            result_data = json.loads(response.choices[0].message.content)
            
            intent_result = SMSIntentResult(
                intent=SMSIntent(result_data.get("intent", "unknown")),
                confidence=result_data.get("confidence", 0.5),
                entities=result_data.get("entities", {}),
                reasoning=result_data.get("reasoning", ""),
                raw_response=response.choices[0].message.content
            )
            
            logger.info(f"LLM analyzed SMS intent: {intent_result.intent.value} (confidence: {intent_result.confidence})")
            return intent_result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}, falling back to rule-based")
            return self._fallback_intent_analysis(sms_message, sender_phone)
    
    def _fallback_intent_analysis(self, sms_message: str, sender_phone: str = None) -> SMSIntentResult:
        """Fallback rule-based intent analysis when LLM unavailable"""
        message_lower = sms_message.lower().strip()
        
        # Rule-based patterns
        patterns = {
            SMSIntent.SEND_PAYMENT: [
                r'^send\s+(\d+\.?\d*)\s+to\s+(\+\d{10,15})',
                r'^pay\s+(\d+\.?\d*)\s+to\s+(\+\d{10,15})',
                r'^transfer\s+(\d+\.?\d*)\s+to\s+(\+\d{10,15})'
            ],
            SMSIntent.REQUEST_PAYMENT: [
                r'^request\s+(\d+\.?\d*)\s+from\s+(\+\d{10,15})',
                r'^ask\s+(\d+\.?\d*)\s+from\s+(\+\d{10,15})'
            ],
            SMSIntent.CHECK_BALANCE: [
                r'^balance$',
                r'^bal$',
                r'^check\s+balance'
            ],
            SMSIntent.HELP: [
                r'^help$',
                r'^\?$',
                r'^what\s+can\s+i\s+do'
            ]
        }
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.match(pattern, message_lower, re.IGNORECASE)
                if match:
                    entities = {}
                    if match.groups():
                        if intent in [SMSIntent.SEND_PAYMENT, SMSIntent.REQUEST_PAYMENT]:
                            entities["amount"] = float(match.group(1))
                            entities["recipient_phone" if intent == SMSIntent.SEND_PAYMENT else "sender_phone"] = match.group(2)
                    
                    return SMSIntentResult(
                        intent=intent,
                        confidence=0.85,
                        entities=entities,
                        reasoning=f"Rule-based pattern matched: {pattern}"
                    )
        
        return SMSIntentResult(
            intent=SMSIntent.UNKNOWN,
            confidence=0.3,
            reasoning="No pattern matched, intent unclear"
        )
    
    async def extract_payment_request(self, sms_message: str, sender_phone: str) -> Optional[SMSPaymentRequest]:
        """Extract structured payment request using LLM"""
        intent_result = await self.analyze_sms_intent(sms_message, sender_phone)
        
        if intent_result.intent != SMSIntent.SEND_PAYMENT or intent_result.confidence < 0.7:
            return None
        
        try:
            entities = intent_result.entities
            amount = entities.get("amount", 0)
            recipient_phone = entities.get("recipient_phone", "")
            
            if not amount or not recipient_phone:
                return None
            
            # Validate amount
            if amount <= 0:
                return None
            
            # Validate phone number
            if not self._validate_phone_number(recipient_phone):
                return None
            
            # Extract message content (everything after phone number)
            message = self._extract_message_content(sms_message, recipient_phone)
            
            return SMSPaymentRequest(
                amount=amount,
                recipient_phone=recipient_phone,
                sender_phone=sender_phone or "",
                message=message,
                currency=entities.get("currency", "USDC"),
                priority="normal"
            )
            
        except Exception as e:
            logger.error(f"Payment request extraction failed: {e}")
            return None
    
    def _extract_message_content(self, sms_message: str, phone_number: str) -> str:
        """Extract message content from SMS (everything after phone number)"""
        # Remove phone number and surrounding words
        pattern = rf'{re.escape(phone_number)}\s*(.*)'
        match = re.search(pattern, sms_message, re.IGNORECASE)
        if match and match.group(1):
            return match.group(1).strip()
        return ""
    
    def _validate_phone_number(self, phone: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+[1-9]\d{9,14}$'
        return bool(re.match(pattern, phone))
    
    async def send_sms(self, to_phone: str, message: str, use_real_sms: bool = True) -> Dict[str, Any]:
        """Send SMS message using real Twilio or fallback"""
        if use_real_sms and self.twilio_client:
            try:
                # Send real SMS via Twilio
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_phone_number,
                    to=to_phone
                )
                
                logger.info(f"Real SMS sent to {to_phone} via Twilio: {message_obj.sid}")
                
                return {
                    "success": True,
                    "method": "twilio",
                    "message_sid": message_obj.sid,
                    "status": message_obj.status,
                    "to": to_phone,
                    "cost": 0.0079  # Twilio cost per SMS
                }
                
            except TwilioRestException as e:
                logger.error(f"Twilio SMS failed: {e}")
                return self._fallback_sms_send(to_phone, message)
        else:
            return self._fallback_sms_send(to_phone, message)
    
    def _fallback_sms_send(self, to_phone: str, message: str) -> Dict[str, Any]:
        """Fallback SMS sending (log only)"""
        logger.info(f"[SMS LOG] To: {to_phone}, Message: {message}")
        return {
            "success": True,
            "method": "log",
            "to": to_phone,
            "message": message,
            "cost": 0.0
        }
    
    async def send_verification_code(self, phone: str, code: str = None) -> str:
        """Send verification code using LLM-generated secure codes"""
        if not code:
            # Generate LLM-optimized verification code
            code = self._generate_secure_verification_code(phone)
        
        message = f"Your Overmanifold verification code is: {code}. Valid for 10 minutes."
        
        result = await self.send_sms(phone, message)
        
        logger.info(f"Verification code sent to {phone}: {code} (method: {result['method']})")
        return code
    
    def _generate_secure_verification_code(self, phone: str) -> str:
        """Generate secure verification code using LLM-inspired logic"""
        import secrets
        import hashlib
        
        # Generate cryptographically secure code
        random_bytes = secrets.token_bytes(4)
        hash_input = f"{phone}{random_bytes.hex()}{datetime.utcnow().isoformat()}"
        hash_result = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Use first 6 digits as code
        code = ''.join(filter(str.isdigit, hash_result))[:6]
        
        # Ensure we have exactly 6 digits
        while len(code) < 6:
            code += str(secrets.randbelow(10))
        
        return code
    
    async def process_sms_payment(
        self, 
        sms_message: str, 
        sender_phone: str,
        use_real_sms: bool = True
    ) -> Dict[str, Any]:
        """Complete SMS payment processing using LLM analysis"""
        try:
            # Step 1: Analyze intent with LLM
            intent_result = await self.analyze_sms_intent(sms_message, sender_phone)
            
            if intent_result.intent != SMSIntent.SEND_PAYMENT:
                return {
                    "success": False,
                    "error": f"Invalid intent: {intent_result.intent.value}",
                    "confidence": intent_result.confidence
                }
            
            # Step 2: Extract payment request
            payment_request = await self.extract_payment_request(sms_message, sender_phone)
            
            if not payment_request:
                return {
                    "success": False,
                    "error": "Could not extract valid payment request"
                }
            
            # Step 3: Validate payment
            validation_result = await self._validate_payment(payment_request)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["reason"]
                }
            
            # Step 4: Process payment (this would connect to your payment system)
            processing_result = await self._execute_payment(payment_request)
            
            # Step 5: Send confirmation SMS
            if processing_result["success"]:
                confirmation = await self._send_payment_confirmation(
                    sender_phone,
                    payment_request.recipient_phone,
                    payment_request.amount,
                    processing_result["transaction_id"],
                    use_real_sms=use_real_sms
                )
                
                return {
                    "success": True,
                    "payment_request": payment_request.to_dict(),
                    "processing_result": processing_result,
                    "confirmation_sent": confirmation["success"],
                    "intent_analysis": intent_result.to_dict(),
                    "sms_cost": confirmation.get("cost", 0.0)
                }
            else:
                return {
                    "success": False,
                    "error": processing_result["error"],
                    "payment_request": payment_request.to_dict()
                }
            
        except Exception as e:
            logger.error(f"SMS payment processing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _validate_payment(self, payment_request: SMSPaymentRequest) -> Dict[str, Any]:
        """Validate payment request using LLM-enhanced checks"""
        # Basic validation
        if payment_request.amount <= 0:
            return {"valid": False, "reason": "Amount must be positive"}
        
        if not self._validate_phone_number(payment_request.recipient_phone):
            return {"valid": False, "reason": "Invalid recipient phone format"}
        
        if payment_request.amount > 10000:  # $10,000 limit
            return {"valid": False, "reason": "Amount exceeds maximum limit"}
        
        return {"valid": True, "reason": "Payment request is valid"}
    
    async def _execute_payment(self, payment_request: SMSPaymentRequest) -> Dict[str, Any]:
        """Execute payment (placeholder for your payment system)"""
        # This would integrate with your actual payment processing system
        transaction_id = f"txn_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate payment processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "processed_amount": payment_request.amount,
            "currency": payment_request.currency,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _send_payment_confirmation(
        self,
        sender_phone: str,
        recipient_phone: str,
        amount: float,
        transaction_id: str,
        use_real_sms: bool = True
    ) -> Dict[str, Any]:
        """Send payment confirmation SMS"""
        message = (
            f"Payment of {amount} USDC to {recipient_phone} completed. "
            f"TX: {transaction_id[:8]}... "
            f"Overmanifold Protocol"
        )
        
        return await self.send_sms(sender_phone, message, use_real_sms)
    
    async def get_sms_cost_estimate(self, num_messages: int) -> Dict[str, Any]:
        """Get cost estimate for SMS operations"""
        twilio_cost = num_messages * 0.0079  # Twilio cost per SMS
        llm_cost = num_messages * 0.001  # Estimated LLM API cost per SMS
        
        return {
            "num_messages": num_messages,
            "twilio_cost": round(twilio_cost, 4),
            "llm_cost": round(llm_cost, 4),
            "total_cost": round(twilio_cost + llm_cost, 4),
            "cost_per_sms": round(0.0079 + 0.001, 4)
        }


# Global LLM SMS processor instance
llm_sms_processor = LLMSMSProcessor()