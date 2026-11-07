"""Recompute all reported metrics from assignments, never solver variables."""

from application.models import DAYS, SESSIONS, WINDOWS, MovementWindow, ScheduleMetrics


def movement_windows(loads):
    windows = []
    for day in DAYS:
        values = [loads.get((day, s), 0) for s in SESSIONS]
        departures = [0, *values]
        arrivals = [*values, 0]
        windows.extend(
            MovementWindow(day, name, dep, arr)
            for name, dep, arr in zip(WINDOWS, departures, arrivals)
        )
    return tuple(windows)


def calculate_metrics(assignments, classes, rooms, config) -> ScheduleMetrics:
    """Call validate_schedule first when using these metrics for comparisons."""
    class_map = {c.class_id: c for c in classes}
    room_map = {r.room_id: r for r in rooms}
    loads = {(d, s): 0 for d in DAYS for s in SESSIONS}
    saturday_enrollment = saturday_classes = seats = enrollment = 0
    for a in assignments:
        students = class_map[a.class_id].students
        loads[a.day, a.session_id] += students
        seats += room_map[a.room_id].capacity
        enrollment += students
        if a.day == "Sat":
            saturday_enrollment += students
            saturday_classes += 1
    windows = movement_windows(loads)
    peak = max(w.total for w in windows)
    return ScheduleMetrics(
        peak_movement=peak,
        saturday_enrollment=saturday_enrollment,
        objective=peak + config.saturday_penalty * saturday_enrollment,
        saturday_classes=saturday_classes,
        unused_seats=seats - enrollment,
        room_utilization=enrollment / seats if seats else 0.0,
        windows=windows,
    )
