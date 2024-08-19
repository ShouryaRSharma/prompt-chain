import pytest
from pytest import MonkeyPatch

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def mock_external_endpoint_urls(monkeypatch: MonkeyPatch):
    monkeypatch.setattr("prompt_chain.config", TEST_DB_URL)
