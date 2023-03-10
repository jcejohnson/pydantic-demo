"""
This is to explore lazy-loading of dict data.

The schema here is a modified version of the v0.2.0 schema.
"""


from collections import UserDict
from typing import Generic, TypeVar, Dict

from pydantic import BaseModel, Field, constr, root_validator, ValidationError
from pydantic.generics import GenericModel

from aktorz.model.v0_2_x import ActorId, MovieId, SchemaVersion

from .lazy_dict import LazyDict, LazyModel


class Actor(LazyModel):
    pass


class Movie(LazyModel):
    pass


class ActorsById(LazyDict[ActorId, Actor]):
    pass


class Model(LazyModel):

    # Illustrate both custom __root__ and traditional Dict[]

    actors: ActorsById
    movies: LazyDict[MovieId, Movie]

    # Use str instead of SchemaVersion to avoid distractions.
    schema_version: str
