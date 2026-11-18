"""Application workflows, usable from Streamlit, tests or a future CLI.

This module knows nothing about widgets, session state, Excel or databases.
Keep algorithm decisions inside greedy/optimizer and verify them there.
"""

from dataclasses import replace

from application.greedy import solve_greedy
from application.models import (
    ComparisonRun,
    Dataset,
    PolicyExperiment,
    ScheduleConfig,
    ScheduleResult,
)
from application.optimizer import solve_cp_sat


def run_comparison(dataset: Dataset, config: ScheduleConfig) -> ComparisonRun:
    """Run both algorithms on exactly the same input and policy."""
    greedy = solve_greedy(dataset.classes, dataset.rooms, config)
    cp_sat = solve_cp_sat(dataset.classes, dataset.rooms, config)
    return ComparisonRun(dataset, config, greedy, cp_sat)


def run_what_if(
    dataset: Dataset, config: ScheduleConfig, penalties=(0, 3, 10)
) -> list[tuple[int, ScheduleResult]]:
    """Validate every policy before starting any expensive solver call."""
    penalties = tuple(penalties)
    if len(penalties) != 3 or len(set(penalties)) != 3:
        raise ValueError("What-if yêu cầu đúng ba mức penalty khác nhau.")
    policies = [replace(config, saturday_penalty=penalty) for penalty in penalties]
    return [
        (penalty, solve_cp_sat(dataset.classes, dataset.rooms, policy))
        for penalty, policy in zip(penalties, policies)
    ]


def run_policy_experiment(
    dataset: Dataset, config: ScheduleConfig, penalties=(0, 3, 10)
) -> PolicyExperiment:
    penalties = tuple(penalties)
    return PolicyExperiment(
        dataset, config, penalties, tuple(run_what_if(dataset, config, penalties))
    )
