"""
Additional base models with conflicting dependencies or that otherwise don't
make sense to belong to .base_model
"""

from .base_model import BaseModel
from .schema_version import SchemaVersionBase


# This may need to become a mixin so that it can be added to either BaseModel or CommentableBaseModel

class BaseVersionedModel(BaseModel):
    """
    Provides a schema_version property and a custom dict() method that will
    represent schema_version as a string.

    Added in v0.1.2
    """

    # 0.1.2 : SchemaVersion
    schema_version: SchemaVersionBase

    # 0.1.2
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        if not isinstance(result["schema_version"], str):
            result["schema_version"] = str(self.schema_version)
        return result
