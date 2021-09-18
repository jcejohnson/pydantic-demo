from typing import Dict, List, NewType, Optional, Tuple, Union

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
# 0.1.1 : conint(ge=1850)
# 0.1.0 : int
Year = NewType("Year", conint(ge=1850))  # type: ignore

# Object identifiers, keys in the json maps / python dicts.

# 0.1.1 : constr(regex=r"[a-z][a-z0-9_]+")
# 0.1.0 : str
MovieId = NewType("MovieId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore

# 0.1.1 : constr(regex=r"[a-z][a-z0-9_]+")
# 0.1.0 : str
PersonId = NewType("PersonId", constr(regex=r"[a-z][a-z0-9_]+"))  # type: ignore

# 0.1.0 : PersonId
ActorId = NewType("ActorId", PersonId)

# #### Model classes


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
