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


def render_shell() -> None:
    with st.sidebar:
        st.subheader("Giờ học")
        for session, (start, end) in TIMES.items():
            st.write(f"Ca {session}　{start} – {end}")
        st.caption("Áp dụng từ thứ Hai đến thứ Bảy.")
        with st.expander("Cách tính lượt di chuyển"):
            st.write("Mỗi lượt đăng ký được tính một lần khi vào ca và một lần khi rời ca. Một sinh viên học nhiều ca có thể được tính nhiều lượt.")
            st.caption("Mô hình dùng lịch lớp và sức chứa phòng. Lịch cá nhân, giảng viên và lưu lượng đo tại cổng nằm ngoài phạm vi tính.")

    st.title("CampusFlow AI")
