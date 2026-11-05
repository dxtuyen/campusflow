import pytest

from application.models import Assignment, ClassSession, Room, ScheduleConfig
from application.validation import validate_inputs, validate_schedule


@pytest.mark.parametrize("bad", [0, -1, 1.5, True, "20"])
def test_students_must_be_positive_integer(bad):
    assert validate_inputs((ClassSession("C", "Name", bad),), (Room("R", 100),))


def test_duplicate_and_blank_ids(basic):
    assert any("mã trùng" in e for e in validate_inputs(basic.classes + basic.classes[:1], basic.rooms))
    assert any("room_id" in e for e in validate_inputs(basic.classes, (Room("", 200),)))
    assert validate_inputs((ClassSession("", "", 1),), (Room("R", 1),))


def test_no_eligible_room():
    assert any("không có phòng" in e for e in validate_inputs((ClassSession("C", "Name", 101),), (Room("R", 100),)))


@pytest.mark.parametrize("days,sessions", [(('Sun',), (1,)), ((), (1,)), (('Mon',), (5,)), (('Mon',), (True,)), (('Mon',), ())])
def test_forbidden_or_empty_domains(days, sessions):
    assert validate_inputs((ClassSession("C", "Name", 10, days, sessions),), (Room("R", 20),))


def test_validator_detects_every_hard_constraint():
    classes = (ClassSession("A", "A", 100, ("Mon",), (1,)), ClassSession("B", "B", 20))
    rooms = (Room("R", 80),)
    assignments = (Assignment("A", "R", "Sun", 4), Assignment("B", "R", "Sun", 4), Assignment("A", "missing", "Sat", 5), Assignment("unknown", "R", "Mon", 1))
    errors = validate_schedule(assignments, classes, rooms, ScheduleConfig(allow_saturday=False))
    for phrase in ("đúng một lần", "không tồn tại", "bị cấm", "không đủ sức chứa", "ngoài ngày/ca", "Trùng phòng", "ca 5"):
        assert any(phrase in e for e in errors)


def test_validator_reports_missing_class(basic, config):
    assert len(validate_schedule((), basic.classes, basic.rooms, config)) == 8


@pytest.mark.parametrize("kwargs", [{"saturday_penalty": -1}, {"saturday_penalty": 1.2}, {"saturday_penalty": True}, {"time_limit_seconds": 0}, {"time_limit_seconds": float("inf")}, {"allow_saturday": "yes"}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        ScheduleConfig(**kwargs)