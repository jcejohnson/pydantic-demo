from typing import Any, Dict, Generic, TypeVar, Union

import pytest
from pydantic import BaseModel, ValidationError, constr, validate_arguments
from pydantic.generics import GenericModel

CommentKey = TypeVar("CommentKey", bound=constr(regex=r"(?:.*-)?comment"))  # type: ignore # noqa: F722
FooOrBar = TypeVar("FooOrBar", bound=constr(regex=r"foo|bar"))  # type: ignore # noqa: F821
FooBarOrComment = TypeVar("FooBarOrComment", bound=Union[FooOrBar, CommentKey])  # type: ignore


class StaticDictLikeThing(BaseModel):
    """
    This is the traditional way I would implement a Model that behaves
    like a dict and ensures that keys are properly constrained.
    """

    __root__: Dict[FooBarOrComment, str]  # type: ignore

    @validate_arguments
    def __getattr__(self, item: FooBarOrComment):
        return self.__root__[item]

    @validate_arguments
    def __setattr__(self, item: FooBarOrComment, value):
        self.__root__[item] = value

    @validate_arguments
    def __getitem__(self, item: FooBarOrComment):
        return self.__root__[item]

    @validate_arguments
    def __setitem__(self, item: FooBarOrComment, value):
        self.__root__[item] = value


class DictLikeMixin:
    """
    Mixin for a pydantic custom root model.
    Adds dict-like behavior but not data (assumes self.__root__ is Mappable).

    Subclasses can override ___validate_item___ to validate keys and/or
    __validate_value__ to validate value types.

    I'm not using @validate_arguments here because we want the mixing to
    support any types for key/value.
    """

    def __getattr__(self, item: Any):
        self.__validate_item__(item)
        return self.__root__[item]

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


class StaticDictLikeThingWithMixin(DictLikeMixin, BaseModel):
    """
    Similar to StaticDictLikeThing but taking the dict-like methods from DictLikeMixin.
    Note that we provide __validate_*__() for DictLikeMixin to validate the key/value types.
    Spoiler alert: This is my favorite.
    """

    __root__: Dict[FooBarOrComment, str]  # type: ignore

    @validate_arguments
    def __validate_item__(self, item: FooBarOrComment):
        return True

    @validate_arguments
    def __validate_value__(self, item: str):
        return True


GDLTKeyT = TypeVar("GDLTKeyT")
GDLTValueT = TypeVar("GDLTValueT")


class GenericDictLikeThing(DictLikeMixin, GenericModel, Generic[GDLTKeyT, GDLTValueT]):
    """
    Similar to StaticDictLikeThingWithMixin but we allow the dictionary's key and value types
    to be specified through generics.
    """

    __root__: Dict[GDLTKeyT, GDLTValueT]  # type: ignore


class DictLikeThingFromGeneric(GenericDictLikeThing[FooBarOrComment, str]):
    """
    Similar to StaticDictLikeThingWithMixin but GenericDictLikeThing provides the underlying
    dictionary. This is a nice data vs behavior separation.
    """

    @validate_arguments
    def __validate_item__(self, item: FooBarOrComment):
        return True

    @validate_arguments
    def __validate_value__(self, item: str):
        return True


class DictLikeThing(DictLikeMixin, BaseModel):
    """
    This is StaticDictLikeThingWithMixin with a better name.
    Generics actually make typechecking more difficult in this
    usecase so I think I like this implementation best.
    """

    __root__: Dict[FooBarOrComment, str]  # type: ignore

    @validate_arguments
    def __validate_item__(self, item: FooBarOrComment):
        return True

    @validate_arguments
    def __validate_value__(self, item: str):
        return True


class TestRootAsDict:

    # Iterate through all of our implementations to be sure they behave identically.
    @pytest.fixture(
        params=[DictLikeThing, StaticDictLikeThing, StaticDictLikeThingWithMixin, DictLikeThingFromGeneric]
    )
    def clazz(self, request):
        return request.param

    def test_properties(self, clazz):

        data = clazz.parse_obj({"foo": "bar", "bar": "baz", "my-comment": "Hello World", "comment": "Heya"})

        assert data["my-comment"] == "Hello World"

        assert data.foo == "bar"
        assert data.bar == "baz"
        assert data.comment == "Heya"

        data.foo = "bar"
        data.bar = "baz"
        data.comment = "Heya"

        with pytest.raises(ValidationError):
            data.baz = "bug"

        data.validate(data)

    def test_indexing(self, clazz):

        data = clazz.parse_obj({"foo": "bar", "bar": "baz", "my-comment": "Hello World", "comment": "Heya"})

        assert data["my-comment"] == "Hello World"

        assert data["foo"] == "bar"
        assert data["bar"] == "baz"
        assert data["comment"] == "Heya"

        data["foo"] = "bar"
        data["bar"] = "baz"
        data["comment"] = "Heya"
        with pytest.raises(ValidationError):
            data["baz"] = "bug"

        data.validate(data)

    def test_bad_input(self, clazz):

        with pytest.raises(ValidationError):
            data = clazz.parse_obj(
                {"foo": "bar", "bar": "baz", "baz": "bug", "my-comment": "Hello World", "comment": "Heya"}
            )

            assert data
