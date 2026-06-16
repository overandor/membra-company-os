"""Autoregressive text generation with top-k / top-p (nucleus) sampling."""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


def top_k_top_p_filter(
    logits: torch.Tensor,
    top_k: int = 0,
    top_p: float = 0.0,
) -> torch.Tensor:
    """Zero-out logits outside the top-k and/or top-p nucleus.

    Args:
        logits: (vocab_size,) raw logits for the *next* token.
        top_k:  Keep only the ``top_k`` highest-probability tokens.
                0 = disabled.
        top_p:  Keep the smallest set of tokens whose cumulative probability
                exceeds ``top_p``.  0.0 = disabled.

    Returns:
        Filtered logits with excluded positions set to ``-inf``.
    """
    if top_k > 0:
        top_k = min(top_k, logits.size(-1))
        threshold = torch.topk(logits, top_k).values[..., -1]
        logits = logits.masked_fill(logits < threshold, float("-inf"))

    if top_p > 0.0:
        sorted_logits, sorted_idx = torch.sort(logits, descending=True)
        cumulative = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
        remove_mask = cumulative - F.softmax(sorted_logits, dim=-1) >= top_p
        sorted_logits[remove_mask] = float("-inf")
        logits = sorted_logits.scatter(-1, sorted_idx, sorted_logits)

    return logits


@torch.no_grad()
def generate(
    model: nn.Module,
    idx: torch.Tensor,
    max_new_tokens: int,
    temperature: float = 1.0,
    top_k: int = 0,
    top_p: float = 0.0,
    block_size: int = 128,
) -> torch.Tensor:
    """Autoregressively generate ``max_new_tokens`` token ids.

    Args:
        model:          A GPT model (or anything that returns ``(logits, _)``).
        idx:            (1, T) seed token indices.
        max_new_tokens: How many new tokens to sample.
        temperature:    Softmax temperature (< 1 = sharper, > 1 = flatter).
        top_k:          Top-k filtering (0 = off).
        top_p:          Nucleus / top-p filtering (0.0 = off).
        block_size:     Max context window the model supports.

    Returns:
        (1, T + max_new_tokens) tensor of token ids.
    """
    model.eval()
    for _ in range(max_new_tokens):
        idx_cond = idx[:, -block_size:]
        logits, _ = model(idx_cond)
        logits = logits[:, -1, :]

        if temperature != 1.0:
            logits = logits / temperature

        logits = top_k_top_p_filter(
            logits.squeeze(0), top_k=top_k, top_p=top_p,
        ).unsqueeze(0)

        probs = F.softmax(logits, dim=-1)
        next_id = torch.multinomial(probs, num_samples=1)
        idx = torch.cat([idx, next_id], dim=1)
    return idx
