from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class BaseModel(PydanticBaseModel):
    class Config:
        extra: str = Extra.forbid

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def items(self):
        return self.dict().items()

    # Not yet required.
    # def keys(self):
    #     return self.dict().keys()

    # Not yet required.
    # def values(self):
    #     return self.dict().values()

    def pop(self, key):
        value = self[key]
        if hasattr(self, key):
            delattr(self, key)
        return value
