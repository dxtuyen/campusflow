from application.metrics import calculate_metrics
from application.models import Assignment, ClassSession, Room, ScheduleConfig


def test_five_windows_and_peak_by_hand():
    sizes = (10, 20, 30, 40, 50)
    classes = tuple(ClassSession(str(i), str(i), n) for i, n in enumerate(sizes))
    assignments = tuple(Assignment(str(i), "R", "Mon" if i < 4 else "Sat", i + 1 if i < 4 else 4) for i in range(5))
    m = calculate_metrics(assignments, classes, (Room("R", 100),), ScheduleConfig(saturday_penalty=3))
    monday = [w for w in m.windows if w.day == "Mon"]
    assert [w.total for w in monday] == [10, 30, 50, 70, 40]
    assert [w.departures for w in monday] == [0, 10, 20, 30, 40]
    assert [w.arrivals for w in monday] == [10, 20, 30, 40, 0]
    assert len(m.windows) == 30
    assert m.peak_movement == 70
    assert m.saturday_enrollment == 50 and m.saturday_classes == 1
    assert m.objective == 220 and m.unused_seats == 350
    assert m.room_utilization == 150 / 500


def test_parallel_classes_sum_into_same_load():
    classes = (ClassSession("A", "A", 10), ClassSession("B", "B", 20))
    assignments = (Assignment("A", "R1", "Mon", 4), Assignment("B", "R2", "Mon", 4))
    m = calculate_metrics(assignments, classes, (Room("R1", 10), Room("R2", 20)), ScheduleConfig())
    assert m.peak_movement == 30
    assert [w.arrivals for w in m.windows[:5]] == [0, 0, 0, 30, 0]


def test_empty_metrics_are_zero():
    m = calculate_metrics((), (), (), ScheduleConfig())
    assert m.objective == m.peak_movement == m.unused_seats == 0