"""Input checks and an output validator that never calls the solver."""

from collections import Counter

from application.models import (
    Assignment,
    ClassSession,
    DAYS,
    Room,
    ScheduleConfig,
    SESSIONS,
)


class DatasetError(ValueError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def positive_int(value) -> bool:
    return type(value) is int and value > 0


def validate_inputs(
    classes: tuple[ClassSession, ...], rooms: tuple[Room, ...]
) -> list[str]:
    errors = []
    if not classes:
        errors.append("Classes: cần ít nhất một buổi học.")
    if not rooms:
        errors.append("Rooms: cần ít nhất một phòng.")
    for name, items, attr in (
        ("Classes", classes, "class_id"),
        ("Rooms", rooms, "room_id"),
    ):
        ids = [getattr(item, attr) for item in items]
        for code, count in Counter(ids).items():
            if count > 1:
                errors.append(f"{name}: mã trùng '{code}'.")
        for row, item in enumerate(items, 2):
            code = getattr(item, attr)
            if not isinstance(code, str) or not code.strip():
                errors.append(f"{name}, dòng {row}: {attr} không được trống.")
    for row, room in enumerate(rooms, 2):
        if not positive_int(room.capacity):
            errors.append(
                f"Rooms, dòng {row} [{room.room_id}]: capacity phải là số nguyên dương."
            )
    for row, cls in enumerate(classes, 2):
        prefix = f"Classes, dòng {row} [{cls.class_id}]"
        if not isinstance(cls.class_name, str) or not cls.class_name.strip():
            errors.append(f"{prefix}: class_name không được trống.")
        if not positive_int(cls.students):
            errors.append(f"{prefix}: students phải là số nguyên dương.")
        elif rooms and not any(
            positive_int(r.capacity) and r.capacity >= cls.students for r in rooms
        ):
            errors.append(
                f"{prefix}: không có phòng đủ sức chứa cho {cls.students} lượt đăng ký."
            )
        if not cls.allowed_days or any(d not in DAYS for d in cls.allowed_days):
            errors.append(
                f"{prefix}: allowed_days chỉ chấp nhận Mon,Tue,Wed,Thu,Fri,Sat; Sunday bị cấm."
            )
        if not cls.allowed_sessions or any(
            type(s) is not int or s not in SESSIONS for s in cls.allowed_sessions
        ):
            errors.append(f"{prefix}: allowed_sessions chỉ chấp nhận ca 1–4.")
    return errors


def require_valid_inputs(classes, rooms):
    errors = validate_inputs(classes, rooms)
    if errors:
        raise DatasetError(errors)


def validate_schedule(
    assignments: tuple[Assignment, ...],
    classes: tuple[ClassSession, ...],
    rooms: tuple[Room, ...],
    config: ScheduleConfig,
) -> list[str]:
    """Verify H1–H6 independently, including missing/unknown/duplicate records."""
    errors = []
    class_map = {c.class_id: c for c in classes}
    room_map = {r.room_id: r for r in rooms}
    counts = Counter(a.class_id for a in assignments)
    for cls in classes:
        if counts[cls.class_id] != 1:
            errors.append(
                f"[{cls.class_id}]: phải được xếp đúng một lần, thực tế {counts[cls.class_id]}."
            )
    occupied = set()
    for a in assignments:
        cls, room = class_map.get(a.class_id), room_map.get(a.room_id)
        if cls is None:
            errors.append(f"Lớp không tồn tại: {a.class_id}.")
        if room is None:
            errors.append(f"[{a.class_id}]: phòng không tồn tại {a.room_id}.")
        if a.day not in config.days:
            errors.append(f"[{a.class_id}]: ngày {a.day} bị cấm theo chính sách.")
        if type(a.session_id) is not int or a.session_id not in SESSIONS:
            errors.append(f"[{a.class_id}]: ca {a.session_id} không hợp lệ.")
        if cls:
            if (
                a.day not in cls.allowed_days
                or a.session_id not in cls.allowed_sessions
            ):
                errors.append(f"[{a.class_id}]: ngoài ngày/ca được phép.")
            if room and room.capacity < cls.students:
                errors.append(f"[{a.class_id}]: phòng {a.room_id} không đủ sức chứa.")
        key = (a.room_id, a.day, a.session_id)
        if key in occupied:
            errors.append(f"Trùng phòng {a.room_id}, {a.day}, ca {a.session_id}.")
        occupied.add(key)
    return errors
