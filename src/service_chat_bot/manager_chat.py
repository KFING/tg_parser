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
from langchain_community.document_loaders import TextLoader
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
from src.service_deepseek import deepseek


def json_loader(path: Path) -> Post:
    #parser_logic
    """return Post(
    channel_name=,
    title=,
    post_id=,
    content=,
    pb_date=,
    link=,
    media=,
    )"""
    pass


def serialize_post(embedder_model: str, embedder: CacheBackedEmbeddings, client: OpenAI, text_splitter: CharacterTextSplitter, text: list[Document]) -> QdrantPostMetadata:
    text_chunks = text_splitter.split_documents(text)
    summary = asyncio.run(deepseek.prompt(client, prompt=""))               #поменять СРОЧНО

    embedding_vector = embedder.embed_query(summary)

    title = "getting title from llm"
    return QdrantPostMetadata(
        id=uuid.uuid4(),
        vector=embedding_vector,
        payload=PayloadPost(
            title=title,                # где то взять
            summary=summary,
            embedding_model=embedder_model,
        ))


def serialize_chunks(embedder_model: str, embedder: CacheBackedEmbeddings, post_id: uuid.UUID, text_splitter: CharacterTextSplitter, text: list[Document]) -> Iterator[QdrantChunkMetadata]:
    text_chunks = text_splitter.split_documents(text)
    embedding_vectors = embedder.embed_documents([text.page_content for text in text_chunks])
    for chunk_id, text in enumerate(text_chunks):
        yield QdrantChunkMetadata(
            id=uuid.uuid4(),
            vector=embedding_vectors[chunk_id],
            payload=PayloadChunk(
                post_id=post_id,
                chunk_id=chunk_id,
                text=text.page_content,
                embedding_model=embedder_model,
            ))



def add_data_to_qdrant(path: Path, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
    client = OpenAI(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")

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
        model_name=embedding_model
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


    s_text = serialize_post(embedder, text_splitter, text)
    qdrant.upsert(
        points=[s_text.model_dump_json(indent=4)],
        prefer_grpc=True,
        collection_name='posts',
        force_recreate=True,
    )

    s_text_chunks = serialize_chunks(embedder, s_text.id, [chunk.page_content for chunk in text_chunks])
    qdrant.upsert(
        points=[chunk.model_dump_json(indent=4) for chunk in s_text_chunks],
        prefer_grpc=True,
        collection_name='chunks',
        force_recreate=True,
    )


def initialize():
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
        collection_name='docs',
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
