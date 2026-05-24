"""
MEMBRA Relayer — Submits transactions on behalf of users, gets reimbursed from GasVault.

The relayer is the bridge between gasless intents and on-chain settlement.
It pays real Solana gas fees and gets reimbursed from GasVault using fee credits.
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .config import L3Config, DEFAULT_CONFIG
from .gas_vault import gas_vault, FeeCredit
from .intent_network import intent_network, PaymentIntent, IntentStatus
from .token_router import token_router, RouteQuote
from .proof_book import proof_book, ProofType
from .identity import identity_registry


@dataclass
class RelayerConfig:
    relayer_address: str
    min_profit_lamports: int = 5000  # minimum profit per relay
    max_gas_per_tx: int = 100_000    # max gas willing to pay
    supported_tokens: List[str] = field(default_factory=lambda: ["USDC", "SOL", "MEMBRA"])
    blacklisted_users: List[str] = field(default_factory=list)


@dataclass
class RelayResult:
    success: bool
    intent_id: str
    tx_signature: Optional[str] = None
    gas_spent_lamports: int = 0
    reimbursement_lamports: int = 0
    profit_lamports: int = 0
    error: Optional[str] = None


class Relayer:
    """
    Watches for pending intents and settles them on-chain.

    Flow:
    1. Find claimable intents
    2. Validate sender identity and risk limits
    3. Get route quote from TokenRouter
    4. Check user has fee credits
    5. Submit on-chain transaction (paying gas)
    6. Get reimbursed from GasVault
    """

    def __init__(self, config: RelayerConfig, l3_config: L3Config = DEFAULT_CONFIG):
        self.config = config
        self.l3_config = l3_config
        self._relayed_count: int = 0
        self._total_profit_lamports: int = 0
        self._total_gas_spent: int = 0

    def find_claimable_intents(self) -> List[PaymentIntent]:
        """Find all intents this relayer can profitably settle."""
        candidates = []
        for intent_id, intent in intent_network._intents.items():
            if not intent.is_claimable():
                continue
            if intent.sender_address in self.config.blacklisted_users:
                continue
            if intent.token_symbol not in self.config.supported_tokens:
                continue
            candidates.append(intent)
        return candidates

    def relay_intent(self, intent: PaymentIntent) -> RelayResult:
        """
        Execute the full relay flow for one intent.

        Returns RelayResult with success/failure and profit details.
        """
        # 1. Check identity and risk limits
        max_transfer, _ = identity_registry.get_risk_adjusted_limits(intent.sender_address)
        token = self.l3_config.get_token(intent.token_symbol)
        if token:
            amount_usd = intent.amount / (10 ** token.decimals)
            # Simplified USD conversion; production would use oracle
            if intent.token_symbol == "SOL":
                amount_usd *= 150
            elif intent.token_symbol == "MEMBRA":
                amount_usd *= 0.01
            if amount_usd > max_transfer:
                return RelayResult(
                    success=False, intent_id=intent.intent_id,
                    error=f"Exceeds risk limit: ${amount_usd:.2f} > ${max_transfer:.2f}"
                )

        # 2. Get route quote (if token conversion needed)
        route_tx_sig: Optional[str] = None
        if intent.token_symbol != intent.token_symbol:  # same token, no route needed
            quote = token_router.get_quote(intent.token_symbol, intent.token_symbol, intent.amount)
            if not quote:
                return RelayResult(
                    success=False, intent_id=intent.intent_id,
                    error="No route available"
                )
            route_tx_sig = token_router.execute_route(
                quote, intent.sender_address, intent.receiver_address
            )

        # 3. Check user fee credits
        user_credits = gas_vault.get_user_credits(intent.sender_address)
        if not user_credits:
            return RelayResult(
                success=False, intent_id=intent.intent_id,
                error="No fee credits available"
            )

        # 4. Estimate gas cost
        estimated_gas = self._estimate_gas(intent)
        if estimated_gas > self.config.max_gas_per_tx:
            return RelayResult(
                success=False, intent_id=intent.intent_id,
                error=f"Gas too high: {estimated_gas} > {self.config.max_gas_per_tx}"
            )

        # 5. Select credits to consume
        credits_to_use = self._select_credits(user_credits, estimated_gas)
        total_credit = sum(c.amount_lamports for c in credits_to_use)
        profit = total_credit - estimated_gas

        if profit < self.config.min_profit_lamports:
            return RelayResult(
                success=False, intent_id=intent.intent_id,
                error=f"Not profitable: {profit} lamports < {self.config.min_profit_lamports}"
            )

        # 6. Claim the intent
        claimed = intent_network.claim_intent(intent.intent_id, self.config.relayer_address)
        if not claimed:
            return RelayResult(
                success=False, intent_id=intent.intent_id,
                error="Failed to claim intent"
            )

        # 7. Submit on-chain tx (simulated)
        tx_sig = route_tx_sig or uuid.uuid4().hex[:44]

        # 8. Confirm settlement
        credit_ids = [c.credit_id for c in credits_to_use]
        intent_network.confirm_settlement(
            intent.intent_id, tx_sig, self.config.relayer_address, credit_ids
        )

        # 9. Get reimbursed from GasVault
        reimbursement = gas_vault.reimburse_relayer(
            self.config.relayer_address, tx_sig, credit_ids
        )

        if not reimbursement:
            return RelayResult(
                success=False, intent_id=intent.intent_id,
                error="Reimbursement failed"
            )

        self._relayed_count += 1
        self._total_profit_lamports += profit
        self._total_gas_spent += estimated_gas

        return RelayResult(
            success=True,
            intent_id=intent.intent_id,
            tx_signature=tx_sig,
            gas_spent_lamports=estimated_gas,
            reimbursement_lamports=reimbursement.amount_lamports,
            profit_lamports=profit,
        )

    def relay_all_profitable(self) -> List[RelayResult]:
        """Find and relay all profitable intents."""
        results = []
        for intent in self.find_claimable_intents():
            result = self.relay_intent(intent)
            results.append(result)
        return results

    # ─── Internal ───────────────────────────────────────────

    def _estimate_gas(self, intent: PaymentIntent) -> int:
        """Estimate Solana gas cost for settling this intent."""
        # Base: 5000 lamports per signature
        # Token transfer: ~10000 lamports
        # With compute units: ~20000 lamports
        base = 5000
        if intent.token_symbol != "SOL":
            base += 10000  # SPL token transfer
        return base

    def _select_credits(self, credits: List[FeeCredit],
                        gas_needed: int) -> List[FeeCredit]:
        """Select credits to cover gas, preferring smallest first."""
        active = [c for c in credits if c.status.value == "active"]
        active.sort(key=lambda c: c.amount_lamports)

        selected = []
        total = 0
        for c in active:
            selected.append(c)
            total += c.amount_lamports
            if total >= gas_needed + self.config.min_profit_lamports:
                break
        return selected

    @property
    def stats(self) -> dict:
        return {
            "relayer_address": self.config.relayer_address,
            "relayed_count": self._relayed_count,
            "total_profit_lamports": self._total_profit_lamports,
            "total_gas_spent": self._total_gas_spent,
            "net_profit_sol": self._total_profit_lamports / 1e9,
        }
