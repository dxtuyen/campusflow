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

## 3. Kết quả trên bốn bộ dữ liệu mẫu

Thực nghiệm gồm bảy trường hợp trên bốn bộ dữ liệu giả lập. Mỗi trường hợp chạy cả hai thuật toán. CP-SAT dùng một luồng tìm kiếm, seed 42 và giới hạn 10 giây. Hai cột cuối ghi cặp **(cao điểm, lượt học thứ Bảy)**, đơn vị đều là lượt đăng ký.

| Bộ dữ liệu | Chính sách thứ Bảy | Greedy | CP-SAT |
|---|---|---:|---:|
| Cơ bản · 8 buổi, 3 phòng | Cho phép, λ = 3 | (120, 0) | (120, 0) |
| Tải tập trung · 24 buổi, 6 phòng | Cho phép, λ = 3 | (390, 0) | (375, 0) |
| Đánh đổi thứ Bảy · 4 buổi, 1 phòng | Cho phép, λ = 0 | (100, 200) | (100, 200) |
| Cùng bộ trên | Cho phép, λ = 3 hoặc 10 | (200, 0) | (200, 0) |
| Cùng bộ trên | Chỉ học ngày thường | (200, 0) | (200, 0) |
| Không khả thi · 3 buổi, 2 phòng | Cho phép, λ = 3 | Xếp thiếu buổi | Vô nghiệm |

Ở bộ **Tải tập trung**, cả 24 buổi chỉ được học từ thứ Hai đến thứ Tư. Greedy cho cao điểm 390 lượt. CP-SAT hạ được 15 lượt, còn 375, và chứng minh đây là mức thấp nhất với các phòng và ca đã cho. Ở bộ Cơ bản, hai cách xếp đạt cùng cao điểm.

Bộ **Đánh đổi thứ Bảy** cho thấy cái giá của việc tránh thứ Bảy. Bốn buổi có cùng sĩ số 100, dùng chung một phòng và chỉ được học thứ Hai hoặc thứ Bảy. Với λ = 0, lịch chia đều hai buổi mỗi ngày, các buổi trong ngày cách nhau ít nhất một ca trống. Cao điểm là 100 lượt. Với λ = 3, cả bốn buổi dồn vào thứ Hai. Lúc một lớp tan và lớp kế tiếp vào học, cao điểm tăng lên 200 lượt. Tăng λ lên 10 cho cùng kết quả.

Ở bộ **Không khả thi**, cả ba buổi đều bắt buộc học ca 1 thứ Hai trong khi chỉ có hai phòng. Greedy dừng khi hết phòng. CP-SAT xác nhận không thể xếp đủ cả ba buổi. [Bảng số liệu của 14 lượt chạy](evidence/experiments.csv) · [Lịch từng buổi và cấu hình thực nghiệm](evidence/experiments.json)

![Biểu đồ số lượt ra vào theo ngày và khoảng chuyển ca](analysis.png)

*Hình 2. Biểu đồ giúp xác định ngày và khoảng chuyển ca đạt cao điểm của lịch đang xem.*

## 4. Kiểm thử và hướng phát triển

Bộ kiểm thử đối chiếu công thức tính cao điểm với ví dụ tính tay, so nghiệm CP-SAT với kết quả duyệt hết các lịch của một bài toán nhỏ và kiểm tra quy trình nhập Excel, tạo lịch, xuất kết quả. Lần chạy ngày 28/11/2026 đạt 111/111 bài kiểm thử. Cả 12 lịch đầy đủ trong bảng thực nghiệm cũng vượt qua bước kiểm tra ràng buộc và tính lại chỉ số. [Kết quả pytest](evidence/pytest.txt)

Giới hạn chính của CampusFlow là dữ liệu chỉ có sĩ số từng buổi. Một lịch có thể hợp lệ về phòng nhưng vẫn xếp hai môn của cùng một sinh viên vào một ca. Bước phát triển tiếp theo là bổ sung danh sách nhóm sinh viên học từng môn và lịch bận của giảng viên, rồi dùng các thông tin đó để loại các phương án trùng ca.
