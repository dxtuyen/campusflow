# CampusFlow · Vì sao cần hỗ trợ phân phòng và xếp ca?

## 1. Một quyết định của người lập lịch

Hai thời khóa biểu đều có thể xếp đủ lớp, đúng phòng và đúng ca. Điểm khác nhau xuất hiện lúc chuyển ca. Giả sử một lớp 100 sinh viên vừa tan và một lớp 100 sinh viên sắp vào học. Theo sĩ số, khoảng chuyển ca đó có 200 lượt ra và vào. Nếu hai buổi cách nhau một ca trống, lượt ra của lớp trước và lượt vào của lớp sau rơi vào hai khoảng khác nhau.

CampusFlow dành cho cán bộ phòng đào tạo phụ trách xếp lịch. Khi có danh sách buổi học và phòng trống, người lập lịch cần biết liệu có xếp đủ các buổi hay không, khoảng chuyển ca nào đông nhất theo lịch và việc cho phép học thứ Bảy ảnh hưởng thế nào đến cao điểm đó.

## 2. Từ bảng tính đến bài toán xếp lịch

Một bảng Excel đủ để ghi mã phòng, sức chứa, sĩ số và các ca được phép. Khi thử chuyển một buổi sang ca khác bằng tay, người lập lịch phải kiểm tra phòng ở ca mới và tính lại số lượt ở cả hai khoảng chuyển ca liền kề. Việc đối chiếu hai phương án còn đòi hỏi tính cùng một chỉ số cho toàn tuần. CampusFlow giữ Excel làm đầu vào và tự động thực hiện các bước này.

## 3. Vai trò của AI

Ứng dụng dùng phương pháp tìm kiếm có ràng buộc. Mỗi buổi phải được xếp đúng một lần, vào phòng đủ chỗ và đúng ngày, ca được phép. Thuật toán tham lam (Greedy) xếp các buổi ít lựa chọn trước. Cách này dễ theo dõi, nhưng một quyết định sớm có thể chiếm mất phòng mà buổi sau cần. Bộ giải CP-SAT xét các quyết định xếp phòng và ca cùng nhau, đồng thời cân nhắc cao điểm và số lượt học thứ Bảy. Hai cách chạy trên cùng dữ liệu để người lập lịch có cơ sở so sánh.

## 4. Phạm vi và kết quả kỳ vọng

Đề tài xét một tuần từ thứ Hai đến thứ Bảy, mỗi ngày có bốn ca. Kết quả cần có là thời khóa biểu theo phòng, biểu đồ lượt ra vào theo ca và bản lịch có thể xuất ra Excel hoặc CSV. Người lập lịch có thể thử lại với chính sách chỉ học ngày thường trước khi chọn phương án.

Dữ liệu dùng trong đề tài là dữ liệu giả lập. Sĩ số cho biết có bao nhiêu lượt đăng ký ở mỗi buổi. Muốn biết tại một cổng trường có thực sự đông vào giờ chuyển ca hay không, cần thêm số liệu quan sát tại trường.
