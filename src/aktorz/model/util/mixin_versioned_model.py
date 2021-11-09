from pydantic import BaseModel as PydanticBaseModel
from pydantic import validator

from .schema_version import SchemaVersion

# Mixins which add fields, validators or other things that pydantic
# needs to be aware of must subclass pydantic.BaseModel


class VersionedModelMixin(PydanticBaseModel):
    """
    Provides a schema_version property and a custom dict() method that will
    represent schema_version as a string.

    Added in v0.1.2
    """

    # 0.1.2 : SchemaVersion
    schema_version: SchemaVersion

    # > 0.1.3
    # Use `pre=True` since we may be doing a type conversion.
    # Otherwise we will get a `value is not a valid dict (type=type_error.dict)`
    # error if a string is provided.
    @validator("schema_version", pre=True)
    @classmethod
    def validate_schema_version(cls, schema_version):
        if isinstance(schema_version, SchemaVersion):
            return schema_version
        if isinstance(schema_version, str):
            return SchemaVersion.create(schema_version)
        raise TypeError("schema_version must be str or SchemaVersion")

    # 0.1.2
    def dict(self, *args, **kwargs):
        # Represent schema_version as a simple string when exporting the model.
        result = super().dict(*args, **kwargs)
        if not isinstance(result["schema_version"], str):
            result["schema_version"] = str(self.schema_version)
        return result
