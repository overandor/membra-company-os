"""
Phone Wallet Module - Maps phone numbers to Solana wallet addresses
Handles phone-to-wallet mapping, premined tokens, and merkle tree derivation.
"""

import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import base58
import nacl.signing
import nacl.encoding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PhoneWallet:
    """Phone number mapped to wallet address"""
    phone_number: str
    wallet_address: str
    public_key: str
    private_key: str  # Encrypted in production
    balance: int
    premined_tokens: int
    merkle_root: str
    registration_date: str
    is_active: bool
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SMSMiningReward:
    """Reward for SMS mining activity"""
    phone_number: str
    sms_type: str  # 'sent' or 'received'
    reward_amount: int
    timestamp: str
    transaction_hash: str
    content_hash: str
    sponsor_address: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PhoneWalletMapper:
    """Maps phone numbers to Solana wallet addresses using cryptographic derivation"""
    
    def __init__(self, seed_phrase: str = "MEMBRA_BRIDGE_ECOSYSTEM_2024"):
        self.seed_phrase = seed_phrase
        self.wallets: Dict[str, PhoneWallet] = {}
        self.merkle_trees: Dict[str, str] = {}
        self.sms_rewards: List[SMSMiningReward] = []
        self.premined_amount = 1000  # Default premined tokens per phone
        
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to standard format"""
        # Remove all non-numeric characters
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        
        # Ensure it starts with country code (default to +1 if no country code)
        if len(cleaned) == 10:
            cleaned = '1' + cleaned
        
        return '+' + cleaned
    
    def _derive_wallet_from_phone(self, phone_number: str) -> Tuple[str, str, str]:
        """Derive wallet address, public key, and private key from phone number"""
        normalized_phone = self._normalize_phone_number(phone_number)
        
        # Create a deterministic seed from phone number and system seed
        combined_seed = f"{self.seed_phrase}:{normalized_phone}"
        seed_hash = hashlib.sha256(combined_seed.encode()).digest()
        
        # Generate Ed25519 key pair from seed
        signing_key = nacl.signing.SigningKey(seed_hash)
        verify_key = signing_key.verify_key
        
        # Get private and public keys
        private_key = signing_key.encode(encoder=nacl.encoding.RawEncoder)
        public_key = verify_key.encode(encoder=nacl.encoding.RawEncoder)
        
        # Convert to Solana address (base58 encoded public key)
        wallet_address = base58.b58encode(public_key).decode('ascii')
        
        return wallet_address, public_key.hex(), private_key.hex()
    
    def _derive_merkle_root(self, phone_number: str, wallet_address: str) -> str:
        """Derive merkle root from phone number and wallet address"""
        normalized_phone = self._normalize_phone_number(phone_number)
        
        # Create hierarchical hash
        level1 = hashlib.sha256(normalized_phone.encode()).hexdigest()
        level2 = hashlib.sha256(wallet_address.encode()).hexdigest()
        level3 = hashlib.sha256((level1 + level2).encode()).hexdigest()
        
        return level3
    
    def register_phone(self, phone_number: str, custom_premined: Optional[int] = None) -> PhoneWallet:
        """Register a phone number and create wallet"""
        normalized_phone = self._normalize_phone_number(phone_number)
        
        if normalized_phone in self.wallets:
            logger.warning(f"Phone number already registered: {normalized_phone}")
            return self.wallets[normalized_phone]
        
        # Derive wallet
        wallet_address, public_key, private_key = self._derive_wallet_from_phone(phone_number)
        
        # Derive merkle root
        merkle_root = self._derive_merkle_root(phone_number, wallet_address)
        
        # Set premined amount
        premined = custom_premined if custom_premined is not None else self.premined_amount
        
        # Create wallet
        wallet = PhoneWallet(
            phone_number=normalized_phone,
            wallet_address=wallet_address,
            public_key=public_key,
            private_key=private_key,
            balance=premined,
            premined_tokens=premined,
            merkle_root=merkle_root,
            registration_date=datetime.now().isoformat(),
            is_active=True
        )
        
        self.wallets[normalized_phone] = wallet
        self.merkle_trees[normalized_phone] = merkle_root
        
        logger.info(f"Registered phone {normalized_phone} -> wallet {wallet_address}")
        return wallet
    
    def get_wallet(self, phone_number: str) -> Optional[PhoneWallet]:
        """Get wallet by phone number"""
        normalized_phone = self._normalize_phone_number(phone_number)
        return self.wallets.get(normalized_phone)
    
    def get_wallet_by_address(self, wallet_address: str) -> Optional[PhoneWallet]:
        """Get wallet by wallet address"""
        for wallet in self.wallets.values():
            if wallet.wallet_address == wallet_address:
                return wallet
        return None
    
    def verify_wallet_ownership(self, phone_number: str, signature: str, message: str) -> bool:
        """Verify that a signature matches the wallet derived from phone number"""
        wallet = self.get_wallet(phone_number)
        if not wallet:
            return False
        
        try:
            # Verify signature using public key
            verify_key = nacl.signing.VerifyKey(bytes.fromhex(wallet.public_key))
            verify_key.verify(message.encode(), base58.b58decode(signature))
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def get_merkle_root(self, phone_number: str) -> Optional[str]:
        """Get merkle root for phone number"""
        normalized_phone = self._normalize_phone_number(phone_number)
        return self.merkle_trees.get(normalized_phone)
    
    def get_all_wallets(self) -> List[PhoneWallet]:
        """Get all registered wallets"""
        return list(self.wallets.values())


class SMSMiningEngine:
    """Handles SMS mining and reward distribution"""
    
    def __init__(self, wallet_mapper: PhoneWalletMapper):
        self.wallet_mapper = wallet_mapper
        self.send_reward = 10  # Tokens for sending SMS
        self.receive_reward = 5  # Tokens for receiving SMS
        self.sponsor_multiplier = 1.5  # Bonus for sponsored messages
        
    def _hash_sms_content(self, content: str) -> str:
        """Hash SMS content for verification"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _calculate_reward(self, sms_type: str, is_sponsored: bool = False) -> int:
        """Calculate reward based on SMS type and sponsorship"""
        base_reward = self.send_reward if sms_type == 'sent' else self.receive_reward
        
        if is_sponsored and sms_type == 'sent':
            return int(base_reward * self.sponsor_multiplier)
        
        return base_reward
    
    def process_sms(
        self,
        phone_number: str,
        sms_type: str,
        content: str,
        sponsor_address: Optional[str] = None
    ) -> Optional[SMSMiningReward]:
        """Process SMS and distribute mining rewards"""
        wallet = self.wallet_mapper.get_wallet(phone_number)
        if not wallet:
            logger.error(f"No wallet found for phone: {phone_number}")
            return None
        
        if not wallet.is_active:
            logger.error(f"Wallet is not active: {phone_number}")
            return None
        
        # Calculate reward
        is_sponsored = sponsor_address is not None
        reward_amount = self._calculate_reward(sms_type, is_sponsored)
        
        # Update wallet balance
        wallet.balance += reward_amount
        
        # Create reward record
        content_hash = self._hash_sms_content(content)
        transaction_hash = hashlib.sha256(
            f"{phone_number}{sms_type}{content_hash}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        reward = SMSMiningReward(
            phone_number=phone_number,
            sms_type=sms_type,
            reward_amount=reward_amount,
            timestamp=datetime.now().isoformat(),
            transaction_hash=transaction_hash,
            content_hash=content_hash,
            sponsor_address=sponsor_address
        )
        
        self.wallet_mapper.sms_rewards.append(reward)
        
        logger.info(f"Processed {sms_type} SMS for {phone_number}: +{reward_amount} tokens")
        return reward
    
    def get_rewards(self, phone_number: str) -> List[SMSMiningReward]:
        """Get all rewards for a phone number"""
        return [r for r in self.wallet_mapper.sms_rewards if r.phone_number == phone_number]
    
    def get_total_rewards(self, phone_number: str) -> int:
        """Get total rewards for a phone number"""
        rewards = self.get_rewards(phone_number)
        return sum(r.reward_amount for r in rewards)
    
    def get_mining_stats(self) -> Dict:
        """Get overall mining statistics"""
        total_rewards = len(self.wallet_mapper.sms_rewards)
        total_tokens_distributed = sum(r.reward_amount for r in self.wallet_mapper.sms_rewards)
        
        sent_count = sum(1 for r in self.wallet_mapper.sms_rewards if r.sms_type == 'sent')
        received_count = sum(1 for r in self.wallet_mapper.sms_rewards if r.sms_type == 'received')
        
        return {
            'total_rewards': total_rewards,
            'total_tokens_distributed': total_tokens_distributed,
            'sent_sms_count': sent_count,
            'received_sms_count': received_count,
            'active_miners': len([w for w in self.wallet_mapper.wallets.values() if w.is_active])
        }


class PhoneWalletBridge:
    """Bridge between phone wallets and Solana blockchain"""
    
    def __init__(self, wallet_mapper: PhoneWalletMapper, mining_engine: SMSMiningEngine):
        self.wallet_mapper = wallet_mapper
        self.mining_engine = mining_engine
        self.pending_transactions: List[Dict] = []
    
    def sync_to_blockchain(self) -> Dict:
        """Sync wallet states to blockchain (placeholder for actual Solana integration)"""
        sync_results = []
        
        for wallet in self.wallet_mapper.get_all_wallets():
            if wallet.is_active:
                # In production, this would interact with Solana smart contracts
                sync_result = {
                    'phone_number': wallet.phone_number,
                    'wallet_address': wallet.wallet_address,
                    'balance': wallet.balance,
                    'status': 'synced',
                    'timestamp': datetime.now().isoformat()
                }
                sync_results.append(sync_result)
        
        return {
            'synced_wallets': len(sync_results),
            'results': sync_results
        }
    
    def generate_transaction_proof(self, phone_number: str) -> Dict:
        """Generate cryptographic proof of transaction"""
        wallet = self.wallet_mapper.get_wallet(phone_number)
        if not wallet:
            return {'error': 'Wallet not found'}
        
        rewards = self.mining_engine.get_rewards(phone_number)
        
        # Create cumulative proof
        reward_hashes = [r.transaction_hash for r in rewards]
        cumulative_hash = hashlib.sha256(''.join(reward_hashes).encode()).hexdigest()
        
        return {
            'phone_number': phone_number,
            'wallet_address': wallet.wallet_address,
            'total_rewards': len(rewards),
            'total_tokens': sum(r.reward_amount for r in rewards),
            'cumulative_hash': cumulative_hash,
            'merkle_root': wallet.merkle_root,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Example usage"""
    import sys
    
    # Initialize systems
    wallet_mapper = PhoneWalletMapper()
    mining_engine = SMSMiningEngine(wallet_mapper)
    bridge = PhoneWalletBridge(wallet_mapper, mining_engine)
    
    # Register phone numbers
    phone1 = "+14155552671"  # Example US number
    phone2 = "+442071838750"  # Example UK number
    
    wallet1 = wallet_mapper.register_phone(phone1, custom_premined=1500)
    wallet2 = wallet_mapper.register_phone(phone2, custom_premined=1200)
    
    print(f"\n=== Registered Wallets ===")
    print(f"Phone 1: {wallet1.phone_number} -> {wallet1.wallet_address}")
    print(f"Balance: {wallet1.balance} tokens")
    print(f"Merkle Root: {wallet1.merkle_root}")
    
    print(f"\nPhone 2: {wallet2.phone_number} -> {wallet2.wallet_address}")
    print(f"Balance: {wallet2.balance} tokens")
    print(f"Merkle Root: {wallet2.merkle_root}")
    
    # Process SMS mining
    print(f"\n=== SMS Mining ===")
    
    # Phone 1 sends SMS (sponsored)
    reward1 = mining_engine.process_sms(
        phone1,
        'sent',
        'Hello from the membra bridge!',
        sponsor_address='SPONSOR_WALLET_ADDRESS'
    )
    print(f"Phone 1 sent SMS: +{reward1.reward_amount} tokens")
    
    # Phone 2 receives SMS
    reward2 = mining_engine.process_sms(
        phone2,
        'received',
        'Hello from the membra bridge!'
    )
    print(f"Phone 2 received SMS: +{reward2.reward_amount} tokens")
    
    # Print updated balances
    print(f"\n=== Updated Balances ===")
    print(f"Phone 1: {wallet1.balance} tokens")
    print(f"Phone 2: {wallet2.balance} tokens")
    
    # Get mining stats
    stats = mining_engine.get_mining_stats()
    print(f"\n=== Mining Statistics ===")
    print(f"Total Rewards: {stats['total_rewards']}")
    print(f"Total Tokens Distributed: {stats['total_tokens_distributed']}")
    print(f"Sent SMS: {stats['sent_sms_count']}")
    print(f"Received SMS: {stats['received_sms_count']}")
    
    # Generate transaction proof
    proof = bridge.generate_transaction_proof(phone1)
    print(f"\n=== Transaction Proof ===")
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()