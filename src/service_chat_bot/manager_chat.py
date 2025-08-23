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
from langchain_community.chat_models import ChatOpenAI
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
from src.env import settings, SCRAPPER_RESULTS_DIR__TELEGRAM


def file_loader_init():
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

    text = TextLoader((SCRAPPER_RESULTS_DIR__TELEGRAM / 'raw' / 'data.txt')).load()
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

def initialize():
    store = RedisStore(redis_url=settings.CACHE_DB_URL, client_kwargs={'db': 2}, namespace='embedding_caches')

    # underlying_embeddings = OpenAIEmbeddings(openai_api_key=str("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"))
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



