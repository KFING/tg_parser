import uuid
from datetime import datetime

from pydantic import BaseModel


class PayloadPost(BaseModel):
    title: str | None
    summary: str
    full_text: str
    embedding_model: str


class QdrantPostMetadata(BaseModel):
    id: uuid.UUID
    vector: list[float]
    payload: PayloadPost


class PayloadChunk(BaseModel):
    post_id: str
    chunk_id: int
    text: str
    embedding_model: str


class QdrantChunkMetadata(BaseModel):
    id: uuid.UUID
    vector: list[float]
    payload: PayloadChunk
