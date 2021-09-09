from typing import Dict, List, NewType, Optional, Tuple, Union

from .base_model import BaseModel

# #### Constants

# 0.2.0 -> from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)
VERSION = SchemaVersion("v0.1.0")

# #### Data types

MovieTitle = NewType("MovieTitle", str)
MovieId = NewType("MovieId", str)
Year = NewType("Year", int)
PersonId = NewType("PersonId", str)
ActorId = NewType("ActorId", PersonId)

# #### Model classes


class Person(BaseModel):

    # 0.1.0 : str
    first_name: str

    # 0.1.0 : str
    last_name: str


class CastMember(BaseModel):

    # 0.1.0 : ActorId
    # 0.2.0 : actor_id
    actor: ActorId

    # 0.1.0 : str
    # 0.2.0 : character
    name: str


class Movie(BaseModel):

    # 0.1.0 : MovieTitle
    title: MovieTitle

    # 0.1.0 : Optional[Dict[ActorId, CastMember]]
    cast: Optional[Dict[ActorId, CastMember]]

    # 0.1.0 : Optional[int]
    budget: Optional[int]

    # 0.1.0 : Optional[int]
    run_time_minutes: Optional[int]

    # 0.1.0 : Optional[Year]
    year: Optional[Year]


class Spouse(Person):
    # 0.1.0 : List[Person]
    children: List[Person]


class Actor(Person):

    # 0.1.0 : Union[Dict[MovieId, Movie], List[Movie]]
    # 0.2.0 : MoviesById
    movies: Union[Dict[MovieId, Movie], List[Movie]]

    # 0.1.0 : Optional[List[Tuple[MovieTitle, Year]]]
    # 0.2.0 : Merge this into movies
    filmography: Optional[List[Tuple[MovieTitle, Year]]]

    # 0.1.0 : Optional[Year]
    birth_year: Optional[Year]

    # 0.1.0 : Optional[bool]
    is_funny: Optional[bool]

    # 0.1.0 : Optional[Dict[PersonId, Spouse]]
    spouses: Optional[Dict[PersonId, Spouse]]

    # 0.1.0 : Optional[Dict[str, str]]
    hobbies: Optional[Dict[str, str]]


class Model(BaseModel):

    # 0.1.0 : SchemaVersion
    schema_version: SchemaVersion

    # 0.1.0 : Dict[ActorId, Actor]
    actors: Dict[ActorId, Actor]


# #### Import / Export

# Nothing here for v0.1.0
