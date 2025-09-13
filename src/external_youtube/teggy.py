from pathlib import Path

from src.env import SCRAPPER_RESULTS_DIR
from src.service_chat_bot.manager_chat import add_post_to_qdrant
scrapper_path: Path = SCRAPPER_RESULTS_DIR / "masterbinarylog" / f"2025"
add_post_to_qdrant((scrapper_path / f"masterbinarylog__6.json"))
