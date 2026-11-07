"""Schedule controls, filters and exports; no solver formulation here."""

import streamlit as st

from application.data_io import schedule_excel, timetable_frame
from application.models import DAY_LABELS, Dataset, ScheduleConfig
from application.presentation import dataset_label, timetable_grid_html
from application.workflows import run_comparison
from application.ui.components import show_metrics, show_overview, show_result_status
from application.ui.state import current_run, save_run


def render_schedule_tab(dataset: Dataset, errors: list[str]) -> ScheduleConfig:
    title, action = st.columns([3, 1])
    with title:
        st.subheader("Thời khóa biểu toàn trường")
        st.caption(dataset_label(dataset.name))
        st.caption("Một ca có thể có nhiều lớp ở các phòng khác nhau. Mỗi phòng chỉ nhận một lớp trong cùng ngày và ca.")
    with st.expander("Chính sách xếp lịch", expanded="run" not in st.session_state):
        a, b, c = st.columns([2, 2, 1])
        policy = a.radio("Ngày học", ["Saturday Allowed", "Weekdays Only"], format_func=lambda p: {"Saturday Allowed": "Cho phép thứ Bảy", "Weekdays Only": "Chỉ học ngày thường"}[p], horizontal=True, key="policy")
        penalty = b.select_slider("Ưu tiên tránh thứ Bảy", options=[0, 1, 3, 5, 10], value=3,
                                  format_func=lambda n: {0: "Không ưu tiên", 1: "Nhẹ", 3: "Vừa", 5: "Cao", 10: "Rất cao"}[n],
                                  disabled=policy == "Weekdays Only", key="penalty", help="Mức phạt λ tương ứng 0, 1, 3, 5, 10. Mức cao ưu tiên ít lượt học thứ Bảy hơn.")
        seconds = c.number_input("Giới hạn giải (giây)", min_value=1, max_value=60, value=10, key="seconds")
    config = ScheduleConfig(policy == "Saturday Allowed", penalty, float(seconds))
    with action:
        generate = st.button("Tạo và so sánh lịch", type="primary", disabled=bool(errors), key="generate", width="stretch")
    if generate:
        with st.spinner("Đang xếp các buổi học và kiểm tra lịch…"):
            save_run(run_comparison(dataset, config))
        st.rerun()

    run = current_run(dataset, config)
    current = run is not None
    if not current:
        st.info("Nhấn Tạo và so sánh lịch để xem các buổi học trên lịch." if "run" not in st.session_state else "Dữ liệu hoặc chính sách đã thay đổi. Nhấn Tạo và so sánh lịch để cập nhật kết quả.")
    else:
        greedy, cp_sat = run.greedy, run.cp_sat
        algorithm = st.session_state.get("view_algorithm", "CP-SAT")
        schedule_view = st.session_state.get("schedule_view", "Lưới tuần")
        result = cp_sat if algorithm == "CP-SAT" else greedy
        if result.complete:
            st.caption(f"✓ Đã xếp đủ {len(result.assignments)}/{len(dataset.classes)} buổi học. Đã kiểm chứng phòng, sức chứa và ca học.")
            if algorithm == "Greedy" and not cp_sat.complete:
                st.warning("Đang xem lịch Greedy hợp lệ; CP-SAT chưa trả về lịch hoàn chỉnh. Xem trạng thái trong chi tiết bộ giải.")
            elif result.status == "FEASIBLE" and result.algorithm == "CP-SAT":
                st.caption("CP-SAT đã tìm được lịch hợp lệ; chưa chứng minh đây là lịch tối ưu.")
            show_overview(result)
            frame = timetable_frame(result, dataset)
            rooms = sorted(r.room_id for r in dataset.rooms)
            a, b = st.columns(2)
            room = a.selectbox("Phòng đang xem", ["Tất cả", *rooms],
                               format_func=lambda r: "Tất cả phòng" if r == "Tất cả" else f"Phòng {r}", key="room_filter")
            day = b.selectbox("Ngày trên lịch", ["Tất cả", *config.days], format_func=lambda d: "Cả tuần" if d == "Tất cả" else DAY_LABELS[d], key="day_filter")
            visible = frame
            if room != "Tất cả":
                visible = visible[visible.room_id == room]
            if day != "Tất cả":
                visible = visible[visible.day == day]
            st.caption(f"Đang hiển thị {len(visible)}/{len(frame)} buổi · Mỗi thẻ là một buổi học, màu thẻ phân biệt phòng · Các chỉ số phía trên tính cho toàn tuần.")
            if schedule_view == "Lưới tuần":
                st.html(timetable_grid_html(visible, config.days if day == "Tất cả" else (day,), rooms))
            else:
                display = visible.copy()
                display["day"] = display["day"].map(DAY_LABELS)
                st.dataframe(display, hide_index=True, width="stretch", column_config={
                    "class_id": "Mã buổi học", "class_name": "Tên buổi học", "students": "Lượt đăng ký", "day": "Ngày",
                    "session_id": "Ca", "start_time": "Bắt đầu", "end_time": "Kết thúc", "room_id": "Phòng",
                })
            if visible.empty:
                st.caption("Không có buổi học trong phòng/ngày đang chọn.")
            st.caption("Ô — là ca trống. Thứ Bảy có nền xanh nhạt. Chọn Tất cả phòng để xem toàn bộ lịch.")
            a, b = st.columns(2)
            a.download_button("↓ Tải lịch Excel · kèm chỉ số", schedule_excel(result, dataset, config), "campusflow-schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
            b.download_button("↓ Tải toàn bộ lịch CSV", frame.to_csv(index=False).encode("utf-8-sig"), "campusflow-schedule.csv", mime="text/csv", width="stretch")
            st.caption("File tải về chứa toàn bộ lịch, kể cả khi đang lọc phòng hoặc ngày.")
        else:
            show_result_status(result)
        with st.expander("Đổi cách xem và thuật toán"):
            a, b = st.columns(2)
            a.radio("Thuật toán", ["CP-SAT", "Greedy"], horizontal=True, key="view_algorithm")
            b.radio("Cách xem", ["Lưới tuần", "Bảng chi tiết"], horizontal=True, key="schedule_view")
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
                st.caption("OPTIMAL: đã chứng minh tối ưu theo mô hình. FEASIBLE: có lịch hợp lệ, chưa chứng minh tối ưu. Ghế dư chưa được tối ưu riêng.")
    return config
