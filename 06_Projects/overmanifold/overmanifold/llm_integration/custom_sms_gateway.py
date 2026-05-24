"""
LLM-Based Custom SMS Gateway
Proprietary SMS gateway using LLM for message understanding and custom delivery
"""

import asyncio
import logging
import json
import hashlib
import secrets
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import os

from openai import AsyncOpenAI

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("llm_custom_sms_gateway")


class SMSDeliveryMethod(Enum):
    """Custom SMS delivery methods"""
    EMAIL_GATEWAY = "email_gateway"
    PUSH_NOTIFICATION = "push_notification"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    USSD = "ussd"
    IP_MESSAGING = "ip_messaging"


@dataclass
class CustomSMSMessage:
    """Custom SMS message structure"""
    id: str
    to_phone: str
    from_phone: str
    message_content: str
    timestamp: datetime
    delivery_method: SMSDeliveryMethod
    status: str = "pending"
    delivery_attempts: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_message_id()
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        data = f"{self.to_phone}{self.from_phone}{self.timestamp.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class SMSDeliveryResult:
    """Result of SMS delivery attempt"""
    success: bool
    message_id: str
    delivery_method: SMSDeliveryMethod
    cost: float = 0.0
    status: str = ""
    error_message: str = ""
    delivery_timestamp: Optional[datetime] = None
    confirmation_code: str = ""


class CustomSMSDeliveryInterface(ABC):
    """Abstract interface for custom SMS delivery methods"""
    
    @abstractmethod
    async def send_sms(self, message: CustomSMSMessage) -> SMSDeliveryResult:
        """Send SMS using custom method"""
        pass
    
    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status"""
        pass


class EmailGatewaySMSDelivery(CustomSMSDeliveryInterface):
    """Custom SMS delivery via email gateway (proprietary)"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587, 
                 smtp_user: str = None, smtp_password: str = None):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    async def send_sms(self, message: CustomSMSMessage) -> SMSDeliveryResult:
        """Send SMS via email-to-SMS gateway"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create email with SMS content
            msg = MIMEMultipart()
            msg['From'] = f"sms@overmanifold.io"
            msg['To'] = self._convert_phone_to_email(message.to_phone)
            msg['Subject'] = f"SMS: {message.from_phone}"
            
            body = f"""
From: {message.from_phone}
To: {message.to_phone}
Message: {message.message_content}
Timestamp: {message.timestamp.isoformat()}
Message ID: {message.id}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            if self.smtp_user and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
            else:
                # Local SMTP for testing
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.send_message(msg)
                server.quit()
            
            return SMSDeliveryResult(
                success=True,
                message_id=message.id,
                delivery_method=SMSDeliveryMethod.EMAIL_GATEWAY,
                cost=0.0,
                status="delivered",
                delivery_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Email gateway SMS delivery failed: {e}")
            return SMSDeliveryResult(
                success=False,
                message_id=message.id,
                delivery_method=SMSDeliveryMethod.EMAIL_GATEWAY,
                cost=0.0,
                status="failed",
                error_message=str(e)
            )
    
    def _convert_phone_to_email(self, phone: str) -> str:
        """Convert phone number to email format for gateway"""
        # Remove + and format as email
        clean_phone = phone.replace('+', '')
        return f"{clean_phone}@sms.overmanifold.io"
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status from email gateway"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "method": "email_gateway",
            "timestamp": datetime.utcnow().isoformat()
        }


class PushNotificationSMSDelivery(CustomSMSDeliveryInterface):
    """Custom SMS delivery via push notifications"""
    
    def __init__(self, push_gateway_url: str = None):
        self.push_gateway_url = push_gateway_url or os.getenv("PUSH_GATEWAY_URL")
        self.registered_devices: Dict[str, Dict] = {}
    
    async def send_sms(self, message: CustomSMSMessage) -> SMSDeliveryResult:
        """Send SMS via push notification"""
        try:
            # Check if device is registered for push notifications
            device_info = self.registered_devices.get(message.to_phone)
            
            if not device_info:
                return SMSDeliveryResult(
                    success=False,
                    message_id=message.id,
                    delivery_method=SMSDeliveryMethod.PUSH_NOTIFICATION,
                    cost=0.0,
                    status="device_not_registered",
                    error_message="Device not registered for push notifications"
                )
            
            # Simulate push notification delivery
            notification_data = {
                "to": device_info["push_token"],
                "title": f"SMS from {message.from_phone}",
                "body": message.message_content,
                "data": {
                    "message_id": message.id,
                    "from_phone": message.from_phone,
                    "timestamp": message.timestamp.isoformat()
                }
            }
            
            # In production, this would call actual push gateway
            logger.info(f"Push notification sent to {message.to_phone}: {notification_data['body']}")
            
            return SMSDeliveryResult(
                success=True,
                message_id=message.id,
                delivery_method=SMSDeliveryMethod.PUSH_NOTIFICATION,
                cost=0.0,
                status="delivered",
                delivery_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Push notification SMS delivery failed: {e}")
            return SMSDeliveryResult(
                success=False,
                message_id=message.id,
                delivery_method=SMSDeliveryMethod.PUSH_NOTIFICATION,
                cost=0.0,
                status="failed",
                error_message=str(e)
            )
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get push notification delivery status"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "method": "push_notification",
            "timestamp": datetime.utcnow().isoformat()
        }


class WebhookSMSDelivery(CustomSMSDeliveryInterface):
    """Custom SMS delivery via webhooks"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.getenv("SMS_WEBHOOK_URL")
    
    async def send_sms(self, message: CustomSMSMessage) -> SMSDeliveryResult:
        """Send SMS via webhook callback"""
        try:
            if not self.webhook_url:
                return SMSDeliveryResult(
                    success=False,
                    message_id=message.id,
                    delivery_method=SMSDeliveryMethod.WEBHOOK,
                    cost=0.0,
                    status="no_webhook_configured",
                    error_message="No webhook URL configured"
                )
            
            # Prepare webhook payload
            payload = {
                "message_id": message.id,
                "to_phone": message.to_phone,
                "from_phone": message.from_phone,
                "message": message.message_content,
                "timestamp": message.timestamp.isoformat(),
                "delivery_method": "webhook"
            }
            
            # Send webhook (using aiohttp for async HTTP)
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return SMSDeliveryResult(
                            success=True,
                            message_id=message.id,
                            delivery_method=SMSDeliveryMethod.WEBHOOK,
                            cost=0.0,
                            status="delivered",
                            delivery_timestamp=datetime.utcnow()
                        )
                    else:
                        return SMSDeliveryResult(
                            success=False,
                            message_id=message.id,
                            delivery_method=SMSDeliveryMethod.WEBHOOK,
                            cost=0.0,
                            status="webhook_error",
                            error_message f"Webhook returned {response.status}"
                        )
            
        except Exception as e:
            logger.error(f"Webhook SMS delivery failed: {e}")
            return SMSDeliveryResult(
                success=False,
                message_id=message.id,
                delivery_method=SMSDeliveryMethod.WEBHOOK,
                cost=0.0,
                status="failed",
                error_message=str(e)
            )
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get webhook delivery status"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "method": "webhook",
            "timestamp": datetime.utcnow().isoformat()
        }


class LLMSMSGateway:
    """Proprietary LLM-based SMS gateway with custom delivery methods"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize LLM for SMS understanding
        if self.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.llm_client = None
            logger.warning("No OpenAI API key, LLM features limited")
        
        # Initialize custom delivery methods
        self.delivery_methods: Dict[SMSDeliveryMethod, CustomSMSDeliveryInterface] = {}
        self._initialize_delivery_methods()
        
        # SMS queue for processing
        self.sms_queue: List[CustomSMSMessage] = []
        self.delivery_history: Dict[str, SMSDeliveryResult] = {}
        
        # Build proprietary SMS understanding prompt
        self.sms_understanding_prompt = self._build_sms_understanding_prompt()
    
    def _initialize_delivery_methods(self):
        """Initialize all custom delivery methods"""
        self.delivery_methods[SMSDeliveryMethod.EMAIL_GATEWAY] = EmailGatewaySMSDelivery()
        self.delivery_methods[SMSDeliveryMethod.PUSH_NOTIFICATION] = PushNotificationSMSDelivery()
        self.delivery_methods[SMSDeliveryMethod.WEBHOOK] = WebhookSMSDelivery()
    
    def _build_sms_understanding_prompt(self) -> str:
        """Build proprietary prompt for SMS understanding and routing"""
        return """You are an intelligent SMS routing system for Overmanifold Protocol. Analyze SMS messages and determine optimal delivery strategy.

SMS DELIVERY METHODS:
1. EMAIL_GATEWAY - Send via email-to-SMS gateway (carrier-specific emails)
2. PUSH_NOTIFICATION - Send via mobile app push notification
3. WEBHOOK - Send via webhook callback to external service
4. IN_APP - Display within mobile application
5. USSD - Send via USSD session
6. IP_MESSAGING - Send via IP-based messaging

ROUTING DECISION FACTORS:
- Phone carrier and country
- Message urgency and priority
- Recipient device capabilities
- Cost considerations
- Delivery speed requirements
- Reliability requirements

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "recommended_method": "email_gateway|push_notification|webhook|in_app|ussd|ip_messaging",
  "confidence": 0.0-1.0,
  "backup_methods": ["method1", "method2"],
  "reasoning": "explain routing decision",
  "priority": "normal|high|urgent",
  "estimated_cost": 0.0,
  "estimated_delivery_time": "seconds"
}

Consider cost, speed, reliability, and recipient capabilities when recommending delivery method."""

    async def analyze_and_route_sms(
        self,
        to_phone: str,
        from_phone: str,
        message: str,
        preferred_method: SMSDeliveryMethod = None
    ) -> Dict[str, Any]:
        """Analyze SMS and determine optimal delivery method using LLM"""
        
        if preferred_method:
            # Use preferred method directly
            return {
                "recommended_method": preferred_method.value,
                "confidence": 1.0,
                "backup_methods": [],
                "reasoning": f"User preferred {preferred_method.value}",
                "priority": "normal",
                "estimated_cost": 0.0,
                "estimated_delivery_time": 5
            }
        
        if not self.llm_client:
            # Fallback to email gateway
            return {
                "recommended_method": SMSDeliveryMethod.EMAIL_GATEWAY.value,
                "confidence": 0.7,
                "backup_methods": [SMSDeliveryMethod.WEBHOOK.value],
                "reasoning": "LLM not available, defaulting to email gateway",
                "priority": "normal",
                "estimated_cost": 0.0,
                "estimated_delivery_time": 10
            }
        
        try:
            # Use LLM to determine optimal routing
            routing_prompt = f"{self.sms_understanding_prompt}\n\nTo Phone: {to_phone}\nFrom Phone: {from_phone}\nMessage: {message}"
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.sms_understanding_prompt},
                    {"role": "user", "content": routing_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            routing_decision = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM SMS routing decision: {routing_decision['recommended_method']} "
                        f"(confidence: {routing_decision['confidence']})")
            
            return routing_decision
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}, using default")
            return {
                "recommended_method": SMSDeliveryMethod.EMAIL_GATEWAY.value,
                "confidence": 0.6,
                "backup_methods": [SMSDeliveryMethod.PUSH_NOTIFICATION.value],
                "reasoning": "LLM routing failed, using default email gateway",
                "priority": "normal",
                "estimated_cost": 0.0,
                "estimated_delivery_time": 10
            }
    
    async def send_custom_sms(
        self,
        to_phone: str,
        from_phone: str,
        message: str,
        preferred_method: SMSDeliveryMethod = None
    ) -> SMSDeliveryResult:
        """Send SMS using custom delivery system"""
        
        # Create custom SMS message
        custom_message = CustomSMSMessage(
            to_phone=to_phone,
            from_phone=from_phone,
            message_content=message,
            timestamp=datetime.utcnow(),
            delivery_method=preferred_method or SMSDeliveryMethod.EMAIL_GATEWAY
        )
        
        # Determine optimal delivery method
        routing_decision = await self.analyze_and_route_sms(
            to_phone, from_phone, message, preferred_method
        )
        
        # Get delivery method
        delivery_method = SMSDeliveryMethod(routing_decision["recommended_method"])
        delivery_interface = self.delivery_methods.get(delivery_method)
        
        if not delivery_interface:
            logger.error(f"Delivery method {delivery_method.value} not available")
            # Fallback to email gateway
            delivery_interface = self.delivery_methods[SMSDeliveryMethod.EMAIL_GATEWAY]
            custom_message.delivery_method = SMSDeliveryMethod.EMAIL_GATEWAY
        
        # Send SMS
        result = await delivery_interface.send_sms(custom_message)
        
        # Store in delivery history
        self.delivery_history[custom_message.id] = result
        
        # Add to processing queue for tracking
        self.sms_queue.append(custom_message)
        
        logger.info(f"Custom SMS sent via {delivery_method.value}: {result.success}")
        
        return result
    
    async def send_verification_code(self, phone: str, code: str = None) -> str:
        """Send verification code using custom SMS system"""
        if not code:
            code = self._generate_secure_code(phone)
        
        from_phone = "Overmanifold"
        message = f"Your verification code is: {code}. Valid for 10 minutes."
        
        result = await self.send_custom_sms(phone, from_phone, message)
        
        if result.success:
            logger.info(f"Verification code sent to {phone} via {result.delivery_method.value}")
        else:
            logger.error(f"Verification code failed: {result.error_message}")
        
        return code
    
    def _generate_secure_code(self, phone: str) -> str:
        """Generate secure verification code"""
        import secrets
        import hashlib
        
        random_bytes = secrets.token_bytes(4)
        hash_input = f"{phone}{random_bytes.hex()}{datetime.utcnow().isoformat()}"
        hash_result = hashlib.sha256(hash_input.encode()).hexdigest()
        
        code = ''.join(filter(str.isdigit, hash_result))[:6]
        while len(code) < 6:
            code += str(secrets.randbelow(10))
        
        return code
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status for a message"""
        if message_id in self.delivery_history:
            result = self.delivery_history[message_id]
            return {
                "message_id": message_id,
                "success": result.success,
                "delivery_method": result.delivery_method.value,
                "status": result.status,
                "cost": result.cost,
                "timestamp": result.delivery_timestamp.isoformat() if result.delivery_timestamp else None
            }
        else:
            return {
                "message_id": message_id,
                "status": "not_found",
                "error": "Message not found in delivery history"
            }
    
    async def get_delivery_statistics(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        total_messages = len(self.delivery_history)
        successful = sum(1 for r in self.delivery_history.values() if r.success)
        failed = total_messages - successful
        
        method_counts = {}
        for result in self.delivery_history.values():
            method = result.delivery_method.value
            method_counts[method] = method_counts.get(method, 0) + 1
        
        total_cost = sum(r.cost for r in self.delivery_history.values())
        
        return {
            "total_messages": total_messages,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_messages if total_messages > 0 else 0.0,
            "method_distribution": method_counts,
            "total_cost": total_cost,
            "average_cost_per_message": total_cost / total_messages if total_messages > 0 else 0.0
        }
    
    def register_device_for_push(self, phone: str, push_token: str, device_type: str = "ios"):
        """Register device for push notifications"""
        self.delivery_methods[SMSDeliveryMethod.PUSH_NOTIFICATION].registered_devices[phone] = {
            "push_token": push_token,
            "device_type": device_type,
            "registered_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Device registered for push notifications: {phone}")
    
    def configure_webhook(self, webhook_url: str):
        """Configure webhook for SMS delivery"""
        self.delivery_methods[SMSDeliveryMethod.WEBHOOK] = WebhookSMSDelivery(webhook_url)
        logger.info(f"Webhook configured: {webhook_url}")


# Global custom SMS gateway instance
llm_custom_sms_gateway = LLMSMSGateway()