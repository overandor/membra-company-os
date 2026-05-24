#!/bin/bash
# Export Gate.io API keys as environment variables

export GATE_API_KEY="YOUR_GATE_API_KEY_HERE"
export GATE_API_SECRET="YOUR_GATE_API_SECRET_HERE"

# Also add to current shell session
echo "✅ Gate.io API keys exported to environment"
echo ""
echo "To use in your current terminal:"
echo "  source /Users/alep/Downloads/export_gate_keys.sh"
echo ""
echo "Or add to your ~/.zshrc:"
echo "  echo 'export GATE_API_KEY=\"YOUR_GATE_API_KEY_HERE\"' >> ~/.zshrc"
echo "  echo 'export GATE_API_SECRET=\"YOUR_GATE_API_SECRET_HERE\"' >> ~/.zshrc"
