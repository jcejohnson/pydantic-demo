from typing import TYPE_CHECKING, Any, Type, TypeVar, cast

from pydantic import BaseModel

if TYPE_CHECKING:
    Model = TypeVar("Model", bound=BaseModel)


class ValidationMixin(object):
    """
    MyModel.validate(myModel) doesn't work the way that _I_ need.
    However, MyModel.validate(myModel.dict()) gets the job done.

    This mixin provides that functionality by implementing validate() as:
        validate(value.dict(by_alias=True, exclude_none=True, exclude_defaults=True))

    See tests/test_validation.py for more.
    """

    @classmethod
    def validate(cls: Type["Model"], value: Any) -> "Model":  # type: ignore
        return getattr(cls, "validate_self")(value, by_alias=True, exclude_none=True, exclude_defaults=True)

    @classmethod
    def validate_self(cls, value: Any, **dict_kwargs) -> "Model":
        # Similar to validate() but lets us customize the dict representation of `value`.
        if isinstance(value, cls):
            # Create, validate and return a new instance from the dict representation of `value`.
            # raises ValidationError if not.
            new_instance = getattr(cls, "parse_obj")(cast(BaseModel, value).dict(**dict_kwargs))
            value = new_instance
        return getattr(super(), "validate")(value)
