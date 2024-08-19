import json

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from requests import RequestException

from prompt_chain.dependencies import DependencyManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import ModelInput, OpenAIRequest, PromptModel

manager = DependencyManager()
app = FastAPI()


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


def run() -> None:
    uvicorn.run(app)


if __name__ == "__main__":
    run()
