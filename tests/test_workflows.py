"""Exercise application workflows without starting Streamlit."""

from dataclasses import replace

import pytest

from application.models import ComparisonRun, PolicyExperiment, ScheduleConfig
from application.sample_data import load_sample
from application.validation import validate_schedule
from application.workflows import run_comparison, run_policy_experiment, run_what_if


@pytest.mark.parametrize("name,status", [("Basic", "OPTIMAL"), ("Infeasible", "INFEASIBLE")])
def test_comparison_keeps_context_and_real_algorithm_statuses(name, status, config):
    dataset = load_sample(name)
    run = run_comparison(dataset, config)
    assert isinstance(run, ComparisonRun)
    assert run.matches(dataset, config)
    assert not run.matches(dataset, replace(config, allow_saturday=False))
    assert not run.matches(replace(dataset, classes=dataset.classes[:-1]), config)
    assert run.cp_sat.status == status
    if status == "OPTIMAL":
        assert run.greedy.complete and run.cp_sat.complete
        assert not validate_schedule(run.cp_sat.assignments, dataset.classes, dataset.rooms, config)
    else:
        assert run.greedy.status == "FAILED" and run.cp_sat.metrics is None


def test_policy_experiment_keeps_context_order_and_true_results(config):
    dataset = load_sample("Saturday trade-off")
    experiment = run_policy_experiment(dataset, config)
    assert isinstance(experiment, PolicyExperiment)
    assert experiment.matches(dataset, config, (0, 3, 10))
    assert not experiment.matches(dataset, config, (0, 1, 10))
    assert not experiment.matches(dataset, replace(config, allow_saturday=False), (0, 3, 10))
    assert [(p, r.metrics.peak_movement, r.metrics.saturday_enrollment) for p, r in experiment.results] == [(0, 100, 200), (3, 200, 0), (10, 200, 0)]
    for penalty, result in experiment.results:
        assert result.status == "OPTIMAL"
        assert not validate_schedule(result.assignments, dataset.classes, dataset.rooms, replace(config, saturday_penalty=penalty))


@pytest.mark.parametrize("penalties", [(0, 3), (0, 3, 3), (0, 3, -1), (0, 3, 1.5)])
def test_all_policies_are_validated_before_any_solver_call(monkeypatch, basic, config, penalties):
    def unexpected_solver(*args, **kwargs):
        pytest.fail("Invalid policy lists must fail before solving any scenario.")
    monkeypatch.setattr("application.workflows.solve_cp_sat", unexpected_solver)
    with pytest.raises(ValueError):
        run_what_if(basic, config, penalties)
