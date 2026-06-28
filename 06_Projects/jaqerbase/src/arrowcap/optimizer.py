"""Bond-rate optimization: a genetic algorithm over a parametric pricing
function, plus a tabular Q-learning (reinforcement learning) layer that
adapts bond sizing per risk bucket from real settlement outcomes.

Both optimizers train on genuine historical AnswerClaim resolutions pulled
from the ClaimStore (collect_history below) -- reward_cents, the seller's
antonymified risk_score, the bond fraction actually charged, and whether the
oracle ultimately passed. There is no synthetic or fabricated training data:
before any claims have settled, both optimizers fall back to a documented,
clearly-labelled bootstrap default rather than inventing history.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from .claims import ClaimStore


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


@dataclass
class HistoryRecord:
    reward_cents: int
    risk_score: float
    bond_fraction_used: float
    passed: bool


def collect_history(store: ClaimStore) -> list[HistoryRecord]:
    records: list[HistoryRecord] = []
    for claim in store.list_claims():
        for answer in store.list_answers_for_claim(claim.claim_id):
            if answer.status == "settled" and answer.oracle_passed is not None:
                fraction = answer.bond_cents / claim.reward_cents if claim.reward_cents else 0.0
                records.append(
                    HistoryRecord(
                        reward_cents=claim.reward_cents,
                        risk_score=answer.antonym_profile.risk_score,
                        bond_fraction_used=fraction,
                        passed=bool(answer.oracle_passed),
                    )
                )
    return records


# ---------------------------------------------------------------------------
# Genetic algorithm
# ---------------------------------------------------------------------------


@dataclass
class BondGenome:
    base_rate: float
    risk_weight: float
    min_fraction: float = 0.02
    max_fraction: float = 0.6

    def bond_fraction(self, risk_score: float) -> float:
        raw = self.base_rate + self.risk_weight * risk_score
        return max(self.min_fraction, min(self.max_fraction, raw))

    def bond_cents(self, reward_cents: int, risk_score: float) -> int:
        return max(1, round(reward_cents * self.bond_fraction(risk_score)))

    def mutate(self, rng: random.Random, sigma: float = 0.05) -> "BondGenome":
        return BondGenome(
            base_rate=_clip01(self.base_rate + rng.gauss(0, sigma)),
            risk_weight=_clip01(self.risk_weight + rng.gauss(0, sigma)),
            min_fraction=self.min_fraction,
            max_fraction=self.max_fraction,
        )

    @staticmethod
    def random(rng: random.Random) -> "BondGenome":
        return BondGenome(base_rate=rng.uniform(0.0, 0.3), risk_weight=rng.uniform(0.0, 1.0))

    @staticmethod
    def crossover(a: "BondGenome", b: "BondGenome", rng: random.Random) -> "BondGenome":
        t = rng.random()
        return BondGenome(
            base_rate=a.base_rate * t + b.base_rate * (1 - t),
            risk_weight=a.risk_weight * t + b.risk_weight * (1 - t),
        )


DEFAULT_GENOME = BondGenome(base_rate=0.1, risk_weight=0.3)


def fitness(genome: BondGenome, records: list[HistoryRecord]) -> float:
    """Average per-claim score: charging a high bond fraction on a seller
    who ultimately passed is penalized (it taxes honest participation);
    charging a high bond fraction on a seller who ultimately failed is
    rewarded (the slashed bond is what compensates the buyer)."""
    if not records:
        return 0.0
    total = 0.0
    for r in records:
        frac = genome.bond_fraction(r.risk_score)
        total += -frac if r.passed else frac
    return total / len(records)


@dataclass
class GAResult:
    best_genome: BondGenome
    best_fitness: float
    generations_run: int
    population_size: int
    history_size: int


def _tournament_select(scored: list[tuple[float, BondGenome]], rng: random.Random, k: int = 3) -> BondGenome:
    contenders = rng.sample(scored, min(k, len(scored)))
    return max(contenders, key=lambda pair: pair[0])[1]


def evolve_bond_genome(
    records: list[HistoryRecord], *, population_size: int = 40, generations: int = 60,
    mutation_sigma: float = 0.05, elite_count: int = 4, seed: Optional[int] = None,
) -> GAResult:
    if not records:
        return GAResult(DEFAULT_GENOME, 0.0, 0, population_size, 0)

    rng = random.Random(seed)
    population = [BondGenome.random(rng) for _ in range(population_size)]
    best_genome = DEFAULT_GENOME
    best_fit = float("-inf")

    for _ in range(generations):
        scored = sorted(
            ((fitness(g, records), g) for g in population), key=lambda p: p[0], reverse=True
        )
        if scored[0][0] > best_fit:
            best_fit, best_genome = scored[0]
        next_population = [g for _, g in scored[:elite_count]]
        while len(next_population) < population_size:
            parent_a = _tournament_select(scored, rng)
            parent_b = _tournament_select(scored, rng)
            child = BondGenome.crossover(parent_a, parent_b, rng).mutate(rng, mutation_sigma)
            next_population.append(child)
        population = next_population

    return GAResult(best_genome, best_fit, generations, population_size, len(records))


# ---------------------------------------------------------------------------
# Tabular Q-learning (contextual bandit over risk buckets)
# ---------------------------------------------------------------------------

DEFAULT_ACTIONS: tuple[float, ...] = (0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5)


class BondQLearner:
    def __init__(
        self, *, bins: int = 5, actions: tuple[float, ...] = DEFAULT_ACTIONS,
        alpha: float = 0.2, epsilon: float = 0.1, seed: Optional[int] = None,
    ):
        self.bins = bins
        self.actions = actions
        self.alpha = alpha
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.q: dict[tuple[int, int], float] = {}

    def _bucket(self, risk_score: float) -> int:
        v = _clip01(risk_score)
        return min(self.bins - 1, int(v * self.bins))

    def _nearest_action(self, fraction: float) -> float:
        return min(self.actions, key=lambda a: abs(a - fraction))

    def choose_action(self, risk_score: float) -> float:
        state = self._bucket(risk_score)
        if self.rng.random() < self.epsilon:
            return self.rng.choice(self.actions)
        qs = [self.q.get((state, i), 0.0) for i in range(len(self.actions))]
        best_idx = max(range(len(self.actions)), key=lambda i: qs[i])
        return self.actions[best_idx]

    def update(self, risk_score: float, action: float, passed: bool) -> float:
        state = self._bucket(risk_score)
        action_idx = self.actions.index(self._nearest_action(action))
        reward = action if not passed else (max(self.actions) - action)
        key = (state, action_idx)
        old = self.q.get(key, 0.0)
        self.q[key] = old + self.alpha * (reward - old)
        return reward

    def train_from_history(self, records: list[HistoryRecord]) -> int:
        for r in records:
            self.update(r.risk_score, r.bond_fraction_used, r.passed)
        return len(records)

    def recommend_bond_fraction(self, risk_score: float) -> float:
        state = self._bucket(risk_score)
        qs = [self.q.get((state, i)) for i in range(len(self.actions))]
        if all(v is None for v in qs):
            return self.actions[len(self.actions) // 2]
        best_idx = max(
            range(len(self.actions)), key=lambda i: qs[i] if qs[i] is not None else float("-inf")
        )
        return self.actions[best_idx]


# ---------------------------------------------------------------------------
# Combined GA + RL optimizer
# ---------------------------------------------------------------------------


@dataclass
class BondRecommendation:
    bond_cents: int
    bond_fraction: float
    ga_fraction: float
    rl_fraction: float
    history_size: int


class BondOptimizer:
    """Blends the GA-evolved pricing genome with the RL bandit's per-bucket
    recommendation. Call retrain() after new claims settle to incorporate
    the latest outcomes; recommend() lazily retrains once if it never has."""

    def __init__(self, store: ClaimStore, *, ga_kwargs: Optional[dict] = None,
                 rl_kwargs: Optional[dict] = None):
        self.store = store
        self.ga_kwargs = ga_kwargs or {}
        self.rl_kwargs = rl_kwargs or {}
        self._ga_result: Optional[GAResult] = None
        self._rl: Optional[BondQLearner] = None

    def retrain(self) -> GAResult:
        records = collect_history(self.store)
        self._ga_result = evolve_bond_genome(records, **self.ga_kwargs)
        self._rl = BondQLearner(**self.rl_kwargs)
        self._rl.train_from_history(records)
        return self._ga_result

    def recommend(self, reward_cents: int, risk_score: float) -> BondRecommendation:
        if self._ga_result is None or self._rl is None:
            self.retrain()
        assert self._ga_result is not None and self._rl is not None
        ga_fraction = self._ga_result.best_genome.bond_fraction(risk_score)
        rl_fraction = self._rl.recommend_bond_fraction(risk_score)
        blended = (ga_fraction + rl_fraction) / 2
        return BondRecommendation(
            bond_cents=max(1, round(reward_cents * blended)),
            bond_fraction=blended,
            ga_fraction=ga_fraction,
            rl_fraction=rl_fraction,
            history_size=self._ga_result.history_size,
        )
