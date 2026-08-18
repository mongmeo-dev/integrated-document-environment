from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from ide_api.cmd.api import app


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app, base_url="https://testserver") as test_client:
        yield test_client
