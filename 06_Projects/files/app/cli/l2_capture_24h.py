"""
24h Continuous L2 Data Capture for Microstructure Research

Captures L2 orderbook and trade data for 24 hours on specified contracts.
Focuses on meme perps (SHIB, PEPE, FLOKI) for toxicity analysis.
"""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import aiohttp

from app.market_data.recorder import L2Recorder

log = logging.getLogger("l2_capture_24h")


async def capture_24h(
    contracts: List[str],
    output_dir: str = "data/l2_24h",
    depth_levels: int = 20,
):
    """
    Capture L2 data for 24 hours continuously.
    
    Args:
        contracts: List of contract symbols (e.g., ["SHIB_USDT", "PEPE_USDT", "FLOKI_USDT"])
        output_dir: Output directory for recorded data
        depth_levels: Number of orderbook levels to record
    """
    print("=" * 60)
    print("24H CONTINUOUS L2 CAPTURE")
    print("=" * 60)
    print(f"Contracts: {', '.join(contracts)}")
    print(f"Output directory: {output_dir}")
    print(f"Depth levels: {depth_levels}")
    print(f"Duration: 24 hours")
    print("=" * 60)
    
    # Create output directory with timestamp
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"capture_{timestamp}"
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput path: {output_path}")
    print(f"Start time: {datetime.now(timezone.utc).isoformat()}")
    
    async with aiohttp.ClientSession() as session:
        recorder = L2Recorder(
            output_dir=output_path,
            contracts=contracts,
            depth_levels=depth_levels,
            gap_threshold=10,
        )
        
        try:
            await recorder.start(session)
            
            # Run for 24 hours
            duration_seconds = 24 * 60 * 60
            print(f"\nRecording for 24 hours ({duration_seconds} seconds)...")
            print("Press Ctrl+C to stop early")
            
            # Wait for 24 hours (or until interrupted)
            await asyncio.sleep(duration_seconds)
            
        except KeyboardInterrupt:
            print("\n\nCapture stopped by user")
        except Exception as e:
            print(f"\n\nCapture error: {e}")
            raise
        finally:
            await recorder.stop()
            print(f"\nEnd time: {datetime.now(timezone.utc).isoformat()}")
            print(f"\nData saved to: {output_path}")
            
            # Print summary
            orderbook_files = list(output_path.glob("orderbook_*.jsonl"))
            trades_files = list(output_path.glob("trades_*.jsonl"))
            unified_files = list(output_path.glob("unified_*.jsonl"))
            
            print(f"\nFiles created:")
            for f in orderbook_files:
                size = f.stat().st_size
                print(f"  {f.name}: {size:,} bytes")
            for f in trades_files:
                size = f.stat().st_size
                print(f"  {f.name}: {size:,} bytes")
            for f in unified_files:
                size = f.stat().st_size
                print(f"  {f.name}: {size:,} bytes")


async def main():
    """Main entry point for 24h L2 capture."""
    import argparse
    
    parser = argparse.ArgumentParser(description="24h Continuous L2 Capture")
    parser.add_argument(
        "--contracts",
        nargs="+",
        default=["SHIB_USDT", "PEPE_USDT", "FLOKI_USDT"],
        help="Contract symbols to capture (default: SHIB_PEPE_FLOKI)"
    )
    parser.add_argument(
        "--output-dir",
        default="data/l2_24h",
        help="Output directory for recorded data"
    )
    parser.add_argument(
        "--depth-levels",
        type=int,
        default=20,
        help="Number of orderbook levels to record"
    )
    parser.add_argument(
        "--duration-hours",
        type=int,
        default=24,
        help="Duration in hours (default: 24)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s %(name)s %(message)s",
    )
    
    await capture_24h(
        contracts=args.contracts,
        output_dir=args.output_dir,
        depth_levels=args.depth_levels,
    )


if __name__ == "__main__":
    asyncio.run(main())
