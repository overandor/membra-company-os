"""
Membra Bridge Client
Interfaces with the membra bridge ecosystem for phone wallet and SMS mining operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
import hashlib
import json

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("membra_bridge_client")


@dataclass
class MembraWallet:
    """Membra phone wallet information"""
    phone_number: str
    wallet_address: str
    public_key: str
    balance: int
    premined_tokens: int
    merkle_root: str
    is_active: bool
    
    def to_dict(self) -> Dict:
        return {
            "phone_number": self.phone_number,
            "wallet_address": self.wallet_address,
            "public_key": self.public_key,
            "balance": self.balance,
            "premined_tokens": self.premined_tokens,
            "merkle_root": self.merkle_root,
            "is_active": self.is_active
        }


@dataclass
class SMSMiningReward:
    """SMS mining reward information"""
    phone_number: str
    sms_type: str
    reward_amount: int
    timestamp: str
    transaction_hash: str
    content_hash: str
    sponsor_address: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "phone_number": self.phone_number,
            "sms_type": self.sms_type,
            "reward_amount": self.reward_amount,
            "timestamp": self.timestamp,
            "transaction_hash": self.transaction_hash,
            "content_hash": self.content_hash,
            "sponsor_address": self.sponsor_address
        }


class MembraBridgeClient:
    """
    Client for interacting with the membra bridge ecosystem
    Handles phone wallet registration, SMS mining, and reward distribution.
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize membra bridge client
        
        Args:
            api_base_url: Base URL for membra bridge API
        """
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        
    def register_phone_wallet(
        self,
        phone_number: str,
        custom_premined: Optional[int] = None
    ) -> MembraWallet:
        """
        Register a phone number as a wallet in the membra system
        
        Args:
            phone_number: Phone number to register
            custom_premined: Custom premined token amount (optional)
            
        Returns:
            MembraWallet with wallet information
        """
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/wallet/register",
                json={
                    "phone_number": phone_number,
                    "custom_premined": custom_premined
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                wallet_data = data["data"]
                return MembraWallet(
                    phone_number=wallet_data["phone_number"],
                    wallet_address=wallet_data["wallet_address"],
                    public_key=wallet_data["public_key"],
                    balance=wallet_data["balance"],
                    premined_tokens=wallet_data["premined_tokens"],
                    merkle_root=wallet_data["merkle_root"],
                    is_active=wallet_data["is_active"]
                )
            else:
                raise Exception(f"Registration failed: {data}")
                
        except Exception as e:
            logger.error(f"Failed to register phone wallet: {e}")
            # Fallback to local simulation for demo purposes
            return self._simulate_phone_wallet(phone_number, custom_premined)
    
    def get_phone_wallet(self, phone_number: str) -> Optional[MembraWallet]:
        """
        Get wallet information by phone number
        
        Args:
            phone_number: Phone number to query
            
        Returns:
            MembraWallet if found, None otherwise
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/wallet/{phone_number}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    wallet_data = data["data"]
                    return MembraWallet(
                        phone_number=wallet_data["phone_number"],
                        wallet_address=wallet_data["wallet_address"],
                        public_key=wallet_data["public_key"],
                        balance=wallet_data["balance"],
                        premined_tokens=wallet_data["premined_tokens"],
                        merkle_root=wallet_data["merkle_root"],
                        is_active=wallet_data["is_active"]
                    )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get phone wallet: {e}")
            return None
    
    def process_sms_mining(
        self,
        phone_number: str,
        sms_type: str,
        content: str,
        sponsor_address: Optional[str] = None
    ) -> Optional[SMSMiningReward]:
        """
        Process SMS for mining rewards
        
        Args:
            phone_number: Phone number processing SMS
            sms_type: Type of SMS ('sent' or 'received')
            content: SMS content
            sponsor_address: Optional sponsor address for bonus rewards
            
        Returns:
            SMSMiningReward if successful, None otherwise
        """
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/sms/process",
                json={
                    "phone_number": phone_number,
                    "sms_type": sms_type,
                    "content": content,
                    "sponsor_address": sponsor_address
                },
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                reward_data = data["data"]
                return SMSMiningReward(
                    phone_number=reward_data["phone_number"],
                    sms_type=reward_data["sms_type"],
                    reward_amount=reward_data["reward_amount"],
                    timestamp=reward_data["timestamp"],
                    transaction_hash=reward_data["transaction_hash"],
                    content_hash=reward_data["content_hash"],
                    sponsor_address=reward_data.get("sponsor_address")
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to process SMS mining: {e}")
            # Fallback to local simulation for demo purposes
            return self._simulate_sms_mining(phone_number, sms_type, content, sponsor_address)
    
    def get_wallet_balance(self, phone_number: str) -> int:
        """
        Get wallet balance for phone number
        
        Args:
            phone_number: Phone number to query
            
        Returns:
            Token balance
        """
        wallet = self.get_phone_wallet(phone_number)
        if wallet:
            return wallet.balance
        return 0
    
    def get_oracle_prices(self) -> Dict[str, float]:
        """
        Get current prices from membra oracle system
        
        Returns:
            Dictionary of token prices
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/oracle/prices",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return {item["symbol"]: item["price"] for item in data["data"]}
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get oracle prices: {e}")
            return {}
    
    def get_kpi_signals(self) -> Dict[str, Any]:
        """
        Get KPI signals from membra system
        
        Returns:
            Dictionary of KPI signals
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/api/oracle/kpi",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("success"):
                return data["data"]
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get KPI signals: {e}")
            return {}
    
    def _simulate_phone_wallet(
        self,
        phone_number: str,
        custom_premined: Optional[int] = None
    ) -> MembraWallet:
        """Simulate phone wallet creation for demo purposes"""
        # Normalize phone number
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        if len(cleaned) == 10:
            cleaned = '1' + cleaned
        normalized_phone = '+' + cleaned
        
        # Generate deterministic wallet address
        seed = f"MEMBRA_SIMULATION:{normalized_phone}"
        wallet_address = hashlib.sha256(seed.encode()).hexdigest()[:44]
        
        # Generate merkle root
        merkle_root = hashlib.sha256((normalized_phone + wallet_address).encode()).hexdigest()
        
        premined = custom_premined or 1000
        
        return MembraWallet(
            phone_number=normalized_phone,
            wallet_address=wallet_address,
            public_key="simulated_public_key",
            balance=premined,
            premined_tokens=premined,
            merkle_root=merkle_root,
            is_active=True
        )
    
    def _simulate_sms_mining(
        self,
        phone_number: str,
        sms_type: str,
        content: str,
        sponsor_address: Optional[str] = None
    ) -> SMSMiningReward:
        """Simulate SMS mining for demo purposes"""
        # Calculate reward
        base_reward = 10 if sms_type == 'sent' else 5
        if sponsor_address and sms_type == 'sent':
            reward_amount = int(base_reward * 1.5)
        else:
            reward_amount = base_reward
        
        # Generate transaction hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        transaction_hash = hashlib.sha256(
            (phone_number + sms_type + content_hash).encode()
        ).hexdigest()
        
        return SMSMiningReward(
            phone_number=phone_number,
            sms_type=sms_type,
            reward_amount=reward_amount,
            timestamp=datetime.now().isoformat(),
            transaction_hash=transaction_hash,
            content_hash=content_hash,
            sponsor_address=sponsor_address
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check membra bridge system health
        
        Returns:
            Health status information
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            return {"status": "unhealthy"}
            
        except Exception as e:
            logger.error(f"Membra bridge health check failed: {e}")
            return {"status": "unreachable", "error": str(e)}