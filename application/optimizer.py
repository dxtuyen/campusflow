"""CP-SAT formulation: feasible assignment variables, H1–H6 and P + λN_Sat."""

from collections import defaultdict
from time import perf_counter

from ortools.sat.python import cp_model

from application.greedy import solve_greedy, valid_choices
from application.metrics import calculate_metrics
from application.models import Assignment, DAYS, ScheduleResult, SESSIONS
from application.validation import require_valid_inputs, validate_schedule


def solve_cp_sat(classes, rooms, config) -> ScheduleResult:
    start = perf_counter()
    require_valid_inputs(classes, rooms)
    total = sum(c.students for c in classes)
    # Leave ample headroom for CP-SAT's signed int64 expression/domain checks.
    if total * (config.saturday_penalty + 2) > 2**60:
        return ScheduleResult(
            "CP-SAT",
            "MODEL_INVALID",
            runtime_seconds=perf_counter() - start,
            warnings=("Quy mô số học vượt miền số nguyên an toàn của CP-SAT.",),
        )
    model = cp_model.CpModel()
    variables, by_room, by_slot, sat_terms = (
        {},
        defaultdict(list),
        defaultdict(list),
        [],
    )
    for cls in classes:
        class_vars = []
        for room, day, session in valid_choices(cls, rooms, config):
            # Invalid rooms/days/sessions never receive a decision variable.
            key = (cls.class_id, room.room_id, day, session)
            x = model.new_bool_var(f"x_{len(variables)}")
            variables[key] = x
            class_vars.append(x)
            by_room[room.room_id, day, session].append(x)
            by_slot[day, session].append(cls.students * x)
            if day == "Sat":
                sat_terms.append(cls.students * x)
        model.add_exactly_one(class_vars)  # H1; an empty domain proves infeasibility.
    for room_vars in by_room.values():
        model.add_at_most_one(room_vars)  # H2; H3–H6 hold by variable construction.

    loads = {}
    flows = []
    for day in DAYS:
        for session in SESSIONS:
            load = model.new_int_var(0, total, f"L_{day}_{session}")
            model.add(load == sum(by_slot[day, session]))
            loads[day, session] = load
        expressions = [
            loads[day, 1],
            *(loads[day, s] + loads[day, s + 1] for s in (1, 2, 3)),
            loads[day, 4],
        ]
        for index, expression in enumerate(expressions):
            flow = model.new_int_var(0, total, f"F_{day}_{index}")
            model.add(flow == expression)
            flows.append(flow)
    peak = model.new_int_var(0, total, "P")
    model.add_max_equality(peak, flows)
    n_sat = model.new_int_var(0, total, "N_Sat")
    model.add(n_sat == sum(sat_terms))
    model.minimize(peak + config.saturday_penalty * n_sat)

    # A feasible Greedy hint can help search. It never constrains CP-SAT.
    baseline = solve_greedy(classes, rooms, config)
    if baseline.complete:
        selected = {
            (a.class_id, a.room_id, a.day, a.session_id) for a in baseline.assignments
        }
        for key, var in variables.items():
            model.add_hint(var, int(key in selected))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = config.time_limit_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    status_code = solver.solve(model)
    status = solver.status_name(status_code)
    runtime = perf_counter() - start
    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        message = {
            "INFEASIBLE": "Không tồn tại lịch thỏa tất cả ràng buộc theo chính sách hiện tại. Chưa xác định chính xác tập ràng buộc gây mâu thuẫn.",
            "UNKNOWN": "Chưa tìm được lịch hoặc chưa kết luận trong giới hạn tính toán; UNKNOWN không có nghĩa là vô nghiệm.",
            "MODEL_INVALID": "Mô hình CP-SAT không hợp lệ; cần kiểm tra cấu hình/mã nguồn.",
        }.get(status, status)
        return ScheduleResult(
            "CP-SAT", status, runtime_seconds=runtime, warnings=(message,)
        )
    assignments = tuple(
        Assignment(*key) for key, x in variables.items() if solver.boolean_value(x)
    )
    violations = tuple(validate_schedule(assignments, classes, rooms, config))
    if violations:
        return ScheduleResult(
            "CP-SAT",
            "MODEL_INVALID",
            assignments,
            runtime_seconds=runtime,
            violations=violations,
            warnings=(
                "Lịch từ solver không vượt qua kiểm chứng độc lập. Không công bố như lịch hợp lệ.",
            ),
        )
    metrics = calculate_metrics(assignments, classes, rooms, config)
    # This detects any disagreement between the formulation and independent arithmetic.
    if (
        metrics.objective != round(solver.objective_value)
        or metrics.peak_movement != solver.value(peak)
        or metrics.saturday_enrollment != solver.value(n_sat)
    ):
        return ScheduleResult(
            "CP-SAT",
            "MODEL_INVALID",
            assignments,
            runtime_seconds=runtime,
            warnings=("Sai khác giữa metric độc lập và biến mục tiêu trong solver.",),
        )
    warnings = (
        ("Đã có lịch hợp lệ; chưa chứng minh tối ưu trong thời gian cho phép.",)
        if status == "FEASIBLE"
        else ()
    )
    return ScheduleResult(
        "CP-SAT",
        status,
        assignments,
        metrics,
        perf_counter() - start,
        solver.objective_value,
        solver.best_objective_bound,
        warnings=warnings,
    )
