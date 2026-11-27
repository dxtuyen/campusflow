import random

import pytest

from application.data_io import read_dataset
from application.models import DAYS, SESSIONS, ScheduleConfig
from application.optimizer import solve_cp_sat
from application.synthetic_data import generate_synthetic_dataset, main
from application.validation import validate_inputs, validate_schedule


def test_same_seed_same_data_and_order_different_seed_can_change():
    a = generate_synthetic_dataset(seed=42)
    assert a == generate_synthetic_dataset(seed=42)
    assert a.dataset != generate_synthetic_dataset(seed=43).dataset


@pytest.mark.parametrize("difficulty", ["easy", "constrained"])
@pytest.mark.parametrize("guarantee", [True, False])
def test_counts_schema_and_sunday(difficulty, guarantee):
    result = generate_synthetic_dataset(30, 6, 77, difficulty, guarantee)
    d = result.dataset
    assert len(d.classes) == 30 and len(d.rooms) == 6
    assert not validate_inputs(d.classes, d.rooms)
    for cls in d.classes:
        assert set(cls.allowed_days) <= set(DAYS) and set(cls.allowed_sessions) <= set(
            SESSIONS
        )
    if guarantee:
        assert result.guaranteed_feasible
        assert not validate_schedule(
            result.witness, d.classes, d.rooms, ScheduleConfig()
        )
        assert solve_cp_sat(
            d.classes, d.rooms, ScheduleConfig(time_limit_seconds=2)
        ).complete
    else:
        assert not result.guaranteed_feasible and not result.witness


def test_does_not_mutate_global_random_state():
    state = random.getstate()
    generate_synthetic_dataset()
    assert state == random.getstate()


def test_guaranteed_slot_capacity_boundary():
    result = generate_synthetic_dataset(48, 2, guaranteed_feasible=True)
    assert len(result.witness) == 48
    assert not validate_schedule(
        result.witness, result.dataset.classes, result.dataset.rooms, ScheduleConfig()
    )
    with pytest.raises(ValueError, match="slot"):
        generate_synthetic_dataset(49, 2, guaranteed_feasible=True)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"num_classes": 9},
        {"num_classes": 101},
        {"num_rooms": 1},
        {"num_rooms": 101},
        {"seed": 1.5},
        {"difficulty": "bad"},
        {"guaranteed_feasible": "yes"},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        generate_synthetic_dataset(**kwargs)


def test_cli_export_and_real_unknown_status(tmp_path, capsys):
    path = tmp_path / "generated.xlsx"
    main(
        [
            "--classes",
            "10",
            "--rooms",
            "2",
            "--seed",
            "42",
            "--output",
            str(path),
            "--check",
            "--time-limit",
            "0.000000001",
        ]
    )
    d = read_dataset(path)
    assert len(d.classes) == 10 and len(d.rooms) == 2
    output = capsys.readouterr().out
    assert "has not been checked" in output
    assert "CP-SAT: UNKNOWN" in output and "CP-SAT: INFEASIBLE" not in output


def test_cli_guaranteed_schema_and_feasibility(tmp_path, capsys):
    path = tmp_path / "generated.xlsx"
    main(
        [
            "--classes",
            "10",
            "--rooms",
            "2",
            "--guaranteed-feasible",
            "--check",
            "--output",
            str(path),
        ]
    )
    text = capsys.readouterr().out
    assert "witness independently validated" in text
    assert "CP-SAT: OPTIMAL" in text or "CP-SAT: FEASIBLE" in text
    assert not validate_inputs(read_dataset(path).classes, read_dataset(path).rooms)
