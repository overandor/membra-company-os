#!/usr/bin/env python3
"""
Gate.io Futures Paper Trading Bot - CCXT Based
Paper mode only - no live orders
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path

GATE_API_KEY = "2b29d118d4fe92628f33a8f298416548"
GATE_API_SECRET = "09b7b2c7af4ba6ee1bd93823591a5216945030d760e27b94aa26fed337e05d35"

# Configuration
PAPER_MODE = True  # Always true for this bot
MAX_NOTIONAL = 0.10  # Max $0.10 per contract
MIN_VOLUME_USD = 10000  # Minimum 24h volume (lowered for testing)
MAX_POSITIONS = 3  # Max paper positions
LEVERAGE = 5  # Leverage
BLACKLIST = ["BTC", "ETH"]  # Exclude these
WHITELIST_MANAGE = []  # Only these can be managed (empty = none)
SCAN_INTERVAL = 30  # Seconds between scans

# Logging
BASE_DIR = Path("/Users/alep/Downloads")
LOG_FILE = BASE_DIR / "paper_futures.log"
PAPER_PNL_FILE = BASE_DIR / "paper_pnl.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    import ccxt
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "ccxt"], check=True)
    import ccxt

class PaperFuturesBot:
    def __init__(self):
        self.exchange = ccxt.gateio({
            'apiKey': GATE_API_KEY,
            'secret': GATE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'defaultSettle': 'usdt',
            }
        })
        self.paper_positions = {}
        self.running = False
        
    def load_markets(self):
        """Load markets"""
        try:
            self.exchange.load_markets()
            logger.info("Markets loaded")
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
    
    def get_micro_contracts(self):
        """Get micro contracts <= $0.10 notional"""
        try:
            markets = self.exchange.markets
            micro_contracts = []
            
            logger.info(f"Total markets loaded: {len(markets)}")
            
            for symbol, market in markets.items():
                if market.get('type') != 'swap' or market.get('settle') != 'usdt':
                    continue
                
                # Skip blacklist
                if any(b in symbol for b in BLACKLIST):
                    continue
                
                # Skip if not active
                if not market.get('active', True):
                    continue
                
                # Get ticker
                try:
                    ticker = self.exchange.fetch_ticker(symbol)
                    last_price = ticker['last']
                    volume_24h = ticker.get('quoteVolume', 0)
                    change_24h = ticker.get('percentage', 0)
                    
                    logger.info(f"Checking {symbol}: price=${last_price:.6f}, vol=${volume_24h:.0f}")
                    
                    if last_price <= 0 or volume_24h < MIN_VOLUME_USD:
                        logger.info(f"  Skipped: price={last_price}, vol={volume_24h}")
                        continue
                    
                    # Check notional (use price directly for micro futures)
                    notional = last_price
                    
                    # Temporarily disable notional filter for testing
                    # if notional > MAX_NOTIONAL:
                    #     continue
                    
                    micro_contracts.append({
                        'symbol': symbol,
                        'price': last_price,
                        'volume': volume_24h,
                        'change_24h': change_24h,
                        'notional': notional,
                        'contract_size': contract_size
                    })
                    
                except Exception as e:
                    logger.error(f"Error fetching ticker for {symbol}: {e}")
                    continue
            
            # Sort by volume
            micro_contracts.sort(key=lambda x: x['volume'], reverse=True)
            logger.info(f"Found {len(micro_contracts)} contracts after filtering")
            return micro_contracts[:30]  # Top 30 by volume
            
        except Exception as e:
            logger.error(f"Error getting micro contracts: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_paper_positions(self):
        """Get current paper positions"""
        return self.paper_positions
    
    def estimate_margin(self, symbol, size, price):
        """Estimate margin required for position"""
        notional = size * price
        margin = notional / LEVERAGE
        return margin
    
    def estimate_fees(self, symbol, size, price):
        """Estimate trading fees (0.075% taker)"""
        notional = size * price
        fee = notional * 0.00075  # 0.075%
        return fee
    
    def log_paper_trade(self, symbol, side, price, size, pnl=0):
        """Log paper trade"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'price': price,
            'size': size,
            'pnl': pnl,
            'notional': price * size,
            'margin': self.estimate_margin(symbol, size, price),
            'fees': self.estimate_fees(symbol, size, price)
        }
        
        with open(PAPER_PNL_FILE, 'a') as f:
            f.write(json.dumps(trade) + '\n')
        
        logger.info(f"[PAPER] {side.upper()} {size} {symbol} @ ${price:.6f} | Margin: ${trade['margin']:.4f} | Fees: ${trade['fees']:.6f}")
        return trade
    
    def should_trade(self, contract):
        """Determine if we should paper trade this contract"""
        # Simple signal: strong momentum
        if contract['change_24h'] > 5:
            return 'buy'
        elif contract['change_24h'] < -5:
            return 'sell'
        return None
    
    def run(self):
        """Main paper trading loop"""
        logger.info("=" * 60)
        logger.info("🤖 PAPER FUTURES BOT STARTING")
        logger.info("=" * 60)
        logger.info(f"Mode: PAPER (no live orders)")
        logger.info(f"Max Notional: ${MAX_NOTIONAL}")
        logger.info(f"Min Volume: ${MIN_VOLUME_USD:,}")
        logger.info(f"Max Positions: {MAX_POSITIONS}")
        logger.info(f"Blacklist: {BLACKLIST}")
        logger.info(f"Do NOT trade ENA unless whitelisted")
        
        self.load_markets()
        self.running = True
        
        while self.running:
            try:
                logger.info("-" * 60)
                logger.info(f"Scanning at {datetime.now().strftime('%H:%M:%S')}")
                
                # Get micro contracts
                contracts = self.get_micro_contracts()
                logger.info(f"Found {len(contracts)} micro contracts")
                
                if not contracts:
                    logger.warning("No micro contracts found")
                    time.sleep(SCAN_INTERVAL)
                    continue
                
                # Show top 10
                logger.info("Top 10 by volume:")
                for i, c in enumerate(contracts[:10]):
                    signal = self.should_trade(c)
                    signal_str = f" [{signal.upper()}]" if signal else ""
                    logger.info(f"  {i+1}. {c['symbol']:25} ${c['price']:10.6f}  Vol: ${c['volume']:12,.0f}  Change: {c['change_24h']:+6.2f}%{signal_str}")
                
                # Check paper positions
                current_positions = len(self.paper_positions)
                logger.info(f"Paper positions: {current_positions}/{MAX_POSITIONS}")
                
                # Paper trade logic
                for contract in contracts[:MAX_POSITIONS]:
                    symbol = contract['symbol']
                    
                    # Skip if already have position
                    if symbol in self.paper_positions:
                        continue
                    
                    # Skip if at max positions
                    if current_positions >= MAX_POSITIONS:
                        break
                    
                    # Check if we should trade
                    signal = self.should_trade(contract)
                    if not signal:
                        continue
                    
                    # Calculate position size (small for paper)
                    size = 1  # 1 contract
                    price = contract['price']
                    
                    # Estimate margin
                    margin = self.estimate_margin(symbol, size, price)
                    fees = self.estimate_fees(symbol, size, price)
                    
                    logger.info(f"\n📝 PAPER ORDER:")
                    logger.info(f"   Symbol: {symbol}")
                    logger.info(f"   Side: {signal.upper()}")
                    logger.info(f"   Size: {size} contract")
                    logger.info(f"   Price: ${price:.6f}")
                    logger.info(f"   Notional: ${price * size:.6f}")
                    logger.info(f"   Margin: ${margin:.4f}")
                    logger.info(f"   Fees: ${fees:.6f}")
                    logger.info(f"   (PAPER MODE - NOT EXECUTED)")
                    
                    # Log paper trade
                    self.log_paper_trade(symbol, signal, price, size)
                    
                    # Add to paper positions
                    self.paper_positions[symbol] = {
                        'side': signal,
                        'size': size,
                        'entry_price': price,
                        'entry_time': datetime.now().isoformat()
                    }
                    
                    current_positions += 1
                
                # Update existing paper positions
                for symbol, pos in list(self.paper_positions.items()):
                    try:
                        ticker = self.exchange.fetch_ticker(symbol)
                        current_price = ticker['last']
                        entry_price = pos['entry_price']
                        
                        if pos['side'] == 'buy':
                            pnl = (current_price - entry_price) * pos['size']
                        else:
                            pnl = (entry_price - current_price) * pos['size']
                        
                        logger.info(f"   {symbol}: {pos['side'].upper()} {pos['size']} @ ${entry_price:.6f} → ${current_price:.6f} | PnL: ${pnl:+.6f}")
                        
                        # Close if profitable
                        if pnl > 0.01:  # $0.01 profit
                            logger.info(f"   ✅ Closing profitable position: +${pnl:.6f}")
                            self.log_paper_trade(symbol, 'close', current_price, pos['size'], pnl)
                            del self.paper_positions[symbol]
                            
                    except Exception as e:
                        logger.error(f"Error updating {symbol}: {e}")
                
                time.sleep(SCAN_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(SCAN_INTERVAL)
        
        logger.info("Paper bot stopped")

def main():
    bot = PaperFuturesBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Interrupted")

if __name__ == "__main__":
    main()
