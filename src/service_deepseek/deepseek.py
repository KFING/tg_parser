# Please install OpenAI SDK first: `pip3 install openai`

from google.genai import Client

from src.common.async_utils import sync_to_async


from openai import OpenAI


@sync_to_async
def prompt(client: OpenAI, prompt: str) -> str:

    response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"content": prompt},
    ],
    stream=False
)
    text = response.text
    if isinstance(text, str):
        return text
    return ""
