import pytest
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from prompt_chain.prompt_lib.db_manager import DatabaseManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import Base, ChainConfig, PromptModel, PromptModelTable
from tests.conftest import TEST_DB_URL


@pytest.fixture(scope="function")
def db_manager():
    manager = DatabaseManager(TEST_DB_URL)
    yield manager
    Base.metadata.drop_all(manager.engine)


def test_add_prompt_model(db_manager):
    result = db_manager.add_prompt_model(
        name="test_model",
        system_prompt="This is a test system prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )
    assert result is True

    models = db_manager.get_all_models()
    assert "test_model" in models


def test_get_prompt_model(db_manager):
    db_manager.add_prompt_model(
        name="test_model",
        system_prompt="This is a test system prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )

    model = db_manager.get_prompt_model("test_model")
    assert isinstance(model, PromptModel)
    assert model.name == "test_model"
    assert model.system_prompt == "This is a test system prompt"
    assert model.user_prompt == {"input": "str"}
    assert model.response == {"output": "str"}


def test_get_nonexistent_prompt_model(db_manager):
    model = db_manager.get_prompt_model("nonexistent_model")
    assert model is None


def test_add_chain_config(db_manager):
    chain_config = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    result = db_manager.add_chain_config(chain_config)
    assert result is True

    configs = db_manager.get_all_chain_configs()
    assert "test_chain" in configs


def test_get_chain_config(db_manager):
    chain_config = ChainConfig(name="test_chain", steps=[], final_output_mapping={})
    db_manager.add_chain_config(chain_config)

    retrieved_config = db_manager.get_chain_config("test_chain")
    assert isinstance(retrieved_config, ChainConfig)
    assert retrieved_config.name == "test_chain"


def test_get_nonexistent_chain_config(db_manager):
    config = db_manager.get_chain_config("nonexistent_chain")
    assert config is None


def test_validate_user_input(db_manager):
    db_manager.add_prompt_model(
        name="test_model",
        system_prompt="This is a test system prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )

    assert db_manager.validate_user_input("test_model", {"input": "test input"}) is True

    with pytest.raises(ValidationError):
        db_manager.validate_user_input("test_model", {"invalid_key": "test input"})


def test_validate_llm_response(db_manager):
    db_manager.add_prompt_model(
        name="test_model",
        system_prompt="This is a test system prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )

    assert db_manager.validate_llm_response("test_model", '{"output": "test output"}') is True

    with pytest.raises(ValidationError):
        db_manager.validate_llm_response("test_model", '{"invalid_key": "test output"}')


def test_session_scope_commit(db_manager):
    with db_manager.session_scope() as session:
        session.add(
            PromptModelTable(
                name="test_model",
                system_prompt="This is a test system prompt",
                user_prompt={"input": "str"},
                response={"output": "str"},
            )
        )

    models = db_manager.get_all_models()
    assert "test_model" in models


def test_session_scope_rollback(db_manager):
    with pytest.raises(DatabaseManagerException):
        with db_manager.session_scope() as session:
            session.add(
                PromptModelTable(
                    name="test_model",
                    system_prompt="This is a test system prompt",
                    user_prompt={"input": "str"},
                    response={"output": "str"},
                )
            )
            raise SQLAlchemyError("Test error")

    models = db_manager.get_all_models()
    assert "test_model" not in models
