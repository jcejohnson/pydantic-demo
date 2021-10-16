from .base_model import BaseModel
from .mixin_versioned_model import VersionedModelMixin


class BaseVersionedModel(VersionedModelMixin, BaseModel):
    pass
