from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from prompt_chain.api import app, manager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException

client = TestClient(app)


@pytest.fixture
def mock_db_manager():
    with patch("prompt_chain.dependencies.DatabaseManager") as mock:
        yield mock.return_value


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_models():
    with patch.object(manager.db_manager, "get_all_models", return_value=["model1", "model2"]):
        response = client.get("/get_models")
        assert response.status_code == 200
        assert response.json() == {"models": ["model1", "model2"]}


def test_create_model_success():
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    with patch.object(manager.db_manager, "add_prompt_model", return_value=True):
        response = client.post("/create_model", json=test_input)
        assert response.status_code == 200
        assert response.json() == {"message": "Model created successfully"}


def test_create_model_failure_exception():
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    with patch.object(
        manager.db_manager,
        "add_prompt_model",
        side_effect=DatabaseManagerException("Failed to add model"),
    ):
        response = client.post("/create_model", json=test_input)
        assert response.status_code == 200
        assert response.json() == {"message": "Error: Failed to add model"}


def test_create_model_failure_no_exception():
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    with patch.object(manager.db_manager, "add_prompt_model", return_value=False):
        response = client.post("/create_model", json=test_input)
        assert response.status_code == 200
        assert response.json() == {"message": "Failed to create model"}


def test_create_model_invalid_input():
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
    }
    response = client.post("/create_model", json=test_input)
    assert response.status_code == 422
