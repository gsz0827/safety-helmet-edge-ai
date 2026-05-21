import gc
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB_PATH = Path("tests/test_app.db")

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_PATH.as_posix()}"

if TEST_DB_PATH.exists():
    try:
        TEST_DB_PATH.unlink()
    except PermissionError:
        pass

from app.db.init_db import init_db  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()

    yield

    engine.dispose()
    gc.collect()

    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            # Windows may keep SQLite file handles briefly after tests finish.
            # The file is ignored by git, so leaving it locally is acceptable.
            pass


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
