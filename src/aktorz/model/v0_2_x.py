from typing import NewType, Union

from . import BaseModel
from . import Exporter as BaseExporter
from . import Loader as BaseLoader
from . import VersionedModelMixin


class BaseVersionedModel(VersionedModelMixin, BaseModel):
    pass


# #### Constants


# #### Data types

from . import SchemaVersion

MovieTitle = NewType("MovieTitle", str)

Year = NewType("Year", int)

# Object identifiers, keys in the json maps / python dicts.

MovieId = NewType("MovieId", str)

PersonId = NewType("PersonId", str)
ActorId = NewType("ActorId", PersonId)
CharacterId = NewType("CharacterId", PersonId)


# ### A custom Exporter for v0.2.x


class Loader(BaseLoader):
    pass


class Exporter(BaseExporter):
    pass
