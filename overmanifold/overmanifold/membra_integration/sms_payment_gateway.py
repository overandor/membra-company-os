"""
SMS Payment Gateway
Enables SMS-based money transfers using the membra bridge ecosystem.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.membra_integration.membra_bridge_client import MembraBridgeClient, MembraWallet, SMSMiningReward
from core.types import Hash, EndpointID, StateTransition, StateTransitionType

logger = get_logger("sms_payment_gateway")


@dataclass
class SMSPaymentRequest:
    """SMS payment request"""
    sender_phone: str
    recipient_phone: str
    amount: int
    currency: str = "USDC"
    message: str = ""
    sponsor_address: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "sender_phone": self.sender_phone,
            "recipient_phone": self.recipient_phone,
            "amount": self.amount,
            "currency": self.currency,
            "message": self.message,
            "sponsor_address": self.sponsor_address
        }


@dataclass
class SMSPaymentResponse:
    """SMS payment response"""
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


class SMSPaymentGateway:
    """
    SMS-based payment gateway using membra bridge ecosystem
    Enables free money transfers via SMS with mining rewards.
    """
    
    def __init__(self, membra_client: MembraBridgeClient):
        """
        Initialize SMS payment gateway
        
        Args:
            membra_client: Membra bridge client instance
        """
        self.membra_client = membra_client
        self.payment_history: List[Dict] = []
        self.min_transaction_amount = 1  # Minimum transfer amount
        self.max_transaction_amount = 10000  # Maximum transfer amount
        self.daily_limit = 100000  # Daily transfer limit per phone
        
    async def send_payment_via_sms(
        self,
        sender_phone: str,
        recipient_phone: str,
        amount: int,
        message: str = "",
        sponsor_address: Optional[str] = None
    ) -> SMSPaymentResponse:
        """
        Send payment via SMS using membra bridge ecosystem
        
        Args:
            sender_phone: Sender's phone number
            recipient_phone: Recipient's phone number
            amount: Amount to transfer
            message: Optional message to include
            sponsor_address: Optional sponsor address for bonus rewards
            
        Returns:
            SMSPaymentResponse with transaction details
        """
        try:
            # Validate inputs
            if not self._validate_payment_request(sender_phone, recipient_phone, amount):
                return SMSPaymentResponse(
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
            
            # Register or get sender wallet
            sender_wallet = self.membra_client.register_phone_wallet(sender_phone)
            
            # Register or get recipient wallet
            recipient_wallet = self.membra_client.register_phone_wallet(recipient_phone)
            
            # Check sender balance
            if sender_wallet.balance < amount:
                return SMSPaymentResponse(
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
            transaction_id = self._generate_transaction_id(sender_phone, recipient_phone, amount)
            
            # Process SMS mining rewards (sender gets rewarded for sending)
            sms_reward = self.membra_client.process_sms_mining(
                sender_phone,
                "sent",
                message or f"Send {amount} to {recipient_phone}",
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
                sender_phone,
                recipient_phone,
                transfer_amount,
                transaction_hash
            )
            
            # Calculate total benefit (transfer + mining reward)
            mining_reward_amount = sms_reward.reward_amount if sms_reward else 0
            total_benefit = transfer_amount + mining_reward_amount
            
            # Record payment
            payment_record = {
                "transaction_id": transaction_id,
                "sender_phone": sender_phone,
                "recipient_phone": recipient_phone,
                "sender_wallet": sender_wallet.wallet_address,
                "recipient_wallet": recipient_wallet.wallet_address,
                "amount": transfer_amount,
                "mining_reward": mining_reward_amount,
                "total_benefit": total_benefit,
                "transaction_hash": transaction_hash,
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "sponsor_address": sponsor_address
            }
            
            self.payment_history.append(payment_record)
            
            logger.info(f"SMS payment completed: {transaction_id}")
            
            return SMSPaymentResponse(
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
            logger.error(f"SMS payment failed: {e}")
            return SMSPaymentResponse(
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
        sender_phone: str,
        recipient_phone: str,
        amount: int
    ) -> bool:
        """Validate payment request parameters"""
        # Validate phone numbers
        if not sender_phone or not recipient_phone:
            return False
        
        if sender_phone == recipient_phone:
            return False  # Cannot send to self
        
        # Validate amount
        if amount < self.min_transaction_amount or amount > self.max_transaction_amount:
            return False
        
        # Validate daily limit (simplified check)
        today = datetime.now().date()
        daily_total = sum(
            p["amount"] for p in self.payment_history
            if p["sender_phone"] == sender_phone and 
            datetime.fromisoformat(p["timestamp"]).date() == today
        )
        
        if daily_total + amount > self.daily_limit:
            return False
        
        return True
    
    def _generate_transaction_id(
        self,
        sender_phone: str,
        recipient_phone: str,
        amount: int
    ) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().isoformat()
        data = f"{sender_phone}:{recipient_phone}:{amount}:{timestamp}"
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
        sender_phone: str,
        recipient_phone: str,
        amount: int,
        transaction_hash: str
    ) -> StateTransition:
        """Create Overmanifold state transition for payment"""
        return StateTransition(
            transition_id=Hash.from_data(transaction_id),
            transition_type=StateTransitionType.SEMANTIC_INTENT,
            from_state=Hash.from_data(f"balance_sender_{sender_phone}"),
            to_state=Hash.from_data(f"balance_recipient_{recipient_phone}"),
            actor=EndpointID(f"sms_gateway_{sender_phone}"),
            timestamp=datetime.now()
        )
    
    def get_payment_history(
        self,
        phone_number: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get payment history
        
        Args:
            phone_number: Filter by phone number (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of payment records
        """
        if phone_number:
            filtered = [
                p for p in self.payment_history
                if p["sender_phone"] == phone_number or p["recipient_phone"] == phone_number
            ]
            return filtered[-limit:]
        else:
            return self.payment_history[-limit:]
    
    def get_wallet_balance(self, phone_number: str) -> Dict[str, Any]:
        """
        Get wallet balance and information
        
        Args:
            phone_number: Phone number to query
            
        Returns:
            Wallet information dictionary
        """
        wallet = self.membra_client.get_phone_wallet(phone_number)
        
        if wallet:
            return {
                "phone_number": wallet.phone_number,
                "wallet_address": wallet.wallet_address,
                "balance": wallet.balance,
                "premined_tokens": wallet.premined_tokens,
                "is_active": wallet.is_active
            }
        else:
            # Register new wallet
            wallet = self.membra_client.register_phone_wallet(phone_number)
            return {
                "phone_number": wallet.phone_number,
                "wallet_address": wallet.wallet_address,
                "balance": wallet.balance,
                "premined_tokens": wallet.premined_tokens,
                "is_active": wallet.is_active
            }
    
    def calculate_sms_cost_savings(
        self,
        amount: int,
        traditional_cost: float = 0.50
    ) -> Dict[str, Any]:
        """
        Calculate cost savings of using SMS payment vs traditional transfer
        
        Args:
            amount: Transfer amount
            traditional_cost: Cost of traditional transfer method
            
        Returns:
            Cost savings information
        """
        mining_reward = 10  # Average mining reward for sending SMS
        net_cost = traditional_cost - mining_reward
        
        return {
            "transfer_amount": amount,
            "traditional_cost": traditional_cost,
            "mining_reward": mining_reward,
            "net_cost": max(0, net_cost),
            "savings_percentage": (mining_reward / traditional_cost * 100) if traditional_cost > 0 else 0
        }