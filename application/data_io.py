"""Excel import/export and fixed, reproducible demonstration datasets."""

from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path

import pandas as pd

from application.models import ClassSession, Dataset, DAYS, Room, SESSIONS, TIMES
from application.validation import DatasetError, require_valid_inputs
# Retain the existing data_io imports for callers; canonical definitions live in sample_data.
from application.sample_data import SAMPLE_DESCRIPTIONS, SAMPLE_NAMES, load_sample

CLASS_COLUMNS = ["class_id", "class_name", "students", "allowed_days", "allowed_sessions"]
ROOM_COLUMNS = ["room_id", "capacity"]
TIMETABLE_COLUMNS = ["class_id", "class_name", "students", "day", "session_id", "start_time", "end_time", "room_id"]

def dataset_frames(dataset: Dataset) -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pd.DataFrame([{
            "class_id": c.class_id, "class_name": c.class_name, "students": c.students,
            "allowed_days": ",".join(c.allowed_days), "allowed_sessions": ",".join(map(str, c.allowed_sessions)),
        } for c in dataset.classes], columns=CLASS_COLUMNS),
        pd.DataFrame([{"room_id": r.room_id, "capacity": r.capacity} for r in dataset.rooms], columns=ROOM_COLUMNS),
    )


def _excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            sheet = writer.sheets[name]
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column in sheet.columns:
                sheet.column_dimensions[column[0].column_letter].width = min(48, max(16, max(len(str(cell.value or "")) for cell in column) + 2))
                for cell in column:
                    if isinstance(cell.value, str):
                        cell.data_type = "s"
    return output.getvalue()


def dataset_excel(dataset: Dataset) -> bytes:
    classes, rooms = dataset_frames(dataset)
    return _excel_bytes({"Classes": classes, "Rooms": rooms})


def _text(value) -> str:
    return str(value).strip() if value is not None and not pd.isna(value) else ""


def _integer(value, label: str) -> int:
    try:
        number = Decimal(_text(value))
        if isinstance(value, bool) or not number.is_finite() or number != number.to_integral_value() or number <= 0:
            raise ValueError
        return int(number)
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError(f"{label} phải là số nguyên dương.") from None


def _tokens(value, defaults, label, converter=str):
    text = _text(value)
    if not text:
        return defaults
    tokens = [part.strip() for part in text.split(",")]
    try:
        values = tuple(converter(token) for token in tokens)
    except ValueError:
        raise ValueError(f"{label}: định dạng không hợp lệ ({text}).") from None
    if any(token == "" for token in tokens) or any(v not in defaults for v in values):
        raise ValueError(f"{label}: chỉ chấp nhận {','.join(map(str, defaults))}; Sunday bị cấm.")
    return tuple(dict.fromkeys(values))


def read_dataset(source, name: str = "Excel upload") -> Dataset:
    """Reject the entire workbook on any bad row; never silently discard rows."""
    try:
        with pd.ExcelFile(source, engine="openpyxl") as book:
            missing = {"Classes", "Rooms"} - set(book.sheet_names)
            if missing:
                raise DatasetError([f"Thiếu sheet: {', '.join(sorted(missing))}."])
            frames = {s: pd.read_excel(book, sheet_name=s, dtype=object, keep_default_na=False) for s in ("Classes", "Rooms")}
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError(["Không đọc được Excel .xlsx. Hãy kiểm tra file và tải lại theo template."]) from exc
    errors, classes, rooms = [], [], []
    for sheet, required in (("Classes", CLASS_COLUMNS[:3]), ("Rooms", ROOM_COLUMNS)):
        missing = set(required) - set(frames[sheet].columns)
        if missing:
            errors.append(f"{sheet}: thiếu cột {', '.join(sorted(missing))}.")
    if errors:
        raise DatasetError(errors)
    for idx, row in frames["Classes"].iterrows():
        prefix = f"Classes, dòng {idx+2} [{_text(row['class_id'])}]"
        try:
            classes.append(ClassSession(
                _text(row["class_id"]), _text(row["class_name"]), _integer(row["students"], "students"),
                _tokens(row.get("allowed_days"), DAYS, "allowed_days"),
                _tokens(row.get("allowed_sessions"), SESSIONS, "allowed_sessions", int),
            ))
        except ValueError as exc:
            errors.append(f"{prefix}: {exc}")
    for idx, row in frames["Rooms"].iterrows():
        try:
            rooms.append(Room(_text(row["room_id"]), _integer(row["capacity"], "capacity")))
        except ValueError as exc:
            errors.append(f"Rooms, dòng {idx+2} [{_text(row['room_id'])}]: {exc}")
    if errors:
        raise DatasetError(errors)
    require_valid_inputs(tuple(classes), tuple(rooms))
    return Dataset(tuple(classes), tuple(rooms), name)


def timetable_frame(result, dataset: Dataset) -> pd.DataFrame:
    classes = {c.class_id: c for c in dataset.classes}
    rows = []
    for a in sorted(result.assignments, key=lambda a: (DAYS.index(a.day), a.session_id, a.room_id)):
        cls = classes[a.class_id]
        start, end = TIMES[a.session_id]
        rows.append(dict(zip(TIMETABLE_COLUMNS, (a.class_id, cls.class_name, cls.students, a.day, a.session_id, start, end, a.room_id))))
    return pd.DataFrame(rows, columns=TIMETABLE_COLUMNS)


def schedule_excel(result, dataset, config) -> bytes:
    if not result.complete:
        raise ValueError("Chỉ xuất lịch hoàn chỉnh đã được kiểm chứng.")
    m = result.metrics
    summary = {
        "dataset": dataset.name, "algorithm": result.algorithm, "status": result.status,
        "allow_saturday": config.allow_saturday, "lambda": config.saturday_penalty,
        "peak_movement": m.peak_movement, "saturday_enrollment": m.saturday_enrollment,
        "objective": m.objective, "saturday_classes": m.saturday_classes,
        "unused_seats": m.unused_seats, "room_utilization": m.room_utilization,
        "runtime_seconds": result.runtime_seconds, "best_bound": result.best_bound,
        "model_note": "Movement proxy; class-session events, not unique people or measured congestion.",
    }
    windows = pd.DataFrame([{"day": w.day, "window": w.window, "departures": w.departures, "arrivals": w.arrivals, "total": w.total} for w in m.windows])
    return _excel_bytes({"Timetable": timetable_frame(result, dataset), "Summary": pd.DataFrame(summary.items(), columns=["metric", "value"]), "Movement": windows})


def write_demo_files(root: Path):
    template = root / "templates"
    samples = root / "samples"
    template.mkdir(parents=True, exist_ok=True)
    samples.mkdir(parents=True, exist_ok=True)
    (template / "campusflow-template.xlsx").write_bytes(dataset_excel(load_sample()))
    for name in SAMPLE_NAMES:
        (samples / f"{name.lower().replace(' ', '-')}.xlsx").write_bytes(dataset_excel(load_sample(name)))


if __name__ == "__main__":
    write_demo_files(Path("data"))