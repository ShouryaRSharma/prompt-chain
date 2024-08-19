import uvicorn
from fastapi import FastAPI

from prompt_chain.dependencies import DependencyManager
from prompt_chain.prompt_lib.exceptions import DatabaseManagerException

manager = DependencyManager()
app = FastAPI()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/get_models")
async def get_models() -> dict[str, list[str]]:
    models = manager.db_manager.get_all_models()
    return {"models": models}


@app.post("/create_model")
async def create_model() -> dict[str, str]:
    system_prompt = """This is a system prompt"""
    try:
        model = manager.db_manager.add_prompt_model(
            name="test_model",
            system_prompt=system_prompt,
            user_prompt_schema={"name": "str", "age": "int"},
            response_schema={"result": "str"},
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
