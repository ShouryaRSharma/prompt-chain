from unittest.mock import Mock

import pytest

from prompt_chain.prompt_lib.chain_executor import ChainExecutor
from prompt_chain.prompt_lib.models import ChainConfig, ChainStep, PromptModel


@pytest.fixture
def mock_db_manager():
    return Mock()


@pytest.fixture
def mock_web_client():
    return Mock()


@pytest.fixture
def chain_executor(mock_db_manager, mock_web_client):
    return ChainExecutor(mock_db_manager, mock_web_client, "fake_api_key")


def test_execute_chain(chain_executor, mock_db_manager, mock_web_client):
    mock_db_manager.get_prompt_model.return_value = PromptModel(
        id=1,
        name="test_model",
        system_prompt="System prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
    )
    mock_web_client.post.return_value = {
        "choices": [{"message": {"content": '{"output": "Test output"}'}}]
    }

    chain_config = ChainConfig(
        name="test_chain",
        steps=[ChainStep(name="test_model", input_mapping={"input": "initial_input.test_input"})],
        final_output_mapping={"result": "step_0.output"},
    )

    result = chain_executor.execute_chain(chain_config, {"test_input": "Test input"})

    assert result == {"result": "Test output"}


def test_execute_chain_model_not_found(chain_executor, mock_db_manager):
    mock_db_manager.get_prompt_model.return_value = None

    chain_config = ChainConfig(
        name="test_chain",
        steps=[
            ChainStep(
                name="non_existent_model", input_mapping={"input": "initial_input.test_input"}
            )
        ],
        final_output_mapping={"result": "step_0.output"},
    )

    with pytest.raises(ValueError, match="Model not found: non_existent_model"):
        chain_executor.execute_chain(chain_config, {"test_input": "Test input"})


def test_map_input(chain_executor):
    data = {"initial_key": "initial_value", "other_key": "other_value"}
    mapping = {
        "mapped_initial": "initial_input.initial_key",
        "mapped_previous": "previous_step.previous_key",
        "mapped_step": "step_0.step_key",
    }
    step_outputs = [{"step_key": "step_value"}, {"previous_key": "previous_value"}]

    result = chain_executor._map_input(data, mapping, step_outputs)

    assert result == {
        "mapped_initial": "initial_value",
        "mapped_previous": "previous_value",
        "mapped_step": "step_value",
    }


def test_map_input_invalid_mapping(chain_executor):
    with pytest.raises(ValueError, match="Invalid mapping: invalid_mapping"):
        chain_executor._map_input({}, {"key": "invalid_mapping"}, [])


def test_validate_input(chain_executor):
    model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="System prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
    )

    valid_input = {"input": "Test input"}
    assert chain_executor._validate_input(model, valid_input) == valid_input

    with pytest.raises(ValueError, match="Input validation failed for model test_model"):
        chain_executor._validate_input(model, {"invalid_key": "Test input"})


def test_validate_output(chain_executor):
    model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="System prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
    )

    valid_output = {"output": "Test output"}
    assert chain_executor._validate_output(model, valid_output) == valid_output

    with pytest.raises(ValueError, match="Output validation failed for model test_model"):
        chain_executor._validate_output(model, {"invalid_key": "Test output"})


def test_execute_step(chain_executor, mock_web_client):
    model = PromptModel(
        id=1,
        name="test_model",
        system_prompt="System prompt",
        user_prompt={"input": "str"},
        response={"output": "str"},
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
    )

    mock_web_client.post.return_value = {
        "choices": [{"message": {"content": '{"output": "Test output"}'}}]
    }

    result = chain_executor._execute_step(model, {"input": "Test input"})

    assert result == {"output": "Test output"}
    mock_web_client.post.assert_called_once()
