from typing import NewType, Union

from .base_models import BaseModel, BaseVersionedModel
from .import_export import Exporter as BaseExporter
from .import_export import Loader as BaseLoader

# #### Constants

# 0.2.0 -> from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)

# #### Data types

# QUERY: Are there any reasonable constraints for a movie title?
MovieTitle = NewType("MovieTitle", str)

# https://en.wikipedia.org/wiki/History_of_film
#
# 0.1.0 : int
Year = NewType("Year", int)

# Object identifiers, keys in the json maps / python dicts.

#
# 0.1.0 : str
MovieId = NewType("MovieId", str)

#
# 0.1.0 : str
PersonId = NewType("PersonId", str)

# 0.1.0 : PersonId
ActorId = NewType("ActorId", PersonId)

# ### A custom Exporter for v0.1.x


class Loader(BaseLoader):
    def set_schema_version(self, model):
        assert isinstance(model, BaseModel)
        assert not isinstance(model, BaseVersionedModel)
        model[self.schema_version_field] = str(self.version)


class Exporter(BaseExporter):
    def set_schema_version(self, model):
        assert isinstance(model, BaseModel)
        assert not isinstance(model, BaseVersionedModel)
        model[self.schema_version_field] = str(self.version)

    def make_compatible(self, model: Union[BaseVersionedModel, BaseModel]) -> dict:
        assert isinstance(model, BaseModel)
        assert not isinstance(model, BaseVersionedModel)
        assert hasattr(model, self.schema_version_field)

        schema_version = str(self.get_schema_version(model=model))
        d = model.dict(include=self.get_includes(), exclude=self.get_excludes())
        d[self.schema_version_field] = schema_version

        return d
