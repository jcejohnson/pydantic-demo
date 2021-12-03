"""
This is to understand how Config.extra works.

See also: https://pydantic-docs.helpmanual.io/usage/model_config/

TL;DR - There are some surprises when you have properties on your Models both set/get and when exporting via dict()
"""

import pytest
from pydantic import BaseModel, Extra, ValidationError

DATA = {"thing1": "THING1", "thing2": "THING2", "thing3": "THING3", "thing4": "THING4"}

DATA4EXPORTS = {"thing1": "THING1", "thing2": "THING2", "thing3": "THING3", "thing4": "THING4", "thing5": "THING5"}


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

        # We can also add new fields whenever we want.

        assert not hasattr(data, "thing5")
        data.thing5 = "THING5"
        assert data.thing5 == "THING5"

    def test_forbid(self):
        class ExtrasForbid(BaseModel):
            class Config:
                extra = Extra.forbid

            thing1: str
            thing2: str
            thing3: str

        with pytest.raises(ValidationError):
            data = ExtrasForbid(**DATA)

        data = ExtrasForbid(**{"thing1": "THING1", "thing2": "THING2", "thing3": "THING3"})

        # We cannot add new fields whenever we want.

        with pytest.raises(ValueError):
            data.thing4 = "THING4"

    def test_ignore(self):
        class ExtrasIgnore(BaseModel):
            class Config:
                extra = Extra.ignore

            thing1: str
            thing2: str
            thing3: str

        data = ExtrasIgnore(**DATA)

        assert not hasattr(data, "thing4")

        # We cannot add new fields whenever we want.

        with pytest.raises(ValueError):
            data.thing4 = "THING4"


class TestExtraExporting:
    """
    How do extra fields behave when exporting a model?
    """

    def test_allow(self):
        """
        Extra fields are exported the same as declared fields.
        """

        class ExtrasAllow(BaseModel):
            class Config:
                extra = Extra.allow

            thing1: str
            thing2: str
            thing3: str

        for exclude in [True, False]:
            data = ExtrasAllow(**DATA4EXPORTS)
            dyct = data.dict(exclude_unset=exclude, exclude_none=exclude, exclude_defaults=exclude)
            assert "thing4" in dyct
            assert dyct["thing4"] == "THING4"

    def test_forbid(self):
        """
        Nothing to check here since the extra fields are not loaded.
        """
        pass

    def test_ignore(self):
        """
        Extra fields are never set on the Model and, therefore, not availalbe for dict() to export.
        """

        class ExtrasIgnore(BaseModel):
            class Config:
                extra = Extra.ignore

            thing1: str
            thing2: str
            thing3: str

        for exclude in [True, False]:
            data = ExtrasIgnore(**DATA4EXPORTS)
            dyct = data.dict(exclude_unset=exclude, exclude_none=exclude, exclude_defaults=exclude)
            assert "thing4" not in dyct


class TestExtraWithProperties:
    """
    What happens when a Model has properties that overlap with data provided when the Model is instantiated?
    """

    def test_class(self):
        """
        An @property without a setter is read-only and will raise AttributeError when attempting to set it.
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
        Some surprises. See comments.
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

        # This is as expected. The properties exist and return the function values.

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING1 - THING2 - THING3"

        assert hasattr(data, "thing5")
        assert data.thing5 == "THING1 - THING2"

        # Setting read-only properties does not fail and setting read-write properties does not invoke the setter.
        # In both cases, accessing the properties returns the functions' value.

        # Property thing4 is not read-only. Setting its value silently fails. I was expecting AttributeError.

        data.thing4 = "THING4"
        assert data.thing4 == "THING1 - THING2 - THING3"

        # The setter for property thing5 is silently ignored. I was expecting the RuntimeError.

        data.thing5 = "THING5"
        assert data.thing5 == "THING1 - THING2"

    def test_forbid(self):
        """
        Some surprises. See comments.
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

            @property
            def thing6(self):
                return f"{self.thing1} - {self.thing2}"

            @thing6.setter
            def thing6(self, value):
                this.thing1 = value
                this.thing2 = value
                this.thing3 = value

        with pytest.raises(ValidationError):
            # This fails.
            # Not because thing4 is a read-only property but because thing4 is not a declared field on the Model.
            # See below where we attempt to set thing4 and thing5.
            data = MyModel(**DATA)

        data = MyModel(**{"thing1": "THING1", "thing2": "THING2", "thing3": "THING3"})

        # This is as expected. The properties exist and return the function values.

        assert hasattr(data, "thing4")
        assert data.thing4 == "THING1 - THING2 - THING3"

        assert hasattr(data, "thing5")
        assert data.thing5 == "THING1 - THING2"

        # I was expecting AttributeError to be rasied (as it is for a non-Model object) but we get ValueError.

        assert hasattr(data, "thing4")
        with pytest.raises(ValueError):
            data.thing4 = "THING4"

        # I was expecting thing5's setter to be invoked but we get ValueError instead.

        with pytest.raises(ValueError):
            data.thing5 = "THING5"

        # I was expecting thing6's setter to be invoked but we get ValueError instead.
        # I included this just in case the RuntimeError was being caught & reraised.

        with pytest.raises(ValueError):
            data.thing6 = "THING6"

    def test_ignore(self):
        """
        When Config.extra == Extra.ignore the model acts exactly the same as in test_forbid WRT properties.
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

        # The thing4 property is now read-only but raises ValueError instead of AttributeError as a regular class
        # would.

        assert hasattr(data, "thing4")
        with pytest.raises(ValueError):
            data.thing4 = "THING4"

        # The thing5 property's setter is ignored and, instead, a ValueError is raised the same as with property
        # thing4.

        with pytest.raises(ValueError):
            data.thing5 = "THING5"
        assert data.thing5 == "THING1 - THING2"


class TestExtraExportingWithProperties:
    """
    What happens when you export a model that has properties?
    """

    def test_class(self):
        # Nothing to check here since a regular class cannot export itself.
        pass

    def test_allow(self):
        """
        Some surprises, see comments.
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

            @property
            def thing6(self):
                return f"{self.thing1} - {self.thing2} - {self.thing3}"

            @property
            def thing7(self):
                return f"{self.thing1} - {self.thing2}"

            @thing7.setter
            def thing7(self, value):
                raise RuntimeError("This will never be raised.")

        for exclude in [True, False]:

            data = MyModel(**DATA4EXPORTS)
            dyct = data.dict(exclude_unset=exclude, exclude_none=exclude, exclude_defaults=exclude)

            # As expected because thing4 & thing5 are provided when MyModel is created.
            # We know from TestExtraWithProperties that extra properties will be available and it is reasonable to
            # assume that dict() will include them.
            assert "thing4" in dyct
            assert "thing5" in dyct

            # As expected because thing6 & thing7 are not provided when MyModel is created and we have no expectation
            # that dict() would include properties which are, after all, methods on the instance.
            assert "thing6" not in dyct
            assert "thing7" not in dyct

            # This may be a little surprising. From TestExtraWithProperties we know that accessing the field
            # (data.thing4) actually invokes the property getter. So, it is not unreasonable to assume that the
            # dict() would include the property value. Instead, however, it includes the value provided when the Model
            # was created.

            with pytest.raises(AssertionError):
                assert dyct["thing4"] == "THING1 - THING2 - THING3"
            assert dyct["thing4"] == "THING4"  # From DATA4EXPORTS

            with pytest.raises(AssertionError):
                assert dyct["thing5"] == "THING1 - THING2"
            assert dyct["thing5"] == "THING5"  # From DATA4EXPORTS

        # TestExtraWithProperties tells us that we can set the properties if they were given values when the Model
        # was created. It also tells us that accessing the field will return the property value. From the test above
        # we expect that the dict() would include the set value rather than either the value provided to the Model's
        # instantiation or the property value.

        for exclude in [True, False]:

            data = MyModel(**DATA4EXPORTS)
            data.thing4 = "thing4"
            data.thing5 = "thing5"

            dyct = data.dict(exclude_unset=exclude, exclude_none=exclude, exclude_defaults=exclude)

            with pytest.raises(AssertionError):
                assert dyct["thing4"] == "THING1 - THING2 - THING3"
            assert dyct["thing4"] == "thing4"  # From `data.thing4 = "thing4"`

            with pytest.raises(AssertionError):
                assert dyct["thing5"] == "THING1 - THING2"
            assert dyct["thing5"] == "thing5"  # From `data.thing5 = "thing5"`

        # We get the same behavior when setting the extra fields thing6 & thing7.

        for exclude in [True, False]:

            data = MyModel(**DATA4EXPORTS)
            data.thing6 = "thing6"
            data.thing7 = "thing7"

            dyct = data.dict(exclude_unset=exclude, exclude_none=exclude, exclude_defaults=exclude)

            with pytest.raises(AssertionError):
                assert dyct["thing6"] == "THING1 - THING2 - THING3"
            assert dyct["thing6"] == "thing6"  # From `data.thing6 = "thing6"`

            with pytest.raises(AssertionError):
                assert dyct["thing7"] == "THING1 - THING2"
            assert dyct["thing7"] == "thing7"  # From `data.thing7 = "thing7"`

    def test_forbid(self):
        # Nothing to check here since the extra fields will not be set on the model and we have already established
        # that property values are not included by dict()
        pass

    def test_ignore(self):
        # TBD
        pass


class TestExtraWithOverlappingProperties:
    """
    Like TestExtraWithProperties but with properites explicitly overlapping declared fields
    """

    def test_nothing(self):
        class MyModel(BaseModel):
            class Config:
                extra = Extra.allow

            thing1: str
            thing2: str
            thing3: str
            thing4: str
            thing5: str

            @property
            def thing4(self):
                return f"{self.thing1} - {self.thing2} - {self.thing3}"

            @property
            def thing5(self):
                return f"{self.thing1} - {self.thing2}"

            @thing5.setter
            def thing5(self, value):
                raise RuntimeError("This will never be raised.")

        # assertions
