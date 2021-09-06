from dataclasses import dataclass
from typing import Any, Dict, List, NewType, Optional, Tuple, Union

from pydantic import conint, constr, validator

from .base_model import BaseModel

# #### Constants

# 0.2.0 -> from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)
VERSION = SchemaVersion("v0.1.1")

# #### Data types

# QUERY: Are there any reasonable constraints for a movie title?
MovieTitle = NewType("MovieTitle", str)

# https://en.wikipedia.org/wiki/History_of_film
Year = NewType("Year", conint(ge=1850))  # type: ignore

# Object identifiers, keys in the json maps / python dicts.
MovieId = NewType("MovieId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore
PersonId = NewType("PersonId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore
ActorId = NewType("ActorId", PersonId)

# #### Model classes


def model(*args, **kwargs):
    return Model(*args, **kwargs)


class Person(BaseModel):
    """A human."""

    # 0.?.?
    # person_id: PersonId

    first_name: str
    last_name: str


class CastMember(BaseModel):
    """An actor performing as a character."""

    # 0.2.0 -> actor_id
    actor: ActorId

    # Added in 0.1.1
    # 0.2.0 -> character
    first_name: Optional[str]
    last_name: Optional[str]

    # 0.2.0 -> character
    # Made optional in 0.1.1 (See validate_name.)
    name: Optional[str]

    # `always` is required so that validate_name() is called when name is not provided.
    @validator("name", always=True)
    @classmethod
    def validate_name(cls, name, values):
        """
        Added in 0.1.1
        To be removed in 0.2.0 when our *name properties are replaced by `character`.
        full_name = [first_name, last_name].join(' ')
        raise VauleError if name is truthy but not equal to full_name
        """
        full_name = " ".join([n for n in [values["first_name"], values["last_name"]] if n])
        if name:
            if full_name and name != full_name:
                raise ValueError(f"name [{name}] != full_name [{full_name}]")
            return name
        if full_name:
            return full_name
        raise ValueError("Either `name` or `first/last_name` must be provided.")


class Movie(BaseModel):

    # 0.?.?
    # movie_id: MovieId

    title: MovieTitle

    cast: Optional[Dict[ActorId, CastMember]]

    budget: Optional[conint(ge=0)]  # type: ignore
    run_time_minutes: Optional[conint(ge=0)]  # type: ignore
    year: Optional[Year]


class Spouse(Person):
    """A human married to another human who may have created additional humans."""

    children: List[Person]


class Actor(Person):
    """A human who acts (performs) in movies."""

    # 0.?.?
    # actor_id: ActorId

    # 0.2.0 -> Dict[str, Movie]
    movies: Union[Dict[MovieId, Movie], List[Movie]]

    # 0.2.0 -> Merge this into movies
    filmography: Optional[List[Tuple[MovieTitle, Year]]]

    birth_year: Optional[Year]
    is_funny: Optional[bool]

    spouses: Optional[Dict[PersonId, Spouse]]

    hobbies: Optional[Dict[str, str]]


class Model(BaseModel):

    schema_version: SchemaVersion
    actors: Dict[ActorId, Actor]


# #### Import / Export


def exporter(*args, **kwargs):
    return Exporter(*args, **kwargs)


@dataclass
class Exporter:
    """
    Export a v0.1.1 model in a variety of formats and older versions.
    """

    model: Model
    version: Union[SchemaVersion, str]

    _data: Union[Dict[Any, Any], None] = None

    def dict(self):
        return self._transmute()

    def _transmute(self):
        if self._data:
            return self._data

        self._data = self.model.copy(deep=True).dict()
        self._data["schema_version"] = self.version

        # Remove the new fields added to CastMember
        for actor in self._data["actors"].values():
            iteron = actor["movies"] if isinstance(actor["movies"], list) else actor["movies"].values()
            for movie in iteron:
                if not movie["cast"]:
                    continue
                for cast_member in movie["cast"].values():
                    cast_member.pop("first_name")
                    cast_member.pop("last_name")

        return self._data
