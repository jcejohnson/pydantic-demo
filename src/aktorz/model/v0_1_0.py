
from pydantic import (
    Extra
)
from pydantic import BaseModel as PydanticBaseModel

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union
)


class BaseModel(PydanticBaseModel):

    class Config:
        extra: str = Extra.forbid


class Actor(BaseModel):

    first_name: str
    last_name: str
    movies: Union[Dict[str, Any], List[Any]]

    birth_year: Optional[int]
    filmography: Optional[List[Any]]
    is_funny: Optional[bool]
    spouses: Optional[Dict[str, Any]]

    hobbies: Optional[Dict[str, Any]]


class Model(BaseModel):

    schema_version: str
    actors: Dict[str, Actor]
