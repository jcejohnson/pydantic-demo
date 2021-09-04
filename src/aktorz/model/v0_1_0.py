from typing import Dict, List, NewType, Optional, Tuple, Union

from .base_model import BaseModel

# 0.2.0 -> from . import SchemaVersion
SchemaVersion = NewType("SchemaVersion", str)
VERSION = SchemaVersion("v0.1.0")


MovieTitle = NewType("MovieTitle", str)
MovieId = NewType("MovieId", str)
Year = NewType("Year", int)
PersonId = NewType("PersonId", str)
ActorId = NewType("ActorId", PersonId)


class Person(BaseModel):
    first_name: str
    last_name: str


class CastMember(BaseModel):

    # 0.2.0 -> actor_id
    actor: ActorId

    # 0.2.0 -> character
    name: str


class Movie(BaseModel):
    title: MovieTitle

    cast: Optional[Dict[ActorId, CastMember]]

    budget: Optional[int]
    run_time_minutes: Optional[int]
    year: Optional[Year]


class Spouse(Person):
    children: List[Person]


class Actor(Person):

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
