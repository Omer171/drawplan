import datetime as dt

import pytest

from drawplan import storage

TODAY = dt.date(2026, 11, 20)


@pytest.fixture
def state():
    return storage.new_state()


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "drawplan_data.json"
