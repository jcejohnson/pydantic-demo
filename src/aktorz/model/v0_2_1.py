from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field, conint

from . import BaseDictModel, BaseListModel, BaseModel
from .v0_2_x import PersonId  # noqa: F401
from .v0_2_x import ActorId, CharacterId, MovieId, MovieTitle, SchemaVersion, Year

VERSION = SchemaVersion.create("v0.2.1")


# #### Model classes


class Personality(str, Enum):

    FUNNY = "funny"


class Person(BaseModel):

    person_id: PersonId

    first_name: str
    last_name: str
    birth_year: Optional[Year]
    gender: Optional[str]
    personality: Personality

    home_town: Optional[str]


class HobbiesById(BaseDictModel):
    __root__: Dict[str, str]


class MovieList(BaseListModel):
    __root__: List[MovieId]


class SpousesById(BaseDictModel):
    __root__: Dict[PersonId, Person]


class Actor(Person):
    """A person who performs in movies."""

    @property
    def actor_id(self):
        return self.person_id

    @actor_id.setter
    def actor_id(self, value: PersonId):
        self.person_id = value

    hobbies: Optional[HobbiesById]
    movies: MovieList
    spouses: Optional[SpousesById]


class Character(Person):
    @property
    def character_id(self):
        return self.person_id

    @character_id.setter
    def character_id(self, value: PersonId):
        self.person_id = value


class CastMember(BaseModel):
    """An actor performing as a character."""

    actor: ActorId
    character: CharacterId

    # type: ignore
    salary: Optional[conint(ge=0)] = Field(description="millions $USD")  # type: ignore


class CastById(BaseDictModel):
    __root__: Dict[ActorId, CastMember]


class Movie(BaseModel):

    movie_id: MovieId

    cast: Optional[CastById]

    title: MovieTitle
    run_time_minutes: Optional[conint(ge=0)]  # type: ignore
    year: Optional[Year]

    # type: ignore
    budget: Optional[conint(ge=0)] = Field(description="millions $USD")  # type: ignore

    # type: ignore
    gross: Optional[conint(ge=0)] = Field(description="millions $USD")  # type: ignore


class MoviesById(BaseDictModel):
    __root__: Dict[MovieId, Movie]


class ActorsById(BaseDictModel):
    __root__: Dict[ActorId, Actor]


class Model(BaseModel):

    schema_version: SchemaVersion

    actors: ActorsById
    movies: MoviesById
