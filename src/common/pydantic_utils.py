from pydantic import BaseModel


class TmpListStruct(BaseModel):
    objects: list[BaseModel]
