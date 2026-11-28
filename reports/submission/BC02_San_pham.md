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
