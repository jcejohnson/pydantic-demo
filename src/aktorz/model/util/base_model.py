"""
This Module provides enhanced pydantic BaseModel classes.

BaseModel

    Extends pydantic.BaseModel to add dict-like behavior and a Config class
    forbidding extra properties.

BaseDictModel

    Extends BaseModel specifically for classes having a __root_ property.
    Modifies dict-like behavior to delegate to __root_.

See also: .base_models
"""

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra


class BaseModel(PydanticBaseModel):
    """
    Extends pydantic.BaseModel to add dict-like behavior and a Config class
    forbidding extra properties.

    Added in v0.1.0
    """

    # v0.1.0
    class Config:
        extra: str = Extra.forbid

    # Added in v0.1.2
    def __iter__(self):
        return iter(self.dict())

    # v0.1.0
    def __getitem__(self, key):
        return getattr(self, key)

    # v0.1.0
    def __setitem__(self, key, value):
        return setattr(self, key, value)

    # v0.1.0
    def items(self):
        return self.dict().items()

    # Not yet required.
    # def keys(self):
    #     return self.dict().keys()

    # Not yet required.
    # def values(self):
    #     return self.dict().values()

    # v0.1.0
    def pop(self, key):
        value = self[key]
        if hasattr(self, key):
            delattr(self, key)
        return value
