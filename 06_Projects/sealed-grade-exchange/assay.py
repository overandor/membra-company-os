#!/usr/bin/env python3
"""
assay.py - Sealed-Grade Exchange (SGE)

A reference mechanism that makes ANSWERS priceable by pricing a BONDED GRADE
instead of the answer itself.

THE PROBLEM (why answers don't sell themselves):
  1. Arrow's information paradox - a buyer cannot value an answer until they
     hold it, at which point they have acquired it for free.
  2. Akerlof's lemons - the seller's own claim of quality is cheap talk, so a
     quality market unravels to the bottom.
  3. Non-rivalry - an answer copies at ~zero marginal cost, so its price -> 0.

THE RESOLUTION (implemented here):
  Relocate the priced unit from the (hidden) answer to a GRADE that is
    (a) produced by a PUBLIC, CONTENT-ADDRESSED, DETERMINISTIC grader G,
    (b) claimed by the seller under a forfeitable BOND,
    (c) settled by anyone re-executing G on the revealed answer.
  - Arrow is threaded: the buyer values G's grade (visible pre-purchase),
    and never needs to see the answer's content to value it.
  - Akerlof is threaded: a false grade claim is caught by deterministic
    re-execution and the bond is slashed to the buyer, so a TRUTHFUL grade is
    the seller's dominant strategy. Cheap talk becomes costly talk.
  - Non-rivalry is handled by first sale: the answer ships encrypted; payment
    releases the key. Excludable per transaction, like any digital good.

  Trust does not vanish - it RELOCATES from an unverifiable answer onto a
  reusable, publicly auditable grader. The grader is the asset that carries
  reputation and price. "Sell the assay, not the answer."

THE BOUNDARY (stated honestly, because this is the kill criterion):
  Sound ONLY for answers whose quality is a deterministic, machine-checkable
  predicate: a preimage, a constraint solution, a held-out test pass, a route
  length. For answers with NO such grader - explanations, strategy, most prose
  (e.g. a "RAM-Clarity" writeup) - no honest grade can be bonded, so this market
  cannot form. Those revert to selling time, liability, a resolving event, or a
  standing relationship. The product opportunity is building cheap graders for
  domains that lack them, not pretending one answer can certify itself.

stdlib only. Deterministic. python3 assay.py
"""
from __future__ import annotations

import hashlib
import json
import itertools
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ----------------------------------------------------------------------------
# primitives
# ----------------------------------------------------------------------------
def canon(obj: Any) -> bytes:
    """Canonical, deterministic serialization for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def H(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def leading_zero_bits(digest: bytes) -> int:
    v = int.from_bytes(digest, "big")
    if v == 0:
        return len(digest) * 8
    return len(digest) * 8 - v.bit_length()


def stream(key: bytes, n: int) -> bytes:
    """Demo keystream. PRODUCTION: replace with AES-GCM (auth + confidentiality)."""
    out = bytearray()
    c = 0
    while len(out) < n:
        out += hashlib.sha256(key + c.to_bytes(8, "big")).digest()
        c += 1
    return bytes(out[:n])


def seal(plaintext: bytes, key: bytes) -> bytes:
    ks = stream(key, len(plaintext))
    return bytes(a ^ b for a, b in zip(plaintext, ks))


def unseal(ciphertext: bytes, key: bytes) -> bytes:
    return seal(ciphertext, key)  # XOR is symmetric


# ----------------------------------------------------------------------------
# grade + grader (the public, content-addressed assay)
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Grade:
    kind: str          # which grader produced this
    score: int         # higher is better, by construction
    required: int      # public pass bar
    passed: bool
    detail: dict = field(default_factory=dict)

    def digest(self) -> str:
        return H(canon(asdict(self)))


class Grader:
    """
    A grader is PUBLIC and CONTENT-ADDRESSED: its identity IS the hash of its
    spec, so a buyer can audit exactly how quality will be measured before
    paying. It must be deterministic and cheaper to run than to satisfy.
    """
    kind = "abstract"

    def __init__(self, spec: dict):
        self.spec = spec

    @property
    def source_hash(self) -> str:
        return H(canon({"kind": self.kind, "spec": self.spec}))

    def describe(self) -> str:
        raise NotImplementedError

    def grade(self, answer: Any) -> Grade:
        raise NotImplementedError


class PreimageGrader(Grader):
    """
    Proof-of-work style. Production cost (~2^required hashes) hugely exceeds
    verification cost (1 hash). This asymmetry is precisely the condition under
    which a market can exist: the grade is expensive to earn, trivial to check.
    Answer = a nonce string.
    """
    kind = "preimage-pow"

    def __init__(self, challenge: str, required_bits: int):
        super().__init__({"challenge": challenge, "required_bits": required_bits})

    def describe(self) -> str:
        c = self.spec["challenge"]
        r = self.spec["required_bits"]
        return (f"PreimageGrader: pass iff sha256('{c}|' + nonce) has >= {r} "
                f"leading zero bits. score = bits achieved. verify cost = 1 hash.")

    def grade(self, answer: Any) -> Grade:
        nonce = str(answer)
        d = hashlib.sha256(f"{self.spec['challenge']}|{nonce}".encode()).digest()
        bits = leading_zero_bits(d)
        req = self.spec["required_bits"]
        return Grade(self.kind, bits, req, bits >= req,
                     {"challenge": self.spec["challenge"]})


class SetCoverGrader(Grader):
    """
    Generality demo: a different deterministic predicate. Answer = list of
    chosen subset indices (<= k). score = number of universe elements covered.
    Verification = a union + count; production = combinatorial search.
    """
    kind = "set-cover"

    def __init__(self, universe: list, subsets: list, k: int, required: int):
        super().__init__({"universe": sorted(universe), "subsets": subsets,
                          "k": k, "required": required})

    def describe(self) -> str:
        s = self.spec
        return (f"SetCoverGrader: choose <= {s['k']} of {len(s['subsets'])} "
                f"subsets; pass iff >= {s['required']} of {len(s['universe'])} "
                f"elements covered. score = elements covered.")

    def grade(self, answer: Any) -> Grade:
        chosen = list(answer)
        req = self.spec["required"]
        if len(chosen) > self.spec["k"]:
            return Grade(self.kind, 0, req, False, {"reason": "too many subsets"})
        covered: set = set()
        for i in chosen:
            if 0 <= i < len(self.spec["subsets"]):
                covered |= set(self.spec["subsets"][i])
        covered &= set(self.spec["universe"])
        score = len(covered)
        return Grade(self.kind, score, req, score >= req, {"chosen": chosen})


# ----------------------------------------------------------------------------
# hash-chained receipt ledger
# ----------------------------------------------------------------------------
@dataclass
class Receipt:
    seq: int
    action: str
    payload: dict
    prev: str

    def digest(self) -> str:
        return H(canon({"seq": self.seq, "action": self.action,
                        "payload": self.payload, "prev": self.prev}))


class Ledger:
    def __init__(self):
        self.chain: list[Receipt] = []

    def append(self, action: str, payload: dict) -> Receipt:
        prev = self.chain[-1].digest() if self.chain else "0" * 64
        r = Receipt(len(self.chain), action, payload, prev)
        self.chain.append(r)
        return r

    def verify(self) -> bool:
        prev = "0" * 64
        for i, r in enumerate(self.chain):
            if r.seq != i or r.prev != prev:
                return False
            prev = r.digest()
        return True


# ----------------------------------------------------------------------------
# the exchange
# ----------------------------------------------------------------------------
@dataclass
class Offer:
    offer_id: str
    seller: str
    grader: Grader
    enc_answer: bytes        # sealed; buyer cannot read it pre-payment
    commit: str              # H(plaintext | nonce) - binds seller to ONE answer
    claimed: Grade           # the grade the seller asserts (priced unit)
    bond: int                # forfeit if the claim is false at settlement
    buyer: Optional[str] = None
    price: int = 0
    state: str = "OPEN"


class SealedGradeExchange:
    def __init__(self):
        self.ledger = Ledger()
        self.bal: dict[str, int] = {}
        self.offers: dict[str, Offer] = {}
        self.rep: dict[str, dict] = {}   # seller -> {settled, slashed}

    # --- accounting helpers
    def fund(self, who: str, amt: int):
        self.bal[who] = self.bal.get(who, 0) + amt
        self.rep.setdefault(who, {"settled": 0, "slashed": 0})

    def _move(self, frm: str, to: str, amt: int):
        self.bal[frm] -= amt
        self.bal[to] = self.bal.get(to, 0) + amt

    # --- seller lists an offer (bond is locked now)
    def list_offer(self, offer_id, seller, grader, answer, nonce, key,
                   claimed: Grade, bond, price) -> Offer:
        plaintext = canon(answer)
        commit = H(plaintext + b"|" + nonce.encode())
        enc = seal(plaintext, key)
        if self.bal.get(seller, 0) < bond:
            raise ValueError("insufficient bond capital")
        self.bal[seller] -= bond  # lock bond
        off = Offer(offer_id, seller, grader, enc, commit, claimed, bond,
                    price=price)
        self.offers[offer_id] = off
        self.rep.setdefault(seller, {"settled": 0, "slashed": 0})
        self.ledger.append("LIST", {
            "offer": offer_id, "seller": seller,
            "grader_hash": grader.source_hash, "commit": commit,
            "claimed_grade": asdict(claimed), "bond": bond, "price": price})
        return off

    # --- what a BUYER sees before paying: the grade, not the answer (Arrow)
    def inspect(self, offer_id) -> dict:
        o = self.offers[offer_id]
        return {
            "offer": o.offer_id,
            "seller": o.seller,
            "seller_reputation": dict(self.rep.get(o.seller, {})),
            "grader_kind": o.grader.kind,
            "grader_hash": o.grader.source_hash,
            "grader_semantics": o.grader.describe(),
            "claimed_score": o.claimed.score,
            "claimed_passed": o.claimed.passed,
            "pass_bar": o.claimed.required,
            "bond_at_risk": o.bond,
            "price": o.price,
            "answer_visible": False,
        }

    # --- buyer escrows payment
    def buy(self, offer_id, buyer):
        o = self.offers[offer_id]
        if o.state != "OPEN":
            raise ValueError("offer not open")
        if self.bal.get(buyer, 0) < o.price:
            raise ValueError("insufficient funds")
        self.bal[buyer] -= o.price  # escrow
        o.buyer = buyer
        o.state = "ESCROWED"
        self.ledger.append("ESCROW", {"offer": offer_id, "buyer": buyer,
                                       "amount": o.price})

    # --- seller reveals; contract re-grades deterministically and settles
    def settle(self, offer_id, answer, nonce, key) -> str:
        o = self.offers[offer_id]
        if o.state != "ESCROWED":
            raise ValueError("nothing escrowed")
        plaintext = canon(answer)

        binding_ok = H(plaintext + b"|" + nonce.encode()) == o.commit
        decrypt_ok = unseal(o.enc_answer, key) == plaintext
        regraded = o.grader.grade(answer)
        grade_ok = regraded.digest() == o.claimed.digest()

        if binding_ok and decrypt_ok and grade_ok:
            # release payment + return bond to seller; release key to buyer
            self.bal[o.seller] = self.bal.get(o.seller, 0) + o.price + o.bond
            o.state = "SETTLED"
            self.rep[o.seller]["settled"] += 1
            self.ledger.append("SETTLE", {
                "offer": offer_id, "outcome": "SETTLED",
                "verified_grade": asdict(regraded),
                "paid_to_seller": o.price, "bond_returned": o.bond,
                "key_released_to": o.buyer})
            return "SETTLED"
        else:
            # slash bond to buyer; refund escrow to buyer
            self.bal[o.buyer] = self.bal.get(o.buyer, 0) + o.price + o.bond
            o.state = "SLASHED"
            self.rep[o.seller]["slashed"] += 1
            self.ledger.append("SETTLE", {
                "offer": offer_id, "outcome": "SLASHED",
                "binding_ok": binding_ok, "decrypt_ok": decrypt_ok,
                "grade_ok": grade_ok,
                "claimed_grade": asdict(o.claimed),
                "actual_grade": asdict(regraded),
                "refund_to_buyer": o.price, "bond_to_buyer": o.bond})
            return "SLASHED"


# ----------------------------------------------------------------------------
# demo
# ----------------------------------------------------------------------------
def mine(grader: PreimageGrader, start: int = 0) -> tuple[str, Grade]:
    n = start
    req = grader.spec["required_bits"]
    while True:
        g = grader.grade(str(n))
        if g.score >= req:
            return str(n), g
        n += 1


def rule(t=""):
    print("\n" + "=" * 72)
    if t:
        print(t)
        print("=" * 72)


def show(d):
    print(json.dumps(d, indent=2, default=lambda o: asdict(o)
                     if hasattr(o, "__dataclass_fields__") else str(o)))


def main():
    ex = SealedGradeExchange()
    for who, amt in [("alice", 100), ("mallory", 100), ("eve", 100),
                     ("dave", 100), ("buyer_bob", 200)]:
        ex.fund(who, amt)

    challenge = "deliver-a-valid-pow-token-for-job-7F3A"
    grader = PreimageGrader(challenge, required_bits=16)

    rule("THE GRADER IS PUBLIC AND CONTENT-ADDRESSED (buyers audit THIS)")
    print(grader.describe())
    print("grader_hash:", grader.source_hash)

    # --- 1) HONEST seller: mines a real proof, claims the EXACT grade -------
    rule("1) HONEST SELLER (alice)")
    nonce, true_grade = mine(grader)
    key = hashlib.sha256(b"key:alice:pow-001").digest()  # demo; AES key in prod
    ex.list_offer("pow-001", "alice", grader, answer=nonce, nonce="r-alice",
                  key=key, claimed=true_grade, bond=50, price=30)
    print("alice mined nonce achieving", true_grade.score, "leading zero bits")
    print("\nBuyer bob inspects BEFORE paying (no answer revealed):")
    show(ex.inspect("pow-001"))
    ex.buy("pow-001", "buyer_bob")
    out = ex.settle("pow-001", answer=nonce, nonce="r-alice", key=key)
    print("\nsettlement:", out)
    # buyer now holds the key and independently re-verifies:
    pt = unseal(ex.offers["pow-001"].enc_answer, key)
    recovered = json.loads(pt)
    print("buyer independently re-grades recovered answer:",
          grader.grade(recovered).passed)

    # --- 2) LIAR-ABOUT-QUALITY: real proof, inflated claimed score ----------
    rule("2) SELLER LIES ABOUT THE GRADE (mallory): same nonce, claims 24 bits")
    forged = Grade(true_grade.kind, score=24, required=16, passed=True,
                   detail={"challenge": challenge})
    keym = hashlib.sha256(b"key:mallory:pow-002").digest()
    ex.list_offer("pow-002", "mallory", grader, answer=nonce, nonce="r-m",
                  key=keym, claimed=forged, bond=50, price=30)
    ex.buy("pow-002", "buyer_bob")
    out = ex.settle("pow-002", answer=nonce, nonce="r-m", key=keym)
    print("settlement:", out, "(deterministic re-grade != claimed -> bond slashed)")

    # --- 3) BAIT-AND-SWITCH: commits to X, reveals Y ------------------------
    rule("3) SELLER NEVER HELD THE ANSWER (eve): commit != revealed")
    keye = hashlib.sha256(b"key:eve:pow-003").digest()
    ex.list_offer("pow-003", "eve", grader, answer=nonce, nonce="r-eve",
                  key=keye, claimed=true_grade, bond=50, price=30)
    ex.buy("pow-003", "buyer_bob")
    out = ex.settle("pow-003", answer="a-different-nonce", nonce="r-eve",
                    key=keye)
    print("settlement:", out, "(binding check fails -> bond slashed)")

    # --- 4) GENERALITY: a different deterministic grader --------------------
    rule("4) DIFFERENT GRADER, SAME MECHANISM (dave, set-cover)")
    universe = list(range(10))
    subsets = [[0, 1, 2, 3], [3, 4, 5, 6], [6, 7, 8, 9], [2, 5, 8]]
    sc = SetCoverGrader(universe, subsets, k=3, required=10)
    print(sc.describe())
    # seller searches for a covering selection (production = combinatorial work)
    answer = next(list(c) for c in itertools.combinations(range(len(subsets)), 3)
                  if sc.grade(list(c)).passed)
    gsc = sc.grade(answer)
    keyd = hashlib.sha256(b"key:dave:sc-001").digest()
    ex.list_offer("sc-001", "dave", sc, answer=answer, nonce="r-dave",
                  key=keyd, claimed=gsc, bond=40, price=25)
    ex.buy("sc-001", "buyer_bob")
    out = ex.settle("sc-001", answer=answer, nonce="r-dave", key=keyd)
    print("chosen subsets:", answer, "covered:", gsc.score, "->", out)

    # --- ledger + balances ---------------------------------------------------
    rule("RECEIPT CHAIN (append-only, hash-linked)")
    for r in ex.ledger.chain:
        print(f"#{r.seq:<2} {r.action:<7} {r.digest()[:16]}  "
              f"{json.dumps(r.payload)[:88]}")
    print("\nchain verifies:", ex.ledger.verify())

    rule("FINAL BALANCES (honest earns, cheaters forfeit bond)")
    for who in ["alice", "mallory", "eve", "dave", "buyer_bob"]:
        print(f"  {who:<10} {ex.bal[who]:>4}   rep={ex.rep[who]}")
    print("\nstart: sellers 100, buyer 200.")
    print("alice +30 (paid) ; mallory -50, eve -50 (slashed to buyer) ; "
          "dave +25 ; bob net pays only for the proof that re-graded true.")

    rule("BOUNDARY")
    print("Sound iff a deterministic public grader exists for the answer.")
    print("No grader for 'is this a good explanation' -> no honest bond ->")
    print("no market. That class sells time / liability / a resolving event.")


if __name__ == "__main__":
    main()
