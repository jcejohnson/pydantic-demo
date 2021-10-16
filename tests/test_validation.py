"""
This is to understand how Model.validate() works.

TL;DR - MyModel.validate(myModel) doesn't work as expected.
        Do MyModel.validate(myModel.dict()) instead.
"""

from typing import TYPE_CHECKING, Any, Type, TypeVar

import pytest
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ValidationError

from aktorz.model.util.mixin_validate_self import ValidationMixin

if TYPE_CHECKING:
    Model = TypeVar("Model", bound="PydanticBaseModel")


class TestValidation:
    def test_validation(self):
        class MyModel(PydanticBaseModel):
            class Config:
                copy_on_model_validation = True

            thing1: str
            thing2: str

        data = {
            "thing1": "Thing 1",
            "thing2": "Thing 2",
        }

        assert isinstance(data, dict)

        assert MyModel.parse_obj(data) == MyModel(**data)

        model = MyModel.parse_obj(data)

        model.thing1 = dict()

        new_model = MyModel.validate(model)

        assert new_model == model
        assert new_model is not model

        """
        Why didn't validation fail with thing1 being a dict instead of a str?

        @classmethod
        def validate(cls: Type['Model'], value: Any) -> 'Model':
            if isinstance(value, cls):
                return value.copy() if cls.__config__.copy_on_model_validation else value
            ...
        """

        assert MyModel.__config__.copy_on_model_validation

        # OK, validate() delegates to copy() but copy doesn't validate
        # the fields. Assuming that the thing-to-copy is in a desirable
        # state seems reasonable.

        new_model = model.copy()
        new_model = model.copy(deep=True)

        """
        So, validating an instance of yourself seems to be a special case
        that may return a copy or the original instance but doesn't actually
        validate? That's fine but not what my usecases require.

        Let's see what else is happening in validate()

        @classmethod
        def validate(cls: Type['Model'], value: Any) -> 'Model':
            ...
            elif isinstance(value, dict):
                return cls(**value)
            ...

        So if we give validate() a dict, it will create a new model instance
        and we know that creating a new instance validates. Let's try that.
        """

        dmodel = model.dict()

        with pytest.raises(ValidationError) as exc_info:
            new_model = MyModel.validate(dmodel)

        assert exc_info.value.errors() == [{"loc": ("thing1",), "msg": "str type expected", "type": "type_error.str"}]

        """
        Failed as expected!
        """

    def test_other_model(self):

        # Use what we learned in test_validation

        class MyCustomBaseModel(PydanticBaseModel):
            @classmethod
            def validate(cls: Type["Model"], value: Any, **dict_kwargs) -> "Model":
                if isinstance(value, cls):
                    return cls.validate(value.dict(**dict_kwargs))
                return super().validate(value)  # type: ignore

            @classmethod
            def validate_self(cls: Type["Model"], value: PydanticBaseModel, **dict_kwargs) -> PydanticBaseModel:
                assert isinstance(value, cls)
                new_instance = cls(**value.dict(**dict_kwargs))  # type: ignore
                return super().validate(new_instance)  # type: ignore

        class MyOtherModel(MyCustomBaseModel):

            thing1: str
            thing2: str

        self._do_the_test(MyOtherModel)

    def test_final_model(self):

        # Verify that ValidationMixin behaves the same as MyCustomBase

        class MyFinalModel(ValidationMixin, PydanticBaseModel):

            thing1: str
            thing2: str

        self._do_the_test(MyFinalModel)

    def _do_the_test(self, clazz):

        data = {
            "thing1": "Thing 1",
            "thing2": "Thing 2",
        }

        model = clazz.parse_obj(data)

        assert clazz.validate(model)
        assert clazz.validate(model) == model
        assert clazz.validate(model) is not model

        model.thing1 = dict()

        with pytest.raises(ValidationError) as exc_info:
            clazz.validate(model)

        assert exc_info.value.errors() == [{"loc": ("thing1",), "msg": "str type expected", "type": "type_error.str"}]

        with pytest.raises(ValidationError) as exc_info:
            clazz.validate(model.dict(exclude_unset=True, exclude_none=True, exclude_defaults=True))

        assert exc_info.value.errors() == [{"loc": ("thing1",), "msg": "str type expected", "type": "type_error.str"}]

        with pytest.raises(ValidationError) as exc_info:
            clazz.validate_self(model, exclude_unset=True, exclude_none=True, exclude_defaults=True)

        assert exc_info.value.errors() == [{"loc": ("thing1",), "msg": "str type expected", "type": "type_error.str"}]
