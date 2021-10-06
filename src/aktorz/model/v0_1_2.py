from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import conint, validator

from . import BaseDictModel, BaseModel
from .v0_1_x import ActorId, Exporter, Loader, MovieId, MovieTitle, PersonId, SchemaVersion, Year  # noqa: F401

VERSION = SchemaVersion("v0.1.2")


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

    # Added after 0.1.3 due to changes to DictLikeMixin.__get_item__.
    @classmethod
    def validate(cls: Type["Model"], value: Any) -> "Model":
        # validate_name() is sufficient to set the `name` field but it does not add
        # `name` to the model instance's __fields_set__. And there doesn't appear to
        # be any way to get the model instance within validate_name(). However, we
        # can wrap the default validate() method and update __fields_set__ after the
        # default model validation.
        # Note that if we don't add `name` to __fields_set__ DictLikeMixin will not
        # recognize the field when it is set by validate_name().
        model = super().validate(value)
        assert model.name, f"{model} expected 'name' to be set by validate_name()."
        model.__fields_set__.add("name")
        return model


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
