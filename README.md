# Prompt Chain

prompt-chain is a powerful tool for creating config-as-code LLM agents.
It allows you to easily define the system prompt, user prompt, and response format for Large Language Models (LLMs),
allowing you to focus on creating sophisticated LLM agents through simple configurations.

## Purpose

By providing a structured way to define prompts and expected responses, it allows developers to:

- Quickly iterate on different prompt configurations
- Ensure consistency in LLM interactions
- Validate inputs and outputs automatically
- (TODO) Chain multiple LLM agents together

## How It Works

prompt-chain consists of two main components:

- API Service
- Database Manager

### Prompt Chain API Service

The API service, built with FastAPI, provides endpoints for:

- Creating new prompt models
- Retrieving existing models
- Calling OpenAI's API with the specified model and user input

Key features of the API service include:

- Dynamic model creation based on user-defined schemas
- Input validation against the defined schemas (so your user prompt matches what the LLM expects)
- Output validation against the LLM response (so you can check your LLM isn't hallucinating)

### Database Manager

The `DatabaseManager` class handles all database operations, including:

- Adding new prompt models to the database
- Retrieving prompt models
- Validating user inputs and LLM responses against defined schemas

Here's a detailed look at its functionality:

#### Model Storage and Retrieval:

The prompt configs are stored in a database table `prompt_models`. The schema for this table is as follows:

```
class PromptModelTable(Base):
    __tablename__ = "prompt_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    system_prompt: Mapped[str] = mapped_column(String)
    user_prompt: Mapped[dict[str, Any]] = mapped_column(JSON)
    response: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

The system_prompt is a string, and is built with the impression that it includes the input and output schemas that would be passed to the LLM. eg. This would be a typical system prompt:

```
Your task is to catch any sentences with an entity name in it.
The entity name and content you want to catch will be provided to you in the user prompt in the format {name: str, content: str}.

You must return a list containing all sentences that include the entity name.
Your output schema will be: {sentences: [str]} where you are returning a list of sentences.
```

The `user_prompt` and `response` stored in the table act as JSON representations of the schema defined in the system prompt, mapping out
each response key to a type. Primitive types are written as a string, whilst tuples, lists and dictionaries are defined my their respective
symbols.

For the system prompt example above, they would be defined as follows.

```
"user_prompt": {
    "name": "str",
    "content": "str"
}
```

```
"response": {
    "sentences": [
      "str"
    ]
}
```

#### Schema Validation:

By defining the schema in the table, we can then perform validation on any inputs and outputs provided / generated with
LLMS. The `DatabaseManager` achieves this by retrieving the stored model from the table and creating a dynamic pydantic model
to validate against. You can find more on this in the `validate_user_input` and `validate_llm_response` functions in `prompt_lib/db_manager.py`

## System Architecture

![System Architecture](systemarchitecture.svg)
