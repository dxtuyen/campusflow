"""Schedule controls, filters and exports; no solver formulation here."""

import streamlit as st

from application.data_io import schedule_excel, timetable_frame
from application.models import DAY_LABELS, Dataset, ScheduleConfig
from application.presentation import dataset_label, timetable_grid_html
from application.workflows import run_comparison
from application.ui.components import show_metrics, show_result_status
from application.ui.state import current_run, save_run


def render_schedule_tab(dataset: Dataset, errors: list[str]) -> ScheduleConfig:
    title, settings, action = st.columns([3, 1, 1], vertical_alignment="center")
    title.subheader("Thời khóa biểu")
    title.caption(dataset_label(dataset.name))
    with settings.popover("Chính sách", width="stretch"):
        policy = st.radio("Ngày học", ["Saturday Allowed", "Weekdays Only"], format_func=lambda p: {"Saturday Allowed": "Cho phép thứ Bảy", "Weekdays Only": "Chỉ học ngày thường"}[p], horizontal=True, key="policy")
        penalty = st.select_slider("Ưu tiên tránh thứ Bảy", options=[0, 1, 3, 5, 10], value=3,
                                  format_func=lambda n: {0: "Không ưu tiên", 1: "Nhẹ", 3: "Vừa", 5: "Cao", 10: "Rất cao"}[n],
                                  disabled=policy == "Weekdays Only", key="penalty", help="Mức phạt λ tương ứng 0, 1, 3, 5, 10. Mức cao ưu tiên ít lượt học thứ Bảy hơn.")
        seconds = st.number_input("Giới hạn giải (giây)", min_value=1, max_value=60, value=10, key="seconds")
    config = ScheduleConfig(policy == "Saturday Allowed", penalty, float(seconds))
    with action:
        generate = st.button("Tạo lịch", type="primary", disabled=bool(errors), key="generate", width="stretch")
    if generate:
        with st.spinner("Đang xếp các buổi học và kiểm tra lịch…"):
            save_run(run_comparison(dataset, config))
        st.rerun()

    run = current_run(dataset, config)
    if run is None:
        if "run" in st.session_state:
            st.info("Chính sách đã thay đổi. Hãy tạo lại lịch.")
    else:
        greedy, cp_sat = run.greedy, run.cp_sat
        algorithm = st.session_state.get("view_algorithm", "CP-SAT")
        schedule_view = st.session_state.get("schedule_view", "Lưới tuần")
        result = cp_sat if algorithm == "CP-SAT" else greedy
        summary = st.container()
        controls = st.container(horizontal=True, vertical_alignment="bottom")
        if result.complete:
            summary.markdown(
                f"**Đã xếp {len(result.assignments)}/{len(dataset.classes)} buổi** · "
                f"Cao điểm {result.metrics.peak_movement:,} lượt · {result.metrics.saturday_classes} buổi thứ Bảy"
            )
            if algorithm == "Greedy" and not cp_sat.complete:
                summary.warning("Đang xem lịch Greedy vì CP-SAT chưa xếp đủ.")
            elif result.status == "FEASIBLE" and result.algorithm == "CP-SAT":
                summary.caption("CP-SAT đã xếp đủ lịch, chưa chứng minh tối ưu.")
            frame = timetable_frame(result, dataset)
            rooms = sorted(r.room_id for r in dataset.rooms)
            room = controls.selectbox("Phòng đang xem", ["Tất cả", *rooms],
                               format_func=lambda r: "Tất cả phòng" if r == "Tất cả" else f"Phòng {r}", key="room_filter", width=160)
            days = ["Tất cả", *config.days]
            headers = st.context.headers
            phone = headers.get("Sec-CH-UA-Mobile") == "?1" or "mobile" in headers.get("User-Agent", "").lower()
            first_day = frame.iloc[0].day if phone else "Tất cả"
            day = controls.selectbox("Ngày trên lịch", days, index=days.index(first_day), format_func=lambda d: "Cả tuần" if d == "Tất cả" else DAY_LABELS[d], key="day_filter", width=160)
            visible = frame
            if room != "Tất cả":
                visible = visible[visible.room_id == room]
            if day != "Tất cả":
                visible = visible[visible.day == day]
            if visible.empty:
                st.caption("Không có buổi học trong phòng/ngày đã chọn.")
            elif room != "Tất cả" or day != "Tất cả":
                st.caption(f"Đang xem {len(visible)}/{len(frame)} buổi")
            if schedule_view == "Lưới tuần":
                st.html(timetable_grid_html(visible, config.days if day == "Tất cả" else (day,), rooms))
            else:
                display = visible.copy()
                display["day"] = display["day"].map(DAY_LABELS)
                st.dataframe(display, hide_index=True, width="stretch", column_config={
                    "class_id": "Mã buổi học", "class_name": "Tên buổi học", "students": "Lượt đăng ký", "day": "Ngày",
                    "session_id": "Ca", "start_time": "Bắt đầu", "end_time": "Kết thúc", "room_id": "Phòng",
                })
        else:
            show_result_status(result)
        with controls.popover("Cách xem"):
            st.radio("Thuật toán", ["CP-SAT", "Greedy"], horizontal=True, key="view_algorithm")
            st.radio("Cách xem", ["Lưới tuần", "Bảng chi tiết"], horizontal=True, key="schedule_view")
        if result.complete:
            with controls.popover("Tải lịch"):
                st.download_button("Tải toàn bộ lịch Excel", schedule_excel(result, dataset, config), "campusflow-schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
                st.download_button("Tải toàn bộ lịch CSV", frame.to_csv(index=False).encode("utf-8-sig"), "campusflow-schedule.csv", mime="text/csv", width="stretch")
        with st.expander("Chi tiết bộ giải và chỉ số"):
            a, b = st.columns(2)
            with a:
                show_result_status(cp_sat)
            with b:
                show_result_status(greedy)
            if result.complete:
                show_metrics(result)
                st.write(f"J = P + λ × N_Sat · λ = {config.saturday_penalty}. Mục tiêu J = {result.metrics.objective:,}.")
                if result.best_bound is not None:
                    st.write(f"Cận dưới của mục tiêu: {result.best_bound:g}.")
    return config
