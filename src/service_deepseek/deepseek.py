# Please install OpenAI SDK first: `pip3 install openai`

from google.genai import Client

from src.common.async_utils import sync_to_async


@sync_to_async
def prompt(client: Client, prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    text = response.text
    if isinstance(text, str):
        return text
    return ""
