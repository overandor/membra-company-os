"""Tests for the Solana SPL launch package. python3 test_solana_launch.py (or pytest)."""
import token_loop as T
import solana_launch as S


def _pkg(**kw):
    return S.build_launch_package(T._fleet(), epochs=3, **kw)


def test_decimals_and_base_unit_scaling():
    p = _pkg()
    s = p["spec"]
    assert s["decimals"] == 9
    assert s["initial_supply_base_units"] == int(round(s["initial_supply_ui"] * 10 ** 9))
    assert s["cluster"] == "devnet"           # safe default


def test_supply_matches_loop_final():
    p = _pkg()
    final = T.run_loop(T._fleet(), 3)["history"][-1]
    assert p["spec"]["initial_supply_ui"] == final["token_supply"]


def test_onchain_metadata_anchors_offchain_reserve():
    m = _pkg()["spec"]["onchain_metadata"]
    assert m["collateralization_ratio"] == T.OCR
    assert len(m["reserve_anchor_sha256"]) == 64
    assert "NOT redemption-guaranteed" in m["peg_type"]
    assert m["disclaimers"]


def test_recipe_has_create_mint_and_fix_supply():
    cmds = " | ".join(_pkg()["commands"])
    assert "create-token --decimals 9" in cmds
    assert "mint $TOKEN_MINT" in cmds
    assert "authorize $TOKEN_MINT mint --disable" in cmds       # supply fixed after mint


def test_dry_run_default_and_devnet_guard():
    p = _pkg()
    assert p["dry_run"] is True
    sh = S.render_launch_sh(p)
    assert "LAUNCH_CONFIRM" in sh and "I_UNDERSTAND_DEVNET" in sh
    assert "DRY RUN" in sh


def test_mainnet_is_blocked_without_explicit_confirm():
    sh = S.render_launch_sh(_pkg(cluster="mainnet-beta"))
    assert "MAINNET_CONFIRM" in sh and "YES_REAL_MONEY_LEGAL_REVIEWED" in sh
    assert "REFUSING mainnet" in sh


def test_invalid_cluster_rejected():
    try:
        _pkg(cluster="prod")
        assert False, "should reject unknown cluster"
    except ValueError:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} tests passed")
