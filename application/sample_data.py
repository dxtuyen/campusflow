"""Four fixed datasets and their descriptions, independent of Excel and Streamlit."""

from application.models import ClassSession, Dataset, Room

SAMPLE_NAMES = ("Basic", "Congestion", "Saturday trade-off", "Infeasible")
SAMPLE_DESCRIPTIONS = {
    "Basic": "8 buổi học · 3 phòng. Bắt đầu với một tuần mẫu nhỏ, dễ kiểm tra.",
    "Congestion": "24 buổi học · 6 phòng. Nhiều lớp tập trung trong ba ngày đầu tuần để so sánh tải chuyển ca.",
    "Saturday trade-off": "4 buổi học · 1 phòng · Mon/Sat. λ = 0 có thể giảm đỉnh tải bằng cách dùng thứ Bảy; λ cao ưu tiên ngày thường.",
    "Infeasible": "3 buổi học chỉ được xếp Mon, ca 1 · 2 phòng. Dữ liệu hợp schema nhưng không thể xếp đủ lịch.",
}


def load_sample(name: str = "Basic") -> Dataset:
    if name == "Basic":
        rooms = (Room("A101", 80), Room("A102", 120), Room("B201", 150))
        names = ("Trí tuệ nhân tạo", "Mạng máy tính", "Cơ sở dữ liệu", "Đại số tuyến tính", "Lập trình Python", "Cấu trúc dữ liệu", "Xác suất thống kê", "Kỹ thuật phần mềm")
        sizes = (90, 65, 120, 45, 75, 100, 60, 80)
        classes = tuple(ClassSession(f"CLS{i:02}", title, size) for i, (title, size) in enumerate(zip(names, sizes), 1))
    elif name == "Congestion":
        rooms = tuple(Room(f"A{101+i}", capacity) for i, capacity in enumerate((60, 80, 100, 120, 140, 160)))
        sizes = (140, 110, 85, 60, 95, 70, 130, 50, 100, 75, 145, 55, 120, 90, 65, 80, 150, 105, 45, 115, 135, 60, 95, 70)
        subjects = ("Lập trình", "Toán ứng dụng", "Khoa học dữ liệu", "Kinh tế học", "Hệ thống thông tin", "Ngoại ngữ")
        classes = tuple(
            ClassSession(f"CG{i:02}", f"{subjects[(i-1) % 6]} {i:02}", size,
                         ("Mon", "Tue", "Wed"), (1, 2, 3, 4) if i % 4 else (1, 2, 3))
            for i, size in enumerate(sizes, 1)
        )
    elif name == "Saturday trade-off":
        rooms = (Room("A101", 100),)
        classes = tuple(ClassSession(f"SAT{i}", f"Chuyên đề {i}", 100, ("Mon", "Sat")) for i in range(1, 5))
    elif name == "Infeasible":
        rooms = (Room("A101", 100), Room("A102", 100))
        classes = tuple(ClassSession(f"INF{i}", f"Buổi học giới hạn {i}", 80, ("Mon",), (1,)) for i in range(1, 4))
    else:
        raise ValueError(f"Dataset không tồn tại: {name}")
    return Dataset(classes, rooms, name)