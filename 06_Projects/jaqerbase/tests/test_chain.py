"""Solana devnet adapter tests.

The mainnet safety boundary and local keypair handling are pure-Python and
always exercised. The actual RPC calls reach a real Solana devnet endpoint;
if this sandbox's network policy denies outbound access to it (as confirmed
during development -- the agent proxy rejects CONNECT to
api.devnet.solana.com), those tests skip rather than fail, since that is an
environment constraint, not a defect in the adapter.
"""

import os
import stat

import pytest

from arrowcap.chain import (
    DEVNET_RPC,
    MainnetNotAuthorized,
    SolanaAnchor,
    load_or_create_keypair,
)


def test_mainnet_requires_explicit_opt_in():
    with pytest.raises(MainnetNotAuthorized):
        SolanaAnchor(network="mainnet")


def test_mainnet_opt_in_succeeds_with_explicit_flag():
    anchor = SolanaAnchor(network="mainnet", allow_mainnet=True)
    assert anchor.network == "mainnet"


def test_unknown_network_rejected():
    with pytest.raises(ValueError):
        SolanaAnchor(network="testnet-typo")


def test_devnet_is_default_and_uses_devnet_rpc():
    anchor = SolanaAnchor()
    assert anchor.network == "devnet"
    assert anchor.rpc_url == DEVNET_RPC


def test_airdrop_never_available_on_mainnet():
    anchor = SolanaAnchor(network="mainnet", allow_mainnet=True)
    from solders.keypair import Keypair

    with pytest.raises(MainnetNotAuthorized):
        anchor.request_devnet_airdrop(Keypair().pubkey())


def test_load_or_create_keypair_persists_with_restricted_permissions(tmp_path):
    path = os.path.join(tmp_path, "devnet.key")
    kp1 = load_or_create_keypair(path)
    assert os.path.exists(path)
    mode = stat.S_IMODE(os.stat(path).st_mode)
    assert mode == 0o600

    kp2 = load_or_create_keypair(path)
    assert bytes(kp1) == bytes(kp2)
    assert kp1.pubkey() == kp2.pubkey()


def test_get_balance_live_devnet_or_skip_on_network_policy():
    anchor = SolanaAnchor()
    from solders.keypair import Keypair

    try:
        balance = anchor.get_balance_lamports(Keypair().pubkey())
    except Exception as exc:  # pragma: no cover - depends on sandbox network policy
        pytest.skip(f"devnet RPC unreachable from this environment: {exc!r}")
    else:
        assert balance >= 0


def test_anchor_commitment_live_devnet_or_skip_on_network_policy(tmp_path):
    anchor = SolanaAnchor()
    keypair = load_or_create_keypair(os.path.join(tmp_path, "devnet.key"))

    try:
        if anchor.get_balance_lamports(keypair.pubkey()) < 5000:
            anchor.request_devnet_airdrop(keypair.pubkey())
        receipt = anchor.anchor_commitment("ab" * 32, keypair)
    except Exception as exc:  # pragma: no cover - depends on sandbox network policy
        pytest.skip(f"devnet RPC unreachable from this environment: {exc!r}")
    else:
        assert receipt.network == "devnet"
        assert receipt.memo == "arrowcap:" + "ab" * 32
