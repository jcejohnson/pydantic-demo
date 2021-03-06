from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra

from .mixin_dict_like import DictLikeMixin
from .mixin_validate_self import ValidationMixin


class BaseModel(DictLikeMixin, ValidationMixin, PydanticBaseModel):
    class Config:
        extra: str = Extra.forbid


class BaseDictModel(DictLikeMixin, ValidationMixin, PydanticBaseModel):
    """
    Baseclass for a pydantic custom root model.
    Adds dict-like behavior but not data (assumes self.__root__ is Mappable).

    Subclasses can override ___validate_item___ to validate keys and/or
    __validate_value__ to validate value types.

    I'm not using @validate_arguments here because we want the baseclass to
    support any types for key/value. If you want to validate the items/values
    you can use @validate_arguments on the __validate_*__ methods of your
    subclass.

    e.g. --

        # Ensure that the items (keys) are a FooBarOrComment
        @validate_arguments
        def __validate_item__(self, item: FooBarOrComment):
            return True
    """

    def __getattr__(self, item: Any):
        if item == "__deepcopy__":
            return None
        self.__validate_item__(item)
        return self.__root__[item]

    def __len__(self):
        return len(self.__root__)

    def __setattr__(self, item: Any, value):
        self.__validate_item__(item)
        self.__validate_value__(item)
        self.__root__[item] = value

    def __getitem__(self, item: Any):
        self.__validate_item__(item)
        return self.__root__[item]

    def __setitem__(self, item: Any, value):
        self.__validate_item__(item)
        self.__validate_value__(item)
        self.__root__[item] = value

    def __validate_item__(self, item: Any):
        return True

    def __validate_value__(self, item: Any):
        return True


class BaseListModel(ValidationMixin, PydanticBaseModel):
    """
    Baseclass for a pydantic custom root model.
    Assumes self.__root__ is a List.
    """

    pass
