import json
import logging
from contextlib import contextmanager
from typing import Any, Generator

from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from prompt_chain.prompt_lib.exceptions import DatabaseManagerException
from prompt_chain.prompt_lib.models import (
    Base,
    ChainConfig,
    ChainConfigTable,
    DynamicModel,
    PromptModel,
    PromptModelTable,
)

LOGGER = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        session = self.session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            LOGGER.error(f"Database error: {str(e)}")
            raise DatabaseManagerException(e)
        finally:
            session.close()

    def add_prompt_model(
        self,
        name: str,
        system_prompt: str,
        user_prompt_schema: dict[str, Any],
        response_schema: dict[str, Any],
    ) -> bool:
        with self.session_scope() as session:
            prompt_model = PromptModelTable(
                name=name,
                system_prompt=system_prompt,
                user_prompt=user_prompt_schema,
                response=response_schema,
            )
            session.add(prompt_model)
        return True

    def get_all_models(self) -> list[str]:
        with self.session_scope() as session:
            models = session.query(PromptModelTable).all()
            models_dict = [self.convert_to_dict(model) for model in models]
            return [model.name for model in models_dict]

    def get_prompt_model(self, model_name: str) -> PromptModel | None:
        with self.session_scope() as session:
            model = (
                session.query(PromptModelTable).filter(PromptModelTable.name == model_name).first()
            )
            return self.convert_to_dict(model) if model else None

    def add_chain_config(self, chain_config: ChainConfig) -> bool:
        with self.session_scope() as session:
            config_entry = ChainConfigTable(
                name=chain_config.name, config=chain_config.model_dump()
            )
            session.add(config_entry)
        return True

    def get_chain_config(self, name: str) -> ChainConfig | None:
        with self.session_scope() as session:
            config = session.query(ChainConfigTable).filter(ChainConfigTable.name == name).first()
            return ChainConfig(**config.config) if config else None

    def get_all_chain_configs(self) -> list[str]:
        with self.session_scope() as session:
            configs = session.query(ChainConfigTable).all()
            return [config.name for config in configs]

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

    @staticmethod
    def convert_to_dict(model: PromptModelTable) -> PromptModel:
        return PromptModel(
            id=model.id,
            name=model.name,
            system_prompt=model.system_prompt,
            user_prompt=model.user_prompt,
            response=model.response,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )
