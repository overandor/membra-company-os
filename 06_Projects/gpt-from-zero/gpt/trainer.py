"""Training loop with AdamW, cosine LR schedule, and gradient clipping."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import List, Optional

import torch
import torch.nn as nn


@dataclass
class TrainerConfig:
    """Training hyper-parameters."""

    max_iters: int = 5000
    batch_size: int = 64
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    grad_clip: float = 1.0
    warmup_iters: int = 100
    lr_decay_iters: int = 5000
    min_lr: float = 1e-5
    eval_interval: int = 250
    eval_iters: int = 20
    device: str = "cpu"
    log_interval: int = 50


class TextDataset:
    """Streams random chunks of token-id sequences for language modelling."""

    def __init__(
        self,
        data: torch.Tensor,
        block_size: int,
    ) -> None:
        self.data = data
        self.block_size = block_size

    def get_batch(
        self,
        batch_size: int,
        device: str = "cpu",
    ) -> tuple[torch.Tensor, torch.Tensor]:
        ix = torch.randint(
            len(self.data) - self.block_size - 1, (batch_size,)
        )
        x = torch.stack([self.data[i: i + self.block_size] for i in ix])
        y = torch.stack(
            [self.data[i + 1: i + self.block_size + 1] for i in ix]
        )
        return x.to(device), y.to(device)


def _cosine_lr(
    it: int,
    warmup: int,
    decay: int,
    max_lr: float,
    min_lr: float,
) -> float:
    if it < warmup:
        return max_lr * it / warmup
    if it > decay:
        return min_lr
    ratio = (it - warmup) / (decay - warmup)
    coeff = 0.5 * (1.0 + math.cos(math.pi * ratio))
    return min_lr + coeff * (max_lr - min_lr)


class Trainer:
    """Minimal training loop for a GPT model."""

    def __init__(
        self,
        model: nn.Module,
        train_dataset: TextDataset,
        config: TrainerConfig,
        val_dataset: Optional[TextDataset] = None,
    ) -> None:
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.config = config
        self.losses: List[float] = []

    @torch.no_grad()
    def _estimate_loss(self) -> dict[str, float]:
        self.model.eval()
        out: dict[str, float] = {}
        datasets = {"train": self.train_dataset}
        if self.val_dataset is not None:
            datasets["val"] = self.val_dataset
        for split, ds in datasets.items():
            total = 0.0
            for _ in range(self.config.eval_iters):
                xb, yb = ds.get_batch(
                    self.config.batch_size, self.config.device
                )
                _, loss = self.model(xb, yb)
                total += loss.item()
            out[split] = total / self.config.eval_iters
        self.model.train()
        return out

    def run(self) -> List[float]:
        cfg = self.config
        device = cfg.device
        self.model.to(device)
        self.model.train()

        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=cfg.learning_rate,
            betas=(cfg.beta1, cfg.beta2),
            weight_decay=cfg.weight_decay,
        )

        t0 = time.time()
        for it in range(cfg.max_iters):
            lr = _cosine_lr(
                it, cfg.warmup_iters, cfg.lr_decay_iters,
                cfg.learning_rate, cfg.min_lr,
            )
            for pg in optimizer.param_groups:
                pg["lr"] = lr

            xb, yb = self.train_dataset.get_batch(cfg.batch_size, device)
            _, loss = self.model(xb, yb)

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            if cfg.grad_clip > 0:
                nn.utils.clip_grad_norm_(
                    self.model.parameters(), cfg.grad_clip
                )
            optimizer.step()

            self.losses.append(loss.item())

            if it % cfg.log_interval == 0:
                dt = time.time() - t0
                print(
                    f"iter {it:5d} | loss {loss.item():.4f} | "
                    f"lr {lr:.2e} | {dt:.1f}s"
                )
                t0 = time.time()

            if it % cfg.eval_interval == 0 and it > 0:
                losses = self._estimate_loss()
                parts = " | ".join(
                    f"{k} {v:.4f}" for k, v in sorted(losses.items())
                )
                print(f"  eval @ {it}: {parts}")

        return self.losses
