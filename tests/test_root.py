from typing import Dict, List, Union

from pydantic import BaseModel, constr

comment = constr(regex=r"(?:.*-)?comment")


class FooLikeMixin:
    def __getitem__(self, item):
        return self.__root__[item]


class DictLikeMixin(FooLikeMixin):
    def __getattr__(self, name):
        return self.__root__[name]


class ListLikeMixin(FooLikeMixin):
    def __getattr__(self, name):
        return self.__root__[int(name.replace("i", ""))]


valid_dict_keys = constr(regex=r"foo|bar")


class DictLikeThing(BaseModel, DictLikeMixin):
    __root__: Dict[Union[valid_dict_keys, comment], str]


class ListLikeThing(ListLikeMixin, BaseModel):
    __root__: List[str]


class TestRoot:
    def test_dict_like_thing(self):

        data = DictLikeThing.parse_obj({"foo": "bar", "bar": "baz", "my-comment": "Hello World", "comment": "Heya"})

        assert data["my-comment"] == "Hello World"

        assert data.foo == "bar"
        assert data.bar == "baz"
        assert data.comment == "Heya"

        assert data["foo"] == "bar"
        assert data["bar"] == "baz"
        assert data["comment"] == "Heya"

    def test_list_like_thing(self):

        data = ListLikeThing.parse_obj([1, "two", "three"])

        assert data[0] == "1"  # Note pydantic has converted the int to a str
        assert data[1] == "two"
        assert data[2] == "three"

        assert data.i0 == "1"  # Note pydantic has converted the int to a str
        assert data.i1 == "two"
        assert data.i2 == "three"
