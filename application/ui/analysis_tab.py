"""Visual analysis and policy experiments using shared workflow results."""

import pandas as pd
import streamlit as st

from application.analysis import comparison_frame, what_if_frame
from application.models import DAY_LABELS, Dataset, ScheduleConfig
from application.presentation import STATUS_LABELS, WINDOW_LABELS, WINDOW_TIMES, busiest_day, comparison_figure, comparison_summary, movement_figure, movement_heatmap, visual_comparison_summary, what_if_summary
from application.workflows import run_policy_experiment
from application.ui.state import current_experiment, current_run, save_experiment

PRIORITY_LABELS = {0: "Không ưu tiên", 1: "Ưu tiên nhẹ", 3: "Ưu tiên vừa", 5: "Ưu tiên cao", 10: "Ưu tiên rất cao"}


def render_analysis_tab(dataset: Dataset, config: ScheduleConfig, errors: list[str]) -> None:
    run = current_run(dataset, config)
    st.subheader("Cao điểm di chuyển trong tuần")
    st.caption("Đọc bản đồ màu để tìm khoảng nhiều lượt nhất; xem thanh bên cạnh để so hai cách xếp. Đây là lượt đăng ký lớp, không phải số người đo tại cổng.")
    if run is None:
        st.info("Tạo lịch trong tab Lịch học để xem bản đồ cao điểm và so sánh hai cách xếp.")
    else:
        greedy, cp_sat = run.greedy, run.cp_sat
        available = {r.algorithm: r for r in (cp_sat, greedy) if r.complete}
        if available:
            selected = st.session_state.get("analysis_algorithm")
            if selected not in available:
                selected = next(iter(available))
                st.session_state.analysis_algorithm = selected
            analyzed = available[selected]
            m = analyzed.metrics
            peak = next(w for w in m.windows if w.total == m.peak_movement)
            overview, comparison_panel = st.columns([2, 1], gap="large")
            with overview:
                st.metric("Cao điểm toàn tuần", f"{m.peak_movement:,} lượt")
                st.caption(f"{DAY_LABELS[peak.day]} · {WINDOW_TIMES[peak.window]} · Lịch {selected} · Một trong các khoảng đạt đỉnh")
                st.plotly_chart(movement_heatmap(m, config.days), width="stretch", key="weekly_heatmap")
                st.caption("Màu đậm hơn = nhiều lượt hơn trong lịch này. ★ là các ô cao nhất. Màu không biểu thị ngưỡng nguy hiểm.")
            with comparison_panel:
                st.markdown("**So với lịch đối chiếu**")
                st.info(visual_comparison_summary(greedy, cp_sat))
                if greedy.complete and cp_sat.complete:
                    st.plotly_chart(comparison_figure(greedy, cp_sat), width="stretch", key="comparison_chart")
                if cp_sat.status == "FEASIBLE":
                    st.caption("Lịch CP-SAT hợp lệ, chưa chứng minh tối ưu.")
            with st.expander("Xem lượt ra và lượt vào trong một ngày"):
                selected = st.selectbox("Phân tích lịch", list(available), key="analysis_algorithm")
                chart_days = ["Tất cả", *config.days]
                chart_day = st.selectbox("Ngày trên biểu đồ", chart_days, index=chart_days.index(busiest_day(m, config.days)),
                                         format_func=lambda d: "Cả tuần" if d == "Tất cả" else DAY_LABELS[d], key="analysis_day")
                chosen_day = None if chart_day == "Tất cả" else chart_day
                st.plotly_chart(movement_figure(m, chosen_day, config.days), width="stretch", key="movement_detail")
                filtered = [w for w in m.windows if w.day in config.days and (chosen_day is None or w.day == chosen_day)]
                if chosen_day:
                    st.caption(f"Đỉnh trong {DAY_LABELS[chosen_day]}: {max(w.total for w in filtered):,} lượt · Đỉnh toàn tuần: {m.peak_movement:,} lượt.")
                st.caption("Mỗi cột = lượt rời ca trước + lượt đến ca sau. Đây là tổng trong một khoảng, không phải số người xuất hiện cùng một giây.")
                st.dataframe(pd.DataFrame([{"Ngày": DAY_LABELS[w.day], "Cửa sổ": WINDOW_LABELS[w.window], "Lượt rời": w.departures, "Lượt đến": w.arrivals, "Tổng lượt": w.total} for w in filtered]), hide_index=True, width="stretch")
        else:
            st.warning("Chưa có lịch hoàn chỉnh để vẽ biểu đồ. Xem trạng thái ở tab Lịch học hoặc bảng chi tiết bên dưới.")
        with st.expander("Bảng so sánh và công thức chi tiết"):
            st.write(comparison_summary(greedy, cp_sat))
            st.dataframe(comparison_frame([greedy, cp_sat]).rename(columns={"Best bound": "Cận dưới"}), hide_index=True, width="stretch")
            st.caption("J = P + λ × N_Sat. Chỉ so sánh J của hai thuật toán trên cùng dữ liệu và cùng λ. Lịch còn thiếu không được dùng để so chất lượng.")

    st.divider()
    st.markdown("### Nếu hạn chế học thứ Bảy thì sao?")
    st.caption("Chạy thử ba mức ưu tiên để nhìn mức cao điểm và số lượt học thứ Bảy thay đổi thế nào.")
    with st.expander("Điều chỉnh ba mức ưu tiên"):
        levels = st.multiselect("Chọn đúng 3 mức λ", [0, 1, 3, 5, 10], default=[0, 3, 10], key="what_if_levels")
        st.caption("0: không ưu tiên tránh thứ Bảy · 3: ưu tiên vừa · 10: ưu tiên rất cao.")
    if not config.allow_saturday:
        st.caption("Đang chỉ học ngày thường: lượt thứ Bảy luôn bằng 0; thay λ không đổi hàm mục tiêu.")
    if st.button("So sánh ba mức phạt", disabled=bool(errors) or len(levels) != 3, key="what_if_button"):
        with st.spinner(f"Đang thử ba chính sách, tối đa {3 * config.time_limit_seconds:g} giây tìm kiếm…"):
            save_experiment(run_policy_experiment(dataset, config, tuple(sorted(levels))))
    experiment = current_experiment(dataset, config, tuple(sorted(levels)))
    if experiment is not None:
        st.write(what_if_summary(experiment.results))
        for column, (level, solution) in zip(st.columns(3), experiment.results):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{PRIORITY_LABELS[level]}**")
                    st.caption(f"Mức phạt λ = {level}")
                    if solution.complete:
                        st.metric("Lượt cao điểm", f"{solution.metrics.peak_movement:,}")
                        st.metric("Lượt học thứ Bảy", f"{solution.metrics.saturday_enrollment:,}")
                    st.caption(STATUS_LABELS.get(solution.status, solution.status))
                    if solution.status == "FEASIBLE":
                        st.caption("Chưa chứng minh tối ưu.")
        with st.expander("Số liệu đầy đủ của ba lần giải"):
            st.dataframe(what_if_frame(experiment.results).rename(columns={"Best bound": "Cận dưới"}), hide_index=True, width="stretch")
            st.caption("J đổi công thức khi λ đổi; so các chính sách bằng cao điểm và lượt thứ Bảy. UNKNOWN chưa kết luận, không có nghĩa vô nghiệm.")
