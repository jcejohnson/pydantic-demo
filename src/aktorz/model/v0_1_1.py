from typing import Dict, List, NewType, Optional, Tuple, Union

from pydantic import validator

from .base_model import BaseModel

# 0.2.0 -> from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)
VERSION = SchemaVersion("v0.1.1")

# QUERY: Are there any reasonable constraints for a movie title?
MovieTitle = NewType("MovieTitle", str)

# FIXME: Constrain to 4-digit positive int.
Year = NewType("Year", int)

# Object identifiers, keys in the json maps / python dicts.
MovieId = NewType("MovieId", str)
PersonId = NewType("PersonId", str)
ActorId = NewType("ActorId", PersonId)


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

    @validator("name")
    @classmethod
    def validate_name(cls, name, values):
        """
        Added in 0.1.1
        To be removed in 0.2.0 when *name attributes are replaced by `character`.
        full_name = [first_name, last_name].join(' ')
        raise VauleError if name is truthy but not equal to full_name
        """
        full_name = " ".join([n for n in [values["first_name"], values["last_name"]] if n])
        if name:
            if full_name and name != full_name:
                raise ValueError(f"name [{name}] != full_name [{full_name}]")
            return name
        return full_name


class Movie(BaseModel):

    # 0.?.?
    # movie_id: MovieId

    title: MovieTitle

    cast: Optional[Dict[ActorId, CastMember]]

    budget: Optional[int]
    run_time_minutes: Optional[int]
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
