"""Seeded synthetic inputs. Optional feasibility comes with a checked witness."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import random

from application.data_io import dataset_excel
from application.models import Assignment, ClassSession, Dataset, DAYS, Room, ScheduleConfig, SESSIONS
from application.validation import require_valid_inputs, validate_schedule


@dataclass(frozen=True)
class GeneratedDataset:
    dataset: Dataset
    witness: tuple[Assignment, ...] = ()

    @property
    def guaranteed_feasible(self) -> bool:
        return bool(self.witness)


def _domain(rng, values, count, required=None):
    if required is None:
        selected = set(rng.sample(list(values), count))
    else:
        remaining = [value for value in values if value != required]
        selected = {required, *rng.sample(remaining, count - 1)}
    return tuple(value for value in values if value in selected)


def generate_synthetic_dataset(num_classes=30, num_rooms=6, seed=42, difficulty="constrained", guaranteed_feasible=False) -> GeneratedDataset:
    """Use a private RNG; never mutate the caller's random state or call CP-SAT.

    Without a witness, feasibility is unknown until a solver is run. With one,
    construct the schedule first, generate compatible data, and independently
    validate that schedule before returning a guaranteed-feasible label.
    """
    if type(num_classes) is not int or not 10 <= num_classes <= 100:
        raise ValueError("num_classes phải là số nguyên từ 10 đến 100.")
    if type(num_rooms) is not int or not 2 <= num_rooms <= 20:
        raise ValueError("num_rooms phải là số nguyên từ 2 đến 20.")
    if type(seed) is not int:
        raise ValueError("seed phải là số nguyên.")
    if difficulty not in ("easy", "constrained"):
        raise ValueError("difficulty phải là easy hoặc constrained.")
    if type(guaranteed_feasible) is not bool:
        raise ValueError("guaranteed_feasible phải là boolean.")
    if guaranteed_feasible and num_classes > num_rooms * len(DAYS) * len(SESSIONS):
        raise ValueError("Không đủ slot phòng cho lịch chứng minh. Giảm số lớp hoặc tăng số phòng.")

    rng = random.Random(seed)
    rooms = tuple(Room(f"R{i:03}", rng.choice((40, 60, 80, 100, 120, 160))) for i in range(1, num_rooms + 1))
    slots = [(r, d, s) for r in rooms for d in DAYS for s in SESSIONS]
    rng.shuffle(slots)
    classes, witness = [], []
    max_capacity = max(r.capacity for r in rooms)
    for index in range(num_classes):
        if guaranteed_feasible:
            room, day, session = slots[index]
            capacity = room.capacity
        else:
            room, day, session = None, None, None
            capacity = max_capacity
        students = rng.randint(max(10, capacity // 3), capacity)
        day_count = rng.randint(4, 6) if difficulty == "easy" else rng.randint(1, 3)
        session_count = rng.randint(3, 4) if difficulty == "easy" else rng.randint(1, 2)
        class_id = f"SYN{index+1:03}"
        classes.append(ClassSession(class_id, f"Buổi học giả lập {index+1:03}", students,
                                    _domain(rng, DAYS, day_count, day),
                                    _domain(rng, SESSIONS, session_count, session)))
        if guaranteed_feasible:
            witness.append(Assignment(class_id, room.room_id, day, session))
    dataset = Dataset(tuple(classes), rooms, f"Synthetic · seed {seed}")
    require_valid_inputs(dataset.classes, dataset.rooms)
    if witness:
        errors = validate_schedule(tuple(witness), dataset.classes, dataset.rooms, ScheduleConfig())
        if errors:
            raise RuntimeError("Lịch chứng minh không hợp lệ: " + "; ".join(errors))
    return GeneratedDataset(dataset, tuple(witness))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate synthetic Classes/Rooms Excel, not real university data.")
    parser.add_argument("--classes", type=int, default=30)
    parser.add_argument("--rooms", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--difficulty", choices=("easy", "constrained"), default="constrained")
    parser.add_argument("--guaranteed-feasible", action="store_true")
    parser.add_argument("--check", action="store_true", help="Actually run CP-SAT and report its status.")
    parser.add_argument("--time-limit", type=float, default=10)
    parser.add_argument("--output", type=Path, default=Path("data/generated.xlsx"))
    args = parser.parse_args(argv)
    try:
        config = ScheduleConfig(time_limit_seconds=args.time_limit)
        result = generate_synthetic_dataset(args.classes, args.rooms, args.seed, args.difficulty, args.guaranteed_feasible)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(dataset_excel(result.dataset))
    print(f"Written: {args.output} · {len(result.dataset.classes)} classes · {len(result.dataset.rooms)} rooms · synthetic data")
    print("Schema valid. " + ("Feasible witness independently validated (Saturday Allowed)." if result.guaranteed_feasible else "Feasibility has not been checked."))
    if args.check:
        from application.optimizer import solve_cp_sat
        solution = solve_cp_sat(result.dataset.classes, result.dataset.rooms, config)
        print(f"CP-SAT: {solution.status} · runtime {solution.runtime_seconds:.3f}s")
        if solution.complete:
            print(f"P={solution.metrics.peak_movement}, N_Sat={solution.metrics.saturday_enrollment}, J={solution.metrics.objective}, best_bound={solution.best_bound}")
        for warning in solution.warnings:
            print(warning)


if __name__ == "__main__":
    main()