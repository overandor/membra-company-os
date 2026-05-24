"""
CLI commands for L2 data recording and replay.
"""

import argparse
import asyncio
from pathlib import Path
from typing import List, Optional

from app.market_data.recorder import record_l2_data, L2Recorder
from app.backtest.l2_replay import L2ReplayEngine
from app.oms.oms import OMS
from app.risk.risk import RiskManager
from app.persistence.sqlite import Database
from app.analytics.performance import PerformanceAnalyzer


def record_gate_l2(
    symbols: List[str],
    duration: Optional[int] = None,
    output_dir: str = "data/l2",
    depth_levels: int = 20,
):
    """
    Record L2 data from Gate.io futures.
    
    Args:
        symbols: List of contract symbols to record
        duration: Recording duration in seconds (None: run indefinitely)
        output_dir: Directory to save recorded data
        depth_levels: Number of orderbook levels to record
    """
    print(f"Recording L2 data for: {', '.join(symbols)}")
    print(f"Output directory: {output_dir}")
    print(f"Depth levels: {depth_levels}")
    if duration:
        print(f"Duration: {duration}s")
    else:
        print("Duration: indefinite (Ctrl-C to stop)")
    
    record_l2_data(
        output_dir=Path(output_dir),
        contracts=symbols,
        duration_seconds=duration,
        depth_levels=depth_levels,
    )


def replay_l2(
    input_path: str,
    markout_intervals: List[str],
    latency_ms: int = 50,
    slippage_bps: int = 5,
    use_queue_model: bool = True,
    use_fill_probability: bool = True,
    use_toxic_detection: bool = True,
):
    """
    Replay L2 data with markout analysis.
    
    Args:
        input_path: Path to L2 JSONL file or directory
        markout_intervals: Markout intervals (e.g., "100ms", "1s", "5s")
        latency_ms: Simulated latency in milliseconds
        slippage_bps: Simulated slippage in basis points
        use_queue_model: Use queue position modeling
        use_fill_probability: Use fill probability model
        use_toxic_detection: Use toxic flow detection
    """
    print(f"Replaying L2 data from: {input_path}")
    print(f"Markout intervals: {', '.join(markout_intervals)}")
    print(f"Latency: {latency_ms}ms")
    print(f"Slippage: {slippage_bps}bps")
    print(f"Queue model: {use_queue_model}")
    print(f"Fill probability: {use_fill_probability}")
    print(f"Toxic detection: {use_toxic_detection}")
    
    async def _run():
        oms = OMS()
        risk = RiskManager()
        db = Database(":memory:")
        
        replay_engine = L2ReplayEngine(
            oms=oms,
            risk=risk,
            db=db,
            latency_ms=latency_ms,
            slippage_bps=slippage_bps,
            markout_intervals=markout_intervals,
            use_queue_model=use_queue_model,
            use_fill_probability=use_fill_probability,
            use_toxic_detection=use_toxic_detection,
        )
        
        input_path_obj = Path(input_path)
        
        if input_path_obj.is_dir():
            # Load all JSONL files in directory
            for file in input_path_obj.glob("*.jsonl"):
                if "orderbook" in file.name:
                    replay_engine.load_snapshots_from_jsonl(file)
                elif "trades" in file.name:
                    replay_engine.load_trades_from_jsonl(file)
        else:
            # Load single file
            if "orderbook" in input_path_obj.name:
                replay_engine.load_snapshots_from_jsonl(input_path_obj)
            elif "trades" in input_path_obj.name:
                replay_engine.load_trades_from_jsonl(input_path_obj)
        
        # Run replay
        contracts = oms._state.keys()
        summary = replay_engine.replay(contracts=list(contracts))
        
        print("\n" + "=" * 60)
        print("L2 REPLAY SUMMARY")
        print("=" * 60)
        for key, value in summary.items():
            if key == "markout_analysis":
                print(f"\n{key}:")
                for interval, metrics in value.items():
                    print(f"  {interval}:")
                    for metric_name, metric_value in metrics.items():
                        print(f"    {metric_name}: {metric_value}")
            elif key == "toxic_flow_analysis":
                print(f"\n{key}:")
                for metric_name, metric_value in value.items():
                    print(f"  {metric_name}: {metric_value}")
            else:
                print(f"{key}: {value}")
        print("=" * 60)
        
        # Generate performance report
        analyzer = PerformanceAnalyzer(db)
        for contract in contracts:
            print(f"\n{analyzer.generate_report(contract)}")
    
    asyncio.run(_run())


def report_metrics(
    input_path: str,
    contract: str,
):
    """
    Report metrics from replayed L2 data.
    
    Args:
        input_path: Path to database file
        contract: Contract to report on
    """
    print(f"Generating metrics report for: {contract}")
    
    db = Database(input_path)
    analyzer = PerformanceAnalyzer(db)
    
    print(analyzer.generate_report(contract))


def main():
    """CLI entry point for L2 commands."""
    parser = argparse.ArgumentParser(description="DepthOS L2 Data CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record L2 data from Gate.io")
    record_parser.add_argument(
        "--symbols",
        nargs="+",
        required=True,
        help="Contract symbols to record (e.g., SHIB_USDT PEPE_USDT)"
    )
    record_parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Recording duration in seconds (default: indefinite)"
    )
    record_parser.add_argument(
        "--output-dir",
        default="data/l2",
        help="Output directory for recorded data"
    )
    record_parser.add_argument(
        "--depth-levels",
        type=int,
        default=20,
        help="Number of orderbook levels to record"
    )
    
    # L2 replay command
    replay_parser = subparsers.add_parser("replay-l2", help="Replay L2 data")
    replay_parser.add_argument(
        "--input",
        required=True,
        help="Path to L2 JSONL file or directory"
    )
    replay_parser.add_argument(
        "--markout",
        nargs="+",
        default=["100ms", "1s", "5s"],
        help="Markout intervals (e.g., 100ms 1s 5s)"
    )
    replay_parser.add_argument(
        "--latency-ms",
        type=int,
        default=50,
        help="Simulated latency in milliseconds"
    )
    replay_parser.add_argument(
        "--slippage-bps",
        type=int,
        default=5,
        help="Simulated slippage in basis points"
    )
    replay_parser.add_argument(
        "--no-queue-model",
        action="store_true",
        help="Disable queue position modeling"
    )
    replay_parser.add_argument(
        "--no-fill-probability",
        action="store_true",
        help="Disable fill probability model"
    )
    replay_parser.add_argument(
        "--no-toxic-detection",
        action="store_true",
        help="Disable toxic flow detection"
    )
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Report metrics")
    report_parser.add_argument(
        "--input",
        required=True,
        help="Path to database file"
    )
    report_parser.add_argument(
        "--contract",
        required=True,
        help="Contract to report on"
    )
    
    args = parser.parse_args()
    
    if args.command == "record":
        record_gate_l2(
            symbols=args.symbols,
            duration=args.duration,
            output_dir=args.output_dir,
            depth_levels=args.depth_levels,
        )
    elif args.command == "replay-l2":
        replay_l2(
            input_path=args.input,
            markout_intervals=args.markout,
            latency_ms=args.latency_ms,
            slippage_bps=args.slippage_bps,
            use_queue_model=not args.no_queue_model,
            use_fill_probability=not args.no_fill_probability,
            use_toxic_detection=not args.no_toxic_detection,
        )
    elif args.command == "report":
        report_metrics(
            input_path=args.input,
            contract=args.contract,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
