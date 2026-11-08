"""Deterministic baseline: most constrained first, then incremental objective."""

from time import perf_counter

from application.metrics import calculate_metrics, movement_windows
from application.models import Assignment, ScheduleResult, SESSIONS
from application.validation import require_valid_inputs, validate_schedule


def valid_choices(cls, rooms, config):
    return tuple(
        (r, d, s)
        for d in config.days
        if d in cls.allowed_days
        for s in SESSIONS
        if s in cls.allowed_sessions
        for r in sorted(rooms, key=lambda r: r.room_id)
        if r.capacity >= cls.students
    )


def solve_greedy(classes, rooms, config) -> ScheduleResult:
    start = perf_counter()
    require_valid_inputs(classes, rooms)
    choices = {c.class_id: valid_choices(c, rooms, config) for c in classes}
    ordered = sorted(
        classes, key=lambda c: (len(choices[c.class_id]), -c.students, c.class_id)
    )
    loads, occupied, assignments = {}, set(), []
    saturday, current_objective = 0, 0
    for cls in ordered:
        candidates = []
        for room, day, session in choices[cls.class_id]:
            if (room.room_id, day, session) in occupied:
                continue
            key = (day, session)
            loads[key] = loads.get(key, 0) + cls.students
            peak = max(w.total for w in movement_windows(loads))
            sat = saturday + (cls.students if day == "Sat" else 0)
            objective = peak + config.saturday_penalty * sat
            loads[key] -= cls.students
            score = (
                objective - current_objective,
                room.capacity - cls.students,
                config.days.index(day),
                session,
                room.room_id,
            )
            candidates.append((score, room, day, session, objective, sat))
        if not candidates:
            partial = tuple(assignments)
            return ScheduleResult(
                "Greedy",
                "FAILED",
                partial,
                runtime_seconds=perf_counter() - start,
                violations=tuple(validate_schedule(partial, classes, rooms, config)),
                warnings=(
                    f"Greedy failed to find complete schedule: không xếp được {cls.class_id}. Không chứng minh bài toán vô nghiệm.",
                ),
            )
        _, room, day, session, current_objective, saturday = min(
            candidates, key=lambda item: item[0]
        )
        assignments.append(Assignment(cls.class_id, room.room_id, day, session))
        occupied.add((room.room_id, day, session))
        loads[day, session] = loads.get((day, session), 0) + cls.students
    assignments = tuple(assignments)
    violations = tuple(validate_schedule(assignments, classes, rooms, config))
    metrics = (
        None if violations else calculate_metrics(assignments, classes, rooms, config)
    )
    return ScheduleResult(
        "Greedy",
        "FAILED" if violations else "FEASIBLE",
        assignments,
        metrics,
        perf_counter() - start,
        metrics.objective if metrics else None,
        violations=violations,
    )
