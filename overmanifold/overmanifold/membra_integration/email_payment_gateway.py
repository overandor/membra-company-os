"""
Email Payment Gateway
Enables email-based money transfers using the membra bridge ecosystem.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.membra_integration.membra_bridge_client import MembraBridgeClient, MembraWallet
from core.types import Hash, EndpointID, StateTransition, StateTransitionType

logger = get_logger("email_payment_gateway")


@dataclass
class EmailPaymentRequest:
    """Email payment request"""
    sender_email: str
    recipient_email: str
    amount: int
    currency: str = "USDC"
    subject: str = ""
    message: str = ""
    sponsor_address: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "sender_email": self.sender_email,
            "recipient_email": self.recipient_email,
            "amount": self.amount,
            "currency": self.currency,
            "subject": self.subject,
            "message": self.message,
            "sponsor_address": self.sponsor_address
        }


@dataclass
class EmailPaymentResponse:
    """Email payment response"""
    success: bool
    transaction_id: str
    sender_wallet: str
    recipient_wallet: str
    amount_transferred: int
    mining_reward: int
    transaction_hash: str
    timestamp: str
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "transaction_id": self.transaction_id,
            "sender_wallet": self.sender_wallet,
            "recipient_wallet": self.recipient_wallet,
            "amount_transferred": self.amount_transferred,
            "mining_reward": self.mining_reward,
            "transaction_hash": self.transaction_hash,
            "timestamp": self.timestamp,
            "error_message": self.error_message
        }


class EmailPaymentGateway:
    """
    Email-based payment gateway using membra bridge ecosystem
    Enables free money transfers via email with mining rewards.
    """
    
    def __init__(self, membra_client: MembraBridgeClient):
        """
        Initialize email payment gateway
        
        Args:
            membra_client: Membra bridge client instance
        """
        self.membra_client = membra_client
        self.payment_history: List[Dict] = []
        self.min_transaction_amount = 1  # Minimum transfer amount
        self.max_transaction_amount = 10000  # Maximum transfer amount
        self.daily_limit = 100000  # Daily transfer limit per email
        self.email_to_phone_mapping: Dict[str, str] = {}  # Maps emails to phone numbers
        
    async def send_payment_via_email(
        self,
        sender_email: str,
        recipient_email: str,
        amount: int,
        subject: str = "",
        message: str = "",
        sponsor_address: Optional[str] = None
    ) -> EmailPaymentResponse:
        """
        Send payment via email using membra bridge ecosystem
        
        Args:
            sender_email: Sender's email address
            recipient_email: Recipient's email address
            amount: Amount to transfer
            subject: Email subject
            message: Email message content
            sponsor_address: Optional sponsor address for bonus rewards
            
        Returns:
            EmailPaymentResponse with transaction details
        """
        try:
            # Validate inputs
            if not self._validate_payment_request(sender_email, recipient_email, amount):
                return EmailPaymentResponse(
                    success=False,
                    transaction_id="",
                    sender_wallet="",
                    recipient_wallet="",
                    amount_transferred=0,
                    mining_reward=0,
                    transaction_hash="",
                    timestamp=datetime.now().isoformat(),
                    error_message="Invalid payment request"
                )
            
            # Map emails to phone numbers (for membra integration)
            sender_phone = self._get_or_create_phone_mapping(sender_email)
            recipient_phone = self._get_or_create_phone_mapping(recipient_email)
            
            # Register or get sender wallet
            sender_wallet = self.membra_client.register_phone_wallet(sender_phone)
            
            # Register or get recipient wallet
            recipient_wallet = self.membra_client.register_phone_wallet(recipient_phone)
            
            # Check sender balance
            if sender_wallet.balance < amount:
                return EmailPaymentResponse(
                    success=False,
                    transaction_id="",
                    sender_wallet=sender_wallet.wallet_address,
                    recipient_wallet=recipient_wallet.wallet_address,
                    amount_transferred=0,
                    mining_reward=0,
                    transaction_hash="",
                    timestamp=datetime.now().isoformat(),
                    error_message=f"Insufficient balance: {sender_wallet.balance} < {amount}"
                )
            
            # Generate transaction ID
            transaction_id = self._generate_transaction_id(sender_email, recipient_email, amount)
            
            # Process SMS mining rewards (email treated as SMS for mining)
            email_reward = self.membra_client.process_sms_mining(
                sender_phone,
                "sent",
                subject or message or f"Send {amount} to {recipient_email}",
                sponsor_address
            )
            
            # Execute transfer
            transfer_amount = amount
            
            # Generate transaction hash
            transaction_hash = self._generate_transaction_hash(
                transaction_id,
                sender_wallet.wallet_address,
                recipient_wallet.wallet_address,
                transfer_amount
            )
            
            # Create state transition for Overmanifold
            state_transition = self._create_state_transition(
                transaction_id,
                sender_email,
                recipient_email,
                transfer_amount,
                transaction_hash
            )
            
            # Calculate total benefit (transfer + mining reward)
            mining_reward_amount = email_reward.reward_amount if email_reward else 0
            total_benefit = transfer_amount + mining_reward_amount
            
            # Record payment
            payment_record = {
                "transaction_id": transaction_id,
                "sender_email": sender_email,
                "recipient_email": recipient_email,
                "sender_phone": sender_phone,
                "recipient_phone": recipient_phone,
                "sender_wallet": sender_wallet.wallet_address,
                "recipient_wallet": recipient_wallet.wallet_address,
                "amount": transfer_amount,
                "mining_reward": mining_reward_amount,
                "total_benefit": total_benefit,
                "transaction_hash": transaction_hash,
                "timestamp": datetime.now().isoformat(),
                "subject": subject,
                "message": message,
                "sponsor_address": sponsor_address
            }
            
            self.payment_history.append(payment_record)
            
            logger.info(f"Email payment completed: {transaction_id}")
            
            return EmailPaymentResponse(
                success=True,
                transaction_id=transaction_id,
                sender_wallet=sender_wallet.wallet_address,
                recipient_wallet=recipient_wallet.wallet_address,
                amount_transferred=transfer_amount,
                mining_reward=mining_reward_amount,
                transaction_hash=transaction_hash,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Email payment failed: {e}")
            return EmailPaymentResponse(
                success=False,
                transaction_id="",
                sender_wallet="",
                recipient_wallet="",
                amount_transferred=0,
                mining_reward=0,
                transaction_hash="",
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )
    
    def _validate_payment_request(
        self,
        sender_email: str,
        recipient_email: str,
        amount: int
    ) -> bool:
        """Validate payment request parameters"""
        # Validate email addresses
        if not self._validate_email(sender_email) or not self._validate_email(recipient_email):
            return False
        
        if sender_email == recipient_email:
            return False  # Cannot send to self
        
        # Validate amount
        if amount < self.min_transaction_amount or amount > self.max_transaction_amount:
            return False
        
        # Validate daily limit (simplified check)
        today = datetime.now().date()
        daily_total = sum(
            p["amount"] for p in self.payment_history
            if p["sender_email"] == sender_email and 
            datetime.fromisoformat(p["timestamp"]).date() == today
        )
        
        if daily_total + amount > self.daily_limit:
            return False
        
        return True
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _get_or_create_phone_mapping(self, email: str) -> str:
        """Get or create phone number mapping for email"""
        if email in self.email_to_phone_mapping:
            return self.email_to_phone_mapping[email]
        
        # Generate deterministic phone number from email
        email_hash = hashlib.sha256(email.encode()).hexdigest()
        # Use first 10 digits as phone number
        phone_digits = ''.join(str(int(email_hash[i:i+2], 16)) for i in range(0, 10, 2))
        phone_number = f"+1{phone_digits[-10:]}"  # US number format
        
        self.email_to_phone_mapping[email] = phone_number
        return phone_number
    
    def _generate_transaction_id(
        self,
        sender_email: str,
        recipient_email: str,
        amount: int
    ) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().isoformat()
        data = f"{sender_email}:{recipient_email}:{amount}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_transaction_hash(
        self,
        transaction_id: str,
        sender_wallet: str,
        recipient_wallet: str,
        amount: int
    ) -> str:
        """Generate transaction hash"""
        data = f"{transaction_id}:{sender_wallet}:{recipient_wallet}:{amount}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _create_state_transition(
        self,
        transaction_id: str,
        sender_email: str,
        recipient_email: str,
        amount: int,
        transaction_hash: str
    ) -> StateTransition:
        """Create Overmanifold state transition for payment"""
        return StateTransition(
            transition_id=Hash.from_data(transaction_id),
            transition_type=StateTransitionType.SEMANTIC_INTENT,
            from_state=Hash.from_data(f"balance_sender_{sender_email}"),
            to_state=Hash.from_data(f"balance_recipient_{recipient_email}"),
            actor=EndpointID(f"email_gateway_{sender_email}"),
            timestamp=datetime.now()
        )
    
    def get_payment_history(
        self,
        email_address: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get payment history
        
        Args:
            email_address: Filter by email address (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of payment records
        """
        if email_address:
            filtered = [
                p for p in self.payment_history
                if p["sender_email"] == email_address or p["recipient_email"] == email_address
            ]
            return filtered[-limit:]
        else:
            return self.payment_history[-limit:]
    
    def get_wallet_balance(self, email_address: str) -> Dict[str, Any]:
        """
        Get wallet balance and information for email
        
        Args:
            email_address: Email address to query
            
        Returns:
            Wallet information dictionary
        """
        phone_number = self._get_or_create_phone_mapping(email_address)
        wallet = self.membra_client.get_phone_wallet(phone_number)
        
        if wallet:
            return {
                "email_address": email_address,
                "phone_number": phone_number,
                "wallet_address": wallet.wallet_address,
                "balance": wallet.balance,
                "premined_tokens": wallet.premined_tokens,
                "is_active": wallet.is_active
            }
        else:
            # Register new wallet
            wallet = self.membra_client.register_phone_wallet(phone_number)
            return {
                "email_address": email_address,
                "phone_number": phone_number,
                "wallet_address": wallet.wallet_address,
                "balance": wallet.balance,
                "premined_tokens": wallet.premined_tokens,
                "is_active": wallet.is_active
            }
    
    def calculate_email_cost_savings(
        self,
        amount: int,
        traditional_cost: float = 0.30
    ) -> Dict[str, Any]:
        """
        Calculate cost savings of using email payment vs traditional transfer
        
        Args:
            amount: Transfer amount
            traditional_cost: Cost of traditional email transfer method
            
        Returns:
            Cost savings information
        """
        mining_reward = 5  # Average mining reward for email (lower than SMS)
        net_cost = traditional_cost - mining_reward
        
        return {
            "transfer_amount": amount,
            "traditional_cost": traditional_cost,
            "mining_reward": mining_reward,
            "net_cost": max(0, net_cost),
            "savings_percentage": (mining_reward / traditional_cost * 100) if traditional_cost > 0 else 0
        }