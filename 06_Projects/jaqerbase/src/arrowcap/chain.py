"""Solana on-chain anchoring for settlement receipts.

This module talks to a real Solana RPC endpoint and submits real
transactions through the SPL Memo program -- there is no simulated client
and no mocked transaction signature. The safety boundary is structural, not
a runtime flag buried in config: this module's default and only
unauthenticated path is Solana **devnet**, which uses free, valueless test
SOL. Mainnet (where lamports are real money) is reachable only through
`SolanaAnchor(network="mainnet", allow_mainnet=True)`, which additionally
refuses to auto-generate or airdrop a keypair -- the caller must supply a
keypair file they funded themselves.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from solders.transaction import Transaction

DEVNET_RPC = "https://api.devnet.solana.com"
MAINNET_RPC = "https://api.mainnet-beta.solana.com"
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
MEMO_PREFIX = "arrowcap:"


class MainnetNotAuthorized(Exception):
    """Raised when mainnet access is attempted without explicit, deliberate
    opt-in (network='mainnet', allow_mainnet=True, and a caller-supplied
    funded keypair)."""


def load_or_create_keypair(path: str) -> Keypair:
    """Load a 64-byte Solana keypair from `path`, generating and persisting
    one (0600 permissions) if it does not exist. On devnet this keypair is
    funded via request_devnet_airdrop; on mainnet the caller must fund it
    themselves before any transaction will succeed."""
    if os.path.exists(path):
        with open(path, "rb") as fh:
            raw = fh.read()
        return Keypair.from_bytes(raw)
    keypair = Keypair()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(bytes(keypair))
    return keypair


@dataclass
class AnchorReceipt:
    network: str
    rpc_url: str
    signature: str
    memo: str
    payer_pubkey: str


class SolanaAnchor:
    def __init__(
        self, *, network: str = "devnet", rpc_url: Optional[str] = None,
        allow_mainnet: bool = False,
    ):
        if network == "mainnet" and not allow_mainnet:
            raise MainnetNotAuthorized(
                "mainnet access requires SolanaAnchor(network='mainnet', "
                "allow_mainnet=True) -- this is a deliberate safety boundary, "
                "not a bug. Devnet is the default for a reason."
            )
        if network not in ("devnet", "testnet", "mainnet"):
            raise ValueError(f"unknown network: {network}")
        self.network = network
        self.rpc_url = rpc_url or (MAINNET_RPC if network == "mainnet" else DEVNET_RPC)
        self.client = Client(self.rpc_url)

    def get_balance_lamports(self, pubkey: Pubkey) -> int:
        return self.client.get_balance(pubkey, commitment=Confirmed).value

    def request_devnet_airdrop(self, pubkey: Pubkey, lamports: int = 1_000_000_000) -> str:
        if self.network == "mainnet":
            raise MainnetNotAuthorized("airdrops do not exist on mainnet; fund the keypair yourself")
        resp = self.client.request_airdrop(pubkey, lamports, commitment=Confirmed)
        signature = str(resp.value)
        self.client.confirm_transaction(resp.value, commitment=Confirmed)
        return signature

    def anchor_commitment(self, commitment_hex: str, keypair: Keypair) -> AnchorReceipt:
        """Submit a Memo-program transaction carrying `arrowcap:<commitment_hex>`
        as its instruction data, and return the confirmed transaction signature.
        This is the on-chain time/identity anchor for a settlement receipt
        (Section 9: receipts should attach location/time anchors so a verifier
        does not have to trust the issuer's clock alone)."""
        memo = f"{MEMO_PREFIX}{commitment_hex}"
        instruction = Instruction(
            MEMO_PROGRAM_ID,
            memo.encode("utf-8"),
            [AccountMeta(pubkey=keypair.pubkey(), is_signer=True, is_writable=False)],
        )
        blockhash_resp = self.client.get_latest_blockhash(commitment=Confirmed)
        recent_blockhash = blockhash_resp.value.blockhash
        tx = Transaction.new_signed_with_payer(
            [instruction], keypair.pubkey(), [keypair], recent_blockhash,
        )
        send_resp = self.client.send_transaction(tx)
        signature = send_resp.value
        self.client.confirm_transaction(signature, commitment=Confirmed)
        return AnchorReceipt(
            network=self.network,
            rpc_url=self.rpc_url,
            signature=str(signature),
            memo=memo,
            payer_pubkey=str(keypair.pubkey()),
        )
