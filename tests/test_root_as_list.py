from typing import List

from pydantic import BaseModel

# FIXME: Expand this similar to test_root_as_dict


class ListLikeMixin:
    def __getitem__(self, item):
        return self.__root__[item]

    def __getattr__(self, name):
        return self.__root__[int(name.replace("i", ""))]


class ListLikeThing(ListLikeMixin, BaseModel):
    __root__: List[str]


class TestRootAsList:
    def test_list_like_thing(self):

        data = ListLikeThing.parse_obj([1, "two", "three"])

        assert data[0] == "1"  # Note pydantic has converted the int to a str
        assert data[1] == "two"
        assert data[2] == "three"

        assert data.i0 == "1"  # Note pydantic has converted the int to a str
        assert data.i1 == "two"
        assert data.i2 == "three"
