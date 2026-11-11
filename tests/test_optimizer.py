from itertools import product

import pytest
from ortools.sat.python import cp_model

from application.data_io import load_sample
from application.greedy import solve_greedy
from application.metrics import calculate_metrics
from application.models import Assignment, ClassSession, Room, ScheduleConfig
from application.optimizer import solve_cp_sat
from application.validation import validate_schedule


@pytest.mark.parametrize("name", ["Basic", "Congestion"])
def test_samples_feasible_and_independently_validated(name, config):
    data = load_sample(name)
    result = solve_cp_sat(data.classes, data.rooms, config)
    assert result.complete
    assert not validate_schedule(result.assignments, data.classes, data.rooms, config)
    assert result.metrics == calculate_metrics(result.assignments, data.classes, data.rooms, config)
    assert result.objective_value == result.metrics.objective
    assert result.best_bound <= result.objective_value


def test_known_saturday_trade_off():
    data = load_sample("Saturday trade-off")
    free = solve_cp_sat(data.classes, data.rooms, ScheduleConfig(saturday_penalty=0))
    costly = solve_cp_sat(data.classes, data.rooms, ScheduleConfig(saturday_penalty=10))
    assert free.status == costly.status == "OPTIMAL"
    assert (free.metrics.peak_movement, free.metrics.saturday_enrollment, free.metrics.objective) == (100, 200, 100)
    assert (costly.metrics.peak_movement, costly.metrics.saturday_enrollment, costly.metrics.objective) == (200, 0, 200)


def test_weekdays_only_never_schedules_saturday():
    data = load_sample("Saturday trade-off")
    result = solve_cp_sat(data.classes, data.rooms, ScheduleConfig(allow_saturday=False, saturday_penalty=0))
    assert result.complete and all(a.day not in ("Sat", "Sun") for a in result.assignments)
    assert result.metrics.saturday_enrollment == 0


def test_no_day_left_is_infeasible():
    result = solve_cp_sat((ClassSession("C", "C", 10, ("Sat",)),), (Room("R", 10),), ScheduleConfig(allow_saturday=False))
    assert result.status == "INFEASIBLE" and not result.complete


def test_collision_infeasible(config):
    data = load_sample("Infeasible")
    result = solve_cp_sat(data.classes, data.rooms, config)
    assert result.status == "INFEASIBLE" and not result.assignments and result.metrics is None


@pytest.mark.parametrize("solve", [solve_greedy, solve_cp_sat], ids=["greedy", "cp_sat"])
@pytest.mark.parametrize("class_count", [20, 21])
def test_school_slot_capacity_is_per_room_and_load_sums_all_classes(solve, class_count, config):
    # Every class must attend the same slot: parallel rooms, not 20 distinct slots.
    classes = tuple(ClassSession(f"C{i}", f"Lớp {i}", 30, ("Mon",), (1,)) for i in range(class_count))
    rooms = tuple(Room(f"R{i}", 40) for i in range(20))
    result = solve(classes, rooms, config)
    if class_count > len(rooms):
        assert not result.complete and result.metrics is None
        assert result.status == ("INFEASIBLE" if solve is solve_cp_sat else "FAILED")
        return
    assert result.complete and len(result.assignments) == 20
    assert {(a.day, a.session_id) for a in result.assignments} == {("Mon", 1)}
    assert len({a.room_id for a in result.assignments}) == 20
    assert not validate_schedule(result.assignments, classes, rooms, config)
    assert result.metrics.peak_movement == 600
    assert result.metrics == calculate_metrics(result.assignments, classes, rooms, config)


def test_real_timeout_is_unknown_not_infeasible(basic):
    result = solve_cp_sat(basic.classes, basic.rooms, ScheduleConfig(time_limit_seconds=1e-9))
    assert result.status == "UNKNOWN" and result.metrics is None


@pytest.mark.parametrize("status", [cp_model.UNKNOWN, cp_model.MODEL_INVALID])
def test_unsolved_statuses_do_not_read_solution(monkeypatch, basic, config, status):
    monkeypatch.setattr(cp_model.CpSolver, "solve", lambda self, model: status)
    result = solve_cp_sat(basic.classes, basic.rooms, config)
    assert result.status == ("UNKNOWN" if status == cp_model.UNKNOWN else "MODEL_INVALID")
    assert not result.complete and result.objective_value is None and result.best_bound is None


def test_feasible_status_preserved(monkeypatch, basic, config):
    original = cp_model.CpSolver.solve
    def report_feasible(self, model):
        assert original(self, model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        return cp_model.FEASIBLE
    monkeypatch.setattr(cp_model.CpSolver, "solve", report_feasible)
    result = solve_cp_sat(basic.classes, basic.rooms, config)
    assert result.complete and result.status == "FEASIBLE" and result.warnings


@pytest.mark.parametrize("penalty", [0, 1, 3])
def test_optimum_against_exhaustive_enumeration(penalty):
    classes = (ClassSession("A", "A", 30, ("Mon", "Sat"), (1, 2)), ClassSession("B", "B", 20, ("Mon", "Sat"), (2, 3)), ClassSession("C", "C", 10, ("Mon", "Sat"), (1, 3)))
    rooms = (Room("R", 30),)
    config = ScheduleConfig(saturday_penalty=penalty)
    domains = [[Assignment(c.class_id, "R", d, s) for d in c.allowed_days for s in c.allowed_sessions] for c in classes]
    objectives = [calculate_metrics(a, classes, rooms, config).objective for a in product(*domains) if not validate_schedule(a, classes, rooms, config)]
    result = solve_cp_sat(classes, rooms, config)
    assert result.status == "OPTIMAL" and result.metrics.objective == min(objectives)