from datetime import datetime
from typing import Any, Generic, TypedDict, TypeVar

from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


class PromptModel(BaseModel, Generic[T]):
    system_prompt: str
    user_prompt: T


class ResponseModel(BaseModel, Generic[U]):
    result: U


class Base(DeclarativeBase):
    pass


class PromptModelDict(TypedDict):
    id: int
    name: str
    system_prompt: str
    user_prompt_schema: dict[str, Any]
    response_schema: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PromptModelTable(Base):
    __tablename__ = "prompt_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    system_prompt: Mapped[str] = mapped_column(String)
    user_prompt_schema: Mapped[dict[str, Any]] = mapped_column(JSON)
    response_schema: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PromptModelCreate(BaseModel, Generic[T, U]):
    name: str
    prompt_model: PromptModel[T]
    response_model: ResponseModel[U]
