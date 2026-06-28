"""Genetic layout breeding.

A LayoutGenome is a weight vector, one gene per pane, that determines how
much of the tiling row's width that pane gets. `evolve_layout` breeds a
population of genomes against the real `layout_fitness` function (real
captured text, real geometry, real recency) and returns the fittest one.
The governor is responsible for actually applying the winner via tmux.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import List, Optional, Sequence

from .fitness import FitnessWeights, PaneSnapshot, layout_fitness

MIN_GENE_WEIGHT = 0.05


@dataclass(frozen=True)
class LayoutGenome:
    weights: tuple

    @staticmethod
    def uniform(n_panes: int) -> "LayoutGenome":
        return LayoutGenome(weights=tuple(1.0 for _ in range(n_panes)))

    def normalized(self) -> tuple:
        total = sum(self.weights) or 1.0
        return tuple(w / total for w in self.weights)

    def to_widths(self, total_width: int, min_width: int = 10) -> List[int]:
        fractions = self.normalized()
        n = len(fractions)
        floor_total = min_width * n
        if floor_total > total_width:
            base = total_width // n
            widths = [base] * n
            widths[-1] += total_width - base * n
            return widths
        spare = total_width - floor_total
        widths = [min_width + int(spare * f) for f in fractions]
        widths[-1] += total_width - sum(widths)
        return widths


def expand_active(genome: LayoutGenome, active_index: int, factor: float = 1.3) -> LayoutGenome:
    weights = list(genome.weights)
    weights[active_index] = max(weights[active_index] * factor, MIN_GENE_WEIGHT)
    return LayoutGenome(weights=tuple(weights))


def shrink_idle(genome: LayoutGenome, idle_indices: Sequence[int], factor: float = 0.7) -> LayoutGenome:
    weights = list(genome.weights)
    for i in idle_indices:
        weights[i] = max(weights[i] * factor, MIN_GENE_WEIGHT)
    return LayoutGenome(weights=tuple(weights))


def swap(genome: LayoutGenome, i: int, j: int) -> LayoutGenome:
    weights = list(genome.weights)
    weights[i], weights[j] = weights[j], weights[i]
    return LayoutGenome(weights=tuple(weights))


def promote_failing(genome: LayoutGenome, error_indices: Sequence[int], factor: float = 1.5) -> LayoutGenome:
    weights = list(genome.weights)
    for i in error_indices:
        weights[i] = max(weights[i] * factor, MIN_GENE_WEIGHT)
    return LayoutGenome(weights=tuple(weights))


def collapse_completed(genome: LayoutGenome, completed_indices: Sequence[int], floor: float = MIN_GENE_WEIGHT) -> LayoutGenome:
    weights = list(genome.weights)
    for i in completed_indices:
        weights[i] = floor
    return LayoutGenome(weights=tuple(weights))


def restore_previous_layout(_genome: LayoutGenome, previous: LayoutGenome) -> LayoutGenome:
    return previous


def blend_crossover(a: LayoutGenome, b: LayoutGenome, rng: random.Random, alpha: float = 0.5) -> LayoutGenome:
    child = []
    for wa, wb in zip(a.weights, b.weights):
        lo, hi = min(wa, wb), max(wa, wb)
        spread = (hi - lo) * alpha
        t = rng.uniform(lo - spread, hi + spread)
        child.append(max(t, MIN_GENE_WEIGHT))
    return LayoutGenome(weights=tuple(child))


def gaussian_mutate(genome: LayoutGenome, rng: random.Random, sigma: float = 0.15) -> LayoutGenome:
    return LayoutGenome(
        weights=tuple(max(w + rng.gauss(0, sigma * w if w else sigma), MIN_GENE_WEIGHT) for w in genome.weights)
    )


def tournament_select(
    population: List[LayoutGenome], fitnesses: List[float], rng: random.Random, k: int = 3
) -> LayoutGenome:
    indices = rng.sample(range(len(population)), min(k, len(population)))
    best_index = max(indices, key=lambda i: fitnesses[i])
    return population[best_index]


def _materialize(
    genome: LayoutGenome, base_snapshots: List[PaneSnapshot], total_width: int
) -> List[PaneSnapshot]:
    widths = genome.to_widths(total_width)
    return [replace(snap, width=w) for snap, w in zip(base_snapshots, widths)]


def evolve_layout(
    base_snapshots: List[PaneSnapshot],
    fitness_weights: FitnessWeights,
    now: float,
    total_width: int,
    generations: int = 30,
    population_size: int = 20,
    elite_count: int = 2,
    seed: Optional[int] = None,
    seed_genome: Optional[LayoutGenome] = None,
) -> LayoutGenome:
    """Breed a LayoutGenome that maximizes layout_fitness for the given real
    pane snapshots. Only `width` is varied per candidate; all other fields
    (captured text, activity, errors) come straight from the real snapshot."""
    n = len(base_snapshots)
    if n == 0:
        return LayoutGenome(weights=())
    if n == 1:
        return LayoutGenome.uniform(1)

    rng = random.Random(seed)
    population = [LayoutGenome.uniform(n)]
    if seed_genome is not None and len(seed_genome.weights) == n:
        population.append(seed_genome)
    while len(population) < population_size:
        population.append(
            LayoutGenome(weights=tuple(rng.uniform(0.2, 2.0) for _ in range(n)))
        )

    def score(genome: LayoutGenome) -> float:
        snapshots = _materialize(genome, base_snapshots, total_width)
        return layout_fitness(snapshots, fitness_weights, now)

    for _ in range(generations):
        fitnesses = [score(g) for g in population]
        ranked = sorted(zip(population, fitnesses), key=lambda pair: pair[1], reverse=True)
        population = [g for g, _ in ranked]
        fitnesses = [f for _, f in ranked]

        next_population = population[:elite_count]
        while len(next_population) < population_size:
            parent_a = tournament_select(population, fitnesses, rng)
            parent_b = tournament_select(population, fitnesses, rng)
            child = blend_crossover(parent_a, parent_b, rng)
            child = gaussian_mutate(child, rng)
            next_population.append(child)
        population = next_population

    final_fitnesses = [score(g) for g in population]
    best_index = max(range(len(population)), key=lambda i: final_fitnesses[i])
    return population[best_index]
