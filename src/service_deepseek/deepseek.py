from src.common.async_utils import sync_to_async
from openai import OpenAI

from src.env import settings


@sync_to_async
def prompt(client: OpenAI, prompt: str) -> str:
    client_s = OpenAI(api_key=settings.DEEP_SEEK_API_KEY.get_secret_value(), base_url="https://api.deepseek.com")
    response = client_s.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": prompt},
    ],
    stream=False
)
    text = response.choices[0].message.content
    if isinstance(text, str):
        return text
    return ""
