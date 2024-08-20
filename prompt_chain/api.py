import json
import logging
from typing import Any

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from requests import RequestException

from prompt_chain.dependencies import DependencyManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import (
    ChainConfig,
    ChainExecutionRequest,
    ModelInput,
    OpenAIRequest,
    PromptModel,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
LOGGER = logging.getLogger(__name__)
manager = DependencyManager()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/get_models")
async def get_models() -> dict[str, list[str]]:
    models = manager.db_manager.get_all_models()
    return {"models": models}


@app.get("/get_model/{model_name}")
async def get_model(model_name: str) -> PromptModel | dict[None, None]:
    model = manager.db_manager.get_prompt_model(model_name)
    if model:
        return model
    else:
        return {}


@app.post("/create_model")
async def create_model(model_input: ModelInput = Body(...)) -> dict[str, str]:
    """
    Create a new prompt model with the given parameters.

    The input schemas should follow the format expected by the DynamicModel class:
    - Primitive types: "str", "int", "float", "bool", "any"
    - Nested objects: Use a dictionary to define nested fields
    - Lists: Use a list with a single item defining the type of list elements
    - Tuples: Use a tuple to define fixed-length sequences with specific types

    Example input:
    ```
    {
        "name": "example_model",
        "system_prompt": "This is a system prompt",
        "user_prompt_schema": {
            "name": "str",
            "age": "int",
            "scores": ["float"],
            "address": {
                "street": "str",
                "city": "str",
                "zip": "str"
            },
            "flags": ("bool", "bool")
        },
        "response_schema": {
            "result": "str",
            "confidence": "float"
        }
    }
    ```
    Returns:
        A dictionary with a message indicating success or failure.
    """
    try:
        model = manager.db_manager.add_prompt_model(
            name=model_input.name,
            system_prompt=model_input.system_prompt,
            user_prompt_schema=model_input.user_prompt_schema,
            response_schema=model_input.response_schema,
        )
        if not model:
            return {"message": "Failed to create model"}
        else:
            return {"message": "Model created successfully"}
    except DatabaseManagerException as e:
        return {"message": f"Error: {str(e)}"}


@app.post("/call_openai")
async def call_openai(request: OpenAIRequest) -> dict[str, str]:
    """
    Call the OpenAI API with the specified model and dynamic user input.

    Args:
        request (OpenAIRequest): Contains model_name and user_input.

    Returns:
        dict: The response from the OpenAI API if it meets the response schema for the model.
    """
    try:
        model = manager.db_manager.get_prompt_model(request.name)
        if not model:
            raise HTTPException(status_code=404, detail=f"No model found with name: {request.name}")

        try:
            manager.db_manager.validate_user_input(request.name, request.user_input)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        headers = {
            "Authorization": f"Bearer {manager.openai_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": model.system_prompt},
                {"role": "user", "content": json.dumps(request.user_input)},
            ],
        }

        response = manager.web_client.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=data
        )
        shaped_response = response["choices"][0]["message"]["content"]

        manager.db_manager.validate_llm_response(request.name, shaped_response)
        return {"response": shaped_response}

    except (ValueError, RequestException) as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_chain")
async def create_chain(chain_config: ChainConfig = Body(...)) -> dict[str, str]:
    """
    Create a new chain configuration.

    Args:
        chain_config (ChainConfig): The configuration for the new chain.

    Returns:
        dict: A message indicating whether the chain was created successfully.

    Example:
    ```
        Request body:
        {
            "name": "sentiment_analysis_chain",
            "steps": [
                {
                    "name": "text_preprocessor",
                    "input_mapping": {
                        "text": "initial_input.article"
                    }
                },
                {
                    "name": "sentiment_analyzer",
                    "input_mapping": {
                        "processed_text": "previous_step.cleaned_text"
                    }
                }
            ],
            "final_output_mapping": {
                "original_text": "initial_input.article",
                "sentiment": "step_1.sentiment_score"
            }
        }

        Response:
        {
            "message": "Chain created successfully"
        }
    ```

    Note:
    ```
        - The "name" field should be unique for each chain.
        - Each step in the "steps" array should correspond to an existing model in the system.
        - The "input_mapping" for each step defines how inputs are sourced:
          - "initial_input.X" refers to the input provided when executing the chain.
          - "previous_step.X" refers to an output from the immediately preceding step.
          - "step_N.X" refers to an output from the Nth step (0-indexed).
        - The "final_output_mapping" defines how the chain's final output is constructed from the results of its steps.
    ```
    """
    try:
        success = manager.db_manager.add_chain_config(chain_config)
        if success:
            return {"message": "Chain created successfully"}
        else:
            return {"message": "Failed to create chain"}
    except DatabaseManagerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_chains")
async def get_chains() -> dict[str, list[str]]:
    chains = manager.db_manager.get_all_chain_configs()
    return {"chains": chains}


@app.get("/get_chain/{chain_name}")
async def get_chain(chain_name: str) -> ChainConfig | dict[None, None]:
    chain = manager.db_manager.get_chain_config(chain_name)
    if chain:
        return chain
    else:
        return {}


@app.post("/execute_chain")
async def execute_chain(request: ChainExecutionRequest) -> dict[str, Any]:
    """
    Execute a chain with the specified chain name and initial input.

    Args:
        request (ChainExecutionRequest): Contains chain_name and initial_input.

    Returns:
        dict: The result of executing the chain.

    Example:
    ```
        Request body:
        {
            "chain_name": "sentiment_analysis_chain",
            "initial_input": {
                "article": "The new product launch was a great success. Customer feedback has been overwhelmingly positive, with many praising the innovative features and user-friendly design."
            }
        }

        Response:
        {
            "result": {
                "original_text": "The new product launch was a great success. Customer feedback has been overwhelmingly positive, with many praising the innovative features and user-friendly design.",
                "sentiment": 0.8
            }
        }
    ```

    Note:
        The structure of the initial_input and the result will depend on how your specific chain is configured.
        The example above assumes a sentiment analysis chain that takes an article as input and
        returns the original text along with a sentiment score.
    """
    try:
        chain_config = manager.db_manager.get_chain_config(request.chain_name)
        if not chain_config:
            raise HTTPException(
                status_code=404, detail=f"No chain found with name: {request.chain_name}"
            )

        result = manager.chain_executor.execute_chain(chain_config, request.initial_input)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def run() -> None:
    uvicorn.run(app)


if __name__ == "__main__":
    run()
