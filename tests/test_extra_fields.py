"""
This is to understand how Config.extra works.

See also: https://pydantic-docs.helpmanual.io/usage/model_config/

Config.extra == Extra.allow
    Fields will be created and populated from the input data even if they are
    not defined on the model.

Config.extra == Extra.forbid
    ValidationError will be raised if the input data provides fields that are
    not defined on the model.

Config.extra == Extra.ignore
    Fields provided by the input data that are not defined on the model will
    will be silently ignored (as if they did not exist in the input).

But when you introduce @property on your model, things get interesting.

"""

import pytest
from pydantic import BaseModel, Extra, ValidationError

DATA = {"thing1": "THING1", "thing2": "THING2", "thing3": "THING3", "thing4": "THING4"}


class TestExtra:
    def test_allow(self):
        class ExtrasAllow(BaseModel):
            class Config:
                extra = Extra.allow

            thing1: str
            thing2: str
            thing3: str

        data = ExtrasAllow(**DATA)

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING4"

    def test_forbid(self):
        class ExtrasForbid(BaseModel):
            class Config:
                extra = Extra.forbid

            thing1: str
            thing2: str
            thing3: str

        with pytest.raises(ValidationError):
            data = ExtrasForbid(**DATA)

    def test_ignore(self):
        class ExtrasIgnore(BaseModel):
            class Config:
                extra = Extra.ignore

            thing1: str
            thing2: str
            thing3: str

        data = ExtrasIgnore(**DATA)

        assert not hasattr(data, "thing4")

class TestExtraAndProperties:
    """
    What happens when you use @property to define read-only and read-write
    properties on a model...
    """

    def test_class(self):
        """
        An @property without a setter is read-only and will raise
        AttributeError when attempting to set it.
        """

        class MyClass(object):

            # A read-only property
            @property
            def thing4(self):
                return "foo - bar - baz"

            # A read-write property
            @property
            def thing5(self):
                if hasattr(self, "_thing5"):
                    return self._thing5
                return "foo - bar"

            @thing5.setter
            def thing5(self, value):
                self._thing5 = value

        data = MyClass()

        assert hasattr(data, "thing4")
        assert data.thing4 == "foo - bar - baz"
        with pytest.raises(AttributeError):
            data.thing4 = "THING4"

        assert hasattr(data, "thing5")
        assert data.thing5 == "foo - bar"

        data.thing5 = "THING5"
        assert data.thing5 == "THING5"

    def test_allow(self):
        """
        An @property without a setter is read-only but will not raise an
        exception when attempting to set it.
        An @property with a setter ignores the setter.
        """

        class MyModel(BaseModel):
            class Config:
                extra = Extra.allow

            thing1: str
            thing2: str
            thing3: str

            @property
            def thing4(self):
                return f"{self.thing1} - {self.thing2} - {self.thing3}"

            @property
            def thing5(self):
                return f"{self.thing1} - {self.thing2}"

            @thing5.setter
            def thing5(self, value):
                raise RuntimeError("This will never be raised.")

        data = MyModel(**DATA)

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING1 - THING2 - THING3"

        assert hasattr(data, "thing5")
        assert data.thing5 == "THING1 - THING2"

        # Property thing4 is not read-only. Setting its value silently fails.
        # Compare this to test_class()

        data.thing4 = "THING4"
        assert data.thing4 == "THING1 - THING2 - THING3"

        # The setter for property thing5 is also silently ignored.
        # Compare this to test_class()

        data.thing5 = "THING5"
        assert data.thing5 == "THING1 - THING2"

    def test_forbid(self):
        """
        An @property with or without a setter will raise ValueError.
        """

        class MyModel(BaseModel):
            class Config:
                extra = Extra.forbid

            thing1: str
            thing2: str
            thing3: str

            @property
            def thing4(self):
                return f"{self.thing1} - {self.thing2} - {self.thing3}"

            @property
            def thing5(self):
                return f"{self.thing1} - {self.thing2}"

            @thing5.setter
            def thing5(self, value):
                raise RuntimeError("This will never be raised.")

        with pytest.raises(ValidationError):
            # This fails.
            # Not because thing4 is a read-only property but because thing4
            # is not a declared field on the Model. See below where we attempt
            # to set thing4 and thing5.
            data = MyModel(**DATA)

        data = MyModel(**{"thing1": "THING1", "thing2": "THING2", "thing3": "THING3"})

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING1 - THING2 - THING3"

        assert hasattr(data, "thing5")
        assert data.thing5 == "THING1 - THING2"

        # The thing4 property is now read-only but raises ValueError instead of
        # AttributeError as a regular class would.
        # Compare this to test_class()

        assert hasattr(data, "thing4")
        with pytest.raises(ValueError):
            data.thing4 = "THING4"

        # The thing5 property's setter is ignored and, instead, a ValueError is
        # raised the same as with property thing4.
        # Compare this to test_class()

        with pytest.raises(ValueError):
            data.thing5 = "THING5"
        assert data.thing5 == "THING1 - THING2"


    def test_ignore(self):
        """
        When Config.extra == Extra.ignore the model acts exactly the same as in
        test_forbid WRT properties.
        """

        class MyModel(BaseModel):
            class Config:
                extra = Extra.ignore

            thing1: str
            thing2: str
            thing3: str

            @property
            def thing4(self):
                return f"{self.thing1} - {self.thing2} - {self.thing3}"

            @property
            def thing5(self):
                return f"{self.thing1} - {self.thing2}"

            @thing5.setter
            def thing5(self, value):
                raise RuntimeError("This will never be raised.")

        data = MyModel(**DATA)

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING1 - THING2 - THING3"

        assert hasattr(data, "thing5")
        assert data.thing5 == "THING1 - THING2"

        # The thing4 property is now read-only but raises ValueError instead of
        # AttributeError as a regular class would.
        # Compare this to test_class()

        assert hasattr(data, "thing4")
        with pytest.raises(ValueError):
            data.thing4 = "THING4"

        # The thing5 property's setter is ignored and, instead, a ValueError is
        # raised the same as with property thing4.
        # Compare this to test_class()

        with pytest.raises(ValueError):
            data.thing5 = "THING5"
        assert data.thing5 == "THING1 - THING2"



class TestExtraAndOverlappingProperties:
    """
    What happens when you use @property to define read-only and read-write
    properties that overlap/override fields on a model...
    """

    def test_nothing(self):
        return
