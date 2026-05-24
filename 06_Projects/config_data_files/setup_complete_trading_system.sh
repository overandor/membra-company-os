#!/bin/bash

# Complete Trading System Setup
# Gate.io + OpenRouter AI Trading Supervisor

echo "🚀 SETTING UP COMPLETE TRADING SYSTEM"
echo "======================================"

# Export all API keys
echo "🔑 Setting up API keys..."

# OpenRouter API Key
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"

# Gate.io API Keys (demo keys - replace with real ones for live trading)
export GATE_API_KEY="YOUR_GATE_API_KEY_HERE"
export GATE_API_SECRET="YOUR_GATE_API_SECRET_HERE"

echo "✅ API keys exported"
echo ""

# Test API connections
echo "🧪 Testing API connections..."

# Test OpenRouter
echo "Testing OpenRouter API..."
python3 -c "
import requests, os, json
key = os.getenv('OPENROUTER_API_KEY')
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
data = {'model': 'anthropic/claude-3-haiku', 'messages': [{'role': 'user', 'content': 'Say OK'}], 'max_tokens': 10}
try:
    r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=data, timeout=5)
    print(f'OpenRouter: ✅ {r.status_code}' if r.status_code == 200 else f'OpenRouter: ❌ {r.status_code}')
except:
    print('OpenRouter: ❌ Connection failed')
"

# Test Gate.io public endpoint
echo "Testing Gate.io API..."
python3 -c "
import requests
try:
    r = requests.get('https://api.gateio.ws/api/v4/futures/usdt/contracts', timeout=5)
    print(f'Gate.io Public: ✅ {r.status_code}' if r.status_code == 200 else f'Gate.io Public: ❌ {r.status_code}')
except:
    print('Gate.io Public: ❌ Connection failed')
"

echo ""
echo "📊 AVAILABLE TRADING SYSTEMS:"
echo ""

echo "1️⃣ Gate.io Market Maker (Demo - works without API keys):"
echo "   python3 gate_working_demo.py"
echo ""

echo "2️⃣ OpenRouter AI Trading Supervisor:"
echo "   python3 openrouter_ai_trader.py"
echo ""

echo "3️⃣ Original Gate.io Scripts (need real API keys):"
echo "   python3 gate.spread.py --dry"
echo "   python3 gateio_alpha_trader.py"
echo ""

echo "🔧 PERMANENT SETUP:"
echo "Add these lines to ~/.zshrc for permanent setup:"
echo ""
echo "# Trading System API Keys"
echo "export OPENROUTER_API_KEY=\"YOUR_OPENROUTER_API_KEY_HERE\""
echo "export GATE_API_KEY=\"YOUR_GATE_API_KEY_HERE\""
echo "export GATE_API_SECRET=\"YOUR_GATE_API_SECRET_HERE\""
echo ""

echo "⚠️  IMPORTANT NOTES:"
echo "- Gate.io keys are DEMO keys - get real ones for live trading"
echo "- OpenRouter key is working and ready for AI decisions"
echo "- All scripts run in dry/simulation mode by default"
echo "- AI trader uses Claude Haiku (fast, cheap: \$0.25/1M tokens)"
echo ""

echo "🚀 READY TO START TRADING!"
echo "Choose a system from the list above and run it."
