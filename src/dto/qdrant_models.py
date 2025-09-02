import uuid
from datetime import datetime

from pydantic import BaseModel


class PayloadPost(BaseModel):
    title: str
    summary: str
    embedding_model: str


class QdrantPostMetadata(BaseModel):
    id: uuid.UUID
    vector: list[int]
    payload: PayloadPost


class PayloadChunk(BaseModel):
    post_id: uuid.UUID
    chunk_id: int
    text: str
    embedding_model: str


class QdrantChunkMetadata(BaseModel):
    id: uuid.UUID
    vector: list[int]
    payload: PayloadChunk
