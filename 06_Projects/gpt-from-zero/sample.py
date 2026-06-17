#!/usr/bin/env python3
"""Generate text from a saved GPT checkpoint.

Usage:
    python sample.py --checkpoint gpt_model.pt --prompt "Hello"
"""

from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(__file__))

from gpt.generate import generate  # noqa: E402
from gpt.model import GPT  # noqa: E402
from gpt.tokenizer import CharTokenizer  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample from trained GPT")
    parser.add_argument("--checkpoint", type=str, default="gpt_model.pt")
    parser.add_argument("--prompt", type=str, default="The ")
    parser.add_argument("--max_tokens", type=int, default=500)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top_k", type=int, default=40)
    parser.add_argument("--top_p", type=float, default=0.9)
    parser.add_argument("--device", type=str,
                        default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    ckpt = torch.load(args.checkpoint, map_location=args.device,
                      weights_only=False)
    config = ckpt["config"]
    model = GPT(config)
    model.load_state_dict(ckpt["model_state"])
    model.to(args.device)
    model.eval()

    tokenizer = CharTokenizer()
    tokenizer.char_to_id = ckpt["tokenizer_chars"]
    tokenizer.id_to_char = {v: k for k, v in tokenizer.char_to_id.items()}

    seed_ids = tokenizer.encode(args.prompt)
    if not seed_ids:
        print("Prompt contains characters not in vocabulary.")
        return
    idx = torch.tensor([seed_ids], dtype=torch.long, device=args.device)

    out = generate(
        model, idx,
        max_new_tokens=args.max_tokens,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        block_size=config.block_size,
    )
    print(tokenizer.decode(out[0].tolist()))


if __name__ == "__main__":
    main()
