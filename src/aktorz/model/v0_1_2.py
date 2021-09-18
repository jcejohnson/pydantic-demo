from dataclasses import dataclass
from typing import Any, Dict, List, NewType, Optional, Tuple, Union

from pydantic import conint, constr, validator

from .base_model import BaseDictModel, BaseModel


# #### Constants


# 0.2.0 : from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)
VERSION = SchemaVersion("v0.1.2")

# #### Data types

# QUERY: Are there any reasonable constraints for a movie title?
MovieTitle = NewType("MovieTitle", str)

# https://en.wikipedia.org/wiki/History_of_film
# 0.1.0 : int
# 0.1.1 : conint(ge=1850)
Year = NewType("Year", conint(ge=1850))  # type: ignore

# Object identifiers, keys in the json maps / python dicts.

# 0.1.0 : str
# 0.1.1 : constr(regex=r"[a-z][a-z0-9_]+")
MovieId = NewType("MovieId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore

# 0.1.0 : str
# 0.1.1 : constr(regex=r"[a-z][a-z0-9_]+")
PersonId = NewType("PersonId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore

# 0.1.0 : PersonId
ActorId = NewType("ActorId", PersonId)

# #### Model classes


def model(*args, **kwargs):
    """Construct and return a Model instance"""
    return Model(*args, **kwargs)


class Person(BaseModel):
    """A human."""

    # 0.?.?
    # person_id: PersonId

    # 0.1.0 : str
    first_name: str

    # 0.1.0 : str
    last_name: str


class CastMember(BaseModel):
    """An actor performing as a character."""

    # 0.1.0 : ActorId
    # 0.2.0 : actor_id
    actor: ActorId

    # 0.2.0 : Replaces both first_name & last_name with Character

    # 0.1.1 : Optional[str]
    first_name: Optional[str]

    # 0.1.1 : Optional[str]
    last_name: Optional[str]

    # 0.1.0 : str
    # 0.1.1 : made optional (See validate_name.)
    # 0.2.0 : character
    name: Optional[str]

    # `always` is required so that validate_name() is called when name is not provided.
    @validator("name", always=True)
    @classmethod
    # Added in 0.1.1
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


# Added in v0.1.2
class CastById(BaseDictModel):
    __root__: Dict[ActorId, CastMember]


class Movie(BaseModel):

    # 0.?.?
    # movie_id: MovieId

    # 0.1.0 : MovieTitle
    title: MovieTitle

    # 0.1.0 : Optional[Dict[ActorId, CastMember]]
    # 0.1.2 : Optional[CastById]
    cast: Optional[CastById]

    # 0.1.0 : Optional[int]
    # 0.1.1 : Optional[conint(ge=0)]
    budget: Optional[conint(ge=0)]  # type: ignore

    # 0.1.0 : Optional[int]
    # 0.1.1 : Optional[conint(ge=0)]
    run_time_minutes: Optional[conint(ge=0)]  # type: ignore

    # 0.1.0 : Optional[Year]
    year: Optional[Year]


# Added in v0.1.2
class MoviesById(BaseDictModel):
    __root__: Dict[MovieId, Movie]


class Spouse(Person):
    """A human married to another human who may have created additional humans."""

    # 0.1.0 : List[Person]
    children: List[Person]


# Added in v0.1.2
class SpousesById(BaseDictModel):
    __root__: Dict[PersonId, Spouse]


# Added in v0.1.2
class HobbiesById(BaseDictModel):
    __root__: Dict[str, str]


class Actor(Person):
    """A human who acts (performs) in movies."""

    # 0.?.?
    # actor_id: ActorId

    # 0.1.0 : Union[Dict[MovieId, Movie], List[Movie]]
    # 0.1.2 : Union[MoviesById, List[Movie]]
    # 0.2.0 : MoviesById
    movies: Union[MoviesById, List[Movie]]

    # 0.1.0 : Optional[List[Tuple[MovieTitle, Year]]]
    # 0.2.0 : Merge this into movies
    filmography: Optional[List[Tuple[MovieTitle, Year]]]

    # 0.1.0 : Optional[Year]
    birth_year: Optional[Year]

    # 0.1.0 : Optional[bool]
    is_funny: Optional[bool]

    # 0.1.0 : Optional[Dict[PersonId, Spouse]]
    # 0.1.2 : Optional[SpousesById]
    spouses: Optional[SpousesById]

    # 0.1.0 : Optional[Dict[str, str]]
    # 0.1.2 : Optional[HobbiesById]
    hobbies: Optional[HobbiesById]


# Added in v0.1.2
class ActorsById(BaseDictModel):
    __root__: Dict[ActorId, Actor]


class Model(BaseModel):

    # 0.1.0 : SchemaVersion
    schema_version: SchemaVersion

    # 0.1.0 : Dict[ActorId, Actor]
    # 0.1.2 : ActorsById
    actors: ActorsById


# #### Import / Export


def exporter(*args, **kwargs):
    """Construct and return an Exporter instance"""
    return Exporter(*args, **kwargs)


@dataclass
class Exporter:
    """
    Export a v0.1.1 model in a variety of formats and older versions.
    """

    SUPPORTED_VERSIONS = ["v0.1.0", "v0.1.1", VERSION]

    model: Model
    version: Union[SchemaVersion, str]

    _data: Union[Dict[Any, Any], None] = None

    def dict(self) -> Dict[Any, Any]:
        return self._transmute()

    def json(self, *args, **kwargs) -> str:
        import json as dumper

        return dumper.dumps(self._transmute(), *args, **kwargs)

    def _transmute(self) -> Dict[Any, Any]:

        if self.version not in Exporter.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Exporter {VERSION} cannot export {self.version}." f"Must be one of {Exporter.SUPPORTED_VERSIONS}"
            )

        if self._data:
            return self._data

        self._data = self.model.copy(deep=True).dict()

        if self.version == VERSION:
            return self._data

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

        # Other v0.1.1 changes (e.g. - various constraints) do not break compatibility

        # I should be able to do this but I can't figure out how (or if pydantic)
        # even supports such a thing.
        # See: https://github.com/samuelcolvin/pydantic/discussions/3193
        #
        # self._data = self.model.dict(
        #     exclude={
        #         'actors': {
        #             '__all__': {
        #                 'movies': {
        #                     '__all__': {
        #                         'cast': {
        #                             '__all__':
        #                                 {'first_name': ..., 'last_name': ...}
        #                         }
        #                     }
        #                 }
        #             }
        #         }
        #     }
        # )

        return self._data
