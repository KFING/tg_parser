from pydantic import BaseModel

from src.dto.feed_rec_info import Lang


class RequestRecipe(BaseModel):
    lang: Lang
    content: bool
    captions: bool
    timeline: bool
    media: bool


class KeycloakUser(BaseModel):
    email: str
    username: str
    password: str


class RequestUser(BaseModel):
    username: str
    email: str
    password: str
