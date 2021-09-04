from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class BaseModel(PydanticBaseModel):
    class Config:
        extra: str = Extra.forbid

    def __getitem__(self, key):
        return getattr(self, key)

    def items(self):
        return self.dict().items()

    def keys(self):
        return self.dict().keys()

    def values(self):
        return self.dict().values()
