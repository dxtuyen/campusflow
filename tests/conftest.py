import pytest

from application.sample_data import load_sample
from application.models import ScheduleConfig


@pytest.fixture
def basic():
    return load_sample()


@pytest.fixture
def config():
    return ScheduleConfig(time_limit_seconds=2)