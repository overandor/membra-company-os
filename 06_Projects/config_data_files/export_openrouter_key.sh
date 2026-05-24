#!/bin/bash

# OpenRouter API Key Export Script
echo "🔑 Exporting OpenRouter API Key..."

# Export OpenRouter API key
export OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"

# Also keep Gate.io keys for trading bots
export GATE_API_KEY="YOUR_GATE_API_KEY_HERE"
export GATE_API_SECRET="YOUR_GATE_API_SECRET_HERE"

echo "✅ OpenRouter API key exported"
echo "✅ Gate.io API keys exported"
echo ""
echo "🚀 API Keys Ready:"
echo "   OpenRouter: ${OPENROUTER_API_KEY:0:20}..."
echo "   Gate.io: ${GATE_API_KEY:0:10}..."
echo ""
echo "💡 To make these permanent, add to your ~/.zshrc:"
echo "   echo 'export OPENROUTER_API_KEY=\"YOUR_OPENROUTER_API_KEY_HERE\"' >> ~/.zshrc"
echo "   echo 'export GATE_API_KEY=\"YOUR_GATE_API_KEY_HERE\"' >> ~/.zshrc"
echo "   echo 'export GATE_API_SECRET=\"YOUR_GATE_API_SECRET_HERE\"' >> ~/.zshrc"
