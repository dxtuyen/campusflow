"""Shared Streamlit chrome and result components."""

import streamlit as st

from application.models import ScheduleResult, TIMES
from application.presentation import STATUS_LABELS


def show_result_status(result: ScheduleResult) -> None:
    message = f"{result.algorithm} · {STATUS_LABELS.get(result.status, result.status)} ({result.status}) · {result.runtime_seconds:.2f} giây"
    if result.complete:
        st.success(message)
    elif result.status == "UNKNOWN":
        st.warning(message)
    else:
        st.error(message)
    for warning in result.warnings:
        st.warning(warning.replace("Greedy failed to find complete schedule:", "Greedy chưa xếp đủ lịch:"))
    if result.violations:
        with st.expander(f"Chi tiết kiểm chứng: {len(result.violations)} lỗi"):
            for violation in result.violations:
                st.write(violation)


def show_metrics(result: ScheduleResult) -> None:
    m = result.metrics
    cols = st.columns(4)
    cols[0].metric("Đỉnh chuyển ca · P", f"{m.peak_movement:,}", help="Lượt đăng ký lớp ra + vào trong một cửa sổ chuyển ca.")
    cols[1].metric("Lượt thứ Bảy · N_Sat", f"{m.saturday_enrollment:,}")
    cols[2].metric("Mục tiêu · J", f"{m.objective:,}")
    cols[3].metric("Lấp đầy phòng", f"{m.room_utilization:.1%}", help="Tổng lượt đăng ký / tổng sức chứa phòng ở các buổi được xếp.")


def show_overview(result: ScheduleResult) -> None:
    a, b, c = st.columns(3)
    a.metric("Buổi học đã xếp", len(result.assignments))
    b.metric("Lượt di chuyển cao nhất", f"{result.metrics.peak_movement:,}", help="Lượt ra + vào trong một khoảng thời gian, tính trên toàn tuần.")
    c.metric("Buổi học thứ Bảy", result.metrics.saturday_classes)


def render_shell() -> None:
    with st.sidebar:
        st.markdown("### 🌿 CampusFlow AI")
        st.caption("PHÂN PHÒNG & ĐIỀU PHỐI CA HỌC")
        st.divider()
        st.markdown("**Một tuần mẫu. Bốn ca cố định.**")
        for session, (start, end) in TIMES.items():
            st.write(f"Ca {session}　{start} — {end}")
        st.caption("150 phút / ca · Chủ nhật luôn nghỉ")
        st.divider()
        st.markdown("**Bắt đầu trong 3 bước**")
        st.write("1. Chọn dữ liệu hoặc tải Excel.\n2. Chọn chính sách, tạo và so sánh lịch.\n3. Đọc biểu đồ và thử các mức λ.")
        with st.expander("Mô hình này đo gì?"):
            st.write("Mỗi bản ghi là một buổi học trong tuần. Các chỉ số đếm lượt đăng ký lớp, không phải số sinh viên duy nhất.")
            st.write("Nhiều lớp có thể học cùng ca ở các phòng khác nhau; tải của ca cộng lượt đăng ký từ tất cả các lớp đó.")
            st.write("Không xét lịch cá nhân, giảng viên, đường đi hay sức chứa cổng. Một người học nhiều ca có thể bị đếm nhiều lượt.")
            st.caption("Đây là chỉ số đại diện từ lịch lớp, không phải dữ liệu đo ùn tắc thực tế.")

    st.title("CampusFlow AI")
    st.caption("Chọn dữ liệu → Tạo lịch → Xem cao điểm di chuyển")
