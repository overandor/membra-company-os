#!/usr/bin/env python3
"""
ENA_USDT HEDGING CONFIGURATION
Configuration settings for ENA/USDT hedging strategy
"""

class ENAHedgingConfig:
    """Configuration for ENA_USDT Hedging Strategy"""
    
    def __init__(self):
        # ===========================================
        # API CONFIGURATION - YOUR KEYS ARE SECURELY STORED HERE
        # ===========================================
        self.api_key = os.environ.get("GATE_API_KEY", "")
        self.api_secret = os.environ.get("GATE_API_SECRET", "")
        self.symbol = "ENA_USDT"  # Default ENA/USDT perpetual futures
        
        # ===========================================
        # MULTI-COIN SUPPORT - SUB-10-CENT TOKENS
        # ===========================================
        self.sub_10_cent_coins = [
            "ENA_USDT",      # Ethena (primary target)
            "PEPE_USDT",     # Pepe
            "SHIB_USDT",     # Shiba Inu
            "DOGE_USDT",     # Dogecoin
            "FLOKI_USDT",    # Floki
            "BABYDOGE_USDT", # Baby Doge
            "1000SATS_USDT", # 1000SATS
            "BONK_USDT",     # Bonk
            "WIF_USDT",      # Dogwifhat
            "PEPE_USDT",     # Pepe (duplicate, will be deduped)
            "TRUMP_USDT",    # Trump
            "MAGA_USDT",     # MAGA
            "BOME_USDT",     # Book of Meme
            "SLERF_USDT",    # Slerf
            "MOG_USDT",      # Mog
            "GME_USDT",      # GameStop
            "AMC_USDT",      # AMC
            "BB_USDT",       # BlackBerry
            "FET_USDT",      # Fetch.ai
            "OCEAN_USDT",    # Ocean Protocol
        ]
        
        # Remove duplicates
        self.sub_10_cent_coins = list(set(self.sub_10_cent_coins))
        
        # ===========================================
        # TRADING PARAMETERS
        # ===========================================
        self.order_size_usd = 1.0  # Base order size in USD
        self.order_refresh_ms = 100  # Order refresh rate (milliseconds)
        self.max_orders_per_second = 50  # Rate limiting
        self.spread_bps = 5.0  # Base spread in basis points
        self.inventory_limit = 10.0  # Maximum position size
        
        # ===========================================
        # ULTRA-CONSERVATIVE RISK MANAGEMENT FOR $6 BALANCE
        # ===========================================
        self.max_balance_usage_percent = 5.0  # Use only 5% of balance ($0.30 max)
        self.max_order_value_usd = 0.10  # Maximum order value ($0.10 per order)
        self.max_total_exposure_usd = 0.30  # Maximum total exposure ($0.30)
        self.emergency_stop_balance_usd = 1.00  # Emergency stop if balance drops to $1
        self.min_balance_threshold_usd = 2.00  # Stop trading if balance below $2
        
        # ===========================================
        # ENA HEDGING CONFIGURATION - ULTRA SAFE SETTINGS
        # ===========================================
        self.hedging_mode = True  # Enable hedging strategy
        self.min_profit_bps = 5.0  # Higher profit requirement (5 bps = 0.05%)
        self.max_hedge_position = 5.0  # Very small max position (5 tokens max)
        self.hedge_order_size_usd = 0.05  # Tiny order size ($0.05 per hedge)
        self.hedge_price_improvement = 0.00001  # Minimal price improvement
        self.market_sell_threshold = 8.0  # Higher threshold for market selling (8 bps)
        self.max_hedge_age_seconds = 120  # Close hedges after 2 minutes max
        self.max_concurrent_hedges = 2  # Maximum 2 concurrent hedge pairs
        
        # ===========================================
        # POSITION PROTECTION SETTINGS
        # ===========================================
        self.max_position_size_percent = 3.0  # Maximum position size 3% of balance
        self.daily_loss_limit_percent = 10.0  # Stop if 10% daily loss ($0.60)
        self.max_drawdown_percent = 15.0  # Stop if 15% drawdown ($0.90)
        self.position_size_scaling = True  # Scale position size with balance
        
        # ===========================================
        # ORDER PLACEMENT SAFETY
        # ===========================================
        self.order_validation_enabled = True  # Validate all orders before placement
        self.balance_check_before_order = True  # Check balance before every order
        self.position_limit_check = True  # Check position limits before order
        self.risk_score_threshold = 0.3  # Very low risk threshold (0.3 instead of 0.8)
        self.margin_call_protection = True  # Stop trading before margin call
        
        # ===========================================
        # CASCADE AI CONFIGURATION - ULTRA CONSERVATIVE
        # ===========================================
        self.ai_confidence_threshold = 0.85  # Very high confidence required (85%)
        self.ai_risk_threshold = 0.2  # Very low risk threshold (20%)
        self.ai_opportunity_threshold = 0.5  # Higher opportunity threshold (50%)
        self.ai_analysis_interval_ms = 10000  # AI analysis every 10 seconds (slower)
        self.ai_conservative_mode = True  # Force conservative AI decisions
        self.ai_max_risk_score = 0.15  # Maximum allowed AI risk score (15%)
        
        # ===========================================
        # WEBSOCKET CONFIGURATION
        # ===========================================
        self.ws_url = "wss://fx-ws.gateio.ws/v4/ws/usdt"
        self.ws_reconnect_delay = 5  # Seconds to wait before reconnect
        self.ws_ping_interval = 20  # Ping interval in seconds
        self.ws_timeout = 10  # WebSocket timeout in seconds
        
        # ===========================================
        # LOGGING CONFIGURATION
        # ===========================================
        self.log_level = "INFO"  # DEBUG, INFO, WARNING, ERROR
        self.log_to_file = True  # Enable file logging
        self.log_file_path = "logs/ena_hedging.log"
        self.max_log_size_mb = 100  # Maximum log file size
        self.log_backup_count = 5  # Number of backup logs
        
        # ===========================================
        # UI CONFIGURATION
        # ===========================================
        self.ui_update_interval_ms = 50  # UI refresh rate
        self.ui_max_log_lines = 1000  # Maximum lines in UI log
        self.ui_theme = "dark"  # dark/light theme
        self.ui_window_width = 1400
        self.ui_window_height = 900
        
        # ===========================================
        # PERFORMANCE CONFIGURATION
        # ===========================================
        self.max_concurrent_orders = 10  # Maximum concurrent orders
        self.order_timeout_seconds = 30  # Order timeout
        self.price_check_interval_ms = 100  # Price update interval
        self.balance_check_interval_seconds = 30  # Balance update interval
        
        # ===========================================
        # SYMBOL-SPECIFIC SETTINGS - ULTRA CONSERVATIVE FOR $6 BALANCE
        # ===========================================
        self.symbol_settings = {
            # Ultra-conservative default settings
            "default": {
                "min_order_size": 0.001,  # Tiny minimum order size
                "price_precision": 6,
                "size_precision": 6,
                "lot_size": 0.0001,
                "min_profit_bps": 8.0,  # High profit requirement (8 bps)
                "max_position": 1.0,  # Very small max position (1 token)
                "order_size_usd": 0.02,  # Tiny order size ($0.02)
                "max_order_value_usd": 0.05,  # Max per order $0.05
                "max_concurrent_orders": 1  # Only 1 order at a time
            },
            # ENA-specific ultra-safe settings
            "ENA_USDT": {
                "min_order_size": 0.01,
                "price_precision": 6,
                "size_precision": 6,
                "lot_size": 0.001,
                "min_profit_bps": 6.0,  # Higher profit requirement (6 bps)
                "max_position": 2.0,  # Very small max position (2 ENA)
                "order_size_usd": 0.03,  # Tiny order size ($0.03)
                "max_order_value_usd": 0.08,  # Max per order $0.08
                "max_concurrent_orders": 2  # Max 2 concurrent orders
            },
            # Ultra-low price coins (extremely conservative)
            "PEPE_USDT": {
                "min_order_size": 100.0,  # Still need larger amounts for PEPE
                "price_precision": 8,
                "size_precision": 0,
                "lot_size": 10.0,
                "min_profit_bps": 12.0,  # Very high profit requirement (12 bps)
                "max_position": 1000.0,  # Small position for PEPE
                "order_size_usd": 0.02,  # Still tiny USD value
                "max_order_value_usd": 0.05,  # Max per order $0.05
                "max_concurrent_orders": 1  # Only 1 order at a time
            },
            "SHIB_USDT": {
                "min_order_size": 1000.0,
                "price_precision": 8,
                "size_precision": 0,
                "lot_size": 100.0,
                "min_profit_bps": 15.0,  # Very high profit requirement (15 bps)
                "max_position": 10000.0,  # Small position for SHIB
                "order_size_usd": 0.02,  # Still tiny USD value
                "max_order_value_usd": 0.05,  # Max per order $0.05
                "max_concurrent_orders": 1  # Only 1 order at a time
            },
            "DOGE_USDT": {
                "min_order_size": 1.0,
                "price_precision": 6,
                "size_precision": 2,
                "lot_size": 0.1,
                "min_profit_bps": 8.0,  # High profit requirement (8 bps)
                "max_position": 5.0,  # Very small position (5 DOGE)
                "order_size_usd": 0.03,  # Tiny order size ($0.03)
                "max_order_value_usd": 0.08,  # Max per order $0.08
                "max_concurrent_orders": 1  # Only 1 order at a time
            }
        }
    
    def get_symbol_settings(self, symbol):
        """Get symbol-specific settings"""
        return self.symbol_settings.get(symbol, self.symbol_settings["default"])
    
    def update_symbol_config(self, symbol):
        """Update configuration for specific symbol"""
        settings = self.get_symbol_settings(symbol)
        
        # Update config with symbol-specific settings
        self.min_profit_bps = settings["min_profit_bps"]
        self.max_hedge_position = settings["max_position"]
        self.hedge_order_size_usd = settings["order_size_usd"]
        
        return settings
        
    def validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        if not self.api_key or not self.api_secret:
            errors.append("API credentials are required")
        
        if self.min_profit_bps <= 0:
            errors.append("Minimum profit bps must be positive")
        
        if self.max_hedge_position <= 0:
            errors.append("Max hedge position must be positive")
        
        if self.hedge_order_size_usd <= 0:
            errors.append("Hedge order size must be positive")
        
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
        
        return True
    
    def get_config_summary(self):
        """Get configuration summary for logging"""
        return f"""
ENA_USDT Hedging Configuration:
- Symbol: {self.symbol}
- Min Profit: {self.min_profit_bps} bps
- Max Position: {self.max_hedge_position} ENA
- Order Size: ${self.hedge_order_size_usd}
- AI Confidence: {self.ai_confidence_threshold}
- Risk Threshold: {self.ai_risk_threshold}
        """.strip()

# Development/Testing configuration
class ENAHedgingConfigDev(ENAHedgingConfig):
    """Development configuration with safer settings"""
    
    def __init__(self):
        super().__init__()
        
        # Safer trading parameters for development
        self.hedge_order_size_usd = 1.0  # Smaller order size
        self.max_hedge_position = 10.0  # Smaller max position
        self.min_profit_bps = 2.0  # Higher profit requirement
        self.ai_confidence_threshold = 0.8  # Higher confidence requirement
        
        # Simulation mode
        self.simulation_mode = True  # Enable simulation for testing
        self.paper_trading = True  # Use paper trading

# Production configuration
class ENAHedgingConfigProd(ENAHedgingConfig):
    """Production configuration with optimal settings"""
    
    def __init__(self):
        super().__init__()
        
        # Optimized for production
        self.hedge_order_size_usd = 5.0  # Larger order size
        self.max_hedge_position = 100.0  # Larger max position
        self.min_profit_bps = 1.0  # Lower profit requirement for more opportunities
        self.ai_confidence_threshold = 0.5  # Lower confidence for more trades
        
        # Production safety
        self.simulation_mode = False
        self.paper_trading = False

if __name__ == "__main__":
    # Test configuration
    config = ENAHedgingConfig()
    config.validate_config()
    print(config.get_config_summary())
