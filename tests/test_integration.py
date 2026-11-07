from io import BytesIO
import pandas as pd
import pytest

from application.analysis import run_what_if, what_if_frame
from application.data_io import CLASS_COLUMNS, SAMPLE_NAMES, dataset_excel, dataset_frames, load_sample, read_dataset, schedule_excel, timetable_frame
from application.optimizer import solve_cp_sat
from application.validation import DatasetError


def workbook(classes=None, rooms=None):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if classes is not None:
            classes.to_excel(writer, sheet_name="Classes", index=False)
        if rooms is not None:
            rooms.to_excel(writer, sheet_name="Rooms", index=False)
    output.seek(0)
    return output


@pytest.mark.parametrize("name", SAMPLE_NAMES)
def test_sample_round_trip(name):
    sample = load_sample(name)
    assert read_dataset(BytesIO(dataset_excel(sample)), name) == sample


def test_optional_columns_default(basic):
    classes, rooms = dataset_frames(basic)
    result = read_dataset(workbook(classes.drop(columns=CLASS_COLUMNS[3:]), rooms))
    assert result.classes == basic.classes


@pytest.mark.parametrize("column,value", [("class_id", ""), ("class_name", ""), ("students", "bad"), ("students", 1.5), ("students", -1), ("allowed_days", "Mon,Sun"), ("allowed_days", "Mon,"), ("allowed_sessions", "1,5"), ("allowed_sessions", "1,x")])
def test_bad_row_rejected_with_location(basic, column, value):
    classes, rooms = dataset_frames(basic)
    classes = classes.astype(object)
    classes.loc[0, column] = value
    with pytest.raises(DatasetError, match="dòng 2"):
        read_dataset(workbook(classes, rooms))


def test_bad_workbook_and_missing_sheet(basic):
    with pytest.raises(DatasetError):
        read_dataset(BytesIO(b"not an xlsx"))
    with pytest.raises(DatasetError, match="Rooms"):
        read_dataset(workbook(dataset_frames(basic)[0]))


def test_duplicate_ids_and_missing_columns(basic):
    classes, rooms = dataset_frames(basic)
    classes.loc[1, "class_id"] = classes.loc[0, "class_id"]
    with pytest.raises(DatasetError, match="mã trùng"):
        read_dataset(workbook(classes, rooms))
    with pytest.raises(DatasetError, match="thiếu cột"):
        read_dataset(workbook(classes.drop(columns=["students"]), rooms))


def test_import_solve_export_readback(basic, config):
    data = read_dataset(BytesIO(dataset_excel(basic)))
    result = solve_cp_sat(data.classes, data.rooms, config)
    exported = BytesIO(schedule_excel(result, data, config))
    with pd.ExcelFile(exported) as book:
        assert set(book.sheet_names) == {"Timetable", "Summary", "Movement"}
        assert len(pd.read_excel(book, "Timetable")) == 8
        summary = pd.read_excel(book, "Summary").set_index("metric")["value"]
        assert summary["objective"] == result.metrics.objective
        assert summary["status"] == result.status
        assert len(pd.read_excel(book, "Movement")) == 30
    csv = timetable_frame(result, data).to_csv(index=False)
    assert "start_time" in csv and len(pd.read_csv(BytesIO(csv.encode()))) == 8


def test_real_what_if(config):
    results = run_what_if(load_sample("Saturday trade-off"), config)
    frame = what_if_frame(results)
    assert list(frame["λ"]) == [0, 3, 10]
    assert list(frame.P) == [100, 200, 200]
    assert list(frame.N_Sat) == [200, 0, 0]
    assert all(r.status == "OPTIMAL" for _, r in results)


def test_what_if_requires_exactly_three(config, basic):
    with pytest.raises(ValueError):
        run_what_if(basic, config, (0, 3))


def test_real_artifact_workbooks_exist_and_import():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "data"
    paths = [root / "templates" / "campusflow-template.xlsx"]
    paths.extend(root / "samples" / f"{name.lower().replace(' ', '-')}.xlsx" for name in SAMPLE_NAMES)
    for path in paths:
        dataset = read_dataset(path)
        assert dataset.classes and dataset.rooms