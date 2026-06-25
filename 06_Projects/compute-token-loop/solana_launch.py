#!/usr/bin/env python3
"""
solana_launch.py — turn the compute token loop into a Solana SPL launch package.

Binds the OFF-CHAIN over-collateralized reserve (supply, backing pool, reserve-ledger
hash from token_loop.py) to an ON-CHAIN SPL mint, so the token's backing is auditable:
on-chain supply  <->  off-chain underwritten reserve.  ("provenance -> collateral, on Solana.")

SAFETY (enforced, non-negotiable):
  * This GENERATES a reviewable launch recipe; it does NOT deploy. No keys, no network calls.
  * Defaults to DRY-RUN. The generated LAUNCH.sh refuses to run without an explicit devnet
    confirmation, and blocks mainnet entirely unless separately confirmed.
  * Devnet first. A mainnet launch of a real token is a financial/securities action that
    needs your keypair, legal review, and is out of scope for autonomous execution.

stdlib only. Deterministic. python3 solana_launch.py
"""
from __future__ import annotations
import hashlib, json
import token_loop as T

SPL_DECIMALS = 9                       # Solana standard (matches SOL)
PLACEHOLDER_AUTHORITY = "<YOUR_GOVERNANCE_PUBKEY>"


def _h(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def build_launch_package(nodes, epochs: int = 3, cluster: str = "devnet",
                         symbol: str = "COMP", mint_authority: str = PLACEHOLDER_AUTHORITY,
                         fix_supply: bool = True) -> dict:
    if cluster not in ("devnet", "testnet", "mainnet-beta"):
        raise ValueError("cluster must be devnet | testnet | mainnet-beta")
    loop = T.run_loop(nodes, epochs)
    final = loop["history"][-1]
    supply_ui = final["token_supply"]
    base_units = int(round(supply_ui * (10 ** SPL_DECIMALS)))

    reserve_anchor = _h({"supply_ui": supply_ui, "backing_pool_usd": final["pool_collateral_usd"],
                         "ratio": T.OCR, "epoch": final["epoch"]})
    spec = {
        "symbol": symbol, "name": "Compute-Collateral Coordination Token",
        "cluster": cluster, "decimals": SPL_DECIMALS,
        "initial_supply_ui": supply_ui, "initial_supply_base_units": base_units,
        "mint_authority": mint_authority,
        "freeze_authority": None,
        "fix_supply_after_mint": fix_supply,
        "onchain_metadata": {
            "backing_pool_usd": final["pool_collateral_usd"],
            "collateralization_ratio": T.OCR,
            "reserve_anchor_sha256": reserve_anchor,
            "peg_type": "coordination claim on verified recoverable compute state (NOT redemption-guaranteed)",
            "disclaimers": T.launch_manifest(final)["disclaimers"],
        },
    }
    return {"spec": spec, "commands": _spl_commands(spec), "dry_run": True,
            "reserve_ledger_verifies": loop["reserve_ledger_verifies"]}


def _spl_commands(spec: dict) -> list[str]:
    """The exact spl-token CLI recipe (NOT executed). Review, then run on devnet."""
    sym, dec = spec["symbol"], spec["decimals"]
    cmds = [
        f"solana config set --url https://api.{spec['cluster']}.solana.com",
        "solana-keygen new --no-bip39-passphrase -o ./mint-authority.json   # or use your governance key",
        f"spl-token create-token --decimals {dec} ./mint-keypair.json        # -> TOKEN_MINT",
        "spl-token create-account $TOKEN_MINT                                 # treasury ATA",
        f"spl-token mint $TOKEN_MINT {spec['initial_supply_ui']}              # mint reserve-matched supply",
    ]
    if spec["fix_supply_after_mint"]:
        cmds.append("spl-token authorize $TOKEN_MINT mint --disable          # fix supply (no further mint)")
    cmds.append(
        "# metadata: attach name/symbol + backing via Metaplex Token Metadata; "
        "store reserve_anchor_sha256 in the off-chain JSON the metadata `uri` points to.")
    return cmds


def render_launch_sh(pkg: dict) -> str:
    s = pkg["spec"]
    lines = ["#!/usr/bin/env bash", "set -euo pipefail",
             "# AUTO-GENERATED launch recipe — review before running. Defaults to DRY-RUN.",
             f"# token={s['symbol']} cluster={s['cluster']} supply={s['initial_supply_ui']} "
             f"decimals={s['decimals']} ratio={s['onchain_metadata']['collateralization_ratio']}",
             'CONFIRM="${LAUNCH_CONFIRM:-}"',
             'if [ "$CONFIRM" != "I_UNDERSTAND_DEVNET" ]; then',
             '  echo "DRY RUN. Set LAUNCH_CONFIRM=I_UNDERSTAND_DEVNET to run on devnet."',
             '  printf "%s\\n" "${CMDS[@]}"; exit 0',
             'fi',
             f'if [ "{s["cluster"]}" = "mainnet-beta" ] && [ "${{MAINNET_CONFIRM:-}}" != "YES_REAL_MONEY_LEGAL_REVIEWED" ]; then',
             '  echo "REFUSING mainnet launch without MAINNET_CONFIRM=YES_REAL_MONEY_LEGAL_REVIEWED"; exit 1',
             'fi',
             "CMDS=("]
    lines += [f'  {json.dumps(c)}' for c in pkg["commands"]]
    lines += [")", 'for c in "${CMDS[@]}"; do echo "+ $c"; eval "$c"; done']
    return "\n".join(lines)


def main() -> None:
    pkg = build_launch_package(T._fleet(), epochs=3, cluster="devnet")
    s = pkg["spec"]
    print("=" * 74, "\nSOLANA SPL LAUNCH PACKAGE (dry-run; devnet-first; not deployed)\n", "=" * 74, sep="")
    print(json.dumps(s, indent=2))
    print("\nRECIPE (review, then run on devnet):")
    for c in pkg["commands"]:
        print("  $", c)
    print(f"\nreserve ledger verifies: {pkg['reserve_ledger_verifies']}  | dry_run: {pkg['dry_run']}")
    print("\nBoundary: this is the reviewable launch recipe, not a deployment. Mint supply is "
          "reserve-matched; backing stays the off-chain over-collateralized underwritten pool.")
    print("Devnet first. Mainnet = your keys + legal review; never autonomous.")


if __name__ == "__main__":
    main()
