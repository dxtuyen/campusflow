"""Data import, preview and optional synthetic input controls."""

from io import BytesIO

import streamlit as st

from application.data_io import dataset_excel, dataset_frames, read_dataset
from application.models import Dataset
from application.presentation import dataset_label
from application.sample_data import SAMPLE_DESCRIPTIONS, SAMPLE_NAMES, load_sample
from application.synthetic_data import generate_synthetic_dataset
from application.validation import DatasetError, validate_inputs
from application.ui.state import use_dataset


def render_data_tab() -> tuple[Dataset, list[str]]:
    st.subheader("Dữ liệu cho tuần học")
    left, right = st.columns(2, gap="large")
    with left:
        with st.form("sample_form", border=True):
            st.markdown("**Khám phá với dữ liệu mẫu**")
            sample_name = st.selectbox("Bộ dữ liệu mẫu", SAMPLE_NAMES, format_func=dataset_label, key="sample_choice")
            st.caption("Bốn bộ cố định, có thể tái tạo. Chọn bộ rồi nhấn tải để thay dữ liệu đang dùng.")
            if st.form_submit_button("Tải bộ dữ liệu mẫu", key="sample_load", width="stretch"):
                use_dataset(load_sample(sample_name))
        st.caption(SAMPLE_DESCRIPTIONS.get(st.session_state.dataset.name, "Dữ liệu đang dùng hiển thị bên dưới."))
    with right:
        with st.form("upload_form", border=True):
            st.markdown("**Dùng dữ liệu của bạn**")
            uploaded = st.file_uploader("Excel với hai sheet Classes và Rooms", type=["xlsx"])
            if st.form_submit_button("Dùng file Excel", width="stretch"):
                if uploaded is None:
                    st.session_state.import_errors = ["Hãy chọn một file .xlsx trước."]
                else:
                    try:
                        use_dataset(read_dataset(BytesIO(uploaded.getvalue()), uploaded.name))
                    except DatasetError as exc:
                        st.session_state.import_errors = exc.errors
        st.download_button("↓ Tải Excel mẫu (.xlsx)", dataset_excel(load_sample()), "campusflow-template.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    with st.expander("Cách chuẩn bị file Excel"):
        st.markdown("Một file **.xlsx**, giữ đúng tên hai sheet và tên cột trong file mẫu:")
        st.markdown("- **Classes:** `class_id` (mã buổi học), `class_name` (tên), `students` (lượt đăng ký). Mỗi dòng là một buổi, chiếm một ca.\n- **Rooms:** `room_id` (mã phòng), `capacity` (sức chứa). Mã không trùng; số người và sức chứa là số nguyên dương.\n- **Tùy chọn:** `allowed_days`, ví dụ `Mon,Tue,Fri`; `allowed_sessions`, ví dụ `1,2,3`. Để trống sẽ cho phép Mon–Sat và ca 1–4. Chủ nhật luôn bị cấm.")
    if st.session_state.get("import_errors"):
        st.error("Không thể dùng file Excel. Dữ liệu đang dùng được giữ lại; sửa các lỗi sau rồi tải lại.")
        for error in st.session_state.import_errors:
            st.write(f"• {error}")
    dataset = st.session_state.dataset
    st.divider()
    st.markdown(f"**Đang dùng: {dataset_label(dataset.name)}**")
    cols = st.columns(3)
    cols[0].metric("Buổi học cần xếp", len(dataset.classes))
    cols[1].metric("Phòng học", len(dataset.rooms))
    cols[2].metric("Tổng lượt đăng ký lớp", f"{sum(c.students for c in dataset.classes):,}")
    errors = validate_inputs(dataset.classes, dataset.rooms)
    if errors:
        for error in errors:
            st.error(error)
    else:
        st.success("Đúng cấu trúc dữ liệu, ngày, ca và sức chứa từng lớp. Chạy bộ giải để kiểm tra có xếp đủ lịch hay không.")
    classes_frame, rooms_frame = dataset_frames(dataset)
    with st.expander("Xem danh sách buổi học và phòng"):
        a, b = st.columns([3, 1], gap="large")
        with a:
            st.markdown("**Classes · Buổi học**")
            st.dataframe(classes_frame, hide_index=True, width="stretch")
        with b:
            st.markdown("**Rooms · Phòng học**")
            st.dataframe(rooms_frame, hide_index=True, width="stretch")
        st.caption("allowed_days trống → Mon–Sat; allowed_sessions trống → ca 1–4. Mỗi class_id là một buổi học, chiếm đúng một ca.")
    st.info("Dữ liệu đã sẵn sàng. Mở tab Lịch học và nhấn Tạo và so sánh lịch." if not errors else "Sửa dữ liệu trước khi tạo lịch.")
    st.download_button("↓ Tải dữ liệu đang dùng", dataset_excel(dataset), "campusflow-input.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.expander("Sinh dữ liệu giả lập"):
        st.caption("Tạo dữ liệu giả lập cho thực nghiệm; không phải dữ liệu thật của nhà trường. Sinh preview trước, sau đó chọn dùng cho luồng lập lịch.")
        with st.form("synthetic_form"):
            g1, g2, g3 = st.columns(3)
            num_classes = g1.number_input("Số buổi học", min_value=10, max_value=100, value=30, key="synthetic_classes")
            num_rooms = g2.number_input("Số phòng", min_value=2, max_value=20, value=6, key="synthetic_rooms")
            seed = g3.number_input("Số khởi tạo (seed)", value=42, step=1, key="synthetic_seed")
            difficulty = st.selectbox("Độ khó ràng buộc", ["constrained", "easy"], format_func=lambda d: {"constrained": "Nhiều giới hạn ngày/ca", "easy": "Ít giới hạn ngày/ca"}[d], key="synthetic_difficulty")
            guarantee = st.checkbox("Dựng và kiểm chứng lịch chứng minh có nghiệm", value=False, key="synthetic_guarantee")
            if st.form_submit_button("Sinh dữ liệu", key="synthetic_generate"):
                try:
                    generated = generate_synthetic_dataset(num_classes, num_rooms, seed, difficulty, guarantee)
                    st.session_state.synthetic = generated
                    st.session_state.pop("synthetic_error", None)
                except ValueError as exc:
                    st.session_state.synthetic_error = str(exc)
        if st.session_state.get("synthetic_error"):
            st.error(st.session_state.synthetic_error)
        if "synthetic" in st.session_state:
            generated = st.session_state.synthetic
            st.write(f"Xem trước: {len(generated.dataset.classes)} buổi học · {len(generated.dataset.rooms)} phòng · {dataset_label(generated.dataset.name)}")
            if generated.guaranteed_feasible:
                st.success("Dữ liệu đúng cấu trúc. Đã kiểm chứng có lịch khi cho phép thứ Bảy; chưa tối ưu. Nếu chỉ học ngày thường, cần giải lại.")
            else:
                st.info("Dữ liệu đúng cấu trúc. Chưa kiểm tra tính khả thi; bộ dữ liệu có thể vô nghiệm.")
            gc, gr = dataset_frames(generated.dataset)
            st.dataframe(gc, hide_index=True, width="stretch")
            st.dataframe(gr, hide_index=True, width="stretch")
            g1, g2 = st.columns(2)
            if g1.button("Dùng dữ liệu này", key="synthetic_use", width="stretch"):
                use_dataset(generated.dataset)
                st.rerun()
            g2.download_button("↓ Tải Excel vừa sinh", dataset_excel(generated.dataset), "campusflow-generated.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
    return dataset, errors
