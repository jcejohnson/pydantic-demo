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
    def validate(cls: Type["Model"], value: Any) -> "Model":  # type: ignore
        return getattr(cls, "validate_self")._validate_self_(value)

    @classmethod
    def validate_self(cls, value: Any, **dict_kwargs) -> "Model":
        # Similar to validate() but lets us customize the dict representation of `value`.
        if isinstance(value, cls):
            # Create, validate and return a new instance from the dict representation of `value`.
            # raises ValidationError if not.
            new_instance = getattr(cls, "parse_obj").value.dict(**dict_kwargs)
            value = new_instance
        assert isinstance(value, cls)
        return getattr(super(), "validate").validate(value)
