import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from prompt_chain.api import app
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import ChainConfig, PromptModel


@pytest.fixture
def mock_dependency_manager():
    with patch("prompt_chain.api.manager") as mock_manager:
        mock_manager.db_manager = MagicMock()
        mock_manager.web_client = MagicMock()
        mock_manager.chain_executor = MagicMock()
        mock_manager.openai_api_key = "fake_api_key"
        yield mock_manager


@pytest.fixture
def client(mock_dependency_manager):
    return TestClient(app)


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_models(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_all_models.return_value = ["model1", "model2"]
    response = client.get("/get_models")
    assert response.status_code == 200
    assert response.json() == {"models": ["model1", "model2"]}


def test_get_model_existing(client, mock_dependency_manager):
    mock_model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="Test prompt",
        user_prompt={},
        response={},
        created_at="",
        updated_at="",
    )
    mock_dependency_manager.db_manager.get_prompt_model.return_value = mock_model
    response = client.get("/get_model/test_model")
    assert response.status_code == 200
    assert response.json()["name"] == "test_model"


def test_get_model_nonexistent(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_prompt_model.return_value = None
    response = client.get("/get_model/nonexistent_model")
    assert response.status_code == 200
    assert response.json() == {}


def test_create_model_success(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_prompt_model.return_value = True
    model_input = {
        "name": "test_model",
        "system_prompt": "Test prompt",
        "user_prompt_schema": {"input": "str"},
        "response_schema": {"output": "str"},
    }
    response = client.post("/create_model", json=model_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Model created successfully"}


def test_create_model_failure(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_prompt_model.return_value = False
    model_input = {
        "name": "test_model",
        "system_prompt": "Test prompt",
        "user_prompt_schema": {"input": "str"},
        "response_schema": {"output": "str"},
    }
    response = client.post("/create_model", json=model_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Failed to create model"}


def test_create_model_exception(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_prompt_model.side_effect = DatabaseManagerException(
        "Test error"
    )
    model_input = {
        "name": "test_model",
        "system_prompt": "Test prompt",
        "user_prompt_schema": {"input": "str"},
        "response_schema": {"output": "str"},
    }
    response = client.post("/create_model", json=model_input)
    assert response.status_code == 200
    assert response.json() == {"message": "Error: Test error"}


def test_call_openai_success(client, mock_dependency_manager):
    mock_model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="Test prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="",
        updated_at="",
    )
    mock_dependency_manager.db_manager.get_prompt_model.return_value = mock_model
    mock_dependency_manager.web_client.post.return_value = {
        "choices": [{"message": {"content": '{"output": "Test output"}'}}]
    }
    request_data = {"name": "test_model", "user_input": {"input": "Test input"}}
    response = client.post("/call_openai", json=request_data)
    assert response.status_code == 200
    assert json.loads(response.json()["response"]) == {"output": "Test output"}


def test_call_openai_model_not_found(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_prompt_model.return_value = None
    request_data = {"name": "nonexistent_model", "user_input": {"input": "Test input"}}
    response = client.post("/call_openai", json=request_data)
    assert response.status_code == 404
    assert "No model found" in response.json()["detail"]


def test_call_openai_invalid_input(client, mock_dependency_manager):
    mock_model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="Test prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="",
        updated_at="",
    )
    mock_dependency_manager.db_manager.get_prompt_model.return_value = mock_model
    mock_dependency_manager.db_manager.validate_user_input.side_effect = ValueError("Invalid input")
    request_data = {"name": "test_model", "user_input": {"invalid": "input"}}
    response = client.post("/call_openai", json=request_data)
    assert response.status_code == 422
    assert "Invalid input" in response.json()["detail"]


def test_create_chain_success(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_chain_config.return_value = True
    chain_config = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    response = client.post("/create_chain", json=chain_config.dict())
    assert response.status_code == 200
    assert response.json() == {"message": "Chain created successfully"}


def test_create_chain_failure(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_chain_config.return_value = False
    chain_config = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    response = client.post("/create_chain", json=chain_config.dict())
    assert response.status_code == 200
    assert response.json() == {"message": "Failed to create chain"}


def test_create_chain_exception(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.add_chain_config.side_effect = DatabaseManagerException(
        "Test error"
    )
    chain_config = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    response = client.post("/create_chain", json=chain_config.dict())
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]


def test_get_chains(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_all_chain_configs.return_value = ["chain1", "chain2"]
    response = client.get("/get_chains")
    assert response.status_code == 200
    assert response.json() == {"chains": ["chain1", "chain2"]}


def test_get_chain_existing(client, mock_dependency_manager):
    mock_chain = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    mock_dependency_manager.db_manager.get_chain_config.return_value = mock_chain
    response = client.get("/get_chain/test_chain")
    assert response.status_code == 200
    assert response.json()["name"] == "test_chain"


def test_get_chain_nonexistent(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_chain_config.return_value = None
    response = client.get("/get_chain/nonexistent_chain")
    assert response.status_code == 200
    assert response.json() == {}


def test_execute_chain_success(client, mock_dependency_manager):
    mock_chain = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    mock_dependency_manager.db_manager.get_chain_config.return_value = mock_chain
    mock_dependency_manager.chain_executor.execute_chain.return_value = {"result": "Test output"}
    request_data = {"chain_name": "test_chain", "initial_input": {"input": "Test input"}}
    response = client.post("/execute_chain", json=request_data)
    assert response.status_code == 200
    assert response.json() == {"result": {"result": "Test output"}}


def test_execute_chain_not_found(client, mock_dependency_manager):
    mock_dependency_manager.db_manager.get_chain_config.return_value = None
    request_data = {"chain_name": "nonexistent_chain", "initial_input": {"input": "Test input"}}
    response = client.post("/execute_chain", json=request_data)
    assert response.status_code == 404
    assert "No chain found" in response.json()["detail"]


def test_execute_chain_exception(client, mock_dependency_manager):
    mock_chain = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    mock_dependency_manager.db_manager.get_chain_config.return_value = mock_chain
    mock_dependency_manager.chain_executor.execute_chain.side_effect = ValueError("Test error")
    request_data = {"chain_name": "test_chain", "initial_input": {"input": "Test input"}}
    response = client.post("/execute_chain", json=request_data)
    assert response.status_code == 422
    assert "Test error" in response.json()["detail"]
