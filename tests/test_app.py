"""Exercise the actual Streamlit script and its stateful user interactions."""

from streamlit.testing.v1 import AppTest


def app():
    return AppTest.from_file("../app.py", default_timeout=20).run()


def chart_spec(at, key):
    import json
    return json.loads(next(p.proto.spec for p in at.get("plotly_chart") if p.proto.id.endswith(f"-{key}")))


def load_sample_ui(at, name):
    at.selectbox(key="sample_choice").select(name)
    at.button(key="sample_load").click().run()
    assert not at.exception


def test_start_generate_compare_and_export_widgets():
    at = app()
    assert not at.exception
    assert [tab.label for tab in at.tabs] == ["Dữ liệu", "Lịch học", "Phân tích AI"]
    assert at.session_state.dataset.name == "Basic"
    at.button(key="generate").click().run()
    assert not at.exception
    assert at.session_state.run.cp_sat.complete
    assert len(at.get("download_button")) == 4
    assert len(at.get("plotly_chart")) == 3
    assert at.radio(key="schedule_view").value == "Lưới tuần"
    assert len(at.get("html")) == 1
    at.radio(key="schedule_view").set_value("Bảng chi tiết").run()
    assert not at.exception
    assert len(at.get("html")) == 0
    at.radio(key="view_algorithm").set_value("Greedy").run()
    assert not at.exception
    at.selectbox(key="day_filter").select("Sat").run()
    assert not at.exception


def test_policy_changes_hide_stale_results():
    at = app()
    at.button(key="generate").click().run()
    at.radio(key="policy").set_value("Weekdays Only").run()
    assert not at.exception
    assert any("đã thay đổi" in info.value for info in at.info)
    assert len(at.get("plotly_chart")) == 0
    at.button(key="generate").click().run()
    assert not at.exception
    assert all(a.day != "Sat" for a in at.session_state.run.cp_sat.assignments)


def test_infeasible_dataset_has_no_export_or_fake_metrics():
    at = app()
    load_sample_ui(at, "Infeasible")
    at.button(key="generate").click().run()
    assert not at.exception
    assert at.session_state.run.cp_sat.status == "INFEASIBLE"
    assert at.session_state.run.greedy.status == "FAILED"
    assert len(at.get("download_button")) == 2
    assert len(at.get("plotly_chart")) == 0


def test_what_if_runs_on_selected_data_and_is_invalidated():
    at = app()
    load_sample_ui(at, "Saturday trade-off")
    at.button(key="what_if_button").click().run()
    assert not at.exception
    results = at.session_state.what_if.results
    assert [r.metrics.peak_movement for _, r in results] == [100, 200, 200]
    at.multiselect(key="what_if_levels").set_value([0, 1]).run()
    assert at.button(key="what_if_button").disabled
    load_sample_ui(at, "Basic")
    assert "what_if" not in at.session_state


def test_synthetic_preview_use_optimize_same_workflow():
    at = app()
    at.number_input(key="synthetic_classes").set_value(10)
    at.number_input(key="synthetic_rooms").set_value(2)
    at.checkbox(key="synthetic_guarantee").check()
    at.button(key="synthetic_generate").click().run()
    assert not at.exception
    assert at.session_state.dataset.name == "Basic"
    assert at.session_state.synthetic.guaranteed_feasible
    assert "run" not in at.session_state  # Generation must never start the solver.
    at.button(key="synthetic_use").click().run()
    assert not at.exception
    assert at.session_state.dataset.name == "Synthetic · seed 42"
    assert len(at.session_state.dataset.classes) == 10
    at.button(key="generate").click().run()
    assert not at.exception
    assert at.session_state.run.cp_sat.complete


def test_synthetic_impossible_guarantee_has_actionable_error():
    at = app()
    at.number_input(key="synthetic_classes").set_value(100)
    at.number_input(key="synthetic_rooms").set_value(2)
    at.checkbox(key="synthetic_guarantee").check()
    at.button(key="synthetic_generate").click().run()
    assert not at.exception
    assert any("Không đủ slot" in error.value for error in at.error)
    assert at.session_state.dataset.name == "Basic"


def test_chart_day_filter_and_weekdays_only_data():
    at = app()
    at.button(key="generate").click().run()
    day_chart = chart_spec(at, "movement_detail")
    assert len(day_chart["data"][0]["x"]) == 5
    at.selectbox(key="analysis_day").select("Sat").run()
    assert not at.exception
    saturday = chart_spec(at, "movement_detail")
    assert list(saturday["data"][0]["y"]) == [0] * 5
    assert list(saturday["data"][1]["y"]) == [0] * 5
    at.selectbox(key="analysis_day").select("Tất cả").run()
    week_chart = chart_spec(at, "movement_detail")
    assert len(week_chart["data"][0]["x"]) == 30
    at.radio(key="policy").set_value("Weekdays Only").run()
    at.button(key="generate").click().run()
    assert not at.exception
    at.selectbox(key="analysis_day").select("Tất cả").run()
    weekday_chart = chart_spec(at, "movement_detail")
    assert len(weekday_chart["data"][0]["x"]) == 25
    assert not any("Thứ Bảy" in label for label in weekday_chart["data"][0]["x"])
    assert len(chart_spec(at, "weekly_heatmap")["data"][0]["x"]) == 5


def test_grid_day_filter_does_not_change_schedule_or_metrics():
    at = app()
    at.button(key="generate").click().run()
    before = at.session_state.run.cp_sat
    at.selectbox(key="day_filter").select("Sat").run()
    assert not at.exception
    assert at.session_state.run.cp_sat == before
    assert "Thứ Bảy" in at.get("html")[0].proto.body
    assert "Thứ Hai" not in at.get("html")[0].proto.body
    assert any("Không có buổi học" in caption.value for caption in at.caption)


def test_room_filter_changes_only_visible_assignments_and_keeps_full_export():
    import re
    at = app()
    load_sample_ui(at, "Congestion")
    at.button(key="generate").click().run()
    before = at.session_state.run.cp_sat
    assert at.selectbox(key="room_filter").value == "Tất cả"
    assert at.get("html")[0].proto.body.count('class="cf-class"') == 24
    selected = before.assignments[0].room_id
    at.selectbox(key="room_filter").select(selected).run()
    assert not at.exception
    grid = at.get("html")[0].proto.body
    expected = [a for a in before.assignments if a.room_id == selected]
    assert grid.count('class="cf-class"') == len(expected)
    assert set(re.findall(r'data-room="([^"]*)"', grid)) == {selected}
    at.selectbox(key="room_filter").select("Tất cả").run()
    assert not at.exception
    assert at.get("html")[0].proto.body.count('class="cf-class"') == 24
    assert at.session_state.run.cp_sat == before
    comparison = chart_spec(at, "comparison_chart")
    assert comparison["data"][1]["x"][0] == before.metrics.peak_movement
    heatmap = chart_spec(at, "weekly_heatmap")
    assert max(max(row) for row in heatmap["data"][0]["z"]) == before.metrics.peak_movement


def test_existing_browser_session_is_preserved_after_typed_result_refactor():
    from application.models import ComparisonRun, PolicyExperiment, ScheduleConfig, ScheduleResult
    from application.sample_data import load_sample
    dataset, config = load_sample(), ScheduleConfig()
    greedy, cp_sat = ScheduleResult("Greedy", "FAILED"), ScheduleResult("CP-SAT", "UNKNOWN")
    at = AppTest.from_file("../app.py", default_timeout=20)
    at.session_state.dataset = dataset
    at.session_state.run = (dataset, config, greedy, cp_sat)
    at.session_state.what_if = (dataset, config, (0, 3, 10), [(p, cp_sat) for p in (0, 3, 10)])
    at.run()
    assert not at.exception
    assert isinstance(at.session_state.run, ComparisonRun)
    assert isinstance(at.session_state.what_if, PolicyExperiment)
    assert at.session_state.run.cp_sat.status == "UNKNOWN"
    assert len(at.session_state.what_if.results) == 3
