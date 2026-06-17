"""Unit tests for every GPT-from-zero component."""

from __future__ import annotations

import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from gpt.config import GPTConfig  # noqa: E402
from gpt.generate import generate, top_k_top_p_filter  # noqa: E402
from gpt.model import (  # noqa: E402
    CausalSelfAttention, FeedForward, GPT, TransformerBlock,
)
from gpt.tokenizer import BPETokenizer, CharTokenizer  # noqa: E402
from gpt.trainer import TextDataset, _cosine_lr  # noqa: E402


# ---- Config --------------------------------------------------------------

def test_config_validation() -> None:
    try:
        GPTConfig(n_embd=10, n_head=3)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_config_defaults() -> None:
    cfg = GPTConfig()
    assert cfg.n_embd % cfg.n_head == 0


# ---- Tokenizer -----------------------------------------------------------

def test_char_tokenizer_roundtrip() -> None:
    tok = CharTokenizer().fit("hello world")
    ids = tok.encode("hello")
    assert tok.decode(ids) == "hello"


def test_char_tokenizer_vocab_size() -> None:
    tok = CharTokenizer().fit("aabbcc")
    assert tok.vocab_size == 3


def test_bpe_tokenizer_roundtrip() -> None:
    corpus = "low low low low low lower lower newest newest widest"
    tok = BPETokenizer(num_merges=10).fit(corpus)
    ids = tok.encode("low lower")
    decoded = tok.decode(ids)
    assert decoded == "low lower"


def test_bpe_vocab_grows() -> None:
    corpus = "ab ab ab ab cd cd cd cd"
    tok0 = BPETokenizer(num_merges=0).fit(corpus)
    tok5 = BPETokenizer(num_merges=5).fit(corpus)
    assert tok5.vocab_size <= tok0.vocab_size


# ---- Model components ----------------------------------------------------

def _tiny_config() -> GPTConfig:
    return GPTConfig(
        vocab_size=32, block_size=16, n_layer=2, n_head=2, n_embd=32,
        dropout=0.0,
    )


def test_causal_attention_shape() -> None:
    cfg = _tiny_config()
    attn = CausalSelfAttention(cfg)
    x = torch.randn(2, 8, cfg.n_embd)
    y = attn(x)
    assert y.shape == (2, 8, cfg.n_embd)


def test_causal_mask_prevents_future() -> None:
    cfg = _tiny_config()
    attn = CausalSelfAttention(cfg)
    x1 = torch.randn(1, 4, cfg.n_embd)
    x2 = x1.clone()
    x2[0, 3, :] = torch.randn(cfg.n_embd)
    y1 = attn(x1)
    y2 = attn(x2)
    assert torch.allclose(y1[0, :3], y2[0, :3], atol=1e-5)


def test_feedforward_shape() -> None:
    cfg = _tiny_config()
    ff = FeedForward(cfg)
    x = torch.randn(2, 8, cfg.n_embd)
    assert ff(x).shape == x.shape


def test_transformer_block_shape() -> None:
    cfg = _tiny_config()
    block = TransformerBlock(cfg)
    x = torch.randn(2, 8, cfg.n_embd)
    assert block(x).shape == x.shape


# ---- Full model ----------------------------------------------------------

def test_gpt_forward_no_targets() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    idx = torch.randint(0, cfg.vocab_size, (2, 8))
    logits, loss = model(idx)
    assert logits.shape == (2, 8, cfg.vocab_size)
    assert loss is None


def test_gpt_forward_with_targets() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    idx = torch.randint(0, cfg.vocab_size, (2, 8))
    tgt = torch.randint(0, cfg.vocab_size, (2, 8))
    logits, loss = model(idx, tgt)
    assert logits.shape == (2, 8, cfg.vocab_size)
    assert loss is not None and loss.item() > 0


def test_gpt_weight_tying() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    assert model.token_emb.weight is model.lm_head.weight


def test_gpt_rejects_long_sequence() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    try:
        model(torch.zeros(1, cfg.block_size + 1, dtype=torch.long))
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_count_parameters() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    assert model.count_parameters() > 0


# ---- Generation ----------------------------------------------------------

def test_generate_length() -> None:
    cfg = _tiny_config()
    model = GPT(cfg)
    model.eval()
    seed = torch.randint(0, cfg.vocab_size, (1, 4))
    out = generate(model, seed, max_new_tokens=10, block_size=cfg.block_size)
    assert out.shape == (1, 14)


def test_top_k_filter() -> None:
    logits = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0])
    filtered = top_k_top_p_filter(logits, top_k=2)
    assert (filtered[:3] == float("-inf")).all()
    assert (filtered[3:] != float("-inf")).all()


def test_top_p_filter() -> None:
    logits = torch.tensor([1.0, 2.0, 3.0, 10.0])
    filtered = top_k_top_p_filter(logits, top_p=0.5)
    probs = torch.softmax(filtered, dim=-1)
    assert probs[-1] > 0.9


# ---- Trainer helpers -----------------------------------------------------

def test_cosine_lr_warmup() -> None:
    lr = _cosine_lr(0, warmup=10, decay=100, max_lr=1e-3, min_lr=1e-5)
    assert lr == 0.0
    lr_mid = _cosine_lr(5, warmup=10, decay=100, max_lr=1e-3, min_lr=1e-5)
    assert 0 < lr_mid < 1e-3


def test_cosine_lr_post_decay() -> None:
    lr = _cosine_lr(200, warmup=10, decay=100, max_lr=1e-3, min_lr=1e-5)
    assert lr == 1e-5


def test_text_dataset_batch() -> None:
    data = torch.arange(100)
    ds = TextDataset(data, block_size=8)
    x, y = ds.get_batch(4)
    assert x.shape == (4, 8)
    assert y.shape == (4, 8)
    assert (y[:, 0] == x[:, 0] + 1).all()


# ---- Entry point ---------------------------------------------------------

if __name__ == "__main__":
    test_funcs = [v for k, v in sorted(globals().items())
                  if k.startswith("test_")]
    passed = 0
    for fn in test_funcs:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
    print(f"\n{passed}/{len(test_funcs)} tests passed")
