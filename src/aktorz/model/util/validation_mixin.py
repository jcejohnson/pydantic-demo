# type: ignore

from typing import TYPE_CHECKING, Any, Type, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    Model = TypeVar("Model", bound="BaseModel")


class ValidationMixin(object):
    """
    MyModel.validate(myModel) doesn't work the way that _I_ need.
    However, MyModel.validate(myModel.dict()) gets the job done.
    This mixin provides that functionality.

    See tests/test_validation.py for more.
    """

    @classmethod
    def validate(cls: Type["Model"], value: Any) -> Type["Model"]:
        if isinstance(value, cls):
            # Create, validate and return a new instance from the dict representation of `value`.
            # raises ValidationError if not.
            new_instance = cls(**value.dict())
            return super().validate(new_instance)
        return super().validate(value)

    @classmethod
    def validate_self(cls: Type["Model"], value: BaseModel, **dict_kwargs) -> Type["Model"]:
        # Similar to validate() but lets us customize the dict representation of `value`.
        assert isinstance(value, cls)
        new_instance = cls(**value.dict(**dict_kwargs))
        return super().validate(new_instance)
