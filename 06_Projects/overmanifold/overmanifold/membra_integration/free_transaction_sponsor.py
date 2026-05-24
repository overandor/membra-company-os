"""
Free Transaction Sponsor System
Enables truly free transactions by having sponsors cover the costs.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json

from overmanifold.infrastructure.logging_config import get_logger

logger = get_logger("free_transaction_sponsor")


@dataclass
class Sponsor:
    """Transaction sponsor information"""
    sponsor_id: str
    sponsor_address: str
    sponsor_name: str
    sponsor_type: str  # 'individual', 'corporate', 'protocol'
    daily_budget: int
    remaining_budget: int
    sponsor_level: str  # 'bronze', 'silver', 'gold', 'platinum'
    is_active: bool
    created_at: str
    last_reset: str
    
    def to_dict(self) -> Dict:
        return {
            "sponsor_id": self.sponsor_id,
            "sponsor_address": self.sponsor_address,
            "sponsor_name": self.sponsor_name,
            "sponsor_type": self.sponsor_type,
            "daily_budget": self.daily_budget,
            "remaining_budget": self.remaining_budget,
            "sponsor_level": self.sponsor_level,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_reset": self.last_reset
        }


@dataclass
class SponsoredTransaction:
    """Sponsored transaction record"""
    transaction_id: str
    sponsor_id: str
    user_identifier: str  # phone number or email
    amount_sponsored: int
    transaction_cost: int
    mining_bonus: int
    timestamp: str
    transaction_hash: str
    
    def to_dict(self) -> Dict:
        return {
            "transaction_id": self.transaction_id,
            "sponsor_id": self.sponsor_id,
            "user_identifier": user_identifier,
            "amount_sponsored": self.amount_sponsored,
            "transaction_cost": self.transaction_cost,
            "mining_bonus": self.mining_bonus,
            "timestamp": self.timestamp,
            "transaction_hash": self.transaction_hash
        }


class FreeTransactionSponsor:
    """
    Free transaction sponsor system
    Enables truly free transactions by having sponsors cover the costs.
    """
    
    def __init__(self):
        """Initialize free transaction sponsor system"""
        self.sponsors: Dict[str, Sponsor] = {}
        self.sponsored_transactions: List[SponsoredTransaction] = []
        self.sponsor_levels = {
            "bronze": {"daily_budget": 1000, "mining_bonus": 5},
            "silver": {"daily_budget": 5000, "mining_bonus": 10},
            "gold": {"daily_budget": 20000, "mining_bonus": 20},
            "platinum": {"daily_budget": 100000, "mining_bonus": 50}
        }
        
        # Initialize default sponsors
        self._initialize_default_sponsors()
    
    def _initialize_default_sponsors(self):
        """Initialize default protocol sponsors"""
        # Protocol treasury as default sponsor
        protocol_sponsor = Sponsor(
            sponsor_id="protocol_treasury",
            sponsor_address="0x0000000000000000000000000000000000000000",
            sponsor_name="Overmanifold Protocol Treasury",
            sponsor_type="protocol",
            daily_budget=1000000,  # 1M tokens daily
            remaining_budget=1000000,
            sponsor_level="platinum",
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_reset=datetime.now().isoformat()
        )
        
        self.sponsors[protocol_sponsor.sponsor_id] = protocol_sponsor
        logger.info("Initialized default protocol sponsor")
    
    def register_sponsor(
        self,
        sponsor_address: str,
        sponsor_name: str,
        sponsor_type: str = "individual",
        sponsor_level: str = "bronze",
        custom_budget: Optional[int] = None
    ) -> Sponsor:
        """
        Register a new sponsor
        
        Args:
            sponsor_address: Sponsor's wallet address
            sponsor_name: Sponsor's name
            sponsor_type: Type of sponsor (individual, corporate, protocol)
            sponsor_level: Sponsor level (bronze, silver, gold, platinum)
            custom_budget: Custom daily budget (optional)
            
        Returns:
            Sponsor object
        """
        sponsor_id = f"sponsor_{hashlib.sha256(sponsor_address.encode()).hexdigest()[:8]}"
        
        # Get budget from level or custom
        if custom_budget:
            daily_budget = custom_budget
        else:
            daily_budget = self.sponsor_levels.get(sponsor_level, {}).get("daily_budget", 1000)
        
        sponsor = Sponsor(
            sponsor_id=sponsor_id,
            sponsor_address=sponsor_address,
            sponsor_name=sponsor_name,
            sponsor_type=sponsor_type,
            daily_budget=daily_budget,
            remaining_budget=daily_budget,
            sponsor_level=sponsor_level,
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_reset=datetime.now().isoformat()
        )
        
        self.sponsors[sponsor_id] = sponsor
        logger.info(f"Registered new sponsor: {sponsor_name} ({sponsor_level})")
        
        return sponsor
    
    def sponsor_transaction(
        self,
        user_identifier: str,
        amount: int,
        transaction_cost: int,
        preferred_sponsor_id: Optional[str] = None
    ) -> Optional[SponsoredTransaction]:
        """
        Sponsor a transaction to make it free for the user
        
        Args:
            user_identifier: User's phone number or email
            amount: Transaction amount
            transaction_cost: Cost of transaction
            preferred_sponsor_id: Preferred sponsor ID (optional)
            
        Returns:
            SponsoredTransaction if successful, None otherwise
        """
        # Reset daily budgets if needed
        self._reset_daily_budgets()
        
        # Select sponsor
        sponsor = self._select_sponsor(amount, preferred_sponsor_id)
        
        if not sponsor:
            logger.warning("No available sponsor for transaction")
            return None
        
        # Check sponsor has enough budget
        if sponsor.remaining_budget < transaction_cost:
            logger.warning(f"Sponsor {sponsor.sponsor_id} has insufficient budget")
            return None
        
        # Calculate mining bonus based on sponsor level
        mining_bonus = self.sponsor_levels.get(sponsor.sponsor_level, {}).get("mining_bonus", 5)
        
        # Generate transaction ID
        transaction_id = self._generate_transaction_id(user_identifier, amount)
        
        # Generate transaction hash
        transaction_hash = self._generate_transaction_hash(transaction_id, user_identifier, amount)
        
        # Create sponsored transaction record
        sponsored_transaction = SponsoredTransaction(
            transaction_id=transaction_id,
            sponsor_id=sponsor.sponsor_id,
            user_identifier=user_identifier,
            amount_sponsored=amount,
            transaction_cost=transaction_cost,
            mining_bonus=mining_bonus,
            timestamp=datetime.now().isoformat(),
            transaction_hash=transaction_hash
        )
        
        # Deduct from sponsor budget
        sponsor.remaining_budget -= transaction_cost
        
        # Record transaction
        self.sponsored_transactions.append(sponsored_transaction)
        
        logger.info(f"Transaction sponsored: {transaction_id} by {sponsor.sponsor_name}")
        
        return sponsored_transaction
    
    def _select_sponsor(
        self,
        amount: int,
        preferred_sponsor_id: Optional[str] = None
    ) -> Optional[Sponsor]:
        """Select appropriate sponsor for transaction"""
        # If preferred sponsor specified, try to use them
        if preferred_sponsor_id:
            sponsor = self.sponsors.get(preferred_sponsor_id)
            if sponsor and sponsor.is_active and sponsor.remaining_budget >= amount:
                return sponsor
        
        # Otherwise, find available sponsor with sufficient budget
        for sponsor in self.sponsors.values():
            if sponsor.is_active and sponsor.remaining_budget >= amount:
                return sponsor
        
        return None
    
    def _reset_daily_budgets(self):
        """Reset daily budgets at midnight"""
        now = datetime.now()
        
        for sponsor in self.sponsors.values():
            last_reset = datetime.fromisoformat(sponsor.last_reset)
            
            # Reset if last reset was more than 24 hours ago
            if now - last_reset > timedelta(hours=24):
                sponsor.remaining_budget = sponsor.daily_budget
                sponsor.last_reset = now.isoformat()
                logger.info(f"Reset daily budget for sponsor: {sponsor.sponsor_name}")
    
    def _generate_transaction_id(
        self,
        user_identifier: str,
        amount: int
    ) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().isoformat()
        data = f"{user_identifier}:{amount}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _generate_transaction_hash(
        self,
        transaction_id: str,
        user_identifier: str,
        amount: int
    ) -> str:
        """Generate transaction hash"""
        data = f"{transaction_id}:{user_identifier}:{amount}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_sponsor_info(self, sponsor_id: str) -> Optional[Sponsor]:
        """Get sponsor information"""
        return self.sponsors.get(sponsor_id)
    
    def get_all_sponsors(self) -> List[Sponsor]:
        """Get all active sponsors"""
        return [s for s in self.sponsors.values() if s.is_active]
    
    def get_sponsor_statistics(self) -> Dict[str, Any]:
        """Get sponsor system statistics"""
        active_sponsors = self.get_all_sponsors()
        
        total_budget = sum(s.daily_budget for s in active_sponsors)
        total_remaining = sum(s.remaining_budget for s in active_sponsors)
        total_sponsored = sum(t.amount_sponsored for t in self.sponsored_transactions)
        
        sponsor_count_by_level = {}
        for sponsor in active_sponsors:
            level = sponsor.sponsor_level
            sponsor_count_by_level[level] = sponsor_count_by_level.get(level, 0) + 1
        
        return {
            "active_sponsors": len(active_sponsors),
            "total_daily_budget": total_budget,
            "total_remaining_budget": total_remaining,
            "total_sponsored_amount": total_sponsored,
            "sponsor_count_by_level": sponsor_count_by_level,
            "total_transactions_sponsored": len(self.sponsored_transactions)
        }
    
    def get_user_sponsorship_history(
        self,
        user_identifier: str,
        limit: int = 50
    ) -> List[SponsoredTransaction]:
        """Get sponsorship history for a user"""
        user_transactions = [
            t for t in self.sponsored_transactions
            if t.user_identifier == user_identifier
        ]
        return user_transactions[-limit:]
    
    def update_sponsor_budget(
        self,
        sponsor_id: str,
        additional_budget: int
    ) -> bool:
        """
        Add additional budget to a sponsor
        
        Args:
            sponsor_id: Sponsor ID
            additional_budget: Additional budget to add
            
        Returns:
            True if successful, False otherwise
        """
        sponsor = self.sponsors.get(sponsor_id)
        if not sponsor:
            return False
        
        sponsor.remaining_budget += additional_budget
        sponsor.daily_budget += additional_budget
        
        logger.info(f"Added {additional_budget} to sponsor {sponsor.sponsor_name}")
        return True
    
    def deactivate_sponsor(self, sponsor_id: str) -> bool:
        """
        Deactivate a sponsor
        
        Args:
            sponsor_id: Sponsor ID to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        sponsor = self.sponsors.get(sponsor_id)
        if not sponsor:
            return False
        
        sponsor.is_active = False
        logger.info(f"Deactivated sponsor: {sponsor.sponsor_name}")
        return True