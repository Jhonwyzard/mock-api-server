import pytest
from fastapi.testclient import TestClient

from app.core.logger import log_store
from app.main import app


@pytest.fixture
def client():
    """
    Test client fixture that cleans up the log store before and after each test.
    """
    log_store.clear()
    with TestClient(app) as test_client:
        yield test_client
    log_store.clear()
