from .base_test import BaseVersionModuleTest
import json
import os
from pathlib import PosixPath
from typing import Any, cast

import pytest
from pydantic import FilePath, ValidationError

# We are testing the public interface so we will import from
# the package rather than the underlying modules.
from aktorz.model import Loader
from aktorz.model.v0_1_3 import VERSION


class Test_0_1_3(BaseVersionModuleTest):  # noqa: N801
    """Schema Version 0.1.3 tests."""

    # Class constants required by BaseTest

    MODEL_MODULE = "aktorz.model.v0_1_3"
    TEST_FILE = "actor-data-0.1.3.json"
    VERSION = "v0.1.3-rc1"

    # Tests...

    def test_character_full_name(self, request, actor_data_path: FilePath):
        """Verify that cast character name is handled properly"""

        # FIXME: Break this into several smaller tests.

        loader = Loader(version=VERSION)

        # Loader.load() returns a BaseVersionedModel.
        # That will trigger mypy when we try to get the `actors` property from it
        # since BaseVersionedModel has no such property.
        # Casting load's return value silences mypy
        model = cast(Any, loader.load(input=actor_data_path))

        # The Data:
        #    "dominic_toretto": {
        #      "actor": "vin_diesel",
        #      "first_name": "Dominic",
        #      "last_name": "Toretto",
        #      ...
        #    }
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].name == "Dominic Toretto"
        assert model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"]["name"] == "Dominic Toretto"
        dom = model.actors["dwayne_johnson"].movies[0].cast["dominic_toretto"].dict()
        assert dom["actor"] == "vin_diesel"
        assert dom["first_name"] == "Dominic"
        assert dom["last_name"] == "Toretto"
        assert dom["name"] == "Dominic Toretto"

    def test_loader_module_and_ctors(self, actor_data_dict: str):
        """
        Verify that loader.foo() and module.foo() and Foo() all behave identically.
        """

        loader = Loader(version=self.__class__.VERSION)

        # Loader.load() returns a BaseVersionedModel.
        # That will trigger mypy when we try to get the `actors` property from it
        # since BaseVersionedModel has no such property.
        # Casting load's return value silences mypy
        module = cast(Any, loader.module)  # aktorz.model.v0_1_3
        assert module.Model == loader.model

        Model = module.Model  # noqa:  N806

        assert Model(**actor_data_dict) == loader.load(input=actor_data_dict)

    # Define expected pydantic errors keyed by test name and optional qualifiers.
    # This helps reduce the noise level of each test and makes it easier to reuse
    # the expected errors.
    _expected_errors = {
        "test_loadable_by_0_1_0": [
            # v0.1.0 Model cannot handle the optional fields added by v0.1.3
            {
                "loc": ("actors", "charlie_chaplin", "movies", "modern_times", "gross"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "movies"),
                "msg": "value is not a valid list",
                "type": "type_error.list",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "lita_grey", "birth_year"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "lita_grey", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "lita_grey", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "mildred_harris", "birth_year"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "mildred_harris", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "mildred_harris", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "oona_oneill", "birth_year"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "oona_oneill", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "oona_oneill", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "paulette_goddard", "birth_year"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "paulette_goddard", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "spouses", "paulette_goddard", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "charlie_chaplin", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies"),
                "msg": "value is not a valid dict",
                "type": "type_error.dict",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "brian_oconner", "salary"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "dominic_toretto", "salary"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "first_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "last_name"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "cast", "mia_toretto", "salary"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "movies", 0, "gross"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "gender"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
            {
                "loc": ("actors", "dwayne_johnson", "home_town"),
                "msg": "extra fields not permitted",
                "type": "value_error.extra",
            },
        ]
    }
