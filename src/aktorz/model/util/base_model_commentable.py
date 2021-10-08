import re

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra, root_validator

from .dict_like_mixin import DictLikeMixin
from .validation_mixin import ValidationMixin

COMMENT_REGEX = r"^(.*[_-])?comment$"


def is_comment(thing: str) -> bool:
    return re.match(COMMENT_REGEX, thing) is not None


# This doesn't work as a mixin. I don't know why.


class CommentableBaseModel(ValidationMixin, PydanticBaseModel):
    class Config:
        extra = Extra.allow

    def __setattr__(self, field, value):
        # Allows obj.some_comment
        if field in self.__fields__ or re.match(COMMENT_REGEX, field):
            object.__setattr__(self, field, value)
            self.__fields_set__.add(field)
            return

        raise ValueError(f'"{self.__class__.__name__}" object has no field "{field}"')

    @root_validator
    @classmethod
    def check_extra_fields(cls, values: dict):
        """Make sure extra fields are only comments."""

        for k, v in list(values.items()):
            if k in cls.__fields__:
                continue

            if not is_comment(k):
                raise ValueError(f'"{cls}" object has no field "{k}"')

        return values


class CommentableDictLikeBaseModel(DictLikeMixin, CommentableBaseModel):

    pass
