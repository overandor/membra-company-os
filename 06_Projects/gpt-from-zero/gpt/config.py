"""Model configuration."""

from dataclasses import dataclass


@dataclass
class GPTConfig:
    """All hyper-parameters for a GPT model in one place."""

    vocab_size: int = 256
    block_size: int = 128
    n_layer: int = 6
    n_head: int = 6
    n_embd: int = 384
    dropout: float = 0.1
    bias: bool = False

    def __post_init__(self) -> None:
        if self.n_embd % self.n_head != 0:
            raise ValueError(
                f"n_embd ({self.n_embd}) must be divisible by "
                f"n_head ({self.n_head})"
            )
