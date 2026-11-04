"""arrowcap: the Hidden Test Claim Market CLI.

    arrowcap post-claim       buyer posts a task + hidden test oracle
    arrowcap submit-preview   seller posts an antonymified preview (no disclosure)
    arrowcap post-bond        seller bonds (no oracle without a bond)
    arrowcap escrow-pay       buyer funds escrow (no full disclosure before payment)
    arrowcap reveal-answer    seller discloses; binding to the preview is checked
    arrowcap settle           runs the oracle and settles (no settlement without an oracle)
    arrowcap status           inspect a claim or answer-claim
    arrowcap optimize-bonds   retrain the GA+RL bond optimizer on settlement history
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from .antonymizer import antonymify
from .claims import ClaimStore
from .escrow import EscrowEngine, ProtocolViolation
from .fidelity import detect_broad_type
from .ledger import Ledger
from .optimizer import BondOptimizer


def _print_json(obj) -> None:
    print(json.dumps(obj, indent=2, default=str))


def _open(data_dir: str) -> tuple[Ledger, ClaimStore, EscrowEngine]:
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "ledger.db")
    ledger = Ledger(db_path)
    store = ClaimStore(db_path)
    engine = EscrowEngine(ledger, store)
    return ledger, store, engine


def _open_dex(data_dir: str):
    from .dex import DexEngine, DexStore, load_or_create_master_key

    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "ledger.db")
    ledger = Ledger(db_path)
    store = DexStore(db_path)
    master_key = load_or_create_master_key(os.path.join(data_dir, "dex_master.key"))
    engine = DexEngine(ledger, store, master_key)
    return ledger, store, engine


def cmd_post_claim(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    if args.fund_buyer_cents:
        ledger.open_account(args.buyer)
        ledger.deposit(args.buyer, args.fund_buyer_cents, memo="cli funding")
    claim = engine.post_claim(
        args.buyer, args.title, args.description, args.reward_cents, args.hidden_test_path,
    )
    _print_json(vars(claim))


def cmd_submit_preview(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    if args.fund_seller_cents:
        ledger.open_account(args.seller)
        ledger.deposit(args.seller, args.fund_seller_cents, memo="cli funding")
    with open(args.answer_file, "rb") as fh:
        content = fh.read()
    broad_type = detect_broad_type(args.answer_file)
    profile = antonymify(content, broad_type)
    answer = engine.submit_preview(args.claim_id, args.seller, profile, args.bond_cents)
    print("antonymified preview (this is all the buyer ever sees before settlement):")
    _print_json(profile.to_dict())
    print()
    _print_json(
        {
            "answer_id": answer.answer_id,
            "claim_id": answer.claim_id,
            "seller_account": answer.seller_account,
            "bond_cents": answer.bond_cents,
            "status": answer.status,
        }
    )


def cmd_post_bond(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    hold_id = engine.post_bond(args.answer_id)
    _print_json({"answer_id": args.answer_id, "bond_hold_id": hold_id})


def cmd_escrow_pay(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    hold_id = engine.fund_escrow(args.answer_id)
    _print_json({"answer_id": args.answer_id, "escrow_hold_id": hold_id})


def cmd_reveal_answer(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    with open(args.answer_file, "rb") as fh:
        content = fh.read()
    ok, mismatches = engine.reveal_answer(args.answer_id, content)
    _print_json({"answer_id": args.answer_id, "binding_ok": ok, "mismatches": mismatches})
    if not ok:
        print(
            "binding violation: the revealed answer does not match the preview's "
            "commitment. Run `settle --binding-violation` instead of `--run-oracle`.",
            file=sys.stderr,
        )


def cmd_settle(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)

    if args.binding_violation:
        outcome = engine.settle(args.answer_id, binding_violation=True)
    else:
        report = engine.run_oracle(
            args.answer_id, timeout_seconds=args.oracle_timeout_seconds,
        )
        print("oracle report:")
        _print_json(report.to_dict())
        outcome = engine.settle(args.answer_id)

    print("\nsettlement outcome:")
    _print_json(outcome.to_dict())

    if args.sign:
        from .settlement import load_or_create_signing_key, sign_settlement

        answer = store.get_answer(args.answer_id)
        key_path = os.path.join(args.data_dir, "signing.key")
        key = load_or_create_signing_key(key_path)
        receipt = sign_settlement(outcome.to_dict(), answer.commitment_sha256, key)
        receipts_dir = os.path.join(args.data_dir, "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        receipt_path = os.path.join(receipts_dir, f"{args.answer_id}.json")
        with open(receipt_path, "w") as fh:
            json.dump(receipt.to_dict(), fh, indent=2)
        print(f"\nsigned settlement receipt written to {receipt_path}:")
        _print_json(receipt.to_dict())

        if args.anchor_devnet:
            from .chain import SolanaAnchor, load_or_create_keypair

            kp_path = os.path.join(args.data_dir, "solana_devnet.key")
            keypair = load_or_create_keypair(kp_path)
            anchor = SolanaAnchor()
            try:
                if anchor.get_balance_lamports(keypair.pubkey()) < 5000:
                    anchor.request_devnet_airdrop(keypair.pubkey())
                anchored = anchor.anchor_commitment(receipt.commitment_sha256, keypair)
                print("\nanchored on Solana devnet:")
                _print_json(vars(anchored))
            except Exception as exc:  # network/RPC failures are real, not silenced
                print(f"\ndevnet anchoring failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def cmd_status(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    if args.answer_id:
        answer = store.get_answer(args.answer_id)
        _print_json(
            {
                "answer_id": answer.answer_id,
                "claim_id": answer.claim_id,
                "seller_account": answer.seller_account,
                "status": answer.status,
                "bond_cents": answer.bond_cents,
                "bond_hold_id": answer.bond_hold_id,
                "escrow_hold_id": answer.escrow_hold_id,
                "oracle_passed": answer.oracle_passed,
                "antonym_profile": answer.antonym_profile.to_dict(),
            }
        )
    elif args.claim_id:
        claim = store.get_claim(args.claim_id)
        answers = store.list_answers_for_claim(args.claim_id)
        _print_json(
            {
                "claim": vars(claim),
                "answers": [
                    {"answer_id": a.answer_id, "seller_account": a.seller_account, "status": a.status}
                    for a in answers
                ],
            }
        )
    else:
        claims = store.list_claims()
        _print_json([vars(c) for c in claims])


def cmd_dex_list(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    if args.fund_seller_cents:
        ledger.open_account(args.seller)
        ledger.deposit(args.seller, args.fund_seller_cents, memo="cli funding")
    with open(args.asset_file, "rb") as fh:
        plaintext = fh.read()
    terms = json.loads(args.terms_json) if args.terms_json else None
    listing = engine.publish_listing(
        args.seller, args.title, args.description, plaintext,
        args.asking_cents, args.bond_cents, terms,
        broad_class=args.broad_class,
        hidden_test_path=args.hidden_test_path,
        disclosure_level=args.disclosure_level,
        ttl_seconds=args.ttl_seconds,
    )
    print("listed (public pricing surface — no plaintext, no keys):")
    _print_json(listing.public_view())


def cmd_dex_browse(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    out = engine.browse(
        broad_class=args.broad_class, max_risk=args.max_risk,
        max_price_cents=args.max_price_cents,
        include_non_buyable=args.all,
    )
    _print_json({"count": len(out), "listings": out})


def cmd_dex_bond(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    hold_id = engine.post_bond(args.listing_id)
    _print_json({"listing_id": args.listing_id, "bond_hold_id": hold_id})


def cmd_dex_buy(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    if args.fund_buyer_cents:
        ledger.open_account(args.buyer)
        ledger.deposit(args.buyer, args.fund_buyer_cents, memo="cli funding")
    hold_id = engine.buy(args.listing_id, args.buyer)
    _print_json({"listing_id": args.listing_id, "buyer": args.buyer, "escrow_hold_id": hold_id})


def cmd_dex_settle(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    outcome = engine.settle(
        args.listing_id, buyer_accept=args.buyer_accept,
        oracle_timeout_seconds=args.oracle_timeout_seconds,
    )
    _print_json(outcome)

    if args.sign:
        from .settlement import load_or_create_signing_key, sign_settlement

        listing = store.get_listing(args.listing_id)
        key = load_or_create_signing_key(os.path.join(args.data_dir, "signing.key"))
        outcome_for_receipt = {**outcome, "answer_id": args.listing_id, "claim_id": args.listing_id}
        receipt = sign_settlement(outcome_for_receipt, listing.asset_commitment_sha256, key)
        receipts_dir = os.path.join(args.data_dir, "receipts")
        os.makedirs(receipts_dir, exist_ok=True)
        receipt_path = os.path.join(receipts_dir, f"{args.listing_id}.json")
        with open(receipt_path, "w") as fh:
            json.dump(receipt.to_dict(), fh, indent=2)
        print(f"\nsigned settlement receipt written to {receipt_path}:")
        _print_json(receipt.to_dict())

        if args.anchor_devnet:
            from .chain import SolanaAnchor, load_or_create_keypair

            kp = load_or_create_keypair(os.path.join(args.data_dir, "solana_devnet.key"))
            anchor = SolanaAnchor()
            try:
                if anchor.get_balance_lamports(kp.pubkey()) < 5000:
                    anchor.request_devnet_airdrop(kp.pubkey())
                anchored = anchor.anchor_commitment(listing.asset_commitment_sha256, kp)
                engine.mark_anchored(args.listing_id, anchored.signature)
                print("\nanchored on Solana devnet:")
                _print_json(vars(anchored))
            except Exception as exc:
                print(f"\ndevnet anchoring failed: {type(exc).__name__}: {exc}", file=sys.stderr)


def cmd_dex_deliver(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    import base64
    import hashlib

    from nacl.secret import SecretBox

    delivery = engine.fetch_delivery(args.listing_id, args.buyer)
    dek = base64.b64decode(delivery["dek_b64"])
    ciphertext = base64.b64decode(delivery["ciphertext_b64"])
    plaintext = SecretBox(dek).decrypt(ciphertext)
    ok = hashlib.sha256(plaintext).hexdigest() == delivery["asset_commitment_sha256"]
    result = {
        "listing_id": args.listing_id,
        "decrypted_bytes": len(plaintext),
        "commitment_verified": ok,
    }
    if args.out_file:
        with open(args.out_file, "wb") as fh:
            fh.write(plaintext)
        result["written_to"] = args.out_file
    _print_json(result)
    if not ok:
        print("delivery failed commitment verification", file=sys.stderr)
        raise SystemExit(1)


def cmd_dex_reputation(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    _print_json(engine.reputation(args.seller))


def cmd_dex_expire(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    _print_json({"swept": engine.sweep_expired()})


def cmd_dex_listing(args: argparse.Namespace) -> None:
    ledger, store, engine = _open_dex(args.data_dir)
    _print_json(store.get_listing(args.listing_id).public_view())


def cmd_optimize_bonds(args: argparse.Namespace) -> None:
    ledger, store, engine = _open(args.data_dir)
    optimizer = BondOptimizer(store)
    ga_result = optimizer.retrain()
    print("GA result:")
    _print_json(
        {
            "best_genome": vars(ga_result.best_genome),
            "best_fitness": ga_result.best_fitness,
            "generations_run": ga_result.generations_run,
            "history_size": ga_result.history_size,
        }
    )
    if args.reward_cents is not None and args.risk_score is not None:
        rec = optimizer.recommend(args.reward_cents, args.risk_score)
        print("\nrecommendation:")
        _print_json(vars(rec))
    else:
        print("\nrecommended bond fraction by risk bucket:")
        for risk in (0.0, 0.25, 0.5, 0.75, 1.0):
            rec = optimizer.recommend(args.reward_cents or 10000, risk)
            print(f"  risk={risk:.2f} -> fraction={rec.bond_fraction:.4f} bond_cents={rec.bond_cents}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="arrowcap", description=__doc__)
    parser.add_argument(
        "--data-dir", default=os.environ.get("ARROWCAP_DATA_DIR", "./.jaqerbase"),
        help="directory holding the ledger/claims SQLite file and key material",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("post-claim", help="buyer posts a task + hidden test oracle")
    p.add_argument("--buyer", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--reward-cents", type=int, required=True)
    p.add_argument("--hidden-test-path", required=True)
    p.add_argument("--fund-buyer-cents", type=int, default=0)
    p.set_defaults(func=cmd_post_claim)

    p = sub.add_parser("submit-preview", help="seller posts an antonymified preview")
    p.add_argument("--claim-id", required=True)
    p.add_argument("--seller", required=True)
    p.add_argument("--answer-file", required=True)
    p.add_argument("--bond-cents", type=int, required=True)
    p.add_argument("--fund-seller-cents", type=int, default=0)
    p.set_defaults(func=cmd_submit_preview)

    p = sub.add_parser("post-bond", help="seller posts the bond hold")
    p.add_argument("--answer-id", required=True)
    p.set_defaults(func=cmd_post_bond)

    p = sub.add_parser("escrow-pay", help="buyer funds the escrow hold")
    p.add_argument("--answer-id", required=True)
    p.set_defaults(func=cmd_escrow_pay)

    p = sub.add_parser("reveal-answer", help="seller discloses the full answer")
    p.add_argument("--answer-id", required=True)
    p.add_argument("--answer-file", required=True)
    p.set_defaults(func=cmd_reveal_answer)

    p = sub.add_parser("settle", help="run the oracle and settle the claim")
    p.add_argument("--answer-id", required=True)
    p.add_argument("--binding-violation", action="store_true")
    p.add_argument("--oracle-timeout-seconds", type=int, default=30)
    p.add_argument("--sign", action="store_true", help="produce a signed settlement receipt")
    p.add_argument(
        "--anchor-devnet", action="store_true",
        help="anchor the receipt's commitment on Solana devnet (implies --sign)",
    )
    p.set_defaults(func=cmd_settle)

    p = sub.add_parser("status", help="inspect a claim or answer-claim")
    p.add_argument("--claim-id")
    p.add_argument("--answer-id")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("optimize-bonds", help="retrain the GA+RL bond optimizer")
    p.add_argument("--reward-cents", type=int)
    p.add_argument("--risk-score", type=float)
    p.set_defaults(func=cmd_optimize_bonds)

    # ---- ArrowCAP Text Exchange (Market A: unique text asset order book) ----

    p = sub.add_parser("dex-list", help="seller lists an encrypted text asset")
    p.add_argument("--seller", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--asset-file", required=True)
    p.add_argument("--asking-cents", type=int, required=True)
    p.add_argument("--bond-cents", type=int, required=True)
    p.add_argument("--terms-json", help="license/resolution terms JSON (committed)")
    p.add_argument("--broad-class", default="text")
    p.add_argument("--hidden-test-path", help="deterministic oracle (pytest suite)")
    p.add_argument("--disclosure-level", type=int, default=5)
    p.add_argument("--ttl-seconds", type=float)
    p.add_argument("--fund-seller-cents", type=int, default=0)
    p.set_defaults(func=cmd_dex_list)

    p = sub.add_parser("dex-browse", help="search the public pricing surface")
    p.add_argument("--broad-class")
    p.add_argument("--max-risk", type=float)
    p.add_argument("--max-price-cents", type=int)
    p.add_argument("--all", action="store_true", help="include non-buyable states")
    p.set_defaults(func=cmd_dex_browse)

    p = sub.add_parser("dex-bond", help="seller posts the listing bond")
    p.add_argument("--listing-id", required=True)
    p.set_defaults(func=cmd_dex_bond)

    p = sub.add_parser("dex-buy", help="buyer funds escrow on a bonded listing")
    p.add_argument("--listing-id", required=True)
    p.add_argument("--buyer", required=True)
    p.add_argument("--fund-buyer-cents", type=int, default=0)
    p.set_defaults(func=cmd_dex_buy)

    p = sub.add_parser("dex-settle", help="run the oracle and settle the trade")
    p.add_argument("--listing-id", required=True)
    p.add_argument("--buyer-accept", action="store_true",
                   help="required when the listing's oracle is buyer_acceptance")
    p.add_argument("--oracle-timeout-seconds", type=int, default=30)
    p.add_argument("--sign", action="store_true")
    p.add_argument("--anchor-devnet", action="store_true", help="implies --sign")
    p.set_defaults(func=cmd_dex_settle)

    p = sub.add_parser("dex-deliver", help="buyer fetches the DEK and decrypts")
    p.add_argument("--listing-id", required=True)
    p.add_argument("--buyer", required=True)
    p.add_argument("--out-file")
    p.set_defaults(func=cmd_dex_deliver)

    p = sub.add_parser("dex-reputation", help="evidence-backed seller stats")
    p.add_argument("--seller", required=True)
    p.set_defaults(func=cmd_dex_reputation)

    p = sub.add_parser("dex-expire", help="sweep listings past their expiry")
    p.set_defaults(func=cmd_dex_expire)

    p = sub.add_parser("dex-listing", help="inspect one listing's public view")
    p.add_argument("--listing-id", required=True)
    p.set_defaults(func=cmd_dex_listing)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (ProtocolViolation, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
