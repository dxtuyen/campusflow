"""Small reproducible experiment CLI for demo datasets and report evidence."""

import argparse
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform

from application.metrics import calculate_metrics
from application.models import ScheduleConfig
from application.sample_data import load_sample
from application.validation import validate_schedule
from application.workflows import run_comparison


@dataclass(frozen=True)
class ExperimentCase:
    case_id: str
    sample: str
    penalty: int = 3
    allow_saturday: bool = True


DEMO_CASES = (
    ExperimentCase("basic", "Basic"),
    ExperimentCase("congestion", "Congestion"),
    ExperimentCase("saturday-lambda-0", "Saturday trade-off", 0),
    ExperimentCase("saturday-lambda-3", "Saturday trade-off", 3),
    ExperimentCase("saturday-lambda-10", "Saturday trade-off", 10),
    ExperimentCase("weekdays-only", "Saturday trade-off", 3, False),
    ExperimentCase("infeasible", "Infeasible"),
)



def run_experiments(time_limit_seconds=10.0, cases=DEMO_CASES) -> dict:
    rows = []
    for case in cases:
        dataset = load_sample(case.sample)
        config = ScheduleConfig(case.allow_saturday, case.penalty, time_limit_seconds)
        comparison = run_comparison(dataset, config)
        for result in (comparison.greedy, comparison.cp_sat):
            if result.complete:
                errors = validate_schedule(result.assignments, dataset.classes, dataset.rooms, config)
                measured = calculate_metrics(result.assignments, dataset.classes, dataset.rooms, config)
                if errors or measured != result.metrics:
                    raise RuntimeError(f"Independent validation failed: {case.case_id}/{result.algorithm}: {errors}")
            m = result.metrics if result.complete else None
            rows.append({
                "case_id": case.case_id, "dataset": case.sample, "class_count": len(dataset.classes), "room_count": len(dataset.rooms),
                "algorithm": result.algorithm, "allow_saturday": config.allow_saturday,
                "lambda": config.saturday_penalty, "time_limit_seconds": config.time_limit_seconds,
                "status": result.status, "complete": result.complete,
                "hard_violations": len(result.violations) if result.assignments or result.complete else None,
                "P": m.peak_movement if m else None, "N_Sat": m.saturday_enrollment if m else None,
                "J": m.objective if m else None, "saturday_classes": m.saturday_classes if m else None,
                "unused_seats": m.unused_seats if m else None,
                "runtime_seconds": result.runtime_seconds, "best_bound": result.best_bound,
                "assignments": [asdict(a) for a in result.assignments], "warnings": list(result.warnings),
            })
    return {
        "project": "CampusFlow AI", "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "versions": {name: version(name) for name in ("campusflow-ai", "ortools", "pandas", "streamlit", "plotly")},
        "num_workers": 1, "solver_seed": 42,
        "movement_note": "Class-session event proxy, not unique students or measured campus congestion.",
        "rows": rows,
    }


def write_results(report: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "experiments.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    fields = [key for key in report["rows"][0] if key not in ("assignments", "warnings")] if report["rows"] else ["case_id", "algorithm", "status"]
    with (output / "experiments.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(report["rows"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run seven small CampusFlow demo cases; all values come from real schedules.")
    parser.add_argument("--time-limit", type=float, default=10)
    parser.add_argument("--output", type=Path, default=Path("reports/experiments"))
    args = parser.parse_args(argv)
    try:
        ScheduleConfig(time_limit_seconds=args.time_limit)
    except ValueError as exc:
        parser.error(str(exc))
    report = run_experiments(args.time_limit)
    write_results(report, args.output)
    print(f"Written {len(report['rows'])} real algorithm results to {args.output}")
    for row in report["rows"]:
        print(f"{row['case_id']:22} {row['algorithm']:6} {row['status']:10} P={row['P']} N_Sat={row['N_Sat']} J={row['J']}")


if __name__ == "__main__":
    main()