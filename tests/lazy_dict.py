"""
This is to explore lazy-loading of dict data.
"""

import os.path as os_path
import json

from collections import UserDict
from typing import Generic, TypeVar, Dict

from pydantic import BaseModel, Field, root_validator, ValidationError
from pydantic.generics import GenericModel

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


class LazyDict(GenericModel, Generic[KeyT, ValueT], UserDict):
    """
    doc...

    Instances of LazyDict are _not_ dicts:

        d = LazyDict(...)
        assert not isinstance(d, dict)

    Use MutableMapping instead:

        d = LazyDict(...)
        assert isinstance(d, MutableMapping)

    It is safe to replace `dict` with `MutableMapping` for any isinstance():

        d = dict()
        assert isinstance(d, MutableMapping)
        assert isinstance(dict(), MutableMapping)
        d = {}
        assert isinstance(d, MutableMapping)
        assert isinstance({}, MutableMapping)
    """

    # Loaded from the json.
    lazy_ref: str = Field(..., alias="$ref")

    # Populated by LazyModel's lazy_dict_initializer() root_validator.
    lazy_root: str = Field(default=None, alias="$root_path")

    # Populated when UserDict accesses self.data.
    lazy_data: Dict[KeyT, ValueT] = Field(default=None)

    @property
    def data(self) -> Dict[KeyT, ValueT]:
        assert self.lazy_ref
        assert self.lazy_root

        if not self.lazy_data:
            import pdb ; pdb.set_trace()
            with open(os_path.join(self.lazy_root, self.lazy_ref)) as f:
                self.lazy_data = json.load(f)

        return self.lazy_data

    @data.setter
    def data(self, value):
        print("!!!!! HELLO World: data.setter")


class LazyModel(BaseModel):

    lazy_root: str = Field(..., alias="$root_path")

    @root_validator(skip_on_failure=True)
    @classmethod
    def lazy_dict_initializer(cls, values):

        if not os_path.isdir(values["lazy_root"]):
            values["lazy_root"] = os_path.dirname(values["lazy_root"])

        for key, value in values.items():
            if isinstance(value, LazyDict):
                value.lazy_root = values["lazy_root"]

        return values
