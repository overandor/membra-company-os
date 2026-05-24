"""
Unified Free Payment API
Integrates SMS and email payment gateways with free transaction sponsorship.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.membra_integration.sms_payment_gateway import SMSPaymentGateway, SMSPaymentRequest, SMSPaymentResponse
from overmanifold.membra_integration.email_payment_gateway import EmailPaymentGateway, EmailPaymentRequest, EmailPaymentResponse
from overmanifold.membra_integration.free_transaction_sponsor import FreeTransactionSponsor, SponsoredTransaction
from overmanifold.membra_integration.membra_bridge_client import MembraBridgeClient

logger = get_logger("unified_free_payment_api")


class PaymentMethod(Enum):
    """Payment method types"""
    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"


@dataclass
class FreePaymentRequest:
    """Unified free payment request"""
    payment_method: PaymentMethod
    sender_identifier: str  # phone number or email
    recipient_identifier: str  # phone number or email
    amount: int
    currency: str = "USDC"
    message: str = ""
    subject: str = ""  # For email
    sponsor_id: Optional[str] = None  # Preferred sponsor
    
    def to_dict(self) -> Dict:
        return {
            "payment_method": self.payment_method.value,
            "sender_identifier": self.sender_identifier,
            "recipient_identifier": self.recipient_identifier,
            "amount": self.amount,
            "currency": self.currency,
            "message": self.message,
            "subject": self.subject,
            "sponsor_id": self.sponsor_id
        }


@dataclass
class FreePaymentResponse:
    """Unified free payment response"""
    success: bool
    transaction_id: str
    payment_method: str
    sender_identifier: str
    recipient_identifier: str
    amount_transferred: int
    transaction_cost: int
    mining_reward: int
    sponsor_bonus: int
    net_cost_to_user: int
    transaction_hash: str
    timestamp: str
    sponsor_id: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "transaction_id": self.transaction_id,
            "payment_method": self.payment_method,
            "sender_identifier": self.sender_identifier,
            "recipient_identifier": self.recipient_identifier,
            "amount_transferred": self.amount_transferred,
            "transaction_cost": self.transaction_cost,
            "mining_reward": self.mining_reward,
            "sponsor_bonus": self.sponsor_bonus,
            "net_cost_to_user": self.net_cost_to_user,
            "transaction_hash": self.transaction_hash,
            "timestamp": self.timestamp,
            "sponsor_id": self.sponsor_id,
            "error_message": self.error_message
        }


class UnifiedFreePaymentAPI:
    """
    Unified free payment API integrating SMS, email, and sponsorship
    Enables truly free money transfers via SMS or email.
    """
    
    def __init__(self, membra_api_url: str = "http://localhost:8000"):
        """
        Initialize unified free payment API
        
        Args:
            membra_api_url: Base URL for membra bridge API
        """
        self.membra_client = MembraBridgeClient(membra_api_url)
        self.sms_gateway = SMSPaymentGateway(self.membra_client)
        self.email_gateway = EmailPaymentGateway(self.membra_client)
        self.sponsor_system = FreeTransactionSponsor()
        
        # Payment configuration
        self.transaction_costs = {
            PaymentMethod.SMS: 0.50,  # Traditional SMS cost
            PaymentMethod.EMAIL: 0.30,  # Traditional email cost
            PaymentMethod.PHONE: 0.50  # Traditional phone cost
        }
        
        logger.info("Unified Free Payment API initialized")
    
    async def send_free_payment(
        self,
        payment_method: PaymentMethod,
        sender_identifier: str,
        recipient_identifier: str,
        amount: int,
        currency: str = "USDC",
        message: str = "",
        subject: str = "",
        sponsor_id: Optional[str] = None
    ) -> FreePaymentResponse:
        """
        Send free payment using specified method
        
        Args:
            payment_method: Payment method (SMS, EMAIL, PHONE)
            sender_identifier: Sender's phone number or email
            recipient_identifier: Recipient's phone number or email
            amount: Amount to transfer
            currency: Currency type (default USDC)
            message: Message content
            subject: Email subject (for email payments)
            sponsor_id: Preferred sponsor ID (optional)
            
        Returns:
            FreePaymentResponse with transaction details
        """
        try:
            # Get transaction cost
            transaction_cost = int(self.transaction_costs.get(payment_method, 0.50) * 100)  # Convert to smallest unit
            
            # Sponsor the transaction
            sponsored_tx = self.sponsor_system.sponsor_transaction(
                user_identifier=sender_identifier,
                amount=amount,
                transaction_cost=transaction_cost,
                preferred_sponsor_id=sponsor_id
            )
            
            if not sponsored_tx:
                return FreePaymentResponse(
                    success=False,
                    transaction_id="",
                    payment_method=payment_method.value,
                    sender_identifier=sender_identifier,
                    recipient_identifier=recipient_identifier,
                    amount_transferred=0,
                    transaction_cost=transaction_cost,
                    mining_reward=0,
                    sponsor_bonus=0,
                    net_cost_to_user=transaction_cost,
                    transaction_hash="",
                    timestamp=datetime.now().isoformat(),
                    error_message="No available sponsor for transaction"
                )
            
            # Route to appropriate gateway
            if payment_method == PaymentMethod.SMS:
                sms_response = await self.sms_gateway.send_payment_via_sms(
                    sender_phone=sender_identifier,
                    recipient_phone=recipient_identifier,
                    amount=amount,
                    message=message,
                    sponsor_address=sponsored_tx.sponsor_id
                )
                
                if not sms_response.success:
                    return FreePaymentResponse(
                        success=False,
                        transaction_id="",
                        payment_method=payment_method.value,
                        sender_identifier=sender_identifier,
                        recipient_identifier=recipient_identifier,
                        amount_transferred=0,
                        transaction_cost=transaction_cost,
                        mining_reward=0,
                        sponsor_bonus=0,
                        net_cost_to_user=transaction_cost,
                        transaction_hash="",
                        timestamp=datetime.now().isoformat(),
                        error_message=sms_response.error_message
                    )
                
                mining_reward = sms_response.mining_reward
                transaction_id = sms_response.transaction_id
                transaction_hash = sms_response.transaction_hash
                
            elif payment_method == PaymentMethod.EMAIL:
                email_response = await self.email_gateway.send_payment_via_email(
                    sender_email=sender_identifier,
                    recipient_email=recipient_identifier,
                    amount=amount,
                    subject=subject,
                    message=message,
                    sponsor_address=sponsored_tx.sponsor_id
                )
                
                if not email_response.success:
                    return FreePaymentResponse(
                        success=False,
                        transaction_id="",
                        payment_method=payment_method.value,
                        sender_identifier=sender_identifier,
                        recipient_identifier=recipient_identifier,
                        amount_transferred=0,
                        transaction_cost=transaction_cost,
                        mining_reward=0,
                        sponsor_bonus=0,
                        net_cost_to_user=transaction_cost,
                        transaction_hash="",
                        timestamp=datetime.now().isoformat(),
                        error_message=email_response.error_message
                    )
                
                mining_reward = email_response.mining_reward
                transaction_id = email_response.transaction_id
                transaction_hash = email_response.transaction_hash
                
            else:
                return FreePaymentResponse(
                    success=False,
                    transaction_id="",
                    payment_method=payment_method.value,
                    sender_identifier=sender_identifier,
                    recipient_identifier=recipient_identifier,
                    amount_transferred=0,
                    transaction_cost=transaction_cost,
                    mining_reward=0,
                    sponsor_bonus=0,
                    net_cost_to_user=transaction_cost,
                    transaction_hash="",
                    timestamp=datetime.now().isoformat(),
                    error_message=f"Unsupported payment method: {payment_method}"
                )
            
            # Calculate net cost to user
            net_cost = max(0, transaction_cost - mining_reward - sponsored_tx.mining_bonus)
            
            logger.info(f"Free payment completed: {transaction_id} via {payment_method.value}")
            
            return FreePaymentResponse(
                success=True,
                transaction_id=transaction_id,
                payment_method=payment_method.value,
                sender_identifier=sender_identifier,
                recipient_identifier=recipient_identifier,
                amount_transferred=amount,
                transaction_cost=transaction_cost,
                mining_reward=mining_reward,
                sponsor_bonus=sponsored_tx.mining_bonus,
                net_cost_to_user=net_cost,
                transaction_hash=transaction_hash,
                timestamp=datetime.now().isoformat(),
                sponsor_id=sponsored_tx.sponsor_id
            )
            
        except Exception as e:
            logger.error(f"Free payment failed: {e}")
            return FreePaymentResponse(
                success=False,
                transaction_id="",
                payment_method=payment_method.value,
                sender_identifier=sender_identifier,
                recipient_identifier=recipient_identifier,
                amount_transferred=0,
                transaction_cost=0,
                mining_reward=0,
                sponsor_bonus=0,
                net_cost_to_user=0,
                transaction_hash="",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )
    
    async def send_free_sms_payment(
        self,
        sender_phone: str,
        recipient_phone: str,
        amount: int,
        message: str = "",
        sponsor_id: Optional[str] = None
    ) -> FreePaymentResponse:
        """
        Send free payment via SMS
        
        Args:
            sender_phone: Sender's phone number
            recipient_phone: Recipient's phone number
            amount: Amount to transfer
            message: SMS message content
            sponsor_id: Preferred sponsor ID
            
        Returns:
            FreePaymentResponse with transaction details
        """
        return await self.send_free_payment(
            payment_method=PaymentMethod.SMS,
            sender_identifier=sender_phone,
            recipient_identifier=recipient_phone,
            amount=amount,
            message=message,
            sponsor_id=sponsor_id
        )
    
    async def send_free_email_payment(
        self,
        sender_email: str,
        recipient_email: str,
        amount: int,
        subject: str = "",
        message: str = "",
        sponsor_id: Optional[str] = None
    ) -> FreePaymentResponse:
        """
        Send free payment via email
        
        Args:
            sender_email: Sender's email address
            recipient_email: Recipient's email address
            amount: Amount to transfer
            subject: Email subject
            message: Email message content
            sponsor_id: Preferred sponsor ID
            
        Returns:
            FreePaymentResponse with transaction details
        """
        return await self.send_free_payment(
            payment_method=PaymentMethod.EMAIL,
            sender_identifier=sender_email,
            recipient_identifier=recipient_email,
            amount=amount,
            subject=subject,
            message=message,
            sponsor_id=sponsor_id
        )
    
    def get_user_balance(self, identifier: str) -> Dict[str, Any]:
        """
        Get user balance and wallet information
        
        Args:
            identifier: Phone number or email address
            
        Returns:
            User balance and wallet information
        """
        # Determine if identifier is phone or email
        if "@" in identifier:
            return self.email_gateway.get_wallet_balance(identifier)
        else:
            return self.sms_gateway.get_wallet_balance(identifier)
    
    def get_payment_statistics(self) -> Dict[str, Any]:
        """
        Get overall payment system statistics
        
        Returns:
            Payment system statistics
        """
        sponsor_stats = self.sponsor_system.get_sponsor_statistics()
        
        # Combine with gateway statistics
        sms_history = self.sms_gateway.get_payment_history()
        email_history = self.email_gateway.get_payment_history()
        
        return {
            "sponsor_statistics": sponsor_stats,
            "sms_payments": len(sms_history),
            "email_payments": len(email_history),
            "total_payments": len(sms_history) + len(email_history),
            "total_amount_transferred": sum(p["amount"] for p in sms_history + email_history)
        }
    
    def register_sponsor(
        self,
        sponsor_address: str,
        sponsor_name: str,
        sponsor_type: str = "individual",
        sponsor_level: str = "bronze",
        custom_budget: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Register a new sponsor
        
        Args:
            sponsor_address: Sponsor's wallet address
            sponsor_name: Sponsor's name
            sponsor_type: Type of sponsor
            sponsor_level: Sponsor level
            custom_budget: Custom daily budget
            
        Returns:
            Sponsor information
        """
        sponsor = self.sponsor_system.register_sponsor(
            sponsor_address=sponsor_address,
            sponsor_name=sponsor_name,
            sponsor_type=sponsor_type,
            sponsor_level=sponsor_level,
            custom_budget=custom_budget
        )
        
        return sponsor.to_dict()
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status
        
        Returns:
            System status information
        """
        membra_health = self.membra_client.health_check()
        
        return {
            "membra_bridge_status": membra_health,
            "sms_gateway_active": self.sms_gateway is not None,
            "email_gateway_active": self.email_gateway is not None,
            "sponsor_system_active": self.sponsor_system is not None,
            "available_sponsors": len(self.sponsor_system.get_all_sponsors()),
            "total_sponsor_budget": self.sponsor_system.get_sponsor_statistics()["total_remaining_budget"]
        }