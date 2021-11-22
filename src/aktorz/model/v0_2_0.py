from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Field, conint

from . import BaseDictModel, BaseListModel, BaseModel, BaseVersionedModel
from . import Loader as BaseLoader
from .v0_2_x import PersonId  # noqa: F401
from .v0_2_x import ActorId, CharacterId, MovieId, MovieTitle, SchemaVersion, Year

VERSION = SchemaVersion.create("v0.2.0")

# #### Custom Loader


class Loader(BaseLoader):
    def can_read(self, other: Union[SchemaVersion, str]):
        """
        The v0.2.0 Loader can read v0.1.3 (the last v0.1.x implementation) data.
        No other v0.1.x data is supported.
        We can also read any version readable by SchemaVersion("v0.2.0")
            (i.e. - default behavior is maintained)
        """

        if self.module_version.can_read(other):
            # Default Loader behavior
            return True

        from .v0_1_3 import VERSION as v013

        if other == SchemaVersion.create(v013):
            # We can read v0.1.3 data
            return True

        # Fail if not natively compatible with v0.2.0 and is not v0.1.3
        raise ValueError(f"Model {VERSION} cannot read {other} data.")

    def make_compatible(self, data: dict, data_version: SchemaVersion) -> dict:
        """
        This is where we mutate `data` into a valid v0.2.0 dict if necessary.
        load_input() will always call this if validate_version() is successful.
        """

        if self.module_version.can_read(data_version):
            # In this example we will not mutate the data if it is compatible
            # with our module's version (i.e. -- Loader's default behavior).
            # In other scenarios we may want to mutate raw data that is, by default,
            # compatible with SchemaVersion("v0.2.0")
            return data

        from .v0_1_3 import VERSION as v013

        if data_version != SchemaVersion.create(v013):
            # We can only make v0.1.3 data compatible with ourselves.
            raise ValueError(f"Model {VERSION} cannot make {other} data compatible with {self.module_version}.")

        # There are a lot of clever things we could do to transmute the v0.1.3 data into
        # a v0.2.0 compatible dict. For this example we will use brute force to show the
        # worst-case scenario.

        result = {"schema_version": VERSION, "actors": {}, "movies": {}}

        self._migrate_actors(data, result)

        self._migrate_movies(data, result)

        return result

    def _migrate_actors(self, data, result):

        for actor_id, actor in data["actors"].items():

            result["actors"][actor_id] = {
                "person_id": actor_id,
                "birth_year": actor.get("birth_year", None),
                "first_name": actor["first_name"],
                "last_name": actor["last_name"],
                "gender": actor["gender"],
                "home_town": actor.get("home_town", None),
                "hobbies": actor.get("hobbies", None),
                "personality": "funny" if actor.get("is_funny", None) else None,
                "spouses": [],
                "movies": [],
            }

            self._migrate_actor_filmography(data, result, actor_id, actor)

            self._migrate_actor_movies(data, result, actor_id, actor)
            result["actors"][actor_id]["movies"] = sorted(set(result["actors"][actor_id]["movies"]))

            self._migrate_actor_spouses(data, result, actor_id, actor)
            if result["actors"][actor_id]["spouses"]:
                result["actors"][actor_id]["spouses"] = sorted(set(result["actors"][actor_id]["spouses"]))
            else:
                del result["actors"][actor_id]["spouses"]

    def _migrate_actor_filmography(self, data, result, actor_id, actor):

        # Blindly add actors movies to the list of movies.
        # In a real implementation we would look for duplicates, etc.

        if "filmography" not in actor:
            return

        for title, year in actor["filmography"]:
            movie_id = title.lower().replace(" ", "_")
            result["actors"][actor_id]["movies"].append(movie_id)
            result["movies"][movie_id] = {
                "title": title,
                "year": year,
            }

    def _migrate_actor_movies(self, data, result, actor_id, actor):

        if "movies" not in actor:
            return

        if isinstance(actor["movies"], dict):
            for movie_id, movie in actor["movies"].items():
                result["actors"][actor_id]["movies"].append(movie_id)
                result["movies"][movie_id] = movie
        elif isinstance(actor["movies"], list):
            for movie in actor["movies"]:
                movie_id = movie["title"].lower().replace(" ", "_")
                # copy/paste
                result["actors"][actor_id]["movies"].append(movie_id)
                result["movies"][movie_id] = movie
        else:
            raise Exception(f"Unknown movies object [{type(actor['movies'])}] of actor [{actor_id}]")

    def _migrate_actor_spouses(self, data, result, actor_id, actor):

        if "spouses" not in actor:
            return

        for spouse_id, spouse in actor["spouses"].items():
            result["actors"][actor_id]["spouses"].append(spouse_id)

            spouse["person_id"] = spouse_id

            # Assume spouses are actors.
            # v0.2.0['actors']  should have been v0.2.0['people']
            spouse["movies"] = []
            if spouse_id not in result["actors"]:
                result["actors"][spouse_id] = spouse

            # Hitch 'em
            spouses = spouse.get("spouses", [])
            spouses.append(actor_id)
            spouse["spouses"] = sorted(set(spouses))

            if spouse.pop("children", None):
                # Our sample v0.1.3 data does not include children.
                raise Exception("I cannot migrate children at this time.")

    def _migrate_movies(self, data, result):

        for movie_id, movie in result["movies"].items():
            movie["movie_id"] = movie_id

            if "cast" not in movie:
                continue

            cast = movie["cast"]
            movie["cast"] = {}
            for character_id, character in cast.items():
                actor_id = character["actor"]
                movie["cast"][actor_id] = {
                    "actor_id": actor_id,
                    "character_id": character_id,
                    "salary": character.get("salary", None),
                }
                character_name = character.get("name", None)
                character_name = character_name.split(" ") if character_name else ["Unknown", "Unknown"]
                character = {
                    "person_id": character_id,
                    "first_name": character.get("first_name", character_name[0]),
                    "last_name": character.get("last_name", character_name[1]),
                }

                if actor_id not in result["actors"]:
                    result["actors"][actor_id] = {
                        "person_id": actor_id,
                        "first_name": actor_id.split("_")[0],
                        "last_name": actor_id.split("_")[1],
                        "movies": [],
                    }


# #### Model classes


class Personality(str, Enum):

    FUNNY = "funny"


class SpouseList(BaseDictModel):
    __root__: List[PersonId]


class ChildList(BaseDictModel):
    __root__: List[PersonId]


class Person(BaseModel):

    person_id: PersonId

    first_name: str
    last_name: str
    birth_year: Optional[Year]
    gender: Optional[str]
    personality: Optional[Personality]
    spouses: Optional[SpouseList]
    children: Optional[ChildList]

    home_town: Optional[str]


class HobbiesById(BaseDictModel):
    __root__: Dict[str, str]


class MovieList(BaseListModel):
    __root__: List[MovieId]


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


class Character(Person):
    @property
    def character_id(self):
        return self.person_id

    @character_id.setter
    def character_id(self, value: PersonId):
        self.person_id = value


class CharactersById(BaseDictModel):
    __root__: Dict[CharacterId, Character]


class CastMember(BaseModel):
    """An actor performing as a character."""

    actor_id: ActorId
    character_id: CharacterId

    # type: ignore
    salary: Optional[conint(ge=0)] = Field(description="millions $USD")  # type: ignore


class CastMembersById(BaseDictModel):
    __root__: Dict[ActorId, CastMember]


class Movie(BaseModel):

    movie_id: MovieId

    cast: Optional[CastMembersById]
    characters: Optional[CharactersById]

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


class Model(BaseVersionedModel):

    actors: ActorsById
    movies: MoviesById
