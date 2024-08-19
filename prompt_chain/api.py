import uvicorn
from fastapi import Body, FastAPI

from prompt_chain.dependencies import DependencyManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import ModelInput, PromptModel

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


def run() -> None:
    uvicorn.run(app)


if __name__ == "__main__":
    run()
