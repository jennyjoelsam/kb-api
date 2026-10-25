"""Pydantic models: the shape of data going into and out of the API.

FastAPI uses these to (1) validate incoming JSON automatically, returning a
422 error if it does not match, and (2) build the /docs page.
"""
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentCreate(BaseModel):
    """What a client must send to create or replace a document."""

    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list, max_length=20)


class Document(DocumentCreate):
    """What the API sends back: the same fields plus ones the server controls."""

    # from_attributes lets Pydantic read a database row object, not only a dict.
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def assume_utc(cls, value: datetime) -> datetime:
        """SQLite stores datetimes without a timezone; we always save UTC, so label it UTC."""
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


class SearchResult(BaseModel):
    """One hit from /search: the document and how well it matched."""

    score: float
    document: Document
