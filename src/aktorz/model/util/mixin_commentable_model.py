import re
from typing import List, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Extra, Field, root_validator

COMMENT_REGEX = r"^(.*[_-])?comment$"


def is_comment(thing: str) -> bool:
    return re.match(COMMENT_REGEX, thing) is not None


# Mixins which add fields, validators or other things that pydantic
# needs to be aware of must subclass pydantic.BaseModel


class CommentableModelMixin(PydanticBaseModel):
    class Config:
        extra = Extra.allow
        # By default, only extra fields matching COMMENT_REGEX are allowed.
        # Set this to Extra.allow to allow all extra fields.
        # This basically restores Config.extra=Extra.allow when CommentableModelMixin is in play.
        commentable_mixin_extra = Extra.forbid

    comment: Union[List[str], str] = Field(
        None, description=f"A default comment field. Any field matching /{COMMENT_REGEX}/ is also allowed."
    )

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

        if getattr(cls.Config, "commentable_mixin_extra", Extra.forbid) == Extra.allow:
            return values

        for k, v in list(values.items()):
            if k in cls.__fields__:
                continue

            if not is_comment(k):
                raise ValueError(f'"{cls}" object has no field "{k}"')

        return values
