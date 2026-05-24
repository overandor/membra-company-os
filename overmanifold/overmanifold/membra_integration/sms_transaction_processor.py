"""
SMS Transaction Processor
Handles the complete flow from SMS receipt to blockchain transaction.
"""

import asyncio
import logging
import re
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import secrets

from overmanifold.infrastructure.logging_config import get_logger
from overmanifold.membra_integration.membra_bridge_client import MembraBridgeClient, MembraWallet, SMSMiningReward
from overmanifold.membra_integration.sms_payment_gateway import SMSPaymentGateway, SMSPaymentRequest, SMSPaymentResponse
from overmanifold.membra_integration.free_transaction_sponsor import FreeTransactionSponsor

logger = get_logger("sms_transaction_processor")


class TransactionState(Enum):
    """States in the SMS transaction lifecycle"""
    RECEIVED = "sms_received"
    PARSED = "sms_parsed"
    VALIDATED = "validated"
    WALLET_RESOLVED = "wallet_resolved"
    SPONSORED = "transaction_sponsored"
    SUBMITTED = "submitted_to_network"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SMSMessage:
    """Incoming SMS message"""
    id: str
    sender_phone: str
    recipient_phone: str
    message_content: str
    timestamp: datetime
    sms_gateway_id: str = ""
    raw_data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = self.generate_message_id()
    
    def generate_message_id(self) -> str:
        """Generate unique message ID"""
        data = f"{self.sender_phone}{self.recipient_phone}{self.timestamp.isoformat()}{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass
class TransactionContext:
    """Context for SMS transaction processing"""
    sms_message: SMSMessage
    state: TransactionState = TransactionState.RECEIVED
    parsed_command: Optional[Dict] = None
    sender_wallet: Optional[MembraWallet] = None
    recipient_wallet: Optional[MembraWallet] = None
    amount: int = 0
    transaction_id: str = ""
    blockchain_tx_hash: str = ""
    sponsor_id: str = ""
    mining_reward: int = 0
    sponsor_bonus: int = 0
    error_message: str = ""
    processing_steps: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_processing_step(self, step: str, status: str, details: Dict = None):
        """Add a processing step to the context"""
        self.processing_steps.append({
            "step": step,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        })
        self.updated_at = datetime.utcnow()


class SMSTransactionProcessor:
    """Processes SMS messages through to blockchain transactions"""
    
    # Command patterns for SMS parsing
    COMMAND_PATTERNS = {
        'send': r'^(?:send|pay|transfer)\s+(\d+)\s+(?:to\s+)?(\+\d{10,15})(?:\s+(.+))?$',
        'request': r'^(?:request|ask)\s+(\d+)\s+from\s+(\+\d{10,15})(?:\s+(.+))?$',
        'balance': r'^(?:balance|bal)$',
        'help': r'^(?:help|\?)$',
    }
    
    def __init__(self):
        self.membra_client = MembraBridgeClient()
        self.sms_gateway = SMSPaymentGateway(self.membra_client)
        self.sponsor_system = FreeTransactionSponsor()
        self.active_transactions: Dict[str, TransactionContext] = {}
        self.transaction_history: List[TransactionContext] = []
    
    async def process_sms_message(self, sms_message: SMSMessage) -> TransactionContext:
        """Process an SMS message through the complete transaction flow"""
        context = TransactionContext(sms_message=sms_message)
        self.active_transactions[context.sms_message.id] = context
        
        try:
            # Step 1: Parse SMS command
            await self._parse_command(context)
            
            # Step 2: Validate transaction
            await self._validate_transaction(context)
            
            # Step 3: Resolve wallets
            await self._resolve_wallets(context)
            
            # Step 4: Sponsor transaction
            await self._sponsor_transaction(context)
            
            # Step 5: Submit to network
            await self._submit_to_network(context)
            
            # Step 6: Confirm transaction
            await self._confirm_transaction(context)
            
            # Step 7: Complete transaction
            await self._complete_transaction(context)
            
        except Exception as e:
            logger.error(f"Error processing SMS {sms_message.id}: {e}")
            context.state = TransactionState.FAILED
            context.error_message = str(e)
            context.add_processing_step("error", "failed", {"error": str(e)})
        
        finally:
            # Move to history
            self.transaction_history.append(context)
            if context.sms_message.id in self.active_transactions:
                del self.active_transactions[context.sms_message.id]
        
        return context
    
    async def _parse_command(self, context: TransactionContext):
        """Parse the SMS command"""
        context.add_processing_step("parse_command", "started")
        
        message = context.sms_message.message_content.strip().lower()
        
        for command_type, pattern in self.COMMAND_PATTERNS.items():
            match = re.match(pattern, message, re.IGNORECASE)
            if match:
                context.parsed_command = {
                    'type': command_type,
                    'match': match.groups(),
                    'raw_message': context.sms_message.message_content
                }
                context.state = TransactionState.PARSED
                context.add_processing_step("parse_command", "completed", {
                    "command_type": command_type,
                    "parsed": True
                })
                return
        
        # If no command matched, try to extract phone and amount from natural language
        context.parsed_command = self._parse_natural_language(message)
        if context.parsed_command:
            context.state = TransactionState.PARSED
            context.add_processing_step("parse_command", "completed", {
                "command_type": "natural_language",
                "parsed": True
            })
        else:
            context.state = TransactionState.FAILED
            context.error_message = "Could not parse command"
            context.add_processing_step("parse_command", "failed", {
                "error": "No command pattern matched"
            })
            raise ValueError("Could not parse SMS command")
    
    def _parse_natural_language(self, message: str) -> Optional[Dict]:
        """Parse natural language payment requests"""
        # Extract phone numbers
        phone_pattern = r'\+\d{10,15}'
        phones = re.findall(phone_pattern, message)
        
        # Extract amounts
        amount_pattern = r'\d+'
        amounts = re.findall(amount_pattern, message)
        
        if len(phones) >= 1 and len(amounts) >= 1:
            return {
                'type': 'send',
                'recipient_phone': phones[0],
                'amount': int(amounts[0]),
                'message': message,
                'raw_message': message
            }
        
        return None
    
    async def _validate_transaction(self, context: TransactionContext):
        """Validate the transaction"""
        context.add_processing_step("validate_transaction", "started")
        
        if not context.parsed_command:
            raise ValueError("No parsed command available")
        
        command = context.parsed_command
        
        if command['type'] == 'send':
            # Validate amount
            if 'amount' not in command:
                # Extract from match groups
                if command['match'] and command['match'][0]:
                    context.amount = int(command['match'][0])
                else:
                    context.amount = command.get('amount', 0)
            else:
                context.amount = command['amount']
            
            if context.amount <= 0:
                raise ValueError("Amount must be positive")
            
            # Validate recipient phone
            if 'recipient_phone' not in command:
                if command['match'] and command['match'][1]:
                    command['recipient_phone'] = command['match'][1]
                else:
                    raise ValueError("Recipient phone number required")
            
            if not self._validate_phone_number(command['recipient_phone']):
                raise ValueError("Invalid recipient phone number")
        
        context.state = TransactionState.VALIDATED
        context.add_processing_step("validate_transaction", "completed", {
            "amount": context.amount,
            "recipient": command.get('recipient_phone')
        })
    
    async def _resolve_wallets(self, context: TransactionContext):
        """Resolve sender and recipient wallets"""
        context.add_processing_step("resolve_wallets", "started")
        
        command = context.parsed_command
        
        # Resolve sender wallet
        try:
            sender_wallet_data = self.membra_client.get_phone_wallet(context.sms_message.sender_phone)
            context.sender_wallet = MembraWallet(**sender_wallet_data)
        except:
            # Auto-register sender if not exists
            registration = self.membra_client.register_phone_wallet(context.sms_message.sender_phone)
            if registration.get('success'):
                context.sender_wallet = MembraWallet(
                    phone_number=context.sms_message.sender_phone,
                    wallet_address=registration['wallet_address'],
                    public_key=registration['public_key'],
                    balance=registration.get('balance', 0),
                    premined_tokens=registration.get('premined_tokens', 1000),
                    merkle_root=registration.get('merkle_root', ''),
                    is_active=True
                )
        
        # Resolve recipient wallet
        if command['type'] == 'send':
            recipient_phone = command['recipient_phone']
            try:
                recipient_wallet_data = self.membra_client.get_phone_wallet(recipient_phone)
                context.recipient_wallet = MembraWallet(**recipient_wallet_data)
            except:
                # Auto-register recipient
                registration = self.membra_client.register_phone_wallet(recipient_phone)
                if registration.get('success'):
                    context.recipient_wallet = MembraWallet(
                        phone_number=recipient_phone,
                        wallet_address=registration['wallet_address'],
                        public_key=registration['public_key'],
                        balance=registration.get('balance', 0),
                        premined_tokens=registration.get('premined_tokens', 1000),
                        merkle_root=registration.get('merkle_root', ''),
                        is_active=True
                    )
        
        context.state = TransactionState.WALLET_RESOLVED
        context.add_processing_step("resolve_wallets", "completed", {
            "sender_wallet": context.sender_wallet.wallet_address if context.sender_wallet else None,
            "recipient_wallet": context.recipient_wallet.wallet_address if context.recipient_wallet else None
        })
    
    async def _sponsor_transaction(self, context: TransactionContext):
        """Get sponsorship for the transaction"""
        context.add_processing_step("sponsor_transaction", "started")
        
        if context.amount > 0:
            sponsorship = self.sponsor_system.sponsor_transaction(
                context.amount,
                context.sms_message.sender_phone,
                "sms"
            )
            
            if sponsorship.get('success'):
                context.sponsor_id = sponsorship.get('sponsor_id')
                context.sponsor_bonus = sponsorship.get('bonus_amount', 0)
                context.mining_reward = sponsorship.get('mining_reward', 0)
        
        context.state = TransactionState.SPONSORED
        context.add_processing_step("sponsor_transaction", "completed", {
            "sponsor_id": context.sponsor_id,
            "bonus": context.sponsor_bonus,
            "mining_reward": context.mining_reward
        })
    
    async def _submit_to_network(self, context: TransactionContext):
        """Submit transaction to the network"""
        context.add_processing_step("submit_to_network", "started")
        
        if context.parsed_command['type'] == 'send' and context.recipient_wallet:
            payment_request = SMSPaymentRequest(
                sender_phone=context.sms_message.sender_phone,
                recipient_phone=context.recipient_wallet.phone_number,
                amount=context.amount,
                message=context.parsed_command.get('message', '')
            )
            
            response = await self.sms_gateway.process_payment(payment_request)
            
            if response.success:
                context.transaction_id = response.transaction_id
                context.blockchain_tx_hash = response.transaction_hash
                context.state = TransactionState.SUBMITTED
                context.add_processing_step("submit_to_network", "completed", {
                    "transaction_id": context.transaction_id,
                    "tx_hash": context.blockchain_tx_hash
                })
            else:
                raise ValueError(f"Payment failed: {response.error_message}")
        else:
            # Handle other command types
            context.state = TransactionState.SUBMITTED
            context.add_processing_step("submit_to_network", "completed", {
                "note": "No blockchain transaction required for this command type"
            })
    
    async def _confirm_transaction(self, context: TransactionContext):
        """Confirm the transaction on the blockchain"""
        context.add_processing_step("confirm_transaction", "started")
        
        if context.blockchain_tx_hash:
            # Simulate blockchain confirmation (in production, this would check actual blockchain)
            await asyncio.sleep(2)  # Simulate network delay
            
            # In production, verify transaction on blockchain
            confirmed = await self._verify_blockchain_transaction(context.blockchain_tx_hash)
            
            if confirmed:
                context.state = TransactionState.CONFIRMED
                context.add_processing_step("confirm_transaction", "completed", {
                    "confirmed": True,
                    "tx_hash": context.blockchain_tx_hash
                })
            else:
                raise ValueError("Transaction confirmation failed")
        else:
            context.state = TransactionState.CONFIRMED
            context.add_processing_step("confirm_transaction", "completed", {
                "note": "No blockchain confirmation needed"
            })
    
    async def _verify_blockchain_transaction(self, tx_hash: str) -> bool:
        """Verify transaction on blockchain (placeholder)"""
        # In production, this would query the actual blockchain
        # For now, simulate successful confirmation
        return True
    
    async def _complete_transaction(self, context: TransactionContext):
        """Complete the transaction and send notifications"""
        context.add_processing_step("complete_transaction", "started")
        
        # Send confirmation SMS to sender
        await self._send_confirmation_sms(context)
        
        # Send notification SMS to recipient if applicable
        if context.recipient_wallet:
            await self._send_recipient_notification(context)
        
        # Process mining rewards
        if context.mining_reward > 0:
            await self._process_mining_reward(context)
        
        context.state = TransactionState.COMPLETED
        context.add_processing_step("complete_transaction", "completed", {
            "final_state": "completed",
            "processing_time": (context.updated_at - context.created_at).total_seconds()
        })
    
    async def _send_confirmation_sms(self, context: TransactionContext):
        """Send confirmation SMS to sender"""
        if context.parsed_command['type'] == 'send':
            message = f"Payment of {context.amount} USDC to {context.recipient_wallet.phone_number} completed. TX: {context.transaction_id[:8]}..."
        else:
            message = "Your request has been processed successfully."
        
        # In production, this would send actual SMS
        logger.info(f"Confirmation SMS to {context.sms_message.sender_phone}: {message}")
    
    async def _send_recipient_notification(self, context: TransactionContext):
        """Send notification SMS to recipient"""
        if context.parsed_command['type'] == 'send':
            message = f"You received {context.amount} USDC from {context.sms_message.sender_phone}. TX: {context.transaction_id[:8]}..."
            
            # In production, this would send actual SMS
            logger.info(f"Notification SMS to {context.recipient_wallet.phone_number}: {message}")
    
    async def _process_mining_reward(self, context: TransactionContext):
        """Process mining rewards for the transaction"""
        if context.sender_wallet and context.mining_reward > 0:
            # In production, this would credit the mining reward to the sender's wallet
            logger.info(f"Crediting {context.mining_reward} mining reward to {context.sender_wallet.phone_number}")
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        pattern = r'^\+[1-9]\d{9,14}$'
        return bool(re.match(pattern, phone_number))
    
    def get_transaction_status(self, sms_message_id: str) -> Optional[TransactionContext]:
        """Get the status of a transaction by SMS message ID"""
        return self.active_transactions.get(sms_message_id)
    
    def get_transaction_history(self, phone_number: str = None, limit: int = 50) -> List[TransactionContext]:
        """Get transaction history, optionally filtered by phone number"""
        history = self.transaction_history
        
        if phone_number:
            history = [
                tx for tx in history 
                if tx.sms_message.sender_phone == phone_number or 
                   (tx.recipient_wallet and tx.recipient_wallet.phone_number == phone_number)
            ]
        
        # Sort by created_at descending
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return history[:limit]


# Global processor instance
sms_processor = SMSTransactionProcessor()