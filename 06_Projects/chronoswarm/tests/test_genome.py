import random

from chronoswarm.fitness import FitnessWeights, PaneSnapshot, layout_fitness
from chronoswarm.genome import (
    LayoutGenome,
    blend_crossover,
    collapse_completed,
    evolve_layout,
    expand_active,
    gaussian_mutate,
    promote_failing,
    restore_previous_layout,
    shrink_idle,
    swap,
    tournament_select,
)


def _snap(pane_id, **kwargs):
    defaults = dict(
        active=False, left=0, top=0, width=80, height=40, captured_text="", last_activity_ts=0.0
    )
    defaults.update(kwargs)
    return PaneSnapshot(pane_id=pane_id, **defaults)


def test_layout_genome_uniform_has_equal_weights():
    genome = LayoutGenome.uniform(4)
    assert genome.weights == (1.0, 1.0, 1.0, 1.0)


def test_to_widths_sums_to_total_width():
    genome = LayoutGenome(weights=(1.0, 3.0))
    widths = genome.to_widths(total_width=200, min_width=10)
    assert sum(widths) == 200


def test_to_widths_proportional_to_weights():
    genome = LayoutGenome(weights=(1.0, 3.0))
    widths = genome.to_widths(total_width=200, min_width=10)
    assert widths[1] > widths[0]


def test_to_widths_respects_min_width_floor_when_total_too_small():
    genome = LayoutGenome(weights=(1.0, 1.0, 1.0))
    widths = genome.to_widths(total_width=15, min_width=10)
    assert sum(widths) == 15
    assert all(w > 0 for w in widths)


def test_expand_active_increases_target_weight():
    genome = LayoutGenome(weights=(1.0, 1.0))
    mutated = expand_active(genome, active_index=0, factor=2.0)
    assert mutated.weights[0] == 2.0
    assert mutated.weights[1] == 1.0


def test_shrink_idle_decreases_target_weights():
    genome = LayoutGenome(weights=(1.0, 1.0, 1.0))
    mutated = shrink_idle(genome, idle_indices=[1, 2], factor=0.5)
    assert mutated.weights[0] == 1.0
    assert mutated.weights[1] == 0.5
    assert mutated.weights[2] == 0.5


def test_swap_exchanges_two_weights():
    genome = LayoutGenome(weights=(1.0, 5.0, 9.0))
    swapped = swap(genome, 0, 2)
    assert swapped.weights == (9.0, 5.0, 1.0)


def test_promote_failing_boosts_error_pane_weight():
    genome = LayoutGenome(weights=(1.0, 1.0))
    promoted = promote_failing(genome, error_indices=[1], factor=3.0)
    assert promoted.weights[1] == 3.0
    assert promoted.weights[0] == 1.0


def test_collapse_completed_floors_weight():
    genome = LayoutGenome(weights=(1.0, 9.0))
    collapsed = collapse_completed(genome, completed_indices=[1], floor=0.1)
    assert collapsed.weights[1] == 0.1


def test_restore_previous_layout_returns_previous_genome():
    current = LayoutGenome(weights=(1.0, 1.0))
    previous = LayoutGenome(weights=(5.0, 0.2))
    assert restore_previous_layout(current, previous) is previous


def test_blend_crossover_stays_within_expanded_range():
    rng = random.Random(0)
    a = LayoutGenome(weights=(1.0, 1.0))
    b = LayoutGenome(weights=(3.0, 3.0))
    for _ in range(50):
        child = blend_crossover(a, b, rng, alpha=0.5)
        assert all(w >= 0.05 for w in child.weights)


def test_gaussian_mutate_changes_at_least_one_weight():
    rng = random.Random(1)
    genome = LayoutGenome(weights=(1.0, 1.0, 1.0))
    mutated = gaussian_mutate(genome, rng, sigma=0.5)
    assert mutated.weights != genome.weights


def test_gaussian_mutate_never_goes_below_floor():
    rng = random.Random(2)
    genome = LayoutGenome(weights=(0.06, 0.06))
    for _ in range(100):
        genome = gaussian_mutate(genome, rng, sigma=2.0)
        assert all(w >= 0.05 for w in genome.weights)


def test_tournament_select_returns_a_population_member():
    rng = random.Random(3)
    population = [LayoutGenome(weights=(i,)) for i in range(1, 6)]
    fitnesses = [float(i) for i in range(1, 6)]
    winner = tournament_select(population, fitnesses, rng, k=5)
    assert winner in population


def test_evolve_layout_zero_panes_returns_empty_genome():
    result = evolve_layout([], FitnessWeights(), now=0.0, total_width=200)
    assert result.weights == ()


def test_evolve_layout_single_pane_returns_uniform():
    result = evolve_layout([_snap("%0")], FitnessWeights(), now=0.0, total_width=200)
    assert result.weights == (1.0,)


def test_evolve_layout_improves_fitness_over_uniform_start():
    now = 1000.0
    base = [
        _snap("%0", active=True, width=100, height=40, last_activity_ts=now),
        _snap(
            "%1",
            active=False,
            width=100,
            height=40,
            captured_text="Traceback (most recent call last):\n",
            last_activity_ts=now,
        ),
    ]
    weights = FitnessWeights()
    uniform_score = layout_fitness(base, weights, now=now)

    best = evolve_layout(
        base, weights, now=now, total_width=200, generations=25, population_size=20, seed=42
    )
    from dataclasses import replace

    bred = [replace(s, width=w) for s, w in zip(base, best.to_widths(200))]
    bred_score = layout_fitness(bred, weights, now=now)

    assert bred_score >= uniform_score


def test_evolve_layout_is_deterministic_with_same_seed():
    now = 500.0
    base = [
        _snap("%0", active=True, width=100, height=40, last_activity_ts=now),
        _snap("%1", active=False, width=100, height=40, last_activity_ts=0.0),
    ]
    weights = FitnessWeights()
    a = evolve_layout(base, weights, now=now, total_width=200, generations=10, population_size=12, seed=99)
    b = evolve_layout(base, weights, now=now, total_width=200, generations=10, population_size=12, seed=99)
    assert a.weights == b.weights
