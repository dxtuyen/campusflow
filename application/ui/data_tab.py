"""Data import, preview and optional synthetic input controls."""

from io import BytesIO

import streamlit as st

from application.data_io import dataset_excel, dataset_frames, read_dataset
from application.models import Dataset
from application.presentation import dataset_label
from application.sample_data import SAMPLE_NAMES, load_sample
from application.synthetic_data import MAX_ROOMS, MIN_ROOMS, generate_synthetic_dataset
from application.validation import DatasetError, validate_inputs
from application.ui.state import use_dataset


def _open_schedule() -> None:
    st.session_state.main_tab = "Lịch học"


def render_data_tab() -> tuple[Dataset, list[str]]:
    active_dataset = st.container()
    excel_tab, sample_tab, synthetic_tab = st.tabs(["Nhập Excel", "Bộ mẫu", "Giả lập"])
    with sample_tab:
        with st.form("sample_form", border=False):
            sample_name = st.selectbox(
                "Bộ dữ liệu mẫu",
                SAMPLE_NAMES,
                format_func=dataset_label,
                key="sample_choice",
            )
            if st.form_submit_button(
                "Dùng bộ mẫu", key="sample_load"
            ):
                use_dataset(load_sample(sample_name))
    with excel_tab:
        with st.form("upload_form", border=False):
            uploaded = st.file_uploader(
                "Nhập file Excel (.xlsx)", type=["xlsx"]
            )
            if st.form_submit_button("Dùng file Excel"):
                if uploaded is None:
                    st.session_state.import_errors = ["Hãy chọn một file .xlsx trước."]
                else:
                    try:
                        use_dataset(
                            read_dataset(BytesIO(uploaded.getvalue()), uploaded.name)
                        )
                    except DatasetError as exc:
                        st.session_state.import_errors = exc.errors
        if st.session_state.get("import_errors"):
            st.error(
                "Không thể dùng file Excel. Hãy sửa các ô được báo rồi tải lại."
            )
            for error in st.session_state.import_errors:
                st.write(f"• {error}")
        with st.expander("Cách chuẩn bị file Excel"):
            st.download_button(
                "Tải Excel mẫu",
                dataset_excel(load_sample()),
                "campusflow-template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
            st.markdown(
                "- **Classes:** `class_id` (mã buổi học), `class_name` (tên), `students` (lượt đăng ký). Mỗi dòng là một buổi, chiếm một ca.\n- **Rooms:** `room_id` (mã phòng), `capacity` (sức chứa). Mã không trùng; số người và sức chứa là số nguyên dương.\n- **Tùy chọn:** `allowed_days`, ví dụ `Mon,Tue,Fri`; `allowed_sessions`, ví dụ `1,2,3`. Để trống sẽ cho phép Mon–Sat và ca 1–4. Chủ nhật luôn bị cấm."
            )
    dataset = st.session_state.dataset
    errors = validate_inputs(dataset.classes, dataset.rooms)
    with active_dataset:
        summary, action = st.columns([3, 1], vertical_alignment="center")
        summary.markdown(f"**Đang dùng: {dataset_label(dataset.name)}**")
        summary.caption(f"{len(dataset.classes)} buổi · {len(dataset.rooms)} phòng · "
                        + ("Cần sửa dữ liệu" if errors else "Sẵn sàng xếp lịch"))
        action.button("Sang lịch học", on_click=_open_schedule, disabled=bool(errors), type="primary")
    for error in errors:
        st.error(error)
    classes_frame, rooms_frame = dataset_frames(dataset)
    with st.expander("Xem danh sách buổi học và phòng"):
        a, b = st.columns([3, 1], gap="large")
        with a:
            st.markdown("**Classes · Buổi học**")
            st.dataframe(classes_frame, hide_index=True, width="stretch")
        with b:
            st.markdown("**Rooms · Phòng học**")
            st.dataframe(rooms_frame, hide_index=True, width="stretch")
        st.caption(f"Tổng lượt đăng ký: {sum(c.students for c in dataset.classes):,}")
        st.download_button("Tải dữ liệu đang dùng", dataset_excel(dataset), "campusflow-input.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with synthetic_tab:
        with st.form("synthetic_form", border=False):
            g1, g2, g3 = st.columns(3)
            num_classes = g1.number_input(
                "Số buổi học",
                min_value=10,
                max_value=100,
                value=30,
                key="synthetic_classes",
            )
            num_rooms = g2.number_input(
                "Số phòng", min_value=MIN_ROOMS, max_value=MAX_ROOMS, value=6, key="synthetic_rooms"
            )
            seed = g3.number_input(
                "Số khởi tạo (seed)", value=42, step=1, key="synthetic_seed"
            )
            difficulty = st.selectbox(
                "Độ khó ràng buộc",
                ["constrained", "easy"],
                format_func=lambda d: {
                    "constrained": "Nhiều giới hạn ngày/ca",
                    "easy": "Ít giới hạn ngày/ca",
                }[d],
                key="synthetic_difficulty",
            )
            guarantee = st.checkbox(
                "Bảo đảm xếp được lịch khi cho phép thứ Bảy",
                value=False,
                key="synthetic_guarantee",
            )
            if st.form_submit_button("Sinh dữ liệu", key="synthetic_generate"):
                try:
                    generated = generate_synthetic_dataset(
                        num_classes, num_rooms, seed, difficulty, guarantee
                    )
                    st.session_state.synthetic = generated
                    st.session_state.pop("synthetic_error", None)
                except ValueError as exc:
                    st.session_state.pop("synthetic", None)
                    st.session_state.synthetic_error = str(exc)
        if st.session_state.get("synthetic_error"):
            st.error(st.session_state.synthetic_error)
        if "synthetic" in st.session_state:
            generated = st.session_state.synthetic
            st.write(
                f"Xem trước: {len(generated.dataset.classes)} buổi học · {len(generated.dataset.rooms)} phòng · {dataset_label(generated.dataset.name)}"
            )
            if generated.guaranteed_feasible:
                st.success(
                    "Đã kiểm chứng có lịch khi cho phép thứ Bảy."
                )
            else:
                st.info(
                    "Chưa kiểm tra khả năng xếp lịch."
                )
            g1, g2 = st.columns(2)
            if g1.button("Dùng dữ liệu này", key="synthetic_use", width="stretch"):
                use_dataset(generated.dataset)
                st.rerun()
            g2.download_button(
                "↓ Tải Excel vừa sinh",
                dataset_excel(generated.dataset),
                "campusflow-generated.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
            with st.expander("Xem các buổi học và phòng vừa sinh"):
                gc, gr = dataset_frames(generated.dataset)
                st.dataframe(gc, hide_index=True, width="stretch")
                st.dataframe(gr, hide_index=True, width="stretch")
    return dataset, errors
