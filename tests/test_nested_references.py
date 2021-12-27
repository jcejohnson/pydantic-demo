import pdb

from pydantic import BaseModel


class TestNestedReferences:
    """
    What happens when we construct models with fields that are models?

    Hint: Config.copy_on_model_validation
    """

    def test_one(self):
        class Foo(BaseModel):
            class Config:
                copy_on_model_validation = True  # This is the default value

            name: str

        class Bar(BaseModel):
            class Config:
                copy_on_model_validation = True  # This is the default value

            foo: Foo

        foo = Foo(name="foober")

        bar = Bar(foo=foo)

        # When copy_on_model_validation is set, bar.foo is a _copy_ of foo

        assert bar.foo == foo
        assert id(bar.foo) != id(foo)  # id(x) returns the memory address of `x`
        assert bar.foo is not foo

    def test_two(self):
        class Foo(BaseModel):
            class Config:
                copy_on_model_validation = False

            name: str

        class Bar(BaseModel):
            class Config:
                copy_on_model_validation = False

            foo: Foo

        class Baz(BaseModel):
            class Config:
                copy_on_model_validation = False

            foo: Foo
            bar: Bar

        foo = Foo(name="foober")

        bar = Bar(foo=foo)

        baz = Baz(foo=foo, bar=bar)

        # When copy_on_model_validation is set, bar.foo _is_ foo

        assert bar.foo is foo
        assert baz.bar is bar
        assert bar.foo is foo

        d = baz.dict()

        # Unfortunately, the dict representations do not point to the same
        # location. This makes sense because pydantic creates a new dict for
        # each object.

        assert d["foo"] == d["bar"]["foo"]
        assert d["foo"] is not d["bar"]["foo"]
