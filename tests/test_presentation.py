"""Verify displayed schedules/plots preserve real assignments and metrics."""

from dataclasses import replace

from application.data_io import load_sample, timetable_frame
from application.metrics import calculate_metrics
from application.models import Assignment, DAYS, ScheduleConfig, ScheduleResult
from application.presentation import busiest_day, comparison_figure, comparison_summary, movement_figure, movement_heatmap, result_summary, room_colors, timetable_grid_html, visual_comparison_summary, what_if_summary


def scheduled(dataset, assignments, penalty=3, algorithm="CP-SAT", status="OPTIMAL"):
    config = ScheduleConfig(saturday_penalty=penalty)
    return ScheduleResult(algorithm, status, assignments, calculate_metrics(assignments, dataset.classes, dataset.rooms, config))


def test_grid_preserves_parallel_classes_rooms_and_empty_slots():
    dataset = load_sample()
    assignments = (Assignment("CLS01", "A102", "Mon", 1), Assignment("CLS02", "A101", "Mon", 1), Assignment("CLS03", "B201", "Sat", 4))
    frame = timetable_frame(ScheduleResult("CP-SAT", "FEASIBLE", assignments), dataset)
    html = timetable_grid_html(frame, DAYS)
    assert html.count('class="cf-class"') == 3
    assert html.count('scope="row"') == 4
    assert "A102 · 90 lượt" in html and "A101 · 65 lượt" in html
    assert 'class="cf-slot-summary">2 lớp · 155 lượt đăng ký' in html
    assert "07:00–09:30" in html and "16:30–19:00" in html
    assert 'class="cf-saturday"' in html
    assert 'aria-label="Không có buổi học"' in html
    assert all(html.count(f"<strong>{a.class_id}</strong>") == 1 for a in assignments)
    saturday = timetable_grid_html(frame[frame.day == "Sat"], ("Sat",))
    assert "Thứ Hai" not in saturday and "CLS03" in saturday and "CLS01" not in saturday


def test_grid_escapes_workbook_text():
    dataset = load_sample()
    malicious = '<script>alert("class")</script>'
    dataset = replace(dataset, classes=(replace(dataset.classes[0], class_name=malicious),))
    frame = timetable_frame(ScheduleResult("CP-SAT", "FEASIBLE", (Assignment("CLS01", "A102", "Mon", 1),)), dataset)
    html = timetable_grid_html(frame, ("Mon",))
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_day_chart_keeps_five_windows_and_global_peak():
    dataset = load_sample("Saturday trade-off")
    assignments = tuple(Assignment(f"SAT{i}", "A101", "Mon", i) for i in range(1, 5))
    result = scheduled(dataset, assignments)
    assert busiest_day(result.metrics) == "Mon"
    # Saturday is empty; do not replace the weekly peak (200) with local peak 0.
    saturday = movement_figure(result.metrics, "Sat")
    assert list(saturday.data[0].y) == [0] * 5
    assert list(saturday.data[1].y) == [0] * 5
    assert saturday.layout.shapes[0].y0 == 200
    monday = movement_figure(result.metrics, "Mon")
    assert list(monday.data[0].y) == [0, 100, 100, 100, 100]
    assert list(monday.data[1].y) == [100, 100, 100, 100, 0]
    assert len(movement_figure(result.metrics).data[0].x) == 30
    assert len(movement_figure(result.metrics, days=DAYS[:-1]).data[0].x) == 25


def test_summary_does_not_confuse_objective_with_peak_improvement():
    dataset = load_sample("Saturday trade-off")
    with_saturday = (Assignment("SAT1", "A101", "Mon", 1), Assignment("SAT2", "A101", "Mon", 3), Assignment("SAT3", "A101", "Sat", 1), Assignment("SAT4", "A101", "Sat", 3))
    weekdays = tuple(Assignment(f"SAT{i}", "A101", "Mon", i) for i in range(1, 5))
    greedy = scheduled(dataset, with_saturday, algorithm="Greedy", status="FEASIBLE")
    cp = scheduled(dataset, weekdays)
    summary = comparison_summary(greedy, cp)
    assert "giảm mục tiêu J từ 700 xuống 200" in summary
    assert "P: 100 → 200" in summary and "lượt thứ Bảy: 200 → 0" in summary
    assert "Đã xếp đủ 4 buổi" in result_summary(cp)
    assert "cùng mục tiêu J" in comparison_summary(cp, cp)
    failed = ScheduleResult("Greedy", "FAILED")
    assert "Không so sánh" in comparison_summary(failed, cp)
    assert "chưa có lịch hoàn chỉnh" in comparison_summary(cp, ScheduleResult("CP-SAT", "UNKNOWN"))


def test_policy_explanation_uses_raw_metrics_and_discloses_missing_results():
    dataset = load_sample("Saturday trade-off")
    weekend = (Assignment("SAT1", "A101", "Mon", 1), Assignment("SAT2", "A101", "Mon", 3), Assignment("SAT3", "A101", "Sat", 1), Assignment("SAT4", "A101", "Sat", 3))
    weekdays = tuple(Assignment(f"SAT{i}", "A101", "Mon", i) for i in range(1, 5))
    low = scheduled(dataset, weekend, penalty=0)
    high = scheduled(dataset, weekdays, penalty=10, status="FEASIBLE")
    summary = what_if_summary([(0, low), (3, ScheduleResult("CP-SAT", "UNKNOWN")), (10, high)])
    assert "P thay đổi 100 → 200" in summary
    assert "thứ Bảy thay đổi 200 → 0" in summary
    assert "chưa được chứng minh tối ưu" in summary
    assert "Một số mức phạt chưa có lịch" in summary
    assert "không đổi" in what_if_summary([(0, high), (10, high)])


def test_heatmap_exact_values_peak_marks_and_weekdays():
    dataset = load_sample("Saturday trade-off")
    result = scheduled(dataset, tuple(Assignment(f"SAT{i}", "A101", "Mon", i) for i in range(1, 5)))
    heatmap = movement_heatmap(result.metrics).data[0]
    assert list(heatmap.z) == [[100, 0, 0, 0, 0, 0], [200, 0, 0, 0, 0, 0], [200, 0, 0, 0, 0, 0], [200, 0, 0, 0, 0, 0], [100, 0, 0, 0, 0, 0]]
    assert sum("★" in cell for row in heatmap.text for cell in row) == 3
    assert len(movement_heatmap(result.metrics, DAYS[:-1]).data[0].x) == 5


def test_room_colors_remain_stable_while_filtering():
    dataset = load_sample()
    assignments = (Assignment("CLS01", "A102", "Mon", 1), Assignment("CLS02", "A101", "Mon", 1))
    frame = timetable_frame(ScheduleResult("CP-SAT", "FEASIBLE", assignments), dataset)
    rooms = [r.room_id for r in dataset.rooms]
    background, border = room_colors(rooms)["A102"]
    all_rooms = timetable_grid_html(frame, DAYS, rooms)
    filtered = timetable_grid_html(frame[frame.room_id == "A102"], DAYS, rooms)
    style = f"background:{background};border-left-color:{border}"
    assert style in all_rooms and style in filtered
    assert 'data-room="A101"' not in filtered and 'data-room="A102"' in filtered


def test_visual_comparison_uses_raw_metrics_and_rejects_partial_schedules():
    import pytest
    dataset = load_sample("Saturday trade-off")
    weekend = (Assignment("SAT1", "A101", "Mon", 1), Assignment("SAT2", "A101", "Mon", 3), Assignment("SAT3", "A101", "Sat", 1), Assignment("SAT4", "A101", "Sat", 3))
    weekdays = tuple(Assignment(f"SAT{i}", "A101", "Mon", i) for i in range(1, 5))
    g, c = scheduled(dataset, weekend), scheduled(dataset, weekdays)
    chart = comparison_figure(g, c)
    assert list(chart.data[0].x) == [100, 200]
    assert list(chart.data[1].x) == [200, 0]
    assert "Cao điểm tăng 100" in visual_comparison_summary(g, c)
    assert "thứ Bảy giảm 200" in visual_comparison_summary(g, c)
    with pytest.raises(ValueError):
        comparison_figure(ScheduleResult("Greedy", "FAILED"), c)
