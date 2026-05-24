"""
Run backtest for DepthOS.

Usage:
    python run_backtest.py --synthetic --snapshots 10000
    python run_backtest.py --csv data/shib_usdt.csv --contract SHIB_USDT
"""
import argparse
import logging
from decimal import Decimal

from app.backtest.engine import BacktestEngine
from app.core.config import ContractSpec, MICRO_CONTRACTS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)
log = logging.getLogger("backtest_cli")


def main():
    parser = argparse.ArgumentParser(description="Run DepthOS backtest")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    parser.add_argument("--csv", type=str, help="CSV file with historical data")
    parser.add_argument("--contract", type=str, help="Contract name for CSV data")
    parser.add_argument("--snapshots", type=int, default=10000, help="Number of synthetic snapshots")
    parser.add_argument("--duration", type=int, help="Duration in seconds")
    
    args = parser.parse_args()
    
    # Create backtest engine
    engine = BacktestEngine()
    
    # Load data
    if args.csv and args.contract:
        engine.load_snapshots_from_csv(args.csv, args.contract)
        contracts = [args.contract]
    else:
        contracts = MICRO_CONTRACTS[:1]  # Use first contract for synthetic
        log.info(f"Using synthetic data for {contracts[0]}")
    
    # Create contract specs
    specs = {
        contract: ContractSpec(
            name=contract,
            tick_size=Decimal("0.000001"),
            lot_size=1,
            quanto_multiplier=Decimal("0.01"),
            max_price=Decimal("0.10"),
        )
        for contract in contracts
    }
    
    # Run backtest
    metrics = engine.run_backtest(
        contracts=contracts,
        specs=specs,
        duration_seconds=args.duration,
    )
    
    # Print summary
    print(metrics.summary())


if __name__ == "__main__":
    main()
