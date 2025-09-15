import uuid
from datetime import datetime

from pydantic import BaseModel

from src.dto.feed_rec_info import Source


class PayloadPost(BaseModel):
    source: str
    channel_name: str
    title: str | None
    summary: str
    full_text: str
    embedding_model: str
    page_content: str


class QdrantPostMetadata(BaseModel):
    id: uuid.UUID
    vector: list[float]
    payload: PayloadPost


class PayloadChunk(BaseModel):
    source: str
    channel_name: str
    post_id: str
    chunk_id: int
    text: str
    embedding_model: str
    page_content: str


class QdrantChunkMetadata(BaseModel):
    id: uuid.UUID
    vector: list[float]
    payload: PayloadChunk
