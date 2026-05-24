"""
Tests for MEMBRA L3 ProofBook
"""
import pytest
import time
from membra_l3.proof_book import ProofBook, ProofEntry, ProofType, proof_book


class TestProofBook:
    def test_append_creates_chained_entry(self):
        pb = ProofBook()
        entry = pb.append(ProofType.VOLATILITY, {"price": 1.5, "twap": 1.48})
        assert entry.proof_type == ProofType.VOLATILITY
        assert entry.prev_hash == "0" * 64
        assert len(entry.entry_hash) == 64
        assert pb.entry_count == 1

    def test_chain_integrity(self):
        pb = ProofBook()
        pb.append(ProofType.VOLATILITY, {"price": 1.0})
        pb.append(ProofType.DEVELOPMENT, {"commit": "abc123"})
        pb.append(ProofType.ZK_COMPUTE, {"proof": "zk_hash"})
        assert pb.verify_chain() is True

    def test_tampered_chain_fails(self):
        pb = ProofBook()
        pb.append(ProofType.VOLATILITY, {"price": 1.0})
        pb.append(ProofType.DEVELOPMENT, {"commit": "abc"})
        # Tamper with an entry
        pb._entries[0].data["price"] = 999.0
        assert pb.verify_chain() is False

    def test_filter_by_type(self):
        pb = ProofBook()
        pb.append(ProofType.VOLATILITY, {"price": 1.0})
        pb.append(ProofType.VOLATILITY, {"price": 1.1})
        pb.append(ProofType.DEVELOPMENT, {"commit": "abc"})

        vol_entries = pb.get_entries(ProofType.VOLATILITY)
        assert len(vol_entries) == 2

        dev_entries = pb.get_entries(ProofType.DEVELOPMENT)
        assert len(dev_entries) == 1

    def test_filter_since_timestamp(self):
        pb = ProofBook()
        pb.append(ProofType.VOLATILITY, {"price": 1.0})
        mid = time.time()
        time.sleep(0.01)
        pb.append(ProofType.VOLATILITY, {"price": 1.1})

        recent = pb.get_entries(since=mid)
        assert len(recent) == 1

    def test_export_json(self):
        pb = ProofBook()
        pb.append(ProofType.GOVERNANCE, {"action": "test"})
        exported = pb.export()
        assert len(exported) == 1
        assert exported[0]["proof_type"] == "governance_action"

    def test_singleton_works(self):
        proof_book.append(ProofType.TREASURY, {"action": "singleton_test"})
        assert proof_book.entry_count >= 1
        assert proof_book.verify_chain()
