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
from pathlib import Path
from typing import Iterator

from langchain_community.chat_models import ChatOpenAI
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_community.document_loaders import TextLoader, JSONLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains import RetrievalQA
from langchain.vectorstores.base import VectorStoreRetriever
from qdrant_client import QdrantClient

from src import service_deepseek
from src.dto.feed_rec_info import Post
from src.dto.qdrant_models import QdrantPostMetadata, QdrantChunkMetadata, PayloadPost, PayloadChunk
from src.env import settings, SCRAPPER_RESULTS_DIR__TELEGRAM
from src.service_deepseek import deepseek, prompts


def json_loader(text_doc: Document) -> Post:
    metadata_doc = text_doc.metadata
    return Post(
    channel_name=metadata_doc['channel_name'],
    title=metadata_doc['title'],
    post_id=metadata_doc['post_id'],
    content=metadata_doc['content'],
    pb_date=metadata_doc['pb_date'],
    link=metadata_doc['link'],
    media=None,
    )


def serialize_post(llm_client: OpenAI, embedder_model: str, embedder: CacheBackedEmbeddings, post: Post) -> QdrantPostMetadata:
    summary = asyncio.run(deepseek.prompt(llm_client, prompt=prompts.realtime_summary(post.content)))
    embedding_vector = embedder.embed_documents(summary)

    return QdrantPostMetadata(
        id=uuid.uuid4(),
        vector=embedding_vector[-1],
        payload=PayloadPost(
            title=post.title,
            summary=summary,
            full_text=post.content,
            embedding_model=embedder_model,
        ))


def serialize_chunks(embedder_model: str, embedder: CacheBackedEmbeddings, post_id: uuid.UUID, text_splitter: CharacterTextSplitter, text: str) -> Iterator[QdrantChunkMetadata]:
    text_chunks = text_splitter.split_text(text)
    embedding_vectors = embedder.embed_documents([text for text in text_chunks])
    for chunk_id, chunk in enumerate(text_chunks):
        yield QdrantChunkMetadata(
            id=uuid.uuid4(),
            vector=embedding_vectors[chunk_id],
            payload=PayloadChunk(
                post_id=post_id,
                chunk_id=chunk_id,
                text=chunk,
                embedding_model=embedder_model,
            ))



def add_post_to_qdrant(path: Path, embedder_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    llm_client = OpenAI(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")
    qdrant = QdrantClient(
            url=str(settings.QDRANT_URL),
            prefer_grpc=True,
        )
    store = RedisStore(
        redis_url=str(settings.CACHE_DB_URL),
        client_kwargs={'db': 2},
        namespace='embedding_caches',
    )
    underlying_embeddings = HuggingFaceEmbeddings(
        model_name=embedder_model
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
    json_text = JSONLoader(path,
                        jq_schema=".posts[]",
                        text_content=False, ).load()


    s_text = serialize_post(llm_client=llm_client, embedder=embedder, embedder_model=embedder_model, post=json_loader(json_text[0]))
    qdrant.upsert(
        points=[s_text],
        prefer_grpc=True,
        collection_name='posts',
        force_recreate=True,
    )

    s_chunks = serialize_chunks(embedder_model=embedder_model, embedder=embedder, post_id=s_text.id, text_splitter=text_splitter, text=json_text[0].content)
    qdrant.upsert(
        points=[s_chunks],
        prefer_grpc=True,
        collection_name='chunks',
        force_recreate=True,
    )


def initialize_retriever():
    store = RedisStore(redis_url=settings.CACHE_DB_URL, client_kwargs={'db': 2}, namespace='embedding_caches')


    underlying_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings,
        store,
        namespace=underlying_embeddings.model_name
    )

    doc_store = Qdrant(
        client=QdrantClient(
            url=str(settings.QDRANT_URL),
            prefer_grpc=True,
        ),
        collection_name='chunks',
        embeddings=embedder,
    )

    llm = ChatOpenAI(  # Используем ChatOpenAI вместо OpenAI
        api_key=str(settings.DEEP_SEEK_API_KEY.get_secret_value()),
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.1,
        max_tokens=1024
    )

    retriever = VectorStoreRetriever(vectorstore=doc_store)

    qa_chain = load_qa_with_sources_chain(llm, chain_type="stuff")

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=doc_store.as_retriever(
            search_type='similarity',
            search_kwargs={"k": 3},
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
