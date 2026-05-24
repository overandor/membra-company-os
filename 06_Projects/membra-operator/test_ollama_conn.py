"""Minimal test for Ollama connectivity in packaged environment."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from llm_bridge import LLMBridge

bridge = LLMBridge()
if bridge.connected:
    print(f"OK: Ollama connected ({bridge.model})")
    sys.exit(0)
else:
    print("FAIL: Ollama not connected")
    sys.exit(1)
