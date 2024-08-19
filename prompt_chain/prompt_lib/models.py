from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, create_model
from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


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


@dataclass
class PromptModel:
    id: int
    name: str
    system_prompt: str
    user_prompt: dict[str, Any]
    response: dict[str, Any]
    created_at: str
    updated_at: str


class OpenAIRequest(BaseModel):
    name: str
    user_input: dict[str, Any]


class ChainExecutionRequest(BaseModel):
    chain_name: str
    initial_input: dict[str, Any]


class ChainStep(BaseModel):
    name: str
    input_mapping: dict[str, str]


class ChainConfig(BaseModel):
    name: str
    steps: list[ChainStep]
    final_output_mapping: dict[str, str]


class ChainConfigTable(Base):
    __tablename__ = "chain_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DynamicModel(BaseModel):
    @classmethod
    def create_from_schema(
        cls, schema: dict[str, Any], model_name: str = "DynamicModel"
    ) -> type[BaseModel]:
        fields: dict[str, Any] = {}
        for field_name, field_type in schema.items():
            field_info = cls._parse_field_type(field_type, field_name)
            fields[field_name] = field_info
        return create_model(model_name, **fields)

    @classmethod
    def _parse_field_type(cls, field_type: Any, field_name: str) -> tuple[Any, Any]:
        if isinstance(field_type, str):
            return cls._parse_primitive_type(field_type)
        elif isinstance(field_type, dict):
            nested_model = cls.create_from_schema(field_type, f"NestedModel_{field_name}")
            return (nested_model, ...)
        elif isinstance(field_type, list):
            return cls._parse_list_type(field_type, field_name)
        elif isinstance(field_type, tuple):
            return cls._parse_tuple_type(field_type, field_name)
        else:
            raise ValueError(f"Unsupported field type for '{field_name}': {field_type}")

    @classmethod
    def _parse_list_type(cls, field_type: list[Any], field_name: str) -> tuple[Any, Any]:
        if not field_type:
            return (list[Any], ...)
        item_type = cls._parse_field_type(field_type[0], f"{field_name}_item")[0]
        return (list[item_type], ...)  # type: ignore

    @classmethod
    def _parse_tuple_type(
        cls, field_type: tuple[Any, Any] | None, field_name: str
    ) -> tuple[Any, Any]:
        if not field_type:
            return (tuple[()], ...)
        item_types = tuple(
            cls._parse_field_type(t, f"{field_name}_item_{i}")[0] for i, t in enumerate(field_type)
        )
        return (tuple[item_types], ...)  # type: ignore

    @staticmethod
    def _parse_primitive_type(field_type: str) -> tuple[Any, Any]:
        if field_type == "str":
            return (str, ...)
        elif field_type == "int":
            return (int, ...)
        elif field_type == "float":
            return (float, ...)
        elif field_type == "bool":
            return (bool, ...)
        elif field_type == "any":
            return (Any, ...)
        else:
            raise ValueError(f"Unsupported primitive type: {field_type}")


class ModelInput(BaseModel):
    name: str = Field(..., description="The name of the model")
    system_prompt: str = Field(..., description="The system prompt for the model")
    user_prompt_schema: dict[str, Any] = Field(..., description="The schema for user prompts")
    response_schema: dict[str, Any] = Field(..., description="The schema for model responses")
