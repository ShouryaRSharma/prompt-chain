import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from prompt_chain.prompt_lib.models import Base, DynamicModel, PromptModelTable


class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_prompt_model(
        self,
        name: str,
        system_prompt: str,
        user_prompt_schema: dict[str, Any],
        response_schema: dict[str, Any],
    ) -> bool:
        try:
            session = self.Session()
            prompt_model = PromptModelTable(
                name=name,
                system_prompt=system_prompt,
                user_prompt=user_prompt_schema,
                response=response_schema,
            )
            session.add(prompt_model)
            session.commit()
            session.close()
            return True
        except SQLAlchemyError:
            return False

    def get_prompt_model(self, name: str) -> PromptModelTable | None:
        session = self.Session()
        prompt_model = session.query(PromptModelTable).filter_by(name=name).first()
        session.close()
        return prompt_model

    def validate_user_input(self, model_name: str, user_input: dict[str, Any]) -> bool:
        prompt_model = self.get_prompt_model(model_name)
        if not prompt_model:
            raise ValueError(f"No model found with name: {model_name}")

        user_model = DynamicModel.create_from_schema(prompt_model.user_prompt)
        try:
            user_model(**user_input)
            return True
        except ValidationError:
            raise

    def validate_llm_response(self, model_name: str, llm_response: str) -> bool:
        prompt_model = self.get_prompt_model(model_name)
        if not prompt_model:
            raise ValueError(f"No model found with name: {model_name}")

        response_model = DynamicModel.create_from_schema(prompt_model.response)
        try:
            response_data = json.loads(llm_response)
            response_model(**response_data)
            return True
        except ValidationError:
            raise
