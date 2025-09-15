from pathlib import Path

from src.dto.feed_rec_info import Source
from src.env import SCRAPPER_RESULTS_DIR
from src.service_chat_bot import manager_chat

scrapper_path: Path = SCRAPPER_RESULTS_DIR / "masterbinarylog" / "2025"
# add_post_to_qdrant((scrapper_path / f"masterbin6.json"))

qa = manager_chat.initialize_retriever(Source.TELEGRAM, "masterbinarylog")
response = qa.invoke({"query": "про что рассказывал Владимир Иванов"})
print(f"Peppi: {response["result"]}")
