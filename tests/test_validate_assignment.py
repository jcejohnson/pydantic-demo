import pytest
from pydantic import BaseModel, ValidationError


class Foo(BaseModel):
    class Config:
        validate_assignment = True

    thing1: str
    thing2: int


class Bar(BaseModel):
    class Config:
        validate_assignment = False

    thing1: str
    thing2: int


class Baz(BaseModel):
    class Config:
        validate_assignment = True

    thing1: str
    thing2: int

    def __setattr__(self, name, value):
        if name == "thing2" and isinstance(value, str):
            value = len(value)
        return super().__setattr__(name, value)


class TestValidateAssignment:
    def test_obj(self):

        obj = Bar(thing1="thing1", thing2=22)

        obj.thing1 = "Thing 1"
        obj.thing2 = 2

        assert obj.thing1 == "Thing 1"
        assert obj.thing2 == 2

        # No coercion
        obj.thing1 = 1
        assert obj.thing1 == 1

        # No assignment validation
        obj.thing2 = "Thing 2"
        assert obj.thing2 == "Thing 2"

    def test_invalid_init(self):

        # Config.validate_assignment=False does not mess
        # with initialization validation. Nor should it.

        with pytest.raises(ValidationError):
            Bar(thing1=dict(), thing2=22)

        with pytest.raises(ValidationError):
            Bar(thing1="Thing 1", thing2="Thing 2")

        with pytest.raises(ValidationError):
            Foo(thing1=dict(), thing2=22)

        with pytest.raises(ValidationError):
            Foo(thing1="Thing 1", thing2="Thing 2")

        with pytest.raises(ValidationError):
            Baz(thing1=dict(), thing2=22)

        with pytest.raises(ValidationError):
            # initialization validation does not use Baz's
            # custom __setattr__()
            Baz(thing1="Thing 1", thing2="Thing 2")

    def test_coercion(self):

        obj = Foo(thing1="thing1", thing2=22)

        obj.thing1 = 1  # pydantic coerces 1 into "1"
        obj.thing2 = "2"  # pydantic coerces "2" into 2

        assert obj.thing1 == "1"
        assert obj.thing2 == 2

    def test_invalid_assignments(self):

        obj = Foo(thing1="thing1", thing2=22)

        with pytest.raises(ValidationError):
            obj.thing1 = dict()

        with pytest.raises(ValidationError):
            obj.thing2 = "Thing 2"

        with pytest.raises(ValidationError):
            obj.thing2 = dict()

    def test_custom_setattr(self):

        obj = Baz(thing1="thing1", thing2=22)

        obj.thing1 = "Thing 1"
        assert obj.thing1 == "Thing 1"

        # Baz.__setattr__ converts string value to its length
        obj.thing2 = "Thing 2"
        assert obj.thing2 == 7
