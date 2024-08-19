import json

import pytest
from pydantic import ValidationError

from prompt_chain.config import DB_URL
from prompt_chain.prompt_lib.db_manager import DatabaseManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import Base


@pytest.fixture(scope="function")
def db_manager():
    manager = DatabaseManager(DB_URL)
    yield manager
    Base.metadata.drop_all(manager.engine)


def test_add_prompt_model(db_manager):
    result = db_manager.add_prompt_model(
        name="test_model",
        system_prompt="This is a test system prompt.",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )
    assert result is True

    prompt_model = db_manager.get_prompt_model("test_model")
    assert prompt_model is not None
    assert prompt_model.name == "test_model"
    assert prompt_model.system_prompt == "This is a test system prompt."
    assert prompt_model.user_prompt == {"input": "str"}
    assert prompt_model.response == {"output": "str"}


def test_add_duplicate_prompt_model(db_manager):
    db_manager.add_prompt_model(
        name="duplicate_model",
        system_prompt="Original prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )

    with pytest.raises(DatabaseManagerException):
        db_manager.add_prompt_model(
            name="duplicate_model",
            system_prompt="Duplicate prompt",
            user_prompt_schema={"input": "str"},
            response_schema={"output": "str"},
        )


def test_get_nonexistent_prompt_model(db_manager):
    prompt_model = db_manager.get_prompt_model("nonexistent_model")
    assert prompt_model is None


def test_validate_user_input_valid(db_manager):
    db_manager.add_prompt_model(
        name="validation_model",
        system_prompt="""Speak to this person using their name. Mention their age.
        You will be given the values through an input schema of {name: <name>, age: <age>}
        Please make sure to respond with a greeting like so:
        {greeting: <greeting that you are saying>}
        """,
        user_prompt_schema={"name": "str", "age": "int"},
        response_schema={"greeting": "str"},
    )

    valid_input = {"name": "Alice", "age": 30}
    assert db_manager.validate_user_input("validation_model", valid_input) is True


def test_validate_user_input_invalid(db_manager):
    db_manager.add_prompt_model(
        name="validation_model",
        system_prompt="""Speak to this person using their name. Mention their age.
        You will be given the values through an input schema of {name: <name>, age: <age>}
        Please make sure to respond with a greeting like so:
        {greeting: <greeting that you are saying>}
        """,
        user_prompt_schema={"name": "str", "age": "int"},
        response_schema={"greeting": "str"},
    )
    invalid_input = {"name": "Bob", "age": "thirty"}
    with pytest.raises(ValidationError):
        db_manager.validate_user_input("validation_model", invalid_input)


def test_validate_user_input_nonexistent_model(db_manager):
    with pytest.raises(ValueError, match="No model found with name: nonexistent_model"):
        db_manager.validate_user_input("nonexistent_model", {"input": "test"})


def test_validate_llm_response_valid(db_manager):
    db_manager.add_prompt_model(
        name="response_model",
        system_prompt="""
            I'm going to give you an input string in the format input:
            str and you will respond with the schema {output: str, confidence: float}
            based on how confident you feal about that.
        """,
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str", "confidence": "float"},
    )

    valid_response = json.dumps({"output": "Hello, world!", "confidence": 0.95})
    assert db_manager.validate_llm_response("response_model", valid_response) is True


def test_validate_llm_response_invalid(db_manager):
    db_manager.add_prompt_model(
        name="response_model",
        system_prompt="""
            I'm going to give you an input string in the format input:
            str and you will respond with the schema {output: str, confidence: float}
            based on how confident you feal about that.
        """,
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str", "confidence": "float"},
    )

    invalid_response = json.dumps({"output": "Hello, world!", "confidence": "high"})
    with pytest.raises(ValidationError):
        db_manager.validate_llm_response("response_model", invalid_response)


def test_validate_llm_response_nonexistent_model(db_manager):
    with pytest.raises(ValueError, match="No model found with name: nonexistent_model"):
        db_manager.validate_llm_response("nonexistent_model", '{"output": "test"}')


def test_validate_llm_response_invalid_json(db_manager):
    db_manager.add_prompt_model(
        name="response_model",
        system_prompt="Test prompt",
        user_prompt_schema={"input": "str"},
        response_schema={"output": "str"},
    )

    invalid_json = "This is not valid JSON"
    with pytest.raises(json.JSONDecodeError):
        db_manager.validate_llm_response("response_model", invalid_json)
