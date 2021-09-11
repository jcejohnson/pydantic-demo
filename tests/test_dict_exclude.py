"""
Python 3.8.0
pydantic-1.8.2

Given a list of movies where each movie has a title and a cast
And a cast has an actor plus first, last and full name
Use pydantic to export the list where last_name has been removed from each
  cast member

Test functions test_exclude_first_name_fail_* show my various attempts

"""

from typing import Dict, List, Optional

import pytest
from pydantic import BaseModel


class CastMember(BaseModel):

    actor: str
    first_name: Optional[str]
    last_name: Optional[str]
    name: Optional[str]


class Movie(BaseModel):
    title: str
    cast: Optional[Dict[str, CastMember]]


class Library(BaseModel):

    movies: List[Movie]


movies = [
    {
        "cast": {
            "brian_oconner": {"actor": "paul_walker", "name": "Brian O'Conner"},
            "dominic_toretto": {"actor": "vin_diesel", "first_name": "Dominic", "last_name": "Toretto"},
            "mia_toretto": {
                "actor": "jordana_brewster",
                "name": "Mia Toretto",
                "first_name": "Mia",
                "last_name": "Toretto",
            },
        },
        "title": "Fast Five",
    }
]

movies_title_only = [{"title": "Fast Five"}]

movies_no_last_name = [
    {
        "cast": {
            "brian_oconner": {"actor": "paul_walker", "name": "Brian O'Conner"},
            "dominic_toretto": {"actor": "vin_diesel", "first_name": "Dominic"},
            "mia_toretto": {"actor": "jordana_brewster", "name": "Mia Toretto", "first_name": "Mia"},
        },
        "title": "Fast Five",
    }
]


class TestDictExclude:
    def test_dict_export(self):
        # Success
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True) == dict({"movies": movies})

    def test_exclude_cast(self):
        # Success
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast"}}}) == dict(
            {"movies": movies_title_only}
        )
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": ...}}}) == dict(
            {"movies": movies_title_only}
        )
        assert library.dict(exclude_unset=True, exclude={"movies": {"__all__": {"cast"}}}) == dict(
            {"movies": movies_title_only}
        )
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {-1: {"cast"}}}) == dict(
            {"movies": movies_title_only}
        )

    def test_exclude_first_name_success_a(self):
        # Success
        library = Library(movies=movies)
        d = library.dict(
            exclude_unset=True,
            exclude={
                "movies": {
                    0: {
                        "cast": {
                            "dominic_toretto": {"last_name"},
                            "mia_toretto": {"last_name"},
                        }
                    }
                }
            },
        )
        assert d == dict({"movies": movies_no_last_name})

    def test_exclude_first_name_success_b(self):
        # Success
        library = Library(movies=movies)
        d = library.dict(
            exclude_unset=True,
            exclude={
                "movies": {
                    0: {
                        "cast": {
                            "dominic_toretto": {"last_name", ...},
                            "mia_toretto": {"last_name", ...},
                        }
                    }
                }
            },
        )
        assert d == dict({"movies": movies_no_last_name})

    # At least one of these _should_ be `==` instead of `!=` but I cannot figure
    # out how to make it work.
    # https://github.com/samuelcolvin/pydantic/discussions/3193

    @pytest.mark.xfail
    def test_exclude_first_name_fail_a(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {...: {"last_name"}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_b(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {...: {"last_name", ...}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_c(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {"__all__": {"last_name"}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_d(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(
            exclude_unset=True, exclude={"movies": {0: {"cast": {"__all__": {"last_name", ...}}}}}
        ) == dict({"movies": movies_no_last_name})

    @pytest.mark.xfail
    def test_exclude_first_name_fail_e(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {"*": {"last_name"}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_f(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {"*": {"last_name", ...}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_g(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {None: {"last_name"}}}}}) == dict(
            {"movies": movies_no_last_name}
        )

    @pytest.mark.xfail
    def test_exclude_first_name_fail_h(self):
        # Fail
        library = Library(movies=movies)
        assert library.dict(exclude_unset=True, exclude={"movies": {0: {"cast": {None: {"last_name", ...}}}}}) == dict(
            {"movies": movies_no_last_name}
        )
