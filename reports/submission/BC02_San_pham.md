# CampusFlow · Xếp lịch và đánh giá kết quả

## 1. Từ danh sách lớp đến thời khóa biểu

Ở mục **Dữ liệu**, người dùng chọn một bộ mẫu hoặc tải tệp Excel gồm hai trang tính. Trang `Classes` ghi từng buổi học, sĩ số và các ngày, ca được phép. Trang `Rooms` ghi mã phòng và sức chứa. Khi dữ liệu hợp lệ, người dùng mở **Lịch học**, chọn chính sách thứ Bảy rồi bấm **Tạo lịch**. Lịch đầy đủ có thể lọc theo phòng, theo ngày và xuất ra Excel hoặc CSV. Mục **Phân tích** cho phép xem khoảng chuyển ca đông nhất và so sánh các chính sách.

![Lưới thời khóa biểu theo ngày và ca](schedule.png)

*Hình 1. Trong cùng một ô ngày–ca có thể có nhiều buổi học nếu mỗi buổi dùng một phòng riêng.*

Ứng dụng viết bằng Python. Giao diện Streamlit nhận tệp qua `data_io.py` và chuyển dữ liệu cho `workflows.py` để chạy Greedy và CP-SAT với cùng chính sách. Hai thuật toán trả về danh sách buổi, phòng, ngày và ca. Phần kiểm tra lịch và tính chỉ số chạy độc lập với giao diện, nên cùng một bộ dữ liệu có thể dùng để trình diễn trên web và chạy thực nghiệm từ dòng lệnh.

## 2. Mô hình và cách giải

Với mỗi buổi học, mô hình chỉ giữ những phương án có phòng đủ chỗ, đúng ngày và ca cho phép. Khi người dùng chọn chỉ học ngày thường, mô hình loại thứ Bảy ngay ở bước này. Biến nhị phân `x[c,r,d,s]` bằng 1 khi buổi c học tại phòng r vào ngày d, ca s. Mỗi buổi phải chọn đúng một phương án. Trong cùng ngày và ca, mỗi phòng chỉ nhận tối đa một buổi.

Để tính cao điểm, ứng dụng cộng sĩ số tất cả các lớp học trong từng ca. Giữa hai ca liên tiếp, số lượt ra vào bằng tổng sĩ số ca trước cộng tổng sĩ số ca sau. Đầu ngày chỉ tính lượt đến ca đầu, cuối ngày chỉ tính lượt rời ca cuối. Gọi **P** là số lượt lớn nhất trong các khoảng đó trên toàn tuần và **N_Sat** là tổng sĩ số các buổi thứ Bảy. Bộ giải tìm lịch có **J = P + λ × N_Sat** nhỏ nhất. Khi cho phép học thứ Bảy, hệ số λ thể hiện mức ưu tiên tránh xếp lớp vào ngày này.

Greedy xếp buổi ít lựa chọn trước, ưu tiên lớp đông hơn khi số lựa chọn bằng nhau. Ở mỗi bước, thuật toán chọn vị trí làm J tăng ít nhất và giữ nguyên những buổi đã xếp. CP-SAT của OR-Tools có thể dùng lịch Greedy làm gợi ý ban đầu rồi tiếp tục tìm trên toàn bộ mô hình. Sau khi có lịch đầy đủ, ứng dụng kiểm tra lại từng buổi và tính lại các chỉ số từ lịch đã xếp.

## 6. Dữ liệu và thiết kế thực nghiệm

Bộ Basic có 8 buổi/3 phòng, Congestion có 24/6 tập trung Mon–Wed, Saturday trade-off có 4 buổi ×100/1 phòng cho Mon/Sat, Infeasible có 3 buổi cùng Mon/ca1 nhưng 2 phòng. Chạy thêm Weekdays Only để đối chiếu hard constraint.

Runner `python -m application.experiments --time-limit 10 --output reports/experiments` chạy bảy cấu hình và lưu 14 hàng thuật toán, cùng assignments và provenance. Các kết quả này thuộc bản tham khảo chạy bởi trợ lý; nhóm cần lưu lần chạy riêng trên máy của mình khi nhận việc.

## 7. Kết quả thực tế của bản tham khảo

| Case | λ | Ngày học | Thuật toán | Status | P | N_Sat | J | Giây |
|---|---:|---|---|---|---:|---:|---:|---:|
| basic | 3 | Mon–Sat | Greedy | FEASIBLE | 120 | 0 | 120 | 0.019 |
| basic | 3 | Mon–Sat | CP-SAT | OPTIMAL | 120 | 0 | 120 | 0.086 |
| congestion | 3 | Mon–Sat | Greedy | FEASIBLE | 390 | 0 | 390 | 0.032 |
| congestion | 3 | Mon–Sat | CP-SAT | OPTIMAL | 375 | 0 | 375 | 1.355 |
| saturday-lambda-0 | 0 | Mon–Sat | Greedy | FEASIBLE | 100 | 200 | 100 | 0.001 |
| saturday-lambda-0 | 0 | Mon–Sat | CP-SAT | OPTIMAL | 100 | 200 | 100 | 0.006 |
| saturday-lambda-3 | 3 | Mon–Sat | Greedy | FEASIBLE | 200 | 0 | 200 | 0.001 |
| saturday-lambda-3 | 3 | Mon–Sat | CP-SAT | OPTIMAL | 200 | 0 | 200 | 0.007 |
| saturday-lambda-10 | 10 | Mon–Sat | Greedy | FEASIBLE | 200 | 0 | 200 | 0.001 |
| saturday-lambda-10 | 10 | Mon–Sat | CP-SAT | OPTIMAL | 200 | 0 | 200 | 0.007 |
| weekdays-only | 3 | Mon–Fri | Greedy | FEASIBLE | 200 | 0 | 200 | 0.000 |
| weekdays-only | 3 | Mon–Fri | CP-SAT | OPTIMAL | 200 | 0 | 200 | 0.003 |
| infeasible | 3 | Mon–Sat | Greedy | FAILED | — | — | — | 0.000 |
| infeasible | 3 | Mon–Sat | CP-SAT | INFEASIBLE | — | — | — | 0.002 |

Các hàng thất bại/không kết luận giữ metric trống, không thay bằng 0. Greedy FAILED không chứng minh bài toán vô nghiệm. Cần xem `(P, N_Sat)` khi so các λ, vì J đổi công thức. Những kết quả trên không cho phép khái quát CP-SAT luôn nhanh/tốt hơn hoặc giảm ùn tắc tại trường.

Bộ trade-off có chứng minh nhỏ: chia Mon/Sat, mỗi ngày ca 1 và 3, cho P=100 và N_Sat=200. Chỉ Mon buộc dùng bốn ca, cho P=200 và N_Sat=0. λ cao làm phương án ngày thường được ưu tiên theo mục tiêu đã chọn.

## 8. Kiểm thử và UI

Kết quả pytest được lưu nguyên văn trong log: **107 passed in 18.78s**. Có tính tay F/P/J, lỗi Excel, ràng buộc lịch, phản ví dụ Greedy, vét cạn bài nhỏ, timeout thật, import → solve → export, typed workflows và tương tác Streamlit. Chrome kiểm tra lưới/bảng, lọc phòng/ngày, export đủ lịch, heatmap, ba chính sách và màn hình 390 px.

![alt text](schedule.png)

Ảnh lịch: mỗi thẻ là một buổi, màu giữ ổn định theo phòng; mặc định xem tất cả phòng. Mỗi ô ngày–ca có số lớp và tổng lượt đăng ký đang hiển thị để nhận ra các lớp học song song. Các chỉ số toàn tuần không đổi khi lọc.

![alt text](analysis.png)

Ảnh phân tích: mỗi ô thể hiện F theo ngày/cửa sổ; ★ là các ô đạt P. Thanh đối chiếu và lời giải thích dùng số thực; chi tiết kỹ thuật được thu gọn.

## 9. Vai trò AI và đóng góp của nhóm

Mã tham khảo, UI, tests và tài liệu có hỗ trợ đáng kể từ Codex trong hội thoại hiện tại. Không tự nhận phần đó là A–D đã viết hoặc nghiệm thu. Phần kế hoạch giao việc trong vault là việc nhóm cần nhận, đọc, kiểm chứng và ghi bàn giao thực.

[[07_Nhat_ky/AI/AI-001_Ho_tro_Codex]] mới là tóm tắt, chưa có raw transcript đầy đủ. Trước khi nộp, nhóm cần xuất hội thoại gốc, ghi nhận xét/giữ-sửa-bỏ và liên kết việc áp dụng. Không lấy prompt gợi ý hoặc một nhật ký mô phỏng làm tương tác thật.

## 10. Hạn chế và hướng phát triển

Chưa xác minh trên máy nhóm/Windows/macOS trừ khi có biên bản bổ sung. Chưa có dữ liệu thật hay danh tính, giảng viên, lịch nhiều tuần, năng lực cổng/đường đi. Không có lưu trữ bền vững; ghế dư chưa tối ưu riêng. Solver có thể chỉ FEASIBLE hoặc UNKNOWN khi timeout.

Hướng phát triển nên bắt đầu từ khảo sát người dùng/quy tắc thực, sau đó bổ sung dữ liệu và ràng buộc có căn cứ. Lưu lịch sử hoặc mục tiêu phụ chỉ được thêm khi có yêu cầu và kiểm chứng tương ứng. Giữ phân biệt proxy với phép đo thực tế.

## Nguồn và việc còn phải chốt

- [ ] Điền lớp, giảng viên, track/rubric và hạn nộp đã xác nhận.
- [ ] Bổ sung lần chạy, nhận xét, đóng góp và biên bản của nhóm.
- [ ] Bổ sung raw transcript AI và rà đủ nguồn.
- [ ] A xác nhận kỹ thuật, D rà hồ sơ rồi mới coi PDF là bản được duyệt.