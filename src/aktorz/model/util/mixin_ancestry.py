from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, PrivateAttr, root_validator, validator

# Mixins which add fields, validators or other things that pydantic
# needs to be aware of must subclass pydantic.BaseModel


class Progenitor(BaseModel):
    """
    Provide a private _progenitor (i.e. -- parent) field so that objects can
    point back to the object that contains them.
    """

    # TODO: Make this a collection in case instances are shared?
    _progenitor: Progenitor = PrivateAttr(None)

    # WARNING: This is NOT thread-safe.
    _ancestry: ClassVar[object] = list()

    # class Config:
    #     underscore_attrs_are_private = True

    def __init__(self, *args, **kwargs):
        Progenitor._ancestry.append(self)
        super().__init__(*args, **kwargs)

    @validator("*", always=True, check_fields=False)
    def _progenitor_set(cls, v, **kwargs):
        if isinstance(v, Progenitor):
            v._progenitor = cls._ancestry[-1]
        return v

    @root_validator
    def _progenitor_remove(cls, values):
        Progenitor._ancestry.pop()
        return values


"""
class SomeData(Progenitor, BaseModel):

    data: str = "Hello World"


class Model(Progenitor, BaseModel):

    some_data: SomeData = SomeData()
    more_data: SomeData = SomeData()
    foo: int = 9


m = Model()
assert m.some_data._progenitor == m
"""
