"""Tabular result reports. Solver orchestration lives in workflows.py."""

import pandas as pd

# Existing callers may keep importing run_what_if here.
from application.workflows import run_what_if


def comparison_frame(results) -> pd.DataFrame:
    rows = []
    for result in results:
        m = result.metrics if result.complete else None
        rows.append({
            "Thuật toán": result.algorithm, "Lịch đầy đủ hợp lệ": result.complete,
            "Vi phạm lịch trả về": len(result.violations) if result.assignments or result.complete else None,
            "P · Đỉnh chuyển ca": m.peak_movement if m else None,
            "N_Sat · Lượt thứ Bảy": m.saturday_enrollment if m else None,
            "J · Mục tiêu": m.objective if m else None,
            "Số lớp thứ Bảy": m.saturday_classes if m else None,
            "Ghế dư": m.unused_seats if m else None,
            "Lấp đầy phòng (%)": round(m.room_utilization * 100, 1) if m else None,
            "Thời gian (s)": round(result.runtime_seconds, 4),
            "Trạng thái": result.status, "Best bound": result.best_bound,
        })
    return pd.DataFrame(rows)



def what_if_frame(results) -> pd.DataFrame:
    return pd.DataFrame([{
        "λ": penalty, "Trạng thái": result.status,
        "P": result.metrics.peak_movement if result.complete else None,
        "N_Sat": result.metrics.saturday_enrollment if result.complete else None,
        "J": result.metrics.objective if result.complete else None,
        "Best bound": result.best_bound, "Thời gian (s)": round(result.runtime_seconds, 4),
    } for penalty, result in results])
