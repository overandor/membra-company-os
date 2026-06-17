#!/usr/bin/env python3
"""Train a GPT model on a text file.

Usage:
    python train.py --data data/input.txt
    python train.py --data data/input.txt --n_layer 4 --n_head 4 --n_embd 256
"""

from __future__ import annotations

import argparse
import os
import sys

import torch

# Allow running from the project root without installing.
sys.path.insert(0, os.path.dirname(__file__))

from gpt.config import GPTConfig  # noqa: E402
from gpt.generate import generate  # noqa: E402
from gpt.model import GPT  # noqa: E402
from gpt.tokenizer import CharTokenizer  # noqa: E402
from gpt.trainer import TextDataset, Trainer, TrainerConfig  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Train GPT from zero")
    parser.add_argument("--data", type=str, default="data/input.txt",
                        help="Path to training text file")
    parser.add_argument("--out", type=str, default="gpt_model.pt",
                        help="Path to save model checkpoint")
    parser.add_argument("--block_size", type=int, default=128)
    parser.add_argument("--n_layer", type=int, default=6)
    parser.add_argument("--n_head", type=int, default=6)
    parser.add_argument("--n_embd", type=int, default=384)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--max_iters", type=int, default=5000)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--device", type=str,
                        default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--sample_len", type=int, default=200,
                        help="Number of tokens to sample after training")
    args = parser.parse_args()

    print(f"Device: {args.device}")

    with open(args.data, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"Corpus: {len(text):,} characters")

    tokenizer = CharTokenizer().fit(text)
    print(f"Vocab size: {tokenizer.vocab_size}")

    data = torch.tensor(tokenizer.encode(text), dtype=torch.long)
    split = int(0.9 * len(data))
    train_data, val_data = data[:split], data[split:]

    model_cfg = GPTConfig(
        vocab_size=tokenizer.vocab_size,
        block_size=args.block_size,
        n_layer=args.n_layer,
        n_head=args.n_head,
        n_embd=args.n_embd,
        dropout=args.dropout,
    )
    model = GPT(model_cfg)
    print(f"Parameters: {model.count_parameters():,}")

    train_ds = TextDataset(train_data, model_cfg.block_size)
    val_ds = TextDataset(val_data, model_cfg.block_size)

    trainer_cfg = TrainerConfig(
        max_iters=args.max_iters,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        device=args.device,
    )
    trainer = Trainer(model, train_ds, trainer_cfg, val_dataset=val_ds)
    trainer.run()

    torch.save(
        {"model_state": model.state_dict(), "config": model_cfg,
         "tokenizer_chars": tokenizer.char_to_id},
        args.out,
    )
    print(f"\nModel saved to {args.out}")

    # --- sample -----------------------------------------------------------
    print("\n--- Sample ---")
    seed = text[:10]
    seed_ids = torch.tensor(
        [tokenizer.encode(seed)], dtype=torch.long, device=args.device,
    )
    out_ids = generate(
        model, seed_ids, max_new_tokens=args.sample_len,
        temperature=0.8, top_k=40, block_size=model_cfg.block_size,
    )
    print(tokenizer.decode(out_ids[0].tolist()))


if __name__ == "__main__":
    main()
