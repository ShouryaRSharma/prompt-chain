from datetime import datetime, timezone
from typing import Any, Generator, TypeVar

from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from prompt_chain.prompt_lib.models import (
    Base,
    PromptModelCreate,
    PromptModelDict,
    PromptModelTable,
)

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


class DBManager:
    def __init__(self, db_url: str):
        """
        Initialize the DBManager with a database URL.

        Args:
            db_url (str): The URL of the database to connect to.
        """
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def get_db(self) -> Generator[Session, None, None]:
        """
        Create a database session.

        Yields:
            Session: A SQLAlchemy database session.
        """
        db = self.session()
        try:
            yield db
        finally:
            db.close()

    def create_model(self, model: PromptModelCreate[T, U]) -> PromptModelDict:
        """
        Create a new prompt model in the database.

        Args:
            model (PromptModelCreate[T, U]): The model to create.

        Returns:
            PromptModelDict: The created model's data.
        """
        db = next(self.get_db())
        db_model = PromptModelTable(
            name=model.name,
            system_prompt=model.prompt_model.system_prompt,
            user_prompt_schema=model.prompt_model.user_prompt.model_dump(),
            response_schema=model.response_model.model_dump(),
        )
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        return PromptModelDict(
            id=db_model.id,
            name=db_model.name,
            system_prompt=db_model.system_prompt,
            user_prompt_schema=db_model.user_prompt_schema,
            response_schema=db_model.response_schema,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
        )

    def get_model(self, name: str) -> PromptModelDict | None:
        """
        Retrieve a prompt model by name.

        Args:
            name (str): The name of the model to retrieve.

        Returns:
            PromptModelDict | None: The retrieved model's data, or None if not found.
        """
        db = next(self.get_db())
        model = db.query(PromptModelTable).filter(PromptModelTable.name == name).first()
        if model:
            return PromptModelDict(
                id=model.id,
                name=model.name,
                system_prompt=model.system_prompt,
                user_prompt_schema=model.user_prompt_schema,
                response_schema=model.response_schema,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
        return None

    def list_models(self) -> list[PromptModelDict]:
        """
        List all prompt models in the database.

        Returns:
            list[PromptModelDict]: A list of all prompt models' data.
        """
        db = next(self.get_db())
        models = db.query(PromptModelTable).all()
        return [
            PromptModelDict(
                id=model.id,
                name=model.name,
                system_prompt=model.system_prompt,
                user_prompt_schema=model.user_prompt_schema,
                response_schema=model.response_schema,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
            for model in models
        ]

    def update_model(self, name: str, updates: dict[str, Any]) -> PromptModelDict | None:
        """
        Update a prompt model by name.

        Args:
            name (str): The name of the model to update.
            updates (dict[str, Any]): The updates to apply to the model.

        Returns:
            PromptModelDict | None: The updated model's data, or None if not found.
        """
        db = next(self.get_db())
        db_model = db.query(PromptModelTable).filter(PromptModelTable.name == name).first()
        if db_model:
            for key, value in updates.items():
                setattr(db_model, key, value)
            db_model.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(db_model)
            return PromptModelDict(
                id=db_model.id,
                name=db_model.name,
                system_prompt=db_model.system_prompt,
                user_prompt_schema=db_model.user_prompt_schema,
                response_schema=db_model.response_schema,
                created_at=db_model.created_at,
                updated_at=db_model.updated_at,
            )
        return None

    def delete_model(self, name: str) -> bool:
        """
        Delete a prompt model by name.

        Args:
            name (str): The name of the model to delete.

        Returns:
            bool: True if the model was deleted, False if not found.
        """
        db = next(self.get_db())
        db_model = db.query(PromptModelTable).filter(PromptModelTable.name == name).first()
        if db_model:
            db.delete(db_model)
            db.commit()
            return True
        return False
