"""Streamlit entry point. Run with: streamlit run app.py."""

import streamlit as st

from application.ui.analysis_tab import render_analysis_tab
from application.ui.components import render_shell
from application.ui.data_tab import render_data_tab
from application.ui.schedule_tab import render_schedule_tab
from application.ui.state import initialize_state


def main() -> None:
    st.set_page_config(
        page_title="CampusFlow AI · Phân phòng & xếp ca",
        page_icon="🌿",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    initialize_state()
    render_shell()
    data_tab, schedule_tab, analysis_tab = st.tabs(
        ["Dữ liệu", "Lịch học", "Phân tích AI"]
    )
    with data_tab:
        dataset, errors = render_data_tab()
    with schedule_tab:
        config = render_schedule_tab(dataset, errors)
    with analysis_tab:
        render_analysis_tab(dataset, config, errors)
    st.divider()
    st.caption(
        "CampusFlow AI · Một tuần mẫu · Không xét lịch cá nhân hay giảng viên · Một người học nhiều ca có thể được đếm nhiều lượt"
    )


if __name__ == "__main__":
    main()
