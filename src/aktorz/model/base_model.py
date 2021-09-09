import copy

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class BaseModel(PydanticBaseModel):
    class Config:
        extra: str = Extra.forbid

    # Added in v0.1.2
    def __iter__(self):
        return iter(self.dict())

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


# Added in v0.1.2
class BaseDictModel(BaseModel):
    def keys(self):
        return self.__root__.keys()

    # Not yet required.
    # def items(self):
    #     return self.__root__.items()

    # Not yet required.
    # def values(self):
    #     return self.dict().values()

    def __iter__(self):
        return iter(self.__root__)

    def __getattr__(self, item):
        return self.__root__[item]

    def __getitem__(self, item):
        return self.__root__[item]

    def __deepcopy__(self, memo):
        return copy.deepcopy(self.__root__)
