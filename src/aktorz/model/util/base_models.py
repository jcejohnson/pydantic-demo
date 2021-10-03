"""
Additional base models with conflicting dependencies or that otherwise don't
make sense to belong to .base_model
"""

import copy

from .base_model import BaseModel
from .schema_version import SchemaVersionBase


class BaseDictModel(BaseModel):
    """
    Extends BaseModel specifically for classes having a __root_ property.
    Modifies dict-like behavior to delegate to __root_.

    Added in v0.1.2
    """

    # Not yet required.
    # def keys(self):
    #     return self.__root__.keys()

    # Not yet required.
    # def items(self):
    #     return self.__root__.items()

    # Not yet required.
    # def values(self):
    #     return self.dict().values()

    # Not yet required.
    # def __iter__(self):
    #     return iter(self.__root__)

    # Not yet required.
    # def __getattr__(self, item):
    #     return self.__root__[item]

    # v0.1.2
    def __deepcopy__(self, memo):
        return copy.deepcopy(self.__root__)

    # v0.1.2
    def __getitem__(self, item):
        return self.__root__[item]

    # v0.1.2
    def __len__(self):
        return len(self.__root__)


class BaseVersionedModel(BaseModel):
    """
    Provides a schema_version property and a custom dict() method that will
    represent schema_version as a string.

    Added in v0.1.2
    """

    # 0.1.2 : SchemaVersion
    schema_version: SchemaVersionBase

    # 0.1.2
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        if not isinstance(result["schema_version"], str):
            result["schema_version"] = str(self.schema_version)
        return result
