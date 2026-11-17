"""Optional real-browser QA. Start ./run.sh before running this script.

Install .[browser], then: ./run.sh tests/browser_smoke.py
CHROME_BIN may point at an existing Chrome/Chromium installation.
CAMPUSFLOW_URL may select a different local preview port.
"""

import os
from pathlib import Path
import shutil

import pandas as pd
from playwright.sync_api import expect, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]


def select_option(page, label, option):
    """A Streamlit rerun may replace an opened dropdown before it is selected."""
    choice = page.get_by_role("option", name=option, exact=True)
    for attempt in range(3):
        page.get_by_role("combobox", name=label, exact=True).click()
        try:
            choice.wait_for(state="visible", timeout=2000)
            break
        except PlaywrightTimeoutError:
            if attempt == 2:
                raise
    choice.click()


def main():
    screenshots = ROOT / "docs" / "screenshots"
    screenshots.mkdir(parents=True, exist_ok=True)
    chrome = os.environ.get("CHROME_BIN") or shutil.which("google-chrome-stable") or shutil.which("chromium")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(os.environ.get("CAMPUSFLOW_URL", "http://127.0.0.1:8501"))
        expect(page.get_by_role("heading", name="CampusFlow AI", exact=True)).to_be_visible()

        # Exercise actual file upload, not just the Python workbook parser.
        page.locator('input[type="file"]').set_input_files(ROOT / "data" / "samples" / "saturday-trade-off.xlsx")
        page.get_by_role("button", name="Dùng file Excel", exact=True).click()
        expect(page.get_by_text("Đang dùng: saturday-trade-off.xlsx", exact=True)).to_be_visible()
        page.get_by_role("tab", name="Lịch học", exact=True).click()
        page.get_by_role("button", name="Tạo và so sánh lịch", exact=True).click()
        expect(page.get_by_text("Đã xếp đủ 4/4 buổi học", exact=False)).to_be_visible(timeout=20000)
        grid = page.get_by_role("table", name="Lịch theo ngày và ca", exact=True)
        expect(grid).to_be_visible()
        expect(grid.get_by_role("rowheader")).to_have_count(4)
        expect(grid.get_by_role("columnheader")).to_have_count(7)
        expect(grid.locator(".cf-class")).to_have_count(4)
        page.locator('[data-testid="stMain"]').evaluate("el => {el.scrollTop = 0}")
        page.screenshot(path=str(screenshots / "schedule.png"), full_page=True)
        page.get_by_text("Đổi cách xem và thuật toán", exact=True).click()
        page.get_by_text("Bảng chi tiết", exact=True).click()
        expect(page.locator('[data-testid="stDataFrame"]:visible')).to_have_count(1)
        expect(grid).to_have_count(0)
        page.get_by_text("Lưới tuần", exact=True).click()
        select_option(page, "Ngày trên lịch", "Thứ Bảy")
        expect(grid.get_by_role("columnheader")).to_have_count(2)
        expect(grid.locator(".cf-class")).to_have_count(0)
        with page.expect_download() as download:
            page.get_by_role("button", name="↓ Tải lịch Excel · kèm chỉ số", exact=True).click()
        book_path = download.value.path()
        with pd.ExcelFile(book_path) as book:
            assert len(pd.read_excel(book, "Timetable")) == 4
            assert set(book.sheet_names) == {"Timetable", "Summary", "Movement"}

        page.get_by_role("tab", name="Phân tích AI", exact=True).click()
        expect(page.locator('[data-testid="stPlotlyChart"]:visible')).to_have_count(2)
        page.get_by_text("Xem lượt ra và lượt vào trong một ngày", exact=True).click()
        select_option(page, "Ngày trên biểu đồ", "Thứ Bảy")
        expect(page.get_by_text("Đỉnh trong Thứ Bảy: 0 lượt", exact=False)).to_be_visible()
        select_option(page, "Ngày trên biểu đồ", "Cả tuần")
        page.wait_for_function("Array.from(document.querySelectorAll('.js-plotly-plot')).some(el => el.offsetParent !== null && el.data?.[0]?.x.length === 30)")
        select_option(page, "Ngày trên biểu đồ", "Thứ Hai")
        page.wait_for_function("Array.from(document.querySelectorAll('.js-plotly-plot')).some(el => el.offsetParent !== null && el.data?.[0]?.x.length === 5)")
        page.get_by_text("Xem lượt ra và lượt vào trong một ngày", exact=True).click()
        page.get_by_role("button", name="So sánh ba mức phạt", exact=True).click()
        expect(page.locator('[data-testid="stPlotlyChart"]:visible')).to_have_count(2, timeout=35000)
        expect(page.get_by_text("Từ λ = 0 sang λ = 10", exact=False)).to_be_visible()
        for level in (0, 3, 10):
            expect(page.get_by_text(f"Mức phạt λ = {level}", exact=True)).to_be_visible()
        page.locator('[data-testid="stMain"]').evaluate("el => {el.scrollTop = 0}")
        page.screenshot(path=str(screenshots / "analysis.png"), full_page=True)

        # A realistic multi-room example must stay readable and retain every class.
        page.get_by_role("tab", name="Dữ liệu", exact=True).click()
        page.locator('input[type="file"]').set_input_files(ROOT / "data" / "samples" / "congestion.xlsx")
        page.get_by_role("button", name="Dùng file Excel", exact=True).click()
        expect(page.get_by_text("Đang dùng: congestion.xlsx", exact=True)).to_be_visible()
        page.get_by_role("tab", name="Lịch học", exact=True).click()
        page.get_by_role("button", name="Tạo và so sánh lịch", exact=True).click()
        expect(page.get_by_text("Đã xếp đủ 24/24 buổi học", exact=False)).to_be_visible(timeout=20000)
        expect(grid.locator(".cf-class")).to_have_count(24)
        expect(page.get_by_text("Thời khóa biểu toàn trường", exact=True)).to_be_visible()
        expect(grid.locator(".cf-slot-summary").first).to_be_visible()
        page.locator('[data-testid="stMain"]').evaluate("el => {el.scrollTop = 0}")
        page.screenshot(path=str(screenshots / "schedule.png"), full_page=True)
        room_id = grid.locator(".cf-class").first.get_attribute("data-room")
        room_count = grid.locator(".cf-class").evaluate_all("(els, room) => els.filter(el => el.dataset.room === room).length", room_id)
        select_option(page, "Phòng đang xem", f"Phòng {room_id}")
        expect(grid.locator(".cf-class")).to_have_count(room_count)
        assert 0 < room_count < 24
        select_option(page, "Phòng đang xem", "Tất cả phòng")
        expect(grid.locator(".cf-class")).to_have_count(24)
        assert len(set(grid.locator('.cf-class').evaluate_all("els => els.map(el => el.style.backgroundColor)"))) > 1
        page.get_by_role("tab", name="Phân tích AI", exact=True).click()
        expect(page.get_by_text("Cao điểm giảm", exact=False)).to_be_visible()
        expect(page.locator('[data-testid="stPlotlyChart"]:visible')).to_have_count(2)
        page.locator('[data-testid="stMain"]').evaluate("el => {el.scrollTop = 0}")
        page.screenshot(path=str(screenshots / "analysis.png"), full_page=True)

        # A bad upload displays an error and keeps the previous valid dataset.
        page.get_by_role("tab", name="Dữ liệu", exact=True).click()
        page.locator('input[type="file"]').set_input_files({"name": "broken.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "buffer": b"invalid workbook"})
        page.get_by_role("button", name="Dùng file Excel", exact=True).click()
        expect(page.get_by_text("Không thể dùng file Excel.", exact=False)).to_be_visible()
        expect(page.get_by_text("Đang dùng: congestion.xlsx", exact=True)).to_be_visible()

        # Generated data uses the same active-dataset and scheduling pipeline.
        page.get_by_text("Sinh dữ liệu giả lập", exact=True).click()
        page.get_by_role("spinbutton", name="Số buổi học", exact=True).fill("10")
        page.get_by_role("spinbutton", name="Số phòng", exact=True).fill("2")
        page.get_by_text("Dựng và kiểm chứng lịch chứng minh có nghiệm", exact=True).click()
        expect(page.get_by_role("checkbox", name="Dựng và kiểm chứng lịch chứng minh có nghiệm", exact=True)).to_be_checked()
        page.get_by_role("button", name="Sinh dữ liệu", exact=True).click()
        expect(page.get_by_text("Xem trước: 10 buổi học · 2 phòng", exact=False)).to_be_visible()
        page.get_by_role("button", name="Dùng dữ liệu này", exact=True).click()
        expect(page.get_by_text("Đang dùng: Giả lập · seed 42", exact=True)).to_be_visible()
        page.set_viewport_size({"width": 390, "height": 844})
        page.get_by_role("tab", name="Lịch học", exact=True).click()
        page.get_by_role("button", name="Tạo và so sánh lịch", exact=True).click()
        expect(page.get_by_role("table", name="Lịch theo ngày và ca", exact=True)).to_be_visible(timeout=20000)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2")
        assert page.locator('.cf-grid').evaluate("el => el.scrollWidth > el.clientWidth")
        page.get_by_role("table", name="Lịch theo ngày và ca", exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(screenshots / "mobile.png"), full_page=True)
        assert not errors, errors
        browser.close()
        print("Browser QA passed: room-colored calendar, room/day filters, full XLSX export, heatmap, visual comparison, movement details, three policy cards, invalid upload, generated data, mobile scrolling.")


if __name__ == "__main__":
    main()
