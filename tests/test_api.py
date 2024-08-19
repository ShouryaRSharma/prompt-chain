from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from prompt_chain.api import app
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException


@pytest.fixture
def mock_dependency_manager():
    with patch("prompt_chain.api.manager") as mock_manager:
        mock_db_manager = MagicMock()
        mock_manager.db_manager = mock_db_manager
        yield mock_manager


@pytest.fixture
def client(mock_dependency_manager):
    with TestClient(app) as client:
        yield client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_models(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_all_models.return_value = ["model1", "model2"]
    response = client.get("/get_models")
    assert response.status_code == 200
    assert response.json() == {"models": ["model1", "model2"]}


def test_create_model_success(client, mock_dependency_manager):
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    mock_dependency_manager.db_manager.add_prompt_model.return_value = True
    response = client.post("/create_model", json=test_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Model created successfully"}


def test_create_model_failure_exception(client, mock_dependency_manager):
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    mock_dependency_manager.db_manager.add_prompt_model.side_effect = DatabaseManagerException(
        "Failed to add model"
    )
    response = client.post("/create_model", json=test_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Error: Failed to add model"}


def test_create_model_failure_no_exception(client, mock_dependency_manager):
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
        "user_prompt_schema": {"name": "str", "age": "int"},
        "response_schema": {"result": "str"},
    }
    mock_dependency_manager.db_manager.add_prompt_model.return_value = False
    response = client.post("/create_model", json=test_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Failed to create model"}


def test_create_model_invalid_input(client):
    test_input = {
        "name": "test_model",
        "system_prompt": "This is a test prompt",
    }
    response = client.post("/create_model", json=test_input)
    assert response.status_code == 422


@patch("prompt_chain.api.manager.web_client.post")
def test_call_openai_input_validation_error(mock_post, client, mock_dependency_manager):
    mock_model = MagicMock()
    mock_dependency_manager.db_manager.get_prompt_model.return_value = mock_model
    mock_dependency_manager.db_manager.validate_user_input.side_effect = ValueError("Invalid input")

    request_data = {"name": "test_model", "user_input": {"invalid": "input"}}

    response = client.post("/call_openai", json=request_data)
    assert response.status_code == 422
    assert "Invalid input" in response.json()["detail"]


@patch("prompt_chain.api.manager.web_client.post")
def test_call_openai_successful_response(mock_post, client, mock_dependency_manager):
    mock_model = MagicMock()
    mock_model.system_prompt = "This is a test system prompt"
    mock_dependency_manager.db_manager.get_prompt_model.return_value = mock_model
    mock_dependency_manager.db_manager.validate_user_input.return_value = None
    mock_dependency_manager.db_manager.validate_llm_response.return_value = None

    mock_openai_response = {"choices": [{"message": {"content": "This is a test response"}}]}
    mock_post.return_value = mock_openai_response

    request_data = {"name": "test_model", "user_input": {"field1": "value1", "field2": 42}}

    response = client.post("/call_openai", json=request_data)
    assert response.status_code == 200
    assert response.json() == {"response": "This is a test response"}
