"""from langchain.embeddings import CacheBackedEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.vectorstores import Qdrant
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.storage import RedisStore
from langchain.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient
from langchain import OpenAI
"""

import asyncio
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from langchain.chains import RetrievalQA
from langchain.embeddings import CacheBackedEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.chat_models import ChatOpenAI
from langchain_community.document_loaders import JSONLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.storage import RedisStore
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAI
from pydantic import HttpUrl
from qdrant_client import QdrantClient, models

from src.dto.feed_rec_info import Post, Source
from src.dto.qdrant_models import PayloadChunk, PayloadPost
from src.env import settings
from src.service_deepseek import deepseek, prompts


def json_loader(text_doc) -> Post:
    page_content_doc = text_doc.metadata
    return Post(
        source=Source(page_content_doc["source"]),
        channel_name=page_content_doc["channel_name"],
        title=page_content_doc["title"],
        post_id=page_content_doc["post_id"],
        content=page_content_doc["content"],
        pb_date=datetime.fromisoformat(page_content_doc["pb_date"]),
        link=HttpUrl(page_content_doc["link"]),
        media=None,
    )


def serialize_post(llm_client: OpenAI, embedder_model: str, embedder: CacheBackedEmbeddings, post: Post) -> models.PointStruct:
    summary = asyncio.run(deepseek.prompt(llm_client, prompt=prompts.realtime_summary(post.content)))
    embedding_vector = embedder.embed_documents(summary)
    payload = PayloadPost(
        source=post.source.value,
        channel_name=post.channel_name,
        title=post.title,
        summary=summary,
        full_text=post.content,
        embedding_model=embedder_model,
        page_content=summary,
    )
    return models.PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding_vector[-1],
        payload=payload.model_dump(),
    )


def serialize_chunks(
    embedder_model: str, embedder: CacheBackedEmbeddings, text_splitter: CharacterTextSplitter, post_id: uuid.UUID, source: Source, channel_name: str, text: str
) -> Iterator[models.PointStruct]:
    text_chunks = text_splitter.split_text(text)
    embedding_vectors = embedder.embed_documents([text for text in text_chunks])

    for chunk_id, chunk in enumerate(text_chunks):
        payload = PayloadChunk(
            source=source.value,
            channel_name=channel_name,
            post_id=str(post_id),
            chunk_id=chunk_id,
            text=chunk,
            embedding_model=embedder_model,
            page_content=chunk,
        )
        yield models.PointStruct(id=str(uuid.uuid4()), vector=embedding_vectors[chunk_id], payload=payload.model_dump())


def add_post_to_qdrant(path: Path, embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    llm_client = OpenAI(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")
    qdrant = QdrantClient(
        url=str(settings.QDRANT_URL),
        prefer_grpc=True,
    )
    store = RedisStore(
        redis_url=str(settings.CACHE_DB_URL),
        client_kwargs={"db": 2},
        namespace="embedding_caches",
    )
    underlying_embeddings = HuggingFaceEmbeddings(model_name=embedder_model)
    embedder = CacheBackedEmbeddings.from_bytes_store(underlying_embeddings, store, namespace=underlying_embeddings.model_name)
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )
    posts_text = JSONLoader(
        file_path=path,
        jq_schema=".posts[]",
        text_content=False,
        metadata_func=lambda record, metadata: {
            "source": record.get("source", ""),
            "channel_name": record.get("channel_name", ""),
            "title": record.get("title", ""),
            "post_id": record.get("post_id", ""),
            "content": record.get("content", ""),
            "pb_date": record.get("pb_date", ""),
            "link": record.get("link", ""),
        },
    ).load()
    qdrant.delete_collection(collection_name="posts")
    qdrant.delete_collection(collection_name="chunks")
    if not qdrant.collection_exists(collection_name="posts"):
        qdrant.create_collection(
            collection_name="posts",
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
    if not qdrant.collection_exists(collection_name="chunks"):
        qdrant.create_collection(
            collection_name="chunks",
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
        )
    for post in posts_text:
        j_post = json_loader(post)
        s_text = serialize_post(llm_client=llm_client, embedder=embedder, embedder_model=embedder_model, post=j_post)
        qdrant.upsert(
            points=[s_text],
            collection_name="posts",
        )

        s_chunks = [
            i
            for i in serialize_chunks(
                embedder_model=embedder_model,
                embedder=embedder,
                text_splitter=text_splitter,
                source=j_post.source,
                channel_name=j_post.channel_name,
                post_id=s_text.id,
                text=j_post.content,
            )
        ]
        qdrant.upsert(
            points=s_chunks,
            collection_name="chunks",
        )


def initialize_retriever(source: Source, channel_name: str):
    store = RedisStore(redis_url=settings.CACHE_DB_URL, client_kwargs={"db": 2}, namespace="embedding_caches")

    underlying_embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embedder = CacheBackedEmbeddings.from_bytes_store(underlying_embeddings, store, namespace=underlying_embeddings.model_name)

    doc_store = Qdrant(
        client=QdrantClient(
            url=str(settings.QDRANT_URL),
            prefer_grpc=True,
        ),
        collection_name="chunks",
        embeddings=embedder,
    )

    llm = ChatOpenAI(  # Используем ChatOpenAI вместо OpenAI
        api_key=str(settings.DEEP_SEEK_API_KEY.get_secret_value()),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.1,
        max_tokens=1024,
    )

    filter_conditions = []

    if source:
        filter_conditions.append(
            models.FieldCondition(
                key="source",  # поле в payload
                match=models.MatchValue(value=source.value),
            )
        )

    if channel_name:
        filter_conditions.append(
            models.FieldCondition(
                key="channel_name",  # поле в payload
                match=models.MatchValue(value=channel_name),
            )
        )

    # Создаем финальный фильтр
    qdrant_filter = models.Filter(must=filter_conditions or None)

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=doc_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3, "filter": qdrant_filter if filter_conditions else None},
        ),
        return_source_documents=False,
    )


"""file_loader_init()


def file_loader_init(path: Path):
    store = RedisStore(
        redis_url=str(settings.CACHE_DB_URL),
        client_kwargs={'db': 2},
        namespace='embedding_caches',
    )

    underlying_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings,
        store,
        namespace=underlying_embeddings.model_name
    )

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
    )

    text = TextLoader(path).load()

    text_chunks = text_splitter.split_documents(text)

    vectorstore = Qdrant.from_documents(
        text_chunks,
        embedder,
        url=str(settings.QDRANT_URL),
        prefer_grpc=True,
        collection_name='docs',
        force_recreate=True,
    )

    embedding_list = embedder.embed_documents([text.page_content for text in text_chunks])

    return embedding_list"""
