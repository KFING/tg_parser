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
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import Qdrant
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import CacheBackedEmbeddings
from langchain_community.storage import RedisStore
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.chains import RetrievalQA
from langchain.vectorstores.base import VectorStoreRetriever
from qdrant_client import QdrantClient
from src.env import settings

store = RedisStore(redis_url=settings.CACHE_DB_URL, client_kwargs={'db': 2}, namespace='embedding_caches')

underlying_embeddings = OpenAIEmbeddings(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")

embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    namespace=underlying_embeddings.model
)

doc_store = Qdrant(
    client=QdrantClient(
        url=str(settings.QDRANT_URL),
        prefer_grpc=True,
    ),
    collection_name="help",
    embeddings=embedder,
)

llm = OpenAI(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")

retriever = VectorStoreRetriever(vectorstore=doc_store)

qa_chain = load_qa_with_sources_chain(llm, chain_type="stuff")

qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=doc_store.as_retriever(
        search_type='similarity',
        search_kwargs={"k": 3},
    ),
    return_source_documents=False,
)

response = qa.invoke({
    "query": "Why Terminator searched John and Sarrah Connor ?"
})
