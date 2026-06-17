"""Tokenizers built from scratch — character-level and byte-pair encoding."""

from __future__ import annotations

import re
from collections import Counter
from typing import Dict, List, Tuple


class CharTokenizer:
    """Simple character-level tokenizer.

    Maps each unique character in the training corpus to an integer id.
    """

    def __init__(self) -> None:
        self.char_to_id: Dict[str, int] = {}
        self.id_to_char: Dict[int, str] = {}

    @property
    def vocab_size(self) -> int:
        return len(self.char_to_id)

    def fit(self, text: str) -> "CharTokenizer":
        chars = sorted(set(text))
        self.char_to_id = {ch: i for i, ch in enumerate(chars)}
        self.id_to_char = {i: ch for ch, i in self.char_to_id.items()}
        return self

    def encode(self, text: str) -> List[int]:
        return [self.char_to_id[ch] for ch in text if ch in self.char_to_id]

    def decode(self, ids: List[int]) -> str:
        return "".join(
            self.id_to_char[i] for i in ids if i in self.id_to_char
        )


# ---------- Byte-Pair Encoding from scratch ----------


def _get_pairs(word: Tuple[str, ...]) -> Counter:
    """Count adjacent symbol pairs in a word tuple."""
    pairs: Counter = Counter()
    for i in range(len(word) - 1):
        pairs[(word[i], word[i + 1])] += 1
    return pairs


class BPETokenizer:
    """Minimal byte-pair encoding tokenizer.

    Algorithm:
      1. Start with a character-level vocabulary.
      2. Iteratively merge the most frequent adjacent pair until
         *num_merges* merges have been performed or no pair appears
         more than once.
    """

    def __init__(self, num_merges: int = 1000) -> None:
        self.num_merges = num_merges
        self.merges: List[Tuple[str, str]] = []
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self._special: Dict[str, int] = {}

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    # ---- training --------------------------------------------------------

    def fit(self, text: str) -> "BPETokenizer":
        words = re.findall(r"\S+|\s", text)
        word_freqs: Counter = Counter(words)

        splits: Dict[str, Tuple[str, ...]] = {
            w: tuple(w) for w in word_freqs
        }

        for _ in range(self.num_merges):
            pair_counts: Counter = Counter()
            for word, freq in word_freqs.items():
                pairs = _get_pairs(splits[word])
                for pair, cnt in pairs.items():
                    pair_counts[pair] += cnt * freq
            if not pair_counts:
                break
            best = pair_counts.most_common(1)[0]
            if best[1] < 2:
                break
            pair = best[0]
            self.merges.append(pair)
            merged = pair[0] + pair[1]
            new_splits: Dict[str, Tuple[str, ...]] = {}
            for word, syms in splits.items():
                new_syms: List[str] = []
                i = 0
                while i < len(syms):
                    if (
                        i < len(syms) - 1
                        and syms[i] == pair[0]
                        and syms[i + 1] == pair[1]
                    ):
                        new_syms.append(merged)
                        i += 2
                    else:
                        new_syms.append(syms[i])
                        i += 1
                new_splits[word] = tuple(new_syms)
            splits = new_splits

        all_tokens: set = set()
        for syms in splits.values():
            all_tokens.update(syms)
        sorted_tokens = sorted(all_tokens)
        self.vocab = {tok: idx for idx, tok in enumerate(sorted_tokens)}
        self.id_to_token = {idx: tok for tok, idx in self.vocab.items()}
        return self

    # ---- encode / decode -------------------------------------------------

    def _apply_merges(self, word: Tuple[str, ...]) -> Tuple[str, ...]:
        for pair in self.merges:
            new_word: List[str] = []
            i = 0
            while i < len(word):
                if (
                    i < len(word) - 1
                    and word[i] == pair[0]
                    and word[i + 1] == pair[1]
                ):
                    new_word.append(pair[0] + pair[1])
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
        return word

    def encode(self, text: str) -> List[int]:
        words = re.findall(r"\S+|\s", text)
        ids: List[int] = []
        for w in words:
            symbols = self._apply_merges(tuple(w))
            for s in symbols:
                token_id = self.vocab.get(s)
                if token_id is not None:
                    ids.append(token_id)
        return ids

    def decode(self, ids: List[int]) -> str:
        return "".join(
            self.id_to_token[i] for i in ids if i in self.id_to_token
        )
