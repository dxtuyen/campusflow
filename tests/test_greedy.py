from application.analysis import comparison_frame
from application.data_io import load_sample
from application.greedy import solve_greedy
from application.models import ClassSession, Room, ScheduleConfig
from application.optimizer import solve_cp_sat
from application.validation import validate_schedule


def test_basic_complete_and_deterministic(basic, config):
    a = solve_greedy(basic.classes, basic.rooms, config)
    b = solve_greedy(basic.classes, basic.rooms, config)
    assert a.complete and a.assignments == b.assignments
    assert not validate_schedule(a.assignments, basic.classes, basic.rooms, config)


def test_failure_never_reports_partial_objective(config):
    data = load_sample("Infeasible")
    result = solve_greedy(data.classes, data.rooms, config)
    assert result.status == "FAILED" and not result.complete
    assert result.metrics is None and result.objective_value is None
    assert result.violations and "Greedy failed" in result.warnings[0]
    table = comparison_frame([result])
    assert table["J · Mục tiêu"].isna().all()


def test_weekdays_only_for_saturday_class():
    result = solve_greedy((ClassSession("C", "C", 10, ("Sat",)),), (Room("R", 10),), ScheduleConfig(allow_saturday=False))
    assert result.status == "FAILED"


def test_greedy_can_fail_when_cp_sat_finds_schedule(config):
    # A occupies slot 1; B then takes 3, leaving C blocked. A at 2 is feasible.
    classes = (ClassSession("A", "A", 100, ("Mon",), (1, 2)),
               ClassSession("B", "B", 90, ("Mon",), (1, 3)),
               ClassSession("C", "C", 80, ("Mon",), (1, 3)))
    rooms = (Room("R", 100),)
    greedy = solve_greedy(classes, rooms, config)
    cp_sat = solve_cp_sat(classes, rooms, config)
    assert greedy.status == "FAILED" and cp_sat.complete
    assert not validate_schedule(cp_sat.assignments, classes, rooms, config)