# CampusFlow · Tài liệu báo cáo

- [Báo cáo 1 · Sự cần thiết của hệ thống](BC01_Su_can_thiet.md)
- [Báo cáo 2 · Xếp lịch và đánh giá kết quả](BC02_San_pham.md)
- [Bảng kết quả thực nghiệm](evidence/experiments.csv), [lịch chi tiết và phiên bản thư viện](evidence/experiments.json), [kết quả kiểm thử](evidence/pytest.txt)

## Chạy thử từ mã nguồn

Từ thư mục gốc của dự án, tạo môi trường Python và chạy ứng dụng trên Linux bằng các lệnh sau.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
bash run.sh
```

Để thử chính sách thứ Bảy, vào **Dữ liệu → Bộ mẫu**, chọn **Đánh đổi thứ Bảy** rồi bấm **Dùng bộ mẫu**. Trong **Lịch học**, mở **Chính sách**, chọn **Cho phép thứ Bảy** và đặt **Ưu tiên tránh thứ Bảy** ở mức **Không ưu tiên**. Bấm **Tạo lịch**, ghi lại cao điểm và số buổi thứ Bảy, rồi lặp lại với mức **Vừa**.

Để chạy lại thực nghiệm và kiểm thử từ thư mục gốc, dùng hai lệnh sau.

```bash
.venv/bin/python -m application.experiments --output reports/experiments
.venv/bin/python -m pytest
```

Theo đề bài, hồ sơ nộp còn cần mã nguồn, bản demo và nhật ký sử dụng AI của nhóm. Thư mục này chứa hai báo cáo Markdown, ảnh minh họa và kết quả kiểm chứng.
