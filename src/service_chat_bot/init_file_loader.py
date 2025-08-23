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

from src import env
from src.env import settings

from src.env import settings, SCRAPPER_RESULTS_DIR__TELEGRAM

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

len(embedding_list)
