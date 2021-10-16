# Mixins which do not add add fields, validators or other things that pydantic
# needs to be aware of are not required to subclass pydantic.BaseModel


class ArbitraryTypeMixin(object):

    # I don't know if this will be generally useful but I'm
    # implementing it as a mixin just in case.

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return v
