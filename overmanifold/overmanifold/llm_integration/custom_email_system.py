"""
LLM-Based Custom Email System
Proprietary email system using LLM for email understanding and custom delivery
"""

import asyncio
import logging
import json
import hashlib
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import os
import re

from openai import AsyncOpenAI

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("llm_custom_email_system")


class EmailDeliveryMethod(Enum):
    """Custom email delivery methods"""
    SMTP = "smtp"
    API = "api"
    QUEUE = "queue"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    PUSH = "push"
    DIRECT = "direct"


@dataclass
class CustomEmailMessage:
    """Custom email message structure"""
    id: str
    to_email: str
    from_email: str
    subject: str
    body: str
    html_body: str = ""
    attachments: List[str] = field(default_factory=list)
    priority: str = "normal"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    delivery_method: EmailDeliveryMethod = EmailDeliveryMethod.SMTP
    status: str = "pending"
    delivery_attempts: int = 0
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_message_id()
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        data = f"{self.to_email}{self.from_email}{self.subject}{self.timestamp.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class EmailDeliveryResult:
    """Result of email delivery attempt"""
    success: bool
    message_id: str
    delivery_method: EmailDeliveryMethod
    cost: float = 0.0
    status: str = ""
    error_message: str = ""
    delivery_timestamp: Optional[datetime] = None
    server_response: str = ""


class CustomEmailDeliveryInterface(ABC):
    """Abstract interface for custom email delivery methods"""
    
    @abstractmethod
    async def send_email(self, message: CustomEmailMessage) -> EmailDeliveryResult:
        """Send email using custom method"""
        pass
    
    @abstractmethod
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status"""
        pass


class SMTPEmailDelivery(CustomEmailDeliveryInterface):
    """Custom SMTP email delivery (proprietary implementation)"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = 587,
                 smtp_user: str = None, smtp_password: str = None,
                 use_tls: bool = True):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user or os.getenv("SMTP_USERNAME")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls
    
    async def send_email(self, message: CustomEmailMessage) -> EmailDeliveryResult:
        """Send email via custom SMTP implementation"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = message.from_email
            msg['To'] = message.to_email
            msg['Subject'] = message.subject
            
            # Add body
            if message.html_body:
                msg.attach(MIMEText(message.html_body, 'html'))
                msg.attach(MIMEText(message.body, 'plain'))
            else:
                msg.attach(MIMEText(message.body, 'plain'))
            
            # Add attachments
            for attachment in message.attachments:
                with open(attachment, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                msg.attach(part)
            
            # Send via SMTP
            if self.smtp_user and self.smtp_password:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
                server.quit()
            else:
                # Local SMTP for testing
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.send_message(msg)
                server.quit()
            
            return EmailDeliveryResult(
                success=True,
                message_id=message.id,
                delivery_method=EmailDeliveryMethod.SMTP,
                cost=0.0,
                status="delivered",
                delivery_timestamp=datetime.utcnow(),
                server_response="Message sent successfully"
            )
            
        except Exception as e:
            logger.error(f"SMTP email delivery failed: {e}")
            return EmailDeliveryResult(
                success=False,
                message_id=message.id,
                delivery_method=EmailDeliveryMethod.SMTP,
                cost=0.0,
                status="failed",
                error_message=str(e)
            )
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get SMTP delivery status"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "method": "smtp",
            "timestamp": datetime.utcnow().isoformat()
        }


class APIEmailDelivery(CustomEmailDeliveryInterface):
    """Custom API email delivery via proprietary API"""
    
    def __init__(self, api_endpoint: str = None, api_key: str = None):
        self.api_endpoint = api_endpoint or os.getenv("EMAIL_API_ENDPOINT")
        self.api_key = api_key or os.getenv("EMAIL_API_KEY")
    
    async def send_email(self, message: CustomEmailMessage) -> EmailDeliveryResult:
        """Send email via custom API"""
        try:
            if not self.api_endpoint:
                return EmailDeliveryResult(
                    success=False,
                    message_id=message.id,
                    delivery_method=EmailDeliveryMethod.API,
                    cost=0.0,
                    status="no_api_configured",
                    error_message="No email API endpoint configured"
                )
            
            # Prepare API payload
            payload = {
                "message_id": message.id,
                "to": message.to_email,
                "from": message.from_email,
                "subject": message.subject,
                "body": message.body,
                "html_body": message.html_body,
                "attachments": message.attachments,
                "priority": message.priority,
                "timestamp": message.timestamp.isoformat()
            }
            
            # Call custom API
            import aiohttp
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_endpoint,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return EmailDeliveryResult(
                            success=True,
                            message_id=message.id,
                            delivery_method=EmailDeliveryMethod.API,
                            cost=result.get("cost", 0.0),
                            status="delivered",
                            delivery_timestamp=datetime.utcnow(),
                            server_response=json.dumps(result)
                        )
                    else:
                        return EmailDeliveryResult(
                            success=False,
                            message_id=message.id,
                            delivery_method=EmailDeliveryMethod.API,
                            cost=0.0,
                            status="api_error",
                            error_message f"API returned {response.status}"
                        )
            
        except Exception as e:
            logger.error(f"API email delivery failed: {e}")
            return EmailDeliveryResult(
                success=False,
                message_id=message.id,
                delivery_method=EmailDeliveryMethod.API,
                cost=0.0,
                status="failed",
                error_message=str(e)
            )
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get API delivery status"""
        return {
            "message_id": message_id,
            "status": "delivered",
            "method": "api",
            "timestamp": datetime.utcnow().isoformat()
        }


class LLMEmailAnalyzer:
    """LLM-based email analysis and routing system"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key:
            self.llm_client = AsyncOpenAI(api_key=self.openai_api_key)
        else:
            self.llm_client = None
            logger.warning("No OpenAI API key, LLM features limited")
        
        self.email_analysis_prompt = self._build_email_analysis_prompt()
    
    def _build_email_analysis_prompt(self) -> str:
        """Build proprietary prompt for email understanding"""
        return """You are an intelligent email analysis system for Overmanifold Protocol. Analyze emails and determine optimal processing strategy.

EMAIL TYPES:
1. TRANSACTION_EMAIL - Payment notifications, confirmations, receipts
2. VERIFICATION_EMAIL - Account verification, security codes
3. NOTIFICATION_EMAIL - System alerts, updates, promotional
4. SUPPORT_EMAIL - Customer support, help requests
5. MARKETING_EMAIL - Promotional content, newsletters

ANALYSIS FACTORS:
- Email content and keywords
- Subject line analysis
- Urgency indicators
- Recipient segmentation
- Compliance requirements
- Delivery speed requirements
- Personalization needs

ANALYSIS FORMAT:
Return JSON with this exact structure:
{
  "email_type": "transaction|verification|notification|support|marketing",
  "confidence": 0.0-1.0,
  "urgency": "normal|high|urgent",
  "priority": "low|medium|high",
  "personalization_required": true|false,
  "compliance_flags": [],
  "recommended_delivery_method": "smtp|api|queue|webhook|in_app",
  "reasoning": "explain analysis decision",
  "estimated_cost": 0.0
}

Consider urgency, personalization needs, compliance requirements, and recipient preferences when making recommendations."""

    async def analyze_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = ""
    ) -> Dict[str, Any]:
        """Analyze email content and determine optimal processing"""
        
        if not self.llm_client:
            # Fallback to keyword-based analysis
            return self._fallback_email_analysis(subject, body)
        
        try:
            analysis_prompt = f"{self.email_analysis_prompt}\n\nTo: {to_email}\nSubject: {subject}\nBody: {body}"
            if html_body:
                analysis_prompt += f"\nHTML Body: {html_body[:500]}..."  # Truncate HTML
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.email_analysis_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis_result = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM email analysis: {analysis_result['email_type']} "
                        f"(confidence: {analysis_result['confidence']})")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"LLM email analysis failed: {e}, using fallback")
            return self._fallback_email_analysis(subject, body)
    
    def _fallback_email_analysis(self, subject: str, body: str) -> Dict[str, Any]:
        """Fallback keyword-based email analysis"""
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        # Keyword-based classification
        if any(word in subject_lower for word in ['verification', 'code', 'verify', 'confirm']):
            return {
                "email_type": "verification",
                "confidence": 0.8,
                "urgency": "normal",
                "priority": "high",
                "personalization_required": True,
                "compliance_flags": [],
                "recommended_delivery_method": "smtp",
                "reasoning": "Verification keywords detected",
                "estimated_cost": 0.0
            }
        elif any(word in subject_lower for word in ['payment', 'transaction', 'receipt', 'sent']):
            return {
                "email_type": "transaction",
                "confidence": 0.75,
                "urgency": "normal",
                "priority": "medium",
                "personalization_required": True,
                "compliance_flags": [],
                "recommended_delivery_method": "smtp",
                "reasoning": "Transaction keywords detected",
                "estimated_cost": 0.0
            }
        else:
            return {
                "email_type": "notification",
                "confidence": 0.6,
                "urgency": "normal",
                "priority": "low",
                "personalization_required": False,
                "compliance_flags": [],
                "recommended_delivery_method": "smtp",
                "reasoning": "Default classification",
                "estimated_cost": 0.0
            }


class LLMCustomEmailSystem:
    """Proprietary LLM-based email system with custom delivery methods"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        # Initialize LLM analyzer
        self.llm_analyzer = LLMEmailAnalyzer(self.openai_api_key)
        
        # Initialize delivery methods
        self.delivery_methods: Dict[EmailDeliveryMethod, CustomEmailDeliveryInterface] = {}
        self._initialize_delivery_methods()
        
        # Email queue for processing
        self.email_queue: List[CustomEmailMessage] = []
        self.delivery_history: Dict[str, EmailDeliveryResult] = {}
        
        # Email templates (LLM-generated)
        self.templates: Dict[str, str] = {}
    
    def _initialize_delivery_methods(self):
        """Initialize all custom delivery methods"""
        self.delivery_methods[EmailDeliveryMethod.SMTP] = SMTPEmailDelivery()
        self.delivery_methods[EmailDeliveryMethod.API] = APIEmailDelivery()
    
    async def send_custom_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = "",
        from_email: str = None,
        attachments: List[str] = None,
        preferred_method: EmailDeliveryMethod = None
    ) -> EmailDeliveryResult:
        """Send email using custom email system"""
        
        # Set default from email
        if not from_email:
            from_email = os.getenv("DEFAULT_FROM_EMAIL", "noreply@overmanifold.io")
        
        # Analyze email for optimal routing
        analysis = await self.llm_analyzer.analyze_email(to_email, subject, body, html_body)
        
        # Create custom email message
        email_message = CustomEmailMessage(
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            body=body,
            html_body=html_body,
            attachments=attachments or [],
            priority=analysis.get("priority", "normal"),
            delivery_method=preferred_method or EmailDeliveryMethod(analysis.get("recommended_delivery_method", "smtp"))
        )
        
        # Get delivery interface
        delivery_interface = self.delivery_methods.get(email_message.delivery_method)
        
        if not delivery_interface:
            # Fallback to SMTP
            delivery_interface = self.delivery_methods[EmailDeliveryMethod.SMTP]
            email_message.delivery_method = EmailDeliveryMethod.SMTP
        
        # Send email
        result = await delivery_interface.send_email(email_message)
        
        # Store in delivery history
        self.delivery_history[email_message.id] = result
        
        # Add to processing queue
        self.email_queue.append(email_message)
        
        logger.info(f"Custom email sent via {email_message.delivery_method.value}: {result.success}")
        
        return result
    
    async def send_verification_email(self, email: str, code: str = None) -> str:
        """Send verification email using custom system"""
        if not code:
            code = self._generate_secure_code(email)
        
        subject = "Overmanifold Verification Code"
        body = f"""
Your verification code is: {code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

---
Overmanifold Protocol
"""
        
        html_body = f"""
<html>
<body>
    <h2>Verification Code</h2>
    <p>Your verification code is: <strong>{code}</strong></p>
    <p>This code will expire in 10 minutes.</p>
    <p>If you did not request this code, please ignore this email.</p>
    <hr>
    <p><small>Overmanifold Protocol</small></p>
</body>
</html>
"""
        
        result = await self.send_custom_email(email, subject, body, html_body)
        
        if result.success:
            logger.info(f"Verification email sent to {email} via {result.delivery_method.value}")
        else:
            logger.error(f"Verification email failed: {result.error_message}")
        
        return code
    
    def _generate_secure_code(self, email: str) -> str:
        """Generate secure verification code"""
        import secrets
        import hashlib
        
        random_bytes = secrets.token_bytes(4)
        hash_input = f"{email}{random_bytes.hex()}{datetime.utcnow().isoformat()}"
        hash_result = hashlib.sha256(hash_input.encode()).hexdigest()
        
        code = ''.join(filter(str.isdigit, hash_result))[:6]
        while len(code) < 6:
            code += str(secrets.randbelow(10))
        
        return code
    
    async def send_payment_notification(
        self,
        email: str,
        amount: float,
        sender: str,
        transaction_id: str
    ) -> EmailDeliveryResult:
        """Send payment notification email"""
        subject = f"Payment of {amount} USDC Received"
        body = f"""
You have received a payment of {amount} USDC from {sender}.

Transaction ID: {transaction_id}
Amount: {amount} USDC
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Thank you for using Overmanifold Protocol.

---
Overmanifold Protocol
"""
        
        html_body = f"""
<html>
<body>
    <h2>Payment Received</h2>
    <p>You have received a payment of <strong>{amount} USDC</strong> from {sender}.</p>
    
    <table border="1" cellpadding="10">
        <tr>
            <td><strong>Amount:</strong></td>
            <td>{amount} USDC</td>
        </tr>
        <tr>
            <td><strong>From:</strong></td>
            <td>{sender}</td>
        </tr>
        <tr>
            <td><strong>Transaction ID:</strong></td>
            <td>{transaction_id}</td>
        </tr>
        <tr>
            <td><strong>Timestamp:</strong></td>
            <td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
    </table>
    
    <p>Thank you for using Overmanifold Protocol.</p>
    <hr>
    <p><small>Overmanifold Protocol</small></p>
</body>
</html>
"""
        
        return await self.send_custom_email(email, subject, body, html_body)
    
    async def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status for an email"""
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
    
    async def get_email_statistics(self) -> Dict[str, Any]:
        """Get email delivery statistics"""
        total_emails = len(self.delivery_history)
        successful = sum(1 for r in self.delivery_history.values() if r.success)
        failed = total_emails - successful
        
        method_counts = {}
        for result in self.delivery_history.values():
            method = result.delivery_method.value
            method_counts[method] = method_counts.get(method, 0) + 1
        
        total_cost = sum(r.cost for r in self.delivery_history.values())
        
        return {
            "total_emails": total_emails,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_emails if total_emails > 0 else 0.0,
            "method_distribution": method_counts,
            "total_cost": total_cost,
            "average_cost_per_email": total_cost / total_emails if total_emails > 0 else 0.0
        }


# Global custom email system instance
llm_custom_email_system = LLMCustomEmailSystem()