from langchain.embeddings import CacheBackedEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain.vectorstores import Qdrant
from langchain.storage import RedisStore
from langchain.embeddings import OpenAIEmbeddings

from src.env import settings

store = RedisStore(
    redis_url=CACHE_DB_URL,
    client_kwargs={'db': 2},
    namespace='embedding_caches',
)

underlying_embeddings = OpenAIEmbeddings(
    openai_api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(),
)

embedder = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings,
    store,
    namespace=underlying_embeddings.model
)

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=1000,
    chunk_overlap=100,
    length_function=len,
)

text = TextLoader('./data/script-terminator.txt').load()
text_chunks = text_splitter.split_documents(text)

vectorstore = Qdrant.from_documents(
    text_chunks,
    embedder,
    url=QDRANT_URL,
    prefer_grpc=True,
    collection_name=CATEGORY,
    force_recreate=True,
)

embedding_list = embedder.embed_documents([text.page_content for text in text_chunks])

len(embedding_list)
