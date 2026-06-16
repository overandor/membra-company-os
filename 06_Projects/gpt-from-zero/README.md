# GPT from Zero

A complete GPT (Generative Pre-trained Transformer) implementation built from scratch in PyTorch.
No pre-built transformer layers — every component is hand-rolled on raw `nn.Module`.

## Architecture

```
Input tokens  ──►  Token Embedding + Positional Embedding
                              │
                              ▼
                   ┌──────────────────────┐
                   │  N × Transformer Block│
                   │  ┌─ LayerNorm ──────┐ │
                   │  │ Causal Self-Attn  │ │  ◄── Multi-head, masked
                   │  └──── + residual ──┘ │
                   │  ┌─ LayerNorm ──────┐ │
                   │  │ Feed-Forward (GELU)│ │  ◄── 4× expansion
                   │  └──── + residual ──┘ │
                   └──────────────────────┘
                              │
                              ▼
                     Final LayerNorm
                              │
                              ▼
                   Linear (weight-tied)  ──►  logits
```

## What's built from scratch

| Component | File | Details |
|-----------|------|---------|
| Character tokenizer | `gpt/tokenizer.py` | Maps chars ↔ ints |
| BPE tokenizer | `gpt/tokenizer.py` | Byte-pair encoding with iterative merging |
| Multi-head causal self-attention | `gpt/model.py` | Packed QKV, causal mask, scaled dot-product |
| Feed-forward network | `gpt/model.py` | Two-layer MLP with GELU activation |
| Transformer block | `gpt/model.py` | Pre-norm (LN → Attn → LN → FFN) with residuals |
| GPT model | `gpt/model.py` | Token/pos embeddings, N blocks, weight tying |
| Cosine LR schedule | `gpt/trainer.py` | Linear warmup → cosine decay → min LR |
| Training loop | `gpt/trainer.py` | AdamW, gradient clipping, periodic eval |
| Top-k / top-p sampling | `gpt/generate.py` | Nucleus sampling for text generation |

## Quick start

```bash
cd 06_Projects/gpt-from-zero
pip install -r requirements.txt

# Train on included Shakespeare excerpts
python train.py --data data/input.txt --max_iters 2000 --device cpu

# Generate from checkpoint
python sample.py --checkpoint gpt_model.pt --prompt "To be" --max_tokens 200
```

## Configuration

All model hyper-parameters live in `GPTConfig`:

```python
GPTConfig(
    vocab_size=256,     # set automatically from tokenizer
    block_size=128,     # context window length
    n_layer=6,          # transformer blocks
    n_head=6,           # attention heads
    n_embd=384,         # embedding dimension
    dropout=0.1,        # dropout rate
    bias=False,         # use bias in linear/LN layers
)
```

## Tests

```bash
python tests/test_model.py
```

Covers: config validation, tokenizer round-trips, attention masking, shape checks,
weight tying, generation length, LR schedule, top-k/top-p filtering.

## Project structure

```
gpt-from-zero/
├── gpt/
│   ├── __init__.py       # public API
│   ├── config.py         # GPTConfig dataclass
│   ├── model.py          # CausalSelfAttention, FeedForward, TransformerBlock, GPT
│   ├── tokenizer.py      # CharTokenizer, BPETokenizer
│   ├── trainer.py        # Trainer, TrainerConfig, TextDataset, cosine LR
│   └── generate.py       # generate(), top_k_top_p_filter()
├── tests/
│   └── test_model.py     # unit tests
├── data/
│   └── input.txt         # sample Shakespeare corpus
├── train.py              # training entry point
├── sample.py             # generation entry point
├── requirements.txt      # torch>=2.0.0
└── README.md
```
