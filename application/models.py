"""Shared, immutable data contracts. A class record represents one session."""

from dataclasses import dataclass, field
from math import isfinite

DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat")
DAY_LABELS = dict(zip(DAYS, ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy")))
SESSIONS = (1, 2, 3, 4)
TIMES = {1: ("07:00", "09:30"), 2: ("10:00", "12:30"), 3: ("13:30", "16:00"), 4: ("16:30", "19:00")}
WINDOWS = ("Morning", "1→2", "2→3", "3→4", "Evening")


@dataclass(frozen=True)
class ClassSession:
    class_id: str
    class_name: str
    students: int
    allowed_days: tuple[str, ...] = DAYS
    allowed_sessions: tuple[int, ...] = SESSIONS


@dataclass(frozen=True)
class Room:
    room_id: str
    capacity: int


@dataclass(frozen=True)
class Assignment:
    class_id: str
    room_id: str
    day: str
    session_id: int


@dataclass(frozen=True)
class Dataset:
    classes: tuple[ClassSession, ...]
    rooms: tuple[Room, ...]
    name: str = "Dataset"


@dataclass(frozen=True)
class ScheduleConfig:
    allow_saturday: bool = True
    saturday_penalty: int = 3
    time_limit_seconds: float = 10.0

    def __post_init__(self):
        if type(self.allow_saturday) is not bool:
            raise ValueError("allow_saturday phải là boolean.")
        if type(self.saturday_penalty) is not int or self.saturday_penalty < 0:
            raise ValueError("Penalty λ phải là số nguyên không âm.")
        if not isinstance(self.time_limit_seconds, (int, float)) or not isfinite(self.time_limit_seconds) or self.time_limit_seconds <= 0:
            raise ValueError("Giới hạn thời gian phải là số hữu hạn lớn hơn 0.")

    @property
    def days(self) -> tuple[str, ...]:
        return DAYS if self.allow_saturday else DAYS[:-1]


@dataclass(frozen=True)
class MovementWindow:
    day: str
    window: str
    departures: int
    arrivals: int

    @property
    def total(self) -> int:
        return self.departures + self.arrivals


@dataclass(frozen=True)
class ScheduleMetrics:
    peak_movement: int
    saturday_enrollment: int
    objective: int
    saturday_classes: int
    unused_seats: int
    room_utilization: float
    windows: tuple[MovementWindow, ...]


@dataclass(frozen=True)
class ScheduleResult:
    algorithm: str
    status: str
    assignments: tuple[Assignment, ...] = ()
    metrics: ScheduleMetrics | None = None
    runtime_seconds: float = 0.0
    objective_value: float | None = None
    best_bound: float | None = None
    violations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def complete(self) -> bool:
        return self.metrics is not None and not self.violations and self.status in ("OPTIMAL", "FEASIBLE")


@dataclass(frozen=True)
class ComparisonRun:
    """One comparison, tied to the exact input and policy that produced it."""

    dataset: Dataset
    config: ScheduleConfig
    greedy: ScheduleResult
    cp_sat: ScheduleResult

    def matches(self, dataset: Dataset, config: ScheduleConfig) -> bool:
        return self.dataset == dataset and self.config == config


@dataclass(frozen=True)
class PolicyExperiment:
    """Real solver results for three penalties, with their original context."""

    dataset: Dataset
    config: ScheduleConfig
    penalties: tuple[int, ...]
    results: tuple[tuple[int, ScheduleResult], ...]

    def matches(self, dataset: Dataset, config: ScheduleConfig, penalties: tuple[int, ...]) -> bool:
        return self.dataset == dataset and self.config == config and self.penalties == penalties