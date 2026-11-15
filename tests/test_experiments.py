import csv
import json

from application.experiments import ExperimentCase, run_experiments, write_results


def test_report_records_true_results(tmp_path):
    cases = (ExperimentCase("trade-off", "Saturday trade-off", 0), ExperimentCase("impossible", "Infeasible"))
    report = run_experiments(2, cases)
    assert report["project"] == "CampusFlow AI" and len(report["rows"]) == 4
    row = next(r for r in report["rows"] if r["case_id"] == "trade-off" and r["algorithm"] == "CP-SAT")
    assert (row["P"], row["N_Sat"], row["J"]) == (100, 200, 100)
    assert row["class_count"] == 4 and row["room_count"] == 1
    assert len(row["assignments"]) == 4 and row["hard_violations"] == 0
    failed = next(r for r in report["rows"] if r["case_id"] == "impossible" and r["algorithm"] == "Greedy")
    assert not failed["complete"] and failed["J"] is None and failed["hard_violations"] > 0
    write_results(report, tmp_path)
    assert json.loads((tmp_path / "experiments.json").read_text())["rows"] == report["rows"]
    with (tmp_path / "experiments.csv").open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 4 and rows[-1]["J"] == ""


def test_timeout_remains_unknown_in_export():
    report = run_experiments(1e-9, (ExperimentCase("timeout", "Basic"),))
    cp = next(r for r in report["rows"] if r["algorithm"] == "CP-SAT")
    assert cp["status"] == "UNKNOWN" and not cp["complete"]
    assert cp["P"] is cp["J"] is cp["best_bound"] is None