from langchain.embeddings import CacheBackedEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain.vectorstores import Qdrant
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.storage import RedisStore
from langchain.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient

from src.env import settings

store = RedisStore(redis_url=CACHE_DB_URL, client_kwargs={'db': 2}, namespace='embedding_caches')

underlying_embeddings = OpenAIEmbeddings(openai_api_key=settings.DEEP_SEEK_API_KEY.get_secret_value())

embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    namespace=underlying_embeddings.model
)

doc_store = Qdrant(
    client=QdrantClient(
        url=QDRANT_URL,
        prefer_grpc=True,
    ),
    collection_name=CATEGORY,
    embeddings=embedder,
)

llm = OpenAI(openai_api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), temperature=0)

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

response = qa({
    "query": "Why Terminator searched John and Sarrah Connor ?"
})
