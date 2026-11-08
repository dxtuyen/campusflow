# Báo cáo 1 · Phân tích sự cần thiết

## 1. Bối cảnh và bài toán

Đề tài đặt ra một kịch bản giả định: phòng đào tạo nhận danh sách các buổi học và phòng có sức chứa khác nhau, cần tạo lịch cho một tuần mẫu. Lịch phải bảo đảm mỗi buổi được xếp đúng một lần, phòng không bị chiếm hai lần trong cùng ca, đủ sức chứa và đúng ngày/ca được phép. Bên cạnh tính hợp lệ, người lập lịch muốn nhìn thấy nhu cầu di chuyển khi một ca kết thúc và ca tiếp theo bắt đầu.

CampusFlow không bắt đầu từ khảo sát giao thông hay cảm biến của một trường cụ thể. Sự cần thiết được phân tích từ cấu trúc bài toán và nhu cầu ra quyết định giả định. Việc xác nhận nhu cầu thực tế, quy tắc nội bộ và hiệu quả sử dụng với cán bộ đào tạo là phần nhóm cần bổ sung nếu triển khai thực địa.

## 2. Người dùng và nhu cầu

Người dùng mục tiêu là người lập lịch/phòng đào tạo. Họ cần nhập dữ liệu theo mẫu, nhận cảnh báo khi dữ liệu sai, có lịch khả thi để kiểm tra, thấy các khoảng chuyển ca có nhiều lượt đăng ký lớp và thử chính sách hạn chế thứ Bảy. Kết quả cần đọc trực tiếp trên UI và có file Excel/CSV để bàn giao.

Nhóm sinh viên thực hiện đề tài còn cần một mô hình AI có thể giải thích: đầu vào, biến, miền, ràng buộc, hàm mục tiêu, baseline và bằng chứng kiểm chứng. Vì vậy cấu trúc của ứng dụng ưu tiên tính đúng và khả năng đối chiếu hơn số lượng chức năng quản lý.

## 3. Phương án và khoảng trống cần giải quyết

| Phương án trong phạm vi đề tài | Điểm hữu ích | Điểm cần bổ sung |
|---|---|---|
| Dùng bảng Excel làm dữ liệu/bàn giao | Dễ xem và chia sẻ theo schema | Quy tắc hợp lệ và cách sinh lịch cần được triển khai/kiểm tra rõ |
| Greedy xác định | Đơn giản, dễ theo dõi, làm baseline | Có thể mắc kẹt; không chứng minh tối ưu hoặc vô nghiệm |
| CP-SAT | Biểu diễn ràng buộc và mục tiêu, có trạng thái/bound | Cần giới hạn thời gian và diễn giải FEASIBLE/UNKNOWN đúng nghĩa |

Bảng trên là phân tích lựa chọn thiết kế của CampusFlow, không phải khảo sát thị trường hay khẳng định mọi công cụ bảng tính không thể tối ưu. Tài liệu chính thức của OR-Tools được dùng để đối chiếu mô hình số nguyên và trạng thái; không thay thế bằng chứng về hiệu quả tại trường.

## 4. Vì sao có thành phần AI

Khi số buổi, phòng và lựa chọn ngày/ca tăng, việc lựa chọn một tổ hợp hợp lệ phải cân nhắc nhiều ràng buộc cùng lúc. CampusFlow diễn đạt điều đó thành bài toán CSP/constraint optimization: một biến nhị phân cho mỗi phương án gán hợp lệ và các ràng buộc tài nguyên/duy nhất. CP-SAT tìm lịch giảm `J = P + λ × N_Sat`; Greedy cung cấp một phương án đối chiếu cùng dữ liệu/chính sách.

Vai trò AI nằm ở tìm kiếm/tối ưu có ràng buộc, không phải chatbot hoặc dự báo. Lợi ích kỳ vọng là hỗ trợ tạo lịch hợp lệ, cung cấp cơ sở so sánh và làm rõ đánh đổi giữa cao điểm với thứ Bảy. Lợi ích kỳ vọng phải được phân biệt với kết quả thực nghiệm đo được trên dữ liệu giả lập.

## 5. Mục tiêu và phạm vi

Đầu vào gồm `Classes` (mã, tên, lượt đăng ký, ngày/ca cho phép) và `Rooms` (mã, sức chứa). Mỗi dòng là một buổi học, dài đúng một ca 150 phút. Có sáu ngày Mon–Sat và bốn ca cố định; Sunday cấm tuyệt đối. Cho phép thứ Bảy là chính sách mềm có penalty, hoặc người dùng có thể cấm Sat hoàn toàn.

Đầu ra là lịch, trạng thái, metric, biểu đồ chuyển ca, so sánh Greedy/CP-SAT, ba chính sách λ và file kết quả. UI có ba tab Dữ liệu, Lịch học, Phân tích AI. Bộ sinh theo seed là phần mở rộng sau core, không thay bốn dataset mẫu có chủ đích.

Không xét danh tính/trùng lịch cá nhân, giảng viên, nhiều tuần học kỳ, đường đi, năng lực cổng, dữ liệu GPS hay mật độ người theo giây. Không có tài khoản, database, API, CRUD phức tạp hoặc lịch kéo thả.

## 6. Tiêu chí đánh giá

Lịch cần vượt qua validator Python độc lập. Metrics được tính lại từ assignments, có ví dụ tay và phép vét cạn bài nhỏ để đối chiếu CP-SAT. Hai thuật toán được so trên cùng dữ liệu/chính sách, chỉ dùng metric của lịch đầy đủ. Thực nghiệm lưu tên bộ dữ liệu, timeout, seed, worker, phiên bản thư viện, status, bound và runtime.

Chất lượng chính sách được đọc bằng cặp `(P, N_Sat)`. Khi λ thay đổi, công thức J thay đổi nên không dùng J ở các λ khác nhau để kết luận lịch nào tốt hơn. Không cam kết CP-SAT nhanh hơn hoặc cải thiện Greedy trên mọi dữ liệu.

## 7. Kết quả kỳ vọng và giới hạn

Ứng dụng có thể dùng làm công cụ học tập và nguyên mẫu hỗ trợ phân phòng/xếp ca. Việc giảm chỉ số di chuyển trong mô hình không chứng minh đã giảm ùn tắc thật. Một sinh viên học nhiều buổi có thể bị đếm nhiều lượt, vì mô hình chỉ có quy mô lớp. Các màu của heatmap là độ lớn tương đối trong lịch, không phải ngưỡng an toàn.

Trước khi dùng thực tế, nhóm cần khảo sát quy tắc trường, bổ sung các ràng buộc nghiệp vụ còn thiếu và đánh giá với người dùng mục tiêu. Các chức năng lưu trữ/lịch sử chỉ được bổ sung khi có yêu cầu rõ; không mở rộng chỉ để chia việc.
