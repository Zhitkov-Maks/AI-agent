from typing import Optional
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    query: str


class GenerateResponse(BaseModel):
    success: bool
    message: str
    content: str | None = None
    file_path: str | None = None
    task_id: str | None = None


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    found: bool
    content: str | None = None
    message: str | None = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    message: Optional[str] = None
