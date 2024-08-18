from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
U = TypeVar("U")


class PromptModel(BaseModel, Generic[T]):
    system_prompt: str
    user_prompt: T


class ResponseModel(BaseModel, Generic[U]):
    result: U


class SentenceExtractionPrompt(BaseModel):
    content: str = Field(..., description="The content from which to extract sentences.")


class SentenceExtractionResponse(ResponseModel[list[str]]):
    result: list[str] = Field(..., description="List of extracted sentences")
